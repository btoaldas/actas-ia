"""
Helper para diarización de hablantes con pyannote.audio
Maneja identificación, clustering y separación de hablantes
"""
import torch
import numpy as np
import logging
from typing import Dict, Any, List, Optional, Tuple
import os
import tempfile

try:
    from pyannote.audio import Pipeline
    from pyannote.core import Annotation, Segment
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False

logger = logging.getLogger(__name__)


class PyannoteProcessor:
    """Procesador de diarización usando pyannote.audio"""
    
    def __init__(self):
        if not PYANNOTE_AVAILABLE:
            logger.warning("pyannote.audio no está disponible. Funcionalidad limitada.")
            
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline_cargado = False
        
    def cargar_pipeline(self, usar_gpu: bool = True) -> bool:
        """
        Carga el pipeline de diarización de pyannote
        
        Args:
            usar_gpu: Si usar GPU cuando esté disponible
            
        Returns:
            bool: True si se cargó exitosamente
        """
        try:
            if not usar_gpu:
                self.device = "cpu"
                
            if self.pipeline_cargado and self.pipeline is not None:
                logger.info("Pipeline de pyannote ya está cargado")
                return True
                
            logger.info(f"Cargando pipeline de pyannote en {self.device}")
            
            # Cargar pipeline pre-entrenado para diarización
            # Nota: Requiere token de Hugging Face para algunos modelos
            try:
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=os.getenv('HUGGINGFACE_TOKEN')
                )
            except:
                # Fallback a modelo más básico si no hay token
                logger.warning("No se pudo cargar modelo premium, usando básico")
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization@2022.07"
                )
            
            # Configurar device
            if hasattr(self.pipeline, 'to'):
                self.pipeline = self.pipeline.to(torch.device(self.device))
                
            self.pipeline_cargado = True
            logger.info("Pipeline de pyannote cargado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando pipeline de pyannote: {str(e)}")
            return False
    
    def diarizar_audio(self, 
                      archivo_audio: str,
                      configuracion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza diarización de hablantes en un archivo de audio
        
        Args:
            archivo_audio: Ruta al archivo de audio
            configuracion: Diccionario con configuración
            
        Returns:
            Dict con resultado de diarización
        """
        if not PYANNOTE_AVAILABLE:
            logger.warning("pyannote.audio no disponible, retornando resultado por defecto")
            return {
                'exito': True,
                'hablantes': {'speaker_0': 'Hablante Único'},
                'segmentos_hablantes': [],
                'num_hablantes': 1,
                'estadisticas': {},
                'mensaje': 'pyannote.audio no disponible - usando fallback'
            }
            
        try:
            # Extraer configuración
            usar_gpu = configuracion.get('usar_gpu', True)
            min_hablantes = configuracion.get('min_hablantes', 1)
            max_hablantes = configuracion.get('max_hablantes', 8)
            umbral_clustering = configuracion.get('umbral_clustering', 0.7)
            
            # Cargar pipeline si es necesario
            if not self.cargar_pipeline(usar_gpu):
                raise Exception("No se pudo cargar el pipeline de pyannote")
            
            # Verificar que el archivo existe
            if not os.path.exists(archivo_audio):
                raise FileNotFoundError(f"Archivo de audio no encontrado: {archivo_audio}")
            
            logger.info(f"Iniciando diarización de {archivo_audio}")
            
            # Configurar parámetros del pipeline
            if hasattr(self.pipeline, '_segmentation'):
                # Configurar parámetros de segmentación
                if hasattr(self.pipeline._segmentation, 'instantiate'):
                    self.pipeline._segmentation.instantiate({
                        'min_duration_on': 0.5,
                        'min_duration_off': 0.1
                    })
            
            # Configurar clustering
            if hasattr(self.pipeline, '_clustering'):
                self.pipeline._clustering.instantiate({
                    'method': 'centroid',
                    'min_cluster_size': min_hablantes,
                    'max_num_speakers': max_hablantes,
                    'threshold': umbral_clustering
                })
            
            # Ejecutar diarización
            diarizacion = self.pipeline(archivo_audio)
            
            # Procesar resultado
            resultado_procesado = self._procesar_resultado_diarizacion(diarizacion, configuracion)
            
            logger.info(f"Diarización completada. {resultado_procesado['num_hablantes']} hablantes detectados")
            
            return {
                'exito': True,
                'hablantes': resultado_procesado['hablantes'],
                'segmentos_hablantes': resultado_procesado['segmentos'],
                'num_hablantes': resultado_procesado['num_hablantes'],
                'duracion_total': resultado_procesado['duracion_total'],
                'estadisticas': resultado_procesado['estadisticas'],
                'configuracion_usada': configuracion,
                'device_usado': self.device
            }
            
        except Exception as e:
            logger.error(f"Error en diarización: {str(e)}")
            return {
                'exito': False,
                'error': str(e),
                'configuracion_usada': configuracion
            }
    
    def _procesar_resultado_diarizacion(self, 
                                       diarizacion: Annotation,
                                       configuracion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa el resultado raw de pyannote para formato estándar
        """
        hablantes = set()
        segmentos = []
        
        # Procesar cada segmento
        for segmento, track, speaker in diarizacion.itertracks(yield_label=True):
            hablantes.add(speaker)
            
            segmento_procesado = {
                'inicio': segmento.start,
                'fin': segmento.end,
                'duracion': segmento.duration,
                'hablante': speaker,
                'track': track,
                'confianza': 1.0  # pyannote no siempre provee confianza explícita
            }
            segmentos.append(segmento_procesado)
        
        # Ordenar segmentos por tiempo
        segmentos.sort(key=lambda x: x['inicio'])
        
        # Calcular estadísticas
        estadisticas = self._calcular_estadisticas_hablantes(segmentos, hablantes)
        
        # Asignar nombres más amigables a los hablantes
        hablantes_nombrados = self._asignar_nombres_hablantes(list(hablantes))
        
        # Actualizar segmentos con nombres amigables
        for segmento in segmentos:
            segmento['hablante_nombre'] = hablantes_nombrados.get(
                segmento['hablante'], 
                f"Hablante {segmento['hablante']}"
            )
        
        duracion_total = max(seg['fin'] for seg in segmentos) if segmentos else 0.0
        
        return {
            'hablantes': hablantes_nombrados,
            'segmentos': segmentos,
            'num_hablantes': len(hablantes),
            'duracion_total': duracion_total,
            'estadisticas': estadisticas
        }
    
    def _calcular_estadisticas_hablantes(self, 
                                        segmentos: List[Dict], 
                                        hablantes: set) -> Dict[str, Any]:
        """
        Calcula estadísticas de participación de cada hablante
        """
        estadisticas = {}
        duracion_total = sum(seg['duracion'] for seg in segmentos)
        
        for hablante in hablantes:
            segmentos_hablante = [seg for seg in segmentos if seg['hablante'] == hablante]
            duracion_hablante = sum(seg['duracion'] for seg in segmentos_hablante)
            
            estadisticas[hablante] = {
                'duracion_total': duracion_hablante,
                'porcentaje_participacion': (duracion_hablante / duracion_total * 100) if duracion_total > 0 else 0,
                'num_intervenciones': len(segmentos_hablante),
                'duracion_promedio_intervencion': duracion_hablante / len(segmentos_hablante) if segmentos_hablante else 0
            }
        
        return estadisticas
    
    def _asignar_nombres_hablantes(self, hablantes: List[str]) -> Dict[str, str]:
        """
        Asigna nombres amigables a los hablantes detectados
        """
        nombres_municipales = [
            "Alcalde/sa", "Vicealcalde/sa", "Concejal 1", "Concejal 2", "Concejal 3",
            "Secretario/a", "Funcionario 1", "Funcionario 2", "Ciudadano 1", "Ciudadano 2"
        ]
        
        hablantes_nombrados = {}
        for i, hablante in enumerate(sorted(hablantes)):
            if i < len(nombres_municipales):
                hablantes_nombrados[hablante] = nombres_municipales[i]
            else:
                hablantes_nombrados[hablante] = f"Participante {i + 1}"
        
        return hablantes_nombrados
    
    def combinar_transcripcion_diarizacion(self,
                                         transcripcion: Dict[str, Any],
                                         diarizacion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina resultados de transcripción y diarización
        """
        try:
            segmentos_transcritos = transcripcion.get('segmentos', [])
            segmentos_hablantes = diarizacion.get('segmentos_hablantes', [])
            
            if not segmentos_transcritos or not segmentos_hablantes:
                logger.warning("No hay segmentos para combinar")
                return {'exito': False, 'error': 'No hay segmentos para combinar'}
            
            # Combinar transcripción con diarización
            segmentos_combinados = []
            
            for seg_texto in segmentos_transcritos:
                inicio_texto = seg_texto['inicio']
                fin_texto = seg_texto['fin']
                texto = seg_texto['texto']
                
                # Encontrar hablante que más se solapa con este segmento
                hablante_principal = self._encontrar_hablante_principal(
                    inicio_texto, fin_texto, segmentos_hablantes
                )
                
                segmento_combinado = {
                    'inicio': inicio_texto,
                    'fin': fin_texto,
                    'duracion': fin_texto - inicio_texto,
                    'texto': texto,
                    'hablante': hablante_principal.get('hablante', 'Desconocido'),
                    'hablante_nombre': hablante_principal.get('hablante_nombre', 'Desconocido'),
                    'confianza_texto': seg_texto.get('confianza', 0.0),
                    'confianza_hablante': hablante_principal.get('confianza', 0.0),
                    'id_segmento': seg_texto.get('id', len(segmentos_combinados))
                }
                
                segmentos_combinados.append(segmento_combinado)
            
            # Generar transcripción formateada
            transcripcion_formateada = self._formatear_transcripcion_completa(segmentos_combinados)
            
            return {
                'exito': True,
                'segmentos_combinados': segmentos_combinados,
                'transcripcion_formateada': transcripcion_formateada,
                'hablantes': diarizacion.get('hablantes', {}),
                'estadisticas': diarizacion.get('estadisticas', {}),
                'num_hablantes': diarizacion.get('num_hablantes', 0),
                'duracion_total': max(seg['fin'] for seg in segmentos_combinados) if segmentos_combinados else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error combinando transcripción y diarización: {str(e)}")
            return {'exito': False, 'error': str(e)}
    
    def _encontrar_hablante_principal(self, 
                                     inicio: float, 
                                     fin: float, 
                                     segmentos_hablantes: List[Dict]) -> Dict[str, Any]:
        """
        Encuentra el hablante que más se solapa con un segmento de tiempo
        """
        mejor_solapamiento = 0.0
        hablante_principal = {'hablante': 'Desconocido', 'hablante_nombre': 'Desconocido', 'confianza': 0.0}
        
        for seg_hablante in segmentos_hablantes:
            # Calcular solapamiento
            inicio_solape = max(inicio, seg_hablante['inicio'])
            fin_solape = min(fin, seg_hablante['fin'])
            
            if fin_solape > inicio_solape:  # Hay solapamiento
                duracion_solape = fin_solape - inicio_solape
                porcentaje_solape = duracion_solape / (fin - inicio)
                
                if porcentaje_solape > mejor_solapamiento:
                    mejor_solapamiento = porcentaje_solape
                    hablante_principal = {
                        'hablante': seg_hablante['hablante'],
                        'hablante_nombre': seg_hablante.get('hablante_nombre', 'Desconocido'),
                        'confianza': seg_hablante.get('confianza', mejor_solapamiento)
                    }
        
        return hablante_principal
    
    def _formatear_transcripcion_completa(self, segmentos: List[Dict]) -> str:
        """
        Formatea la transcripción completa con hablantes identificados
        """
        lineas = []
        hablante_actual = None
        
        for segmento in segmentos:
            hablante = segmento.get('hablante_nombre', 'Desconocido')
            texto = segmento.get('texto', '').strip()
            inicio = segmento.get('inicio', 0)
            
            if texto:
                # Formatear timestamp
                minutos = int(inicio // 60)
                segundos = int(inicio % 60)
                timestamp = f"[{minutos:02d}:{segundos:02d}]"
                
                if hablante != hablante_actual:
                    lineas.append(f"\n{timestamp} {hablante}:")
                    hablante_actual = hablante
                
                lineas.append(f"{texto}")
        
        return " ".join(lineas).strip()
    
    def limpiar_pipeline(self):
        """Libera la memoria del pipeline cargado"""
        try:
            if self.pipeline is not None:
                del self.pipeline
                self.pipeline = None
                self.pipeline_cargado = False
                
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
                logger.info("Pipeline de pyannote liberado de memoria")
                
        except Exception as e:
            logger.error(f"Error liberando pipeline de pyannote: {str(e)}")


def obtener_configuraciones_diarizacion() -> List[Dict[str, Any]]:
    """
    Retorna configuraciones predefinidas para diarización
    """
    return [
        {
            'nombre': 'Reunión Pequeña',
            'descripcion': 'Para reuniones de 2-4 personas',
            'min_hablantes': 2,
            'max_hablantes': 4,
            'umbral_clustering': 0.8,
            'adecuado_para': 'Reuniones íntimas, entrevistas'
        },
        {
            'nombre': 'Reunión Mediana',
            'descripcion': 'Para reuniones de 4-8 personas',
            'min_hablantes': 3,
            'max_hablantes': 8,
            'umbral_clustering': 0.7,
            'adecuado_para': 'Concejos municipales, comisiones'
        },
        {
            'nombre': 'Reunión Grande',
            'descripcion': 'Para reuniones de más de 8 personas',
            'min_hablantes': 5,
            'max_hablantes': 15,
            'umbral_clustering': 0.6,
            'adecuado_para': 'Asambleas, audiencias públicas'
        }
    ]
