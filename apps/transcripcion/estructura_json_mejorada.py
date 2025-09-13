"""
Nueva estructura de datos para transcripción y diarización mejorada
Genera JSON con información detallada de hablantes, segmentos y métricas
INCLUYE AUDITORÍA COMPLETA DE PARÁMETROS Y METADATOS
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def formatear_tiempo_str(segundos: float) -> str:
    """
    Convierte segundos a formato MM:SS
    
    Args:
        segundos: Tiempo en segundos
        
    Returns:
        String en formato MM:SS
    """
    minutos = int(segundos // 60)
    segundos_restantes = int(segundos % 60)
    return f"{minutos:02d}:{segundos_restantes:02d}"


def calcular_metricas_asr(segmentos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula métricas de calidad de ASR (Automatic Speech Recognition)
    
    Args:
        segmentos: Lista de segmentos de transcripción
        
    Returns:
        Dict con métricas calculadas
    """
    if not segmentos:
        return {
            'asr_avg_confidence': 0.0,
            'asr_low_confidence_ratio': 0.0,
            'total_words': 0,
            'language': 'es',
            'language_probability': 1.0
        }
    
    # Calcular confianza promedio ASR
    confidencias = [seg.get('confidence', 0.0) for seg in segmentos if 'confidence' in seg]
    asr_avg_confidence = sum(confidencias) / len(confidencias) if confidencias else 0.0
    
    # Calcular ratio de baja confianza (< 0.5)
    baja_confianza = sum(1 for conf in confidencias if conf < 0.5)
    asr_low_confidence_ratio = baja_confianza / len(confidencias) if confidencias else 0.0
    
    # Contar palabras totales
    total_words = sum(len(seg.get('text', '').split()) for seg in segmentos)
    
    return {
        'asr_avg_confidence': asr_avg_confidence,
        'asr_low_confidence_ratio': asr_low_confidence_ratio, 
        'total_words': total_words,
        'language': 'es',  # Por defecto español
        'language_probability': 1.0  # Asumir alta confianza para español
    }


def calcular_metricas_diarizacion(segmentos: List[Dict[str, Any]]) -> float:
    """
    Calcula métricas de calidad de diarización
    
    Args:
        segmentos: Lista de segmentos con speaker_confidence
        
    Returns:
        Confianza promedio de diarización
    """
    confidencias = [seg.get('speaker_confidence', 0.0) for seg in segmentos if 'speaker_confidence' in seg]
    return sum(confidencias) / len(confidencias) if confidencias else 0.0


def generar_estructura_json_mejorada(
    file_id: str,
    resultado_whisper: Dict[str, Any],
    resultado_pyannote: Dict[str, Any],
    hablantes_predefinidos: List[Dict[str, Any]],
    configuracion: Dict[str, Any],
    archivo_normalizado: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera la estructura JSON mejorada según las especificaciones
    
    Args:
        file_id: Identificador único del archivo
        resultado_whisper: Resultado del procesamiento con Whisper
        resultado_pyannote: Resultado del procesamiento con pyannote
        hablantes_predefinidos: Lista de hablantes con información detallada
        configuracion: Configuración utilizada
        archivo_normalizado: Ruta del archivo de audio normalizado
        
    Returns:
        Dict con la estructura JSON mejorada
    """
    try:
        # Combinar segmentos de Whisper con diarización de pyannote
        segmentos_whisper = resultado_whisper.get('segmentos', [])
        diarizacion = resultado_pyannote.get('segmentos_hablantes', [])
        
        # Crear mapeo de hablantes detectados a predefinidos
        hablantes_mapeados = mapear_hablantes_predefinidos(
            resultado_pyannote.get('hablantes', {}),
            hablantes_predefinidos
        )
        
        # Generar segmentos combinados
        segmentos_combinados = combinar_segmentos_whisper_pyannote(
            segmentos_whisper,
            diarizacion,
            hablantes_mapeados
        )
        
        # Calcular métricas
        metricas_asr = calcular_metricas_asr(segmentos_whisper)
        diarizacion_avg_confidence = calcular_metricas_diarizacion(segmentos_combinados)
        
        # ===== AUDITORÍA: Extraer metadatos de Whisper y pyannote =====
        metadatos_whisper = resultado_whisper.get('metadatos_modelo', {})
        metadatos_pyannote = resultado_pyannote.get('metadatos_pipeline', {})
        parametros_whisper = resultado_whisper.get('parametros_aplicados', {})
        parametros_pyannote = resultado_pyannote.get('parametros_aplicados', {})
        auditoria_whisper = resultado_whisper.get('auditoria', {})
        auditoria_pyannote = resultado_pyannote.get('auditoria', {})
        
        # Estructura JSON final CON AUDITORÍA COMPLETA
        json_mejorado = {
            "file_id": file_id,
            "speakers_detected": len(hablantes_mapeados),
            "speakers": generar_informacion_hablantes(hablantes_mapeados, hablantes_predefinidos),
            "segments": segmentos_combinados,
            "metrics": {
                **metricas_asr,
                "diarization_avg_confidence": diarizacion_avg_confidence
            },
            "normalized_wav": archivo_normalizado or f"/data/outputs/{file_id}.wav",
            
            # ===== NUEVA SECCIÓN: AUDITORÍA COMPLETA =====
            "processing_audit": {
                "timestamp": datetime.now().isoformat(),
                "configuration_original": configuracion,
                "whisper_processing": {
                    "success": resultado_whisper.get('exito', False),
                    "model_metadata": {
                        "model_name": metadatos_whisper.get('modelo', 'N/A'),
                        "model_size_mb": metadatos_whisper.get('size_mb', 'N/A'),
                        "model_version": metadatos_whisper.get('version', 'N/A'),
                        "model_hash": metadatos_whisper.get('hash', 'N/A'),
                        "model_path": metadatos_whisper.get('path', 'N/A'),
                        "device_used": metadatos_whisper.get('device', parametros_whisper.get('device_usado', 'N/A')),
                        "cuda_available": metadatos_whisper.get('cuda_available', False),
                        "model_languages": metadatos_whisper.get('languages', []),
                        "is_multilingual": metadatos_whisper.get('is_multilingual', True)
                    },
                    "parameters_applied": {
                        "model_whisper": parametros_whisper.get('modelo_whisper', 'N/A'),
                        "language": parametros_whisper.get('idioma_principal', 'N/A'),
                        "temperature": parametros_whisper.get('temperatura', 'N/A'),
                        "use_gpu": parametros_whisper.get('usar_gpu', 'N/A'),
                        "word_timestamps": parametros_whisper.get('palabra_por_palabra', 'N/A'),
                        "audio_enhancement": parametros_whisper.get('mejora_audio', 'N/A'),
                        "whisper_options_real": parametros_whisper.get('opciones_whisper_reales', {})
                    },
                    "audit_info": {
                        "parameters_from_user": auditoria_whisper.get('parametros_del_usuario', False),
                        "hardcoded_parameters": auditoria_whisper.get('parametros_hardcodeados', True),
                        "model_requested": auditoria_whisper.get('modelo_solicitado', 'N/A'),
                        "model_actually_used": auditoria_whisper.get('modelo_usado', 'N/A'),
                        "flags_applied": auditoria_whisper.get('flags_aplicados', {})
                    }
                },
                "diarization_processing": {
                    "success": resultado_pyannote.get('exito', False),
                    "pipeline_metadata": {
                        "pipeline_name": metadatos_pyannote.get('pipeline', 'N/A'),
                        "pipeline_version": metadatos_pyannote.get('version', 'N/A'),
                        "models_used": metadatos_pyannote.get('models', {}),
                        "device_used": metadatos_pyannote.get('device', parametros_pyannote.get('device_usado', 'N/A')),
                        "cuda_available": metadatos_pyannote.get('cuda_available', False),
                        "memory_usage_mb": metadatos_pyannote.get('memory_usage_mb', 'N/A'),
                        "token_required": metadatos_pyannote.get('token_required', True),
                        "is_instantiated": metadatos_pyannote.get('is_instantiated', False)
                    },
                    "parameters_applied": {
                        "model_diarization": parametros_pyannote.get('modelo_diarizacion', 'N/A'),
                        "min_speakers": parametros_pyannote.get('min_speakers', 'N/A'),
                        "max_speakers": parametros_pyannote.get('max_speakers', 'N/A'),
                        "clustering_threshold": parametros_pyannote.get('clustering_threshold', 'N/A'),
                        "use_gpu": parametros_pyannote.get('usar_gpu', 'N/A'),
                        "pipeline_params_real": parametros_pyannote.get('parametros_pipeline_reales', {})
                    },
                    "audit_info": {
                        "parameters_from_user": auditoria_pyannote.get('parametros_del_usuario', False),
                        "hardcoded_parameters": auditoria_pyannote.get('parametros_hardcodeados', True),
                        "model_requested": auditoria_pyannote.get('modelo_solicitado', 'N/A'),
                        "model_actually_used": auditoria_pyannote.get('modelo_usado', 'N/A'),
                        "threshold_applied": auditoria_pyannote.get('threshold_aplicado', 'N/A'),
                        "speakers_constraint": auditoria_pyannote.get('speakers_constraint', {})
                    }
                },
                "combination_processing": {
                    "method_used": resultado_pyannote.get('parametros_combinacion', {}).get('metodo', 'overlap_temporal'),
                    "overlap_threshold": resultado_pyannote.get('parametros_combinacion', {}).get('threshold_overlap', 0.5),
                    "audit_combination": resultado_pyannote.get('auditoria_combinacion', {}),
                    "segments_whisper": len(segmentos_whisper),
                    "segments_diarization": len(diarizacion),
                    "segments_combined": len(segmentos_combinados)
                },
                "quality_indicators": {
                    "asr_confidence": metricas_asr.get('asr_avg_confidence', 0.0),
                    "diarization_confidence": diarizacion_avg_confidence,
                    "low_confidence_ratio": metricas_asr.get('asr_low_confidence_ratio', 0.0),
                    "total_words": metricas_asr.get('total_words', 0),
                    "language_detected": metricas_asr.get('language', 'es'),
                    "language_probability": metricas_asr.get('language_probability', 1.0)
                }
            }
        }
        
        return json_mejorado
        
    except Exception as e:
        logger.error(f"Error generando estructura JSON mejorada: {str(e)}")
        return generar_json_fallback(file_id, resultado_whisper, archivo_normalizado)


def mapear_hablantes_predefinidos(
    hablantes_detectados: Dict[str, Any],
    hablantes_predefinidos: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Mapea hablantes detectados por pyannote a hablantes predefinidos
    ACTUALIZADO: Usa directamente el mapeo que ya viene del pyannote_helper_simple.py
    
    Args:
        hablantes_detectados: Dict de hablantes mapeados por pyannote_helper
        hablantes_predefinidos: Lista de hablantes con información completa (para compatibilidad)
        
    Returns:
        Dict mapeando speaker_id a información completa
    """
    # Si ya tenemos un mapeo completo desde pyannote_helper_simple.py, usarlo directamente
    if hablantes_detectados and isinstance(list(hablantes_detectados.values())[0], dict):
        logger.info(f"🎯 USANDO MAPEO DIRECTO DE PYANNOTE_HELPER:")
        for speaker_id, info in hablantes_detectados.items():
            nombre = info.get('nombre', f'Hablante {speaker_id}')
            logger.info(f"   {speaker_id} → {nombre}")
        return hablantes_detectados
    
    # Código de fallback si viene el formato antiguo
    mapeo = {}
    
    # Si hay hablantes predefinidos, usarlos
    if hablantes_predefinidos:
        logger.info(f"🔧 MAPEO POR ORDEN DE APARICIÓN (FALLBACK):")
        logger.info(f"   Speakers detectados: {list(hablantes_detectados.keys())}")
        logger.info(f"   Hablantes predefinidos: {[h.get('first_name', h.get('nombres', f'Hablante {i+1}')) for i, h in enumerate(hablantes_predefinidos)]}")
        
        # Los speakers ya vienen ordenados cronológicamente desde pyannote_helper
        # SPEAKER_00 = primero en hablar, SPEAKER_01 = segundo en hablar, etc.
        speaker_ids = list(hablantes_detectados.keys())
        
        for speaker_id in speaker_ids:
            # Extraer el índice del speaker (que ya representa orden cronológico)
            if '_' in speaker_id:
                idx_cronologico = int(speaker_id.split('_')[-1])
            else:
                idx_cronologico = 0
                
            # Mapear al hablante predefinido correspondiente
            if idx_cronologico < len(hablantes_predefinidos):
                hablante_info = hablantes_predefinidos[idx_cronologico]
                
                mapeo[speaker_id] = {
                    "id": idx_cronologico,  # Usar el índice cronológico
                    "label": hablante_info.get('nombre_completo', 
                            f"{hablante_info.get('first_name', hablante_info.get('nombres', ''))} {hablante_info.get('last_name', hablante_info.get('apellidos', ''))}".strip() or f"Hablante {idx_cronologico+1}"),
                    "info_completa": hablante_info
                }
                
                logger.info(f"   🎯 {speaker_id} (posición cronológica {idx_cronologico+1}) → {mapeo[speaker_id]['label']}")
            else:
                # Si hay más speakers detectados que predefinidos
                mapeo[speaker_id] = {
                    "id": idx_cronologico,
                    "label": f"Hablante Extra {idx_cronologico+1}",
                    "info_completa": {}
                }
                logger.warning(f"   ⚠️ {speaker_id} → Hablante Extra (no predefinido)")
    else:
        # Si no hay predefinidos, usar los detectados
        for i, (speaker_id, nombre) in enumerate(hablantes_detectados.items()):
            idx_cronologico = int(speaker_id.split('_')[-1]) if '_' in speaker_id else i
            mapeo[speaker_id] = {
                "id": idx_cronologico,
                "label": nombre if isinstance(nombre, str) else f"Hablante {idx_cronologico+1}",
                "info_completa": {}
            }
    
    return mapeo


def combinar_segmentos_whisper_pyannote(
    segmentos_whisper: List[Dict[str, Any]],
    diarizacion: List[Dict[str, Any]],
    hablantes_mapeados: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Combina segmentos de Whisper con información de diarización
    SIMPLIFICADO: Usa el mapeo cronológico directo del nuevo helper
    
    Args:
        segmentos_whisper: Segmentos de transcripción de Whisper
        diarizacion: Segmentos de diarización con mapeo cronológico aplicado
        hablantes_mapeados: Mapeo de hablantes (puede ser None con nuevo sistema)
        
    Returns:
        Lista de segmentos combinados
    """
    segmentos_combinados = []
    
    for seg_whisper in segmentos_whisper:
        inicio = seg_whisper.get('inicio', seg_whisper.get('start', 0.0))
        fin = seg_whisper.get('fin', seg_whisper.get('end', 0.0))
        texto = seg_whisper.get('texto', seg_whisper.get('text', ''))
        
        # Buscar segmento de diarización que mejor coincida
        speaker_idx = 0  # Default
        speaker_confidence = 0.5
        
        mejor_overlap = 0.0
        for seg_diar in diarizacion:
            inicio_diar = seg_diar.get('inicio', seg_diar.get('start', 0.0))
            fin_diar = seg_diar.get('fin', seg_diar.get('end', 0.0))
            
            # Calcular overlap temporal
            overlap_inicio = max(inicio, inicio_diar)
            overlap_fin = min(fin, fin_diar)
            
            if overlap_fin > overlap_inicio:
                overlap_duracion = overlap_fin - overlap_inicio
                whisper_duracion = fin - inicio
                overlap_ratio = overlap_duracion / whisper_duracion if whisper_duracion > 0 else 0
                
                if overlap_ratio > mejor_overlap:
                    mejor_overlap = overlap_ratio
                    # USAR EL SPEAKER MAPEADO CRONOLÓGICAMENTE
                    speaker_idx = seg_diar.get('speaker', 0)  # Ya viene con mapeo cronológico
                    speaker_confidence = overlap_ratio
        
        # Crear segmento combinado con mapeo cronológico aplicado
        segmento = {
            "start": inicio,
            "end": fin,
            "start_time_str": formatear_tiempo_str(inicio),
            "end_time_str": formatear_tiempo_str(fin),
            "speaker": speaker_idx,  # Índice cronológico directo (0=primero, 1=segundo, etc.)
            "text": texto,
            "speaker_confidence": speaker_confidence
        }
        segmentos_combinados.append(segmento)
    
    return segmentos_combinados


def encontrar_hablante_en_tiempo(
    inicio: float,
    fin: float,
    diarizacion: List[Dict[str, Any]]
) -> str:
    """
    Encuentra qué hablante corresponde a un segmento temporal
    
    Args:
        inicio: Tiempo de inicio del segmento
        fin: Tiempo de fin del segmento
        diarizacion: Lista de segmentos de diarización
        
    Returns:
        ID del hablante
    """
    tiempo_medio = (inicio + fin) / 2
    
    for seg_diaz in diarizacion:
        seg_inicio = seg_diaz.get('inicio', seg_diaz.get('start', 0.0))
        seg_fin = seg_diaz.get('fin', seg_diaz.get('end', 0.0))
        
        if seg_inicio <= tiempo_medio <= seg_fin:
            return seg_diaz.get('hablante', seg_diaz.get('speaker', 'SPEAKER_00'))
    
    return 'SPEAKER_00'  # Fallback


def obtener_confianza_speaker(
    inicio: float,
    fin: float,
    diarizacion: List[Dict[str, Any]]
) -> float:
    """
    Obtiene la confianza del speaker para un segmento temporal
    
    Args:
        inicio: Tiempo de inicio
        fin: Tiempo de fin
        diarizacion: Lista de segmentos de diarización
        
    Returns:
        Confianza del speaker (0.0 a 1.0)
    """
    tiempo_medio = (inicio + fin) / 2
    
    for seg_diaz in diarizacion:
        seg_inicio = seg_diaz.get('inicio', seg_diaz.get('start', 0.0))
        seg_fin = seg_diaz.get('fin', seg_diaz.get('end', 0.0))
        
        if seg_inicio <= tiempo_medio <= seg_fin:
            return seg_diaz.get('confianza', seg_diaz.get('confidence', 1.0))
    
    return 1.0  # Confianza alta por defecto


def generar_informacion_hablantes(
    hablantes_mapeados: Dict[str, Dict[str, Any]],
    hablantes_predefinidos: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Genera la información detallada de hablantes para el JSON
    
    Args:
        hablantes_mapeados: Hablantes mapeados
        hablantes_predefinidos: Información predefinida de hablantes
        
    Returns:
        Lista de hablantes con información completa
    """
    hablantes_info = []
    
    for speaker_id, info in hablantes_mapeados.items():
        hablante_predefinido = info.get('info_completa', {})
        
        hablante = {
            "id": info.get('id', 0),
            "label": info.get('label', f"Hablante {info.get('id', 0) + 1}"),
            "role": hablante_predefinido.get('cargo', 'Participante'),
            "description": hablante_predefinido.get('descripcion', ''),
            "cedula": hablante_predefinido.get('cedula', ''),
            "titulo": hablante_predefinido.get('titulo', ''),
            "cargo": hablante_predefinido.get('cargo', ''),
            "institucion": hablante_predefinido.get('institucion', ''),
            "first_name": hablante_predefinido.get('nombres', ''),
            "last_name": hablante_predefinido.get('apellidos', ''),
            "can_vote": hablante_predefinido.get('puede_votar', False),
            "has_voice": hablante_predefinido.get('tiene_voz', True),
            "can_sign": hablante_predefinido.get('puede_firmar', False),
            "attendance": hablante_predefinido.get('presente', True),
            "details": hablante_predefinido.get('detalles'),
            "actor_type": hablante_predefinido.get('tipo_actor')
        }
        
        hablantes_info.append(hablante)
    
    return hablantes_info


def generar_json_fallback(
    file_id: str,
    resultado_whisper: Dict[str, Any],
    archivo_normalizado: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera un JSON básico cuando falla el procesamiento completo
    
    Args:
        file_id: ID del archivo
        resultado_whisper: Resultado básico de Whisper
        archivo_normalizado: Ruta del archivo normalizado
        
    Returns:
        JSON básico funcional
    """
    segmentos_basicos = []
    segmentos_whisper = resultado_whisper.get('segmentos', [])
    
    for i, seg in enumerate(segmentos_whisper):
        inicio = seg.get('inicio', seg.get('start', i * 5.0))
        fin = seg.get('fin', seg.get('end', (i + 1) * 5.0))
        
        segmento = {
            "start": inicio,
            "end": fin,
            "start_time_str": formatear_tiempo_str(inicio),
            "end_time_str": formatear_tiempo_str(fin),
            "speaker": 0,
            "text": seg.get('texto', seg.get('text', '')),
            "speaker_confidence": 1.0
        }
        segmentos_basicos.append(segmento)
    
    return {
        "file_id": file_id,
        "speakers_detected": 1,
        "speakers": [{
            "id": 0,
            "label": "Hablante Único",
            "role": "Participante",
            "description": "",
            "cedula": "",
            "titulo": "",
            "cargo": "",
            "institucion": "",
            "first_name": "",
            "last_name": "",
            "can_vote": False,
            "has_voice": True,
            "can_sign": False,
            "attendance": True,
            "details": None,
            "actor_type": None
        }],
        "segments": segmentos_basicos,
        "metrics": {
            "asr_avg_confidence": 0.8,
            "asr_low_confidence_ratio": 0.0,
            "total_words": sum(len(seg.get('texto', seg.get('text', '')).split()) for seg in segmentos_whisper),
            "language": "es",
            "language_probability": 1.0,
            "diarization_avg_confidence": 1.0
        },
        "normalized_wav": archivo_normalizado or f"/data/outputs/{file_id}.wav"
    }