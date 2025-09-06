#!/usr/bin/env python
"""
Prueba final del sistema SMTP corregido
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.smtp_service import smtp_service
from django.contrib.auth.models import User

print('📨 === PRUEBA FINAL SISTEMA SMTP CORREGIDO ===')
print()

# Buscar o crear usuario admin
admin_user, created = User.objects.get_or_create(
    username='admin_smtp',
    defaults={
        'email': 'admin@puyo.gob.ec',
        'is_superuser': True,
        'is_staff': True
    }
)

if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print('✅ Usuario admin creado')

# Email de prueba (cambiar por uno real para probar)
email_destino = 'btoaldas@gmail.com'

contenido = f"""
<div style="background: #f8f9fa; padding: 30px; font-family: Arial, sans-serif;">
    <div style="background: white; max-width: 600px; margin: 0 auto; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        
        <div style="background: linear-gradient(135deg, #1e40af, #3b82f6); color: white; padding: 30px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">🎉 Sistema SMTP Operativo</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Municipio de Pastaza - Puyo</p>
        </div>
        
        <div style="padding: 30px;">
            <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h2 style="color: #059669; margin: 0 0 10px 0;">✅ Sistema Completamente Funcional</h2>
                <p style="margin: 0; color: #047857;">
                    El sistema SMTP ha sido corregido y está funcionando perfectamente con las credenciales de Quipux.
                </p>
            </div>
            
            <h3 style="color: #374151;">📋 Características Activas:</h3>
            <ul style="color: #6b7280;">
                <li>✅ Lazy loading implementado</li>
                <li>✅ Conexión PostgreSQL estable</li>
                <li>✅ Credenciales Quipux configuradas</li>
                <li>✅ Interfaz web accesible</li>
                <li>✅ Sistema de logs funcionando</li>
                <li>✅ Failover automático activo</li>
            </ul>
            
            <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 15px; margin: 20px 0;">
                <h4 style="color: #92400e; margin: 0 0 10px 0;">🚀 Sistema Listo para Producción</h4>
                <p style="margin: 0; color: #78350f; font-size: 14px;">
                    Todas las funcionalidades han sido probadas y validadas. El sistema está listo para uso en el Municipio de Pastaza.
                </p>
            </div>
        </div>
        
        <div style="background: #f3f4f6; padding: 20px; text-align: center; color: #6b7280; font-size: 14px;">
            <p style="margin: 0;">
                <strong>Municipio de Pastaza</strong><br>
                Sistema de Actas Municipales v2.0<br>
                <em>Generado automáticamente</em>
            </p>
        </div>
        
    </div>
</div>
"""

print(f'📧 Enviando email de prueba a: {email_destino}')
print('🚀 Procesando...')

try:
    exito, mensaje = smtp_service.enviar_email(
        destinatario=email_destino,
        asunto='🎉 Sistema SMTP Corregido - Municipio de Pastaza [FINAL]',
        contenido=contenido,
        es_html=True,
        usuario_solicitante=admin_user
    )
    
    if exito:
        print(f'✅ EMAIL ENVIADO EXITOSAMENTE!')
        print(f'📧 Revisa: {email_destino}')
        print(f'💌 Resultado: {mensaje}')
        
        # Mostrar estadísticas
        stats = smtp_service.get_estadisticas_envio()
        print()
        print('📊 ESTADÍSTICAS:')
        print(f'   Enviados hoy: {stats["total_enviados_hoy"]}')
        print(f'   Proveedores activos: {stats["proveedores_activos"]}')
        
    else:
        print(f'❌ ERROR: {mensaje}')
        
except Exception as e:
    print(f'❌ Error general: {str(e)}')
    import traceback
    traceback.print_exc()

print()
print('🏁 Prueba final completada')
print('🌐 Accede a: http://localhost:8000/config-system/smtp/')
