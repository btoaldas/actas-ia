#!/usr/bin/env python
"""
Script para probar el pipeline de audio con un archivo de prueba.
"""
import os
import django
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.audio_processing.services.audio_pipeline import improve_audio

def test_audio_pipeline():
    """Probar el pipeline completo con un archivo sintético."""
    print("🎵 PRUEBA DEL PIPELINE DE AUDIO")
    print("=" * 40)
    
    # 1. Crear audio de prueba
    print("1. Creando archivo de audio de prueba...")
    sample_rate = 16000
    duration = 2.0  # 2 segundos
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Crear señal de prueba: tono + ruido
    signal = 0.5 * np.sin(2 * np.pi * 440 * t)  # La musical
    noise = 0.1 * np.random.normal(0, 1, len(signal))  # Ruido
    audio_data = signal + noise
    
    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_input:
        sf.write(tmp_input.name, audio_data, sample_rate)
        input_file = tmp_input.name
    
    print(f"✅ Archivo creado: {input_file}")
    
    # 2. Procesar con el pipeline
    print("\n2. Procesando con pipeline completo...")
    try:
        with tempfile.NamedTemporaryFile(suffix='_processed.wav', delete=False) as tmp_output:
            output_file = tmp_output.name
        
        # Llamar al pipeline
        metadata = improve_audio(
            input_file, 
            output_file,
            apply_noise_reduction=True,
            use_sox_effects=True
        )
        
        print("✅ Procesamiento completado")
        print(f"📊 Metadatos: {metadata}")
        
        # 3. Verificar resultado
        if Path(output_file).exists():
            output_data, output_sr = sf.read(output_file)
            print(f"✅ Archivo procesado: {len(output_data)} samples a {output_sr} Hz")
            
            # Limpiar archivos temporales
            os.unlink(input_file)
            os.unlink(output_file)
            
            print("\n🎉 ¡PIPELINE FUNCIONANDO CORRECTAMENTE!")
            return True
        else:
            print("❌ Archivo procesado no encontrado")
            return False
            
    except Exception as e:
        print(f"❌ Error en pipeline: {e}")
        # Limpiar en caso de error
        try:
            os.unlink(input_file)
            if 'output_file' in locals():
                os.unlink(output_file)
        except:
            pass
        return False

if __name__ == "__main__":
    success = test_audio_pipeline()
    exit(0 if success else 1)
