"""
Tareas de Celery para procesamiento de transcripción y diarización
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
import os
import tempfile
import shutil
from typing import Dict, Any
import json

from .models import Transcripcion, EstadoTranscripcion
from .whisper_helper import WhisperProcessor
from .pyannote_helper import PyannoteProcessor
from .logging_helper import log_transcripcion_accion, log_transcripcion_error

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=2)
def procesar_transcripcion_completa(self, transcripcion_id: int):
    """
    Tarea principal que procesa transcripción completa con Whisper + pyannote
    
    Args:
        transcripcion_id: ID de la transcripción a procesar
    """
    transcripcion = None
    archivo_temporal = None
    
    try:
        # Obtener transcripción
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        logger.info(f"Iniciando procesamiento de transcripción {transcripcion_id}")
        
        # Actualizar estado
        transcripcion.estado = EstadoTranscripcion.EN_PROCESO
        transcripcion.fecha_inicio_procesamiento = timezone.now()
        transcripcion.progreso = 10
        transcripcion.save()
        
        # Obtener configuración
        configuracion = transcripcion.get_configuracion_completa()
        logger.info(f"Configuración: {configuracion}")
        
        # Verificar archivo de audio
        archivo_audio = transcripcion.procesamiento_audio.archivo_audio
        if not archivo_audio or not os.path.exists(archivo_audio.path):
            # Intentar con archivo mejorado
            archivo_audio = transcripcion.procesamiento_audio.archivo_mejorado
            if not archivo_audio or not os.path.exists(archivo_audio.path):
                raise Exception("No se encontró archivo de audio para procesar")
        
        archivo_audio_path = archivo_audio.path
        logger.info(f"Procesando archivo: {archivo_audio_path}")
        
        # Paso 1: Transcripción con Whisper
        transcripcion.estado = EstadoTranscripcion.TRANSCRIBIENDO
        transcripcion.progreso = 20
        transcripcion.mensaje_estado = "Transcribiendo audio con Whisper..."
        transcripcion.save()
        
        resultado_whisper = procesar_con_whisper(archivo_audio_path, configuracion)
        
        if not resultado_whisper.get('exito'):
            raise Exception(f"Error en Whisper: {resultado_whisper.get('error')}")
        
        logger.info("Transcripción con Whisper completada")
        transcripcion.progreso = 50
        transcripcion.save()
        
        # Paso 2: Diarización con pyannote
        transcripcion.estado = EstadoTranscripcion.DIARIZANDO
        transcripcion.progreso = 60
        transcripcion.mensaje_estado = "Identificando hablantes con pyannote..."
        transcripcion.save()
        
        resultado_pyannote = procesar_con_pyannote(archivo_audio_path, configuracion)
        
        if not resultado_pyannote.get('exito'):
            logger.warning(f"Error en pyannote: {resultado_pyannote.get('error')}")
            # Continuar sin diarización si falla
            resultado_pyannote = {
                'exito': True,
                'hablantes': {'speaker_0': 'Hablante Único'},
                'segmentos_hablantes': [],
                'num_hablantes': 1,
                'estadisticas': {}
            }
        
        logger.info("Diarización con pyannote completada")
        transcripcion.progreso = 80
        transcripcion.save()
        
        # Paso 3: Combinar resultados
        transcripcion.estado = EstadoTranscripcion.PROCESANDO
        transcripcion.progreso = 90
        transcripcion.mensaje_estado = "Combinando transcripción y diarización..."
        transcripcion.save()
        
        resultado_final = combinar_resultados(resultado_whisper, resultado_pyannote)
        
        # Paso 4: Guardar resultados
        transcripcion.texto_completo = resultado_final.get('transcripcion_formateada', '')
        transcripcion.datos_whisper = resultado_whisper
        transcripcion.datos_pyannote = resultado_pyannote
        transcripcion.resultado_final = resultado_final
        transcripcion.hablantes_detectados = resultado_final.get('hablantes', {})
        transcripcion.num_hablantes = resultado_final.get('num_hablantes', 1)
        
        # Generar estadísticas
        estadisticas = generar_estadisticas_transcripcion(resultado_final)
        transcripcion.estadisticas_procesamiento = estadisticas
        
        # Completar
        transcripcion.estado = EstadoTranscripcion.COMPLETADO
        transcripcion.progreso = 100
        transcripcion.mensaje_estado = "Transcripción completada exitosamente"
        transcripcion.fecha_completado = timezone.now()
        transcripcion.save()
        
        log_transcripcion_accion(
            transcripcion, 
            'transcripcion_completada',
            {
                'duracion_procesamiento': (timezone.now() - transcripcion.fecha_inicio_procesamiento).total_seconds(),
                'num_hablantes': transcripcion.num_hablantes,
                'palabras_transcritas': len(transcripcion.texto_completo.split())
            }
        )
        
        logger.info(f"Transcripción {transcripcion_id} completada exitosamente")
        
        return {
            'exito': True,
            'transcripcion_id': transcripcion_id,
            'num_hablantes': transcripcion.num_hablantes,
            'duracion_texto': len(transcripcion.texto_completo)
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error procesando transcripción {transcripcion_id}: {error_msg}")
        
        if transcripcion:
            transcripcion.estado = EstadoTranscripcion.ERROR
            transcripcion.mensaje_error = error_msg
            transcripcion.fecha_completado = timezone.now()
            transcripcion.save()
            
            log_transcripcion_error(
                transcripcion,
                'error_procesamiento',
                error_msg,
                {'task_id': self.request.id}
            )
        
        # Reintentar si es posible
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando transcripción {transcripcion_id} en 60 segundos...")
            raise self.retry(countdown=60, exc=e)
        
        return {
            'exito': False,
            'error': error_msg,
            'transcripcion_id': transcripcion_id
        }
    
    finally:
        # Limpiar archivo temporal si existe
        if archivo_temporal and os.path.exists(archivo_temporal):
            try:
                os.unlink(archivo_temporal)
            except:
                pass


def procesar_con_whisper(archivo_audio: str, configuracion: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa audio con Whisper para transcripción
    """
    whisper_processor = None
    try:
        whisper_processor = WhisperProcessor()
        resultado = whisper_processor.transcribir_audio(archivo_audio, configuracion)
        return resultado
        
    except Exception as e:
        logger.error(f"Error en procesamiento Whisper: {str(e)}")
        return {'exito': False, 'error': str(e)}
        
    finally:
        if whisper_processor:
            whisper_processor.limpiar_modelo()


def procesar_con_pyannote(archivo_audio: str, configuracion: Dict[str, Any]) -> Dict[str, Any]:
    """
    Procesa audio con pyannote para diarización
    """
    pyannote_processor = None
    try:
        pyannote_processor = PyannoteProcessor()
        resultado = pyannote_processor.diarizar_audio(archivo_audio, configuracion)
        return resultado
        
    except Exception as e:
        logger.error(f"Error en procesamiento pyannote: {str(e)}")
        return {'exito': False, 'error': str(e)}
        
    finally:
        if pyannote_processor:
            pyannote_processor.limpiar_pipeline()


def combinar_resultados(resultado_whisper: Dict[str, Any], 
                       resultado_pyannote: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combina resultados de Whisper y pyannote
    """
    try:
        pyannote_processor = PyannoteProcessor()
        resultado_combinado = pyannote_processor.combinar_transcripcion_diarizacion(
            resultado_whisper, resultado_pyannote
        )
        return resultado_combinado
        
    except Exception as e:
        logger.error(f"Error combinando resultados: {str(e)}")
        # Fallback: usar solo transcripción de Whisper
        return {
            'exito': True,
            'segmentos_combinados': resultado_whisper.get('segmentos', []),
            'transcripcion_formateada': resultado_whisper.get('texto_completo', ''),
            'hablantes': {'speaker_0': 'Hablante Único'},
            'num_hablantes': 1,
            'estadisticas': {}
        }


def generar_estadisticas_transcripcion(resultado_final: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera estadísticas del procesamiento
    """
    try:
        segmentos = resultado_final.get('segmentos_combinados', [])
        texto_completo = resultado_final.get('transcripcion_formateada', '')
        
        estadisticas = {
            'num_segmentos': len(segmentos),
            'duracion_total': resultado_final.get('duracion_total', 0.0),
            'num_palabras': len(texto_completo.split()) if texto_completo else 0,
            'num_caracteres': len(texto_completo) if texto_completo else 0,
            'hablantes_estadisticas': resultado_final.get('estadisticas', {}),
            'promedio_duracion_segmento': 0.0
        }
        
        if segmentos:
            duraciones = [seg.get('duracion', 0) for seg in segmentos]
            estadisticas['promedio_duracion_segmento'] = sum(duraciones) / len(duraciones)
            estadisticas['segmento_mas_largo'] = max(duraciones)
            estadisticas['segmento_mas_corto'] = min(duraciones)
        
        return estadisticas
        
    except Exception as e:
        logger.error(f"Error generando estadísticas: {str(e)}")
        return {}
