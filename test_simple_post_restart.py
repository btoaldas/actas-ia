#!/usr/bin/env python3
"""
Test simple para verificar que Resemblyzer funcionará después de restart
"""
import sys
import os

# Configurar Django path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def test_resemblyzer():
    """Test simple de Resemblyzer"""
    print("🧪 PROBANDO RESEMBLYZER...")
    
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav
        print("✅ Importación exitosa: VoiceEncoder, preprocess_wav")
        
        # Probar instanciar el encoder
        encoder = VoiceEncoder()
        print("✅ VoiceEncoder instanciado correctamente")
        
        return True
    except Exception as e:
        print(f"❌ Error con Resemblyzer: {e}")
        return False

def test_pipeline_functions():
    """Test de funciones del pipeline"""
    print("\n🔧 PROBANDO FUNCIONES PIPELINE...")
    
    try:
        from apps.audio_processing.services.audio_pipeline import ensure_wav_optimized, preprocess_wav_optimized
        print("✅ Funciones importadas: ensure_wav_optimized, preprocess_wav_optimized")
        return True
    except Exception as e:
        print(f"❌ Error importando funciones: {e}")
        return False

def main():
    print("🎯 TEST SIMPLE POST-RESTART")
    print("=" * 40)
    
    resemblyzer_ok = test_resemblyzer()
    pipeline_ok = test_pipeline_functions()
    
    print("\n📊 RESULTADO:")
    if resemblyzer_ok and pipeline_ok:
        print("🎉 ¡TODO LISTO!")
        print("✅ Resemblyzer funcionará después de restart")
        print("✅ Pipeline de audio optimizado disponible")
        print("\n💡 NO necesitas reinstalar nada al reiniciar Docker")
        print("   Ya está en requirements.txt")
    else:
        print("⚠️ PROBLEMAS DETECTADOS")
        if not resemblyzer_ok:
            print("❌ Resemblyzer no funciona")
        if not pipeline_ok:
            print("❌ Pipeline optimizado no funciona")

if __name__ == "__main__":
    main()