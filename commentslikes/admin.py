from django.contrib import admin

from .models import Vote,Mention,Badword,Comment


admin.site.register(Vote)
admin.site.register(Mention)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'created_at']
    list_filter = ('created_at','is_active')
    search_fields = ('user_name', 'content', 'is_active','teacher__full_name', 'subject__name')


@admin.register(Badword)
class BadwordAdmin(admin.ModelAdmin):
    list_display = ('word', 'replacement', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('word',)