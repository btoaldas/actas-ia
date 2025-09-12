import logging
import json
from datetime import datetime
from django.db import connection

logger = logging.getLogger('transcripcion')


def log_transcripcion_accion(transcripcion, accion, detalles=None, usuario=None):
    """
    Registra acciones importantes realizadas en transcripciones
    """
    try:
        detalles = detalles or {}
        
        log_data = {
            'transcripcion_id': transcripcion.id,
            'id_transcripcion': str(transcripcion.id_transcripcion),
            'audio_procesamiento_id': transcripcion.procesamiento_audio.id,
            'nombre_archivo': transcripcion.procesamiento_audio.nombre_archivo,
            'estado_actual': transcripcion.estado,
            'accion': accion,
            'detalles': detalles,
            'timestamp': datetime.now().isoformat()
        }
        
        # Agregar información del usuario si está disponible
        if usuario:
            log_data['usuario_id'] = usuario.id
            log_data['usuario_username'] = usuario.username
        elif transcripcion.usuario_creacion:
            log_data['usuario_id'] = transcripcion.usuario_creacion.id
            log_data['usuario_username'] = transcripcion.usuario_creacion.username
        
        # Insertar en la tabla de logs del sistema
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs 
                (timestamp, nivel, categoria, mensaje, datos_extra, usuario_id, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                datetime.now(),
                'INFO',
                'transcripcion',
                f"Transcripción {accion}: {transcripcion}",
                json.dumps(log_data, ensure_ascii=False),
                log_data.get('usuario_id'),
                None,  # IP se puede agregar desde la vista
                'Sistema Transcripción'
            ])
        
        logger.info(f"Acción de transcripción registrada: {accion} para transcripción {transcripcion.id}")
        
    except Exception as e:
        logger.error(f"Error al registrar acción de transcripción: {str(e)}")


def log_transcripcion_navegacion(request, transcripcion, vista, parametros=None):
    """
    Registra navegación y acceso a vistas de transcripción
    """
    try:
        parametros = parametros or {}
        
        nav_data = {
            'vista': vista,
            'transcripcion_id': transcripcion.id if transcripcion else None,
            'usuario_id': request.user.id if request.user.is_authenticated else None,
            'parametros': parametros,
            'session_key': request.session.session_key,
            'timestamp': datetime.now().isoformat()
        }
        
        if transcripcion:
            nav_data.update({
                'estado_transcripcion': transcripcion.estado,
                'audio_procesamiento_id': transcripcion.procesamiento_audio.id,
                'nombre_archivo': transcripcion.procesamiento_audio.nombre_archivo
            })
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs 
                (timestamp, nivel, categoria, mensaje, datos_extra, usuario_id, ip_address, user_agent, session_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                datetime.now(),
                'INFO',
                'transcripcion_navegacion',
                f"Acceso a vista {vista} de transcripción",
                json.dumps(nav_data, ensure_ascii=False),
                request.user.id if request.user.is_authenticated else None,
                _get_client_ip(request),
                request.META.get('HTTP_USER_AGENT', ''),
                request.session.session_key
            ])
        
    except Exception as e:
        logger.error(f"Error al registrar navegación de transcripción: {str(e)}")


def log_transcripcion_edicion(transcripcion, usuario, tipo_edicion, cambios):
    """
    Registra ediciones realizadas en transcripciones
    """
    try:
        edicion_data = {
            'transcripcion_id': transcripcion.id,
            'tipo_edicion': tipo_edicion,
            'cambios_realizados': cambios,
            'usuario_id': usuario.id,
            'usuario_username': usuario.username,
            'timestamp_edicion': datetime.now().isoformat(),
            'version_anterior': cambios.get('version_anterior'),
            'version_nueva': cambios.get('version_nueva')
        }
        
        # Información adicional del contexto
        if 'segmento_editado' in cambios:
            edicion_data['segmento_info'] = {
                'inicio': cambios['segmento_editado'].get('inicio'),
                'fin': cambios['segmento_editado'].get('fin'),
                'hablante': cambios['segmento_editado'].get('hablante'),
                'texto_anterior': cambios.get('texto_anterior'),
                'texto_nuevo': cambios.get('texto_nuevo')
            }
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs 
                (timestamp, nivel, categoria, mensaje, datos_extra, usuario_id, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                datetime.now(),
                'INFO',
                'transcripcion_edicion',
                f"Edición {tipo_edicion} en transcripción {transcripcion.id}",
                json.dumps(edicion_data, ensure_ascii=False),
                usuario.id,
                cambios.get('ip_address'),
                'Editor Transcripción'
            ])
        
        logger.info(f"Edición registrada: {tipo_edicion} por {usuario.username} en transcripción {transcripcion.id}")
        
    except Exception as e:
        logger.error(f"Error al registrar edición de transcripción: {str(e)}")


def log_transcripcion_error(transcripcion, error_tipo, error_mensaje, contexto=None):
    """
    Registra errores específicos del procesamiento de transcripción
    """
    try:
        contexto = contexto or {}
        
        error_data = {
            'transcripcion_id': transcripcion.id if transcripcion else None,
            'error_tipo': error_tipo,
            'error_mensaje': error_mensaje,
            'contexto': contexto,
            'estado_transcripcion': transcripcion.estado if transcripcion else None,
            'timestamp': datetime.now().isoformat()
        }
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs 
                (timestamp, nivel, categoria, mensaje, datos_extra, usuario_id, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                datetime.now(),
                'ERROR',
                'transcripcion_error',
                f"Error en transcripción {transcripcion.id if transcripcion else 'N/A'}: {error_mensaje}",
                json.dumps(error_data, ensure_ascii=False),
                transcripcion.usuario_creacion.id if transcripcion and transcripcion.usuario_creacion else None,
                None,
                'Sistema Transcripción'
            ])
        
        logger.error(f"Error de transcripción registrado: {error_tipo} - {error_mensaje}")
        
    except Exception as e:
        logger.error(f"Error al registrar error de transcripción: {str(e)}")


def log_transcripcion_estadisticas(transcripcion, estadisticas, tiempo_calculo=None):
    """
    Registra la generación de estadísticas de transcripción
    """
    try:
        stats_data = {
            'transcripcion_id': transcripcion.id,
            'estadisticas_generadas': estadisticas,
            'tiempo_calculo_segundos': tiempo_calculo,
            'numero_hablantes': transcripcion.numero_hablantes,
            'numero_segmentos': transcripcion.numero_segmentos,
            'palabras_totales': transcripcion.palabras_totales,
            'timestamp': datetime.now().isoformat()
        }
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs 
                (timestamp, nivel, categoria, mensaje, datos_extra, usuario_id, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                datetime.now(),
                'INFO',
                'transcripcion_estadisticas',
                f"Estadísticas generadas para transcripción {transcripcion.id}",
                json.dumps(stats_data, ensure_ascii=False),
                transcripcion.usuario_creacion.id if transcripcion.usuario_creacion else None,
                None,
                'Sistema Estadísticas'
            ])
        
    except Exception as e:
        logger.error(f"Error al registrar estadísticas de transcripción: {str(e)}")


def _get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
