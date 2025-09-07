from django import template
from django.contrib.auth.models import User
from apps.config_system.models_proxy import (
    user_has_permission_proxy as user_has_permission, 
    get_user_permissions_proxy as get_user_permissions
)

register = template.Library()


@register.filter
def has_permission(user, permission_code):
    """
    Template filter para verificar permisos
    
    Uso: {{ user|has_permission:"menu.actas" }}
    """
    if not isinstance(user, User):
        return False
    return user_has_permission(user, permission_code)


@register.filter
def has_any_permission(user, permission_codes):
    """
    Template filter para verificar si tiene alguno de varios permisos
    
    Uso: {{ user|has_any_permission:"menu.actas,menu.transparencia" }}
    """
    if not isinstance(user, User):
        return False
    
    codes = [code.strip() for code in permission_codes.split(',')]
    return any(user_has_permission(user, code) for code in codes)


@register.filter
def has_all_permissions(user, permission_codes):
    """
    Template filter para verificar si tiene todos los permisos
    
    Uso: {{ user|has_all_permissions:"menu.actas,view.actas_list" }}
    """
    if not isinstance(user, User):
        return False
    
    codes = [code.strip() for code in permission_codes.split(',')]
    return all(user_has_permission(user, code) for code in codes)


@register.filter
def get_user_permissions_proxy(user):
    """
    Template filter para obtener todos los permisos del usuario
    
    Uso: {{ user|get_user_permissions_proxy }}
    """
    if not isinstance(user, User):
        return []
    return get_user_permissions(user)


@register.filter
def key(dictionary, key_name):
    """
    Template filter para acceder a valores de diccionario por clave
    
    Uso: {{ my_dict|key:"some_key" }}
    """
    try:
        return dictionary[key_name]
    except (KeyError, TypeError, AttributeError):
        return None


@register.simple_tag
def user_permissions(user):
    """
    Template tag para obtener todos los permisos del usuario
    
    Uso: {% user_permissions user as permissions %}
    """
    if not isinstance(user, User):
        return []
    return get_user_permissions(user)


@register.simple_tag
def user_permission_codes(user):
    """
    Template tag para obtener códigos de permisos del usuario
    
    Uso: {% user_permission_codes user as codes %}
    """
    if not isinstance(user, User):
        return []
    return list(get_user_permissions(user).values_list('code', flat=True))


@register.inclusion_tag('config_system/templatetags/menu_item.html')
def menu_item(user, menu_code, menu_name, menu_url, icon_class="fas fa-circle", active_class=""):
    """
    Template tag para renderizar un elemento de menú con verificación de permisos
    
    Uso: {% menu_item user "actas" "Actas" "/actas/" "fas fa-file-alt" %}
    """
    can_access = user_has_permission(user, f'menu.{menu_code}')
    
    return {
        'can_access': can_access,
        'menu_name': menu_name,
        'menu_url': menu_url,
        'icon_class': icon_class,
        'active_class': active_class,
    }


@register.inclusion_tag('config_system/templatetags/admin_menu_section.html')
def admin_menu_section(user, title, items):
    """
    Template tag para renderizar una sección completa del menú administrativo
    
    Uso: 
    {% admin_menu_section user "Gestión" menu_items %}
    """
    accessible_items = []
    
    for item in items:
        permission_code = item.get('permission', '')
        if not permission_code or user_has_permission(user, permission_code):
            accessible_items.append(item)
    
    return {
        'title': title,
        'items': accessible_items,
        'has_items': len(accessible_items) > 0,
    }


@register.simple_tag
def can_access_menu(user, menu_code):
    """
    Verificación simple para menús
    
    Uso: {% can_access_menu user "actas" as can_access %}
    """
    return user_has_permission(user, f'menu.{menu_code}')


@register.simple_tag
def can_access_view(user, view_name):
    """
    Verificación simple para vistas
    
    Uso: {% can_access_view user "actas_list" as can_access %}
    """
    return user_has_permission(user, f'view.{view_name}')


@register.simple_tag
def can_access_module(user, module_name):
    """
    Verificación simple para módulos
    
    Uso: {% can_access_module user "actas" as can_access %}
    """
    return user_has_permission(user, f'module.{module_name}')


@register.filter
def permission_type_icon(permission_type):
    """
    Retorna un ícono CSS para el tipo de permiso
    
    Uso: {{ permission.permission_type|permission_type_icon }}
    """
    icons = {
        'menu': 'fas fa-bars',
        'view': 'fas fa-eye',
        'widget': 'fas fa-puzzle-piece',
        'module': 'fas fa-cube',
    }
    return icons.get(permission_type, 'fas fa-question')


@register.filter
def permission_type_color(permission_type):
    """
    Retorna una clase CSS de color para el tipo de permiso
    
    Uso: {{ permission.permission_type|permission_type_color }}
    """
    colors = {
        'menu': 'text-primary',
        'view': 'text-success',
        'widget': 'text-warning',
        'module': 'text-info',
    }
    return colors.get(permission_type, 'text-secondary')
