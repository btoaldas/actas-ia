#!/usr/bin/env python
"""
Script para configurar SMTP con credenciales reales del sistema Quipux
Sistema de Actas Municipales - Municipio de Pastaza
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import ConfiguracionSMTP, ConfiguracionEmail
from django.contrib.auth.models import User
from django.utils import timezone


def configurar_smtp_quipux():
    """Configura SMTP con las credenciales reales del sistema Quipux"""
    print("🔧 === CONFIGURANDO SMTP CON CREDENCIALES QUIPUX ===")
    print()
    
    # Primero eliminar configuraciones existentes para evitar duplicados
    ConfiguracionSMTP.objects.all().delete()
    print("🗑️  Configuraciones anteriores eliminadas")
    
    # Crear configuración principal con credenciales de Quipux
    config_quipux = ConfiguracionSMTP.objects.create(
        nombre="Office 365 Quipux - Producción",
        proveedor="office365",
        servidor_smtp="smtp.office365.com",
        puerto=587,
        usa_tls=True,
        usa_ssl=False,
        usuario_smtp="quipux@puyo.gob.ec",
        password_smtp="Mpuyo2016",  # Credencial real del sistema
        email_remitente="quipux@puyo.gob.ec",
        nombre_remitente="Sistema Quipux del GADMPastaza",
        activo=True,
        por_defecto=True,
        prioridad=1,
        limite_diario=500,  # Límite generoso para Office 365
        configuracion_adicional={
            "timeout": 30,
            "charset": "UTF-8",
            "authentication": "login",
            "debug_level": 0
        }
    )
    
    print(f"✅ Configuración principal creada: {config_quipux.nombre}")
    
    # Crear configuración de respaldo (misma cuenta pero menor prioridad)
    config_backup = ConfiguracionSMTP.objects.create(
        nombre="Office 365 Quipux - Respaldo",
        proveedor="office365",
        servidor_smtp="smtp.office365.com",
        puerto=587,
        usa_tls=True,
        usa_ssl=False,
        usuario_smtp="quipux@puyo.gob.ec",
        password_smtp="Mpuyo2016",
        email_remitente="quipux@puyo.gob.ec",
        nombre_remitente="Sistema de Actas Municipales - Pastaza",
        activo=True,
        por_defecto=False,
        prioridad=2,
        limite_diario=300,
        configuracion_adicional={
            "timeout": 45,
            "charset": "UTF-8",
            "authentication": "login",
            "debug_level": 1
        }
    )
    
    print(f"✅ Configuración de respaldo creada: {config_backup.nombre}")
    
    # Crear/actualizar configuración global de emails
    config_email, created = ConfiguracionEmail.objects.get_or_create(
        defaults={
            'nombre_aplicacion': 'Sistema de Actas Municipales',
            'logo_url': 'https://puyo.gob.ec/images/logo-municipio.png',
            'sitio_web': 'https://puyo.gob.ec',
            'direccion_fisica': 'Municipio de Pastaza, Puyo, Ecuador',
            'telefono_contacto': '(03) 2885-174',
            'email_soporte': 'quipux@puyo.gob.ec',
            'pie_pagina': '''
                <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-top: 3px solid #28a745;">
                    <table width="100%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td align="center">
                                <img src="https://puyo.gob.ec/images/logo-municipio.png" alt="Municipio de Pastaza" style="max-height: 60px;">
                                <h3 style="color: #28a745; margin: 10px 0;">Municipio de Pastaza</h3>
                                <p style="margin: 5px 0; color: #6c757d;">
                                    <strong>Dirección:</strong> Av. Alberto Zambrano Palacios y 27 de Febrero<br>
                                    <strong>Teléfono:</strong> (03) 2885-174 | <strong>Email:</strong> quipux@puyo.gob.ec<br>
                                    <strong>Web:</strong> <a href="https://puyo.gob.ec" style="color: #28a745;">www.puyo.gob.ec</a>
                                </p>
                                <p style="font-size: 12px; color: #6c757d; margin-top: 15px;">
                                    <em>Sistema de Actas Municipales - Generando transparencia y eficiencia</em>
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>
            ''',
            'template_html': '''
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{{asunto}}</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; }
                        .header { background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 20px; text-align: center; }
                        .content { padding: 30px; }
                        .footer { background-color: #f8f9fa; border-top: 3px solid #28a745; }
                        .btn { display: inline-block; padding: 12px 24px; background-color: #28a745; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }
                        .alert { padding: 15px; border-radius: 5px; margin: 15px 0; }
                        .alert-info { background-color: #d1ecf1; border-color: #bee5eb; color: #0c5460; }
                        .alert-success { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>{{nombre_aplicacion}}</h1>
                            <p>Municipio de Pastaza - Puyo, Ecuador</p>
                        </div>
                        <div class="content">
                            {{contenido}}
                        </div>
                        {{pie_pagina}}
                    </div>
                </body>
                </html>
            ''',
            'activo': True
        }
    )
    
    if created:
        print("✅ Configuración global de emails creada")
    else:
        print("✅ Configuración global de emails actualizada")
    
    print()
    print("🎯 === CONFIGURACIÓN COMPLETADA ===")
    print(f"📧 Email remitente: quipux@puyo.gob.ec")
    print(f"🏢 Nombre remitente: Sistema Quipux del GADMPastaza")
    print(f"🌐 Servidor: smtp.office365.com:587")
    print(f"🔐 Autenticación: TLS activada")
    print(f"📊 Límite diario: 500 emails")
    print()
    
    return config_quipux, config_backup


def probar_conexion_inmediata():
    """Prueba inmediatamente la conexión con las credenciales configuradas"""
    print("🔍 === PROBANDO CONEXIÓN INMEDIATA ===")
    print()
    
    from apps.config_system.smtp_service import smtp_service
    
    config = ConfiguracionSMTP.objects.filter(por_defecto=True).first()
    if not config:
        print("❌ No se encontró configuración por defecto")
        return False
    
    print(f"Probando configuración: {config.nombre}")
    print(f"Servidor: {config.servidor_smtp}:{config.puerto}")
    print(f"Usuario: {config.usuario_smtp}")
    print("🚀 Iniciando prueba de conexión...")
    
    exito, mensaje = smtp_service._probar_conexion_smtp(config)
    
    if exito:
        print(f"✅ CONEXIÓN EXITOSA: {mensaje}")
        
        # Actualizar el registro de prueba en la BD
        config.ultimo_test = timezone.now()
        config.test_exitoso = True
        config.mensaje_error = None
        config.save()
        
        return True
    else:
        print(f"❌ ERROR DE CONEXIÓN: {mensaje}")
        
        # Actualizar el registro de error en la BD
        config.ultimo_test = timezone.now()
        config.test_exitoso = False
        config.mensaje_error = mensaje
        config.save()
        
        return False


def enviar_email_prueba_inmediato():
    """Envía un email de prueba inmediatamente"""
    print("📨 === ENVIANDO EMAIL DE PRUEBA ===")
    print()
    
    # Buscar usuario administrador
    admin_user = User.objects.filter(is_superuser=True).first()
    email_destino = "quipux@puyo.gob.ec"  # Usar el mismo email del sistema
    
    print(f"📧 Enviando email de prueba a: {email_destino}")
    print("🚀 Procesando envío...")
    
    from apps.config_system.smtp_service import smtp_service
    from django.utils import timezone
    
    contenido = f"""
    <div class="alert alert-success">
        <h2>🎉 ¡Configuración SMTP Exitosa!</h2>
        <p>El sistema SMTP ha sido configurado correctamente con las credenciales del sistema Quipux.</p>
    </div>
    
    <h3>📋 Detalles de la Configuración:</h3>
    <ul>
        <li><strong>Servidor:</strong> smtp.office365.com:587</li>
        <li><strong>Usuario:</strong> quipux@puyo.gob.ec</li>
        <li><strong>Seguridad:</strong> TLS habilitado</li>
        <li><strong>Fecha de configuración:</strong> {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}</li>
    </ul>
    
    <div class="alert alert-info">
        <h4>✅ Funcionalidades Disponibles:</h4>
        <ul>
            <li>📤 Envío de invitaciones a eventos municipales</li>
            <li>📋 Notificaciones de actas y documentos</li>
            <li>👥 Comunicaciones con funcionarios</li>
            <li>🔄 Sistema de failover automático</li>
            <li>📊 Estadísticas y logs de envío</li>
            <li>🧪 Herramientas de prueba y diagnóstico</li>
        </ul>
    </div>
    
    <p>
        <a href="http://localhost:8000/config-system/smtp/" class="btn">
            🔧 Acceder al Panel de Control SMTP
        </a>
    </p>
    
    <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <h4>🚀 Próximos Pasos:</h4>
        <ol>
            <li>Acceder al panel de administración SMTP</li>
            <li>Configurar límites y preferencias adicionales</li>
            <li>Probar envío a diferentes destinatarios</li>
            <li>Revisar logs y estadísticas</li>
            <li>Integrar con eventos municipales</li>
        </ol>
    </div>
    """
    
    variables = {
        'fecha_actual': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
        'nombre_aplicacion': 'Sistema de Actas Municipales - Pastaza'
    }
    
    exito, mensaje = smtp_service.enviar_email(
        destinatario=email_destino,
        asunto="🎉 Sistema SMTP Configurado - Municipio de Pastaza",
        contenido=contenido,
        es_html=True,
        variables_template=variables,
        usuario_solicitante=admin_user
    )
    
    if exito:
        print(f"✅ EMAIL ENVIADO EXITOSAMENTE")
        print(f"📧 Revisa la bandeja de: {email_destino}")
        print(f"💌 Mensaje: {mensaje}")
    else:
        print(f"❌ ERROR ENVIANDO EMAIL: {mensaje}")
    
    return exito


def main():
    """Función principal"""
    print("🚀 === CONFIGURACIÓN SMTP CON CREDENCIALES QUIPUX ===")
    print("   Sistema de Actas Municipales")
    print("   Municipio de Pastaza - Puyo, Ecuador")
    print("=" * 60)
    print()
    
    try:
        # 1. Configurar SMTP
        config_principal, config_backup = configurar_smtp_quipux()
        
        # 2. Probar conexión inmediatamente
        if probar_conexion_inmediata():
            print()
            
            # 3. Enviar email de prueba
            if enviar_email_prueba_inmediato():
                print()
                print("🎉 === CONFIGURACIÓN COMPLETADA EXITOSAMENTE ===")
                print()
                print("📋 RESUMEN:")
                print("✅ Credenciales SMTP configuradas")
                print("✅ Conexión al servidor verificada")
                print("✅ Email de prueba enviado")
                print("✅ Sistema listo para producción")
                print()
                print("🔗 ACCESOS RÁPIDOS:")
                print("🌐 Panel SMTP: http://localhost:8000/config-system/smtp/")
                print("📊 Dashboard: http://localhost:8000/")
                print("🧪 Pruebas: python probar_smtp.py")
                print()
            else:
                print("⚠️  Conexión OK pero fallo en envío de email")
        else:
            print("❌ Error en la conexión SMTP")
            print("🔍 Revisa las credenciales y la conectividad")
    
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
