from django.shortcuts import render
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.core.cache import cache
from django.http import JsonResponse
from django.urls import reverse
from .models import Subject, Teacher

from django.views.decorators.cache import cache_page
from django.core.cache import cache


from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Teacher


@cache_page(60 * 5)
def subjects_list(request):
    return render(request, 'subjects_list.html')


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



class TeacherSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Teacher.objects.all()

    def location(self, obj):
        # Solo el dominio correcto + URL relativa
        return f"{reverse('subjects_list', args=[obj.slug])}"