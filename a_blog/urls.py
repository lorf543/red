
from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.blog_list, name='blog_list'),
    path('add_section_form/', views.add_section_form, name='add_section_form'),
    path('create_blog/', views.create_blog, name='create_blog'),
    
    path('update_blog/<slug:slug>/', views.update_blog, name='update_blog'),
    path('blog_detail/<slug:slug>/', views.blog_detail, name='blog_detail'),
    
    path('blog/<slug:slug>/statistics/', views.blog_statistics, name='blog_statistics')

]