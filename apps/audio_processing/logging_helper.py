"""
Helper para logging y auditoría del módulo de procesamiento de audio
"""
import json
import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.auditoria.models import SistemaLogs, NavegacionUsuarios, AdminLogs, ArchivoLogs
from apps.audio_processing.models import ProcesamientoAudio

User = get_user_model()

# Configurar logger específico para audio processing
logger = logging.getLogger('audio_processing')


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Obtener User Agent del cliente"""
    return request.META.get('HTTP_USER_AGENT', '')


def log_sistema(nivel, categoria, mensaje, request=None, usuario=None, datos_extra=None, 
                subcategoria=None, modulo='audio_processing'):
    """
    Registrar log del sistema
    
    Args:
        nivel: INFO, WARNING, ERROR, DEBUG
        categoria: PROCESAMIENTO_AUDIO, CRUD, API, etc.
        mensaje: Descripción del evento
        request: HttpRequest object (opcional)
        usuario: User object (opcional)
        datos_extra: Dict con datos adicionales
        subcategoria: Subcategoría específica
        modulo: Módulo que genera el log
    """
    try:
        # Obtener datos del request si está disponible
        ip_address = None
        user_agent = None
        url_solicitada = None
        metodo_http = None
        session_id = None
        
        if request:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
            url_solicitada = request.get_full_path()
            metodo_http = request.method
            session_id = request.session.session_key
            
            # Si no hay usuario pasado, intentar obtenerlo del request
            if not usuario and hasattr(request, 'user') and request.user.is_authenticated:
                usuario = request.user
        
        # Crear el log
        log_data = {
            'nivel': nivel,
            'categoria': categoria,
            'subcategoria': subcategoria,
            'mensaje': mensaje,
            'datos_extra': datos_extra or {},
            'modulo': modulo,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'url_solicitada': url_solicitada,
            'metodo_http': metodo_http,
            'session_id': session_id,
        }
        
        if usuario:
            log_data['usuario_id'] = usuario.id
            log_data['datos_extra']['username'] = usuario.username
        
        # Guardar en BD usando SQL directo para evitar problemas de modelos unmanaged
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs (
                    timestamp, nivel, categoria, subcategoria, usuario_id, session_id,
                    ip_address, user_agent, mensaje, datos_extra, modulo, url_solicitada,
                    metodo_http, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                timezone.now(),
                nivel,
                categoria,
                subcategoria,
                log_data.get('usuario_id'),
                session_id,
                ip_address,
                user_agent,
                mensaje,
                json.dumps(datos_extra or {}),
                modulo,
                url_solicitada,
                metodo_http,
                timezone.now()
            ])
    
    except Exception as e:
        # Fallback al logger de Python si falla la BD
        logger.error(f"Error al guardar log en BD: {e}")
        logger.log(getattr(logging, nivel, logging.INFO), f"{categoria}: {mensaje}")


def log_navegacion(request, accion_realizada=None, elemento_interactuado=None, 
                   datos_formulario=None, tiempo_permanencia_ms=None):
    """
    Registrar navegación del usuario
    """
    try:
        if not request.user.is_authenticated:
            return
            
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.navegacion_usuarios (
                    usuario_id, session_id, timestamp, url_visitada, url_anterior,
                    metodo_http, parametros_get, parametros_post, tiempo_permanencia_ms,
                    accion_realizada, elemento_interactuado, datos_formulario, ip_address
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                request.user.id,
                request.session.session_key,
                timezone.now(),
                request.get_full_path(),
                request.META.get('HTTP_REFERER'),
                request.method,
                json.dumps(dict(request.GET)) if request.GET else None,
                json.dumps(dict(request.POST)) if request.POST else None,
                tiempo_permanencia_ms,
                accion_realizada,
                elemento_interactuado,
                json.dumps(datos_formulario) if datos_formulario else None,
                get_client_ip(request)
            ])
    except Exception as e:
        logger.error(f"Error al guardar log de navegación: {e}")


def log_admin_action(request, modelo_afectado, accion, objeto_id=None, 
                     campos_modificados=None, valores_anteriores=None, valores_nuevos=None):
    """
    Registrar acción administrativa
    """
    try:
        if not request.user.is_authenticated:
            return
            
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.admin_logs (
                    timestamp, usuario_id, modelo_afectado, accion, objeto_id,
                    campos_modificados, valores_anteriores, valores_nuevos,
                    ip_address, user_agent, url_admin, exitoso
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                timezone.now(),
                request.user.id,
                modelo_afectado,
                accion,
                str(objeto_id) if objeto_id else None,
                json.dumps(campos_modificados) if campos_modificados else None,
                json.dumps(valores_anteriores) if valores_anteriores else None,
                json.dumps(valores_nuevos) if valores_nuevos else None,
                get_client_ip(request),
                get_user_agent(request),
                request.get_full_path(),
                True
            ])
    except Exception as e:
        logger.error(f"Error al guardar log admin: {e}")


def log_archivo_operacion(operacion, archivo_nombre, archivo_path, archivo_size_bytes=0,
                         archivo_tipo_mime='', request=None, usuario=None, resultado='SUCCESS',
                         mensaje_error=None, metadatos=None):
    """
    Registrar operación con archivos
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.archivo_logs (
                    timestamp, operacion, archivo_nombre, archivo_path, archivo_size_bytes,
                    archivo_tipo_mime, usuario_id, ip_address, resultado, mensaje_error, metadatos
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                timezone.now(),
                operacion,
                archivo_nombre,
                archivo_path,
                archivo_size_bytes,
                archivo_tipo_mime,
                usuario.id if usuario else (request.user.id if request and request.user.is_authenticated else None),
                get_client_ip(request) if request else None,
                resultado,
                mensaje_error,
                json.dumps(metadatos) if metadatos else None
            ])
    except Exception as e:
        logger.error(f"Error al guardar log de archivo: {e}")


def log_procesamiento_audio(accion, procesamiento, request=None, datos_adicionales=None):
    """
    Helper específico para logs de procesamiento de audio
    """
    datos_extra = {
        'procesamiento_id': procesamiento.id,
        'titulo': procesamiento.titulo,
        'estado': procesamiento.estado,
        'usuario_procesamiento': procesamiento.usuario.username if procesamiento.usuario else None,
    }
    
    if datos_adicionales:
        datos_extra.update(datos_adicionales)
    
    # Mapear acciones a categorías
    categoria_map = {
        'crear': 'PROCESAMIENTO_CREADO',
        'editar': 'PROCESAMIENTO_EDITADO', 
        'eliminar': 'PROCESAMIENTO_ELIMINADO',
        'listar': 'PROCESAMIENTO_LISTADO',
        'ver': 'PROCESAMIENTO_VISUALIZADO',
        'procesar': 'PROCESAMIENTO_INICIADO',
        'detener': 'PROCESAMIENTO_DETENIDO',
        'reiniciar': 'PROCESAMIENTO_REINICIADO',
    }
    
    categoria = categoria_map.get(accion, 'PROCESAMIENTO_OTRO')
    mensaje = f"Procesamiento '{procesamiento.titulo}' ({accion})"
    
    log_sistema(
        nivel='INFO',
        categoria=categoria,
        subcategoria=accion.upper(),
        mensaje=mensaje,
        request=request,
        datos_extra=datos_extra
    )
    
    # También registrar en navegación si hay request
    if request:
        log_navegacion(
            request=request,
            accion_realizada=f"procesamiento_{accion}",
            elemento_interactuado=f"procesamiento_{procesamiento.id}",
            datos_formulario={'procesamiento_id': procesamiento.id, 'accion': accion}
        )


def log_error_procesamiento(error_msg, procesamiento=None, request=None, stack_trace=None):
    """
    Log específico para errores en procesamiento de audio
    """
    datos_extra = {}
    if procesamiento:
        datos_extra.update({
            'procesamiento_id': procesamiento.id,
            'titulo': procesamiento.titulo,
            'estado': procesamiento.estado,
        })
    
    if stack_trace:
        datos_extra['stack_trace'] = stack_trace
    
    log_sistema(
        nivel='ERROR',
        categoria='PROCESAMIENTO_ERROR',
        mensaje=error_msg,
        request=request,
        datos_extra=datos_extra
    )
