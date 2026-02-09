from django.urls import path

from . import views

urlpatterns = [
    path("",views.teachers_list,name='teachers_list'),

    path('create/teacher/', views.create_teacher, name='create_teacher'),
    path('manage/teachers/', views.manage_teachers, name='manage_teachers'),

    path('approve/teacher/<slug:teacher_slug>/', views.approve_teacher, name='approve_teacher'),
    
    path('<slug:teacher_slug>/', views.teacher_detail, name='teacher_detail'),
    path('<slug:teacher_slug>/assign/', views.assign_subject, name='assign_subject'),
    path('<slug:teacher_slug>/subject/<int:subject_id>/delete/', views.delete_subject, name='delete_subject'),
    
    
    path('teachers/<int:teacher_id>/vote/', views.vote_teacher_2, name='vote_teacher_2'),
    path('vote/analysis/',views.votes_analysis,name="votes_analysis"),
        
]
