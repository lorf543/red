from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from schedules.models import Teacher
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from collections import defaultdict

from django.views.decorators.cache import cache_page
from django.core.cache import cache

from django.db.models import Count,Q, Prefetch, Case, When, IntegerField, Sum


from commentslikes.models import Comment, Vote

# Create your views here.

from schedules.models import Teacher, Subject
from .forms import SubjectForm


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

@cache_page(60 * 5)
def teachers_list(request):

    teachers = Teacher.objects.annotate(
        guagua_votes=Count('votes', filter=Q(votes__vote_type=1)),
        te_va_a_quemar_votes=Count('votes', filter=Q(votes__vote_type=2)),
        se_aprende_votes=Count('votes', filter=Q(votes__vote_type=3)),
        vago_votes=Count('votes', filter=Q(votes__vote_type=4)),
    ).values('id', 'full_name', 'guagua_votes', 'te_va_a_quemar_votes', 'se_aprende_votes', 'vago_votes','slug')

    context = {
        'teachers': teachers,
    }
    return render(request,'teachers/teachers_list.html',context)


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
    teachers = Teacher.objects.annotate(
        total_votes=Count('votes'),
        guagua_votes=Count(Case(When(votes__vote_type=1, then=1), output_field=IntegerField())),
        burn_votes=Count(Case(When(votes__vote_type=2, then=1), output_field=IntegerField())),
        learn_votes=Count(Case(When(votes__vote_type=3, then=1), output_field=IntegerField())),
        lazy_votes=Count(Case(When(votes__vote_type=4, then=1), output_field=IntegerField()))
    ).filter(total_votes__gt=0).order_by('-total_votes')

    # Calculate totals
    totals = teachers.aggregate(
        total=Sum('total_votes'),
        guagua=Sum('guagua_votes'),
        burn=Sum('burn_votes'),
        learn=Sum('learn_votes'),
        lazy=Sum('lazy_votes')
    )

    # Get top teachers for each category
    top_guagua = teachers.order_by('-guagua_votes').first()
    top_burn = teachers.order_by('-burn_votes').first()
    top_learn = teachers.order_by('-learn_votes').first()
    top_lazy = teachers.order_by('-lazy_votes').first()

    # Prepare category data
    categories = [
        {
            'id': 1,
            'name': 'Guagua 🚍',
            'total': totals['guagua'] or 0,
            'top_teacher': top_guagua,
            'top_votes': top_guagua.guagua_votes if top_guagua else 0,
            'color': 'success'
        },
        {
            'id': 2,
            'name': 'Quemar 🔥',
            'total': totals['burn'] or 0,
            'top_teacher': top_burn,
            'top_votes': top_burn.burn_votes if top_burn else 0,
            'color': 'error'
        },
        {
            'id': 3,
            'name': 'Aprende 📚',
            'total': totals['learn'] or 0,
            'top_teacher': top_learn,
            'top_votes': top_learn.learn_votes if top_learn else 0,
            'color': 'info'
        },
        {
            'id': 4,
            'name': 'Vago 😴',
            'total': totals['lazy'] or 0,
            'top_teacher': top_lazy,
            'top_votes': top_lazy.lazy_votes if top_lazy else 0,
            'color': 'warning'
        }
    ]
    
    votes = Vote.objects.select_related('teacher', 'subject', 'user').order_by('-created_at')

    context = {
        'teachers': teachers,
        'total_votes': totals['total'] or 0,
        'categories': categories,
        'votes': votes  
    }
    return render(request, 'votes/analysis.html', context)