"""
Command para agregar permisos específicos del sistema de gestión avanzada
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.config_system.models_proxy import SystemPermissionProxy, PermissionType


class Command(BaseCommand):
    help = 'Agrega permisos específicos para el sistema de gestión avanzada'

    def handle(self, *args, **options):
        self.stdout.write('Agregando permisos para gestión avanzada...')
        
        # Permisos para gestión avanzada
        advanced_permissions = [
            # Gestión de usuarios
            {
                'name': 'Gestión de Usuarios',
                'code': 'menu.user_management',
                'permission_type': PermissionType.MENU,
                'url_pattern': '/config-system/new-permissions/users/',
                'view_name': 'user_management_list',
                'app_name': 'config_system',
                'description': 'Acceso al módulo de gestión de usuarios y asignación de perfiles'
            },
            {
                'name': 'Asignar Perfiles a Usuarios',
                'code': 'view.user_profile_assignment',
                'permission_type': PermissionType.VIEW,
                'url_pattern': '/config-system/new-permissions/users/*/assign/',
                'view_name': 'user_profile_assignment',
                'app_name': 'config_system',
                'description': 'Permite asignar y modificar perfiles de usuarios específicos'
            },
            
            # Gestión de perfiles avanzada
            {
                'name': 'Gestión Avanzada de Perfiles',
                'code': 'menu.profile_management',
                'permission_type': PermissionType.MENU,
                'url_pattern': '/config-system/new-permissions/profiles/advanced/',
                'view_name': 'profile_management_advanced',
                'app_name': 'config_system',
                'description': 'Acceso a gestión avanzada de perfiles con asignación de permisos'
            },
            {
                'name': 'Asignar Permisos a Perfiles',
                'code': 'view.profile_permission_assignment',
                'permission_type': PermissionType.VIEW,
                'url_pattern': '/config-system/new-permissions/profiles/*/permissions/',
                'view_name': 'profile_permission_assignment',
                'app_name': 'config_system',
                'description': 'Permite asignar permisos específicos a perfiles'
            },
            {
                'name': 'Eliminar Perfiles',
                'code': 'view.profile_delete',
                'permission_type': PermissionType.VIEW,
                'url_pattern': '/config-system/new-permissions/profiles/*/delete/',
                'view_name': 'profile_delete',
                'app_name': 'config_system',
                'description': 'Permite eliminar perfiles que no tengan usuarios asignados'
            },
            
            # Creación de permisos
            {
                'name': 'Crear Nuevos Permisos',
                'code': 'menu.permission_creation',
                'permission_type': PermissionType.MENU,
                'url_pattern': '/config-system/new-permissions/permissions/create/',
                'view_name': 'permission_creation',
                'app_name': 'config_system',
                'description': 'Acceso para crear permisos personalizados con rutas específicas'
            },
            {
                'name': 'Descubrir Permisos desde Rutas',
                'code': 'view.discover_routes_permissions',
                'permission_type': PermissionType.VIEW,
                'url_pattern': '/config-system/new-permissions/permissions/discover-routes/',
                'view_name': 'discover_routes_permissions',
                'app_name': 'config_system',
                'description': 'Ejecutar descubrimiento automático de permisos desde rutas de Django'
            },
            
            # Permisos del sistema principal
            {
                'name': 'Dashboard de Permisos',
                'code': 'menu.permissions_system',
                'permission_type': PermissionType.MENU,
                'url_pattern': '/config-system/new-permissions/',
                'view_name': 'permissions_dashboard',
                'app_name': 'config_system',
                'description': 'Acceso al dashboard principal del sistema de permisos'
            },
            
            # Gestión de asignaciones masivas
            {
                'name': 'Asignación Masiva de Perfiles',
                'code': 'view.bulk_profile_assignment',
                'permission_type': PermissionType.VIEW,
                'url_pattern': '/config-system/new-permissions/bulk-assign/',
                'view_name': 'bulk_assignment',
                'app_name': 'config_system',
                'description': 'Permite asignar perfiles a múltiples usuarios simultáneamente'
            }
        ]
        
        with transaction.atomic():
            created_count = 0
            updated_count = 0
            
            for perm_data in advanced_permissions:
                permission, created = SystemPermissionProxy.objects.get_or_create(
                    code=perm_data['code'],
                    defaults={
                        'name': perm_data['name'],
                        'permission_type': perm_data['permission_type'],
                        'url_pattern': perm_data['url_pattern'],
                        'view_name': perm_data['view_name'],
                        'app_name': perm_data['app_name'],
                        'description': perm_data['description'],
                        'is_active': True,
                        'auto_generated': False  # Estos son permisos manuales
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Creado: {permission.code}')
                    )
                else:
                    # Actualizar si ya existe
                    for field, value in perm_data.items():
                        if field != 'code':  # No actualizar el código
                            setattr(permission, field, value)
                    permission.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'→ Actualizado: {permission.code}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado:'
                f'\n   - {created_count} permisos creados'
                f'\n   - {updated_count} permisos actualizados'
                f'\n   - Total procesados: {len(advanced_permissions)}'
            )
        )
        
        # Mostrar resumen por tipo
        self.stdout.write('\n📊 Resumen por tipo:')
        for ptype in PermissionType.choices:
            count = SystemPermissionProxy.objects.filter(
                permission_type=ptype[0],
                is_active=True
            ).count()
            self.stdout.write(f'   - {ptype[1]}: {count} permisos')
