from django.core.management.base import BaseCommand
from django.db import transaction
from apps.config_system.models_proxy import (
    SystemPermissionProxy as SystemPermission, 
    UserProfileProxy as UserProfile, 
    PermissionDiscoveryProxy as PermissionDiscovery,
    PermissionType
)


class Command(BaseCommand):
    help = 'Descubre y crea automáticamente todos los permisos del sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Elimina todos los permisos auto-generados y los vuelve a crear',
        )
        parser.add_argument(
            '--create-admin-profile',
            action='store_true',
            help='Crea un perfil de administrador con todos los permisos',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando descubrimiento de permisos del sistema...')
        )

        if options['recreate']:
            self.stdout.write('⚠️  Eliminando permisos auto-generados existentes...')
            deleted_count = SystemPermission.objects.filter(auto_generated=True).delete()[0]
            self.stdout.write(
                self.style.WARNING(f'   Eliminados: {deleted_count} permisos')
            )

        with transaction.atomic():
            # Descubrir todos los permisos
            discovered = PermissionDiscovery.discover_all_permissions()
            
            # Mostrar resultados
            total_created = 0
            
            self.stdout.write('\n📋 RESUMEN DE PERMISOS CREADOS:')
            self.stdout.write('=' * 50)
            
            for perm_type, permissions in discovered.items():
                count = len(permissions)
                total_created += count
                
                if count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {perm_type.upper()}: {count} permisos')
                    )
                    
                    for perm in permissions:
                        self.stdout.write(f'   - {perm.code}: {perm.name}')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  {perm_type.upper()}: 0 permisos')
                    )
            
            self.stdout.write('=' * 50)
            self.stdout.write(
                self.style.SUCCESS(f'🎯 TOTAL CREADO: {total_created} permisos')
            )

        # Crear perfil de administrador si se solicita
        if options['create_admin_profile']:
            self.create_admin_profile()

        # Mostrar estadísticas finales
        self.show_final_stats()

    def create_admin_profile(self):
        """Crea un perfil de administrador con todos los permisos"""
        self.stdout.write('\n👑 Creando perfil de Administrador...')
        
        admin_profile, created = UserProfile.objects.get_or_create(
            name='Administrador',
            defaults={
                'description': 'Perfil con acceso completo a todo el sistema',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('✅ Perfil "Administrador" creado')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️  Perfil "Administrador" ya existía')
            )
        
        # Asignar todos los permisos activos
        all_permissions = SystemPermission.objects.filter(is_active=True)
        admin_profile.permissions.set(all_permissions)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Asignados {all_permissions.count()} permisos al perfil Administrador')
        )

    def show_final_stats(self):
        """Muestra estadísticas finales del sistema de permisos"""
        self.stdout.write('\n📊 ESTADÍSTICAS DEL SISTEMA:')
        self.stdout.write('=' * 40)
        
        # Contar por tipo
        stats = {}
        for perm_type in PermissionType.values:
            count = SystemPermission.objects.filter(
                permission_type=perm_type,
                is_active=True
            ).count()
            stats[perm_type] = count
        
        total_permissions = SystemPermission.objects.filter(is_active=True).count()
        total_profiles = UserProfile.objects.filter(is_active=True).count()
        
        for perm_type, count in stats.items():
            type_display = PermissionType(perm_type).label
            self.stdout.write(f'📂 {type_display}: {count}')
        
        self.stdout.write('=' * 40)
        self.stdout.write(f'🔑 Total Permisos Activos: {total_permissions}')
        self.stdout.write(f'👥 Total Perfiles Activos: {total_profiles}')
        
        self.stdout.write('\n🚀 ¡Sistema de permisos listo!')
        self.stdout.write(
            self.style.SUCCESS('   Ejecuta este comando periódicamente para mantener actualizados los permisos.')
        )
