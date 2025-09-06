# ============================================================================
# Middleware de Auditoría y Logs - Actas Municipales
# Descripción: Middleware para capturar automáticamente todas las actividades
# ============================================================================

import json
import time
import hashlib
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from django.http import JsonResponse
try:
    from user_agents import parse
    USER_AGENTS_AVAILABLE = True
except ImportError:
    print("⚠️  user_agents no está disponible, el análisis de user-agent estará limitado")
    USER_AGENTS_AVAILABLE = False
    parse = None
import logging
from typing import Optional, Dict, Any

# Configurar logger
logger = logging.getLogger('auditoria')

class AuditoriaMiddleware(MiddlewareMixin):
    """
    Middleware para capturar automáticamente todas las actividades del sistema
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Procesar la petición entrante"""
        # Marcar tiempo de inicio
        request._start_time = time.time()
        
        # Configurar variables de auditoría en la BD
        self._set_audit_context(request)
        
        # Registrar navegación
        self._log_navigation(request)
        
        return None
    
    def process_response(self, request, response):
        """Procesar la respuesta saliente"""
        # Calcular tiempo de respuesta
        if hasattr(request, '_start_time'):
            response_time_ms = int((time.time() - request._start_time) * 1000)
        else:
            response_time_ms = None
        
        # Registrar log del sistema
        self._log_system_activity(request, response, response_time_ms)
        
        # Si es una respuesta de error, registrarlo específicamente
        if response.status_code >= 400:
            self._log_error_response(request, response)
        
        return response
    
    def process_exception(self, request, exception):
        """Procesar excepciones no manejadas"""
        self._log_system_exception(request, exception)
        return None
    
    def _set_audit_context(self, request):
        """Configurar contexto de auditoría en la base de datos"""
        try:
            with connection.cursor() as cursor:
                # Configurar variables de sesión para auditoría
                if hasattr(request, 'user') and request.user.is_authenticated:
                    cursor.execute("SELECT set_config('audit.user_id', %s, true)", [str(request.user.id)])
                    cursor.execute("SELECT set_config('audit.username', %s, true)", [request.user.username])
                
                if hasattr(request, 'session') and request.session.session_key:
                    cursor.execute("SELECT set_config('audit.session_id', %s, true)", [request.session.session_key])
                
                ip_address = self._get_client_ip(request)
                if ip_address:
                    cursor.execute("SELECT set_config('audit.ip_address', %s, true)", [ip_address])
                    
                # ID de transacción único para esta request
                transaction_id = hashlib.md5(f"{time.time()}_{request.path}".encode()).hexdigest()[:16]
                cursor.execute("SELECT set_config('audit.transaction_id', %s, true)", [transaction_id])
                
        except Exception as e:
            logger.error(f"Error configurando contexto de auditoría: {e}")
    
    def _log_navigation(self, request):
        """Registrar navegación del usuario"""
        try:
            with connection.cursor() as cursor:
                # Preparar datos
                usuario_id = request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None
                session_id = request.session.session_key if hasattr(request, 'session') else None
                url_visitada = request.get_full_path()
                url_anterior = request.META.get('HTTP_REFERER')
                metodo_http = request.method
                ip_address = self._get_client_ip(request)
                
                # Parámetros GET y POST (sin datos sensibles)
                parametros_get = dict(request.GET) if request.GET else None
                parametros_post = self._clean_sensitive_data(dict(request.POST)) if request.POST else None
                
                # Determinar acción realizada
                accion = self._determine_action(request)
                
                # Ejecutar función de logging
                cursor.execute("""
                    SELECT logs.registrar_navegacion(%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    usuario_id, session_id, url_visitada, url_anterior, metodo_http,
                    accion, ip_address, 
                    json.dumps(parametros_get) if parametros_get else None,
                    json.dumps(parametros_post) if parametros_post else None
                ])
                
        except Exception as e:
            logger.error(f"Error registrando navegación: {e}")
    
    def _log_system_activity(self, request, response, response_time_ms):
        """Registrar actividad general del sistema"""
        try:
            with connection.cursor() as cursor:
                # Determinar nivel de log
                if response.status_code >= 500:
                    nivel = 'ERROR'
                elif response.status_code >= 400:
                    nivel = 'WARNING'
                else:
                    nivel = 'INFO'
                
                # Determinar categoría
                categoria = self._determine_category(request)
                subcategoria = self._determine_subcategory(request, response)
                
                # Preparar mensaje
                mensaje = f"{request.method} {request.path} - {response.status_code}"
                
                # Datos extra
                user_agent_info = self._parse_user_agent(request.META.get('HTTP_USER_AGENT', ''))
                datos_extra = {
                    'user_agent_info': user_agent_info,
                    'content_type': response.get('Content-Type'),
                    'content_length': response.get('Content-Length'),
                    'request_size': len(request.body) if hasattr(request, 'body') else 0
                }
                
                # Determinar módulo basado en la URL
                modulo = self._determine_module(request.path)
                
                # Ejecutar función de logging
                cursor.execute("""
                    SELECT logs.registrar_log_sistema(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    nivel, categoria, subcategoria, mensaje,
                    request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                    request.session.session_key if hasattr(request, 'session') else None,
                    self._get_client_ip(request),
                    json.dumps(datos_extra),
                    modulo,
                    request.get_full_path(),
                    request.method,
                    response_time_ms,
                    response.status_code
                ])
                
        except Exception as e:
            logger.error(f"Error registrando actividad del sistema: {e}")
    
    def _log_error_response(self, request, response):
        """Registrar respuestas de error específicamente"""
        try:
            with connection.cursor() as cursor:
                nivel_error = 'CRITICAL' if response.status_code >= 500 else 'ERROR'
                codigo_error = f"HTTP_{response.status_code}"
                mensaje_error = f"Error {response.status_code} en {request.path}"
                
                # Datos del request para debugging
                datos_request = {
                    'method': request.method,
                    'path': request.path,
                    'get_params': dict(request.GET),
                    'post_params': self._clean_sensitive_data(dict(request.POST)),
                    'headers': dict(request.META)
                }
                
                cursor.execute("""
                    INSERT INTO logs.errores_sistema (
                        nivel_error, codigo_error, mensaje_error, url_error,
                        usuario_id, session_id, ip_address, user_agent, datos_request
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    nivel_error, codigo_error, mensaje_error, request.get_full_path(),
                    request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                    request.session.session_key if hasattr(request, 'session') else None,
                    self._get_client_ip(request),
                    request.META.get('HTTP_USER_AGENT'),
                    json.dumps(datos_request)
                ])
                
        except Exception as e:
            logger.error(f"Error registrando error de respuesta: {e}")
    
    def _log_system_exception(self, request, exception):
        """Registrar excepciones del sistema"""
        try:
            import traceback
            
            with connection.cursor() as cursor:
                stack_trace = traceback.format_exc()
                
                cursor.execute("""
                    INSERT INTO logs.errores_sistema (
                        nivel_error, codigo_error, mensaje_error, stack_trace, url_error,
                        usuario_id, session_id, ip_address, user_agent
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    'CRITICAL',
                    type(exception).__name__,
                    str(exception),
                    stack_trace,
                    request.get_full_path(),
                    request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                    request.session.session_key if hasattr(request, 'session') else None,
                    self._get_client_ip(request),
                    request.META.get('HTTP_USER_AGENT')
                ])
                
        except Exception as e:
            logger.error(f"Error registrando excepción del sistema: {e}")
    
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
            if not USER_AGENTS_AVAILABLE:
                return {
                    'browser': 'Desconocido',
                    'os': 'Desconocido', 
                    'device': 'Desconocido',
                    'is_mobile': False,
                    'is_tablet': False,
                    'is_pc': True,
                    'is_bot': False
                }
            
            user_agent = parse(user_agent_string)
            return {
                'browser': f"{user_agent.browser.family} {user_agent.browser.version_string}",
                'os': f"{user_agent.os.family} {user_agent.os.version_string}",
                'device': user_agent.device.family,
                'is_mobile': user_agent.is_mobile,
                'is_tablet': user_agent.is_tablet,
                'is_pc': user_agent.is_pc,
                'is_bot': user_agent.is_bot
            }
        except Exception:
            return {'raw': user_agent_string}
    
    def _clean_sensitive_data(self, data_dict):
        """Remover datos sensibles de los logs"""
        sensitive_fields = [
            'password', 'password1', 'password2', 'old_password', 'new_password',
            'csrfmiddlewaretoken', 'api_key', 'secret', 'token', 'credit_card',
            'ssn', 'social_security'
        ]
        
        cleaned = {}
        for key, value in data_dict.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                cleaned[key] = '[REDACTED]'
            else:
                cleaned[key] = value
        return cleaned
    
    def _determine_action(self, request):
        """Determinar la acción realizada basada en la request"""
        if request.method == 'GET':
            return 'VISIT'
        elif request.method == 'POST':
            if 'delete' in request.path.lower():
                return 'DELETE'
            elif 'create' in request.path.lower() or 'add' in request.path.lower():
                return 'CREATE'
            else:
                return 'FORM_SUBMIT'
        elif request.method == 'PUT':
            return 'UPDATE'
        elif request.method == 'DELETE':
            return 'DELETE'
        elif request.method == 'PATCH':
            return 'PARTIAL_UPDATE'
        else:
            return request.method
    
    def _determine_category(self, request):
        """Determinar categoría del log"""
        if '/admin/' in request.path:
            return 'ADMIN'
        elif '/api/' in request.path:
            return 'API'
        elif '/file_manager/' in request.path:
            return 'ARCHIVOS'
        elif request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            return 'ACCION'
        else:
            return 'NAVEGACION'
    
    def _determine_subcategory(self, request, response):
        """Determinar subcategoría del log"""
        if response.status_code >= 500:
            return 'ERROR_SERVIDOR'
        elif response.status_code >= 400:
            return 'ERROR_CLIENTE'
        elif request.method == 'POST':
            return 'CREATE_UPDATE'
        elif request.method == 'DELETE':
            return 'DELETE'
        elif request.method == 'GET':
            return 'VIEW'
        else:
            return request.method
    
    def _determine_module(self, path):
        """Determinar módulo basado en la URL"""
        if '/admin/' in path:
            return 'admin'
        elif '/users/' in path:
            return 'users'
        elif '/pages/' in path:
            return 'pages'
        elif '/file_manager/' in path:
            return 'file_manager'
        elif '/dyn_dt/' in path:
            return 'dyn_dt'
        elif '/dyn_api/' in path:
            return 'dyn_api'
        elif '/charts/' in path:
            return 'charts'
        elif '/api/' in path:
            return 'api'
        else:
            return 'core'


# ============================================================================
# SIGNALS PARA AUTENTICACIÓN
# ============================================================================

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registrar login exitoso"""
    try:
        with connection.cursor() as cursor:
            if USER_AGENTS_AVAILABLE:
                user_agent_info = parse(request.META.get('HTTP_USER_AGENT', ''))
                datos_adicionales = {
                    'dispositivo': user_agent_info.device.family,
                    'navegador': f"{user_agent_info.browser.family} {user_agent_info.browser.version_string}",
                    'sistema_operativo': f"{user_agent_info.os.family} {user_agent_info.os.version_string}",
                    'is_mobile': user_agent_info.is_mobile,
                    'is_bot': user_agent_info.is_bot
                }
            else:
                datos_adicionales = {
                    'dispositivo': 'Desconocido',
                    'navegador': 'Desconocido',
                    'sistema_operativo': 'Desconocido',
                    'is_mobile': False,
                    'is_bot': False
                }
            
            # Determinar método de autenticación
            metodo_auth = 'PASSWORD'
            if 'github' in request.path.lower():
                metodo_auth = 'OAUTH_GITHUB'
            elif 'google' in request.path.lower():
                metodo_auth = 'OAUTH_GOOGLE'
            
            cursor.execute("""
                SELECT logs.registrar_acceso_usuario(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                user.id,
                user.username,
                'LOGIN',
                get_client_ip(request),
                request.META.get('HTTP_USER_AGENT'),
                request.session.session_key,
                True,
                None,
                metodo_auth,
                json.dumps(datos_adicionales)
            ])
            
    except Exception as e:
        logger.error(f"Error registrando login: {e}")

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registrar logout"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT logs.registrar_acceso_usuario(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                user.id if user else None,
                user.username if user else 'anonymous',
                'LOGOUT',
                get_client_ip(request),
                request.META.get('HTTP_USER_AGENT'),
                request.session.session_key if hasattr(request, 'session') else None,
                True,
                None,
                'MANUAL',
                None
            ])
            
    except Exception as e:
        logger.error(f"Error registrando logout: {e}")

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Registrar intento de login fallido"""
    try:
        with connection.cursor() as cursor:
            username = credentials.get('username', 'unknown')
            
            cursor.execute("""
                SELECT logs.registrar_acceso_usuario(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                None,  # usuario_id es NULL para login fallido
                username,
                'LOGIN_FAILED',
                get_client_ip(request),
                request.META.get('HTTP_USER_AGENT'),
                request.session.session_key if hasattr(request, 'session') else None,
                False,
                'Credenciales inválidas',
                'PASSWORD',
                None
            ])
            
    except Exception as e:
        logger.error(f"Error registrando login fallido: {e}")

def get_client_ip(request):
    """Función auxiliar para obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================================
# DECORADOR PARA LOGGING MANUAL
# ============================================================================

def log_activity(categoria='ACCION', subcategoria=None, mensaje=None):
    """
    Decorador para registrar actividades específicas
    
    Uso:
    @log_activity(categoria='ARCHIVO', subcategoria='UPLOAD', mensaje='Archivo subido')
    def subir_archivo(request):
        # tu código aquí
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            resultado = func(request, *args, **kwargs)
            response_time = int((time.time() - start_time) * 1000)
            
            try:
                with connection.cursor() as cursor:
                    mensaje_final = mensaje or f"Ejecutada función {func.__name__}"
                    subcategoria_final = subcategoria or func.__name__.upper()
                    
                    cursor.execute("""
                        SELECT logs.registrar_log_sistema(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, [
                        'INFO',
                        categoria,
                        subcategoria_final,
                        mensaje_final,
                        request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
                        request.session.session_key if hasattr(request, 'session') else None,
                        get_client_ip(request),
                        json.dumps({'function': func.__name__, 'module': func.__module__}),
                        func.__module__.split('.')[-1] if '.' in func.__module__ else func.__module__,
                        request.get_full_path() if hasattr(request, 'get_full_path') else None,
                        request.method if hasattr(request, 'method') else None,
                        response_time,
                        200
                    ])
                    
            except Exception as e:
                logger.error(f"Error en decorador de logging: {e}")
            
            return resultado
        return wrapper
    return decorator
