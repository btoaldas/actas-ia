"""
Helper para procesamiento de audio con Whisper
Maneja transcripción de texto con diferentes modelos y configuraciones
"""
import os
import logging
from typing import Dict, Any, Optional, List
import tempfile

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)


class WhisperProcessor:
    """Procesador de transcripción usando Whisper de OpenAI"""
    
    def __init__(self):
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper no está disponible. Funcionalidad limitada.")
            
        self.modelo = None
        self.device = "cuda" if WHISPER_AVAILABLE and torch.cuda.is_available() else "cpu"
        self.modelo_cargado = None
        
    def get_model_info(self) -> Dict[str, Any]:
        """
        Obtiene información detallada del modelo cargado
        
        Returns:
            Dict con metadatos del modelo
        """
        if not self.modelo:
            return {
                'modelo': 'no_cargado',
                'device': self.device,
                'version': 'N/A',
                'size_mb': 'N/A',
                'hash': 'N/A',
                'path': 'N/A',
                'parametros_soportados': ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
            }
        
        try:
            # Mapeo de tamaños aproximados por modelo
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
                'version': getattr(self.modelo, 'version', 'whisper-1.0'),
                'size_mb': model_sizes.get(self.modelo_cargado, 'unknown'),
                'hash': getattr(self.modelo, 'sha256', 'N/A'),
                'path': getattr(self.modelo, 'path', 'cached'),
                'parametros_soportados': ['temperature', 'language', 'task', 'word_timestamps'],
                'cuda_available': torch.cuda.is_available() if WHISPER_AVAILABLE else False,
                'dims': getattr(self.modelo, 'dims', {}),
                'is_multilingual': getattr(self.modelo, 'is_multilingual', True)
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
                def transcribir_audio(self, 
                                     archivo_audio: str,
                                     configuracion: Dict[str, Any]) -> Dict[str, Any]:
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
        Transcribe un archivo de audio usando Whisper
        
        Args:
            archivo_audio: Ruta al archivo de audio
            configuracion: Diccionario con configuración
            
        Returns:
            Dict con resultado de transcripción
        """
                            'palabra_por_palabra': configuracion.get('palabra_por_palabra', False),
                            'mejora_audio': configuracion.get('mejora_audio', False),
                            'metadatos_modelo': {
                                'modelo': 'simulado',
                                'device': 'cpu',
                                'version': 'N/A',
                                'size': 'N/A',
                                'hash': 'N/A',
                                'ruta': 'N/A',
                                'parametros': configuracion
                            }
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper no disponible, retornando transcripción simulada")
            return {
                'exito': True,
                'texto_completo': 'Transcripción de ejemplo porque Whisper no está disponible.',
                'modelo_usado': 'simulado',
                'segmentos': [
                        palabra_por_palabra = configuracion.get('palabra_por_palabra', False)
                        mejora_audio = configuracion.get('mejora_audio', False)
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
                'mensaje': 'Whisper no disponible - usando simulación'
            }
                            # Si palabra por palabra está activo, ajustar parámetros
                            "word_timestamps": palabra_por_palabra
            
        try:
            # Extraer configuración
            modelo_nombre = configuracion.get('modelo_whisper', 'base')
            idioma = configuracion.get('idioma_principal', 'es')
            temperatura = configuracion.get('temperatura', 0.0)
                        return {
                            'exito': True,
                            'texto_completo': transcripcion_procesada['texto_completo'],
                            'segmentos': transcripcion_procesada['segmentos'],
                            'idioma_detectado': resultado.get('language', idioma),
                            'duracion_total': transcripcion_procesada['duracion_total'],
                            'configuracion_usada': configuracion,
                            'modelo_usado': modelo_nombre,
                            'device_usado': self.device,
                            'palabra_por_palabra': palabra_por_palabra,
                            'mejora_audio': mejora_audio,
                            'metadatos_modelo': {
                                'modelo': modelo_nombre,
                                'device': self.device,
                                'version': getattr(self.modelo, 'version', 'unknown'),
                                'size': getattr(self.modelo, 'size', 'unknown'),
                                'hash': getattr(self.modelo, 'sha256', 'unknown'),
                                'ruta': getattr(self.modelo, 'path', 'unknown'),
                                'parametros': configuracion
                            }
                        }
            logger.info(f"Iniciando transcripción de {archivo_audio}")
            
            # Configurar opciones de transcripción
            opciones = {
                "language": idioma,
                "temperature": temperatura,
                "task": "transcribe",
                "verbose": True,
            }
            
            # Ejecutar transcripción
            resultado = self.modelo.transcribe(archivo_audio, **opciones)
            
            # Procesar resultado
            transcripcion_procesada = self._procesar_resultado_whisper(resultado)
            
            logger.info(f"Transcripción completada. {len(transcripcion_procesada['segmentos'])} segmentos")
            
            return {
                'exito': True,
                'texto_completo': transcripcion_procesada['texto_completo'],
                'segmentos': transcripcion_procesada['segmentos'],
                'idioma_detectado': resultado.get('language', idioma),
                'duracion_total': transcripcion_procesada['duracion_total'],
                'configuracion_usada': configuracion,
                'modelo_usado': modelo_nombre,
                'device_usado': self.device
            }
            
        except Exception as e:
            logger.error(f"Error en transcripción: {str(e)}")
            return {
                'exito': False,
                'error': str(e),
                'configuracion_usada': configuracion
            }
    
    def _procesar_resultado_whisper(self, resultado: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa el resultado raw de Whisper para formato estándar con información mejorada
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
            
            # Convertir avg_logprob a confianza (0-1)
            avg_logprob = segmento.get('avg_logprob', 0.0)
            # avg_logprob típicamente está entre -1 y 0, convertir a 0-1
            confidence = max(0.0, min(1.0, (avg_logprob + 1.0))) if avg_logprob != 0 else 0.8
            
            segmento_procesado = {
                'id': segmento.get('id', 0),
                'inicio': inicio,
                'fin': fin,
                'start': inicio,  # Alias para compatibilidad
                'end': fin,       # Alias para compatibilidad
                'start_time_str': formatear_tiempo_str(inicio),
                'end_time_str': formatear_tiempo_str(fin),
                'texto': segmento.get('text', '').strip(),
                'text': segmento.get('text', '').strip(),  # Alias para compatibilidad
                'confianza': confidence,
                'confidence': confidence,  # Alias para compatibilidad
                'tokens': segmento.get('tokens', []),
                'temperatura': segmento.get('temperature', 0.0),
                'no_speech_prob': segmento.get('no_speech_prob', 0.0),
                'words': segmento.get('words', [])  # Palabras individuales si están disponibles
            }
            segmentos_procesados.append(segmento_procesado)
        
        duracion_total = 0.0
        if segmentos_procesados:
            duracion_total = max(seg['fin'] for seg in segmentos_procesados)
        
        # Calcular métricas adicionales
        total_words = len(texto_completo.split()) if texto_completo else 0
        avg_confidence = sum(seg['confianza'] for seg in segmentos_procesados) / len(segmentos_procesados) if segmentos_procesados else 0.0
        low_confidence_segments = sum(1 for seg in segmentos_procesados if seg['confianza'] < 0.5)
        low_confidence_ratio = low_confidence_segments / len(segmentos_procesados) if segmentos_procesados else 0.0
        
        return {
            'texto_completo': texto_completo,
            'segmentos': segmentos_procesados,
            'duracion_total': duracion_total,
            'metricas': {
                'total_words': total_words,
                'avg_confidence': avg_confidence,
                'low_confidence_ratio': low_confidence_ratio,
                'num_segments': len(segmentos_procesados)
            },
            'language': resultado.get('language', 'es'),
            'language_probability': resultado.get('language_probability', 1.0)
        }
    
    def limpiar_modelo(self):
        """Libera la memoria del modelo cargado"""
        try:
            if self.modelo is not None:
                del self.modelo
                self.modelo = None
                self.modelo_cargado = None
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
                logger.info("Modelo Whisper liberado de memoria")
                
        except Exception as e:
            logger.error(f"Error liberando modelo Whisper: {str(e)}")


def obtener_modelos_disponibles() -> List[Dict[str, Any]]:
    """
    Retorna lista de modelos Whisper disponibles con sus características
    """
    return [
        {
            'nombre': 'tiny',
            'tamaño': '39 MB',
            'descripcion': 'Muy rápido, menor precisión',
            'velocidad': 'Muy rápida',
            'calidad': 'Básica'
        },
        {
            'nombre': 'base', 
            'tamaño': '74 MB',
            'descripcion': 'Equilibrado velocidad/precisión',
            'velocidad': 'Rápida',
            'calidad': 'Buena'
        },
        {
            'nombre': 'small',
            'tamaño': '244 MB', 
            'descripcion': 'Buena precisión',
            'velocidad': 'Media',
            'calidad': 'Muy buena'
        },
        {
            'nombre': 'medium',
            'tamaño': '769 MB',
            'descripcion': 'Muy buena precisión',
            'velocidad': 'Lenta',
            'calidad': 'Excelente'
        },
        {
            'nombre': 'large',
            'tamaño': '1550 MB',
            'descripcion': 'Excelente precisión', 
            'velocidad': 'Muy lenta',
            'calidad': 'Superior'
        },
        {
            'nombre': 'large-v2',
            'tamaño': '1550 MB',
            'descripcion': 'Mejor para múltiples idiomas',
            'velocidad': 'Muy lenta', 
            'calidad': 'Superior+'
        },
        {
            'nombre': 'large-v3',
            'tamaño': '1550 MB',
            'descripcion': 'Estado del arte',
            'velocidad': 'Muy lenta',
            'calidad': 'Máxima'
        }
    ]
