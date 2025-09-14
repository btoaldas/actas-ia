"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path,re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from apps.pages import views
from django.conf.urls.i18n import i18n_patterns
from .native_admin import native_admin_site


handler404 = 'apps.pages.views.handler404'
handler403 = 'apps.pages.views.handler403'
handler500 = 'apps.pages.views.handler500'


urlpatterns = [
    path('', include('apps.pages.urls')),
    path("admin/", admin.site.urls),  # Admin personalizado con AdminLTE
    path("administracion/", native_admin_site.urls),  # Admin NATIVO de Django
    
    # Rutas de autenticación y OAuth
    path('accounts/', include('allauth.urls')),
    
    # APIs y aplicaciones
    path("", include("apps.dyn_api.urls")),
    path("", include("apps.dyn_dt.urls")),
    path("charts/",include("apps.charts.urls")),
    path('', include('apps.file_manager.urls')),
    path("users/", include("apps.users.urls")),
    path('tasks/', include('apps.tasks.urls')),
    path("auditoria/", include("apps.auditoria.urls")),
    path("", include("apps.react.urls")),
    path("config-system/", include("apps.config_system.urls")),
    path("audio/", include("apps.audio_processing.urls")),
    path("transcripcion/", include("apps.transcripcion.urls")),
    path("generador-actas/", include("apps.generador_actas.urls")),

    # Archivos estáticos y media
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}), 
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}), 

    # Debug toolbar
    path("__debug__/", include("debug_toolbar.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path('i18n/', views.i18n_view, name="i18n_view")
)