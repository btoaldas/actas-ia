#!/usr/bin/env python
"""
Script simple para verificar el estado del sistema después de la corrección
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print('🔧 === VERIFICANDO SISTEMA DESPUÉS DE CORRECCIÓN ===')
print()

try:
    # Verificar importación del servicio SMTP
    from apps.config_system.smtp_service import smtp_service
    print('✅ Servicio SMTP importado correctamente')
    
    # Verificar modelos
    from apps.config_system.models import ConfiguracionSMTP, ConfiguracionEmail, LogEnvioEmail
    print('✅ Modelos importados correctamente')
    
    # Verificar acceso a la base de datos
    smtp_count = ConfiguracionSMTP.objects.count()
    print(f'✅ ConfiguracionSMTP: {smtp_count} registros')
    
    email_count = ConfiguracionEmail.objects.count()
    print(f'✅ ConfiguracionEmail: {email_count} registros')
    
    logs_count = LogEnvioEmail.objects.count()
    print(f'✅ LogEnvioEmail: {logs_count} registros')
    
    # Probar estadísticas
    stats = smtp_service.get_estadisticas_envio()
    print(f'✅ Estadísticas: {stats["proveedores_activos"]} proveedores activos')
    
    print()
    print('🎉 ¡Sistema funcionando correctamente!')
    
except Exception as e:
    print(f'❌ Error: {str(e)}')
    import traceback
    traceback.print_exc()
