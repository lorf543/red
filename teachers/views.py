from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from schedules.models import Teacher
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from collections import defaultdict
import hashlib

from django.views.decorators.cache import cache_page
from django.core.cache import cache

from django.db.models import Q, Prefetch, Sum


from commentslikes.models import Comment, Vote

# Create your views here.

from schedules.models import Teacher, Subject
from .forms import SubjectForm, TeacherForm


def get_comments(user=None, teacher_id=None):
    replies_prefetch = Prefetch(
        'replies',
        queryset=Comment.objects.filter(is_active=True)
                              .select_related('user')
                              .order_by('created_at')[:3],
        to_attr='preview_replies'
    )
    
    # Query base
    queryset = Comment.objects.filter(is_active=True)
    
    if user:
        queryset = queryset.filter(user=user, teacher__isnull=False)
    elif teacher_id:
        queryset = queryset.filter(teacher_id=teacher_id, parent=None)
    else:
        queryset = queryset.filter(parent=None)
    
    # Aplicar optimizaciones
    comments = list(queryset.select_related('user', 'teacher')
                       .prefetch_related(replies_prefetch)
                       .annotate(total_replies=Count('replies'))
                       .order_by('-created_at'))
        
    result = []
    for comment in comments:
        result.append({
            'comment': comment,
            'has_more_replies': comment.total_replies > 3,
            'preview_replies': getattr(comment, 'preview_replies', []),
            'total_replies': comment.total_replies
        })
    
    return result


def teachers_list(request):
    """Vista principal con paginación y búsqueda optimizada"""
    user_is_staff = request.user.is_authenticated and request.user.is_staff
    
    
    # Parámetros de búsqueda y paginación
    search_query = request.GET.get('search', '').strip()
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20)
    sort_by = request.GET.get('sort', '-se_aprende_votes')  # Default: ordenar por "Se aprende"
    
    # Generar cache key única basada en parámetros
    cache_key = f"teachers_list_{hashlib.md5(f'{search_query}_{page_number}_{per_page}_{sort_by}'.encode()).hexdigest()}"
    
    # Intentar obtener del caché
    cached_data = cache.get(cache_key)
    
    if cached_data and not request.GET.get('no_cache'):
        context = cached_data
    else:
        # Query base optimizado
        teachers_qs = Teacher.objects.filter(is_aproved=True).annotate(
            guagua_votes=Count('votes', filter=Q(votes__vote_type=1)),
            te_va_a_quemar_votes=Count('votes', filter=Q(votes__vote_type=2)),
            se_aprende_votes=Count('votes', filter=Q(votes__vote_type=3)),
            vago_votes=Count('votes', filter=Q(votes__vote_type=4)),
            total_votes=Count('votes')
        ).select_related()  
        
        # Aplicar búsqueda si existe
        if search_query:
            teachers_qs = teachers_qs.filter(
                Q(full_name__icontains=search_query) |
                Q(area__icontains=search_query)
            )
        
        # Aplicar ordenamiento
        valid_sorts = {
            'name': 'full_name',
            '-name': '-full_name',
            'guagua': '-guagua_votes',
            'quemar': '-te_va_a_quemar_votes',
            'aprende': '-se_aprende_votes',
            'vago': '-vago_votes',
            'total': '-total_votes'
        }
        teachers_qs = teachers_qs.order_by(valid_sorts.get(sort_by, '-se_aprende_votes'))
        
        # Paginación
        paginator = Paginator(teachers_qs, per_page)
        
        try:
            teachers_page = paginator.page(page_number)
        except PageNotAnInteger:
            teachers_page = paginator.page(1)
        except EmptyPage:
            teachers_page = paginator.page(paginator.num_pages)
        
        context = {
            'teachers': teachers_page,
            'search_query': search_query,
            'sort_by': sort_by,
            'total_teachers': paginator.count,
            'is_paginated': paginator.num_pages > 1,
            'page_obj': teachers_page,
        }
        
        # Cachear por 5 minutos
        cache.set(cache_key, context, 60 * 5)
    
    # Si es una petición AJAX/Fetch, devolver solo la tabla
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('teachers/partials/_teachers_table.html', context)
        return JsonResponse({
            'html': html,
            'total': context['total_teachers'],
            'page': context['page_obj'].number,
            'num_pages': context['page_obj'].paginator.num_pages
        })
    
    return render(request, 'teachers/teachers_list.html', context)


def teacher_detail(request, teacher_slug):
    teacher = get_object_or_404(Teacher, slug=teacher_slug)
    subjects = Subject.objects.filter(teacher=teacher)

    comments = Comment.objects.filter(
        teacher=teacher, 
        parent__isnull=True  # Solo comentarios principales, no replies
    ).order_by('-created_at')

    # Obtener votos para ese profesor
    votes = Vote.objects.filter(teacher=teacher).values('vote_type').annotate(count=Count('id'))
    votes_count = {
        'guagua': 0,
        'te_va_a_quemar': 0,
        'se_aprende': 0,
        'vago': 0,
    }
    for v in votes:
        if v['vote_type'] == 1:
            votes_count['guagua'] = v['count']
        elif v['vote_type'] == 2:
            votes_count['te_va_a_quemar'] = v['count']
        elif v['vote_type'] == 3:
            votes_count['se_aprende'] = v['count']
        elif v['vote_type'] == 4:
            votes_count['vago'] = v['count']

    current_vote = Vote.objects.filter(teacher=teacher, user_name=request.user.username).first()
    current_vote_type = current_vote.vote_type if current_vote else 0

    context = {
        'teacher': teacher,
        'subjects': subjects,
        'comments': comments,
        'votes_count': votes_count,
        'positive_votes': votes_count.get('se_aprende', 0),
        'negative_votes': votes_count.get('vago', 0),
        'current_vote': current_vote_type,
    }
    return render(request, 'teachers/teacher_detail.html', context)


@login_required
def create_teacher(request):

    form = TeacherForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f"Maestro '{teacher.full_name}' creado exitosamente.")
            return redirect('teachers_list')
        else:
            messages.error(request, "Formulario inválido. Verifica los campos.")

    context = {
        'form': form
    }
    return render(request, 'teachers/create_teacher.html', context)

def manage_teachers(request):
    if not request.user.is_staff:
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('teachers_list')

    teachers = Teacher.objects.filter(is_aproved=False)

    context = {
        'teachers': teachers
    }
    return render(request, 'teachers/manage_teachers.html', context)

def approve_teacher(request, teacher_slug):
    if not request.user.is_staff:
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('teachers_list')

    teacher = get_object_or_404(Teacher, slug=teacher_slug)
    teacher.is_aproved = True
    teacher.save()
    messages.success(request, f"Maestro '{teacher.full_name}' aprobado exitosamente.")
    return redirect('teachers_list')

@login_required
def assign_subject(request, teacher_slug):
    teacher = get_object_or_404(Teacher, slug=teacher_slug)
    form = SubjectForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            subject = form.save(commit=False)
            subject.teacher = teacher
            subject.added_by = request.user
            print(request.user)

            existing = Subject.objects.filter(
                teacher=teacher,
                day=subject.day,
                hour=subject.hour
            ).exists()

            if existing:
                messages.error(request, f"Ya existe una materia asignada al profesor el {subject.get_day_display()} a las {subject.hour}.")
            else:
                subject.save()
                messages.success(request, "Materia agregada exitosamente.")
                return redirect('subjects_list', teacher_slug=teacher.slug)   # O redirige a otra vista si prefieres
        else:
            messages.error(request, "Formulario inválido. Verifica los campos.")

    context = {
        'form': form,
        'teacher': teacher
    }
    return render(request, 'subjects/add_subject.html', context)
 
    
@login_required
def delete_subject(request, teacher_slug, subject_id):  # Agregué teacher_slug como parámetro
    teacher = get_object_or_404(Teacher, slug=teacher_slug)
    subject = get_object_or_404(Subject, id=subject_id, teacher=teacher)  # Validamos que la materia pertenezca al profesor

    if request.method == "POST":
        subject.delete()
        messages.success(request, "Materia eliminada exitosamente.")
        return redirect('subjects_list', teacher_slug=teacher.slug)

    context = {
        'subject': subject,
        'teacher': teacher
    }
    return render(request, 'subjects/delete_subject.html', context)


@login_required
@require_POST
def vote_teacher_2(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    vote_type = int(request.POST.get("vote_type"))

    # Buscar voto existente del usuario
    vote = Vote.objects.filter(
        teacher=teacher,
        user=request.user
    ).first()

    # Si ya existe un voto
    if vote:
        if vote.vote_type == vote_type:
            # Si vota lo mismo -> eliminar (toggle off)
            vote.delete()
            vote = None
        else:
            # Si cambia de voto -> actualizar
            vote.vote_type = vote_type
            vote.save()
    else:
        # Si no existe -> crear
        vote = Vote.objects.create(
            teacher=teacher,
            user=request.user,
            vote_type=vote_type,
        )

    # Determinar voto actual del usuario
    current_vote_type = vote.vote_type if vote else 0

    # Contar todos los votos por tipo
    votes = Vote.objects.filter(teacher=teacher).values("vote_type").annotate(count=Count("id"))

    votes_count_map = defaultdict(int)
    for v in votes:
        votes_count_map[v["vote_type"]] = v["count"]

    # Construir contexto
    context = {
        "teacher": teacher,
        "votes_count": {
            "guagua": votes_count_map[1],
            "te_va_a_quemar": votes_count_map[2],
            "se_aprende": votes_count_map[3],
            "vago": votes_count_map[4],
        },
        "current_vote": current_vote_type,
    }

    # Renderizar solo el bloque de botones
    return render(request, "teachers/partials/vote_buttons.html", context)


def votes_analysis(request):
    
    # Parámetros
    page_number = request.GET.get('page', 1)
    category_filter = request.GET.get('category', 'all')  # all, 1, 2, 3, 4
    vote_type_filter = request.GET.get('type', 'all')  # all, teacher, subject
    
    # Cache key para estadísticas (no cambian tan seguido)
    stats_cache_key = 'votes_stats_v1'
    stats = cache.get(stats_cache_key)
    
    if not stats:
        # Calcular estadísticas globales
        teachers = Teacher.objects.annotate(
            total_votes=Count('votes'),
            guagua_votes=Count('votes', filter=Q(votes__vote_type=1)),
            burn_votes=Count('votes', filter=Q(votes__vote_type=2)),
            learn_votes=Count('votes', filter=Q(votes__vote_type=3)),
            lazy_votes=Count('votes', filter=Q(votes__vote_type=4))
        ).filter(total_votes__gt=0)
        
        # Totales generales
        totals = teachers.aggregate(
            total=Sum('total_votes'),
            guagua=Sum('guagua_votes'),
            burn=Sum('burn_votes'),
            learn=Sum('learn_votes'),
            lazy=Sum('lazy_votes')
        )
        
        # Top teachers por categoría (top 3 de cada una)
        top_guagua = list(teachers.order_by('-guagua_votes')[:3])
        top_burn = list(teachers.order_by('-burn_votes')[:3])
        top_learn = list(teachers.order_by('-learn_votes')[:3])
        top_lazy = list(teachers.order_by('-lazy_votes')[:3])
        
        # Top overall (más votados en general)
        top_overall = list(teachers.order_by('-total_votes')[:5])
        
        stats = {
            'totals': totals,
            'top_guagua': top_guagua,
            'top_burn': top_burn,
            'top_learn': top_learn,
            'top_lazy': top_lazy,
            'top_overall': top_overall,
        }
        
        # Cachear por 10 minutos
        cache.set(stats_cache_key, stats, 60 * 10)
    
    # Query de votos con filtros
    votes_query = Vote.objects.select_related(
        'teacher', 
        'subject', 
        'user',
        'user__profile'
    ).order_by('-created_at')
    
    # Aplicar filtros
    if category_filter != 'all':
        votes_query = votes_query.filter(vote_type=int(category_filter))
    
    if vote_type_filter == 'teacher':
        votes_query = votes_query.filter(teacher__isnull=False)
    elif vote_type_filter == 'subject':
        votes_query = votes_query.filter(subject__isnull=False)
    
    # Paginación (20 votos por página)
    paginator = Paginator(votes_query, 20)
    votes_page = paginator.get_page(page_number)
    
    # Preparar datos de categorías para el template
    categories = [
        {
            'id': 1,
            'name': 'Guagua',
            'emoji': '🚍',
            'total': stats['totals']['guagua'] or 0,
            'top_teachers': stats['top_guagua'],
            'color': 'info',
            'bg_class': 'bg-info/10',
            'text_class': 'text-info',
            'border_class': 'border-info/30',
        },
        {
            'id': 2,
            'name': 'Te va a quemar',
            'emoji': '🔥',
            'total': stats['totals']['burn'] or 0,
            'top_teachers': stats['top_burn'],
            'color': 'danger',
            'bg_class': 'bg-danger/10',
            'text_class': 'text-danger',
            'border_class': 'border-danger/30',
        },
        {
            'id': 3,
            'name': 'Se aprende',
            'emoji': '📚',
            'total': stats['totals']['learn'] or 0,
            'top_teachers': stats['top_learn'],
            'color': 'success',
            'bg_class': 'bg-success/10',
            'text_class': 'text-success',
            'border_class': 'border-success/30',
        },
        {
            'id': 4,
            'name': 'Vago',
            'emoji': '😴',
            'total': stats['totals']['lazy'] or 0,
            'top_teachers': stats['top_lazy'],
            'color': 'muted',
            'bg_class': 'bg-muted/10',
            'text_class': 'text-muted',
            'border_class': 'border-muted/30',
        }
    ]
    stats_version = cache.get("votes:stats:version", 1)
    
    context = {
        'votes': votes_page,
        'total_votes': stats['totals']['total'] or 0,
        'categories': categories,
        'top_overall': stats['top_overall'],
        'category_filter': category_filter,
        'vote_type_filter': vote_type_filter,
        'stats_version': stats_version,
    }
    
    return render(request, 'votes/analysis.html', context)