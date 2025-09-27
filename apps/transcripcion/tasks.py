"""
Tareas de Celery para procesamiento de transcripción y diarización
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from datetime import datetime
import os
import tempfile
import shutil
from typing import Dict, Any, List
import json

from .models import Transcripcion, EstadoTranscripcion
from .whisper_helper import WhisperProcessor
from .pyannote_helper_simple import crear_processor_simplificado
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
        
        # Actualizar estado inicial
        try:
            transcripcion.task_id_celery = getattr(self.request, 'id', '') or getattr(transcripcion, 'task_id_celery', '')
        except Exception:
            pass
        transcripcion.estado = EstadoTranscripcion.EN_PROCESO
        transcripcion.tiempo_inicio_proceso = timezone.now()
        if hasattr(transcripcion, 'progreso_porcentaje'):
            transcripcion.progreso_porcentaje = 10
        transcripcion.save()
        # Publicar meta en Celery
        try:
            self.update_state(state='PROGRESS', meta={'fase': 'inicio', 'msg': 'Preparando procesamiento', 'pct': 10})
        except Exception:
            pass
        
        # Obtener configuración
        configuracion = transcripcion.get_configuracion_completa()
        logger.info(f"Configuración: {configuracion}")
        
        # Verificar archivo de audio
        archivo_audio = None
        archivo_audio_path = None
        
        # Intentar primero con archivo mejorado (preferido)
        if hasattr(transcripcion.procesamiento_audio, 'archivo_mejorado') and transcripcion.procesamiento_audio.archivo_mejorado:
            archivo_mejorado = transcripcion.procesamiento_audio.archivo_mejorado
            if archivo_mejorado and os.path.exists(archivo_mejorado.path):
                archivo_audio = archivo_mejorado
                archivo_audio_path = archivo_mejorado.path
                logger.info(f"Usando archivo mejorado: {archivo_audio_path}")
        
        # Si no, intentar con archivo original
        if not archivo_audio:
            if hasattr(transcripcion.procesamiento_audio, 'archivo_audio') and transcripcion.procesamiento_audio.archivo_audio:
                archivo_original = transcripcion.procesamiento_audio.archivo_audio
                if archivo_original and os.path.exists(archivo_original.path):
                    archivo_audio = archivo_original
                    archivo_audio_path = archivo_original.path
                    logger.info(f"Usando archivo original: {archivo_audio_path}")
        
        # Debug: mostrar qué archivos están disponibles
        logger.info(f"DEBUG - Procesamiento audio ID: {transcripcion.procesamiento_audio.id}")
        if hasattr(transcripcion.procesamiento_audio, 'archivo_audio'):
            logger.info(f"DEBUG - archivo_audio: {transcripcion.procesamiento_audio.archivo_audio}")
        if hasattr(transcripcion.procesamiento_audio, 'archivo_mejorado'):
            logger.info(f"DEBUG - archivo_mejorado: {transcripcion.procesamiento_audio.archivo_mejorado}")
        
        if not archivo_audio or not archivo_audio_path:
            raise Exception("No se encontró archivo de audio para procesar")
        
        archivo_audio_path = archivo_audio.path
        logger.info(f"Procesando archivo: {archivo_audio_path}")
        
        # Paso 1: Transcripción con Whisper
        transcripcion.estado = EstadoTranscripcion.TRANSCRIBIENDO
        if hasattr(transcripcion, 'progreso_porcentaje'):
            transcripcion.progreso_porcentaje = 20
        transcripcion.mensaje_estado = "Transcribiendo audio con Whisper..."
        transcripcion.save()
        try:
            self.update_state(state='PROGRESS', meta={'fase': 'whisper', 'msg': 'Transcribiendo con Whisper', 'pct': 20})
        except Exception:
            pass
        
        resultado_whisper = procesar_con_whisper(archivo_audio_path, configuracion)
        
        if not resultado_whisper.get('exito'):
            raise Exception(f"Error en Whisper: {resultado_whisper.get('error')}")
        
        logger.info("Transcripción con Whisper completada")
        if hasattr(transcripcion, 'progreso_porcentaje'):
            transcripcion.progreso_porcentaje = 50
        transcripcion.save()
        try:
            self.update_state(state='PROGRESS', meta={'fase': 'whisper', 'msg': 'Whisper completado', 'pct': 50})
        except Exception:
            pass
        
        # Obtener hablantes predefinidos de la configuración
        hablantes_predefinidos = []
        
        # La configuración ya debe incluir los participantes desde get_configuracion_completa()
        if 'participantes_esperados' in configuracion and configuracion['participantes_esperados']:
            hablantes_predefinidos = configuracion['participantes_esperados']
            logger.info(f"AUDIT - Usando participantes de configuración: {len(hablantes_predefinidos)}")
            logger.info(f"AUDIT - Participantes: {[p.get('nombres', f'P{i+1}') for i, p in enumerate(hablantes_predefinidos)]}")
        elif 'hablantes_predefinidos' in configuracion and configuracion['hablantes_predefinidos']:
            hablantes_predefinidos = configuracion['hablantes_predefinidos']
            logger.info(f"AUDIT - Usando hablantes_predefinidos de configuración: {len(hablantes_predefinidos)}")
            logger.info(f"AUDIT - Participantes: {[p.get('nombres', f'P{i+1}') for i, p in enumerate(hablantes_predefinidos)]}")
        else:
            logger.info("AUDIT - No hay participantes en configuración, usando detección automática")
        
        logger.info(f"AUDIT - Hablantes predefinidos finales: {len(hablantes_predefinidos)} participantes")
        
        # Paso 2: Diarización con pyannote
        transcripcion.estado = EstadoTranscripcion.DIARIZANDO
        if hasattr(transcripcion, 'progreso_porcentaje'):
            transcripcion.progreso_porcentaje = 60
        transcripcion.mensaje_estado = "Identificando hablantes con pyannote..."
        transcripcion.save()
        try:
            self.update_state(state='PROGRESS', meta={'fase': 'pyannote', 'msg': 'Diarizando con pyannote', 'pct': 60})
        except Exception:
            pass
        
        resultado_pyannote = procesar_con_pyannote(archivo_audio_path, configuracion, hablantes_predefinidos)
        
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
        
        # Paso 3: Combinar resultados con estructura mejorada
        transcripcion.estado = EstadoTranscripcion.PROCESANDO
        transcripcion.progreso = 90
        transcripcion.mensaje_estado = "Generando estructura JSON mejorada..."
        transcripcion.save()
        
        logger.info("DEBUG - Iniciando generación de estructura JSON mejorada")
        logger.info(f"DEBUG - Whisper segmentos: {len(resultado_whisper.get('segmentos', []))}")
        logger.info(f"DEBUG - Pyannote exitoso: {resultado_pyannote.get('exito', False)}")
        logger.info(f"DEBUG - Hablantes predefinidos: {len(hablantes_predefinidos)}")
        
        # 🔥 USAR ESTRUCTURA SIMPLE Y DIRECTA
        from .estructura_simple_directa import generar_estructura_simple
        
        # Obtener referencia al procesamiento_audio ANTES de llamar la función
        procesamiento_audio = transcripcion.procesamiento_audio
        
        logger.info("🔧 Generando estructura JSON con método SIMPLE Y DIRECTO")
        
        # Generar la nueva estructura JSON SIMPLE
        try:
            conversacion_json = generar_estructura_simple(
                resultado_whisper=resultado_whisper,
                resultado_pyannote=resultado_pyannote,
                procesamiento_audio=procesamiento_audio,
                transcripcion=transcripcion
            )
            logger.info("✅ Estructura JSON SIMPLE generada exitosamente")
        except Exception as e:
            logger.error(f"❌ Error generando estructura JSON simple: {str(e)}")
            # Estructura de fallback básica
            conversacion_json = {
                "cabecera": {
                    "audio": {"error": "Error procesando metadata"},
                    "transcripcion": {"error": "Error procesando transcripción"},
                    "hablantes": {},
                    "mapeo_hablantes": {}
                },
                "conversacion": [],
                "metadata": {"error": str(e)}
            }
        
        # Debug: Log del resultado 
        logger.info(f"✅ Conversación JSON generada:")
        logger.info(f"  - Cabecera: {'cabecera' in conversacion_json}")
        logger.info(f"  - Conversación: {len(conversacion_json.get('conversacion', []))} segmentos")
        logger.info(f"  - Hablantes mapeados: {len(conversacion_json.get('cabecera', {}).get('mapeo_hablantes', {}))}")
        
        # Paso 4: Guardar resultados con nueva estructura
        # Extraer datos de la estructura simple
        conversacion_segmentos = conversacion_json.get('conversacion', [])
        cabecera = conversacion_json.get('cabecera', {})
        metadata = conversacion_json.get('metadata', {})
        
        # 🎯 EXTRAER TEXTO COMPLETO Y ESTRUCTURADO
        # Texto completo tradicional (para compatibilidad)
        transcripcion.texto_completo = ' '.join(seg.get('texto', '') for seg in conversacion_segmentos)
        
        # 🔥 NUEVO: Texto estructurado con formato Tiempo,hablante,texto
        texto_estructurado = conversacion_json.get('texto_estructurado', '')
        if texto_estructurado:
            logger.info(f"📝 Texto estructurado disponible: {len(texto_estructurado.splitlines())} líneas")
            # Guardar en conversacion_json para preservarlo
            if isinstance(transcripcion.conversacion_json, dict):
                transcripcion.conversacion_json['texto_estructurado'] = texto_estructurado
            else:
                # Si conversacion_json es lista, convertir a dict
                transcripcion.conversacion_json = {
                    'conversacion': transcripcion.conversacion_json if isinstance(transcripcion.conversacion_json, list) else [],
                    'texto_estructurado': texto_estructurado,
                    'estructura_version': 'v2.0_mejorada'
                }
            logger.info(f"💾 Texto estructurado guardado en conversacion_json")
        
        # Extraer hablantes desde la cabecera
        hablantes_info = cabecera.get('hablantes', {})
        transcripcion.hablantes_detectados = list(hablantes_info.values()) if hablantes_info else []
        
        # 🔥 USAR INFORMACIÓN REAL DE PYANNOTE PARA NÚMERO DE HABLANTES
        num_speakers_pyannote = resultado_pyannote.get('speakers_detectados', resultado_pyannote.get('num_speakers', 1))
        transcripcion.numero_hablantes = num_speakers_pyannote
        
        logger.info(f"📊 HABLANTES FINALES:")
        logger.info(f"  - Pyannote detectó: {num_speakers_pyannote} speakers")
        logger.info(f"  - Cabecera tiene: {len(hablantes_info)} hablantes")
        logger.info(f"  - Conversación tiene: {len(conversacion_segmentos)} segmentos")
        logger.info(f"  - Resultado final: {transcripcion.numero_hablantes} hablantes")
        
        # Generar estadísticas básicas
        estadisticas = {
            'total_segmentos': len(conversacion_segmentos),
            'duracion_total': sum(seg.get('duracion', 0) for seg in conversacion_segmentos),
            'palabras_total': len(transcripcion.texto_completo.split()) if transcripcion.texto_completo else 0,
            'hablantes_detectados': transcripcion.numero_hablantes,
            'texto_estructurado_disponible': bool(texto_estructurado)
        }
        transcripcion.estadisticas_procesamiento = estadisticas
        
        # Obtener información del modelo Whisper del resultado directo
        parametros_whisper = resultado_whisper.get('parametros_aplicados', {})
        metadatos_whisper = resultado_whisper.get('metadatos_modelo', {})
        
        # Guardar resultados en campos JSON con estructura completa
        transcripcion.transcripcion_json = {
            'texto_completo': transcripcion.texto_completo or '',
            'texto_estructurado': texto_estructurado,  # 🎯 NUEVO: Formato Tiempo,hablante,texto
            'segmentos': conversacion_segmentos,       # 🎯 Segmentos con: inicio, hablante, texto
            'metadatos': {
                'modelo_whisper': parametros_whisper.get('modelo_whisper', metadatos_whisper.get('modelo', 'unknown')),
                'idioma_detectado': resultado_whisper.get('idioma_detectado', parametros_whisper.get('idioma_principal', 'es')),
                'confianza_promedio': metadata.get('confianza_promedio', 0.0),
                'fecha_procesamiento': timezone.now().isoformat(),
                'archivo_procesado': str(transcripcion.procesamiento_audio.archivo_audio) if transcripcion.procesamiento_audio and transcripcion.procesamiento_audio.archivo_audio else 'no_disponible',
                'estructura_mejorada': True,
                'formato_segmentos': ['inicio', 'fin', 'hablante', 'hablante_id', 'texto', 'duracion']
            }
        }
        
        # ===== GENERAR CONVERSACION_JSON CON CABECERA COMPLETA =====
        # NUEVA ESTRUCTURA: {cabecera: {...}, conversacion: [...]}
        
        # La variable procesamiento_audio ya está definida arriba
        
        # Obtener segmentos y hablantes desde diarizacion_json
        segmentos_json = transcripcion.diarizacion_json.get('segmentos', [])
        hablantes_json = transcripcion.diarizacion_json.get('hablantes', {})
        
        logger.info(f"DEBUG - Convirtiendo diarizacion_json a formato chat: {len(segmentos_json)} segmentos")
        logger.info(f"DEBUG - Hablantes disponibles: {list(hablantes_json.keys())}")
        
        # ===== CREAR CABECERA COMPLETA =====
        cabecera = {
            # Información del Audio
            'audio': {
                'id': procesamiento_audio.id if procesamiento_audio else None,
                'titulo': procesamiento_audio.titulo if procesamiento_audio else None,
                'archivo_original': procesamiento_audio.archivo_audio.name if procesamiento_audio and procesamiento_audio.archivo_audio else None,
                'archivo_mejorado': procesamiento_audio.archivo_mejorado.name if procesamiento_audio and procesamiento_audio.archivo_mejorado else None,
                'duracion_segundos': getattr(procesamiento_audio, 'duracion_segundos', None),
                'fecha_creacion': procesamiento_audio.created_at.isoformat() if procesamiento_audio and hasattr(procesamiento_audio, 'created_at') else None,
                'metadatos': procesamiento_audio.metadatos_originales if procesamiento_audio else {}
            },
            # Información de la Transcripción
            'transcripcion': {
                'id': transcripcion.id,
                'estado': transcripcion.estado,
                'fecha_creacion': transcripcion.fecha_creacion.isoformat(),
                'usuario_creacion': transcripcion.usuario_creacion.username if transcripcion.usuario_creacion else None,
                'modelo_whisper': transcripcion.configuracion_utilizada.modelo_whisper if transcripcion.configuracion_utilizada else None,
                'idioma': transcripcion.configuracion_utilizada.idioma_principal if transcripcion.configuracion_utilizada else 'es',
                'configuracion_id': transcripcion.configuracion_utilizada.id if transcripcion.configuracion_utilizada else None
            },
            # ✅ MAPEO COMPLETO DE HABLANTES
            'hablantes': {},
            'mapeo_hablantes': {},  # Mapeo directo: "Hablante 0" → "Beto"
            'participantes_configurados': [],
            'total_hablantes': 0
        }
        
        # Obtener participantes configurados
        if procesamiento_audio and procesamiento_audio.participantes_detallados:
            participantes = procesamiento_audio.participantes_detallados
            cabecera['participantes_configurados'] = participantes
            cabecera['total_hablantes'] = len(participantes)
            
            # Crear mapeo directo Hablante 0/1/2 → Nombres reales
            for i, participante in enumerate(participantes):
                nombre_real = participante.get('nombres', f'Participante {i+1}')
                apellidos = participante.get('apellidos', '')
                nombre_completo = f"{nombre_real} {apellidos}".strip() if apellidos else nombre_real
                
                # Mapeo directo para la UI
                cabecera['mapeo_hablantes'][f'Hablante {i}'] = {
                    'nombre': nombre_real,
                    'apellidos': apellidos,
                    'nombre_completo': nombre_completo,
                    'cargo': participante.get('cargo', ''),
                    'institucion': participante.get('institucion', ''),
                    'orden': participante.get('orden', i + 1),
                    'info_completa': participante
                }
                
                # También mapear los speakers detectados si están disponibles
                speaker_key = f'SPEAKER_{i:02d}'  # SPEAKER_00, SPEAKER_01, etc.
                if speaker_key in hablantes_json:
                    cabecera['hablantes'][speaker_key] = cabecera['mapeo_hablantes'][f'Hablante {i}']
                
                logger.info(f"🎯 MAPEO CABECERA: Hablante {i} → {nombre_completo}")
        
        # Si hay hablantes en el JSON de diarización, incluirlos también
        if hablantes_json:
            for speaker_id, info in hablantes_json.items():
                if speaker_id not in cabecera['hablantes']:
                    cabecera['hablantes'][speaker_id] = info
        
        # ===== GENERAR CONVERSACIÓN CON MAPEO CORRECTO =====
        conversacion_mensajes = []
        
        # Generar paleta de colores para hablantes
        colores_hablantes = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6f42c1', '#e83e8c', '#fd7e14']
        hablantes_colores = {}
        
        for i, segmento in enumerate(segmentos_json):
            # Obtener información del speaker (asegurar que sea string)
            speaker_id = str(segmento.get('speaker', 'unknown'))
            
            # 🎯 USAR EL MAPEO DE LA CABECERA PARA OBTENER EL NOMBRE REAL
            nombre_hablante = f'Hablante {speaker_id}'  # Formato estándar
            
            # Buscar en el mapeo de la cabecera
            if nombre_hablante in cabecera['mapeo_hablantes']:
                speaker_info = cabecera['mapeo_hablantes'][nombre_hablante]
                speaker_name = speaker_info['nombre_completo']
            elif speaker_id in cabecera['hablantes']:
                speaker_info = cabecera['hablantes'][speaker_id]
                speaker_name = speaker_info.get('nombre', speaker_info.get('label', f'Hablante {speaker_id}'))
            else:
                speaker_name = f'Hablante {speaker_id}'
                speaker_info = {}
            
            # Asignar color consistente por hablante
            if speaker_id not in hablantes_colores:
                color_index = len(hablantes_colores) % len(colores_hablantes)
                hablantes_colores[speaker_id] = colores_hablantes[color_index]
            
            color = hablantes_colores[speaker_id]
            
            # Validar datos antes de crear mensaje
            inicio = float(segmento.get('start', 0.0))
            fin = float(segmento.get('end', 0.0))
            texto = segmento.get('text', '').strip()
            
            # Solo agregar si tiene contenido válido
            if texto and inicio >= 0 and fin > inicio:
                mensaje_chat = {
                    'hablante': speaker_name,  # ✅ NOMBRE REAL desde cabecera
                    'texto': texto,
                    'inicio': inicio,
                    'fin': fin,
                    'duracion': fin - inicio,
                    'confianza': segmento.get('speaker_confidence', 0.8),
                    'speaker_id': speaker_id,
                    'color': color,
                    'timestamp': f"{inicio:.1f}s - {fin:.1f}s",
                    'info_hablante': speaker_info
                }
                
                conversacion_mensajes.append(mensaje_chat)
            else:
                logger.warning(f"DEBUG - Segmento inválido omitido: speaker={speaker_id}, texto='{texto}', inicio={inicio}, fin={fin}")
        
        # ===== ESTRUCTURA FINAL CON CABECERA =====
        conversacion_completa = {
            'cabecera': cabecera,
            'conversacion': conversacion_mensajes,
            'metadata': {
                'total_mensajes': len(conversacion_mensajes),
                'hablantes_detectados': len(set(msg['speaker_id'] for msg in conversacion_mensajes)),
                'duracion_total': max([msg['fin'] for msg in conversacion_mensajes]) if conversacion_mensajes else 0,
                'fecha_generacion': datetime.now().isoformat(),
                'version_estructura': '2.0'
            }
        }
        
        # Guardar conversación COMPLETA en formato correcto para el template  
        # 🔥 USAR LA NUEVA ESTRUCTURA SIMPLE DIRECTAMENTE
        transcripcion.conversacion_json = conversacion_json  # Estructura completa con cabecera, conversacion, texto_estructurado
        
        logger.info(f"💾 ESTRUCTURA COMPLETA GUARDADA:")
        logger.info(f"  - Tipo: {type(conversacion_json)}")
        logger.info(f"  - Campos: {list(conversacion_json.keys()) if isinstance(conversacion_json, dict) else 'No es dict'}")
        if 'conversacion' in conversacion_json:
            logger.info(f"  - Segmentos conversación: {len(conversacion_json['conversacion'])}")
        if 'texto_estructurado' in conversacion_json:
            lineas = conversacion_json['texto_estructurado'].count('\n') + 1
            logger.info(f"  - Líneas texto estructurado: {lineas}")
        if 'cabecera' in conversacion_json and 'mapeo_hablantes' in conversacion_json['cabecera']:
            logger.info(f"  - Mapeos hablantes: {len(conversacion_json['cabecera']['mapeo_hablantes'])}")
        
        # COMPATIBILIDAD: También generar formato anterior para templates existentes
        conversacion_mensajes = conversacion_json.get('conversacion', [])
        if conversacion_mensajes:
            primer_mensaje = conversacion_mensajes[0]
            logger.info(f"🔍 Primer mensaje: hablante='{primer_mensaje.get('hablante')}', texto='{primer_mensaje.get('texto', '')[:50]}...', tiempo={primer_mensaje.get('inicio')}s-{primer_mensaje.get('fin')}s")
        
        # También guardar estructura completa en campo separado
        transcripcion.diarizacion_json = {
            'segmentos': conversacion_segmentos,
            'hablantes': hablantes_info,
            'metadatos': metadata,
            'cabecera': cabecera,
            'estado_transcripcion': 'exitosa' if transcripcion.texto_completo else 'sin_texto'
        }
        
        # ⚠️ PRESERVAR segmentos_hablantes del pyannote helper
        if 'segmentos_hablantes' in resultado_pyannote:
            transcripcion.diarizacion_json['segmentos_hablantes'] = resultado_pyannote['segmentos_hablantes']
            logger.info(f"DEBUG - Preservados {len(resultado_pyannote['segmentos_hablantes'])} segmentos_hablantes del pyannote helper")
        
        # Guardar métricas mejoradas
        transcripcion.estadisticas_json = {
            **estadisticas,
            **metadata,
            'estructura_version': 'simple_directa_v1.0'
        }
        
        # Completar
        transcripcion.estado = EstadoTranscripcion.COMPLETADO
        transcripcion.progreso = 100
        transcripcion.mensaje_estado = "Transcripción completada exitosamente"
        transcripcion.fecha_completado = timezone.now()
        
        # DEBUG: Verificar que conversacion_json tenga la nueva estructura
        logger.info(f"DEBUG - ANTES DEL SAVE - conversacion_json tipo: {type(transcripcion.conversacion_json)}")
        if isinstance(transcripcion.conversacion_json, dict):
            cabecera = transcripcion.conversacion_json.get('cabecera', {})
            conversacion = transcripcion.conversacion_json.get('conversacion', [])
            metadata = transcripcion.conversacion_json.get('metadata', {})
            logger.info(f"DEBUG - ANTES DEL SAVE - estructura completa: cabecera={bool(cabecera)}, conversacion={len(conversacion)} mensajes, metadata={bool(metadata)}")
            logger.info(f"DEBUG - ANTES DEL SAVE - mapeo_hablantes en cabecera: {len(cabecera.get('mapeo_hablantes', {}))}")
        else:
            logger.warning(f"DEBUG - ANTES DEL SAVE - conversacion_json no tiene estructura esperada")
        
        transcripcion.save()
        
        log_transcripcion_accion(
            transcripcion, 
            'transcripcion_completada',
            {
                'duracion_procesamiento': (timezone.now() - transcripcion.tiempo_inicio_proceso).total_seconds() if transcripcion.tiempo_inicio_proceso else 0,
                'num_hablantes': transcripcion.numero_hablantes,
                'palabras_transcritas': len(transcripcion.texto_completo.split())
            }
        )
        
        logger.info(f"Transcripción {transcripcion_id} completada exitosamente")
        
        return {
            'exito': True,
            'transcripcion_id': transcripcion_id,
            'num_hablantes': transcripcion.numero_hablantes,  # 🔥 Ahora usa el número real de pyannote
            'duracion_texto': len(transcripcion.texto_completo),
            'speakers_detectados': num_speakers_pyannote,  # 🔥 Info adicional para verificación
            'participantes_configurados': len(hablantes_predefinidos) if hablantes_predefinidos else 0
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


def procesar_con_pyannote(archivo_audio: str, configuracion: Dict[str, Any], hablantes_predefinidos: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Procesa audio con pyannote para diarización
    
    Args:
        archivo_audio: Ruta al archivo de audio
        configuracion: Diccionario con configuración
        hablantes_predefinidos: Lista de hablantes con información completa
    """
    pyannote_processor = None
    try:
        # Preparar configuración con participantes esperados
        configuracion_pyannote = configuracion.copy()
        
        if hablantes_predefinidos:
            # 🎯 FORZAR NÚMERO EXACTO DE SPEAKERS
            num_participantes = len(hablantes_predefinidos)
            logger.info(f"🔥 CONFIGURANDO PYANNOTE PARA EXACTAMENTE {num_participantes} SPEAKERS")
            logger.info(f"📝 Participantes: {[p.get('nombres', f'P{i+1}') for i, p in enumerate(hablantes_predefinidos)]}")
            
            configuracion_pyannote.update({
                'hablantes_predefinidos': hablantes_predefinidos,
                'participantes_esperados': hablantes_predefinidos,
                'min_speakers': num_participantes,  # 🎯 MISMO NÚMERO EXACTO
                'max_speakers': num_participantes,  # 🎯 MISMO NÚMERO EXACTO
                'num_speakers_esperados': num_participantes
            })
        else:
            # Fallback para audio sin participantes configurados
            logger.warning("⚠️ No hay participantes predefinidos, usando configuración automática")
            configuracion_pyannote.update({
                'min_speakers': configuracion.get('min_speakers', 2),
                'max_speakers': configuracion.get('max_speakers', 4)
            })
        
        pyannote_processor = crear_processor_simplificado()
        resultado = pyannote_processor.procesar_diarizacion(archivo_audio, configuracion_pyannote)
        
        logger.info(f"✅ Pyannote procesado: {resultado.get('exito', False)}")
        if resultado.get('exito'):
            logger.info(f"🎯 Speakers detectados: {resultado.get('num_speakers', 0)}")
        
        return resultado
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento pyannote: {str(e)}")
        return {'exito': False, 'error': str(e)}
        
    finally:
        # El processor simplificado no necesita limpieza especial
        pass


def combinar_resultados(resultado_whisper: Dict[str, Any], 
                       resultado_pyannote: Dict[str, Any],
                       configuracion: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Combina resultados de Whisper y pyannote
    """
    logger.info("DEBUG - Iniciando combinar_resultados")
    try:
        # Verificar si tenemos datos válidos de Whisper
        segmentos_whisper = resultado_whisper.get('segmentos', [])
        texto_whisper = resultado_whisper.get('texto_completo', '')
        
        logger.info(f"DEBUG - Whisper texto length: {len(texto_whisper)}, segmentos: {len(segmentos_whisper)}")
        
        # Si pyannote falló o no hay segmentos de hablantes, usar solo Whisper
        segmentos_hablantes = resultado_pyannote.get('segmentos_hablantes', [])
        
        logger.info(f"DEBUG - Pyannote segmentos hablantes: {len(segmentos_hablantes)}, exito: {resultado_pyannote.get('exito', False)}")
        
        if not segmentos_hablantes or not resultado_pyannote.get('exito', False):
            logger.info("Usando solo resultados de Whisper (pyannote no disponible)")
            return {
                'exito': True,
                'segmentos_combinados': segmentos_whisper,
                'transcripcion_formateada': texto_whisper,
                'hablantes': {'speaker_0': 'Hablante Único'},
                'num_hablantes': 1,
                'estadisticas': {},
                'texto_completo': texto_whisper,  # Para compatibilidad
                'segmentos': segmentos_whisper,  # Para compatibilidad
                'dialogo': [],  # Para conversacion_json
                'turnos_conversacion': [],  # Para conversacion_json
                'resumen_participacion': {}  # Para conversacion_json
            }
        
        # Si tenemos ambos resultados, usar el helper simplificado
        logger.info("DEBUG - Usando helper simplificado para combinar")
        pyannote_processor = crear_processor_simplificado()
        
        # Para compatibilidad, generar resultado básico
        resultado_combinado = {
            'exito': True,
            'segmentos_combinados': segmentos_whisper,
            'transcripcion_formateada': texto_whisper,
            'hablantes': {},
            'num_hablantes': resultado_pyannote.get('num_speakers', 0),
            'estadisticas': {},
            'texto_completo': texto_whisper,
            'segmentos': resultado_pyannote.get('segmentos', []),
            'dialogo': [],
            'turnos_conversacion': [],
            'resumen_participacion': {}
        }
        return resultado_combinado
        
    except Exception as e:
        logger.error(f"Error combinando resultados: {str(e)}")
        # Fallback final: usar solo transcripción de Whisper
        return {
            'exito': True,
            'segmentos_combinados': resultado_whisper.get('segmentos', []),
            'transcripcion_formateada': resultado_whisper.get('texto_completo', ''),
            'hablantes': {'speaker_0': 'Hablante Único'},
            'num_hablantes': 1,
            'estadisticas': {},
            'texto_completo': resultado_whisper.get('texto_completo', ''),  # Agregado para compatibilidad
            'segmentos': resultado_whisper.get('segmentos', []),  # Agregado para compatibilidad
            'dialogo': [],  # Para conversacion_json
            'turnos_conversacion': [],  # Para conversacion_json
            'resumen_participacion': {}  # Para conversacion_json
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
