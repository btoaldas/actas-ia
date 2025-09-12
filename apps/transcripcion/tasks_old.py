"""
Tareas de Celery para transcripción y diarización de audio
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging
import traceback
import tempfile
import os
import json
import subprocess
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("Whisper no está disponible")

try:
    from pyannote.audio import Pipeline
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    logger.warning("pyannote.audio no está disponible")


@shared_task(bind=True, max_retries=2)
def procesar_transcripcion_completa(self, transcripcion_id: int):
    """
    Tarea principal que ejecuta todo el proceso de transcripción y diarización
    """
    from apps.transcripcion.models import Transcripcion, EstadoTranscripcion
    from apps.transcripcion.logging_helper import log_transcripcion_accion
    
    try:
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        
        # Registrar inicio del procesamiento
        log_transcripcion_accion(
            transcripcion, 
            'inicio_procesamiento',
            {'task_id': self.request.id}
        )
        
        # Actualizar estado inicial
        transcripcion.estado = EstadoTranscripcion.EN_PROCESO
        transcripcion.tiempo_inicio_proceso = timezone.now()
        transcripcion.task_id_celery = self.request.id
        transcripcion.progreso_porcentaje = 0
        transcripcion.save()
        
        # Fase 1: Transcripción con Whisper
        logger.info(f"Iniciando transcripción para ID: {transcripcion_id}")
        transcripcion_result = transcribir_audio.delay(transcripcion_id)
        transcripcion.progreso_porcentaje = 25
        transcripcion.save()
        
        # Esperar resultado de transcripción
        whisper_result = transcripcion_result.get()
        if not whisper_result['success']:
            raise Exception(f"Error en transcripción: {whisper_result['error']}")
        
        # Fase 2: Diarización con pyannote
        logger.info(f"Iniciando diarización para ID: {transcripcion_id}")
        transcripcion.progreso_porcentaje = 50
        transcripcion.save()
        
        diarizacion_result = diarizar_audio.delay(transcripcion_id)
        pyannote_result = diarizacion_result.get()
        if not pyannote_result['success']:
            raise Exception(f"Error en diarización: {pyannote_result['error']}")
        
        # Fase 3: Combinar resultados
        logger.info(f"Combinando resultados para ID: {transcripcion_id}")
        transcripcion.progreso_porcentaje = 75
        transcripcion.save()
        
        combinar_result = combinar_transcripcion_diarizacion.delay(transcripcion_id)
        resultado_final = combinar_result.get()
        if not resultado_final['success']:
            raise Exception(f"Error al combinar: {resultado_final['error']}")
        
        # Fase 4: Análisis y estadísticas
        transcripcion.progreso_porcentaje = 90
        transcripcion.save()
        
        analisis_result = generar_estadisticas_transcripcion.delay(transcripcion_id)
        estadisticas = analisis_result.get()
        
        # Finalizar procesamiento
        transcripcion.refresh_from_db()
        transcripcion.estado = EstadoTranscripcion.COMPLETADO
        transcripcion.tiempo_fin_proceso = timezone.now()
        transcripcion.progreso_porcentaje = 100
        transcripcion.save()
        
        log_transcripcion_accion(
            transcripcion, 
            'procesamiento_completado',
            {'duracion_segundos': transcripcion.duracion_proceso}
        )
        
        logger.info(f"Transcripción completada para ID: {transcripcion_id}")
        
        return {
            'success': True,
            'transcripcion_id': transcripcion_id,
            'duracion_proceso': transcripcion.duracion_proceso,
            'estadisticas': estadisticas
        }
        
    except Exception as e:
        logger.error(f"Error en procesamiento completo para ID: {transcripcion_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        try:
            transcripcion = Transcripcion.objects.get(id=transcripcion_id)
            transcripcion.estado = EstadoTranscripcion.ERROR
            transcripcion.mensaje_error = str(e)
            transcripcion.tiempo_fin_proceso = timezone.now()
            transcripcion.save()
            
            log_transcripcion_accion(
                transcripcion, 
                'error_procesamiento',
                {'error': str(e), 'traceback': traceback.format_exc()}
            )
        except Exception as save_error:
            logger.error(f"Error al guardar estado de error: {str(save_error)}")
        
        raise


@shared_task(bind=True, max_retries=1)
def transcribir_audio(self, transcripcion_id: int):
    """
    Transcribe audio usando Whisper
    """
    from apps.transcripcion.models import Transcripcion, EstadoTranscripcion
    
    try:
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        
        if not WHISPER_AVAILABLE:
            # Usar transcripción simulada para desarrollo
            return _transcripcion_simulada(transcripcion)
        
        transcripcion.estado = EstadoTranscripcion.TRANSCRIBIENDO
        transcripcion.save()
        
        # Obtener configuración
        config = transcripcion.configuracion_utilizada
        if not config:
            config = transcripcion.configuracion_utilizada.__class__.get_configuracion_activa()
        
        # Cargar modelo Whisper
        modelo = whisper.load_model(config.modelo_whisper)
        
        # Obtener archivo de audio procesado
        archivo_audio = transcripcion.procesamiento_audio.archivo_mejorado
        if not archivo_audio or not os.path.exists(archivo_audio.path):
            archivo_audio = transcripcion.procesamiento_audio.archivo_original
        
        # Transcribir
        resultado = modelo.transcribe(
            archivo_audio.path,
            language=config.idioma_principal if config.idioma_principal != 'auto' else None,
            temperature=config.temperatura,
            word_timestamps=True,
            verbose=True
        )
        
        # Guardar resultados
        transcripcion.texto_completo = resultado['text']
        transcripcion.transcripcion_json = {
            'segments': resultado['segments'],
            'language': resultado['language'],
            'model_used': config.modelo_whisper,
            'timestamp': timezone.now().isoformat()
        }
        transcripcion.save()
        
        logger.info(f"Transcripción Whisper completada para ID: {transcripcion_id}")
        
        return {
            'success': True,
            'texto_completo': resultado['text'],
            'num_segmentos': len(resultado['segments'])
        }
        
    except Exception as e:
        logger.error(f"Error en transcripción Whisper para ID: {transcripcion_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True, max_retries=1)
def diarizar_audio(self, transcripcion_id: int):
    """
    Realiza diarización usando pyannote
    """
    from apps.transcripcion.models import Transcripcion, EstadoTranscripcion
    
    try:
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        
        if not PYANNOTE_AVAILABLE:
            # Usar diarización simulada para desarrollo
            return _diarizacion_simulada(transcripcion)
        
        transcripcion.estado = EstadoTranscripcion.DIARIZANDO
        transcripcion.save()
        
        # Obtener configuración
        config = transcripcion.configuracion_utilizada
        if not config:
            config = transcripcion.configuracion_utilizada.__class__.get_configuracion_activa()
        
        # Cargar pipeline de diarización
        pipeline = Pipeline.from_pretrained(config.modelo_diarizacion)
        
        # Obtener archivo de audio
        archivo_audio = transcripcion.procesamiento_audio.archivo_mejorado
        if not archivo_audio or not os.path.exists(archivo_audio.path):
            archivo_audio = transcripcion.procesamiento_audio.archivo_original
        
        # Configurar número de hablantes
        diarization = pipeline(
            archivo_audio.path,
            min_speakers=config.min_hablantes,
            max_speakers=config.max_hablantes
        )
        
        # Procesar resultados
        segmentos_diarizacion = []
        hablantes_detectados = set()
        
        for turn, _, hablante in diarization.itertracks(yield_label=True):
            hablantes_detectados.add(hablante)
            segmentos_diarizacion.append({
                'inicio': turn.start,
                'fin': turn.end,
                'duracion': turn.duration,
                'hablante': hablante
            })
        
        # Guardar resultados
        transcripcion.diarizacion_json = {
            'segmentos': segmentos_diarizacion,
            'num_hablantes': len(hablantes_detectados),
            'hablantes': list(hablantes_detectados),
            'model_used': config.modelo_diarizacion,
            'timestamp': timezone.now().isoformat()
        }
        transcripcion.hablantes_detectados = list(hablantes_detectados)
        transcripcion.numero_hablantes = len(hablantes_detectados)
        transcripcion.save()
        
        logger.info(f"Diarización completada para ID: {transcripcion_id}")
        
        return {
            'success': True,
            'num_hablantes': len(hablantes_detectados),
            'num_segmentos': len(segmentos_diarizacion)
        }
        
    except Exception as e:
        logger.error(f"Error en diarización para ID: {transcripcion_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def combinar_transcripcion_diarizacion(self, transcripcion_id: int):
    """
    Combina los resultados de Whisper y pyannote en una conversación estructurada
    """
    from apps.transcripcion.models import Transcripcion, EstadoTranscripcion
    
    try:
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        transcripcion.estado = EstadoTranscripcion.PROCESANDO
        transcripcion.save()
        
        # Obtener datos de transcripción y diarización
        segmentos_whisper = transcripcion.transcripcion_json.get('segments', [])
        segmentos_diarizacion = transcripcion.diarizacion_json.get('segmentos', [])
        
        # Combinar segmentos por tiempo
        conversacion = []
        segmento_id = 0
        
        for seg_whisper in segmentos_whisper:
            inicio_whisper = seg_whisper['start']
            fin_whisper = seg_whisper['end']
            texto = seg_whisper['text'].strip()
            
            if not texto:
                continue
            
            # Encontrar hablante correspondiente
            hablante = _encontrar_hablante_para_segmento(
                inicio_whisper, fin_whisper, segmentos_diarizacion
            )
            
            conversacion.append({
                'id': f"seg_{segmento_id}",
                'inicio': inicio_whisper,
                'fin': fin_whisper,
                'duracion': fin_whisper - inicio_whisper,
                'hablante': hablante,
                'texto': texto,
                'confianza': seg_whisper.get('confidence', 0.0),
                'palabras': seg_whisper.get('words', []),
                'editado': False,
                'timestamp_edicion': None
            })
            segmento_id += 1
        
        # Guardar conversación estructurada
        transcripcion.conversacion_json = conversacion
        transcripcion.numero_segmentos = len(conversacion)
        transcripcion.save()
        
        # Inicializar mapeo de hablantes
        _inicializar_hablantes_identificados(transcripcion)
        
        logger.info(f"Combinación completada para ID: {transcripcion_id}")
        
        return {
            'success': True,
            'num_segmentos_conversacion': len(conversacion)
        }
        
    except Exception as e:
        logger.error(f"Error al combinar para ID: {transcripcion_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(bind=True)
def generar_estadisticas_transcripcion(self, transcripcion_id: int):
    """
    Genera estadísticas y análisis de la transcripción
    """
    from apps.transcripcion.models import Transcripcion
    
    try:
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        conversacion = transcripcion.conversacion_json
        
        if not conversacion:
            return {'success': False, 'error': 'No hay conversación para analizar'}
        
        # Calcular estadísticas por hablante
        stats_hablantes = {}
        palabras_totales = 0
        duracion_total = 0
        confianzas = []
        
        for segmento in conversacion:
            hablante = segmento['hablante']
            duracion = segmento['duracion']
            palabras = len(segmento['texto'].split())
            confianza = segmento.get('confianza', 0.0)
            
            if hablante not in stats_hablantes:
                stats_hablantes[hablante] = {
                    'tiempo_total': 0,
                    'intervenciones': 0,
                    'palabras_total': 0,
                    'confianza_promedio': []
                }
            
            stats_hablantes[hablante]['tiempo_total'] += duracion
            stats_hablantes[hablante]['intervenciones'] += 1
            stats_hablantes[hablante]['palabras_total'] += palabras
            stats_hablantes[hablante]['confianza_promedio'].append(confianza)
            
            palabras_totales += palabras
            duracion_total += duracion
            confianzas.append(confianza)
        
        # Procesar estadísticas finales
        for hablante, stats in stats_hablantes.items():
            if stats['confianza_promedio']:
                stats['confianza_promedio'] = sum(stats['confianza_promedio']) / len(stats['confianza_promedio'])
            else:
                stats['confianza_promedio'] = 0.0
            
            stats['palabras_por_minuto'] = (stats['palabras_total'] / (stats['tiempo_total'] / 60)) if stats['tiempo_total'] > 0 else 0
            stats['porcentaje_tiempo'] = (stats['tiempo_total'] / duracion_total * 100) if duracion_total > 0 else 0
        
        # Extraer palabras clave simples
        texto_completo = ' '.join([seg['texto'] for seg in conversacion])
        palabras_clave = _extraer_palabras_clave_simple(texto_completo)
        
        # Guardar estadísticas
        estadisticas = {
            'hablantes': stats_hablantes,
            'resumen_general': {
                'duracion_total_segundos': duracion_total,
                'palabras_totales': palabras_totales,
                'confianza_promedio': sum(confianzas) / len(confianzas) if confianzas else 0,
                'palabras_por_minuto_global': (palabras_totales / (duracion_total / 60)) if duracion_total > 0 else 0,
                'numero_intervenciones': len(conversacion)
            },
            'timestamp_analisis': timezone.now().isoformat()
        }
        
        transcripcion.estadisticas_json = estadisticas
        transcripcion.palabras_clave = palabras_clave
        transcripcion.palabras_totales = palabras_totales
        transcripcion.duracion_total = duracion_total
        transcripcion.confianza_promedio = sum(confianzas) / len(confianzas) if confianzas else 0
        transcripcion.save()
        
        logger.info(f"Estadísticas generadas para ID: {transcripcion_id}")
        
        return {
            'success': True,
            'estadisticas': estadisticas
        }
        
    except Exception as e:
        logger.error(f"Error al generar estadísticas para ID: {transcripcion_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# Funciones auxiliares

def _transcripcion_simulada(transcripcion):
    """Transcripción simulada para desarrollo sin Whisper"""
    texto_ejemplo = f"Ejemplo de transcripción para {transcripcion.procesamiento_audio.nombre_archivo}. Esta es una transcripción simulada que incluye múltiples segmentos para pruebas. Hablante uno inicia la conversación. Hablante dos responde con comentarios adicionales."
    
    segmentos = [
        {
            'start': 0.0,
            'end': 5.0,
            'text': 'Ejemplo de transcripción para archivo de audio.',
            'confidence': 0.85,
            'words': []
        },
        {
            'start': 5.0,
            'end': 10.0,
            'text': 'Esta es una transcripción simulada que incluye múltiples segmentos.',
            'confidence': 0.90,
            'words': []
        },
        {
            'start': 10.0,
            'end': 15.0,
            'text': 'Hablante uno inicia la conversación con comentarios iniciales.',
            'confidence': 0.88,
            'words': []
        }
    ]
    
    transcripcion.texto_completo = texto_ejemplo
    transcripcion.transcripcion_json = {
        'segments': segmentos,
        'language': 'es',
        'model_used': 'simulado',
        'timestamp': timezone.now().isoformat()
    }
    transcripcion.save()
    
    return {
        'success': True,
        'texto_completo': texto_ejemplo,
        'num_segmentos': len(segmentos)
    }


def _diarizacion_simulada(transcripcion):
    """Diarización simulada para desarrollo sin pyannote"""
    segmentos = [
        {'inicio': 0.0, 'fin': 10.0, 'duracion': 10.0, 'hablante': 'SPEAKER_00'},
        {'inicio': 10.0, 'fin': 15.0, 'duracion': 5.0, 'hablante': 'SPEAKER_01'},
    ]
    
    hablantes = ['SPEAKER_00', 'SPEAKER_01']
    
    transcripcion.diarizacion_json = {
        'segmentos': segmentos,
        'num_hablantes': len(hablantes),
        'hablantes': hablantes,
        'model_used': 'simulado',
        'timestamp': timezone.now().isoformat()
    }
    transcripcion.hablantes_detectados = hablantes
    transcripcion.numero_hablantes = len(hablantes)
    transcripcion.save()
    
    return {
        'success': True,
        'num_hablantes': len(hablantes),
        'num_segmentos': len(segmentos)
    }


def _encontrar_hablante_para_segmento(inicio, fin, segmentos_diarizacion):
    """Encuentra el hablante más probable para un segmento de tiempo"""
    mejor_hablante = 'SPEAKER_00'  # Default
    mayor_solapamiento = 0
    
    for seg_dia in segmentos_diarizacion:
        # Calcular solapamiento
        inicio_max = max(inicio, seg_dia['inicio'])
        fin_min = min(fin, seg_dia['fin'])
        solapamiento = max(0, fin_min - inicio_max)
        
        if solapamiento > mayor_solapamiento:
            mayor_solapamiento = solapamiento
            mejor_hablante = seg_dia['hablante']
    
    return mejor_hablante


def _inicializar_hablantes_identificados(transcripcion):
    """Inicializa el mapeo de hablantes con nombres por defecto"""
    hablantes_identificados = {}
    
    for i, hablante in enumerate(transcripcion.hablantes_detectados):
        hablantes_identificados[hablante] = f"Participante {i + 1}"
    
    transcripcion.hablantes_identificados = hablantes_identificados
    transcripcion.save()


def _extraer_palabras_clave_simple(texto):
    """Extracción simple de palabras clave"""
    import re
    from collections import Counter
    
    # Palabras comunes a ignorar
    palabras_ignorar = {
        'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le',
        'da', 'su', 'por', 'son', 'con', 'no', 'me', 'una', 'si', 'ya', 'o', 'fue', 'muy',
        'pero', 'como', 'para', 'del', 'los', 'las', 'este', 'esta', 'eso', 'ese', 'esa'
    }
    
    # Limpiar y tokenizar
    texto_limpio = re.sub(r'[^\w\s]', '', texto.lower())
    palabras = [p for p in texto_limpio.split() if len(p) > 3 and p not in palabras_ignorar]
    
    # Contar y obtener las más frecuentes
    contador = Counter(palabras)
    return [palabra for palabra, count in contador.most_common(20)]
