
from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.notifications_view, name='notifications_view'),
    path('notifications/redirect/<int:notification_id>/', views.notification_redirect, name='notification_redirect'),

    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    path('comment/<int:notification_id>/', views.notification_detail, name='notification_detail'),
    path("count/", views.notification_count, name="notification_count"),

]