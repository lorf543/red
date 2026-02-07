from django.urls import path
from . import views

urlpatterns = [
    path('materias/',  views.subjects_list, name='subjects_list'),
    path('materias/data/', views.subjects_data, name='subjects_data'),
]