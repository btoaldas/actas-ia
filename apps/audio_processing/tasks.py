"""
Tareas de Celery para procesamiento de audio en background.
Actualizado para usar el nuevo pipeline robusto.
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from pathlib import Path
import os
import logging
import tempfile

from .models import ProcesamientoAudio, LogProcesamiento
from .services.audio_pipeline import AudioProcessor, AudioPipelineError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=2, autoretry_for=(Exception,), retry_backoff=True)
def procesar_audio_task(self, procesamiento_id: int):
    """
    Tarea de Celery mejorada para procesar audio en background.
    
    Args:
        procesamiento_id: ID del procesamiento a ejecutar
        
    Returns:
        Resultado del procesamiento
    """
    procesamiento = ProcesamientoAudio.objects.get(id=procesamiento_id)
    
    # Verificar si ya está en proceso o completado
    if procesamiento.estado in ('procesando', 'completado'):
        logger.info(f"Procesamiento {procesamiento_id} ya está en estado {procesamiento.estado}")
        return
    
    # Marcar como en proceso
    procesamiento.estado = 'procesando'
    procesamiento.progreso = 10
    procesamiento.fecha_procesamiento = timezone.now()
    procesamiento.mensaje_estado = 'Iniciando procesamiento...'
    procesamiento.save(update_fields=['estado', 'progreso', 'fecha_procesamiento', 'mensaje_estado'])
    
    # Log inicial
    LogProcesamiento.objects.create(
        procesamiento=procesamiento,
        nivel='info',
        mensaje='Iniciando procesamiento de audio con pipeline v2.0',
        detalles_json={'archivo': procesamiento.archivo_audio.name}
    )
    
    try:
        # Verificar archivo original
        if not procesamiento.archivo_audio or not os.path.exists(procesamiento.archivo_audio.path):
            raise AudioPipelineError("Archivo de audio original no encontrado")
        
        archivo_original = procesamiento.archivo_audio.path
        
        # Crear directorio de salida
        output_dir = Path(settings.MEDIA_ROOT) / "audio" / "mejorado"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generar nombre del archivo de salida
        archivo_salida = output_dir / f"proceso_{procesamiento.id}.wav"
        
        # Actualizar progreso
        procesamiento.progreso = 30
        procesamiento.mensaje_estado = 'Procesando audio...'
        procesamiento.save(update_fields=['progreso', 'mensaje_estado'])
        
        # Crear instancia del procesador
        processor = AudioProcessor()
        
        # Log de inicio de procesamiento
        LogProcesamiento.objects.create(
            procesamiento=procesamiento,
            nivel='info',
            mensaje='Iniciando pipeline de procesamiento',
            detalles_json={'pipeline': processor.pipeline_version}
        )
        
        # Obtener configuración de procesamiento
        config = procesamiento.configuracion or {}
        options = {
            'noise_reduction': config.get('aplicar_reduccion_ruido', True),
            'sox_effects': config.get('aplicar_efectos_sox', True),
            'sample_rate': config.get('sample_rate', 16000)
        }
        
        # Procesar audio
        archivo_procesado, metadata = processor.process_audio(
            archivo_original, 
            str(archivo_salida),
            options=options
        )
        
        # Actualizar progreso
        procesamiento.progreso = 80
        procesamiento.mensaje_estado = 'Guardando resultados...'
        procesamiento.save(update_fields=['progreso', 'mensaje_estado'])
        
        # Guardar resultados usando transacción atómica
        with transaction.atomic():
            # Guardar archivo mejorado
            rel_path = str(Path(archivo_procesado).relative_to(settings.MEDIA_ROOT))
            procesamiento.archivo_mejorado.name = rel_path
            
            # Guardar metadatos solo datos serializables
            safe_metadata = {
                'processed_duration': metadata.get('processed_duration'),
                'processed_sample_rate': metadata.get('processed_sample_rate'),
                'pipeline_version': metadata.get('pipeline_version', 'v2.0'),
                'original_size': metadata.get('original_size'),
                'processed_size': metadata.get('processed_size'),
                'compression_ratio': metadata.get('compression_ratio'),
                'processing_timestamp': timezone.now().isoformat()
            }
            
            procesamiento.duracion_seg = metadata.get('processed_duration')
            procesamiento.sample_rate = metadata.get('processed_sample_rate')
            procesamiento.metadatos_procesamiento = safe_metadata
            procesamiento.version_pipeline = metadata.get('pipeline_version', 'v2.0')
            
            # Actualizar estado final
            procesamiento.estado = 'completado'
            procesamiento.progreso = 100
            procesamiento.fecha_completado = timezone.now()
            procesamiento.mensaje_estado = 'Procesamiento completado exitosamente'
            
            procesamiento.save()
        
        # Log de éxito
        LogProcesamiento.objects.create(
            procesamiento=procesamiento,
            nivel='info',
            mensaje='Procesamiento completado exitosamente',
            detalles_json={
                'archivo_procesado': str(archivo_procesado),
                'duracion': metadata.get("processed_duration", 0),
                'pipeline_version': metadata.get('pipeline_version', 'v2.0'),
                'sample_rate': metadata.get('processed_sample_rate'),
                'status': 'completed'
            }
        )
        
        logger.info(f"Procesamiento {procesamiento_id} completado exitosamente")
        return {
            'status': 'success',
            'procesamiento_id': procesamiento_id,
            'archivo_procesado': rel_path,
            'duracion': metadata.get('processed_duration', 0),
            'pipeline_version': metadata.get('pipeline_version', 'v2.0')
        }
        
    except Exception as e:
        # Marcar como error
        procesamiento.estado = 'error'
        procesamiento.progreso = 0
        procesamiento.mensaje_estado = f'Error: {str(e)}'
        procesamiento.save(update_fields=['estado', 'progreso', 'mensaje_estado'])
        
        # Log de error
        LogProcesamiento.objects.create(
            procesamiento=procesamiento,
            nivel='error',
            mensaje='Error durante el procesamiento',
            detalles_json={'error': str(e), 'tipo_error': type(e).__name__}
        )
        
        logger.error(f"Error procesando audio {procesamiento_id}: {e}")
        raise
        
        # Guardar configuración utilizada
        procesamiento.configuracion = {
            'normalizacion': True,
            'reduccion_ruido': True,
            'mejora_voz': True,
            'sample_rate': info_procesado['sample_rate'],
            'canales': info_procesado['canales'],
            'formato_salida': 'wav'
        }
        
        # Guardar información en resultado
        procesamiento.resultado = {
            'archivo_original': {
                'nombre': os.path.basename(archivo_original),
                'duracion': info_original['duracion'],
                'tamano_mb': info_original['tamano_bytes'] / (1024 * 1024),
                'formato': info_original['formato'],
                'bitrate': info_original['bitrate'],
                'sample_rate': info_original['sample_rate'],
                'canales': info_original['canales']
            },
            'archivo_procesado': {
                'nombre': os.path.basename(archivo_procesado),
                'duracion': info_procesado['duracion'],
                'tamano_mb': info_procesado['tamano_bytes'] / (1024 * 1024),
                'formato': info_procesado['formato'],
                'bitrate': info_procesado['bitrate'],
                'sample_rate': info_procesado['sample_rate'],
                'canales': info_procesado['canales']
            },
            'mejoras_aplicadas': [
                'Normalización de volumen (-16 LUFS)',
                'Conversión a mono (mejor para transcripción)',
                'Sample rate 16kHz (óptimo para STT)',
                'Reducción de ruido de fondo',
                'Filtro pasa-altos (80Hz) y pasa-bajos (8kHz)',
                'Compresión dinámica para mejor claridad',
                'Realce de frecuencias de voz (1kHz y 3kHz)'
            ],
            'estadisticas': {
                'reduccion_tamano': round(
                    (1 - (info_procesado['tamano_bytes'] / info_original['tamano_bytes'])) * 100, 1
                ) if info_original['tamano_bytes'] > 0 else 0,
                'tiempo_procesamiento': (timezone.now() - procesamiento.fecha_procesamiento).total_seconds()
            }
        }
        
        # Completar procesamiento
        procesamiento.estado = 'completado'
        procesamiento.progreso = 100
        procesamiento.fecha_completado = timezone.now()
        procesamiento.mensaje_estado = 'Procesamiento completado exitosamente'
        procesamiento.save()
        
        # Log de éxito
        LogProcesamiento.objects.create(
            procesamiento=procesamiento,
            nivel='info',
            mensaje='Procesamiento de audio completado exitosamente',
            detalles_json={'archivo_procesado': archivo_procesado}
        )
        
        # Estadísticas del resultado
        stats = procesamiento.resultado['estadisticas']
        LogProcesamiento.objects.create(
            procesamiento=procesamiento,
            nivel='info',
            mensaje='Estadísticas del procesamiento',
            detalles_json={
                'reduccion_tamano_pct': stats["reduccion_tamano"],
                'tiempo_procesamiento_seg': stats["tiempo_procesamiento"],
                'estadisticas_completas': stats
            }
        )
        
        logger.info(f"Procesamiento {procesamiento_id} completado exitosamente")
        
        return {
            'status': 'success',
            'procesamiento_id': procesamiento_id,
            'archivo_procesado': archivo_procesado,
            'duracion': procesamiento.duracion,
            'tamano_mb': float(procesamiento.tamano_mb)
        }
        
    except ProcesamientoAudio.DoesNotExist:
        error_msg = f"Procesamiento {procesamiento_id} no encontrado"
        logger.error(error_msg)
        return {'status': 'error', 'error': error_msg}
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error en procesamiento {procesamiento_id}: {error_msg}")
        
        try:
            # Actualizar estado de error
            procesamiento = ProcesamientoAudio.objects.get(id=procesamiento_id)
            procesamiento.estado = 'error'
            procesamiento.mensaje_estado = f'Error: {error_msg}'
            procesamiento.save()
            
            # Log de error
            LogProcesamiento.objects.create(
                procesamiento=procesamiento,
                nivel='error',
                mensaje='Error en procesamiento de audio',
                detalles_json={'error_mensaje': error_msg, 'procesamiento_id': procesamiento_id}
            )
            
        except Exception as log_error:
            logger.error(f"Error adicional al registrar fallo: {log_error}")
            
        return {
            'status': 'error',
            'procesamiento_id': procesamiento_id,
            'error': error_msg
        }


@shared_task
def limpiar_archivos_temporales():
    """
    Tarea periódica para limpiar archivos temporales antiguos
    """
    import glob
    from datetime import datetime, timedelta
    
    # Limpiar archivos temporales de más de 24 horas
    temp_patterns = [
        '/tmp/*_normalized.*',
        '/tmp/*_denoised.*',
        '/tmp/*_enhanced.*',
        '/tmp/*.prof'
    ]
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    cleaned_files = 0
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_time:
                    os.unlink(file_path)
                    cleaned_files += 1
                    logger.info(f"Archivo temporal eliminado: {file_path}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar {file_path}: {e}")
                
    logger.info(f"Limpieza completada: {cleaned_files} archivos eliminados")
    return {'files_cleaned': cleaned_files}


@shared_task
def actualizar_estadisticas_procesamiento():
    """
    Tarea para actualizar estadísticas generales del sistema
    """
    from django.db.models import Count, Avg
    from django.contrib.auth.models import User
    
    # Estadísticas generales
    stats = ProcesamientoAudio.objects.aggregate(
        total=Count('id'),
        completados=Count('id', filter={'estado': 'completado'}),
        en_proceso=Count('id', filter={'estado__in': ['pendiente', 'procesando']}),
        con_error=Count('id', filter={'estado': 'error'}),
        duracion_promedio=Avg('duracion'),
        tamano_promedio=Avg('tamano_mb')
    )
    
    # Estadísticas por usuario
    user_stats = User.objects.annotate(
        total_procesamientos=Count('procesamientos_audio'),
        completados=Count('procesamientos_audio', filter={'procesamientos_audio__estado': 'completado'})
    ).filter(total_procesamientos__gt=0)
    
    logger.info(f"Estadísticas actualizadas: {stats}")
    
    return {
        'general': stats,
        'usuarios_activos': user_stats.count(),
        'timestamp': timezone.now().isoformat()
    }
