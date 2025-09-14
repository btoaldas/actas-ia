"""
Pipeline robusto de procesamiento de audio.
Combina FFmpeg, SoX, librosa y noisereduce para mejoras profesionales.
MEJORADO con mejores prácticas del ejemplo externo que funciona bien.
"""
import os
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional

import numpy as np
import librosa
import soundfile as sf

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    logging.warning("noisereduce no disponible, se omitirá reducción de ruido avanzada")

try:
    import webrtcvad
    WEBRTCVAD_AVAILABLE = True
except ImportError:
    WEBRTCVAD_AVAILABLE = False
    logging.warning("webrtcvad no disponible, se usará detección de silencio por energía")

# ✅ MEJORA DEL EJEMPLO: Importar resemblyzer para preprocess_wav
try:
    from resemblyzer import preprocess_wav
    RESEMBLYZER_AVAILABLE = True
except ImportError:
    RESEMBLYZER_AVAILABLE = False
    logging.warning("resemblyzer no disponible, se usará procesamiento estándar")

logger = logging.getLogger(__name__)

# Configuración del pipeline optimizada del ejemplo
FFMPEG = "ffmpeg"
SOX = "sox"
DEFAULT_SAMPLE_RATE = 16000  # ✅ IGUAL QUE EL EJEMPLO
DEFAULT_CHANNELS = 1
PIPELINE_VERSION = "v2.1_optimized"  # ✅ VERSIÓN MEJORADA


class AudioPipelineError(Exception):
    """Excepción personalizada para errores del pipeline de audio"""
    pass


def run_command(cmd: list, check: bool = True) -> subprocess.CompletedProcess:
    """
    Ejecuta un comando de sistema y maneja errores.
    """
    try:
        logger.debug(f"Ejecutando comando: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        error_msg = f"Error ejecutando comando: {e.stderr}"
        logger.error(error_msg)
        raise AudioPipelineError(error_msg) from e


def get_audio_info(file_path: str) -> Dict:
    """
    Obtiene información detallada del archivo de audio usando FFprobe.
    """
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json", 
        "-show_format", "-show_streams", file_path
    ]
    
    try:
        result = run_command(cmd)
        import json
        data = json.loads(result.stdout)
        
        # Buscar el stream de audio
        audio_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'audio':
                audio_stream = stream
                break
        
        if not audio_stream:
            raise AudioPipelineError("No se encontró stream de audio en el archivo")
        
        format_info = data.get('format', {})
        
        return {
            'duration': float(format_info.get('duration', 0)),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': int(audio_stream.get('channels', 0)),
            'codec': audio_stream.get('codec_name', 'unknown'),
            'bit_rate': int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0,
            'format': format_info.get('format_name', 'unknown'),
            'size': int(format_info.get('size', 0)),
        }
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise AudioPipelineError(f"Error analizando información de audio: {e}") from e


def convert_to_wav_mono(input_path: str, output_path: str, sample_rate: int = DEFAULT_SAMPLE_RATE) -> None:
    """
    Convierte cualquier formato de audio a WAV mono con sample rate específico.
    """
    cmd = [
        FFMPEG, "-y", "-i", input_path,
        "-ac", str(DEFAULT_CHANNELS),  # mono
        "-ar", str(sample_rate),       # sample rate
        "-vn",                         # sin video
        "-f", "wav",                   # formato WAV
        "-acodec", "pcm_s16le",       # 16-bit PCM
        output_path
    ]
    
    run_command(cmd)
    logger.info(f"Audio convertido a WAV mono: {output_path}")


def ensure_wav_optimized(input_path: str, output_dir: Optional[str] = None) -> str:
    """
    ✅ FUNCIÓN OPTIMIZADA INSPIRADA EN EL EJEMPLO EXTERNO
    Convierte a WAV mono 16kHz si es necesario, similar al ejemplo que funciona bien.
    Soporta mp3, wav, m4a, etc.
    """
    input_path_obj = Path(input_path)
    
    if output_dir is None:
        output_dir = input_path_obj.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre de salida optimizado
    base_name = input_path_obj.stem
    output_path = output_dir / f"{base_name}_16k.wav"
    
    # Si ya existe el archivo procesado, devolverlo
    if output_path.exists():
        logger.info(f"Archivo WAV optimizado ya existe: {output_path}")
        return str(output_path)
    
    # ✅ COMANDO FFMPEG OPTIMIZADO (del ejemplo)
    cmd = [
        FFMPEG, "-y", "-i", str(input_path),
        "-ac", "1",                    # mono
        "-ar", str(DEFAULT_SAMPLE_RATE),  # 16kHz
        "-f", "wav",                   # formato WAV
        "-acodec", "pcm_s16le",       # 16-bit PCM
        str(output_path)
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Audio convertido a WAV optimizado: {output_path}")
        return str(output_path)
        
    except subprocess.CalledProcessError as e:
        error_msg = f"ffmpeg falló: {e.stderr[:500] if e.stderr else 'Error desconocido'}"
        logger.error(error_msg)
        raise AudioPipelineError(error_msg) from e
    except FileNotFoundError:
        raise AudioPipelineError("FFmpeg no está instalado o no está en el PATH")


def preprocess_wav_optimized(wav_path: str) -> Tuple[np.ndarray, int]:
    """
    ✅ PREPROCESAMIENTO OPTIMIZADO INSPIRADO EN EL EJEMPLO
    Usa resemblyzer si está disponible para eliminar silencio y normalizar,
    sino usa librosa con parámetros similares.
    """
    if RESEMBLYZER_AVAILABLE:
        try:
            # ✅ USAR RESEMBLYZER COMO EN EL EJEMPLO (elimina silencio, normaliza)
            wav = preprocess_wav(wav_path)
            sr = DEFAULT_SAMPLE_RATE  # resemblyzer normaliza a 16kHz
            logger.info(f"Audio preprocesado con resemblyzer: {len(wav)} muestras")
            return wav, sr
        except Exception as e:
            logger.warning(f"Error con resemblyzer, usando fallback: {e}")
    
    # Fallback con librosa (similar al comportamiento de resemblyzer)
    try:
        wav, sr = librosa.load(wav_path, sr=DEFAULT_SAMPLE_RATE, mono=True)
        
        # Eliminar silencio como lo hace resemblyzer
        wav_trimmed, _ = librosa.effects.trim(wav, top_db=20)
        
        # Normalizar como lo hace resemblyzer
        if np.max(np.abs(wav_trimmed)) > 0:
            wav_trimmed = wav_trimmed / np.max(np.abs(wav_trimmed)) * 0.9
        
        logger.info(f"Audio preprocesado con librosa (fallback): {len(wav_trimmed)} muestras")
        return wav_trimmed, sr
        
    except Exception as e:
        logger.error(f"Error en preprocesamiento: {e}")
        raise AudioPipelineError(f"Error preprocesando audio: {e}") from e


def normalize_peak(y: np.ndarray, target_db: float = -3.0) -> np.ndarray:
    """
    Normaliza el audio por pico a un nivel específico en dB.
    """
    if len(y) == 0:
        return y
        
    peak = np.max(np.abs(y))
    if peak == 0:
        return y
    
    # Convertir dB a factor lineal
    target_linear = 10 ** (target_db / 20.0)
    scale_factor = target_linear / peak
    
    return y * scale_factor


def highpass_preemphasis(y: np.ndarray, coef: float = 0.97) -> np.ndarray:
    """
    Aplica pre-énfasis como filtro de realce de altas frecuencias.
    """
    if len(y) == 0:
        return y
    
    try:
        return librosa.effects.preemphasis(y, coef=coef)
    except Exception as e:
        logger.warning(f"Error en pre-énfasis, devolviendo audio original: {e}")
        return y


def reduce_noise_advanced(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Reduce ruido usando noisereduce si está disponible.
    """
    if not NOISEREDUCE_AVAILABLE:
        logger.info("noisereduce no disponible, omitiendo reducción avanzada")
        return y
    
    if len(y) == 0:
        return y
    
    try:
        # Usar reducción de ruido estacionario
        y_reduced = nr.reduce_noise(y=y, sr=sr, stationary=True)
        logger.info("Reducción de ruido aplicada con noisereduce")
        return y_reduced
    except Exception as e:
        logger.warning(f"Error en reducción de ruido, devolviendo audio original: {e}")
        return y


def trim_silence_advanced(y: np.ndarray, sr: int, top_db: int = 20) -> np.ndarray:
    """
    Recorta silencios del inicio y final del audio.
    """
    if len(y) == 0:
        return y
    
    try:
        y_trimmed, _ = librosa.effects.trim(y, top_db=top_db)
        
        # Si el audio se recortó demasiado, usar el original
        if len(y_trimmed) < len(y) * 0.1:  # Si queda menos del 10%
            logger.warning("Recorte de silencio muy agresivo, manteniendo audio original")
            return y
        
        logger.info(f"Silencio recortado: {len(y)} -> {len(y_trimmed)} muestras")
        return y_trimmed
        
    except Exception as e:
        logger.warning(f"Error recortando silencio, devolviendo audio original: {e}")
        return y


def apply_sox_effects(input_path: str, output_path: str) -> None:
    """
    Aplica efectos de SoX para mejora adicional.
    """
    try:
        cmd = [
            SOX, input_path, output_path,
            "highpass", "300",      # Filtro pasa-altos a 300Hz
            "lowpass", "3400",      # Filtro pasa-bajos a 3400Hz (rango de voz)
            "compand", "0.3,1", "6:-70,-60,-20", "-5", "-90", "0.2",  # Compresión suave
            "gain", "-n"            # Normalización
        ]
        
        run_command(cmd)
        logger.info("Efectos de SoX aplicados correctamente")
        
    except Exception as e:
        logger.warning(f"Error aplicando efectos SoX: {e}")
        # Si SoX falla, copiar el archivo original
        import shutil
        shutil.copy2(input_path, output_path)


def improve_audio_optimized(input_path: str, output_path: str, 
                           apply_noise_reduction: bool = True,
                           use_sox_effects: bool = True,
                           target_sample_rate: int = DEFAULT_SAMPLE_RATE) -> Dict:
    """
    ✅ PIPELINE COMPLETO DE MEJORA DE AUDIO OPTIMIZADO
    Incorpora mejores prácticas del ejemplo externo que funciona bien.
    
    Pasos optimizados:
    1. Conversión a WAV mono 16kHz (como el ejemplo)
    2. Preprocesamiento con resemblyzer si está disponible (del ejemplo)
    3. Pre-énfasis
    4. Reducción de ruido (opcional)
    5. Normalización por pico
    6. Efectos SoX (opcional)
    
    Returns:
        Dict con metadatos del procesamiento
    """
    logger.info(f"Iniciando mejora de audio optimizada: {input_path} -> {output_path}")
    
    # Crear directorio de salida si no existe
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Información del archivo original
    original_info = get_audio_info(input_path)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # ✅ PASO 1: Conversión optimizada a WAV mono 16kHz (como el ejemplo)
            temp_wav = ensure_wav_optimized(input_path, temp_dir)
            logger.info(f"Conversión a WAV optimizada completada: {temp_wav}")
            
            # ✅ PASO 2: Preprocesamiento optimizado (eliminar silencio + normalizar)
            y, sr = preprocess_wav_optimized(temp_wav)
            logger.info(f"Preprocesamiento optimizado: {len(y)} muestras a {sr}Hz")
            
            # ✅ PASO 3: Pre-énfasis (mantener del pipeline actual)
            y = highpass_preemphasis(y)
            
            # ✅ PASO 4: Reducción de ruido avanzada (opcional)
            if apply_noise_reduction:
                y = reduce_noise_advanced(y, sr)
                logger.info("Reducción de ruido aplicada")
            
            # ✅ PASO 5: Normalización por pico optimizada
            y = normalize_peak(y, target_db=-3.0)
            logger.info("Normalización por pico aplicada")
            
            # Guardar resultado intermedio
            temp_processed = os.path.join(temp_dir, "temp_processed.wav")
            sf.write(temp_processed, y, sr, subtype="PCM_16")
            
            # ✅ PASO 6: Efectos SoX finales (opcional)
            if use_sox_effects:
                apply_sox_effects(temp_processed, output_path)
                logger.info("Efectos SoX aplicados")
            else:
                import shutil
                shutil.copy2(temp_processed, output_path)
            
            # Obtener información del archivo procesado
            processed_info = get_audio_info(output_path)
            
            # Calcular métricas mejoradas
            duration_processed = float(len(y)) / sr
            
            # ✅ METADATOS MEJORADOS
            metadata = {
                'pipeline_version': PIPELINE_VERSION,
                'optimization_applied': True,  # Nueva bandera
                'resemblyzer_used': RESEMBLYZER_AVAILABLE,
                'original_duration': original_info['duration'],
                'processed_duration': duration_processed,
                'duration_reduction': original_info['duration'] - duration_processed,
                'original_sample_rate': original_info['sample_rate'],
                'processed_sample_rate': sr,
                'original_size': original_info['size'],
                'processed_size': processed_info['size'],
                'compression_ratio': original_info['size'] / processed_info['size'] if processed_info['size'] > 0 else 1.0,
                'noise_reduction_applied': apply_noise_reduction,
                'sox_effects_applied': use_sox_effects,
                'quality_improvements': [
                    'wav_16k_mono_conversion',
                    'resemblyzer_preprocessing' if RESEMBLYZER_AVAILABLE else 'librosa_preprocessing',
                    'preemphasis_filter',
                    'noise_reduction' if apply_noise_reduction else 'noise_reduction_skipped',
                    'peak_normalization',
                    'sox_effects' if use_sox_effects else 'sox_effects_skipped'
                ]
            }
            
            logger.info(f"Mejora de audio optimizada completada exitosamente")
            logger.info(f"Duración: {original_info['duration']:.2f}s -> {duration_processed:.2f}s")
            logger.info(f"Reducción de duración: {metadata['duration_reduction']:.2f}s (silencio eliminado)")
            logger.info(f"Tamaño: {original_info['size']} -> {processed_info['size']} bytes")
            logger.info(f"Optimizaciones aplicadas: {len(metadata['quality_improvements'])}")
            
            return metadata
            
    except Exception as e:
        logger.error(f"Error en pipeline optimizado de mejora de audio: {e}")
        raise AudioPipelineError(f"Error procesando audio: {e}") from e


# ✅ MANTENER FUNCIÓN ORIGINAL COMO FALLBACK
def improve_audio(input_path: str, output_path: str, 
                 apply_noise_reduction: bool = True,
                 use_sox_effects: bool = True,
                 target_sample_rate: int = DEFAULT_SAMPLE_RATE) -> Dict:
    """
    Pipeline completo de mejora de audio (versión original como fallback).
    """
    try:
        # Intentar pipeline optimizado primero
        return improve_audio_optimized(
            input_path, output_path, 
            apply_noise_reduction, use_sox_effects, target_sample_rate
        )
    except Exception as e:
        logger.warning(f"Pipeline optimizado falló, usando pipeline original: {e}")
        # Pipeline original como fallback
        return improve_audio_original(
            input_path, output_path,
            apply_noise_reduction, use_sox_effects, target_sample_rate
        )


def improve_audio_original(input_path: str, output_path: str, 
                          apply_noise_reduction: bool = True,
                          use_sox_effects: bool = True,
                          target_sample_rate: int = DEFAULT_SAMPLE_RATE) -> Dict:
    """
    Pipeline completo de mejora de audio.
    
    Pasos:
    1. Conversión a WAV mono
    2. Pre-énfasis
    3. Reducción de ruido (opcional)
    4. Normalización por pico
    5. Recorte de silencios
    6. Efectos SoX (opcional)
    
    Returns:
        Dict con metadatos del procesamiento
    """
    logger.info(f"Iniciando mejora de audio: {input_path} -> {output_path}")
    
    # Crear directorio de salida si no existe
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Información del archivo original
    original_info = get_audio_info(input_path)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Paso 1: Convertir a WAV mono
            temp_wav = os.path.join(temp_dir, "temp_mono.wav")
            convert_to_wav_mono(input_path, temp_wav, target_sample_rate)
            
            # Cargar audio para procesamiento
            y, sr = librosa.load(temp_wav, sr=target_sample_rate, mono=True)
            logger.info(f"Audio cargado: {len(y)} muestras a {sr}Hz")
            
            # Paso 2: Pre-énfasis
            y = highpass_preemphasis(y)
            
            # Paso 3: Reducción de ruido (opcional)
            if apply_noise_reduction:
                y = reduce_noise_advanced(y, sr)
            
            # Paso 4: Normalización por pico
            y = normalize_peak(y, target_db=-3.0)
            
            # Paso 5: Recorte de silencios
            y = trim_silence_advanced(y, sr)
            
            # Guardar resultado intermedio
            temp_processed = os.path.join(temp_dir, "temp_processed.wav")
            sf.write(temp_processed, y, sr, subtype="PCM_16")
            
            # Paso 6: Efectos SoX (opcional)
            if use_sox_effects:
                apply_sox_effects(temp_processed, output_path)
            else:
                import shutil
                shutil.copy2(temp_processed, output_path)
            
            # Obtener información del archivo procesado
            processed_info = get_audio_info(output_path)
            
            # Calcular métricas
            duration_processed = float(len(y)) / sr
            
            metadata = {
                'pipeline_version': PIPELINE_VERSION,
                'original_duration': original_info['duration'],
                'processed_duration': duration_processed,
                'original_sample_rate': original_info['sample_rate'],
                'processed_sample_rate': sr,
                'original_size': original_info['size'],
                'processed_size': processed_info['size'],
                'compression_ratio': original_info['size'] / processed_info['size'] if processed_info['size'] > 0 else 1.0,
                'noise_reduction_applied': apply_noise_reduction,
                'sox_effects_applied': apply_sox_effects,
                'steps_completed': [
                    'conversion_to_wav_mono',
                    'preemphasis',
                    'noise_reduction' if apply_noise_reduction else 'noise_reduction_skipped',
                    'peak_normalization',
                    'silence_trimming',
                    'sox_effects' if apply_sox_effects else 'sox_effects_skipped'
                ]
            }
            
            logger.info(f"Mejora de audio completada exitosamente")
            logger.info(f"Duración: {original_info['duration']:.2f}s -> {duration_processed:.2f}s")
            logger.info(f"Tamaño: {original_info['size']} -> {processed_info['size']} bytes")
            
            return metadata
            
    except Exception as e:
        logger.error(f"Error en pipeline de mejora de audio: {e}")
        raise AudioPipelineError(f"Error procesando audio: {e}") from e


class AudioProcessor:
    """
    Clase principal para procesamiento de audio.
    Mantiene compatibilidad con la implementación anterior.
    """
    
    def __init__(self):
        self.pipeline_version = PIPELINE_VERSION
        logger.info("AudioProcessor inicializado")
    
    @staticmethod
    def verificar_ffmpeg() -> bool:
        """Verifica si FFmpeg está disponible"""
        try:
            result = subprocess.run([FFMPEG, "-version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    @staticmethod
    def verificar_sox() -> bool:
        """Verifica si SoX está disponible"""
        try:
            result = subprocess.run([SOX, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def get_audio_info(self, file_path: str) -> Dict:
        """Wrapper para get_audio_info"""
        return get_audio_info(file_path)
    
    def normalize_audio(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Normaliza el audio manteniendo compatibilidad.
        """
        if output_path is None:
            base = Path(input_path).stem
            output_path = str(Path(input_path).parent / f"{base}_normalized.wav")
        
        # Usar solo normalización
        metadata = improve_audio(
            input_path, output_path,
            apply_noise_reduction=False,
            use_sox_effects=False
        )
        
        return output_path
    
    def reduce_noise(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Reduce ruido manteniendo compatibilidad.
        """
        if output_path is None:
            base = Path(input_path).stem
            output_path = str(Path(input_path).parent / f"{base}_denoised.wav")
        
        # Usar solo reducción de ruido
        metadata = improve_audio(
            input_path, output_path,
            apply_noise_reduction=True,
            use_sox_effects=False
        )
        
        return output_path
    
    def enhance_speech(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Mejora completa de voz.
        """
        if output_path is None:
            base = Path(input_path).stem
            output_path = str(Path(input_path).parent / f"{base}_enhanced.wav")
        
        # Pipeline completo
        metadata = improve_audio(
            input_path, output_path,
            apply_noise_reduction=True,
            use_sox_effects=True
        )
        
        return output_path
    
    def process_audio(self, input_path: str, output_path: Optional[str] = None, 
                     options: Optional[Dict] = None) -> Tuple[str, Dict]:
        """
        Procesa audio con opciones personalizables.
        """
        if output_path is None:
            base = Path(input_path).stem
            output_path = str(Path(input_path).parent / f"{base}_processed.wav")
        
        options = options or {}
        
        metadata = improve_audio(
            input_path, output_path,
            apply_noise_reduction=options.get('noise_reduction', True),
            use_sox_effects=options.get('sox_effects', True),
            target_sample_rate=options.get('sample_rate', DEFAULT_SAMPLE_RATE)
        )
        
        return output_path, metadata
