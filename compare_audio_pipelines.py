#!/usr/bin/env python3
"""
Comparación específica entre pipeline original vs optimizado
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.audio_processing.services.audio_pipeline import (
    AudioProcessor, 
    improve_audio_optimized,
    improve_audio_original,
    get_audio_info
)
import tempfile
import time

def compare_pipelines():
    """
    Compara el pipeline original vs el optimizado
    """
    print("🆚 COMPARACIÓN: PIPELINE ORIGINAL vs OPTIMIZADO")
    print("=" * 60)
    
    # Usar archivo de audio real
    test_file = "/app/media/audio/mejorado/proceso_22.wav"
    
    if not os.path.exists(test_file):
        print(f"❌ Archivo no encontrado: {test_file}")
        return
    
    print(f"🎵 Archivo de prueba: {test_file}")
    
    # Información original
    original_info = get_audio_info(test_file)
    print(f"📊 Info del archivo:")
    print(f"   - Duración: {original_info['duration']:.2f}s")
    print(f"   - Sample rate: {original_info['sample_rate']}Hz")
    print(f"   - Tamaño: {original_info['size']/1024/1024:.2f}MB")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # PRUEBA 1: Pipeline original
        print(f"\n🔄 PIPELINE ORIGINAL:")
        original_output = os.path.join(temp_dir, "original_output.wav")
        
        start_time = time.time()
        try:
            metadata_original = improve_audio_original(
                test_file, original_output,
                apply_noise_reduction=True,
                use_sox_effects=False  # Desactivar SoX para comparación justa
            )
            original_time = time.time() - start_time
            print(f"✅ Completado en {original_time:.2f}s")
            print(f"   - Versión: {metadata_original.get('pipeline_version', 'N/A')}")
            print(f"   - Tamaño resultado: {metadata_original.get('processed_size', 0)/1024/1024:.2f}MB")
            print(f"   - Compresión: {metadata_original.get('compression_ratio', 1):.2f}x")
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # PRUEBA 2: Pipeline optimizado
        print(f"\n🔄 PIPELINE OPTIMIZADO:")
        optimized_output = os.path.join(temp_dir, "optimized_output.wav")
        
        start_time = time.time()
        try:
            metadata_optimized = improve_audio_optimized(
                test_file, optimized_output,
                apply_noise_reduction=True,
                use_sox_effects=False  # Desactivar SoX para comparación justa
            )
            optimized_time = time.time() - start_time
            print(f"✅ Completado en {optimized_time:.2f}s")
            print(f"   - Versión: {metadata_optimized.get('pipeline_version', 'N/A')}")
            print(f"   - Tamaño resultado: {metadata_optimized.get('processed_size', 0)/1024/1024:.2f}MB")
            print(f"   - Compresión: {metadata_optimized.get('compression_ratio', 1):.2f}x")
            print(f"   - Resemblyzer usado: {metadata_optimized.get('resemblyzer_used', False)}")
            print(f"   - Optimizaciones: {len(metadata_optimized.get('quality_improvements', []))}")
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # COMPARACIÓN FINAL
        print(f"\n📊 COMPARACIÓN FINAL:")
        print(f"⏱️  Tiempo de procesamiento:")
        print(f"   - Original: {original_time:.2f}s")
        print(f"   - Optimizado: {optimized_time:.2f}s")
        print(f"   - Mejora de velocidad: {((original_time - optimized_time) / original_time * 100):+.1f}%")
        
        print(f"💾 Tamaño de salida:")
        original_size = metadata_original.get('processed_size', 0) / 1024 / 1024
        optimized_size = metadata_optimized.get('processed_size', 0) / 1024 / 1024
        print(f"   - Original: {original_size:.2f}MB")
        print(f"   - Optimizado: {optimized_size:.2f}MB")
        if original_size > 0:
            size_diff = ((optimized_size - original_size) / original_size * 100)
            print(f"   - Diferencia de tamaño: {size_diff:+.1f}%")
        
        print(f"🎯 Mejoras implementadas en el optimizado:")
        improvements = metadata_optimized.get('quality_improvements', [])
        for improvement in improvements:
            print(f"   ✓ {improvement}")

if __name__ == "__main__":
    compare_pipelines()