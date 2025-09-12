"""
Helper para logging específico del módulo de transcripción
"""
import json
import logging
from datetime import datetime
from django.db import connection
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


def log_transcripcion_accion(transcripcion, accion, detalles=None, usuario=None):
    """
    Registra acciones importantes realizadas en transcripciones
    """
    try:
        logger.info(f"Acción de transcripción: {accion} para transcripción {transcripcion.id if transcripcion else 'N/A'}")
    except Exception as e:
        logger.error(f"Error al registrar acción de transcripción: {str(e)}")


def log_transcripcion_navegacion(request, transcripcion, vista, parametros=None):
    """
    Registra navegación y acceso a vistas de transcripción
    """
    try:
        logger.info(f"Navegación transcripción - Vista: {vista}, Usuario: {request.user.id if request.user.is_authenticated else 'Anónimo'}")
    except Exception as e:
        logger.error(f"Error al registrar navegación de transcripción: {str(e)}")


def log_transcripcion_edicion(transcripcion, usuario, tipo_edicion, cambios):
    """
    Registra ediciones realizadas en transcripciones
    """
    try:
        logger.info(f"Edición {tipo_edicion} en transcripción {transcripcion.id} por {usuario.username}")
    except Exception as e:
        logger.error(f"Error al registrar edición de transcripción: {str(e)}")


def log_transcripcion_error(transcripcion, error_tipo, error_mensaje, contexto=None):
    """
    Registra errores específicos del procesamiento de transcripción
    """
    try:
        logger.error(f"Error de transcripción: {error_tipo} - {error_mensaje}")
    except Exception as e:
        logger.error(f"Error al registrar error de transcripción: {str(e)}")


def log_transcripcion_admin(usuario, accion, detalles=None):
    """
    Registra acciones administrativas relacionadas con transcripciones
    """
    try:
        logger.info(f"Acción admin transcripción: {accion} por {usuario.username}")
    except Exception as e:
        logger.error(f"Error al registrar acción admin de transcripción: {str(e)}")


def log_transcripcion_estadisticas(transcripcion, estadisticas, tiempo_calculo=None):
    """
    Registra la generación de estadísticas de transcripción
    """
    try:
        logger.info(f"Estadísticas generadas para transcripción {transcripcion.id}")
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
