from django.urls import path

from . import views

urlpatterns = [
    path("",views.teachers_list,name='teachers_list'),
    # path('data/', views.teachers_data, name='teachers_data'),
    
    # URLs específicas de cada profesor (usando slug)
    path('<slug:teacher_slug>/', views.teacher_detail, name='teacher_detail'),
    path('<slug:teacher_slug>/assign/', views.assign_subject, name='assign_subject'),
    path('<slug:teacher_slug>/subject/<int:subject_id>/delete/', views.delete_subject, name='delete_subject'),
    
    
    path('teachers/<int:teacher_id>/vote/', views.vote_teacher_2, name='vote_teacher_2'),
    path('vote/analysis/',views.votes_analysis,name="votes_analysis"),
    


    
]
