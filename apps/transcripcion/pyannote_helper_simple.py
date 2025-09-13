"""
Pyannote Helper Simplificado - Solo mapeo cronológico directo
"""

import os
import torch
import logging
from typing import Dict, Any, List, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Configuración pyannote
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
PYANNOTE_AVAILABLE = False

try:
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation
    PYANNOTE_AVAILABLE = True
    logger.info("✅ pyannote-audio disponible")
except ImportError:
    logger.warning("⚠️ pyannote-audio no disponible")

class PyannoteProcessor:
    """
    Procesador simplificado de pyannote con mapeo cronológico directo
    """
    
    def __init__(self, device: str = "cpu"):
        self.device = device
        self.pipeline = None
        self.modelo_cargado = None
        
    def procesar_diarizacion(self, 
                           archivo_audio: str,
                           configuracion: Dict[str, Any]) -> Dict[str, Any]:
        """
        PROCESO SIMPLIFICADO:
        1. Ejecutar pyannote
        2. Detectar orden cronológico de speakers
        3. Mapear directamente a participantes
        """
        
        # Extraer configuración
        min_speakers = configuracion.get('min_speakers', 1)
        max_speakers = configuracion.get('max_speakers', 8)
        participantes_esperados = configuracion.get('participantes_esperados', [])
        
        logger.info(f"🎯 PROCESO SIMPLIFICADO DE DIARIZACIÓN")
        logger.info(f"  - Archivo: {archivo_audio}")
        logger.info(f"  - Participantes esperados: {len(participantes_esperados)}")
        logger.info(f"  - Speakers min/max: {min_speakers}/{max_speakers}")
        
        # 🔥 VERIFICAR Y CORREGIR CONFIGURACIÓN DE SPEAKERS
        if participantes_esperados and len(participantes_esperados) >= 2:
            num_participantes = len(participantes_esperados)
            logger.info(f"🔥 FORZANDO EXACTAMENTE {num_participantes} SPEAKERS (sobrescribiendo min/max)")
            min_speakers = num_participantes
            max_speakers = num_participantes
            logger.info(f"🎯 SPEAKERS FORZADOS: min={min_speakers}, max={max_speakers}")
        else:
            logger.warning(f"⚠️ Usando configuración original: min={min_speakers}, max={max_speakers}")
        
        try:
            # PASO 1: Ejecutar pyannote
            resultado_pyannote = self._ejecutar_pyannote(archivo_audio, min_speakers, max_speakers)
            
            if not resultado_pyannote['exito']:
                logger.error("❌ pyannote falló")
                return self._resultado_vacio()
            
            # PASO 2: Mapeo cronológico DIRECTO
            segmentos_mapeados = self._mapear_cronologicamente(
                resultado_pyannote['segmentos'], 
                participantes_esperados
            )
            
            # PASO 3: Generar mapeo de hablantes basado en el mapeo cronológico REAL
            hablantes_mapeados = {}
            
            # Obtener speakers únicos de los segmentos mapeados  
            speakers_unicos = set()
            for seg in segmentos_mapeados:
                if 'speaker_id' in seg:
                    speakers_unicos.add(seg['speaker_id'])
            
            logger.info(f"🎯 Speakers únicos detectados para mapeo JSON: {sorted(speakers_unicos)}")
            
            # Mapear cada speaker único a su participante correspondiente
            for speaker_id in speakers_unicos:
                # Buscar qué participante corresponde a este speaker según mapeo cronológico
                for seg in segmentos_mapeados:
                    if seg.get('speaker_id') == speaker_id and 'nombre_participante' in seg:
                        hablantes_mapeados[speaker_id] = {
                            'nombre': seg['nombre_participante'],
                            'participante': seg.get('participante_info', {}),
                            'id': speaker_id
                        }
                        break
            
            logger.info(f"🎯 Hablantes mapeados para JSON: {hablantes_mapeados}")
            
            # 🔥 CALCULAR NÚMERO REAL DE SPEAKERS DETECTADOS
            speakers_detectados = len(speakers_unicos)
            participantes_configurados = len(participantes_esperados) if participantes_esperados else 0
            
            logger.info(f"📊 RESULTADOS FINALES:")
            logger.info(f"  - Speakers detectados por pyannote: {speakers_detectados}")
            logger.info(f"  - Participantes configurados: {participantes_configurados}")
            logger.info(f"  - Speakers mapeados: {len(hablantes_mapeados)}")
            
            # PASO 4: Resultado final COMPLETO
            return {
                'exito': True,
                'segmentos_hablantes': segmentos_mapeados,
                'hablantes': hablantes_mapeados,  # ⚠️ CAMPO REQUERIDO para estructura_json_mejorada
                'num_speakers': speakers_detectados,  # 🔥 USAR NÚMERO REAL DETECTADO
                'speakers_detectados': speakers_detectados,  # 🔥 CAMPO ADICIONAL PARA CLARIDAD
                'participantes_configurados': participantes_configurados,
                'speakers': self._generar_info_speakers(participantes_esperados),
                'backend': 'pyannote_simplificado',
                'mapeo_cronologico_aplicado': True,
                # ✅ NUEVO: Info adicional para cabecera
                'participantes_esperados': participantes_esperados,
                'total_participantes': participantes_configurados,
                'mapeo_directo': {
                    speaker_id: info['nombre'] for speaker_id, info in hablantes_mapeados.items()
                } if hablantes_mapeados else {}
            }
            
        except Exception as e:
            logger.error(f"❌ Error en diarización simplificada: {str(e)}")
            return self._resultado_vacio()
    
    def _ejecutar_pyannote(self, archivo_audio: str, min_speakers: int, max_speakers: int) -> Dict[str, Any]:
        """Ejecuta pyannote y devuelve segmentos básicos"""
        
        if not PYANNOTE_AVAILABLE or not HUGGINGFACE_TOKEN:
            logger.error("❌ pyannote no disponible o token faltante")
            return {'exito': False}
        
        try:
            # Cargar pipeline
            if self.pipeline is None:
                logger.info("🔧 Cargando pipeline de pyannote...")
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization@2.1",
                    use_auth_token=HUGGINGFACE_TOKEN
                )
                logger.info("✅ Pipeline cargado")
            
            # 🔥 DETERMINAR NÚMERO EXACTO DE SPEAKERS ESPERADOS
            num_speakers_esperados = max_speakers if max_speakers == min_speakers else None
            
            # Ejecutar diarización con parámetros específicos
            logger.info("🎙️ Ejecutando diarización...")
            if num_speakers_esperados and num_speakers_esperados >= 2:
                logger.info(f"🎯 FORZANDO exactamente {num_speakers_esperados} speakers")
                diarizacion = self.pipeline(archivo_audio, num_speakers=num_speakers_esperados)
            else:
                logger.info(f"🎯 Usando rango min={min_speakers}, max={max_speakers}")
                diarizacion = self.pipeline(archivo_audio, min_speakers=min_speakers, max_speakers=max_speakers)
            
            # Convertir a segmentos simples
            segmentos = []
            for segmento, _, speaker in diarizacion.itertracks(yield_label=True):
                segmentos.append({
                    'inicio': float(segmento.start),
                    'fin': float(segmento.end),
                    'speaker_id': speaker,  # ID original de pyannote
                    'duracion': float(segmento.end - segmento.start)
                })
            
            speakers_detectados = len(set(seg['speaker_id'] for seg in segmentos))
            logger.info(f"✅ pyannote detectó {len(segmentos)} segmentos con {speakers_detectados} speakers únicos")
            
            return {
                'exito': True,
                'segmentos': segmentos,
                'num_speakers': speakers_detectados
            }
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando pyannote: {str(e)}")
            return {'exito': False}
    
    def _mapear_cronologicamente(self, segmentos: List[Dict], participantes: List[Dict]) -> List[Dict]:
        """
        MAPEO CRONOLÓGICO SIMPLE:
        1. Detectar orden de primera aparición de cada speaker
        2. Mapear directamente: 1er speaker → 1er participante, 2do → 2do, etc.
        """
        
        if not segmentos:
            return []
        
        logger.info("🔧 APLICANDO MAPEO CRONOLÓGICO DIRECTO")
        
        # PASO 1: Detectar orden cronológico de speakers
        primera_aparicion = {}
        for seg in segmentos:
            speaker_id = seg['speaker_id']
            inicio = seg['inicio']
            
            if speaker_id not in primera_aparicion:
                primera_aparicion[speaker_id] = inicio
                logger.info(f"  - {speaker_id} apareció por primera vez a los {inicio:.1f}s")
        
        # PASO 2: Ordenar speakers por tiempo de aparición
        speakers_cronologicos = sorted(primera_aparicion.items(), key=lambda x: x[1])
        
        logger.info("🕐 ORDEN CRONOLÓGICO DETECTADO:")
        for i, (speaker_id, tiempo) in enumerate(speakers_cronologicos):
            logger.info(f"  {i+1}. {speaker_id} → {tiempo:.1f}s")
        
        # PASO 3: Crear mapeo directo speaker_id → participante
        mapeo = {}
        for i, (speaker_id, _) in enumerate(speakers_cronologicos):
            if i < len(participantes):
                nombre = participantes[i]['nombres']
                mapeo[speaker_id] = {
                    'indice': i,
                    'nombre': nombre,
                    'participante': participantes[i]
                }
                logger.info(f"🎯 MAPEO: {speaker_id} → {nombre} (posición {i})")
            else:
                mapeo[speaker_id] = {
                    'indice': i,
                    'nombre': f'Speaker_{i}',
                    'participante': None
                }
        
        # PASO 4: Aplicar mapeo a todos los segmentos
        segmentos_mapeados = []
        for seg in segmentos:
            speaker_id_original = seg['speaker_id']
            mapeo_info = mapeo.get(speaker_id_original, {'indice': 0, 'nombre': 'Speaker_0', 'participante': None})
            
            segmento_mapeado = {
                'inicio': seg['inicio'],
                'fin': seg['fin'],
                'speaker': mapeo_info['indice'],  # Índice cronológico (0, 1, 2...)
                'speaker_name': mapeo_info['nombre'],  # Nombre del participante
                'speaker_id': speaker_id_original,  # ID original de pyannote (para mapeo JSON)
                'speaker_id_original': speaker_id_original,  # Compatibilidad
                'nombre_participante': mapeo_info['nombre'],  # Para mapeo JSON
                'participante_info': mapeo_info.get('participante', {}),  # Info completa del participante
                'duracion': seg['duracion']
            }
            
            segmentos_mapeados.append(segmento_mapeado)
        
        logger.info(f"✅ Mapeados {len(segmentos_mapeados)} segmentos cronológicamente")
        return segmentos_mapeados
    
    def _generar_info_speakers(self, participantes: List[Dict]) -> List[Dict]:
        """Genera información de speakers basada en participantes"""
        speakers = []
        for i, participante in enumerate(participantes):
            speakers.append({
                'id': i,
                'label': participante['nombres'],
                'participante': participante
            })
        return speakers
    
    def _resultado_vacio(self) -> Dict[str, Any]:
        """Resultado cuando falla la diarización"""
        return {
            'exito': False,
            'segmentos': [],
            'num_speakers': 0,
            'speakers': [],
            'backend': 'fallback',
            'mapeo_cronologico_aplicado': False
        }

def crear_processor_simplificado(device: str = "cpu") -> PyannoteProcessor:
    """Factory function para crear el processor"""
    return PyannoteProcessor(device=device)