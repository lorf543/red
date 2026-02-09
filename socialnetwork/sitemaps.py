from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from schedules.models import Teacher
from a_blog.models import BlogPost


from django.http import HttpResponse

# class PostSitemap(Sitemap):
#     changefreq = "weekly"
#     priority = 0.8
#     protocol = 'https'

#     def items(self):

#         return Post.objects.filter(status='published').order_by('-published_at')

#     def lastmod(self, obj):
#         return obj.updated_at
    
#     def location(self, obj):
#         return reverse('a_authentication:view_blog_detail', kwargs={'slug': obj.slug})

# class CourseSitemap(Sitemap):
#     changefreq = "monthly"
#     priority = 0.9
#     protocol = 'https'

#     def items(self):
#         # Solo indexamos cursos activos
#         return Course.objects.filter(is_active=True).order_by('-created_at')

#     def lastmod(self, obj):
#         return obj.updated_at
    
#     def location(self, obj):

#         return obj.get_absolute_url()



class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'monthly'
    protocol = 'https'

    def items(self):
        return ['home', 'donations','politicas']  

    def location(self, item):
        return reverse(item)
    
    
class BlogPostSitemap(Sitemap):
    priority = 1.0
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return BlogPost.objects.filter(is_published=True) 
    
    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()

class TeacherSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    protocol = 'https'
    
    def items(self):
        return Teacher.objects.filter(is_aproved=True)
    

    # def lastmod(self, obj):
    #     return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()
    

   

    
    
    
def robots_txt(request):
    content = """User-agent: *
        Disallow: /admin/
        Disallow: /accounts/
        Disallow: /login/
        Disallow: /logout/
        Disallow: /signup/
        Disallow: /password-reset/

        Sitemap: https://https://itlasocial.org/sitemap.xml
    """
    return HttpResponse(content, content_type="text/plain")