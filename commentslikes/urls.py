# urls.py (en tu app de comentarios o principal)
from django.urls import path
from . import views

urlpatterns = [

    
    # CRUD de comentarios
    path('comment/create/', views.create_comment, name='create_comment'),
    path('comments/<int:comment_id>/edit/', views.update_comment, name='update_comment'),
    path('comments/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    path('comments/<int:comment_id>/', views.comment_detail_partial, name='comment_detail_partial'),

    
    path('comment/<int:comment_id>/reply/', views.create_reply, name='create_reply'),
    path('comments/<int:comment_id>/replies/', views.load_more_replies, name='load_more_replies'),
    path('comments/load-more/', views.load_more_comments, name='load_more_comments'),
    path('top-comments/', views.top_comments_view, name='top_comments'),
    
    
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    path('comments/<int:comment_id>/react/', views.react_to_comment, name='react_to_comment'),
    
    path('comment/<int:comment_id>/reply/', views.create_reply, name='create_reply'),

    path('comment/create/teacher/<int:teacher_id>/', views.create_teacher_comment, name='create_teacher_comment'),
    
    
    #mentions
    path('look-users',views.look_users,name="look_users"),
    
    #moderations
    path('moderate/<int:comment_id>/',views.toggle_moderate,name="toggle_moderate"),
    path('get_comment_status/<int:comment_id>/',views.get_comment_status,name="get_comment_status"),
    
]