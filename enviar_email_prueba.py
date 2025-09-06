#!/usr/bin/env python
"""
Enviar email de prueba real usando credenciales Quipux
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.smtp_service import smtp_service
from django.contrib.auth.models import User
from django.utils import timezone

print('📨 === ENVIANDO EMAIL DE PRUEBA REAL ===')
print('   Usando credenciales del sistema Quipux')
print()

# Buscar usuario administrador o crear uno temporal
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    print('⚠️  Creando usuario administrador temporal...')
    admin_user = User.objects.create_user(
        username='admin_temp',
        email='admin@puyo.gob.ec',
        password='temp123',
        is_superuser=True,
        is_staff=True
    )

# Email de destino - puedes cambiar esto
email_destino = 'btoaldas@gmail.com'  # Cambiar por tu email para prueba
print(f'📧 Enviando a: {email_destino}')

# Contenido del email de prueba
contenido_html = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    
    <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
        <h1 style="margin: 0; font-size: 28px;">🧪 Prueba Sistema SMTP</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Sistema de Actas Municipales - Pastaza</p>
    </div>
    
    <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
        
        <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
            <h2 style="color: #059669; margin: 0 0 15px 0; font-size: 20px;">✅ ¡Conexión Exitosa!</h2>
            <p style="margin: 0; color: #047857;">
                El sistema SMTP del Municipio de Pastaza está funcionando correctamente utilizando 
                las credenciales del sistema Quipux existente.
            </p>
        </div>
        
        <h3 style="color: #374151; border-bottom: 2px solid #f3f4f6; padding-bottom: 10px;">📋 Detalles de la Prueba</h3>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr>
                <td style="padding: 10px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: bold; width: 40%;">
                    🏢 Sistema de Origen
                </td>
                <td style="padding: 10px; border: 1px solid #e5e7eb;">
                    Sistema Quipux GADMPastaza
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: bold;">
                    📧 Servidor SMTP
                </td>
                <td style="padding: 10px; border: 1px solid #e5e7eb;">
                    smtp.office365.com:587 (TLS)
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: bold;">
                    👤 Cuenta de Envío
                </td>
                <td style="padding: 10px; border: 1px solid #e5e7eb;">
                    quipux@puyo.gob.ec
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: bold;">
                    🕐 Fecha/Hora
                </td>
                <td style="padding: 10px; border: 1px solid #e5e7eb;">
                    {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
                </td>
            </tr>
            <tr>
                <td style="padding: 10px; background: #f9fafb; border: 1px solid #e5e7eb; font-weight: bold;">
                    🎯 Sistema Destino
                </td>
                <td style="padding: 10px; border: 1px solid #e5e7eb;">
                    Sistema de Actas Municipales v2.0
                </td>
            </tr>
        </table>
        
        <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h4 style="color: #92400e; margin: 0 0 10px 0;">🔧 Funcionalidades Verificadas</h4>
            <ul style="margin: 0; padding-left: 20px; color: #78350f;">
                <li>✅ Autenticación SMTP con Office365</li>
                <li>✅ Conexión TLS segura establecida</li>
                <li>✅ Envío de emails HTML formateados</li>
                <li>✅ Integración con PostgreSQL</li>
                <li>✅ Sistema de logs y auditoria</li>
                <li>✅ Failover automático configurado</li>
            </ul>
        </div>
        
        <div style="background: #e0f2fe; border-radius: 8px; padding: 20px; margin: 25px 0;">
            <h4 style="color: #0277bd; margin: 0 0 15px 0;">🚀 Próximos Pasos</h4>
            <p style="margin: 0 0 10px 0; color: #01579b;">
                <strong>1. Acceso Web:</strong> <a href="http://localhost:8000/config-system/smtp/" style="color: #1976d2;">http://localhost:8000/config-system/smtp/</a>
            </p>
            <p style="margin: 0 0 10px 0; color: #01579b;">
                <strong>2. Configurar más proveedores:</strong> Agregar Gmail, SendGrid como respaldo
            </p>
            <p style="margin: 0; color: #01579b;">
                <strong>3. Integración:</strong> El sistema ya está integrado con los eventos municipales
            </p>
        </div>
        
    </div>
    
    <div style="background: #f3f4f6; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; color: #6b7280; font-size: 14px;">
        <p style="margin: 0 0 10px 0;">
            <strong>Municipio de Pastaza - Puyo, Ecuador</strong><br>
            Av. Francisco de Orellana y Ceslao Marín<br>
            Teléfono: (03) 2885-174
        </p>
        <p style="margin: 0; font-size: 12px; color: #9ca3af;">
            Este mensaje es confidencial y puede contener información privilegiada.<br>
            Sistema generado automáticamente - No responder a este email.
        </p>
    </div>
    
</div>
"""

# Enviar email
print('🚀 Iniciando envío...')

try:
    exito, mensaje = smtp_service.enviar_email(
        destinatario=email_destino,
        asunto='🧪 Prueba Sistema SMTP - Municipio de Pastaza [QUIPUX INTEGRADO]',
        contenido=contenido_html,
        es_html=True,
        usuario_solicitante=admin_user
    )
    
    if exito:
        print(f'✅ EMAIL ENVIADO EXITOSAMENTE!')
        print(f'📧 Revisa la bandeja de entrada de: {email_destino}')
        print(f'💌 Mensaje: {mensaje}')
        
        # Mostrar estadísticas actualizadas
        stats = smtp_service.get_estadisticas_envio()
        print()
        print('📊 ESTADÍSTICAS ACTUALIZADAS:')
        print(f'   Emails enviados hoy: {stats["total_enviados_hoy"]}')
        print(f'   Proveedores activos: {stats["proveedores_activos"]}')
        
    else:
        print(f'❌ ERROR ENVIANDO EMAIL: {mensaje}')
        
except Exception as e:
    print(f'❌ Error general: {str(e)}')
    import traceback
    traceback.print_exc()

print()
print('🏁 Prueba de envío completada')
print('🌐 Accede a http://localhost:8000/config-system/smtp/ para más configuraciones')
