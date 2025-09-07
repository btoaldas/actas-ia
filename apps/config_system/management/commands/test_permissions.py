from django.core.management.base import BaseCommand
from apps.config_system.models_proxy import (
    SystemPermissionProxy,
    UserProfileProxy,
    PermissionType
)


class Command(BaseCommand):
    help = 'Prueba simple del sistema de permisos'

    def handle(self, *args, **options):
        self.stdout.write('🧪 Probando el sistema de permisos...')
        
        try:
            # Probar modelos
            permissions_count = SystemPermissionProxy.objects.count()
            profiles_count = UserProfileProxy.objects.count()
            
            self.stdout.write(f'✅ Permisos en BD: {permissions_count}')
            self.stdout.write(f'✅ Perfiles en BD: {profiles_count}')
            
            # Probar PermissionType
            self.stdout.write(f'✅ Tipos de permisos: {list(PermissionType.values)}')
            
            self.stdout.write('🎉 ¡Sistema funcionando correctamente!')
            
        except Exception as e:
            self.stdout.write(f'❌ Error: {str(e)}')
            import traceback
            self.stdout.write(traceback.format_exc())
