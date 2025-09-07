from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models_proxy import (
    user_has_permission_proxy as user_has_permission, 
    get_user_permissions_proxy as get_user_permissions
)


def require_permission(permission_code, redirect_url=None):
    """
    Decorador para requerir un permiso específico
    
    Uso:
    @require_permission('view.actas_list')
    def my_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not user_has_permission(request.user, permission_code):
                messages.error(
                    request, 
                    f'No tienes permisos para acceder a esta funcionalidad ({permission_code})'
                )
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect('dashboard-v3')  # Página principal
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def require_any_permission(*permission_codes, redirect_url=None):
    """
    Decorador para requerir AL MENOS UNO de varios permisos
    
    Uso:
    @require_any_permission('view.actas_list', 'view.actas_detail')
    def my_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            has_any_permission = any(
                user_has_permission(request.user, code) 
                for code in permission_codes
            )
            
            if not has_any_permission:
                messages.error(
                    request, 
                    f'No tienes permisos para acceder a esta funcionalidad'
                )
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect('dashboard-v3')
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def require_all_permissions(*permission_codes, redirect_url=None):
    """
    Decorador para requerir TODOS los permisos especificados
    
    Uso:
    @require_all_permissions('view.actas_list', 'view.actas_edit')
    def my_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            has_all_permissions = all(
                user_has_permission(request.user, code) 
                for code in permission_codes
            )
            
            if not has_all_permissions:
                missing = [
                    code for code in permission_codes
                    if not user_has_permission(request.user, code)
                ]
                
                messages.error(
                    request, 
                    f'No tienes todos los permisos requeridos. Faltan: {", ".join(missing)}'
                )
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return redirect('dashboard-v3')
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


class PermissionMixin:
    """
    Mixin para vistas basadas en clases que requieren permisos
    
    Uso:
    class MyView(PermissionMixin, ListView):
        required_permission = 'view.actas_list'
        ...
    """
    required_permission = None
    required_any_permissions = None
    required_all_permissions = None
    permission_denied_url = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verificar permiso único
        if self.required_permission:
            if not user_has_permission(request.user, self.required_permission):
                return self._handle_permission_denied(request, [self.required_permission])
        
        # Verificar cualquier permiso
        if self.required_any_permissions:
            has_any = any(
                user_has_permission(request.user, code)
                for code in self.required_any_permissions
            )
            if not has_any:
                return self._handle_permission_denied(request, self.required_any_permissions)
        
        # Verificar todos los permisos
        if self.required_all_permissions:
            missing = [
                code for code in self.required_all_permissions
                if not user_has_permission(request.user, code)
            ]
            if missing:
                return self._handle_permission_denied(request, missing)
        
        return super().dispatch(request, *args, **kwargs)
    
    def _handle_permission_denied(self, request, missing_permissions):
        """Maneja la denegación de permisos"""
        messages.error(
            request,
            f'No tienes permisos para acceder a esta funcionalidad'
        )
        
        if self.permission_denied_url:
            return redirect(self.permission_denied_url)
        else:
            return redirect('dashboard-v3')


# Context processors para templates
def permissions_context(request):
    """
    Context processor que añade los permisos del usuario a todos los templates
    
    Uso en templates:
    {% if 'menu.actas' in user_permissions_codes %}
        <a href="...">Actas</a>
    {% endif %}
    """
    if not request.user.is_authenticated:
        return {
            'user_permissions': [],
            'user_permissions_codes': [],
            'user_can_access_admin': False,
        }
    
    user_permissions = get_user_permissions(request.user)
    permission_codes = list(user_permissions.values_list('code', flat=True))
    
    return {
        'user_permissions': user_permissions,
        'user_permissions_codes': permission_codes,
        'user_can_access_admin': request.user.is_superuser or request.user.is_staff,
    }


# Template tags helpers
def user_can_access_menu(user, menu_code):
    """Verifica si el usuario puede acceder a un menú específico"""
    return user_has_permission(user, f'menu.{menu_code}')


def user_can_access_view(user, view_name):
    """Verifica si el usuario puede acceder a una vista específica"""
    return user_has_permission(user, f'view.{view_name}')


def user_can_access_module(user, module_name):
    """Verifica si el usuario puede acceder a un módulo específico"""
    return user_has_permission(user, f'module.{module_name}')


# Middleware simple para logging de accesos
class PermissionLoggingMiddleware:
    """
    Middleware para registrar intentos de acceso denegados
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Si es una respuesta 403 (Forbidden), loguearlo
        if response.status_code == 403 and request.user.is_authenticated:
            import logging
            logger = logging.getLogger('permissions')
            logger.warning(
                f'Acceso denegado: Usuario {request.user.username} '
                f'intentó acceder a {request.path}'
            )
        
        return response
