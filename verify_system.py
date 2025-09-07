#!/usr/bin/env python
"""
Script de verificación completa del sistema de procesamiento de audio.
Verifica todos los componentes: BD, backend, frontend, dependencias.
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verificar_sistema():
    """Verificar todos los componentes del sistema."""
    print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA DE AUDIO")
    print("=" * 60)
    
    errores = []
    
    # 1. Verificar modelos de base de datos
    print("\n📊 1. BASE DE DATOS")
    print("-" * 30)
    try:
        from apps.audio_processing.models import ProcesamientoAudio, LogProcesamiento
        count_proc = ProcesamientoAudio.objects.count()
        count_logs = LogProcesamiento.objects.count()
        print(f"✅ ProcesamientoAudio: {count_proc} registros")
        print(f"✅ LogProcesamiento: {count_logs} registros")
        print(f"✅ Modelos importados correctamente")
    except Exception as e:
        error_msg = f"❌ Error en base de datos: {e}"
        print(error_msg)
        errores.append(error_msg)
    
    # 2. Verificar pipeline de audio
    print("\n🎵 2. PIPELINE DE AUDIO")
    print("-" * 30)
    try:
        from apps.audio_processing.services.audio_pipeline import AudioProcessor
        ffmpeg_ok = AudioProcessor.verificar_ffmpeg()
        sox_ok = AudioProcessor.verificar_sox()
        print(f"✅ FFmpeg disponible: {ffmpeg_ok}")
        print(f"✅ SoX disponible: {sox_ok}")
        print(f"✅ AudioProcessor importado correctamente")
        
        if not ffmpeg_ok:
            errores.append("❌ FFmpeg no está disponible")
        if not sox_ok:
            errores.append("❌ SoX no está disponible")
            
    except Exception as e:
        error_msg = f"❌ Error en pipeline: {e}"
        print(error_msg)
        errores.append(error_msg)
    
    # 3. Verificar dependencias de audio
    print("\n📦 3. DEPENDENCIAS DE AUDIO")
    print("-" * 30)
    dependencias = [
        ('librosa', 'Análisis de audio'),
        ('soundfile', 'Lectura/escritura de archivos de audio'),
        ('pydub', 'Manipulación de audio'),
        ('noisereduce', 'Reducción de ruido'),
        ('webrtcvad', 'Detección de actividad de voz'),
        ('torch', 'Framework de aprendizaje automático'),
        ('torchaudio', 'Procesamiento de audio con PyTorch'),
    ]
    
    for dep, desc in dependencias:
        try:
            __import__(dep)
            print(f"  ✅ {dep:<15} - {desc}")
        except ImportError:
            error_msg = f"  ❌ {dep:<15} - NO INSTALADO"
            print(error_msg)
            errores.append(f"Dependencia faltante: {dep}")
    
    # 4. Verificar tareas de Celery
    print("\n⚙️  4. PROCESAMIENTO EN SEGUNDO PLANO")
    print("-" * 30)
    try:
        from apps.audio_processing.tasks import procesar_audio_task
        print("✅ Tarea procesar_audio_task: Importada correctamente")
        
        # Verificar configuración de Celery
        from celery import current_app
        print(f"✅ Celery configurado: {current_app.conf.broker_url[:20]}...")
        
    except Exception as e:
        error_msg = f"❌ Error en Celery: {e}"
        print(error_msg)
        errores.append(error_msg)
    
    # 5. Verificar formularios
    print("\n📝 5. FORMULARIOS Y VISTAS")
    print("-" * 30)
    try:
        from apps.audio_processing.forms import SubirAudioForm
        from apps.audio_processing.views import api_procesar_audio
        print("✅ SubirAudioForm: Importado correctamente")
        print("✅ API views: Importadas correctamente")
    except Exception as e:
        error_msg = f"❌ Error en formularios/vistas: {e}"
        print(error_msg)
        errores.append(error_msg)
    
    # 6. Verificar configuración del sistema
    print("\n🔧 6. CONFIGURACIÓN DEL SISTEMA")
    print("-" * 30)
    try:
        from django.conf import settings
        
        # Verificar configuración de medios
        print(f"✅ MEDIA_ROOT: {settings.MEDIA_ROOT}")
        print(f"✅ MEDIA_URL: {settings.MEDIA_URL}")
        
        # Verificar aplicaciones instaladas
        if 'apps.audio_processing' in settings.INSTALLED_APPS:
            print("✅ audio_processing app: Configurada en INSTALLED_APPS")
        else:
            errores.append("❌ audio_processing no está en INSTALLED_APPS")
            
    except Exception as e:
        error_msg = f"❌ Error en configuración: {e}"
        print(error_msg)
        errores.append(error_msg)
    
    # 7. Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE VERIFICACIÓN")
    print("=" * 60)
    
    if not errores:
        print("� ¡SISTEMA COMPLETAMENTE FUNCIONAL!")
        print("✅ Todos los componentes están configurados correctamente")
        print("✅ Pipeline de audio listo para procesar archivos")
        print("✅ Base de datos configurada y accesible")
        print("✅ Dependencias instaladas correctamente")
        return True
    else:
        print(f"⚠️  SE ENCONTRARON {len(errores)} PROBLEMAS:")
        for i, error in enumerate(errores, 1):
            print(f"   {i}. {error}")
        print("\n🔧 Resuelve estos problemas para tener un sistema completamente funcional")
        return False

if __name__ == "__main__":
    exito = verificar_sistema()
    sys.exit(0 if exito else 1)
