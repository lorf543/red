from django.contrib import admin
from .models import BlogPost, PostSection, Tag, BlogPostView, BlogPostStatistics

class SectionInline(admin.StackedInline):
    model = PostSection
    extra = 1

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'created_at', 'is_published')
    inlines = [SectionInline]
    
    
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
 
 
@admin.register(BlogPostView)
class BlogPostViewAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at', 'post']
    search_fields = ['post__title', 'user__username', 'ip_address']
    readonly_fields = ['viewed_at']

@admin.register(BlogPostStatistics)
class BlogPostStatisticsAdmin(admin.ModelAdmin):
    list_display = ['post', 'date', 'views_count', 'unique_visitors']
    list_filter = ['date']
    search_fields = ['post__title']