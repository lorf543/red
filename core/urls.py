from django.urls import path
from allauth.account.views import LoginView, SignupView,LogoutView

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('login/', LoginView.as_view(template_name='account/login.html'), name='login'),
    path('registro/', SignupView.as_view(template_name='account/signup.html'), name='account_signup'),
    path('logout/', LogoutView.as_view(), name='account_logout'),
    
    path('perfil/<slug:slug>/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    
    path('conf/',views.confifraciones,name='configurations'),
    path('politicas/',views.politicas,name='politicas'),
    
    path('check-username/',views.check_username,name='check_username'),
    path('search/', views.search_view, name='search-view'),
    
    path('tutorail/',views.tutoriales,name='tutoriales'),
    path('donaciones',views.donations,name='donations'),
]
