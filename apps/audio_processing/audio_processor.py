"""
Procesamiento de audio en background para mejora y normalización
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Clase para procesar y mejorar archivos de audio"""
    
    def __init__(self):
        self.supported_formats = ['.mp3', '.wav', '.m4a', '.mp4', '.webm', '.ogg']
        
    def normalize_audio(self, input_path: str, output_path: str = None) -> str:
        """
        Normaliza un archivo de audio usando FFmpeg
        
        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida (opcional)
            
        Returns:
            Ruta del archivo normalizado
        """
        if output_path is None:
            name, ext = os.path.splitext(input_path)
            output_path = f"{name}_normalized{ext}"
            
        try:
            # Comando FFmpeg para normalización
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', 'loudnorm=I=-16:LRA=11:TP=-1.5',  # Normalización de volumen
                '-ar', '16000',  # Sample rate 16kHz (óptimo para transcripción)
                '-ac', '1',      # Mono (reduce tamaño y mejora transcripción)
                '-y',            # Sobrescribir archivo de salida
                output_path
            ]
            
            logger.info(f"Normalizando audio: {input_path} -> {output_path}")
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            if result.returncode == 0:
                logger.info(f"Audio normalizado exitosamente: {output_path}")
                return output_path
            else:
                raise Exception(f"Error en FFmpeg: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error normalizando audio: {e.stderr}")
            raise Exception(f"Error en normalización: {e.stderr}")
        except FileNotFoundError:
            raise Exception("FFmpeg no está instalado. Instalar con: apt-get install ffmpeg")
            
    def reduce_noise(self, input_path: str, output_path: str = None) -> str:
        """
        Reduce el ruido de fondo del audio
        
        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida (opcional)
            
        Returns:
            Ruta del archivo con ruido reducido
        """
        if output_path is None:
            name, ext = os.path.splitext(input_path)
            output_path = f"{name}_denoised{ext}"
            
        try:
            # Primer paso: Crear perfil de ruido
            noise_profile = tempfile.mktemp(suffix='.prof')
            
            # Analizar los primeros 0.5 segundos para obtener perfil de ruido
            cmd_profile = [
                'sox', input_path, '-n', 'trim', '0', '0.5',
                'noiseprof', noise_profile
            ]
            
            subprocess.run(cmd_profile, check=True, capture_output=True)
            
            # Segundo paso: Aplicar reducción de ruido
            cmd_denoise = [
                'sox', input_path, output_path,
                'noisered', noise_profile, '0.21'
            ]
            
            result = subprocess.run(
                cmd_denoise, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            # Limpiar archivo temporal
            os.unlink(noise_profile)
            
            logger.info(f"Ruido reducido exitosamente: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error reduciendo ruido: {e.stderr}")
            raise Exception(f"Error en reducción de ruido: {e.stderr}")
        except FileNotFoundError:
            raise Exception("SoX no está instalado. Instalar con: apt-get install sox")
            
    def enhance_speech(self, input_path: str, output_path: str = None) -> str:
        """
        Mejora la claridad del habla
        
        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta del archivo de salida (opcional)
            
        Returns:
            Ruta del archivo con habla mejorada
        """
        if output_path is None:
            name, ext = os.path.splitext(input_path)
            output_path = f"{name}_enhanced{ext}"
            
        try:
            # Filtros para mejorar claridad del habla
            filters = [
                'highpass=f=80',     # Eliminar frecuencias muy bajas (ruido)
                'lowpass=f=8000',    # Eliminar frecuencias muy altas (silbidos)
                'compand=0.02,0.05:-60/-60,-30/-15,-20/-10,-5/-5,0/-3:6:0:-3:0.2',  # Compresión
                'equalizer=f=1000:t=q:w=2:g=2',    # Realzar frecuencias de voz (1kHz)
                'equalizer=f=3000:t=q:w=2:g=1.5',  # Realzar frecuencias de voz (3kHz)
            ]
            
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-af', ','.join(filters),
                '-y',
                output_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            logger.info(f"Habla mejorada exitosamente: {output_path}")
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error mejorando habla: {e.stderr}")
            raise Exception(f"Error en mejora de habla: {e.stderr}")
            
    def get_audio_info(self, input_path: str) -> Dict[str, Any]:
        """
        Obtiene información del archivo de audio
        
        Args:
            input_path: Ruta del archivo de audio
            
        Returns:
            Diccionario con información del audio
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                input_path
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            
            import json
            data = json.loads(result.stdout)
            
            # Extraer información relevante
            format_info = data.get('format', {})
            audio_stream = None
            
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                raise Exception("No se encontró stream de audio")
                
            info = {
                'duracion': float(format_info.get('duration', 0)),
                'tamano_bytes': int(format_info.get('size', 0)),
                'formato': format_info.get('format_name', ''),
                'bitrate': int(format_info.get('bit_rate', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'canales': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', ''),
            }
            
            return info
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error obteniendo información de audio: {e.stderr}")
            raise Exception(f"Error obteniendo información: {e.stderr}")
        except FileNotFoundError:
            raise Exception("FFprobe no está instalado. Instalar con: apt-get install ffmpeg")
            
    def process_full_pipeline(self, input_path: str, output_dir: str = None) -> Dict[str, str]:
        """
        Ejecuta el pipeline completo de procesamiento de audio
        
        Args:
            input_path: Ruta del archivo de entrada
            output_dir: Directorio de salida (opcional)
            
        Returns:
            Diccionario con las rutas de los archivos procesados
        """
        if output_dir is None:
            output_dir = os.path.dirname(input_path)
            
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        try:
            logger.info(f"Iniciando procesamiento completo: {input_path}")
            
            # 1. Obtener información original
            original_info = self.get_audio_info(input_path)
            
            # 2. Normalización
            normalized_path = os.path.join(output_dir, f"{base_name}_normalized.wav")
            self.normalize_audio(input_path, normalized_path)
            
            # 3. Reducción de ruido
            denoised_path = os.path.join(output_dir, f"{base_name}_denoised.wav")
            self.reduce_noise(normalized_path, denoised_path)
            
            # 4. Mejora de habla
            final_path = os.path.join(output_dir, f"{base_name}_processed.wav")
            self.enhance_speech(denoised_path, final_path)
            
            # 5. Obtener información final
            final_info = self.get_audio_info(final_path)
            
            # Limpiar archivos intermedios
            if os.path.exists(normalized_path):
                os.unlink(normalized_path)
            if os.path.exists(denoised_path):
                os.unlink(denoised_path)
                
            result = {
                'original_file': input_path,
                'processed_file': final_path,
                'original_info': original_info,
                'processed_info': final_info,
                'status': 'success'
            }
            
            logger.info(f"Procesamiento completado exitosamente: {final_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error en pipeline de procesamiento: {str(e)}")
            raise Exception(f"Error en procesamiento: {str(e)}")


def process_audio_file(file_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Función principal para procesar un archivo de audio
    
    Args:
        file_path: Ruta del archivo a procesar
        output_dir: Directorio de salida (opcional)
        
    Returns:
        Resultado del procesamiento
    """
    processor = AudioProcessor()
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            raise Exception(f"Archivo no encontrado: {file_path}")
            
        # Verificar formato soportado
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in processor.supported_formats:
            raise Exception(f"Formato no soportado: {ext}")
            
        # Procesar archivo
        result = processor.process_full_pipeline(file_path, output_dir)
        
        return result
        
    except Exception as e:
        logger.error(f"Error procesando archivo {file_path}: {str(e)}")
        return {
            'original_file': file_path,
            'processed_file': None,
            'status': 'error',
            'error': str(e)
        }


if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python audio_processor.py <archivo_audio>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    result = process_audio_file(file_path)
    
    if result['status'] == 'success':
        print(f"✅ Procesamiento exitoso:")
        print(f"   Archivo original: {result['original_file']}")
        print(f"   Archivo procesado: {result['processed_file']}")
        print(f"   Duración: {result['processed_info']['duracion']:.1f}s")
        print(f"   Tamaño: {result['processed_info']['tamano_bytes']/1024/1024:.1f}MB")
    else:
        print(f"❌ Error en procesamiento: {result['error']}")
