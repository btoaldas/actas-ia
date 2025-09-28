"""
Sistema de notificaciones por email para publicación de actas
Basado en la configuración SMTP del sistema Quipux del GAD Pastaza
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

# Configuración SMTP del GAD Pastaza (desde sistema Quipux)
SMTP_CONFIG = {
    'host': '',
    'port': 587,
    'username': '',
    'password': '',  # En producción debería estar en variables de entorno
    'use_tls': True,
    'from_name': 'Sistema de Actas Municipales - GAD Pastaza'
}

def enviar_notificacion_publicacion(acta_gestion, acta_portal, usuario_publicador):
    """
    Enviar notificación por email cuando se publica un acta
    
    Args:
        acta_gestion: Instancia de GestionActa
        acta_portal: Instancia de ActaMunicipal creada en el portal
        usuario_publicador: Usuario que publicó el acta
    """
    try:
        # Lista de destinatarios (alcalde, secretarios, concejales)
        destinatarios = obtener_destinatarios_notificacion()
        
        if not destinatarios:
            logger.warning("No hay destinatarios configurados para notificaciones")
            return False
        
        # Preparar datos para el template
        contexto = {
            'acta_gestion': acta_gestion,
            'acta_portal': acta_portal,
            'usuario_publicador': usuario_publicador,
            'url_portal': f"http://localhost:8000/acta/{acta_portal.id}/",
            'url_gestion': f"http://localhost:8000/gestion-actas/acta/{acta_gestion.id}/",
            'fecha_publicacion': acta_portal.fecha_publicacion,
            'municipio': 'Municipio de Pastaza'
        }
        
        # Generar contenido del email
        asunto = f"Nueva Acta Publicada: {acta_portal.titulo}"
        contenido_html = generar_contenido_email(contexto)
        contenido_texto = generar_contenido_texto(contexto)
        
        # Enviar email a cada destinatario
        emails_enviados = 0
        for destinatario in destinatarios:
            if enviar_email_smtp(
                destinatario['email'], 
                asunto, 
                contenido_html, 
                contenido_texto
            ):
                emails_enviados += 1
                logger.info(f"Notificación enviada a {destinatario['email']}")
            else:
                logger.error(f"Error enviando notificación a {destinatario['email']}")
        
        logger.info(f"Notificaciones de publicación enviadas: {emails_enviados}/{len(destinatarios)}")
        return emails_enviados > 0
        
    except Exception as e:
        logger.error(f"Error enviando notificaciones de publicación: {str(e)}")
        return False


def obtener_destinatarios_notificacion():
    """
    Obtener lista de destinatarios para notificaciones de publicación
    En producción esto debería venir de una configuración o modelo
    """
    try:
        # Obtener superusuarios y staff activos
        destinatarios = []
        
        # Usuarios con permisos administrativos
        usuarios_admin = User.objects.filter(
            is_active=True,
            is_staff=True,
            email__isnull=False
        ).exclude(email='')
        
        for usuario in usuarios_admin:
            destinatarios.append({
                'email': usuario.email,
                'nombre': usuario.get_full_name() or usuario.username,
                'cargo': 'Administrador' if usuario.is_superuser else 'Personal Municipal'
            })
        
        # Lista adicional de funcionarios municipales (configurable)
        funcionarios_adicionales = [
            {
                'email': 'alcaldia@puyo.gob.ec',
                'nombre': 'Alcaldía Municipal',
                'cargo': 'Alcalde'
            },
            {
                'email': 'secretaria@puyo.gob.ec',
                'nombre': 'Secretaría Municipal',
                'cargo': 'Secretario/a'
            },
            # Agregar más funcionarios según necesidad
        ]
        
        # Solo agregar si no están duplicados
        emails_existentes = {d['email'] for d in destinatarios}
        for funcionario in funcionarios_adicionales:
            if funcionario['email'] not in emails_existentes:
                destinatarios.append(funcionario)
        
        return destinatarios
        
    except Exception as e:
        logger.error(f"Error obteniendo destinatarios: {str(e)}")
        return []


def generar_contenido_email(contexto):
    """Generar contenido HTML del email"""
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nueva Acta Municipal Publicada</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 30px 20px; text-align: center; }}
            .content {{ padding: 30px 20px; }}
            .acta-info {{ background: #f8f9fa; padding: 20px; border-left: 4px solid #3498db; margin: 20px 0; border-radius: 5px; }}
            .button {{ display: inline-block; background: #3498db; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
            .button:hover {{ background: #2980b9; }}
            .footer {{ background: #34495e; color: white; padding: 20px; text-align: center; font-size: 12px; }}
            .metadata {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }}
            .metadata div {{ background: #ecf0f1; padding: 8px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏛️ Nueva Acta Municipal Publicada</h1>
                <p>{contexto['municipio']}</p>
            </div>
            
            <div class="content">
                <h2>Se ha publicado una nueva acta en el Portal Ciudadano</h2>
                
                <div class="acta-info">
                    <h3>{contexto['acta_portal'].titulo}</h3>
                    <div class="metadata">
                        <div><strong>Número:</strong> {contexto['acta_portal'].numero_acta}</div>
                        <div><strong>Fecha Sesión:</strong> {contexto['acta_portal'].fecha_sesion.strftime('%d/%m/%Y')}</div>
                        <div><strong>Publicado por:</strong> {contexto['usuario_publicador'].get_full_name() or contexto['usuario_publicador'].username}</div>
                        <div><strong>Fecha Publicación:</strong> {contexto['fecha_publicacion'].strftime('%d/%m/%Y %H:%M')}</div>
                    </div>
                    
                    <p><strong>Resumen:</strong></p>
                    <p>{contexto['acta_portal'].resumen}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{contexto['url_portal']}" class="button">📖 Ver en Portal Ciudadano</a>
                    <a href="{contexto['url_gestion']}" class="button">⚙️ Ver en Sistema de Gestión</a>
                </div>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>ℹ️ Información:</strong> Esta acta ya está disponible para consulta pública en el Portal Ciudadano. 
                    Los ciudadanos pueden acceder, consultar y descargar los documentos relacionados.
                </div>
            </div>
            
            <div class="footer">
                <p><strong>Sistema de Gestión de Actas Municipales</strong></p>
                <p>Municipio de Pastaza - Ecuador</p>
                <p>Generado automáticamente el {contexto['fecha_publicacion'].strftime('%d de %B de %Y a las %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """


def generar_contenido_texto(contexto):
    """Generar versión en texto plano del email"""
    return f"""
NUEVA ACTA MUNICIPAL PUBLICADA
{contexto['municipio']}
{'=' * 60}

Se ha publicado una nueva acta en el Portal Ciudadano:

TÍTULO: {contexto['acta_portal'].titulo}
NÚMERO: {contexto['acta_portal'].numero_acta}
FECHA DE SESIÓN: {contexto['acta_portal'].fecha_sesion.strftime('%d/%m/%Y')}
PUBLICADO POR: {contexto['usuario_publicador'].get_full_name() or contexto['usuario_publicador'].username}
FECHA DE PUBLICACIÓN: {contexto['fecha_publicacion'].strftime('%d/%m/%Y %H:%M')}

RESUMEN:
{contexto['acta_portal'].resumen}

ENLACES:
- Portal Ciudadano: {contexto['url_portal']}
- Sistema de Gestión: {contexto['url_gestion']}

INFORMACIÓN:
Esta acta ya está disponible para consulta pública en el Portal Ciudadano.
Los ciudadanos pueden acceder, consultar y descargar los documentos relacionados.

---
Sistema de Gestión de Actas Municipales
Municipio de Pastaza - Ecuador
Generado automáticamente el {contexto['fecha_publicacion'].strftime('%d de %B de %Y a las %H:%M:%S')}
"""


def enviar_email_smtp(destinatario, asunto, contenido_html, contenido_texto):
    """
    Enviar email usando la configuración SMTP del GAD Pastaza
    """
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{SMTP_CONFIG['from_name']} <{SMTP_CONFIG['from_email']}>"
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg['Reply-To'] = SMTP_CONFIG['from_email']
        
        # Agregar contenido en texto y HTML
        part1 = MIMEText(contenido_texto, 'plain', 'utf-8')
        part2 = MIMEText(contenido_html, 'html', 'utf-8')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Conectar y enviar
        with smtplib.SMTP(SMTP_CONFIG['host'], SMTP_CONFIG['port']) as server:
            if SMTP_CONFIG['use_tls']:
                server.starttls()
            
            server.login(SMTP_CONFIG['username'], SMTP_CONFIG['password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        logger.error(f"Error enviando email a {destinatario}: {str(e)}")
        return False


def probar_configuracion_smtp():
    """
    Función de prueba para verificar la configuración SMTP
    """
    try:
        email_prueba = "test@example.com"  # Cambiar por email real para pruebas
        asunto = "Prueba de Configuración SMTP - Sistema de Actas"
        contenido = """
        Este es un email de prueba del Sistema de Gestión de Actas Municipales.
        
        Si recibes este mensaje, la configuración SMTP está funcionando correctamente.
        
        ---
        Sistema de Actas Municipales
        Municipio de Pastaza
        """
        
        resultado = enviar_email_smtp(email_prueba, asunto, contenido, contenido)
        
        if resultado:
            print("✅ Configuración SMTP funcionando correctamente")
        else:
            print("❌ Error en la configuración SMTP")
            
        return resultado
        
    except Exception as e:
        print(f"❌ Error probando configuración SMTP: {str(e)}")
        return False


# Función para usar desde Django admin o shell
def enviar_notificacion_test(acta_id):
    """
    Función de prueba para enviar notificación de una acta específica
    """
    try:
        from gestion_actas.models import GestionActa
        
        acta_gestion = GestionActa.objects.get(id=acta_id)
        if not acta_gestion.acta_portal:
            print("❌ Esta acta no está publicada en el portal")
            return False
        
        usuario = acta_gestion.usuario_editor or User.objects.filter(is_superuser=True).first()
        
        resultado = enviar_notificacion_publicacion(
            acta_gestion, 
            acta_gestion.acta_portal, 
            usuario
        )
        
        if resultado:
            print("✅ Notificación de prueba enviada")
        else:
            print("❌ Error enviando notificación de prueba")
            
        return resultado
        
    except Exception as e:
        print(f"❌ Error en notificación de prueba: {str(e)}")
        return False