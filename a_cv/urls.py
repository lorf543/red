from django.urls import path
from . import views



urlpatterns = [
    path('templates/', views.cv_template_gallery, name='cv_template_gallery'),
    
    # Crear CV
    path('create/<int:template_id>/', views.create_cv, name='create_cv'),
    
    # Preview de template
    path('preview/template/<int:template_id>/', views.preview_template, name='preview_template'),
    
    # Ver CV público
    path('<slug:slug>/', views.cv_detail, name='cv_detail'),
    
    # path("add_experience",views.add_experience_form, name="add_experience_form"),
    # path('add-education', views.add_education_form, name='add_education_form'),
    # path('add-category', views.add_category_form, name='add_category_form'),
    path('forms/add-skill/', views.add_skill_form, name='add_skill_form'),
    # path('add-language', views.add_language_form, name='add_language_form'),
    # path('add-certification', views.add_certification_form, name='add_certification_form'),
]