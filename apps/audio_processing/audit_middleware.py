"""
Middleware específico para auditoría avanzada del módulo de procesamiento de audio
"""
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve

# Logger específico para auditoría de audio
audit_logger = logging.getLogger('audio_audit')

# Importar funciones de logging específicas para audio processing
try:
    from .logging_helper import log_navegacion, log_sistema
except ImportError:
    # Fallback si hay problemas de importación circular
    log_navegacion = None
    log_sistema = None


class AudioProcessingAuditMiddleware(MiddlewareMixin):
    """
    Middleware específico para auditoría detallada del módulo de procesamiento de audio
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Inicializar timing para la petición"""
        request._audio_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Procesar la respuesta y generar logs específicos de audio processing"""
        try:
            # Solo procesar URLs del módulo de audio
            if not self._is_audio_processing_url(request):
                return response
            
            # Calcular tiempo de respuesta
            if hasattr(request, '_audio_start_time'):
                response_time_ms = int((time.time() - request._audio_start_time) * 1000)
            else:
                response_time_ms = None
            
            # Obtener información de la URL
            url_info = self._get_url_info(request)
            
            # Solo loggear si el usuario está autenticado y las funciones están disponibles
            if request.user.is_authenticated and log_navegacion and log_sistema:
                # Log específico de navegación en audio processing
                accion = self._get_accion_from_url(url_info)
                elemento = self._get_elemento_from_url(request, url_info)
                
                log_navegacion(
                    request=request,
                    accion_realizada=accion,
                    elemento_interactuado=elemento,
                    tiempo_permanencia_ms=response_time_ms
                )
                
                # Log de sistema solo para acciones importantes
                if self._is_important_action(accion):
                    log_sistema(
                        nivel='INFO',
                        categoria='AUDIO_PROCESSING_ACCESS',
                        subcategoria=accion.upper(),
                        mensaje=f'Acceso a {accion} en módulo de audio',
                        request=request,
                        datos_extra={
                            'url_info': url_info,
                            'response_time_ms': response_time_ms,
                            'response_status': response.status_code
                        }
                    )
            
        except Exception as e:
            # No queremos que errores en el logging rompan la aplicación
            audit_logger.error(f"Error en AudioProcessingAuditMiddleware: {e}")
        
        return response
    
    def _is_audio_processing_url(self, request):
        """Verificar si la URL pertenece al módulo de audio processing"""
        try:
            resolved = resolve(request.path_info)
            return resolved.app_name == 'audio_processing'
        except:
            return False
    
    def _get_url_info(self, request):
        """Obtener información de la URL"""
        try:
            resolved = resolve(request.path_info)
            return {
                'url_name': resolved.url_name,
                'app_name': resolved.app_name,
                'kwargs': resolved.kwargs,
                'args': resolved.args
            }
        except:
            return {
                'url_name': 'unknown',
                'app_name': 'unknown',
                'kwargs': {},
                'args': []
            }
    
    def _get_accion_from_url(self, url_info):
        """Mapear URL a acción descriptiva"""
        url_name = url_info.get('url_name', '')
        
        accion_map = {
            'centro_audio': 'centro_audio',
            'lista_procesamientos': 'listar_procesamientos',
            'detalle_procesamiento': 'ver_detalle_procesamiento',
            'editar_procesamiento': 'editar_procesamiento',
            'confirmar_eliminar_procesamiento': 'confirmar_eliminar_procesamiento',
            'eliminar_procesamiento': 'eliminar_procesamiento',
            'api_procesar_audio': 'crear_procesamiento',
            'api_stats': 'ver_estadisticas',
            'api_recent_processes': 'ver_procesos_recientes',
            'api_estado_procesamiento': 'verificar_estado_procesamiento',
            'tipos_reunion': 'gestionar_tipos_reunion',
            'crear_tipo_reunion': 'crear_tipo_reunion',
            'editar_tipo_reunion': 'editar_tipo_reunion',
            'eliminar_tipo_reunion': 'eliminar_tipo_reunion',
        }
        
        return accion_map.get(url_name, f'audio_processing_{url_name}')
    
    def _get_elemento_from_url(self, request, url_info):
        """Obtener elemento específico desde la URL"""
        kwargs = url_info.get('kwargs', {})
        
        if 'id' in kwargs:
            return f"procesamiento_{kwargs['id']}"
        
        # Para APIs, incluir algunos parámetros
        if url_info.get('url_name', '').startswith('api_'):
            if request.method == 'POST':
                return 'api_endpoint_post'
            else:
                return 'api_endpoint_get'
        
        return url_info.get('url_name', 'unknown')
    
    def _is_important_action(self, accion):
        """Determinar si una acción es importante para el log del sistema"""
        important_actions = {
            'crear_procesamiento',
            'eliminar_procesamiento',
            'editar_procesamiento',
            'confirmar_eliminar_procesamiento',
            'crear_tipo_reunion',
            'editar_tipo_reunion',
            'eliminar_tipo_reunion'
        }
        return accion in important_actions
