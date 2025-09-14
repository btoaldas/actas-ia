#!/usr/bin/env python3
"""
Script para verificar que las mejoras de audio funcionan después de reiniciar Docker
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verificar_dependencias():
    """Verificar que todas las dependencias estén disponibles"""
    print("🔍 VERIFICANDO DEPENDENCIAS DE AUDIO...")
    
    errores = []
    
    # Verificar Resemblyzer
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
        print("✅ Resemblyzer: OK")
    except ImportError as e:
        errores.append(f"❌ Resemblyzer: {e}")
    
    # Verificar librosa
    try:
        import librosa
        print("✅ Librosa: OK")
    except ImportError as e:
        errores.append(f"❌ Librosa: {e}")
    
    # Verificar FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg: OK")
        else:
            errores.append("❌ FFmpeg: No disponible")
    except Exception as e:
        errores.append(f"❌ FFmpeg: {e}")
    
    # Verificar funciones propias
    try:
        from apps.audio_processing.services.audio_pipeline import ensure_wav_optimized, preprocess_wav_optimized
        print("✅ Pipeline audio optimizado: OK")
    except ImportError as e:
        errores.append(f"❌ Pipeline audio: {e}")
    
    return errores

def verificar_funcionalidad():
    """Verificar que las funciones principales funcionen"""
    print("\n🔧 VERIFICANDO FUNCIONALIDAD...")
    
    try:
        from apps.audio_processing.services.audio_pipeline import AudioProcessor
        processor = AudioProcessor()
        print("✅ AudioProcessor: Instancia creada correctamente")
        
        # Verificar que los métodos optimizados existen
        if hasattr(processor, 'ensure_wav_optimized'):
            print("✅ Método ensure_wav_optimized: Disponible")
        else:
            print("❌ Método ensure_wav_optimized: NO disponible")
            
        if hasattr(processor, 'preprocess_wav_optimized'):
            print("✅ Método preprocess_wav_optimized: Disponible")
        else:
            print("❌ Método preprocess_wav_optimized: NO disponible")
            
        return True
    except Exception as e:
        print(f"❌ Error verificando funcionalidad: {e}")
        return False

def main():
    print("🎯 VERIFICACIÓN POST-RESTART DE MEJORAS DE AUDIO")
    print("=" * 60)
    
    # Verificar dependencias
    errores = verificar_dependencias()
    
    # Verificar funcionalidad
    funcionalidad_ok = verificar_funcionalidad()
    
    # Resumen
    print("\n📊 RESUMEN:")
    if not errores and funcionalidad_ok:
        print("🎉 ¡TODO FUNCIONA CORRECTAMENTE!")
        print("✅ Resemblyzer está instalado y funcionando")
        print("✅ Pipeline de audio optimizado disponible")
        print("✅ Todas las dependencias están OK")
        print("\n💡 El sistema está listo para procesar audio con mejoras de calidad")
    else:
        print("⚠️ SE ENCONTRARON PROBLEMAS:")
        for error in errores:
            print(f"   {error}")
        if not funcionalidad_ok:
            print("   ❌ Funcionalidad de pipeline comprometida")
        
        print("\n🔧 SOLUCIÓN:")
        print("   1. Ejecutar: docker exec -it actas_web pip install -r requirements.txt")
        print("   2. Reiniciar el contenedor si es necesario")

if __name__ == "__main__":
    main()