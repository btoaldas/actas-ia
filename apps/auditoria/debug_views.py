"""
Vistas de debugging para verificar sesiones y cookies
"""
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, datetime

@login_required
def debug_session_info(request):
    """
    Vista para mostrar información detallada de la sesión actual
    """
    # Información de la sesión actual
    session_data = {
        'session_key': request.session.session_key,
        'session_data': dict(request.session),
        'session_expiry': request.session.get_expiry_date(),
        'session_age': request.session.get_expiry_age(),
        'session_modified': request.session.modified,
        'session_accessed': request.session.accessed,
    }
    
    # Información de cookies
    cookies_data = {}
    for name, value in request.COOKIES.items():
        cookies_data[name] = {
            'value': value,
            'length': len(value)
        }
    
    # Información del usuario
    user_data = {
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'is_authenticated': request.user.is_authenticated,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
        'last_login': request.user.last_login,
        'date_joined': request.user.date_joined,
    }
    
    # Información del request
    request_data = {
        'method': request.method,
        'path': request.path,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'remote_addr': request.META.get('REMOTE_ADDR', ''),
        'http_host': request.META.get('HTTP_HOST', ''),
        'server_name': request.META.get('SERVER_NAME', ''),
        'server_port': request.META.get('SERVER_PORT', ''),
        'content_type': request.META.get('CONTENT_TYPE', ''),
        'query_string': request.META.get('QUERY_STRING', ''),
    }
    
    # Headers relevantes
    headers_data = {}
    for key, value in request.META.items():
        if key.startswith('HTTP_'):
            header_name = key[5:].replace('_', '-').title()
            headers_data[header_name] = value
    
    context = {
        'session_data': session_data,
        'cookies_data': cookies_data,
        'user_data': user_data,
        'request_data': request_data,
        'headers_data': headers_data,
    }
    
    return render(request, 'auditoria/debug_session.html', context)

@login_required
def session_debug_api(request):
    """API para obtener información de sesión en tiempo real"""
    
    session = request.session
    user = request.user
    
    # Calcular tiempo de expiración
    expires_in = None
    if session.get_expiry_age():
        expires_in = f"{session.get_expiry_age() // 60} minutos"
    
    # Obtener todas las cookies
    cookies = {}
    for cookie_name, cookie_value in request.COOKIES.items():
        cookies[cookie_name] = cookie_value
    
    # Información de la sesión
    session_data = {
        'session_key': session.session_key,
        'user': user.username if user.is_authenticated else 'Anónimo',
        'user_id': user.id if user.is_authenticated else None,
        'last_activity': session.get('last_activity', 'No disponible'),
        'ip_address': session.get('ip_address', 'No disponible'),
        'expires_in': expires_in,
        'is_authenticated': user.is_authenticated,
        'path_history': session.get('path_history', []),
        'cookies': cookies,
        'session_data_keys': list(session.keys()),
        'request_count': session.get('request_count', 0),
        'user_agent': session.get('user_agent', 'No disponible')[:100] + '...' if session.get('user_agent', '') else 'No disponible'
    }
    
    return JsonResponse(session_data)

@login_required
@csrf_exempt
def clear_session_data(request):
    """API para limpiar datos de sesión específicos"""
    
    if request.method == 'POST':
        # Limpiar datos específicos pero mantener autenticación
        keys_to_keep = ['_auth_user_id', '_auth_user_backend', '_auth_user_hash']
        
        # Crear nueva sesión limpia
        new_session_data = {}
        for key in keys_to_keep:
            if key in request.session:
                new_session_data[key] = request.session[key]
        
        # Limpiar toda la sesión
        request.session.flush()
        
        # Restaurar datos de autenticación
        for key, value in new_session_data.items():
            request.session[key] = value
            
        request.session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Datos de sesión limpiados exitosamente'
        })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@csrf_exempt
def log_frontend_activity(request):
    """API para logging de actividad del frontend"""
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action', 'unknown')
            activity_data = data.get('data', {})
            
            # Agregar contexto de la sesión
            activity_data.update({
                'session_key': request.session.session_key,
                'user_id': request.user.id if request.user.is_authenticated else None,
                'ip_address': request.session.get('ip_address', 'unknown'),
                'timestamp': datetime.now().isoformat()
            })
            
            # Log de la actividad
            import logging
            logger = logging.getLogger('django.request')
            logger.info(f"Frontend Activity - {action}: {json.dumps(activity_data)}")
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})

@login_required
def debug_all_sessions(request):
    """
    Vista para mostrar todas las sesiones activas (solo para superusuarios)
    """
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Acceso denegado'}, status=403)
    
    # Obtener todas las sesiones no expiradas
    now = timezone.now()
    active_sessions = Session.objects.filter(expire_date__gte=now)
    
    sessions_info = []
    for session in active_sessions:
        try:
            session_data = session.get_decoded()
            user_id = session_data.get('_auth_user_id')
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    pass
            
            session_info = {
                'session_key': session.session_key,
                'expire_date': session.expire_date,
                'user_id': user_id,
                'username': user.username if user else 'Anónimo',
                'session_data_keys': list(session_data.keys()),
                'is_expired': session.expire_date < now,
                'time_remaining': str(session.expire_date - now) if session.expire_date > now else 'Expirada',
                'last_activity': session_data.get('last_activity', 'No disponible'),
                'ip_address': session_data.get('ip_address', 'No disponible'),
                'request_count': session_data.get('request_count', 0)
            }
            sessions_info.append(session_info)
        except Exception as e:
            sessions_info.append({
                'session_key': session.session_key,
                'error': str(e)
            })
    
    context = {
        'sessions_info': sessions_info,
        'total_sessions': len(sessions_info),
    }
    
    return render(request, 'auditoria/debug_all_sessions.html', context)

@csrf_exempt
def test_session_modification(request):
    """
    Vista para probar modificaciones de sesión
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'set_test_data':
            request.session['test_timestamp'] = timezone.now().isoformat()
            request.session['test_counter'] = request.session.get('test_counter', 0) + 1
            request.session['test_data'] = {
                'message': 'Datos de prueba',
                'user': request.user.username if request.user.is_authenticated else 'Anónimo'
            }
            return JsonResponse({'success': True, 'message': 'Datos de prueba agregados a la sesión'})
        
        elif action == 'clear_test_data':
            if 'test_timestamp' in request.session:
                del request.session['test_timestamp']
            if 'test_counter' in request.session:
                del request.session['test_counter']
            if 'test_data' in request.session:
                del request.session['test_data']
            return JsonResponse({'success': True, 'message': 'Datos de prueba eliminados de la sesión'})
        
        elif action == 'flush_session':
            request.session.flush()
            return JsonResponse({'success': True, 'message': 'Sesión completamente limpiada'})
    
    return JsonResponse({'error': 'Acción no válida'}, status=400)

def cookie_test_view(request):
    """
    Vista para probar el manejo de cookies
    """
    response_data = {
        'current_cookies': dict(request.COOKIES),
        'session_key': request.session.session_key,
        'csrf_token': request.META.get('CSRF_COOKIE', 'No encontrado')
    }
    
    response = JsonResponse(response_data)
    
    # Establecer una cookie de prueba
    response.set_cookie(
        'test_cookie', 
        'valor_de_prueba',
        max_age=3600,  # 1 hora
        secure=False,  # Para desarrollo
        httponly=True,
        samesite='Lax'
    )
    
    return response
