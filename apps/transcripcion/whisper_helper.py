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
        Transcribe un archivo de audio usando Whisper
        
        Args:
            archivo_audio: Ruta al archivo de audio
            configuracion: Diccionario con configuración
            
        Returns:
            Dict con resultado de transcripción
        """
        if not WHISPER_AVAILABLE:
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
                'mensaje': 'Whisper no disponible - usando simulación'
            }
            
        try:
            # Extraer configuración
            modelo_nombre = configuracion.get('modelo_whisper', 'base')
            idioma = configuracion.get('idioma_principal', 'es')
            temperatura = configuracion.get('temperatura', 0.0)
            usar_gpu = configuracion.get('usar_gpu', True)
            
            # Cargar modelo si es necesario
            if not self.cargar_modelo(modelo_nombre, usar_gpu):
                raise Exception(f"No se pudo cargar el modelo {modelo_nombre}")
            
            # Verificar que el archivo existe
            if not os.path.exists(archivo_audio):
                raise FileNotFoundError(f"Archivo de audio no encontrado: {archivo_audio}")
            
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
        Procesa el resultado raw de Whisper para formato estándar
        """
        segmentos_procesados = []
        texto_completo = resultado.get('text', '').strip()
        
        for segmento in resultado.get('segments', []):
            segmento_procesado = {
                'id': segmento.get('id', 0),
                'inicio': segmento.get('start', 0.0),
                'fin': segmento.get('end', 0.0),
                'texto': segmento.get('text', '').strip(),
                'confianza': segmento.get('avg_logprob', 0.0),
                'tokens': segmento.get('tokens', []),
                'temperatura': segmento.get('temperature', 0.0),
                'no_speech_prob': segmento.get('no_speech_prob', 0.0)
            }
            segmentos_procesados.append(segmento_procesado)
        
        duracion_total = 0.0
        if segmentos_procesados:
            duracion_total = max(seg['fin'] for seg in segmentos_procesados)
        
        return {
            'texto_completo': texto_completo,
            'segmentos': segmentos_procesados,
            'duracion_total': duracion_total
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
