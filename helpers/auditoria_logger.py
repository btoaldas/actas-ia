"""
Logger para el sistema de auditoría
Proporciona métodos convenientes para registrar diferentes tipos de eventos
"""
from django.db import connection
import json
from datetime import datetime
import traceback


class AuditoriaLogger:
    """
    Clase principal para logging y auditoría
    """
    
    def __init__(self):
        self.connection = connection
    
    def registrar_log_sistema(self, nivel, categoria, subcategoria, mensaje, 
                             usuario_id=None, session_id=None, ip_address=None,
                             metadatos=None, modulo=None, url_solicitada=None, metodo_http=None,
                             tiempo_respuesta=None, codigo_respuesta=None, user_agent=None):
        """
        Registra un log del sistema
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.sistema_logs (
                        nivel, categoria, subcategoria, mensaje, usuario_id, session_id, 
                        ip_address, datos_extra, modulo, url_solicitada, metodo_http, 
                        tiempo_respuesta_ms, codigo_respuesta, user_agent
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                ''', [
                    nivel, categoria, subcategoria, mensaje, usuario_id, session_id,
                    ip_address, json.dumps(metadatos) if metadatos else None,
                    modulo, url_solicitada, metodo_http, tiempo_respuesta, codigo_respuesta, user_agent
                ])
                return True
        except Exception as e:
            print(f"Error registrando log del sistema: {e}")
            return False
    
    def registrar_navegacion(self, usuario_id, session_id, url_visitada,
                           url_anterior=None, metodo_http='GET', accion_realizada=None,
                           ip_address=None, parametros_get=None, parametros_post=None,
                           tiempo_permanencia_ms=None, elemento_interactuado=None,
                           datos_formulario=None, codigo_respuesta=200):
        """
        Registra navegación de usuario
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.navegacion_usuarios (
                        usuario_id, session_id, url_visitada, url_anterior,
                        metodo_http, accion_realizada, ip_address, parametros_get, 
                        parametros_post, tiempo_permanencia_ms, elemento_interactuado,
                        datos_formulario, codigo_respuesta
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                ''', [
                    usuario_id, session_id, url_visitada, url_anterior,
                    metodo_http, accion_realizada, ip_address,
                    json.dumps(parametros_get) if parametros_get else None,
                    json.dumps(parametros_post) if parametros_post else None,
                    tiempo_permanencia_ms, elemento_interactuado,
                    json.dumps(datos_formulario) if datos_formulario else None,
                    codigo_respuesta
                ])
                return True
        except Exception as e:
            print(f"Error registrando navegación: {e}")
            return False
    
    def registrar_log_api(self, endpoint, metodo_http, usuario_id=None, 
                         parametros_query=None, payload_request=None, payload_response=None,
                         codigo_respuesta=None, tiempo_respuesta_ms=None,
                         ip_address=None, user_agent=None, api_key_id=None,
                         tamaño_request_bytes=None, tamaño_response_bytes=None,
                         version_api=None, rate_limit_remaining=None, error_mensaje=None):
        """
        Registra llamadas a la API
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.api_logs (
                        endpoint, metodo_http, usuario_id, api_key_id, ip_address,
                        user_agent, parametros_query, payload_request, payload_response,
                        codigo_respuesta, tiempo_respuesta_ms, tamaño_request_bytes,
                        tamaño_response_bytes, version_api, rate_limit_remaining, error_mensaje
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                ''', [
                    endpoint, metodo_http, usuario_id, api_key_id, ip_address, user_agent,
                    json.dumps(parametros_query) if parametros_query else None,
                    json.dumps(payload_request) if payload_request else None,
                    json.dumps(payload_response) if payload_response else None,
                    codigo_respuesta, tiempo_respuesta_ms, tamaño_request_bytes,
                    tamaño_response_bytes, version_api, rate_limit_remaining, error_mensaje
                ])
                return True
        except Exception as e:
            print(f"Error registrando log de API: {e}")
            return False
    
    def registrar_error(self, mensaje_error, codigo_error=None, stack_trace=None,
                       usuario_id=None, ip_address=None, nivel_error='ERROR',
                       url_error=None, session_id=None, user_agent=None,
                       datos_request=None, contexto_aplicacion=None):
        """
        Registra errores del sistema
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.errores_sistema (
                        nivel_error, codigo_error, mensaje_error, stack_trace, 
                        url_error, usuario_id, session_id, ip_address, user_agent,
                        datos_request, contexto_aplicacion
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                ''', [
                    nivel_error, codigo_error, mensaje_error, stack_trace,
                    url_error, usuario_id, session_id, ip_address, user_agent,
                    json.dumps(datos_request) if datos_request else None,
                    json.dumps(contexto_aplicacion) if contexto_aplicacion else None
                ])
                return True
        except Exception as e:
            print(f"Error registrando error: {e}")
            return False
    
    def registrar_celery_task(self, task_id, task_name, estado, resultado=None,
                             metadatos=None, tiempo_ejecucion=None):
        """
        Registra tareas de Celery
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.celery_logs (
                        task_id, task_name, estado, resultado, metadatos,
                        tiempo_ejecucion_ms, fecha_ejecucion
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, NOW()
                    )
                ''', [
                    task_id, task_name, estado,
                    json.dumps(resultado) if resultado else None,
                    json.dumps(metadatos) if metadatos else None,
                    tiempo_ejecucion
                ])
                return True
        except Exception as e:
            print(f"Error registrando tarea Celery: {e}")
            return False
    
    def registrar_acceso_usuario(self, usuario_id, evento, ip_address=None,
                                user_agent=None, metadatos=None):
        """
        Registra accesos de usuario (login, logout, etc.)
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.acceso_usuarios (
                        usuario_id, evento, ip_address, user_agent, metadatos, fecha_evento
                    ) VALUES (
                        %s, %s, %s, %s, %s, NOW()
                    )
                ''', [
                    usuario_id, evento, ip_address, user_agent,
                    json.dumps(metadatos) if metadatos else None
                ])
                return True
        except Exception as e:
            print(f"Error registrando acceso de usuario: {e}")
            return False
    
    def obtener_estadisticas_hoy(self):
        """
        Obtiene estadísticas del día actual
        """
        try:
            with self.connection.cursor() as cursor:
                estadisticas = {}
                
                # Logs del sistema
                cursor.execute('''
                    SELECT COUNT(*) FROM logs.sistema_logs 
                    WHERE DATE(timestamp) = CURRENT_DATE
                ''')
                estadisticas['logs_sistema'] = cursor.fetchone()[0]
                
                # Navegación
                cursor.execute('''
                    SELECT COUNT(*) FROM logs.navegacion_usuarios 
                    WHERE DATE(timestamp) = CURRENT_DATE
                ''')
                estadisticas['navegacion'] = cursor.fetchone()[0]
                
                # Cambios en BD
                cursor.execute('''
                    SELECT COUNT(*) FROM auditoria.cambios_bd 
                    WHERE DATE(timestamp) = CURRENT_DATE
                ''')
                estadisticas['cambios_bd'] = cursor.fetchone()[0]
                
                # API
                cursor.execute('''
                    SELECT COUNT(*) FROM logs.api_logs 
                    WHERE DATE(timestamp) = CURRENT_DATE
                ''')
                estadisticas['api_calls'] = cursor.fetchone()[0]
                
                # Errores
                cursor.execute('''
                    SELECT COUNT(*) FROM logs.errores_sistema 
                    WHERE DATE(timestamp) = CURRENT_DATE
                ''')
                estadisticas['errores'] = cursor.fetchone()[0]
                
                # Accesos
                cursor.execute('''
                    SELECT COUNT(*) FROM logs.acceso_usuarios 
                    WHERE DATE(timestamp) = CURRENT_DATE
                ''')
                estadisticas['accesos'] = cursor.fetchone()[0]
                
                # Celery
                cursor.execute('''
                    SELECT COUNT(*) FROM logs.celery_logs 
                    WHERE DATE(timestamp) = CURRENT_DATE
                ''')
                estadisticas['celery_tasks'] = cursor.fetchone()[0]
                
                return estadisticas
                
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}
