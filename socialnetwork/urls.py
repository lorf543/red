from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from debug_toolbar.toolbar import debug_toolbar_urls
import os

from core import views as views_robot

from django.contrib.sitemaps.views import sitemap
from schedules.views import TeacherSitemap


sitemaps_dict = {
    "teachers": TeacherSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("allauth.urls")),
    path("horarios/", include("schedules.urls")),
    path("teachers/", include("teachers.urls")),
    path("comments/", include("commentslikes.urls")),
    path("notifications/", include("notifications.urls")),
    path("schema-viewer/", include("schema_viewer.urls")),
    path("robots.txt", views_robot.robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps_dict}, name="sitemap"),
]


if settings.DEBUG:
    # Sirve archivos estáticos y media en desarrollo
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
    urlpatterns += static(settings.MEDIA_URL, document_root=os.path.join(settings.BASE_DIR, 'media'))
