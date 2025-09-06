"""
Middleware avanzado para manejo y tracking de sesiones
"""
import json
import logging
from datetime import datetime
from django.contrib.auth.models import AnonymousUser
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.contrib import messages
from django.conf import settings

# Configurar logger específico para sesiones
logger = logging.getLogger('django.request')

class AdvancedSessionMiddleware(MiddlewareMixin):
    """
    Middleware avanzado para manejo y tracking de sesiones
    """
    
    def process_request(self, request):
        """Procesar cada request para tracking de sesiones"""
        
        # Información básica de la sesión
        session_key = request.session.session_key
        user = request.user if hasattr(request, 'user') else AnonymousUser()
        
        # Detectar nueva sesión
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
            
            # Log de nueva sesión
            logger.info(f"Nueva sesión creada: {session_key}")
        
        # Actualizar información de sesión
        request.session['last_activity'] = datetime.now().isoformat()
        request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limitar tamaño
        request.session['ip_address'] = self.get_client_ip(request)
        request.session['path_history'] = self.update_path_history(request)
        request.session['request_count'] = request.session.get('request_count', 0) + 1
        
        # Log de actividad solo para rutas importantes
        if not self.is_excluded_url(request.path):
            logger.info(
                f"Actividad - Usuario: {user.username if not user.is_anonymous else 'Anónimo'}, "
                f"Sesión: {session_key[:8]}..., IP: {request.session['ip_address']}, "
                f"Ruta: {request.path}"
            )
        
        return None
    
    def process_response(self, request, response):
        """Procesar respuesta para agregar headers de debugging"""
        
        if hasattr(request, 'session') and hasattr(request, 'user'):
            # Agregar headers de debugging (solo en desarrollo o para superusuarios)
            if settings.DEBUG or (request.user.is_authenticated and request.user.is_superuser):
                response['X-Session-Key'] = request.session.session_key or 'No-Session'
                response['X-Session-Age'] = str(request.session.get_expiry_age())
                response['X-User-Authenticated'] = str(not request.user.is_anonymous)
                response['X-Request-Count'] = str(request.session.get('request_count', 0))
        
        return response
    
    def get_client_ip(self, request):
        """Obtener IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'Unknown')
        return ip
    
    def update_path_history(self, request):
        """Mantener historial de rutas visitadas"""
        current_path = request.path
        history = request.session.get('path_history', [])
        
        # Agregar nueva ruta si es diferente a la última
        if not history or history[-1] != current_path:
            history.append({
                'path': current_path,
                'timestamp': datetime.now().isoformat(),
                'method': request.method
            })
            
        # Mantener solo las últimas 20 rutas
        if len(history) > 20:
            history = history[-20:]
            
        return history
    
    def is_excluded_url(self, path):
        """Verificar si la URL debe ser excluida del tracking"""
        excluded_patterns = getattr(settings, 'EXCLUDE_URLS_FROM_TRACKING', [])
        for pattern in excluded_patterns:
            if pattern in path:
                return True
        return False
