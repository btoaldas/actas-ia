"""
Servicio de envío de emails con múltiples proveedores SMTP y failover
Sistema para el Municipio de Pastaza
"""
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import Template, Context
from django.utils import timezone
from typing import List, Optional, Dict, Any
import logging

from .models import ConfiguracionSMTP, ConfiguracionEmail, LogEnvioEmail

logger = logging.getLogger(__name__)


class SMTPService:
    """Servicio principal para envío de emails con failover"""
    
    def __init__(self):
        self._configuracion_email = None
    
    def _get_configuracion_email(self) -> ConfiguracionEmail:
        """Obtiene la configuración global de email (lazy loading)"""
        if self._configuracion_email is None:
            try:
                config, created = ConfiguracionEmail.objects.get_or_create()
                if created:
                    logger.info("Configuración de email creada por primera vez")
                self._configuracion_email = config
            except Exception as e:
                logger.warning(f"No se pudo cargar configuración de email: {e}")
                # Retornar configuración por defecto si hay error
                return None
        return self._configuracion_email
    
    def _get_proveedores_activos(self) -> List[ConfiguracionSMTP]:
        """Obtiene proveedores SMTP activos ordenados por prioridad"""
        return ConfiguracionSMTP.objects.filter(
            activo=True
        ).order_by('prioridad', 'por_defecto')
    
    def _get_proveedor_por_defecto(self) -> Optional[ConfiguracionSMTP]:
        """Obtiene el proveedor SMTP por defecto"""
        try:
            return ConfiguracionSMTP.objects.filter(
                activo=True, 
                por_defecto=True
            ).first()
        except ConfiguracionSMTP.DoesNotExist:
            return None
    
    def _generar_html_desde_template(self, contenido: str, asunto: str, 
                                   variables_extra: Dict[str, Any] = None) -> str:
        """Genera HTML desde el template base"""
        config = self._get_configuracion_email()
        
        # Si no hay configuración, usar template básico
        if config is None:
            return f"""
            <html>
            <body>
                <h1>{asunto}</h1>
                <div>{contenido}</div>
                <footer>
                    <p>Sistema de Actas Municipales - Pastaza</p>
                </footer>
            </body>
            </html>
            """
        
        template = Template(config.template_html_base)
        
        # Marcar el contenido como safe para que Django no lo escape
        from django.utils.safestring import mark_safe
        contenido_safe = mark_safe(contenido)
        
        context_data = {
            'contenido': contenido_safe,
            'asunto': asunto,
            'nombre_aplicacion': config.nombre_aplicacion,
            'pie_pagina': config.pie_pagina,
            'url_sistema': config.url_sistema,
            'logo_url': config.logo_email.url if config.logo_email else None,
        }
        
        if variables_extra:
            context_data.update(variables_extra)
        
        context = Context(context_data)
        return template.render(context)
    
    def _probar_conexion_smtp(self, config: ConfiguracionSMTP) -> tuple[bool, str]:
        """Prueba la conexión SMTP con una configuración específica"""
        try:
            # Crear conexión SMTP
            if config.usa_ssl:
                server = smtplib.SMTP_SSL(config.servidor_smtp, config.puerto)
            else:
                server = smtplib.SMTP(config.servidor_smtp, config.puerto)
            
            if config.usa_tls and not config.usa_ssl:
                server.starttls()
            
            # Autenticar
            server.login(config.usuario_smtp, config.password_smtp)
            server.quit()
            
            # Actualizar estado
            config.ultimo_test = timezone.now()
            config.test_exitoso = True
            config.mensaje_error = ""
            config.save()
            
            return True, "Conexión exitosa"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error probando SMTP {config.nombre}: {error_msg}")
            
            # Actualizar estado
            config.ultimo_test = timezone.now()
            config.test_exitoso = False
            config.mensaje_error = error_msg
            config.save()
            
            return False, error_msg
    
    def _enviar_con_proveedor(self, config: ConfiguracionSMTP, destinatario: str,
                             asunto: str, contenido_texto: str = None, 
                             contenido_html: str = None, adjuntos: List = None,
                             log_envio: LogEnvioEmail = None) -> tuple[bool, str]:
        """Envía email usando un proveedor específico"""
        try:
            start_time = time.time()
            
            # Verificar límites
            if not config.puede_enviar_email():
                return False, f"Límite diario alcanzado ({config.limite_diario})"
            
            # Crear mensaje
            if contenido_texto and contenido_html:
                # Email con versiones texto y HTML
                msg = MIMEMultipart('alternative')
                msg['From'] = f"{config.nombre_remitente} <{config.email_remitente}>"
                msg['To'] = destinatario
                msg['Subject'] = asunto
                
                # Agregar contenido texto
                part_texto = MIMEText(contenido_texto, 'plain', 'utf-8')
                msg.attach(part_texto)
                
                # Agregar contenido HTML
                part_html = MIMEText(contenido_html, 'html', 'utf-8')
                msg.attach(part_html)
                
            elif contenido_html:
                # Solo HTML
                msg = MIMEText(contenido_html, 'html', 'utf-8')
                msg['From'] = f"{config.nombre_remitente} <{config.email_remitente}>"
                msg['To'] = destinatario
                msg['Subject'] = asunto
                
            elif contenido_texto:
                # Solo texto
                msg = MIMEText(contenido_texto, 'plain', 'utf-8')
                msg['From'] = f"{config.nombre_remitente} <{config.email_remitente}>"
                msg['To'] = destinatario
                msg['Subject'] = asunto
                
            else:
                return False, "No hay contenido para enviar"
            
            # Agregar adjuntos si los hay
            if adjuntos:
                # Si hay adjuntos, necesitamos convertir a MIMEMultipart
                if not isinstance(msg, MIMEMultipart):
                    # Crear nuevo mensaje multipart y mover el contenido
                    original_msg = msg
                    msg = MIMEMultipart()
                    msg['From'] = original_msg['From']
                    msg['To'] = original_msg['To']
                    msg['Subject'] = original_msg['Subject']
                    msg.attach(original_msg)
                
                for adjunto in adjuntos:
                    if hasattr(adjunto, 'read'):  # Es un archivo
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(adjunto.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {adjunto.name}'
                        )
                        msg.attach(part)
            
            # Enviar email
            if config.usa_ssl:
                server = smtplib.SMTP_SSL(config.servidor_smtp, config.puerto)
            else:
                server = smtplib.SMTP(config.servidor_smtp, config.puerto)
            
            if config.usa_tls and not config.usa_ssl:
                server.starttls()
            
            server.login(config.usuario_smtp, config.password_smtp)
            text = msg.as_string()
            server.sendmail(config.email_remitente, destinatario, text)
            server.quit()
            
            # Actualizar contadores y logs
            config.incrementar_contador()
            end_time = time.time()
            
            if log_envio:
                log_envio.estado = 'enviado'
                log_envio.enviado_en = timezone.now()
                log_envio.tiempo_procesamiento = end_time - start_time
                log_envio.configuracion_smtp = config
                log_envio.save()
            
            logger.info(f"Email enviado exitosamente a {destinatario} usando {config.nombre}")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error enviando email con {config.nombre}: {error_msg}")
            
            if log_envio:
                log_envio.mensaje_error = error_msg
                log_envio.save()
            
            return False, error_msg
    
    def enviar_email(self, destinatario: str, asunto: str, contenido: str,
                    es_html: bool = True, adjuntos: List = None, 
                    variables_template: Dict[str, Any] = None,
                    usuario_solicitante = None, ip_origen: str = None) -> tuple[bool, str]:
        """
        Envía un email usando el sistema de failover
        
        Args:
            destinatario: Email del destinatario
            asunto: Asunto del email
            contenido: Contenido del email
            es_html: Si el contenido es HTML
            adjuntos: Lista de archivos adjuntos
            variables_template: Variables adicionales para el template
            usuario_solicitante: Usuario que solicita el envío
            ip_origen: IP de origen
        
        Returns:
            tuple: (éxito, mensaje)
        """
        
        # Verificar si el sistema está activo
        config = self._get_configuracion_email()
        if config and hasattr(config, 'sistema_activo') and not config.sistema_activo:
            return False, "Sistema de emails desactivado"
        
        # Crear log de envío
        log_envio = LogEnvioEmail.objects.create(
            destinatario=destinatario,
            asunto=asunto,
            contenido_texto=contenido if not es_html else "",
            contenido_html=contenido if es_html else "",
            usuario_solicitante=usuario_solicitante,
            ip_origen=ip_origen
        )
        
        try:
            # Preparar contenido
            contenido_html = None
            contenido_texto = None
            
            if es_html:
                contenido_html = self._generar_html_desde_template(
                    contenido, asunto, variables_template
                )
                log_envio.contenido_html = contenido_html
            else:
                contenido_texto = contenido
                log_envio.contenido_texto = contenido_texto
            
            log_envio.save()
            
            # Obtener proveedores activos
            proveedores = self._get_proveedores_activos()
            
            if not proveedores.exists():
                log_envio.estado = 'error'
                log_envio.mensaje_error = "No hay proveedores SMTP activos"
                log_envio.save()
                return False, "No hay proveedores SMTP configurados"
            
            # Intentar envío con cada proveedor
            ultimo_error = ""
            for config in proveedores:
                log_envio.intentos_realizados += 1
                log_envio.save()
                
                logger.info(f"Intentando envío con {config.nombre} (intento {log_envio.intentos_realizados})")
                
                exito, mensaje = self._enviar_con_proveedor(
                    config, destinatario, asunto, contenido_texto, 
                    contenido_html, adjuntos, log_envio
                )
                
                if exito:
                    return True, mensaje
                
                ultimo_error = mensaje
                
                # Esperar antes del siguiente intento
                if log_envio.intentos_realizados < len(proveedores):
                    time.sleep(2)
            
            # Si llegamos aquí, todos los proveedores fallaron
            log_envio.estado = 'error'
            log_envio.mensaje_error = f"Todos los proveedores fallaron. Último error: {ultimo_error}"
            log_envio.save()
            
            return False, f"Error enviando email: {ultimo_error}"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error general enviando email: {error_msg}")
            
            log_envio.estado = 'error'
            log_envio.mensaje_error = error_msg
            log_envio.save()
            
            return False, error_msg
    
    def enviar_email_test(self, email_destino: str, config_id: int = None) -> tuple[bool, str]:
        """Envía un email de prueba"""
        if config_id:
            try:
                config = ConfiguracionSMTP.objects.get(id=config_id)
                return self._probar_conexion_smtp(config)
            except ConfiguracionSMTP.DoesNotExist:
                return False, "Configuración SMTP no encontrada"
        
        # Usar el sistema normal de envío
        contenido = """
        <h2>🧪 Email de Prueba</h2>
        <p>Este es un email de prueba del Sistema de Actas Municipales de Pastaza.</p>
        <p><strong>Fecha y hora:</strong> {{fecha_actual}}</p>
        <p>Si recibiste este email, significa que la configuración SMTP está funcionando correctamente.</p>
        <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h4>✅ Funcionalidades verificadas:</h4>
            <ul>
                <li>Conexión SMTP establecida</li>
                <li>Autenticación exitosa</li>
                <li>Envío de email completado</li>
                <li>Template HTML renderizado</li>
            </ul>
        </div>
        """
        
        variables = {
            'fecha_actual': timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        }
        
        return self.enviar_email(
            destinatario=email_destino,
            asunto="🧪 Prueba SMTP - Sistema Actas Municipales",
            contenido=contenido,
            es_html=True,
            variables_template=variables
        )
    
    def get_estadisticas_envio(self) -> Dict[str, Any]:
        """Obtiene estadísticas de envío de emails"""
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        now = timezone.now()
        hoy = now.date()
        hace_7_dias = hoy - timedelta(days=7)
        hace_30_dias = hoy - timedelta(days=30)
        
        stats = {
            'total_enviados_hoy': LogEnvioEmail.objects.filter(
                fecha_creacion__date=hoy,
                estado='enviado'
            ).count(),
            
            'total_errores_hoy': LogEnvioEmail.objects.filter(
                fecha_creacion__date=hoy,
                estado='error'
            ).count(),
            
            'total_enviados_7_dias': LogEnvioEmail.objects.filter(
                fecha_creacion__date__gte=hace_7_dias,
                estado='enviado'
            ).count(),
            
            'total_enviados_30_dias': LogEnvioEmail.objects.filter(
                fecha_creacion__date__gte=hace_30_dias,
                estado='enviado'
            ).count(),
            
            'proveedores_activos': ConfiguracionSMTP.objects.filter(activo=True).count(),
            
            'proveedor_por_defecto': self._get_proveedor_por_defecto(),
            
            'emails_por_proveedor': ConfiguracionSMTP.objects.filter(
                activo=True
            ).annotate(
                emails_enviados=Count('logenviomail', filter=Q(logenviomail__estado='enviado'))
            ).values('nombre', 'emails_enviados', 'emails_enviados_hoy', 'limite_diario')
        }
        
        return stats


# Instancia global del servicio
smtp_service = SMTPService()


# Funciones de conveniencia
def enviar_email_notificacion(destinatario: str, asunto: str, contenido: str, 
                            usuario_solicitante=None) -> tuple[bool, str]:
    """Función de conveniencia para enviar notificaciones"""
    return smtp_service.enviar_email(
        destinatario=destinatario,
        asunto=asunto,
        contenido=contenido,
        es_html=True,
        usuario_solicitante=usuario_solicitante
    )


def enviar_email_evento(destinatario: str, evento, tipo_notificacion: str = 'invitacion',
                       usuario_solicitante=None) -> tuple[bool, str]:
    """Función específica para enviar emails de eventos"""
    
    if tipo_notificacion == 'invitacion':
        asunto = f"Invitación: {evento.titulo}"
        contenido = f"""
        <h2>📅 Invitación a Evento Municipal</h2>
        <p>Has sido invitado al siguiente evento:</p>
        
        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>{evento.titulo}</h3>
            <p><strong>📅 Fecha:</strong> {evento.fecha.strftime('%d/%m/%Y')}</p>
            <p><strong>🕐 Hora:</strong> {evento.hora.strftime('%H:%M')}</p>
            <p><strong>📍 Lugar:</strong> {evento.lugar}</p>
            <p><strong>📝 Descripción:</strong> {evento.descripcion}</p>
        </div>
        
        <p>Por favor confirma tu asistencia accediendo al sistema.</p>
        """
    
    elif tipo_notificacion == 'recordatorio':
        asunto = f"Recordatorio: {evento.titulo}"
        contenido = f"""
        <h2>⏰ Recordatorio de Evento</h2>
        <p>Te recordamos que tienes un evento próximo:</p>
        
        <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>{evento.titulo}</h3>
            <p><strong>📅 Fecha:</strong> {evento.fecha.strftime('%d/%m/%Y')}</p>
            <p><strong>🕐 Hora:</strong> {evento.hora.strftime('%H:%M')}</p>
            <p><strong>📍 Lugar:</strong> {evento.lugar}</p>
        </div>
        """
    
    elif tipo_notificacion == 'confirmacion':
        asunto = f"Confirmación: {evento.titulo}"
        contenido = f"""
        <h2>✅ Confirmación de Asistencia</h2>
        <p>Gracias por confirmar tu asistencia al evento:</p>
        
        <div style="background-color: #d1edff; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <h3>{evento.titulo}</h3>
            <p><strong>📅 Fecha:</strong> {evento.fecha.strftime('%d/%m/%Y')}</p>
            <p><strong>🕐 Hora:</strong> {evento.hora.strftime('%H:%M')}</p>
            <p><strong>📍 Lugar:</strong> {evento.lugar}</p>
        </div>
        
        <p>Te esperamos puntualmente.</p>
        """
    
    return smtp_service.enviar_email(
        destinatario=destinatario,
        asunto=asunto,
        contenido=contenido,
        es_html=True,
        usuario_solicitante=usuario_solicitante
    )
