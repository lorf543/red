from django.contrib import admin
from .models import Teacher, Subject

from commentslikes.models import Reaction




admin.site.register(Reaction)
admin.site.register(Teacher)
admin.site.register(Subject)

# @admin.register(Teacher)
# class TeacherAdmin(admin.ModelAdmin):
#     list_display = ('full_name', 'area')
#     search_fields = ('full_name', 'area')

# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('code', 'name', 'teacher', 'dia', 'hora')
#     list_filter = ('dia', 'teacher')
#     search_fields = ('code', 'name', 'teacher__full_name')




# @admin.register(Vote)
# class VoteAdmin(admin.ModelAdmin):
#     list_display = ('user_name', 'vote_type_display', 'created_at', 'teacher_or_subject')
#     list_filter = ('vote_type', 'created_at')
    
#     def vote_type_display(self, obj):
#         return 'Positivo' if obj.vote_type == 1 else 'Negativo'
#     vote_type_display.short_description = 'Tipo de voto'
    
#     def teacher_or_subject(self, obj):
#         return obj.teacher if obj.teacher else obj.subject
#     teacher_or_subject.short_description = 'Objetivo'