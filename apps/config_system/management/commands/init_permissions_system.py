"""
Script de inicialización completa del nuevo sistema de permisos
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.auth.models import User
from apps.config_system.models_proxy import (
    SystemPermissionProxy,
    UserProfileProxy,
    UserProfileAssignmentProxy,
    PermissionDiscoveryProxy
)


class Command(BaseCommand):
    help = 'Inicializa completamente el nuevo sistema de permisos'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando inicialización completa del sistema de permisos...')
        )

        try:
            # 1. Verificar que las tablas existen
            self.verify_tables()
            
            # 2. Descubrir y crear permisos automáticamente
            self.discover_permissions()
            
            # 3. Crear perfiles básicos
            self.create_basic_profiles()
            
            # 4. Asignar perfiles a usuarios existentes
            self.assign_profiles_to_users()
            
            # 5. Mostrar resumen
            self.show_summary()
            
            self.stdout.write(
                self.style.SUCCESS('✅ ¡Inicialización completa exitosa!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la inicialización: {str(e)}')
            )

    def verify_tables(self):
        """Verifica que las tablas del sistema existen"""
        self.stdout.write('🔍 Verificando tablas...')
        
        with connection.cursor() as cursor:
            tables = [
                'config_system_systempermission',
                'config_system_userprofile',
                'config_system_userprofileassignment',
                'config_system_userprofile_permissions'
            ]
            
            for table in tables:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = %s
                """, [table])
                
                if cursor.fetchone()[0] == 0:
                    raise Exception(f"Tabla {table} no existe. Ejecuta primero 'setup_new_permissions'")
                else:
                    self.stdout.write(f'   ✅ Tabla {table} existe')

    def discover_permissions(self):
        """Descubre y crea permisos automáticamente"""
        self.stdout.write('🔍 Descubriendo permisos del sistema...')
        
        try:
            discovered = PermissionDiscoveryProxy.discover_all_permissions()
            
            total_created = 0
            for perm_type, permissions in discovered.items():
                count = len(permissions)
                total_created += count
                self.stdout.write(f'   ✅ {perm_type.upper()}: {count} permisos')
            
            self.stdout.write(f'   🎯 Total creados: {total_created} permisos')
            
        except Exception as e:
            self.stdout.write(f'   ⚠️  Error en descubrimiento: {e}')

    def create_basic_profiles(self):
        """Crea perfiles básicos del sistema"""
        self.stdout.write('👥 Creando perfiles básicos...')
        
        profiles_data = [
            {
                'name': 'Super Administrador',
                'description': 'Acceso completo a todo el sistema',
                'permissions': 'all'
            },
            {
                'name': 'Administrador',
                'description': 'Acceso administrativo general',
                'permissions': ['menu.*', 'view.*', 'module.config_system']
            },
            {
                'name': 'Editor de Actas',
                'description': 'Acceso completo al módulo de actas',
                'permissions': ['menu.actas', 'view.actas_*', 'module.actas']
            },
            {
                'name': 'Visualizador',
                'description': 'Solo lectura del sistema',
                'permissions': ['menu.dashboard', 'view.*_list', 'view.*_detail']
            },
            {
                'name': 'Secretario Municipal',
                'description': 'Acceso específico para secretario',
                'permissions': ['menu.actas', 'menu.transparencia', 'view.actas_*']
            }
        ]
        
        for profile_data in profiles_data:
            try:
                profile, created = UserProfileProxy.objects.get_or_create(
                    name=profile_data['name'],
                    defaults={
                        'description': profile_data['description'],
                        'is_active': True
                    }
                )
                
                if created or not profile.permissions.exists():
                    self.assign_permissions_to_profile(profile, profile_data['permissions'])
                    self.stdout.write(f'   ✅ Perfil creado: {profile.name}')
                else:
                    self.stdout.write(f'   ℹ️  Perfil existente: {profile.name}')
                    
            except Exception as e:
                self.stdout.write(f'   ⚠️  Error creando perfil {profile_data["name"]}: {e}')

    def assign_permissions_to_profile(self, profile, permissions_config):
        """Asigna permisos a un perfil basado en configuración"""
        if permissions_config == 'all':
            # Asignar todos los permisos
            all_permissions = SystemPermissionProxy.objects.filter(is_active=True)
            profile.permissions.set(all_permissions)
        else:
            # Asignar permisos específicos
            permissions_to_assign = []
            
            for pattern in permissions_config:
                if '*' in pattern:
                    # Patrón con wildcard
                    base_pattern = pattern.replace('*', '')
                    matching_permissions = SystemPermissionProxy.objects.filter(
                        code__startswith=base_pattern,
                        is_active=True
                    )
                    permissions_to_assign.extend(matching_permissions)
                else:
                    # Patrón exacto
                    try:
                        permission = SystemPermissionProxy.objects.get(
                            code=pattern,
                            is_active=True
                        )
                        permissions_to_assign.append(permission)
                    except SystemPermissionProxy.DoesNotExist:
                        pass
            
            profile.permissions.set(permissions_to_assign)

    def assign_profiles_to_users(self):
        """Asigna perfiles automáticamente a usuarios existentes"""
        self.stdout.write('🔗 Asignando perfiles a usuarios...')
        
        try:
            # Asignar perfil Super Administrador a superusuarios
            super_admin_profile = UserProfileProxy.objects.get(name='Super Administrador')
            superusers = User.objects.filter(is_superuser=True)
            
            for user in superusers:
                assignment, created = UserProfileAssignmentProxy.objects.get_or_create(
                    user=user,
                    profile=super_admin_profile,
                    defaults={'assigned_by': None}
                )
                if created:
                    self.stdout.write(f'   ✅ Super Admin asignado a: {user.username}')
            
            # Asignar perfil Visualizador a usuarios normales sin perfil
            viewer_profile = UserProfileProxy.objects.get(name='Visualizador')
            users_without_profile = User.objects.filter(
                is_active=True,
                is_superuser=False,
                userprofileassignment__isnull=True
            )
            
            for user in users_without_profile[:5]:  # Solo los primeros 5
                assignment, created = UserProfileAssignmentProxy.objects.get_or_create(
                    user=user,
                    profile=viewer_profile,
                    defaults={'assigned_by': None}
                )
                if created:
                    self.stdout.write(f'   ✅ Visualizador asignado a: {user.username}')
                    
        except Exception as e:
            self.stdout.write(f'   ⚠️  Error asignando perfiles: {e}')

    def show_summary(self):
        """Muestra resumen del sistema"""
        self.stdout.write('\n📊 RESUMEN DEL SISTEMA:')
        self.stdout.write('=' * 50)
        
        try:
            # Estadísticas generales
            total_permissions = SystemPermissionProxy.objects.filter(is_active=True).count()
            total_profiles = UserProfileProxy.objects.filter(is_active=True).count()
            total_assignments = UserProfileAssignmentProxy.objects.count()
            
            self.stdout.write(f'🔑 Permisos activos: {total_permissions}')
            self.stdout.write(f'👥 Perfiles activos: {total_profiles}')
            self.stdout.write(f'🔗 Asignaciones: {total_assignments}')
            
            # Permisos por tipo
            from apps.config_system.models_proxy import PermissionType
            self.stdout.write('\n📋 Permisos por tipo:')
            for ptype in PermissionType.values:
                count = SystemPermissionProxy.objects.filter(
                    permission_type=ptype,
                    is_active=True
                ).count()
                type_display = PermissionType(ptype).label
                self.stdout.write(f'   {type_display}: {count}')
            
            # Perfiles con más permisos
            self.stdout.write('\n🏆 Perfiles principales:')
            profiles = UserProfileProxy.objects.filter(is_active=True).prefetch_related('permissions')
            for profile in profiles[:3]:
                perm_count = profile.permissions.filter(is_active=True).count()
                self.stdout.write(f'   {profile.name}: {perm_count} permisos')
            
        except Exception as e:
            self.stdout.write(f'   ⚠️  Error mostrando resumen: {e}')
        
        self.stdout.write('=' * 50)
        self.stdout.write('🎉 ¡Sistema de permisos listo para usar!')
        self.stdout.write('   👉 Accede a: http://localhost:8000/config-system/new-permissions/')
        self.stdout.write('   👉 Panel Admin: http://localhost:8000/admin/')
