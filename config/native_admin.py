"""
Admin Nativo de Django - Sin Templates Personalizados
Este módulo crea un admin site completamente separado que usa
los templates originales de Django en lugar de AdminLTE
"""
from django.contrib.admin import AdminSite
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.template.response import TemplateResponse
from django.contrib.admin import forms as admin_forms


class DjangoNativeAdminSite(AdminSite):
    """
    Admin site que usa templates nativos específicos
    """
    site_header = "Administración Nativa Django - Actas IA"
    site_title = "Admin Nativo Django"
    index_title = "Panel de Administración Django"
    
    def login(self, request, extra_context=None):
        """
        Override para usar template nativo específico de login
        """
        if request.method == 'GET':
            context = {
                'title': 'Log in',
                'site_title': self.site_title,
                'site_header': self.site_header,
                'site_url': '/',
                'form': admin_forms.AdminAuthenticationForm(),
            }
            if extra_context:
                context.update(extra_context)
            
            return TemplateResponse(request, 'admin_nativo/login.html', context)
        
        # Para POST, usar el comportamiento normal de Django admin
        return super().login(request, extra_context)
    
    def index(self, request, extra_context=None):
        """
        Override para usar template nativo específico de index
        """
        context = {
            'title': self.index_title,
            'site_title': self.site_title,
            'site_header': self.site_header,
            'site_url': '/',
            'available_apps': self.get_app_list(request),
            'user': request.user,
        }
        if extra_context:
            context.update(extra_context)
            
        return TemplateResponse(request, 'admin_nativo/index.html', context)


# Crear instancia del admin nativo
native_admin_site = DjangoNativeAdminSite(name='native_admin')

# Registrar modelos básicos de Django
native_admin_site.register(User)
native_admin_site.register(Group)