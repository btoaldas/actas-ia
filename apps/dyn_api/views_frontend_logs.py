# ============================================================================
# API View para recibir logs del frontend - Actas Municipales
# Archivo: apps/dyn_api/views_frontend_logs.py
# ============================================================================

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.models import User
import logging
from typing import Dict, List, Any
# from user_agents import parse  # Comentado temporalmente por dependencia faltante

logger = logging.getLogger('frontend_audit')

class FrontendLogsAPIView(View):
    """
    API para recibir logs del frontend JavaScript
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        """Recibir y procesar logs del frontend"""
        try:
            # Parsear datos JSON
            data = json.loads(request.body)
            events = data.get('events', [])
            metadata = data.get('metadata', {})
            
            if not events:
                return JsonResponse({'error': 'No events provided'}, status=400)
            
            # Información del request
            user_id = request.user.id if request.user.is_authenticated else None
            session_id = request.session.session_key
            ip_address = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Procesar eventos en batch
            eventos_procesados = 0
            with transaction.atomic():
                for event in events:
                    if self._process_frontend_event(
                        event, user_id, session_id, ip_address, user_agent
                    ):
                        eventos_procesados += 1
            
            return JsonResponse({
                'success': True,
                'events_processed': eventos_procesados,
                'total_events': len(events)
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error(f"Error procesando logs frontend: {e}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
    
    def _process_frontend_event(
        self, 
        event: Dict[str, Any], 
        user_id: int, 
        session_id: str, 
        ip_address: str, 
        user_agent: str
    ) -> bool:
        """Procesar un evento individual del frontend"""
        
        try:
            event_type = event.get('tipo', 'UNKNOWN')
            categoria = event.get('categoria', 'FRONTEND')
            
            # Determinar dónde guardar el evento según su tipo
            if event_type in ['PAGE_VIEW', 'PAGE_EXIT', 'VISIBILITY_CHANGE']:
                return self._save_navigation_event(event, user_id, session_id, ip_address)
            elif event_type in ['ERROR_JS', 'PROMISE_REJECTION']:
                return self._save_error_event(event, user_id, session_id, ip_address, user_agent)
            elif event_type in ['FILE_UPLOAD', 'FILE_DOWNLOAD']:
                return self._save_file_event(event, user_id, session_id, ip_address)
            else:
                return self._save_system_log_event(event, user_id, session_id, ip_address, user_agent)
                
        except Exception as e:
            logger.error(f"Error procesando evento frontend {event_type}: {e}")
            return False
    
    def _save_navigation_event(
        self, 
        event: Dict[str, Any], 
        user_id: int, 
        session_id: str, 
        ip_address: str
    ) -> bool:
        """Guardar evento de navegación"""
        
        with connection.cursor() as cursor:
            # Determinar acción realizada
            tipo = event.get('tipo')
            if tipo == 'PAGE_VIEW':
                accion = 'VISIT'
            elif tipo == 'PAGE_EXIT':
                accion = 'EXIT'
            elif tipo == 'VISIBILITY_CHANGE':
                accion = 'VISIBILITY_CHANGE'
            else:
                accion = tipo
            
            # Datos específicos de navegación
            url_visitada = event.get('url', event.get('url_actual', ''))
            tiempo_permanencia = event.get('tiempo_permanencia', event.get('tiempo_en_pagina'))
            
            # Parámetros adicionales
            parametros_extra = {
                'frontend_timestamp': event.get('timestamp'),
                'referrer': event.get('referrer'),
                'titulo': event.get('titulo'),
                'viewport': event.get('viewport'),
                'screen': event.get('screen'),
                'tiempo_carga': event.get('tiempo_carga'),
                'visible': event.get('visible'),
                'language': event.get('language'),
                'timezone': event.get('timezone')
            }
            
            cursor.execute("""
                INSERT INTO logs.navegacion_usuarios (
                    usuario_id, session_id, url_visitada, metodo_http,
                    tiempo_permanencia_ms, accion_realizada, ip_address,
                    parametros_get
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                user_id,
                session_id,
                url_visitada,
                'GET',
                tiempo_permanencia,
                accion,
                ip_address,
                json.dumps(parametros_extra)
            ])
            
        return True
    
    def _save_error_event(
        self, 
        event: Dict[str, Any], 
        user_id: int, 
        session_id: str, 
        ip_address: str, 
        user_agent: str
    ) -> bool:
        """Guardar evento de error JavaScript"""
        
        with connection.cursor() as cursor:
            tipo = event.get('tipo')
            mensaje_error = event.get('mensaje', event.get('razon', 'Error desconocido'))
            
            # Código de error específico
            if tipo == 'ERROR_JS':
                codigo_error = 'JAVASCRIPT_ERROR'
            elif tipo == 'PROMISE_REJECTION':
                codigo_error = 'PROMISE_REJECTION'
            else:
                codigo_error = 'FRONTEND_ERROR'
            
            # Contexto del error
            contexto = {
                'archivo': event.get('archivo'),
                'linea': event.get('linea'),
                'columna': event.get('columna'),
                'user_agent_info': self._parse_user_agent(user_agent),
                'url_error': event.get('url_actual'),
                'frontend_timestamp': event.get('timestamp'),
                'language': event.get('language'),
                'timezone': event.get('timezone')
            }
            
            cursor.execute("""
                INSERT INTO logs.errores_sistema (
                    nivel_error, codigo_error, mensaje_error, stack_trace,
                    url_error, usuario_id, session_id, ip_address,
                    user_agent, contexto_aplicacion, entorno
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                'ERROR',
                codigo_error,
                mensaje_error,
                event.get('stack'),
                event.get('url_actual'),
                user_id,
                session_id,
                ip_address,
                user_agent,
                json.dumps(contexto),
                'frontend'
            ])
            
        return True
    
    def _save_file_event(
        self, 
        event: Dict[str, Any], 
        user_id: int, 
        session_id: str, 
        ip_address: str
    ) -> bool:
        """Guardar evento de archivo (upload/download)"""
        
        with connection.cursor() as cursor:
            tipo = event.get('tipo')
            accion = 'UPLOAD' if tipo == 'FILE_UPLOAD' else 'DOWNLOAD'
            
            # Datos del archivo
            nombre_archivo = event.get('nombre_archivo', 'unknown')
            tamaño_archivo = event.get('tamaño_archivo')
            tipo_archivo = event.get('tipo_archivo')
            url_descarga = event.get('url_descarga')
            
            # Datos adicionales
            datos_adicionales = {
                'frontend_timestamp': event.get('timestamp'),
                'url_origen': event.get('url_actual'),
                'language': event.get('language'),
                'timezone': event.get('timezone')
            }
            
            if url_descarga:
                datos_adicionales['url_descarga'] = url_descarga
            
            cursor.execute("""
                INSERT INTO logs.archivo_logs (
                    accion, nombre_archivo, tamaño_bytes, tipo_mime,
                    usuario_id, ip_address, session_id, datos_adicionales
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                accion,
                nombre_archivo,
                tamaño_archivo,
                tipo_archivo,
                user_id,
                ip_address,
                session_id,
                json.dumps(datos_adicionales)
            ])
            
        return True
    
    def _save_system_log_event(
        self, 
        event: Dict[str, Any], 
        user_id: int, 
        session_id: str, 
        ip_address: str, 
        user_agent: str
    ) -> bool:
        """Guardar evento general del sistema"""
        
        with connection.cursor() as cursor:
            tipo = event.get('tipo', 'FRONTEND_EVENT')
            categoria = event.get('categoria', 'FRONTEND')
            
            # Determinar nivel de log
            if 'ERROR' in tipo.upper():
                nivel = 'ERROR'
            elif 'WARNING' in tipo.upper():
                nivel = 'WARNING'
            else:
                nivel = 'INFO'
            
            # Mensaje descriptivo
            mensaje = self._generate_event_message(event)
            
            # Datos extra con toda la información del evento
            datos_extra = {
                'tipo_evento': tipo,
                'frontend_timestamp': event.get('timestamp'),
                'user_agent_info': self._parse_user_agent(user_agent),
                'language': event.get('language'),
                'timezone': event.get('timezone'),
                'url_actual': event.get('url_actual')
            }
            
            # Añadir datos específicos del evento
            for key, value in event.items():
                if key not in ['tipo', 'categoria', 'timestamp', 'user_id', 'session_id', 'url_actual']:
                    datos_extra[key] = value
            
            cursor.execute("""
                SELECT logs.registrar_log_sistema(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                nivel,
                categoria,
                tipo,
                mensaje,
                user_id,
                session_id,
                ip_address,
                json.dumps(datos_extra),
                'frontend',
                event.get('url_actual'),
                'POST',  # Método usado para enviar el log
                None,    # tiempo_respuesta_ms
                200      # código_respuesta
            ])
            
        return True
    
    def _generate_event_message(self, event: Dict[str, Any]) -> str:
        """Generar mensaje descriptivo para el evento"""
        
        tipo = event.get('tipo', 'UNKNOWN')
        
        if tipo == 'CLICK':
            return f"Click en elemento: {event.get('elemento', 'desconocido')}"
        elif tipo == 'FORM_SUBMIT':
            return f"Envío de formulario: {event.get('formulario_id', 'sin_id')}"
        elif tipo == 'SEARCH':
            return f"Búsqueda realizada: '{event.get('consulta_busqueda', '')}'"
        elif tipo == 'PERFORMANCE':
            return "Métricas de rendimiento registradas"
        elif tipo == 'CONNECTION_CHANGE':
            estado = event.get('estado_conexion', 'unknown')
            return f"Cambio de conexión a: {estado}"
        else:
            return f"Evento frontend: {tipo}"
    
    def _get_client_ip(self, request):
        """Obtener IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _parse_user_agent(self, user_agent_string):
        """Parsear información del User Agent"""
        try:
            # user_agent = parse(user_agent_string)  # Comentado temporalmente
            return {
                'browser': "Unknown Browser",  # f"{user_agent.browser.family} {user_agent.browser.version_string}",
                'os': "Unknown OS",  # f"{user_agent.os.family} {user_agent.os.version_string}",
                'device': "Unknown Device",  # user_agent.device.family,
                'is_mobile': False,  # user_agent.is_mobile,
                'is_tablet': False,  # user_agent.is_tablet,
                'is_pc': False,  # user_agent.is_pc,
                'is_bot': False  # user_agent.is_bot
            }
        except Exception:
            return {'raw': user_agent_string}


# ============================================================================
# VISTAS ADICIONALES PARA REPORTES
# ============================================================================

@require_http_methods(["GET"])
def frontend_stats_api(request):
    """API para obtener estadísticas de actividad frontend"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        dias = int(request.GET.get('dias', 7))
        
        with connection.cursor() as cursor:
            # Estadísticas de navegación
            cursor.execute("""
                SELECT 
                    url_visitada,
                    COUNT(*) as visitas,
                    COUNT(DISTINCT usuario_id) as usuarios_unicos,
                    AVG(tiempo_permanencia_ms) as tiempo_promedio
                FROM logs.navegacion_usuarios 
                WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
                AND accion_realizada = 'VISIT'
                GROUP BY url_visitada
                ORDER BY visitas DESC
                LIMIT 20
            """, [dias])
            
            paginas_populares = [
                {
                    'url': row[0],
                    'visitas': row[1],
                    'usuarios_unicos': row[2],
                    'tiempo_promedio_ms': float(row[3]) if row[3] else 0
                }
                for row in cursor.fetchall()
            ]
            
            # Estadísticas de errores frontend
            cursor.execute("""
                SELECT 
                    codigo_error,
                    COUNT(*) as total_errores,
                    COUNT(DISTINCT usuario_id) as usuarios_afectados
                FROM logs.errores_sistema 
                WHERE entorno = 'frontend'
                AND timestamp >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY codigo_error
                ORDER BY total_errores DESC
            """, [dias])
            
            errores_frontend = [
                {
                    'codigo_error': row[0],
                    'total_errores': row[1],
                    'usuarios_afectados': row[2]
                }
                for row in cursor.fetchall()
            ]
            
        return JsonResponse({
            'success': True,
            'data': {
                'paginas_populares': paginas_populares,
                'errores_frontend': errores_frontend,
                'periodo_dias': dias
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas frontend: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def user_activity_timeline(request):
    """API para obtener timeline de actividad de un usuario"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'user_id required'}, status=400)
            
        dias = int(request.GET.get('dias', 1))
        
        with connection.cursor() as cursor:
            # Obtener actividad de navegación
            cursor.execute("""
                SELECT 
                    timestamp,
                    'navegacion' as tipo_actividad,
                    url_visitada as detalle,
                    accion_realizada as accion,
                    tiempo_permanencia_ms
                FROM logs.navegacion_usuarios
                WHERE usuario_id = %s
                AND timestamp >= CURRENT_DATE - INTERVAL '%s days'
                
                UNION ALL
                
                SELECT 
                    timestamp,
                    'sistema' as tipo_actividad,
                    mensaje as detalle,
                    subcategoria as accion,
                    tiempo_respuesta_ms
                FROM logs.sistema_logs
                WHERE usuario_id = %s
                AND timestamp >= CURRENT_DATE - INTERVAL '%s days'
                
                ORDER BY timestamp DESC
                LIMIT 100
            """, [user_id, dias, user_id, dias])
            
            actividades = [
                {
                    'timestamp': row[0].isoformat(),
                    'tipo_actividad': row[1],
                    'detalle': row[2],
                    'accion': row[3],
                    'duracion_ms': row[4]
                }
                for row in cursor.fetchall()
            ]
            
        return JsonResponse({
            'success': True,
            'data': {
                'actividades': actividades,
                'user_id': user_id,
                'periodo_dias': dias
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo timeline de usuario: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
