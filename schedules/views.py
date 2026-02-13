from django.shortcuts import render
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.core.cache import cache
from django.http import JsonResponse
from django.urls import reverse
from django.template.loader import render_to_string
from .models import Subject, Teacher

from django.views.decorators.cache import cache_page
from django.core.cache import cache


from django.contrib.sitemaps import Sitemap

from .models import Teacher



def subjects_list(request):
    """
    Vista principal para el listado de materias con búsqueda, filtros y paginación
    """
    # Obtener parámetros de búsqueda y filtros
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'name')
    modalidad_filter = request.GET.get('modalidad', '')
    page_number = request.GET.get('page', 1)
    
    # Query base con anotaciones de votos del profesor
    subjects = Subject.objects.select_related('teacher').annotate(
        guagua_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=1)),
        te_va_a_quemar_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=2)),
        se_aprende_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=3)),
        vago_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=4)),
        total_votes=Count('teacher__votes')
    )
    
    # Aplicar búsqueda
    if search_query:
        subjects = subjects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(teacher__full_name__icontains=search_query) |
            Q(teacher__area__icontains=search_query)
        ).distinct()
    
    # Aplicar filtro de modalidad
    if modalidad_filter:
        subjects = subjects.filter(modalidad=modalidad_filter)
    
    # Aplicar ordenamiento
    sort_mapping = {
        'name': 'name',
        '-name': '-name',
        'aprende': '-se_aprende_votes',
        'quemar': '-te_va_a_quemar_votes',
        'guagua': '-guagua_votes',
        'vago': '-vago_votes',
        'total': '-total_votes'
    }
    
    order_by = sort_mapping.get(sort_by, 'name')
    subjects = subjects.order_by(order_by)
    
    # Paginación
    paginator = Paginator(subjects, 20)  # 20 materias por página
    page_obj = paginator.get_page(page_number)
    
    # Contexto común
    context = {
        'subjects': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'sort_by': sort_by,
        'modalidad_filter': modalidad_filter,
        'total_subjects': Subject.objects.count(),
    }
    
    # Si es una petición AJAX, devolver solo la tabla en JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string(
            'subjects/partials/_subjects_table.html',
            context,
            request=request
        )
        return JsonResponse({'html': html})
    
    # Si es petición normal, devolver el template completo
    return render(request, 'subjects_list.html', context)


def subjects_data(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    search_value = request.GET.get("search[value]", "")


    cache_key = f"subjects_data:{search_value}:{start}:{length}"
    cached_response = cache.get(cache_key)

    if cached_response:
        return JsonResponse(cached_response)

    # Anotamos cada materia con los votos de su profesor
    queryset = Subject.objects.select_related('teacher').annotate(
        guagua_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=1)),
        te_va_a_quemar_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=2)),
        se_aprende_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=3)),
        vago_votes=Count('teacher__votes', filter=Q(teacher__votes__vote_type=4)),
        total_votes=Count('teacher__votes')
    )

    if search_value:
        queryset = queryset.filter(
            Q(name__icontains=search_value) |
            Q(teacher__full_name__icontains=search_value) |
            Q(description__icontains=search_value)
        ).distinct()

    total_records = Subject.objects.count()
    filtered_records = queryset.count()

    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page = paginator.get_page(page_number)

    data = []
    for subject in page:
        data.append({
            'name': subject.name,
            'description': subject.description or "—",
            'teacher': subject.teacher.full_name if subject.teacher else "—",
            'modalidad': subject.get_modalidad_display() if subject.modalidad else "—",
            'schedule': subject.subject_schedule(),
            'guagua_votes': subject.guagua_votes,
            'te_va_a_quemar_votes': subject.te_va_a_quemar_votes,
            'se_aprende_votes': subject.se_aprende_votes,
            'vago_votes': subject.vago_votes,
            'total_votes': subject.total_votes,

        })

    response_data = {
        'draw': draw,
        'recordsTotal': total_records,
        'recordsFiltered': filtered_records,
        'data': data
    }
    cache.set(cache_key, response_data, timeout=300)
    return JsonResponse(response_data)


