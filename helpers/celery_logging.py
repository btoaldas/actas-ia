# ============================================================================
# Sistema de Logging para Celery - Actas Municipales
# Archivo: helpers/celery_logging.py
# ============================================================================

import json
import time
from celery.signals import (
    task_prerun, task_postrun, task_failure, task_retry, 
    task_success, worker_ready, worker_shutdown
)
from django.db import connection
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger('celery_audit')

class CeleryAuditLogger:
    """
    Clase para manejar el logging de tareas Celery
    """
    
    @staticmethod
    def log_celery_task(task_id, task_name, estado, **kwargs):
        """Registra actividad de tarea Celery en la base de datos"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO logs.celery_logs (
                        task_id, task_name, estado, worker_name, queue_name,
                        tiempo_inicio, tiempo_fin, duracion_segundos,
                        usuario_que_inicio_id, parametros_entrada, resultado,
                        error_mensaje, error_traceback, reintentos, prioridad,
                        datos_contexto
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (task_id) DO UPDATE SET
                        estado = EXCLUDED.estado,
                        tiempo_fin = EXCLUDED.tiempo_fin,
                        duracion_segundos = EXCLUDED.duracion_segundos,
                        resultado = EXCLUDED.resultado,
                        error_mensaje = EXCLUDED.error_mensaje,
                        error_traceback = EXCLUDED.error_traceback,
                        reintentos = EXCLUDED.reintentos
                """, [
                    task_id,
                    task_name,
                    estado,
                    kwargs.get('worker_name'),
                    kwargs.get('queue_name', 'default'),
                    kwargs.get('tiempo_inicio'),
                    kwargs.get('tiempo_fin'),
                    kwargs.get('duracion_segundos'),
                    kwargs.get('usuario_que_inicio_id'),
                    json.dumps(kwargs.get('parametros_entrada')) if kwargs.get('parametros_entrada') else None,
                    json.dumps(kwargs.get('resultado')) if kwargs.get('resultado') else None,
                    kwargs.get('error_mensaje'),
                    kwargs.get('error_traceback'),
                    kwargs.get('reintentos', 0),
                    kwargs.get('prioridad', 5),
                    json.dumps(kwargs.get('datos_contexto')) if kwargs.get('datos_contexto') else None
                ])
                
        except Exception as e:
            logger.error(f"Error registrando log de Celery: {e}")

# Variables globales para tracking de tiempo
task_start_times = {}

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Se ejecuta antes de que inicie una tarea"""
    start_time = time.time()
    task_start_times[task_id] = start_time
    
    # Obtener información del usuario si está disponible en los argumentos
    usuario_id = None
    if args and len(args) > 0:
        # Buscar user_id en los argumentos
        for arg in args:
            if isinstance(arg, dict) and 'user_id' in arg:
                usuario_id = arg['user_id']
                break
            elif isinstance(arg, int) and arg > 0:  # Asumir que el primer entero es user_id
                usuario_id = arg
                break
    
    if kwargs and 'user_id' in kwargs:
        usuario_id = kwargs['user_id']
    
    # Preparar parámetros de entrada (sin datos sensibles)
    parametros_entrada = {
        'args_count': len(args) if args else 0,
        'kwargs_keys': list(kwargs.keys()) if kwargs else [],
        'task_name': task.name if hasattr(task, 'name') else str(sender)
    }
    
    # Registrar inicio de tarea
    CeleryAuditLogger.log_celery_task(
        task_id=task_id,
        task_name=task.name if hasattr(task, 'name') else str(sender),
        estado='STARTED',
        tiempo_inicio=timezone.now(),
        usuario_que_inicio_id=usuario_id,
        parametros_entrada=parametros_entrada,
        worker_name=kwds.get('hostname'),
        datos_contexto={
            'retries': getattr(task, 'retries', 0) if task else 0,
            'eta': str(getattr(task, 'eta', None)) if task and hasattr(task, 'eta') else None
        }
    )

@task_postrun.connect  
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Se ejecuta después de que termina una tarea (exitosa o fallida)"""
    end_time = time.time()
    start_time = task_start_times.pop(task_id, end_time)
    duration = int(end_time - start_time)
    
    # Preparar resultado (limitado para evitar logs enormes)
    resultado = None
    if retval is not None:
        if isinstance(retval, (dict, list)):
            resultado = retval
        else:
            resultado = {'result': str(retval)[:1000]}  # Limitar a 1000 caracteres
    
    CeleryAuditLogger.log_celery_task(
        task_id=task_id,
        task_name=task.name if hasattr(task, 'name') else str(sender),
        estado=state or 'COMPLETED',
        tiempo_fin=timezone.now(),
        duracion_segundos=duration,
        resultado=resultado,
        worker_name=kwds.get('hostname')
    )

@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Se ejecuta cuando una tarea termina exitosamente"""
    # El estado ya se maneja en task_postrun, aquí solo loggeamos información adicional
    logger.info(f"Tarea {sender} completada exitosamente")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs):
    """Se ejecuta cuando una tarea falla"""
    import traceback as tb
    
    error_traceback = None
    if einfo:
        error_traceback = str(einfo)
    elif traceback:
        error_traceback = tb.format_exc()
    
    CeleryAuditLogger.log_celery_task(
        task_id=task_id,
        task_name=sender.name if hasattr(sender, 'name') else str(sender),
        estado='FAILURE',
        tiempo_fin=timezone.now(),
        error_mensaje=str(exception) if exception else 'Error desconocido',
        error_traceback=error_traceback,
        worker_name=kwargs.get('hostname')
    )
    
    # También registrar en logs de errores del sistema
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.errores_sistema (
                    nivel_error, codigo_error, mensaje_error, stack_trace,
                    contexto_aplicacion, entorno
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """, [
                'ERROR',
                'CELERY_TASK_FAILURE',
                f"Fallo en tarea Celery: {sender}",
                error_traceback,
                json.dumps({
                    'task_id': task_id,
                    'task_name': sender.name if hasattr(sender, 'name') else str(sender),
                    'exception_type': type(exception).__name__ if exception else 'Unknown'
                }),
                getattr(settings, 'ENVIRONMENT', 'production')
            ])
    except Exception as e:
        logger.error(f"Error registrando fallo de tarea en errores_sistema: {e}")

@task_retry.connect
def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwargs):
    """Se ejecuta cuando una tarea va a reintentarse"""
    
    CeleryAuditLogger.log_celery_task(
        task_id=task_id,
        task_name=sender.name if hasattr(sender, 'name') else str(sender),
        estado='RETRY',
        tiempo_fin=timezone.now(),
        error_mensaje=str(reason) if reason else 'Reintento programado',
        reintentos=getattr(sender, 'retries', 0) + 1 if sender else 1,
        worker_name=kwargs.get('hostname')
    )

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Se ejecuta cuando un worker está listo"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs (
                    nivel, categoria, subcategoria, mensaje, datos_extra
                ) VALUES (%s, %s, %s, %s, %s)
            """, [
                'INFO',
                'CELERY',
                'WORKER_READY',
                f'Worker {sender} está listo para recibir tareas',
                json.dumps({
                    'worker_name': str(sender),
                    'timestamp': timezone.now().isoformat()
                })
            ])
    except Exception as e:
        logger.error(f"Error registrando worker ready: {e}")

@worker_shutdown.connect  
def worker_shutdown_handler(sender=None, **kwargs):
    """Se ejecuta cuando un worker se apaga"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO logs.sistema_logs (
                    nivel, categoria, subcategoria, mensaje, datos_extra
                ) VALUES (%s, %s, %s, %s, %s)
            """, [
                'WARNING',
                'CELERY', 
                'WORKER_SHUTDOWN',
                f'Worker {sender} se está apagando',
                json.dumps({
                    'worker_name': str(sender),
                    'timestamp': timezone.now().isoformat()
                })
            ])
    except Exception as e:
        logger.error(f"Error registrando worker shutdown: {e}")


# ============================================================================
# DECORADOR PARA TAREAS PERSONALIZADAS
# ============================================================================

def logged_task(bind=True, **options):
    """
    Decorador para tareas Celery que incluye logging automático mejorado
    
    Uso:
    @logged_task
    def mi_tarea(self, user_id, datos):
        # código de la tarea
        return resultado
    """
    from celery import current_app
    
    def decorator(func):
        # Configurar la tarea con bind=True por defecto
        task_options = {'bind': True}
        task_options.update(options)
        
        @current_app.task(**task_options)
        def wrapper(self, *args, **kwargs):
            task_id = self.request.id
            task_name = self.name
            
            # Registrar inicio detallado
            start_time = time.time()
            
            # Extraer user_id si está disponible
            user_id = None
            if args and len(args) > 0 and isinstance(args[0], int):
                user_id = args[0]
            elif 'user_id' in kwargs:
                user_id = kwargs['user_id']
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO logs.celery_logs (
                            task_id, task_name, estado, tiempo_inicio,
                            usuario_que_inicio_id, parametros_entrada, prioridad
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, [
                        task_id,
                        task_name,
                        'STARTED',
                        timezone.now(),
                        user_id,
                        json.dumps({
                            'args_summary': f"{len(args)} argumentos",
                            'kwargs_keys': list(kwargs.keys()),
                            'task_retries': self.request.retries
                        }),
                        kwargs.get('priority', 5)
                    ])
            except Exception as e:
                logger.error(f"Error iniciando log de tarea {task_name}: {e}")
            
            try:
                # Ejecutar la tarea original
                resultado = func(self, *args, **kwargs)
                
                # Registrar éxito
                duration = int(time.time() - start_time)
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE logs.celery_logs 
                        SET estado = %s, tiempo_fin = %s, duracion_segundos = %s, resultado = %s
                        WHERE task_id = %s
                    """, [
                        'SUCCESS',
                        timezone.now(),
                        duration,
                        json.dumps(resultado if isinstance(resultado, (dict, list)) else {'result': str(resultado)[:500]}),
                        task_id
                    ])
                
                return resultado
                
            except Exception as exc:
                # Registrar fallo
                duration = int(time.time() - start_time)
                
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE logs.celery_logs 
                        SET estado = %s, tiempo_fin = %s, duracion_segundos = %s, 
                            error_mensaje = %s, reintentos = %s
                        WHERE task_id = %s
                    """, [
                        'FAILURE',
                        timezone.now(),
                        duration,
                        str(exc),
                        self.request.retries,
                        task_id
                    ])
                
                # Re-lanzar la excepción
                raise exc
        
        return wrapper
    return decorator


# ============================================================================
# FUNCIONES AUXILIARES PARA REPORTES
# ============================================================================

def obtener_estadisticas_celery(dias=7):
    """Obtiene estadísticas de tareas Celery de los últimos días"""
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                task_name,
                estado,
                COUNT(*) as total,
                AVG(duracion_segundos) as duracion_promedio,
                MIN(duracion_segundos) as duracion_minima,
                MAX(duracion_segundos) as duracion_maxima,
                COUNT(CASE WHEN estado = 'FAILURE' THEN 1 END) as fallos
            FROM logs.celery_logs 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY task_name, estado
            ORDER BY task_name, estado
        """, [dias])
        
        resultados = cursor.fetchall()
        
        estadisticas = {}
        for row in resultados:
            task_name = row[0]
            if task_name not in estadisticas:
                estadisticas[task_name] = {}
            
            estadisticas[task_name][row[1]] = {
                'total': row[2],
                'duracion_promedio': float(row[3]) if row[3] else 0,
                'duracion_minima': row[4],
                'duracion_maxima': row[5],
                'fallos': row[6]
            }
    
    return estadisticas

def obtener_tareas_lentas(limite_segundos=60, dias=7):
    """Obtiene tareas que han tardado más del límite especificado"""
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                task_name,
                task_id,
                duracion_segundos,
                tiempo_inicio,
                usuario_que_inicio_id,
                parametros_entrada
            FROM logs.celery_logs
            WHERE duracion_segundos > %s 
            AND timestamp >= CURRENT_DATE - INTERVAL '%s days'
            ORDER BY duracion_segundos DESC
            LIMIT 50
        """, [limite_segundos, dias])
        
        return [
            {
                'task_name': row[0],
                'task_id': row[1], 
                'duracion_segundos': row[2],
                'tiempo_inicio': row[3],
                'usuario_que_inicio_id': row[4],
                'parametros_entrada': json.loads(row[5]) if row[5] else None
            }
            for row in cursor.fetchall()
        ]
