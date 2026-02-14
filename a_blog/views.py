from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .utils import get_client_ip
from .models import BlogPost, Tag, PostSection, BlogPostStatistics, BlogPostView


from .forms import BlogPostForm
# Create your views here.


def blog_list(request):
    page_number = request.GET.get("page", 1)

    version = cache.get_or_set("blog:posts:version", 1)
    cache_key = f"blog:posts:v{version}:page:{page_number}"

    cached_data = cache.get(cache_key)

    if cached_data:
        page_obj, posts = cached_data
    else:
        posts_qs = (
            BlogPost.objects
            .filter(is_published=True)
            .select_related('author')
            .prefetch_related('tags')
        )

        paginator = Paginator(posts_qs, 5)
        page_obj = paginator.get_page(page_number)
        posts = list(page_obj.object_list)

        cache.set(cache_key, (page_obj, posts), 60 * 5)

    tags = Tag.objects.all()

    return render(request, "a_blog/blog_list.html", {
        "page_obj": page_obj,
        "posts": posts,
        "tags": tags,
    })

@login_required
def create_blog(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Crear el blog post pero no guardar aún
            blog_post = form.save(commit=False)
            blog_post.author = request.user
            blog_post.is_published = (request.POST.get('action') == 'publish')
            blog_post.save()
            
            # Guardar relaciones ManyToMany
            form.save_m2m()
            
            # Crear secciones
            section_data = {}
            for key, value in request.POST.items():
                if key.startswith('sections['):
                    import re
                    match = re.match(r'sections\[(\d+)\]\[(\w+)\]', key)
                    if match:
                        index, field = match.groups()
                        if index not in section_data:
                            section_data[index] = {}
                        section_data[index][field] = value
            
            # Crear PostSection para cada sección
            for index, data in section_data.items():
                PostSection.objects.create(
                    post=blog_post,
                    subtitle=data.get('subtitle', ''),
                    content=data.get('content', ''),
                    order=int(data.get('order', 0))
                )
            
            return redirect('blog_detail', slug=blog_post.slug)
    else:
        form = BlogPostForm()
    
    # GET request
    available_tags = Tag.objects.all()
    return render(request, 'a_blog/create_blog.html', {
        'available_tags': available_tags,
        'form': form
    })


@login_required
def update_blog(request, slug):
    blog_post = get_object_or_404(
        BlogPost.objects.prefetch_related('sections', 'tags'), 
        slug=slug
    )
    
    if request.user != blog_post.author:
        return redirect('blog_list')
    
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=blog_post)
        
        if form.is_valid():
            # Guardar post principal
            blog_post = form.save(commit=False)
            blog_post.is_published = (request.POST.get('action') == 'publish')
            blog_post.save()
            form.save_m2m()  # Guardar tags
            
            # ===== MANEJO DE SECCIONES =====
            section_data = {}
            section_ids = {}  # Para tracking de IDs existentes
            
            # 1. Recolectar datos del POST
            for key, value in request.POST.items():
                if key.startswith('sections['):
                    import re
                    match = re.match(r'sections\[(\d+)\]\[(\w+)\]', key)
                    if match:
                        index, field = match.groups()
                        if index not in section_data:
                            section_data[index] = {}
                        section_data[index][field] = value
                        
                        # Capturar IDs existentes si vienen del formulario
                        if field == 'id' and value:
                            section_ids[index] = int(value)
            
            # 2. IDs de secciones que vienen del formulario (existentes)
            ids_from_form = [int(id) for id in section_ids.values() if id]
            
            # 3. Eliminar secciones que fueron removidas del formulario
            sections_to_delete = blog_post.sections.exclude(id__in=ids_from_form)
            sections_to_delete.delete()
            
            # 4. Crear o actualizar secciones
            for index, data in section_data.items():
                section_id = section_ids.get(index)
                
                if section_id:  # Actualizar existente
                    try:
                        section = PostSection.objects.get(id=section_id, post=blog_post)
                        section.subtitle = data.get('subtitle', '')
                        section.content = data.get('content', '')
                        section.order = int(data.get('order', 0))
                        section.save()
                    except PostSection.DoesNotExist:
                        # Si no existe, crear nueva
                        PostSection.objects.create(
                            post=blog_post,
                            subtitle=data.get('subtitle', ''),
                            content=data.get('content', ''),
                            order=int(data.get('order', 0))
                        )
                else:  # Crear nueva
                    PostSection.objects.create(
                        post=blog_post,
                        subtitle=data.get('subtitle', ''),
                        content=data.get('content', ''),
                        order=int(data.get('order', 0))
                    )
            
            return redirect('blog_detail', slug=blog_post.slug)
    else:
        form = BlogPostForm(instance=blog_post)
    
    available_tags = Tag.objects.all()
    
    return render(request, 'a_blog/update_blog.html', {  # ← Cambio aquí
        'available_tags': available_tags,
        'form': form,
        'blog_post': blog_post,
    })


@require_POST
def add_section_form(request):
    """Endpoint para HTMX que devuelve el HTML de una nueva sección"""
    import random
    section_index = random.randint(1000, 9999)  # Índice único temporal
    return render(request, 'a_blog/add_section_form.html', {
        'section_index': section_index
    })


def blog_detail(request, slug):
    blog_post = get_object_or_404(BlogPost.objects.prefetch_related('sections', 'tags'), slug=slug)
    
    # Blogs relacionados por tags similares
    related_blogs = BlogPost.objects.filter(
        tags__in=blog_post.tags.all(),
        is_published=True
    ).exclude(id=blog_post.id).annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-created_at')[:5]
    
    # Posts recientes
    recent_posts = BlogPost.objects.filter(
        is_published=True
    ).exclude(id=blog_post.id).order_by('-created_at')[:5]
    
    # Todos los tags para el sidebar
    all_tags = Tag.objects.all()
    
    # Obtener estadísticas
    stats = {
        'total_views': blog_post.get_total_views(),
        'unique_views': blog_post.get_unique_views(),
        'views_today': blog_post.get_views_today(),
        'views_this_week': blog_post.get_views_this_week(),
        'views_this_month': blog_post.get_views_this_month(),
    }
    
    
    context = {
        'post': blog_post,
        'related_blogs': related_blogs,
        'recent_posts': recent_posts,
        'all_tags': all_tags,
    }
    
    return render(request, 'a_blog/blog_detail.html', context)


def _register_blog_view(request, blog_post):
    """
    Registra una vista del blog si no se ha registrado recientemente
    (evita múltiples registros en la misma sesión)
    """
    # Clave de sesión para este post
    session_key = f'viewed_post_{blog_post.id}'
    
    # Si ya vió este post en esta sesión (últimas 24 horas), no contar
    if request.session.get(session_key):
        return
    
    # Obtener información del visitante
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Crear el registro de vista
    BlogPostView.objects.create(
        post=blog_post,
        user=request.user if request.user.is_authenticated else None,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer,
        session_key=request.session.session_key
    )
    
    # Marcar en la sesión que ya vió este post
    request.session[session_key] = True
    request.session.set_expiry(86400)  # 24 horas
    
    # Actualizar estadísticas del día
    _update_daily_stats(blog_post)


def _update_daily_stats(blog_post):
    from django.db.models import Count
    today = timezone.now().date()
    
    stats, created = BlogPostStatistics.objects.get_or_create(
        post=blog_post,
        date=today
    )
    
    # Contar vistas del día
    today_views = blog_post.views.filter(viewed_at__date=today)
    stats.views_count = today_views.count()
    stats.unique_visitors = today_views.values('ip_address').distinct().count()
    stats.save()
    
    
@login_required
def blog_statistics(request, slug):
    blog_post = get_object_or_404(BlogPost, slug=slug, author=request.user)
    
    # Estadísticas generales
    total_views = blog_post.get_total_views()
    unique_views = blog_post.get_unique_views()
    
    # Vistas por día (últimos 30 días)
    views_by_day = blog_post.get_views_by_day(days=30)
    
    # Top referrers
    top_referrers = blog_post.views.exclude(
        Q(referrer='') | Q(referrer__isnull=True)
    ).values('referrer').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Dispositivos más comunes (simplificado)
    mobile_count = blog_post.views.filter(
        user_agent__icontains='Mobile'
    ).count()
    desktop_count = total_views - mobile_count
    
    # Lectores más frecuentes (usuarios autenticados)
    top_readers = blog_post.views.filter(
        user__isnull=False
    ).values(
        'user__username',
        'user__profile__slug'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'post': blog_post,
        'total_views': total_views,
        'unique_views': unique_views,
        'views_today': blog_post.get_views_today(),
        'views_this_week': blog_post.get_views_this_week(),
        'views_this_month': blog_post.get_views_this_month(),
        'views_by_day': list(views_by_day),
        'top_referrers': top_referrers,
        'mobile_count': mobile_count,
        'desktop_count': desktop_count,
        'top_readers': top_readers,
    }
    
    return render(request, 'a_blog/blog_statistics.html', context)