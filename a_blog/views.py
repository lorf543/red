from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BlogPost, Tag, PostSection
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count


from django.core.cache import cache
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

def create_blog(request):
    if request.method == 'POST':
        # Procesar el formulario
        title = request.POST.get('title')
        subtitle = request.POST.get('subtitle')
        main_paragraph = request.POST.get('main_paragraph')
        main_image = request.FILES.get('main_image')
        tags = request.POST.getlist('tags')
        action = request.POST.get('action')
        
        # Crear el blog post
        blog_post = BlogPost.objects.create(
            author=request.user,
            title=title,
            subtitle=subtitle,
            main_paragraph=main_paragraph,
            main_image=main_image,
            is_published=(action == 'publish')
        )
        
        # Agregar tags
        blog_post.tags.set(tags)
        
        # Crear secciones
        section_data = {}
        for key, value in request.POST.items():
            if key.startswith('sections['):
                # Extraer índice y campo
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
    
    # GET request
    available_tags = Tag.objects.all()
    return render(request, 'a_blog/create_blog.html', {
        'available_tags': available_tags
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
    
    context = {
        'post': blog_post,
        'related_blogs': related_blogs,
        'recent_posts': recent_posts,
        'all_tags': all_tags,
    }
    
    return render(request, 'a_blog/blog_detail.html', context)


