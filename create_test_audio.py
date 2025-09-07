"""
Script para crear archivos de audio de prueba para el sistema.
"""
import os
import numpy as np
import wave
from pathlib import Path

def crear_audio_prueba():
    """Crea un archivo de audio de prueba simple"""
    
    # Parámetros del audio
    sample_rate = 44100  # 44.1 kHz
    duration = 3  # 3 segundos
    frequency = 440  # La 440 Hz
    
    # Generar onda sinusoidal
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(frequency * 2 * np.pi * t)
    
    # Añadir un poco de ruido para simular audio real
    noise = np.random.normal(0, 0.1, tone.shape)
    audio_with_noise = tone + noise
    
    # Normalizar a rango de 16-bit
    audio_normalized = np.int16(audio_with_noise * 32767 * 0.5)
    
    # Crear directorio de media si no existe
    media_dir = Path("media")
    media_dir.mkdir(exist_ok=True)
    
    # Guardar archivo WAV
    output_file = media_dir / "test_audio.wav"
    with wave.open(str(output_file), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_normalized.tobytes())
    
    print(f"✅ Archivo de prueba creado: {output_file}")
    print(f"📊 Duración: {duration}s, Frecuencia: {frequency}Hz, Sample Rate: {sample_rate}Hz")
    
    return str(output_file)

def mostrar_info_audio(archivo):
    """Muestra información del archivo de audio"""
    try:
        with wave.open(archivo, 'r') as wav_file:
            frames = wav_file.getnframes()
            sample_rate = wav_file.getframerate()
            duration = frames / float(sample_rate)
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            
            print("\n🎵 Información del archivo:")
            print(f"  - Archivo: {archivo}")
            print(f"  - Duración: {duration:.2f} segundos")
            print(f"  - Canales: {channels}")
            print(f"  - Sample Rate: {sample_rate} Hz")
            print(f"  - Bit Depth: {sample_width * 8} bits")
            print(f"  - Frames: {frames}")
            
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")

if __name__ == "__main__":
    print("🎵 Creando archivo de audio de prueba...")
    
    try:
        archivo = crear_audio_prueba()
        mostrar_info_audio(archivo)
        
        print("\n🧪 Para probar el procesamiento de audio:")
        print("1. Asegúrate de que el contenedor Docker esté construido")
        print("2. Ejecuta: python manage.py shell")
        print("3. Importa: from apps.audio_processing.audio_processor import AudioProcessor")
        print("4. Crea una instancia: processor = AudioProcessor()")
        print("5. Procesa: processor.process_audio('media/test_audio.wav')")
        
    except ImportError:
        print("❌ numpy no está disponible. Instala con: pip install numpy")
    except Exception as e:
        print(f"❌ Error: {e}")
