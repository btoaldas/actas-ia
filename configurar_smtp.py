#!/usr/bin/env python
"""
Script para configurar SMTP por defecto con Office 365
Sistema de Actas Municipales - Municipio de Pastaza
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import ConfiguracionSMTP, ConfiguracionEmail
from django.contrib.auth.models import User


def crear_configuracion_smtp_office365():
    """Crea configuración SMTP por defecto para Office 365"""
    
    print("🔧 === CONFIGURANDO SMTP OFFICE 365 POR DEFECTO ===")
    print()
    
    # Obtener usuario admin
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = None
        print("⚠️  No se encontró usuario admin, creando configuración sin usuario")
    
    # Crear configuración Office 365 por defecto
    config_office365, created = ConfiguracionSMTP.objects.get_or_create(
        nombre="Office 365 Municipio Pastaza",
        defaults={
            'proveedor': 'office365',
            'activo': False,  # Inactivo hasta que se configure
            'por_defecto': True,
            'prioridad': 1,
            'servidor_smtp': 'smtp-mail.outlook.com',
            'puerto': 587,
            'usuario_smtp': 'actas@puyo.gob.ec',  # Cambiar por email real
            'password_smtp': 'CONFIGURAR_PASSWORD',  # Placeholder
            'usa_tls': True,
            'usa_ssl': False,
            'email_remitente': 'actas@puyo.gob.ec',
            'nombre_remitente': 'Sistema de Actas Municipales - Pastaza',
            'limite_diario': 500,
            'creado_por': admin_user,
        }
    )
    
    if created:
        print(f"✅ Configuración Office 365 creada: {config_office365.nombre}")
    else:
        print(f"ℹ️  Configuración Office 365 ya existe: {config_office365.nombre}")
    
    # Crear configuración Gmail como backup
    config_gmail, created = ConfiguracionSMTP.objects.get_or_create(
        nombre="Gmail Backup Municipio",
        defaults={
            'proveedor': 'gmail',
            'activo': False,
            'por_defecto': False,
            'prioridad': 2,
            'servidor_smtp': 'smtp.gmail.com',
            'puerto': 587,
            'usuario_smtp': 'sistema.actas.puyo@gmail.com',  # Cambiar por email real
            'password_smtp': 'CONFIGURAR_APP_PASSWORD',  # Placeholder
            'usa_tls': True,
            'usa_ssl': False,
            'email_remitente': 'sistema.actas.puyo@gmail.com',
            'nombre_remitente': 'Sistema de Actas - Municipio de Pastaza',
            'limite_diario': 100,  # Gmail tiene límites más restrictivos
            'creado_por': admin_user,
        }
    )
    
    if created:
        print(f"✅ Configuración Gmail backup creada: {config_gmail.nombre}")
    else:
        print(f"ℹ️  Configuración Gmail backup ya existe: {config_gmail.nombre}")
    
    print()
    return config_office365, config_gmail


def crear_configuracion_email_global():
    """Crea configuración global de emails"""
    
    print("📧 === CONFIGURANDO SISTEMA GLOBAL DE EMAILS ===")
    print()
    
    config_email, created = ConfiguracionEmail.objects.get_or_create()
    
    if created:
        print("✅ Configuración global de email creada")
    else:
        print("ℹ️  Configuración global de email ya existe")
    
    # Actualizar configuraciones específicas para Pastaza
    config_email.nombre_aplicacion = "Sistema de Actas Municipales - Pastaza"
    config_email.email_respuesta = "noreply@puyo.gob.ec"
    config_email.email_soporte = "soporte.actas@puyo.gob.ec"
    config_email.url_sistema = "http://localhost:8000"
    config_email.url_publica = "http://puyo.gob.ec"
    
    # Template personalizado para Pastaza
    config_email.template_html_base = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{asunto}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
        .container { max-width: 600px; margin: 0 auto; background-color: #ffffff; }
        .header { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 30px 20px; text-align: center; }
        .content { padding: 30px 20px; }
        .footer { background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666; border-top: 1px solid #e9ecef; }
        .logo { max-width: 200px; height: auto; margin-bottom: 15px; }
        .badge { background-color: #10b981; color: white; padding: 8px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .divider { border-top: 2px solid #e5e7eb; margin: 20px 0; }
        h1 { margin: 0; font-size: 28px; font-weight: 600; }
        h2 { color: #1e3a8a; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
        .highlight { background-color: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {% if logo_url %}<img src="{{logo_url}}" alt="Logo Municipio de Pastaza" class="logo">{% endif %}
            <h1>{{nombre_aplicacion}}</h1>
            <div class="badge">Municipio de Pastaza</div>
        </div>
        <div class="content">
            {{contenido}}
        </div>
        <div class="footer">
            {{pie_pagina}}
        </div>
    </div>
</body>
</html>
    """
    
    # Pie de página personalizado
    config_email.pie_pagina = """
<p><strong>🏛️ Municipio de Pastaza</strong><br>
<strong>📍 Dirección:</strong> Francisco de Orellana y 9 de Octubre<br>
Puyo, Pastaza - Ecuador<br>
<strong>📞 Teléfono:</strong> (03) 2885-133 | <strong>📧 Email:</strong> info@puyo.gob.ec<br>
<strong>🌐 Web:</strong> <a href="http://puyo.gob.ec">www.puyo.gob.ec</a></p>

<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e9ecef;">
    <p><small><strong>🔒 Aviso de Confidencialidad:</strong> Este mensaje es confidencial y está dirigido exclusivamente al destinatario indicado. Si usted no es el destinatario previsto, por favor no lea, copie o distribuya este mensaje.</small></p>
    <p><small><strong>🤖 Mensaje Automático:</strong> Este email fue generado automáticamente por el Sistema de Actas Municipales. Por favor no responder directamente a este email.</small></p>
    <p><small><strong>💚 Compromiso Ambiental:</strong> Antes de imprimir este email, piense en el medio ambiente.</small></p>
</div>

<div style="text-align: center; margin-top: 20px;">
    <small style="color: #9ca3af;">
        © {{ "now"|date:"Y" }} Municipio de Pastaza | Sistema de Actas Municipales v2.0
    </small>
</div>
    """
    
    config_email.save()
    
    print(f"✅ Configuración actualizada:")
    print(f"   • Nombre de aplicación: {config_email.nombre_aplicacion}")
    print(f"   • Email de no respuesta: {config_email.email_respuesta}")
    print(f"   • Email de soporte: {config_email.email_soporte}")
    print(f"   • URL del sistema: {config_email.url_sistema}")
    print(f"   • URL pública: {config_email.url_publica}")
    print()
    
    return config_email


def mostrar_instrucciones_configuracion(config_office365, config_gmail):
    """Muestra instrucciones para completar la configuración"""
    
    print("📋 === INSTRUCCIONES DE CONFIGURACIÓN ===")
    print()
    print("Para completar la configuración SMTP, sigue estos pasos:")
    print()
    
    print("1️⃣  CONFIGURAR OFFICE 365:")
    print("   • Ve a: http://localhost:8000/config-system/smtp/")
    print(f"   • Edita la configuración: {config_office365.nombre}")
    print("   • Actualiza los siguientes campos:")
    print("     - Usuario SMTP: tu-email@puyo.gob.ec")
    print("     - Contraseña SMTP: tu-contraseña-de-aplicacion")
    print("     - Email remitente: tu-email@puyo.gob.ec")
    print("   • Activa la configuración marcando 'Activo'")
    print("   • Prueba el envío con el botón 'Probar'")
    print()
    
    print("2️⃣  CONFIGURAR GMAIL BACKUP (OPCIONAL):")
    print("   • Ve a: https://myaccount.google.com/apppasswords")
    print("   • Genera una contraseña de aplicación")
    print(f"   • Edita la configuración: {config_gmail.nombre}")
    print("   • Actualiza usuario y contraseña")
    print("   • Activa como backup")
    print()
    
    print("3️⃣  PROBAR EL SISTEMA:")
    print("   • Ve a: http://localhost:8000/config-system/email-test/")
    print("   • Envía un email de prueba")
    print("   • Verifica que llegue correctamente")
    print("   • Revisa los logs en: http://localhost:8000/config-system/email-logs/")
    print()
    
    print("4️⃣  CONFIGURACIONES ADICIONALES:")
    print("   • Config. General: http://localhost:8000/config-system/email-config/")
    print("   • Estadísticas: http://localhost:8000/config-system/smtp-stats/")
    print("   • Dashboard: http://localhost:8000/config-system/")
    print()


def main():
    """Función principal"""
    print("🚀 === CONFIGURADOR SMTP SISTEMA ACTAS MUNICIPALES ===")
    print("     Municipio de Pastaza - Puyo, Ecuador")
    print("=" * 60)
    print()
    
    try:
        # Crear configuraciones SMTP
        config_office365, config_gmail = crear_configuracion_smtp_office365()
        
        # Crear configuración global de emails
        config_email = crear_configuracion_email_global()
        
        # Mostrar instrucciones
        mostrar_instrucciones_configuracion(config_office365, config_gmail)
        
        print("🎉 === CONFIGURACIÓN INICIAL COMPLETADA ===")
        print()
        print("✅ El sistema SMTP ha sido configurado con:")
        print(f"   • {ConfiguracionSMTP.objects.count()} proveedores SMTP")
        print(f"   • Configuración global de emails")
        print(f"   • Templates personalizados para Pastaza")
        print()
        print("⚠️  IMPORTANTE: Recuerda actualizar las credenciales SMTP reales")
        print("   antes de activar los proveedores.")
        print()
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
