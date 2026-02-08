
from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.notifications_view, name='notifications_view'),
    
    path('comment/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    
    path('notifications/<int:notification_id>/read/', views.mark_as_read, name='mark_as_read'),
    path('notifications/mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path("count/", views.notification_count, name="notification_count"),

]