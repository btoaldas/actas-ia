"""
Helper mejorado para diarización de speakers con pyannote-audio
MEJORAS ADOPTADAS DEL EJEMPLO QUE FUNCIONA BIEN:
- Merge inteligente de segmentos contiguos
- Asignación por overlap temporal
- Fallback automático a resemblyzer
- Configuración robusta
"""
import os
import logging
import tempfile
from typing import Dict, Any, Optional, List, Tuple
import json
import numpy as np

try:
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation, Segment
    import torch
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False

# ✅ Intentar cargar resemblyzer como fallback (del ejemplo)
try:
    from resemblyzer import VoiceEncoder, preprocess_wav
    import soundfile as sf
    from sklearn.cluster import AgglomerativeClustering
    RESEMBLYZER_AVAILABLE = True
except ImportError:
    RESEMBLYZER_AVAILABLE = False

logger = logging.getLogger(__name__)

# ✅ CONFIGURACIÓN OPTIMIZADA (del ejemplo)
_MAX_SPEAKERS = int(os.getenv("MAX_SPEAKERS", "8"))
_DIARIZATION_DEFAULT = (os.getenv("DIARIZATION_BACKEND", "pyannote") or "pyannote").lower()
_HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HF_TOKEN")

# Cache global para modelos (mejora del ejemplo)
_pipeline_cache = {}
_encoder_cache = None


class PyannoteProcessor:
    """Procesador de diarización con mejores prácticas adoptadas del ejemplo"""
    
    def __init__(self):
        if not PYANNOTE_AVAILABLE and not RESEMBLYZER_AVAILABLE:
            logger.warning("pyannote-audio y resemblyzer no disponibles. Funcionalidad limitada.")
            
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.modelo_cargado = None
        self.token_huggingface = None
        self.backend = "pyannote"  # pyannote, resemblyzer, none
    def _frame_signal(self, wav: np.ndarray, sr: int, frame_ms=1000, hop_ms=500):
        """
        Genera frames de señal para procesamiento (del ejemplo)
        """
        frame_len = int(sr * frame_ms / 1000)
        hop_len = int(sr * hop_ms / 1000)
        for start in range(0, len(wav) - frame_len + 1, hop_len):
            yield start / sr, wav[start:start+frame_len]
    
    def _diarize_resemblyzer(self, wav_path: str, max_speakers: Optional[int]) -> Dict[str, Any]:
        """
        ✅ FALLBACK USANDO RESEMBLYZER (del ejemplo que funciona bien)
        """
        if not RESEMBLYZER_AVAILABLE:
            logger.warning("Resemblyzer no disponible para fallback")
            return {"num_speakers": 0, "speakers": [], "segments": [], "backend": "none"}
        
        try:
            global _encoder_cache
            if _encoder_cache is None:
                _encoder_cache = VoiceEncoder()
            
            wav, sr = sf.read(wav_path)
            if wav.ndim > 1:
                wav = np.mean(wav, axis=1)
            
            # Normalizar con preprocess_wav (remueve silencio, normaliza)
            try:
                wav = preprocess_wav(wav, source_sr=sr)
                sr = 16000
            except Exception:
                pass

            # Extraer embeddings por frames
            times = []
            embeds = []
            for t, frame in self._frame_signal(wav, sr, frame_ms=1000, hop_ms=500):
                try:
                    emb = _encoder_cache.embed_utterance(frame)
                    embeds.append(emb)
                    times.append(t)
                except Exception:
                    continue

            if len(embeds) == 0:
                return {"num_speakers": 0, "speakers": [], "segments": [], "backend": "resemblyzer"}

            X = np.vstack(embeds)
            n_speakers = max_speakers or min(_MAX_SPEAKERS, 5)

            clustering = AgglomerativeClustering(n_clusters=max(1, int(n_speakers)))
            labels = clustering.fit_predict(X)

            # Construir segmentos por etiqueta
            segments = []
            for i, t in enumerate(times):
                start = t
                end = t + 1.0  # 1s por frame
                segments.append({
                    "start": float(start),
                    "end": float(end),
                    "speaker": int(labels[i])
                })

            # ✅ MERGE INTELIGENTE (del ejemplo)
            merged = self._merge_contiguous_segments(segments)

            # Describir speakers
            unique = sorted(set(s for s in labels.tolist()))
            speakers = [{"id": int(s), "label": f"Speaker {int(s)}"} for s in unique]

            return {
                "num_speakers": len(unique),
                "speakers": speakers,
                "segments": merged,
                "backend": "resemblyzer",
            }
        except Exception as e:
            logger.error(f"Error en fallback resemblyzer: {str(e)}")
            return {"num_speakers": 0, "speakers": [], "segments": [], "backend": "error"}
    
    def _merge_contiguous_segments(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ✅ MERGE INTELIGENTE DE SEGMENTOS CONTIGUOS (del ejemplo)
        Une segmentos del mismo speaker que están muy cerca temporalmente
        """
        if not segments:
            return []
        
        # Ordenar por tiempo de inicio
        sorted_segments = sorted(segments, key=lambda s: s["start"])
        merged = []
        
        for seg in sorted_segments:
            if not merged:
                merged.append(seg)
            else:
                last = merged[-1]
                # ✅ Si mismo speaker y están cerca (0.05s), unir
                if (seg["speaker"] == last["speaker"] and 
                    seg["start"] <= last["end"] + 0.05):
                    last["end"] = max(last["end"], seg["end"])
                else:
                    merged.append(seg)
        
        return merged
    
    def _diarize_pyannote_optimized(self, wav_path: str, max_speakers: Optional[int]) -> Dict[str, Any]:
        """
        ✅ DIARIZACIÓN PYANNOTE OPTIMIZADA (con mejoras del ejemplo)
        """
        try:
            model_id = os.getenv("PYANNOTE_MODEL", "pyannote/speaker-diarization-3.1")
            
            # Usar cache de pipeline
            cache_key = f"{model_id}_{self.device}"
            if cache_key not in _pipeline_cache:
                if not _HF_TOKEN:
                    raise RuntimeError("HUGGINGFACE_TOKEN no configurado para pyannote")
                _pipeline_cache[cache_key] = Pipeline.from_pretrained(
                    model_id, 
                    use_auth_token=_HF_TOKEN
                )
            
            pipeline = _pipeline_cache[cache_key]
            
            # Ejecutar diarización
            diar = pipeline(wav_path)
            
            # ✅ CONVERSIÓN DE ANOTACIONES (del ejemplo)
            label_to_id: Dict[str, int] = {}
            next_id = 0
            segments: List[Dict[str, Any]] = []
            
            for segment, track, label in diar.itertracks(yield_label=True):
                if label not in label_to_id:
                    label_to_id[label] = next_id
                    next_id += 1
                sid = label_to_id[label]
                segments.append({
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "speaker": int(sid),
                })
            
            # ✅ MERGE INTELIGENTE (del ejemplo)
            merged = self._merge_contiguous_segments(segments)
            
            speakers = [
                {"id": int(sid), "label": f"Speaker {int(sid)}"} 
                for sid in sorted(set(s["speaker"] for s in merged))
            ]
            
            return {
                "num_speakers": len(speakers), 
                "speakers": speakers, 
                "segments": merged, 
                "backend": "pyannote"
            }
            
        except Exception as e:
            logger.error(f"Error en pyannote: {str(e)}")
            # ✅ FALLBACK AUTOMÁTICO (del ejemplo)
            logger.info("Intentando fallback a resemblyzer...")
            return self._diarize_resemblyzer(wav_path, max_speakers)
    
    def assign_speaker_labels_optimized(self, diarization: Dict[str, Any], transcription: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        ✅ ASIGNACIÓN POR OVERLAP TEMPORAL OPTIMIZADA (del ejemplo)
        Asigna a cada segmento de transcripción el hablante con mayor solapamiento temporal
        """
        diar_segs = diarization.get("segments", [])
        tx_segs = transcription.get("segments", [])

        labeled = []
        for tx in tx_segs:
            t_start = tx["start"]
            t_end = tx["end"]
            
            # ✅ ENCONTRAR SPEAKER DOMINANTE POR OVERLAP (del ejemplo)
            best_speaker = None
            best_overlap = 0.0
            total_overlap = 0.0
            
            for ds in diar_segs:
                start = max(t_start, ds["start"])
                end = min(t_end, ds["end"])
                overlap = max(0.0, end - start)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = ds["speaker"]
                total_overlap += overlap
            
            # ✅ HEURÍSTICA DE CONFIANZA (del ejemplo)
            # confianza = overlap máximo / duración del segmento
            dur = max(1e-6, t_end - t_start)
            speaker_conf = float(max(0.0, min(1.0, best_overlap / dur)))
            speaker_label = f"Speaker {best_speaker}" if best_speaker is not None else "Speaker ?"
            
            labeled.append({
                "start": t_start,
                "end": t_end,
                "speaker": best_speaker,
                "speaker_label": speaker_label,
                "text": tx.get("text", ""),
                "speaker_confidence": speaker_conf,
            })

        return labeled

    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Obtiene información detallada del pipeline cargado para auditoría
        
        Returns:
            Dict con metadatos completos del pipeline
        """
        if not self.pipeline:
            return {
                'pipeline': 'no_cargado',
                'device': self.device,
                'version': 'N/A',
                'models': 'N/A',
                'parameters': 'N/A',
                'hash': 'N/A',
                'token_required': True,
                'cuda_available': torch.cuda.is_available() if PYANNOTE_AVAILABLE else False
            }
        
        try:
            pipeline_info = {
                'pipeline': self.modelo_cargado,
                'device': self.device,
                'version': getattr(self.pipeline, '__version__', 'pyannote-audio-3.x'),
                'models': {
                    'segmentation': getattr(self.pipeline, '_segmentation', 'model_info'),
                    'embedding': getattr(self.pipeline, '_embedding', 'model_info'),
                    'clustering': getattr(self.pipeline, '_clustering', 'model_info')
                },
                'parameters': getattr(self.pipeline, 'parameters', {}),
                'hash': getattr(self.pipeline, 'sha256', 'N/A'),
                'token_required': True,
                'cuda_available': torch.cuda.is_available() if PYANNOTE_AVAILABLE else False,
                'is_instantiated': hasattr(self.pipeline, '_segmentation'),
                'memory_usage_mb': self._estimate_memory_usage()
            }
            
            return pipeline_info
            
        except Exception as e:
            logger.error(f"Error obteniendo información del pipeline: {str(e)}")
            return {
                'pipeline': self.modelo_cargado,
                'device': self.device,
                'error': str(e)
            }
    
    def _estimate_memory_usage(self) -> str:
        """Estima el uso de memoria del pipeline"""
        try:
            if torch.cuda.is_available() and self.device == "cuda":
                memory_allocated = torch.cuda.memory_allocated() / 1024 / 1024  # MB
                return f"{memory_allocated:.1f}MB"
            else:
                return "unknown"
        except:
            return "unknown"
            
    def configurar_pipeline(self, 
                           modelo_nombre: str = "pyannote/speaker-diarization-3.1",
                           token: Optional[str] = None,
                           usar_gpu: bool = True) -> bool:
        """
        Configura el pipeline de diarización
        
        Args:
            modelo_nombre: Nombre del modelo en HuggingFace
            token: Token de HuggingFace (requerido para algunos modelos)
            usar_gpu: Si usar GPU cuando esté disponible
            
        Returns:
            bool: True si se configuró exitosamente
        """
        try:
            if not PYANNOTE_AVAILABLE:
                logger.warning("pyannote-audio no disponible")
                return False
                
            if not usar_gpu:
                self.device = "cpu"
                
            self.token_huggingface = token
            
            # Verificar si ya está cargado el mismo modelo
            if self.modelo_cargado == modelo_nombre and self.pipeline is not None:
                logger.info(f"Pipeline {modelo_nombre} ya está cargado")
                return True
                
            logger.info(f"Configurando pipeline de diarización: {modelo_nombre} en {self.device}")
            
            # Intentar cargar con token si está disponible
            if token:
                self.pipeline = Pipeline.from_pretrained(modelo_nombre, use_auth_token=token)
            else:
                logger.warning("Intentando cargar pipeline sin token - puede fallar con modelos premium")
                self.pipeline = Pipeline.from_pretrained(modelo_nombre)
            
            # Mover al dispositivo especificado
            if self.device == "cuda" and torch.cuda.is_available():
                self.pipeline = self.pipeline.to(torch.device("cuda"))
            else:
                self.pipeline = self.pipeline.to(torch.device("cpu"))
                self.device = "cpu"
                
            self.modelo_cargado = modelo_nombre
            
            logger.info(f"Pipeline {modelo_nombre} configurado exitosamente en {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando pipeline {modelo_nombre}: {str(e)}")
            # Fallback a versión básica sin token
            try:
                logger.info("Intentando fallback a modelo básico...")
                self.pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
                self.modelo_cargado = "pyannote/speaker-diarization"
                self.device = "cpu"
                logger.info("Fallback exitoso")
                return True
            except Exception as e2:
                logger.error(f"Fallback también falló: {str(e2)}")
                return False
    
    def procesar_diarizacion(self, 
                           archivo_audio: str,
                           configuracion: Dict[str, Any]) -> Dict[str, Any]:
        """
        ✅ PROCESAMIENTO DE DIARIZACIÓN MEJORADO (con mejoras del ejemplo)
        Incluye fallback automático y merge inteligente de segmentos
        
        Args:
            archivo_audio: Ruta al archivo de audio
            configuracion: Diccionario con configuración del usuario
            
        Returns:
            Dict con resultado de diarización y auditoría completa
        """
        try:
            # ===== AUDITORÍA: Extraer configuración del usuario =====
            modelo_diarizacion = configuracion.get('modelo_diarizacion', 'pyannote/speaker-diarization-3.1')
            min_speakers = configuracion.get('min_speakers', 1)
            max_speakers = configuracion.get('max_speakers', 8)
            backend = configuracion.get('backend', 'pyannote')
            token = configuracion.get('huggingface_token') or _HF_TOKEN
            
            logger.info(f"AUDIT - Parámetros de diarización recibidos:")
            logger.info(f"  - modelo_diarizacion: {modelo_diarizacion}")
            logger.info(f"  - min_speakers: {min_speakers}")
            logger.info(f"  - max_speakers: {max_speakers}")
            logger.info(f"  - backend: {backend}")
            logger.info(f"  - token_disponible: {bool(token)}")
            
            # ✅ SELECCIÓN DE BACKEND CON FALLBACK (del ejemplo)
            backend = (backend or _DIARIZATION_DEFAULT or "resemblyzer").lower()
            
            if backend == "none":
                return {
                    'exito': True,
                    'speakers_detectados': 0,
                    'segmentos_hablantes': [],
                    'mensaje': 'Diarización deshabilitada por configuración',
                    'backend': 'none'
                }
            
            # Verificar archivo
            if not os.path.exists(archivo_audio):
                raise FileNotFoundError(f"Archivo de audio no encontrado: {archivo_audio}")
            
            logger.info(f"Iniciando diarización de {archivo_audio} con backend {backend}")
            
            # ✅ INTENTAR PYANNOTE CON FALLBACK AUTOMÁTICO (del ejemplo)
            if backend == "pyannote":
                try:
                    resultado = self._diarize_pyannote_optimized(archivo_audio, max_speakers)
                    if resultado.get("num_speakers", 0) == 0:
                        logger.warning("pyannote no detectó speakers, intentando fallback...")
                        resultado = self._diarize_resemblyzer(archivo_audio, max_speakers)
                except Exception as e:
                    logger.error(f"pyannote falló: {str(e)}, usando fallback")
                    resultado = self._diarize_resemblyzer(archivo_audio, max_speakers)
            else:
                # usar resemblyzer directamente
                resultado = self._diarize_resemblyzer(archivo_audio, max_speakers)
            
            # ✅ CONVERTIR A FORMATO ESPERADO POR NUESTRO SISTEMA
            segmentos_convertidos = []
            for seg in resultado.get("segments", []):
                segmentos_convertidos.append({
                    'inicio': seg["start"],
                    'fin': seg["end"],
                    'speaker': f'SPEAKER_{seg["speaker"]:02d}',
                    'confianza': 0.8  # Default, se puede mejorar
                })
            
            # ✅ GENERAR INFORMACIÓN DE SPEAKERS EN ORDEN CRONOLÓGICO
            # Primero encontrar el orden de aparición temporal
            speaker_apariciones = []  # Lista para mantener orden de primera aparición
            speaker_tiempos = {}
            
            for seg in segmentos_convertidos:
                speaker_id = seg['speaker']
                if speaker_id not in speaker_tiempos:
                    speaker_tiempos[speaker_id] = seg['inicio']
                    speaker_apariciones.append(speaker_id)  # Agregar en orden de aparición
            
            # ✅ CREAR MAPEO DE SPEAKER_ID ORIGINAL A POSICIÓN CRONOLÓGICA
            mapeo_cronologico = {}
            for idx, speaker_id in enumerate(speaker_apariciones):
                # Mapear el speaker_id original a su posición cronológica
                mapeo_cronologico[speaker_id] = idx
                logger.info(f"🎯 MAPEO CRONOLÓGICO: {speaker_id} (apareció a {speaker_tiempos[speaker_id]:.1f}s) → Posición {idx+1}")
            
            # ✅ CREAR speakers_info CON POSICIONES CRONOLÓGICAS
            from collections import OrderedDict
            speakers_info_ordenado = OrderedDict()
            
            for idx, speaker_id in enumerate(speaker_apariciones):
                # Usar el índice cronológico como clave
                speaker_cronologico = f'SPEAKER_{idx:02d}'
                speakers_info_ordenado[speaker_cronologico] = {
                    'id': idx,  # ID basado en orden cronológico
                    'id_original_pyannote': int(speaker_id.split('_')[-1]),  # Guardar ID original de pyannote
                    'label': f"Speaker {idx+1}",  # Etiqueta temporal
                    'total_time': sum(
                        seg['fin'] - seg['inicio'] 
                        for seg in segmentos_convertidos 
                        if seg['speaker'] == speaker_id
                    ),
                    'tiempo_primera_aparicion': speaker_tiempos[speaker_id]
                }
                logger.info(f"   Speaker cronológico {speaker_cronologico}: primera aparición a {speaker_tiempos[speaker_id]:.1f}s")
            
            # ✅ ACTUALIZAR SEGMENTOS CON MAPEO CRONOLÓGICO
            for seg in segmentos_convertidos:
                speaker_original = seg['speaker']
                posicion_cronologica = mapeo_cronologico[speaker_original]
                seg['speaker'] = f'SPEAKER_{posicion_cronologica:02d}'
                seg['speaker_original_pyannote'] = speaker_original
                
            # ===== AUDITORÍA: Información del backend usado =====
            pipeline_info = {
                'backend_usado': resultado.get("backend", backend),
                'modelo': modelo_diarizacion if resultado.get("backend") == "pyannote" else "resemblyzer",
                'device': self.device,
                'num_speakers_detectados': resultado.get("num_speakers", 0),
                'fallback_usado': resultado.get("backend") != backend,
                'mapeo_cronologico': mapeo_cronologico  # Agregar mapeo para auditoría
            }
            
            logger.info(f"AUDIT - Diarización completada:")
            logger.info(f"  - Backend usado: {pipeline_info['backend_usado']}")
            logger.info(f"  - Speakers detectados: {pipeline_info['num_speakers_detectados']}")
            logger.info(f"  - Segmentos generados: {len(segmentos_convertidos)}")
            logger.info(f"  - Fallback usado: {pipeline_info['fallback_usado']}")
            
            return {
                'exito': True,
                'speakers_detectados': resultado.get("num_speakers", 0),
                'segmentos_hablantes': segmentos_convertidos,
                'hablantes': speakers_info_ordenado,  # ✅ ORDEN CRONOLÓGICO PRESERVADO
                'duracion_total': max([seg['fin'] for seg in segmentos_convertidos]) if segmentos_convertidos else 0.0,
                'mensaje': f'Diarización completada con {pipeline_info["backend_usado"]}',
                'parametros_aplicados': {
                    'modelo_diarizacion': pipeline_info['modelo'],
                    'min_speakers': min_speakers,
                    'max_speakers': max_speakers,
                    'backend': pipeline_info['backend_usado']
                },
                'metadatos_pipeline': pipeline_info
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error en diarización: {error_msg}")
            
            # Fallback final: simulación
            return {
                'exito': False,
                'error': error_msg,
                'speakers_detectados': 1,
                'segmentos_hablantes': [
                    {
                        'inicio': 0.0,
                        'fin': 10.0,
                        'speaker': 'SPEAKER_00',
                        'confianza': 0.5
                    }
                ],
                'mensaje': f'Error en diarización: {error_msg}',
                'parametros_aplicados': {
                    'modelo_diarizacion': 'fallback',
                    'backend': 'error'
                }
            }
            
    def _diarize_pyannote_optimized(self, archivo_audio: str, max_speakers: int) -> Dict[str, Any]:
        """
        ✅ PROCESAMIENTO PYANNOTE OPTIMIZADO (del ejemplo)
        Con merge de segmentos contiguos y asignación por overlap temporal
        """
        try:
            if not PYANNOTE_AVAILABLE:
                raise ImportError("pyannote-audio no disponible")
            
            # Load pipeline con cache
            pipeline = self._get_cached_pipeline("pyannote/speaker-diarization-3.1")
            
            # Aplicar diarización
            diarization = pipeline(archivo_audio, num_speakers=max_speakers)
            
            # Convertir a formato estándar
            segments = []
            for segment, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "speaker": int(speaker.split('_')[-1]) if '_' in speaker else 0
                })
            
            # ✅ MERGE CONTIGUOUS SEGMENTS (del ejemplo)
            merged_segments = self._merge_contiguous_segments(segments)
            
            # ✅ ASIGNACIÓN OPTIMIZADA DE SPEAKERS (del ejemplo)
            final_segments = self.assign_speaker_labels_optimized(merged_segments)
            
            num_speakers = len(set(seg["speaker"] for seg in final_segments))
            
            return {
                "segments": final_segments,
                "num_speakers": num_speakers,
                "speakers": [{"id": i, "label": f"Speaker {i+1}"} for i in range(num_speakers)],
                "backend": "pyannote"
            }
            
        except Exception as e:
            logger.error(f"Error en pyannote optimizado: {str(e)}")
            raise
            
    def _get_cached_pipeline(self, model_name: str):
        """Cache de pipelines para evitar recargas"""
        if hasattr(self, '_pipeline_cache') and model_name in self._pipeline_cache:
            return self._pipeline_cache[model_name]
        
        if not hasattr(self, '_pipeline_cache'):
            self._pipeline_cache = {}
        
        # Crear nuevo pipeline
        from pyannote.audio import Pipeline
        pipeline = Pipeline.from_pretrained(model_name, use_auth_token=_HF_TOKEN)
        
        if self.device != "cpu":
            pipeline = pipeline.to(torch.device(self.device))
        
        self._pipeline_cache[model_name] = pipeline
        return pipeline
    
    def _procesar_resultado_diarizacion(self, diarizacion: Annotation) -> Dict[str, Any]:
        """
        Procesa el resultado raw de pyannote para formato estándar
        """
        segmentos_procesados = []
        speakers_unicos = set()
        
        def formatear_tiempo_str(segundos: float) -> str:
            """Convierte segundos a formato MM:SS"""
            minutos = int(segundos // 60)
            segundos_restantes = int(segundos % 60)
            return f"{minutos:02d}:{segundos_restantes:02d}"
        
        for segmento, _, speaker in diarizacion.itertracks(yield_label=True):
            inicio = segmento.start
            fin = segmento.end
            
            segmento_procesado = {
                'inicio': inicio,
                'fin': fin,
                'start': inicio,  # Alias para compatibilidad
                'end': fin,       # Alias para compatibilidad
                'start_time_str': formatear_tiempo_str(inicio),
                'end_time_str': formatear_tiempo_str(fin),
                'duracion': fin - inicio,
                'speaker': speaker,
                'speaker_id': speaker,  # Alias
                'confianza': 0.8,  # pyannote no siempre proporciona confianza
                'confidence': 0.8   # Alias
            }
            
            segmentos_procesados.append(segmento_procesado)
            speakers_unicos.add(speaker)
        
        # Ordenar segmentos por tiempo de inicio
        segmentos_procesados.sort(key=lambda x: x['inicio'])
        
        duracion_total = max([seg['fin'] for seg in segmentos_procesados]) if segmentos_procesados else 0.0
        
        return {
            'segmentos': segmentos_procesados,
            'speakers_detectados': len(speakers_unicos),
            'duracion_total': duracion_total,
            'num_segmentos': len(segmentos_procesados),
            'lista_speakers': sorted(list(speakers_unicos))
        }
    
    def _procesar_resultado_diarizacion_inteligente(self, 
                                                   diarizacion: Annotation,
                                                   participantes_esperados: List[Dict[str, Any]] = None,
                                                   hablantes_predefinidos: List[Dict[str, Any]] = None,
                                                   configuracion: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa el resultado de pyannote con mapeo inteligente a participantes predefinidos
        
        Args:
            diarizacion: Resultado de pyannote
            participantes_esperados: Lista de participantes esperados del audio
            hablantes_predefinidos: Lista de hablantes predefinidos del sistema
            configuracion: Configuración que incluye tipo de mapeo
            
        Returns:
            Dict con resultado procesado y mapeo inteligente
        """
        segmentos_procesados = []
        speakers_detectados = {}
        speakers_tiempo_aparicion = {}  # Para mapeo por orden de aparición
        
        def formatear_tiempo_str(segundos: float) -> str:
            """Convierte segundos a formato MM:SS"""
            minutos = int(segundos // 60)
            segundos_restantes = int(segundos % 60)
            return f"{minutos:02d}:{segundos_restantes:02d}"
        
        # PASO 1: Procesar segmentos y registrar orden de aparición
        for segmento, _, speaker in diarizacion.itertracks(yield_label=True):
            inicio = segmento.start
            fin = segmento.end
            
            # Registrar primera aparición de cada speaker para mapeo inteligente
            if speaker not in speakers_tiempo_aparicion:
                speakers_tiempo_aparicion[speaker] = inicio
                
            segmento_procesado = {
                'inicio': inicio,
                'fin': fin,
                'start': inicio,  # Alias para compatibilidad
                'end': fin,       # Alias para compatibilidad
                'start_time_str': formatear_tiempo_str(inicio),
                'end_time_str': formatear_tiempo_str(fin),
                'duracion': fin - inicio,
                'speaker': speaker,  # Será remapeado después
                'speaker_original': speaker,  # Conservar original de pyannote
                'speaker_id': speaker,  # Alias
                'confianza': 0.8,  # pyannote no siempre proporciona confianza
                'confidence': 0.8   # Alias
            }
            
            segmentos_procesados.append(segmento_procesado)
            speakers_detectados[speaker] = speakers_detectados.get(speaker, 0) + 1
        
        # PASO 2: MAPEO INTELIGENTE basado en participantes esperados
        mapeo_speakers = {}
        
        if participantes_esperados and len(participantes_esperados) > 0:
            logger.info(f"AUDIT - Aplicando mapeo inteligente con {len(participantes_esperados)} participantes esperados")
            
            # NUEVA OPCIÓN: Mapeo por orden del JSON vs orden de aparición temporal
            if configuracion is None:
                configuracion = {}
            tipo_mapeo = configuracion.get('tipo_mapeo_speakers', 'orden_json')  # 'orden_json' o 'orden_temporal'
            
            if tipo_mapeo == 'orden_json':
                # MAPEO POR ORDEN CRONOLÓGICO DE APARICIÓN = ORDEN DEL JSON DEL USUARIO
                logger.info("AUDIT - Usando mapeo por ORDEN CRONOLÓGICO DE APARICIÓN")
                logger.info("AUDIT - 1er speaker en aparecer → 1er participante JSON")
                logger.info("AUDIT - 2do speaker en aparecer → 2do participante JSON")
                logger.info("AUDIT - 3er speaker en aparecer → 3er participante JSON")
                
                # Ordenar speakers por tiempo de PRIMERA aparición (orden cronológico)
                speakers_ordenados_cronologicamente = sorted(speakers_tiempo_aparicion.items(), key=lambda x: x[1])
                
                logger.info("AUDIT - Orden cronológico detectado:")
                for i, (speaker_id, tiempo) in enumerate(speakers_ordenados_cronologicamente):
                    logger.info(f"  {i+1}. {speaker_id} apareció por primera vez a los {tiempo:.1f}s")
                
                # VALIDAR que pyannote detectó exactamente los hablantes esperados
                if len(speakers_ordenados_cronologicamente) != len(participantes_esperados):
                    logger.warning(f"ADVERTENCIA: pyannote detectó {len(speakers_ordenados_cronologicamente)} speakers pero se esperaban {len(participantes_esperados)}")
                    logger.warning("Verificar configuración min_speakers/max_speakers forzada")
                
                # Mapear por orden cronológico: 1er aparición → 1er participante JSON
                for i, (speaker_original, tiempo_aparicion) in enumerate(speakers_ordenados_cronologicamente):
                    if i < len(participantes_esperados):
                        participante = participantes_esperados[i]  # i-ésimo participante del JSON
                        
                        nombre_mapeado = participante.get('nombre_completo', 
                                                        f"{participante.get('nombres', '')} {participante.get('apellidos', '')}".strip())
                        if not nombre_mapeado:
                            nombre_mapeado = f"Participante_{i+1}"
                            
                        mapeo_speakers[speaker_original] = {
                            'nombre': nombre_mapeado,
                            'id': f"SPEAKER_{i:02d}",
                            'participante_info': participante,
                            'orden_json': i+1,  # Posición en JSON del usuario
                            'orden_cronologico': i+1,  # Orden de aparición cronológica
                            'tiempo_primera_aparicion': tiempo_aparicion
                        }
                        
                        logger.info(f"AUDIT - {speaker_original} (aparece {i+1}º a los {tiempo_aparicion:.1f}s) → {nombre_mapeado} (posición {i+1} en JSON)")
                    else:
                        # Si hay más speakers de los esperados, crear entrada sin mapear
                        logger.error(f"ERROR: Speaker adicional {speaker_original} detectado pero no hay participante {i+1} en JSON")
                
                # Verificar que todos los participantes tienen speaker asignado
                for i, participante in enumerate(participantes_esperados):
                    if i >= len(speakers_ordenados_cronologicamente):
                        logger.error(f"ERROR: Participante {i+1} '{participante.get('nombre_completo')}' no tiene speaker asignado")
                
                logger.info(f"AUDIT - Mapeo cronológico completado: {len(mapeo_speakers)} speakers mapeados de {len(participantes_esperados)} esperados")
                    
            else:
                # MAPEO POR ORDEN DE APARICIÓN TEMPORAL (comportamiento anterior)
                logger.info("AUDIT - Usando mapeo por ORDEN DE APARICIÓN TEMPORAL")
                
                # Ordenar speakers detectados por orden de aparición temporal
                speakers_ordenados = sorted(speakers_tiempo_aparicion.items(), key=lambda x: x[1])
                
                for i, (speaker_original, tiempo_aparicion) in enumerate(speakers_ordenados):
                    if i < len(participantes_esperados):
                        participante = participantes_esperados[i]
                        nombre_mapeado = participante.get('nombre_completo', 
                                                        f"{participante.get('nombres', '')} {participante.get('apellidos', '')}".strip())
                        if not nombre_mapeado:
                            nombre_mapeado = f"Participante_{i+1}"
                            
                        mapeo_speakers[speaker_original] = {
                            'nombre': nombre_mapeado,
                            'id': f"SPEAKER_{i:02d}",
                            'participante_info': participante,
                            'orden_aparicion': i+1,
                            'tiempo_primera_aparicion': tiempo_aparicion
                        }
                        
                        logger.info(f"AUDIT - Speaker {speaker_original} → {nombre_mapeado} (aparición: {tiempo_aparicion:.1f}s)")
                    else:
                        # Speakers adicionales no esperados
                        mapeo_speakers[speaker_original] = {
                            'nombre': f"Speaker_Adicional_{i+1}",
                            'id': f"SPEAKER_{i:02d}",
                            'participante_info': {},
                        'orden_aparicion': i+1,
                        'tiempo_primera_aparicion': tiempo_aparicion
                    }
                    logger.info(f"AUDIT - Speaker adicional {speaker_original} → Speaker_Adicional_{i+1}")
        else:
            # Sin participantes esperados, usar mapeo genérico
            speakers_ordenados = sorted(speakers_tiempo_aparicion.items(), key=lambda x: x[1])
            for i, (speaker_original, tiempo_aparicion) in enumerate(speakers_ordenados):
                mapeo_speakers[speaker_original] = {
                    'nombre': f"Hablante_{i+1}",
                    'id': f"SPEAKER_{i:02d}",
                    'participante_info': {},
                    'orden_aparicion': i+1,
                    'tiempo_primera_aparicion': tiempo_aparicion
                }
        
        # PASO 3: Aplicar mapeo a todos los segmentos
        for segmento in segmentos_procesados:
            speaker_original = segmento['speaker_original']
            if speaker_original in mapeo_speakers:
                mapeo_info = mapeo_speakers[speaker_original]
                segmento['speaker'] = mapeo_info['nombre']
                segmento['speaker_id'] = mapeo_info['id']
                segmento['participante_info'] = mapeo_info['participante_info']
                # Usar el campo correcto según el tipo de mapeo
                segmento['orden_aparicion'] = mapeo_info.get('orden_cronologico', mapeo_info.get('orden_aparicion', 1))
        
        # Ordenar segmentos por tiempo de inicio
        segmentos_procesados.sort(key=lambda x: x['inicio'])
        
        duracion_total = max([seg['fin'] for seg in segmentos_procesados]) if segmentos_procesados else 0.0
        
        return {
            'segmentos': segmentos_procesados,
            'speakers_detectados': len(speakers_detectados),
            'duracion_total': duracion_total,
            'num_segmentos': len(segmentos_procesados),
            'lista_speakers': sorted(list(speakers_detectados.keys())),
            'mapeo_inteligente': mapeo_speakers,
            'participantes_mapeados': len(participantes_esperados) if participantes_esperados else 0,
            'orden_aparicion': [mapeo_speakers[sp]['nombre'] for sp, _ in sorted(speakers_tiempo_aparicion.items(), key=lambda x: x[1])]
        }
    
    def combinar_transcripcion_y_diarizacion(self, 
                                           resultado_whisper: Dict[str, Any],
                                           resultado_diarizacion: Dict[str, Any],
                                           configuracion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina resultados de transcripción y diarización con auditoría
        """
        try:
            logger.info("AUDIT - Combinando transcripción y diarización")
            
            # Extraer configuración de combinación
            metodo_combinacion = configuracion.get('metodo_combinacion', 'overlap_temporal')
            threshold_overlap = configuracion.get('threshold_overlap', 0.5)
            
            logger.info(f"AUDIT - Método de combinación: {metodo_combinacion}")
            logger.info(f"AUDIT - Threshold de overlap: {threshold_overlap}")
            
            segmentos_whisper = resultado_whisper.get('segmentos', [])
            segmentos_diarizacion = resultado_diarizacion.get('segmentos', [])
            
            segmentos_combinados = []
            
            for seg_whisper in segmentos_whisper:
                inicio_whisper = seg_whisper['inicio']
                fin_whisper = seg_whisper['fin']
                texto = seg_whisper['texto']
                
                # Buscar speaker más probable por overlap temporal
                mejor_speaker = 'SPEAKER_00'
                mejor_overlap = 0.0
                
                for seg_diar in segmentos_diarizacion:
                    inicio_diar = seg_diar['inicio']
                    fin_diar = seg_diar['fin']
                    
                    # Calcular overlap
                    overlap_inicio = max(inicio_whisper, inicio_diar)
                    overlap_fin = min(fin_whisper, fin_diar)
                    
                    if overlap_fin > overlap_inicio:
                        overlap_duracion = overlap_fin - overlap_inicio
                        whisper_duracion = fin_whisper - inicio_whisper
                        overlap_ratio = overlap_duracion / whisper_duracion if whisper_duracion > 0 else 0
                        
                        if overlap_ratio > mejor_overlap and overlap_ratio >= threshold_overlap:
                            mejor_overlap = overlap_ratio
                            mejor_speaker = seg_diar['speaker']
                
                segmento_combinado = {
                    'inicio': inicio_whisper,
                    'fin': fin_whisper,
                    'duracion': fin_whisper - inicio_whisper,
                    'texto': texto,
                    'speaker': mejor_speaker,
                    'confianza_transcripcion': seg_whisper.get('confianza', 0.8),
                    'confianza_speaker': mejor_overlap,
                    'start_time_str': seg_whisper.get('start_time_str', ''),
                    'end_time_str': seg_whisper.get('end_time_str', '')
                }
                
                segmentos_combinados.append(segmento_combinado)
            
            return {
                'exito': True,
                'segmentos_combinados': segmentos_combinados,
                'num_segmentos': len(segmentos_combinados),
                'speakers_detectados': resultado_diarizacion.get('speakers_detectados', 0),
                'duracion_total': resultado_whisper.get('duracion_total', 0.0),
                'parametros_combinacion': {
                    'metodo': metodo_combinacion,
                    'threshold_overlap': threshold_overlap
                },
                'auditoria_combinacion': {
                    'segmentos_whisper': len(segmentos_whisper),
                    'segmentos_diarizacion': len(segmentos_diarizacion),
                    'segmentos_combinados': len(segmentos_combinados),
                    'parametros_del_usuario': True
                }
            }
            
        except Exception as e:
            logger.error(f"Error combinando resultados: {str(e)}")
            return {
                'exito': False,
                'error': str(e),
                'configuracion_original': configuracion
            }
    
    def limpiar_pipeline(self):
        """
        Libera memoria del pipeline cargado
        """
        if self.pipeline:
            del self.pipeline
            self.pipeline = None
            self.modelo_cargado = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.info("Pipeline de diarización liberado de memoria")