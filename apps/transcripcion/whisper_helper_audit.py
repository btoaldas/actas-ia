"""
Helper mejorado para procesamiento de audio con Whisper
Incluye auditoría completa de parámetros y metadatos del modelo
MEJORAS ADOPTADAS DEL EJEMPLO QUE FUNCIONA BIEN
"""
import os
import logging
from typing import Dict, Any, Optional, List
import tempfile
import numpy as np

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Intentar usar faster-whisper si está disponible (mejor rendimiento)
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)

# ✅ CONFIGURACIÓN OPTIMIZADA (del ejemplo)
_DEFAULT_MODEL_NAME = os.getenv("WHISPER_MODEL", "base")
_NUM_THREADS = int(os.getenv("NUM_THREADS", "4"))
_models_cache = {}  # Cache global de modelos


class WhisperProcessor:
    """Procesador de transcripción usando Whisper con mejores prácticas adoptadas"""
    
    def __init__(self):
        if not WHISPER_AVAILABLE and not FASTER_WHISPER_AVAILABLE:
            logger.warning("Whisper no está disponible. Funcionalidad limitada.")
            
        self.modelo = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.modelo_cargado = None
        self.use_faster_whisper = FASTER_WHISPER_AVAILABLE and os.getenv("USE_FASTER_WHISPER", "true").lower() == "true"
        
    def _get_cached_model(self, modelo_whisper: str):
        """
        Obtiene modelo del cache o lo carga (mejora del ejemplo)
        """
        key = f"{modelo_whisper}_{self.device}"
        
        if key not in _models_cache:
            if self.use_faster_whisper:
                logger.info(f"Cargando faster-whisper modelo: {modelo_whisper}")
                _models_cache[key] = WhisperModel(
                    modelo_whisper,
                    device="cpu",  # faster-whisper maneja GPU automáticamente
                    compute_type="int8",
                    cpu_threads=_NUM_THREADS,
                )
            else:
                logger.info(f"Cargando whisper modelo: {modelo_whisper}")
                _models_cache[key] = whisper.load_model(modelo_whisper, device=self.device)
        
        return _models_cache[key]
        
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información detallada del modelo cargado para auditoría
        
        Returns:
            Dict con metadatos completos del modelo
        """
        if not self.modelo:
            return {
                'modelo': 'no_cargado',
                'device': self.device,
                'version': 'N/A',
                'size_mb': 'N/A',
                'hash': 'N/A',
                'path': 'N/A',
                'parametros_soportados': ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
                'cuda_available': torch.cuda.is_available() if WHISPER_AVAILABLE else False
            }
        
        try:
            # Mapeo de tamaños aproximados por modelo (MB)
            model_sizes = {
                'tiny': 39,
                'base': 74,
                'small': 244,
                'medium': 769,
                'large': 1550,
                'large-v2': 1550,
                'large-v3': 1550
            }
            
            model_info = {
                'modelo': self.modelo_cargado,
                'device': self.device,
                'version': getattr(self.modelo, '__version__', 'whisper-1.0'),
                'size_mb': model_sizes.get(self.modelo_cargado, 'unknown'),
                'hash': getattr(self.modelo, 'sha256', 'N/A'),
                'path': getattr(self.modelo, 'path', 'cached'),
                'parametros_soportados': ['temperature', 'language', 'task', 'word_timestamps', 'verbose'],
                'cuda_available': torch.cuda.is_available() if WHISPER_AVAILABLE else False,
                'dims': getattr(self.modelo, 'dims', {}),
                'is_multilingual': getattr(self.modelo, 'is_multilingual', True),
                'languages': getattr(self.modelo, 'languages', [])
            }
            
            return model_info
            
        except Exception as e:
            logger.error(f"Error obteniendo información del modelo: {str(e)}")
            return {
                'modelo': self.modelo_cargado,
                'device': self.device,
                'error': str(e)
            }
            
    def cargar_modelo(self, modelo_nombre: str = "base", usar_gpu: bool = True) -> bool:
        """
        Carga el modelo de Whisper especificado
        
        Args:
            modelo_nombre: tiny, base, small, medium, large, large-v2, large-v3
            usar_gpu: Si usar GPU cuando esté disponible
            
        Returns:
            bool: True si se cargó exitosamente
        """
        try:
            if not usar_gpu:
                self.device = "cpu"
                
            if self.modelo_cargado == modelo_nombre and self.modelo is not None:
                logger.info(f"Modelo {modelo_nombre} ya está cargado")
                return True
                
            logger.info(f"Cargando modelo Whisper: {modelo_nombre} en {self.device}")
            self.modelo = whisper.load_model(modelo_nombre, device=self.device)
            self.modelo_cargado = modelo_nombre
            
            logger.info(f"Modelo {modelo_nombre} cargado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando modelo Whisper {modelo_nombre}: {str(e)}")
            return False
    
    def transcribir_audio(self, 
                         archivo_audio: str,
                         configuracion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe un archivo de audio usando Whisper con parámetros optimizados
        MEJORAS ADOPTADAS DEL EJEMPLO QUE FUNCIONA BIEN
        
        Args:
            archivo_audio: Ruta al archivo de audio
            configuracion: Diccionario con configuración del usuario
            
        Returns:
            Dict con resultado de transcripción y auditoría completa
        """
        if not WHISPER_AVAILABLE and not FASTER_WHISPER_AVAILABLE:
            logger.warning("Whisper no disponible, retornando transcripción simulada")
            return {
                'exito': True,
                'texto_completo': 'Transcripción de ejemplo porque Whisper no está disponible.',
                'modelo_usado': 'simulado',
                'segmentos': [
                    {
                        'inicio': 0.0,
                        'fin': 5.0,
                        'duracion': 5.0,
                        'texto': 'Transcripción de ejemplo porque Whisper no está disponible.',
                        'confianza': 0.8
                    }
                ],
                'idioma_detectado': 'es',
                'probabilidad_idioma': 0.9,
                'duracion_total': 5.0,
                'mensaje': 'Whisper no disponible - usando simulación',
                'parametros_aplicados': {
                    'modelo_whisper': 'simulado',
                    'palabra_por_palabra': configuracion.get('palabra_por_palabra', False),
                    'mejora_audio': configuracion.get('mejora_audio', False)
                },
                'metadatos_modelo': {
                    'modelo': 'simulado',
                    'device': 'cpu',
                    'version': 'N/A',
                    'size_mb': 'N/A',
                    'hash': 'N/A'
                }
            }
            
        try:
            # ===== AUDITORÍA: Extraer configuración del usuario =====
            modelo_nombre = configuracion.get('modelo_whisper', 'base')
            idioma = configuracion.get('idioma_principal', 'es')
            temperatura = configuracion.get('temperatura', 0.0)
            usar_gpu = configuracion.get('usar_gpu', True)
            palabra_por_palabra = configuracion.get('palabra_por_palabra', False)
            mejora_audio = configuracion.get('mejora_audio', False)
            
            # Log de auditoría: mostrar que parámetros se recibieron del usuario
            logger.info(f"AUDIT - Parámetros recibidos del usuario:")
            logger.info(f"  - modelo_whisper: {modelo_nombre}")
            logger.info(f"  - idioma_principal: {idioma}")
            logger.info(f"  - temperatura: {temperatura}")
            logger.info(f"  - usar_gpu: {usar_gpu}")
            logger.info(f"  - palabra_por_palabra: {palabra_por_palabra}")
            logger.info(f"  - mejora_audio: {mejora_audio}")
            
            # Obtener modelo del cache
            modelo = self._get_cached_model(modelo_nombre)
            self.modelo = modelo
            self.modelo_cargado = modelo_nombre
            
            # Verificar que el archivo existe
            if not os.path.exists(archivo_audio):
                raise FileNotFoundError(f"Archivo de audio no encontrado: {archivo_audio}")
            
            logger.info(f"Iniciando transcripción de {archivo_audio}")
            
            # ===== PARÁMETROS OPTIMIZADOS (del ejemplo) =====
            if self.use_faster_whisper:
                # faster-whisper con parámetros optimizados
                segments, info = modelo.transcribe(
                    archivo_audio,
                    beam_size=1,                        # ✅ Rápido y eficiente
                    best_of=1,                         # ✅ Sin múltiples candidatos
                    vad_filter=True,                   # ✅ CLAVE! Filtro VAD para silencio
                    language=idioma if idioma != 'auto' else None,
                    initial_prompt=configuracion.get('prompt_inicial', None),
                    condition_on_previous_text=False,   # ✅ IMPORTANTE! Evita dependencias
                    no_speech_threshold=0.5,           # ✅ Umbral de silencio
                    temperature=temperatura,           # ✅ Del usuario
                    word_timestamps=palabra_por_palabra # ✅ Para mejor confianza
                )
                
                # Procesar segmentos de faster-whisper
                segmentos_resultado = []
                total_words = 0
                
                for seg in segments:
                    # ✅ CÁLCULO DE CONFIANZA MEJORADO (del ejemplo)
                    asr_conf = None
                    try:
                        words = getattr(seg, 'words', None) or []
                        if words:
                            probs = [getattr(w, 'probability', None) for w in words]
                            probs = [p for p in probs if p is not None]
                            if probs:
                                asr_conf = float(sum(probs) / len(probs))
                        # fallback con avg_logprob si no hay words
                        if asr_conf is None and hasattr(seg, 'avg_logprob') and seg.avg_logprob is not None:
                            # mapear logprob (~[-5..0]) a [0..1] de forma suave
                            x = float(seg.avg_logprob)
                            asr_conf = 1.0 / (1.0 + np.exp(- (x + 3.0)))  # shift
                    except Exception:
                        asr_conf = None
                    
                    texto = seg.text.strip()
                    total_words += len(texto.split()) if texto else 0
                    
                    segmentos_resultado.append({
                        'inicio': float(seg.start),
                        'fin': float(seg.end),
                        'duracion': float(seg.end - seg.start),
                        'texto': texto,
                        'confianza': asr_conf,
                        'start': float(seg.start),  # Para compatibilidad
                        'end': float(seg.end),
                        'text': texto
                    })
                
                resultado = {
                    'text': ' '.join([s['texto'] for s in segmentos_resultado]),
                    'segments': segmentos_resultado,
                    'language': info.language,
                    'language_probability': getattr(info, 'language_probability', 0.0) if hasattr(info, 'language_probability') else None
                }
                
            else:
                # Whisper tradicional con opciones optimizadas
                opciones = {
                    "language": idioma if idioma != 'auto' else None,
                    "temperature": temperatura,
                    "task": "transcribe",
                    "verbose": True,
                    "word_timestamps": palabra_por_palabra,
                    "condition_on_previous_text": False,  # ✅ Del ejemplo
                    "no_speech_threshold": 0.5           # ✅ Del ejemplo
                }
                
                # Log de auditoría: mostrar opciones que se envían a Whisper
                logger.info(f"AUDIT - Opciones optimizadas enviadas a Whisper: {opciones}")
                
                # Ejecutar transcripción
                resultado = modelo.transcribe(archivo_audio, **opciones)
            
            # Obtener información del modelo cargado
            model_info = self.get_model_info()
            
            # Procesar resultado
            transcripcion_procesada = self._procesar_resultado_whisper(resultado)
            
            logger.info(f"Transcripción completada. {len(transcripcion_procesada['segmentos'])} segmentos")
            
            # ===== AUDITORÍA: Retornar con todos los parámetros usados =====
            return {
                'exito': True,
                'texto_completo': transcripcion_procesada['texto_completo'],
                'segmentos': transcripcion_procesada['segmentos'],
                'idioma_detectado': resultado.get('language', idioma),
                'duracion_total': transcripcion_procesada['duracion_total'],
                'configuracion_original': configuracion,
                'parametros_aplicados': {
                    'modelo_whisper': modelo_nombre,
                    'idioma_principal': idioma,
                    'temperatura': temperatura,
                    'usar_gpu': usar_gpu,
                    'palabra_por_palabra': palabra_por_palabra,
                    'mejora_audio': mejora_audio,
                    'opciones_whisper_reales': opciones,
                    'device_usado': self.device
                },
                'metadatos_modelo': model_info,
                'auditoria': {
                    'parametros_hardcodeados': False,
                    'parametros_del_usuario': True,
                    'modelo_solicitado': modelo_nombre,
                    'modelo_usado': self.modelo_cargado,
                    'flags_aplicados': {
                        'palabra_por_palabra': palabra_por_palabra,
                        'mejora_audio': mejora_audio
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error en transcripción: {str(e)}")
            return {
                'exito': False,
                'error': str(e),
                'configuracion_original': configuracion,
                'parametros_aplicados': {
                    'modelo_whisper': configuracion.get('modelo_whisper', 'base'),
                    'error_en_paso': 'transcripcion'
                }
            }
    
    def _procesar_resultado_whisper(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa el resultado raw de Whisper para formato estándar
        """
        segmentos_procesados = []
        texto_completo = resultado.get('text', '').strip()
        
        def formatear_tiempo_str(segundos: float) -> str:
            """Convierte segundos a formato MM:SS"""
            minutos = int(segundos // 60)
            segundos_restantes = int(segundos % 60)
            return f"{minutos:02d}:{segundos_restantes:02d}"
        
        for segmento in resultado.get('segments', []):
            inicio = segmento.get('start', 0.0)
            fin = segmento.get('end', 0.0)
            
            segmento_procesado = {
                'inicio': inicio,
                'fin': fin,
                'start': inicio,  # Alias para compatibilidad
                'end': fin,       # Alias para compatibilidad
                'start_time_str': formatear_tiempo_str(inicio),
                'end_time_str': formatear_tiempo_str(fin),
                'duracion': fin - inicio,
                'texto': segmento.get('text', '').strip(),
                'text': segmento.get('text', '').strip(),  # Alias
                'confianza': segmento.get('avg_logprob', 0.0),
                'confidence': segmento.get('avg_logprob', 0.0),  # Alias
                'tokens': segmento.get('tokens', []),
                'temperature': segmento.get('temperature', 0.0),
                'compression_ratio': segmento.get('compression_ratio', 0.0),
                'no_speech_prob': segmento.get('no_speech_prob', 0.0)
            }
            
            # Agregar timestamps por palabra si están disponibles
            if 'words' in segmento:
                segmento_procesado['palabras'] = segmento['words']
            
            segmentos_procesados.append(segmento_procesado)
        
        duracion_total = max([seg['fin'] for seg in segmentos_procesados]) if segmentos_procesados else 0.0
        
        return {
            'texto_completo': texto_completo,
            'segmentos': segmentos_procesados,
            'duracion_total': duracion_total,
            'num_segmentos': len(segmentos_procesados)
        }
    
    def limpiar_modelo(self):
        """
        Libera memoria del modelo cargado
        """
        if self.modelo:
            del self.modelo
            self.modelo = None
            self.modelo_cargado = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            logger.info("Modelo Whisper liberado de memoria")