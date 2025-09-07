"""
Modelos Django que mapean a las tablas creadas manualmente
Estos modelos permiten que Django trabaje con las tablas sin conflictos de migración
"""
from django.db import models
from django.contrib.auth.models import User


class PermissionType(models.TextChoices):
    """Tipos de permisos en el sistema"""
    MENU = 'menu', 'Menú'
    VIEW = 'view', 'Vista'
    WIDGET = 'widget', 'Widget'
    MODULE = 'module', 'Módulo'


class SystemPermissionProxy(models.Model):
    """Modelo proxy para la tabla config_system_systempermission"""
    
    class PermissionType(models.TextChoices):
        MENU = 'menu', 'Menú'
        VIEW = 'view', 'Vista'
        WIDGET = 'widget', 'Widget'
        MODULE = 'module', 'Módulo'
    
    name = models.CharField(max_length=255, verbose_name="Nombre")
    code = models.CharField(max_length=255, unique=True, verbose_name="Código único")
    permission_type = models.CharField(
        max_length=20, 
        choices=PermissionType.choices,
        verbose_name="Tipo de permiso"
    )
    url_pattern = models.CharField(max_length=500, blank=True, null=True, verbose_name="Patrón URL")
    view_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Nombre de la vista")
    app_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Aplicación")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    auto_generated = models.BooleanField(default=True, verbose_name="Auto-generado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'config_system_systempermission'
        verbose_name = "Permiso del Sistema"
        verbose_name_plural = "Permisos del Sistema"
        ordering = ['permission_type', 'app_name', 'name']

    def __str__(self):
        return f"{self.get_permission_type_display()}: {self.name}"


class UserProfileProxy(models.Model):
    """Modelo proxy para la tabla config_system_userprofile"""
    
    name = models.CharField(max_length=255, unique=True, verbose_name="Nombre del perfil")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")
    permissions = models.ManyToManyField(
        SystemPermissionProxy,
        blank=True,
        verbose_name="Permisos",
        help_text="Permisos incluidos en este perfil",
        through='UserProfilePermissionProxy'
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'config_system_userprofile'
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_permission_codes(self):
        """Retorna lista de códigos de permisos del perfil"""
        return list(self.permissions.filter(is_active=True).values_list('code', flat=True))


class UserProfileAssignmentProxy(models.Model):
    """Modelo proxy para la tabla config_system_userprofileassignment"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Usuario",
        related_name="userprofileassignmentproxy_set"
    )
    profile = models.ForeignKey(
        UserProfileProxy, 
        on_delete=models.CASCADE, 
        verbose_name="Perfil",
        related_name="userprofileassignmentproxy_set"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="profile_assignments_made_proxy",
        verbose_name="Asignado por"
    )

    class Meta:
        db_table = 'config_system_userprofileassignment'
        verbose_name = "Asignación de Perfil"
        verbose_name_plural = "Asignaciones de Perfiles"
        unique_together = ['user', 'profile']

    def __str__(self):
        return f"{self.user.username} - {self.profile.name}"


class UserProfilePermissionProxy(models.Model):
    """Modelo proxy para la tabla de relación many-to-many"""
    
    userprofile = models.ForeignKey(UserProfileProxy, on_delete=models.CASCADE)
    systempermission = models.ForeignKey(SystemPermissionProxy, on_delete=models.CASCADE)

    class Meta:
        db_table = 'config_system_userprofile_permissions'
        unique_together = ['userprofile', 'systempermission']


# Funciones helper para trabajar con los modelos proxy
def user_has_permission_proxy(user, permission_code):
    """
    Verifica si un usuario tiene un permiso específico usando modelos proxy
    """
    if user.is_superuser or user.is_staff:
        return True
    
    # Buscar en los perfiles del usuario
    try:
        assignments = UserProfileAssignmentProxy.objects.filter(
            user=user,
            profile__is_active=True
        ).select_related('profile')
        
        for assignment in assignments:
            if assignment.profile.permissions.filter(
                code=permission_code,
                is_active=True
            ).exists():
                return True
        
        return False
    except Exception:
        return False


def get_user_permissions_proxy(user):
    """
    Obtiene todos los permisos de un usuario usando modelos proxy
    """
    if user.is_superuser or user.is_staff:
        return SystemPermissionProxy.objects.filter(is_active=True)
    
    try:
        # Obtener IDs de permisos de todos los perfiles del usuario
        assignments = UserProfileAssignmentProxy.objects.filter(
            user=user,
            profile__is_active=True
        ).values_list('profile__permissions__id', flat=True)
        
        permission_ids = [pid for pid in assignments if pid is not None]
        
        return SystemPermissionProxy.objects.filter(
            id__in=set(permission_ids),
            is_active=True
        )
    except Exception:
        return SystemPermissionProxy.objects.none()


# Clases para descubrimiento automático
class PermissionDiscoveryProxy:
    """Clase para auto-descubrir permisos usando modelos proxy"""
    
    @classmethod
    def discover_all_permissions(cls):
        """Descubre y crea todos los permisos del sistema"""
        discovered = {
            'menus': cls.discover_menus(),
            'views': cls.discover_views(),
            'widgets': cls.discover_widgets(),
            'modules': cls.discover_modules(),
        }
        return discovered
    
    @classmethod
    def discover_views(cls):
        """Descubre todas las vistas del sistema"""
        from django.urls import get_resolver
        
        permissions_created = []
        resolver = get_resolver()
        
        for url_pattern in cls._get_all_url_patterns(resolver):
            if url_pattern.name:
                code = f"view.{url_pattern.name}"
                name = url_pattern.name.replace('_', ' ').title()
                
                permission, created = SystemPermissionProxy.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'permission_type': SystemPermissionProxy.PermissionType.VIEW,
                        'view_name': url_pattern.name,
                        'url_pattern': str(url_pattern.pattern),
                        'description': f"Acceso a la vista {name}",
                        'auto_generated': True,
                    }
                )
                
                if created:
                    permissions_created.append(permission)
        
        return permissions_created
    
    @classmethod
    def discover_menus(cls):
        """Descubre menús del sistema"""
        known_menus = [
            {'code': 'menu.dashboard', 'name': 'Dashboard', 'url': '/dashboard-v3/'},
            {'code': 'menu.actas', 'name': 'Actas', 'url': '/actas/'},
            {'code': 'menu.transparencia', 'name': 'Transparencia', 'url': '/transparencia/'},
            {'code': 'menu.config_system', 'name': 'Configuración del Sistema', 'url': '/config-system/'},
            {'code': 'menu.users', 'name': 'Gestión de Usuarios', 'url': '/users/'},
            {'code': 'menu.permisos', 'name': 'Gestión de Permisos', 'url': '/config-system/new-permissions/'},
        ]
        
        permissions_created = []
        for menu_data in known_menus:
            permission, created = SystemPermissionProxy.objects.get_or_create(
                code=menu_data['code'],
                defaults={
                    'name': menu_data['name'],
                    'permission_type': SystemPermissionProxy.PermissionType.MENU,
                    'url_pattern': menu_data['url'],
                    'description': f"Acceso al menú {menu_data['name']}",
                    'auto_generated': True,
                }
            )
            
            if created:
                permissions_created.append(permission)
        
        return permissions_created
    
    @classmethod
    def discover_widgets(cls):
        """Descubre widgets del sistema"""
        return []
    
    @classmethod
    def discover_modules(cls):
        """Descubre módulos del sistema"""
        from django.apps import apps
        
        permissions_created = []
        
        for app_config in apps.get_app_configs():
            if not app_config.name.startswith('django.'):
                code = f"module.{app_config.name}"
                name = app_config.verbose_name or app_config.name.title()
                
                permission, created = SystemPermissionProxy.objects.get_or_create(
                    code=code,
                    defaults={
                        'name': f"Módulo {name}",
                        'permission_type': SystemPermissionProxy.PermissionType.MODULE,
                        'app_name': app_config.name,
                        'description': f"Acceso al módulo {name}",
                        'auto_generated': True,
                    }
                )
                
                if created:
                    permissions_created.append(permission)
        
        return permissions_created
    
    @classmethod
    def _get_all_url_patterns(cls, resolver, namespace_path=''):
        """Recursivamente obtiene todos los patrones de URL"""
        patterns = []
        
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                namespace = pattern.namespace or ''
                if namespace_path:
                    full_namespace = f"{namespace_path}:{namespace}" if namespace else namespace_path
                else:
                    full_namespace = namespace
                patterns.extend(cls._get_all_url_patterns(pattern, full_namespace))
            else:
                if namespace_path and pattern.name:
                    pattern.name = f"{namespace_path}:{pattern.name}"
                patterns.append(pattern)
        
        return patterns
