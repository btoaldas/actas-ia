"""
Middleware para auditoría y logging de acciones del sistema
"""
import logging
import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.urls import resolve
from django.utils import timezone

# Configurar logger específico para auditoría
audit_logger = logging.getLogger('audit')

class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para registrar todas las acciones del usuario en el sistema
    """
    
    def process_request(self, request):
        """Registrar información al inicio de cada request"""
        request.start_time = time.time()
        
        # Obtener información del usuario
        user_info = "Anonymous"
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            user_info = f"{request.user.username} (ID: {request.user.id})"
        
        # Obtener información de la vista
        try:
            resolver_match = resolve(request.path_info)
            view_name = f"{resolver_match.view_name}"
            app_name = getattr(resolver_match, 'app_name', 'unknown')
        except:
            view_name = "unknown"
            app_name = "unknown"
        
        # Información base del request
        request_info = {
            'timestamp': timezone.now().isoformat(),
            'user': user_info,
            'method': request.method,
            'path': request.path,
            'view_name': view_name,
            'app_name': app_name,
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
        }
        
        # Agregar datos POST/GET si existen (sin passwords)
        if request.method in ['POST', 'PUT', 'PATCH']:
            post_data = dict(request.POST)
            # Filtrar campos sensibles
            sensitive_fields = ['password', 'csrfmiddlewaretoken', 'password1', 'password2']
            for field in sensitive_fields:
                if field in post_data:
                    post_data[field] = '***'
            request_info['post_data'] = post_data
        
        if request.GET:
            request_info['get_params'] = dict(request.GET)
        
        # Log del acceso
        audit_logger.info(f"REQUEST_START", extra=request_info)
        
        # Guardar en request para uso posterior
        request.audit_info = request_info
    
    def process_response(self, request, response):
        """Registrar información al final de cada request"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            response_info = {
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'content_type': response.get('Content-Type', 'unknown'),
            }
            
            # Agregar información del request si existe
            if hasattr(request, 'audit_info'):
                response_info.update(request.audit_info)
            
            # Determinar el nivel de log según el status
            if 200 <= response.status_code < 300:
                log_level = 'info'
            elif 300 <= response.status_code < 400:
                log_level = 'warning'
            else:
                log_level = 'error'
            
            # Log de la respuesta
            getattr(audit_logger, log_level)(
                f"REQUEST_END - {response.status_code}", 
                extra=response_info
            )
        
        return response
    
    def process_exception(self, request, exception):
        """Registrar excepciones"""
        if hasattr(request, 'audit_info'):
            error_info = request.audit_info.copy()
            error_info.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'status': 'EXCEPTION'
            })
            
            audit_logger.error(f"REQUEST_EXCEPTION", extra=error_info)
        
        return None
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AudioProcessingAuditMiddleware(MiddlewareMixin):
    """
    Middleware específico para auditar acciones de procesamiento de audio
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Auditar acciones específicas de audio processing"""
        
        # Solo auditar vistas de audio_processing
        if hasattr(view_func, 'view_class'):
            module_name = view_func.view_class.__module__
        else:
            module_name = view_func.__module__
        
        if 'audio_processing' in module_name:
            user_info = "Anonymous"
            if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
                user_info = f"{request.user.username}"
            
            action_info = {
                'timestamp': timezone.now().isoformat(),
                'user': user_info,
                'action': view_func.__name__,
                'method': request.method,
                'view_args': view_args,
                'view_kwargs': view_kwargs,
                'ip_address': self.get_client_ip(request),
            }
            
            # Log específico de acciones de audio
            audio_logger = logging.getLogger('audio_audit')
            audio_logger.info(f"AUDIO_ACTION: {view_func.__name__}", extra=action_info)
        
        return None
    
    def get_client_ip(self, request):
        """Obtener la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
