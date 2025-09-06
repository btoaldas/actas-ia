#!/usr/bin/env python
"""
Probar conexión SMTP real con credenciales Quipux
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import ConfiguracionSMTP
from apps.config_system.smtp_service import smtp_service

print('🔍 === PROBANDO CONEXIÓN SMTP REAL ===')
print()

# Obtener la configuración de Quipux
try:
    config_quipux = ConfiguracionSMTP.objects.get(nombre='Quipux Office365')
    print(f'📧 Probando: {config_quipux.nombre}')
    print(f'   Servidor: {config_quipux.servidor_smtp}:{config_quipux.puerto}')
    print(f'   Usuario: {config_quipux.usuario_smtp}')
    print()
    
    # Probar conexión
    print('🚀 Intentando conectar...')
    exito, mensaje = smtp_service._probar_conexion_smtp(config_quipux)
    
    if exito:
        print(f'✅ CONEXIÓN EXITOSA: {mensaje}')
        
        # Actualizar timestamp de prueba
        from django.utils import timezone
        config_quipux.ultimo_test = timezone.now()
        config_quipux.test_exitoso = True
        config_quipux.mensaje_error = None
        config_quipux.save()
        
        print('📝 Estado actualizado en base de datos')
        
    else:
        print(f'❌ ERROR DE CONEXIÓN: {mensaje}')
        
        # Actualizar con error
        from django.utils import timezone
        config_quipux.ultimo_test = timezone.now()
        config_quipux.test_exitoso = False
        config_quipux.mensaje_error = mensaje[:500]  # Limitar longitud
        config_quipux.save()
        
        print('📝 Error registrado en base de datos')

except ConfiguracionSMTP.DoesNotExist:
    print('❌ No se encontró la configuración de Quipux Office365')
except Exception as e:
    print(f'❌ Error general: {str(e)}')
    import traceback
    traceback.print_exc()

print()
print('🏁 Prueba completada')
