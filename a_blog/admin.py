from django.contrib import admin
from .models import BlogPost, PostSection

class SectionInline(admin.StackedInline):
    model = PostSection
    extra = 1

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'created_at', 'is_published')
    inlines = [SectionInline]