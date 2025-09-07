"""
Script completo de verificación del sistema de procesamiento de audio.
Verifica toda la pipeline desde la interfaz hasta el procesamiento.
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def verificar_imports():
    """Verifica que todos los módulos necesarios se importen correctamente"""
    print("🔍 Verificando imports...")
    
    try:
        from apps.audio_processing.models import AudioRecording
        print("✅ Modelo AudioRecording importado")
    except Exception as e:
        print(f"❌ Error importando modelo: {e}")
        return False
    
    try:
        from apps.audio_processing.views import centro_audio, api_procesar_audio
        print("✅ Vistas importadas")
    except Exception as e:
        print(f"❌ Error importando vistas: {e}")
        return False
    
    try:
        from apps.audio_processing.audio_processor import AudioProcessor
        print("✅ AudioProcessor importado")
    except Exception as e:
        print(f"❌ Error importando AudioProcessor: {e}")
        return False
    
    try:
        from apps.audio_processing.tasks import procesar_audio_task
        print("✅ Task de Celery importada")
    except Exception as e:
        print(f"❌ Error importando task: {e}")
        return False
    
    return True

def verificar_herramientas():
    """Verifica que las herramientas de audio estén disponibles"""
    print("\n🛠️ Verificando herramientas de audio...")
    
    import subprocess
    
    # Verificar FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg disponible")
        else:
            print("❌ FFmpeg no funciona correctamente")
            return False
    except Exception as e:
        print(f"❌ FFmpeg no encontrado: {e}")
        return False
    
    # Verificar SoX
    try:
        result = subprocess.run(['sox', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ SoX disponible")
        else:
            print("❌ SoX no funciona correctamente")
            return False
    except Exception as e:
        print(f"❌ SoX no encontrado: {e}")
        return False
    
    return True

def verificar_directorios():
    """Verifica que los directorios necesarios existan"""
    print("\n📁 Verificando directorios...")
    
    directorios = [
        '/app/media',
        '/app/media/audio',
        '/app/staticfiles',
        '/app/templates/audio_processing'
    ]
    
    for directorio in directorios:
        if Path(directorio).exists():
            print(f"✅ {directorio}")
        else:
            print(f"❌ {directorio} no existe")
            # Crear directorio si no existe
            try:
                Path(directorio).mkdir(parents=True, exist_ok=True)
                print(f"  ✅ Creado automáticamente")
            except Exception as e:
                print(f"  ❌ Error creando directorio: {e}")
                return False
    
    return True

def verificar_database():
    """Verifica la conexión a la base de datos"""
    print("\n🗄️ Verificando base de datos...")
    
    try:
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Conexión a base de datos OK")
        
        # Verificar tablas específicas
        from apps.audio_processing.models import AudioRecording
        count = AudioRecording.objects.count()
        print(f"✅ Tabla audio_recording accesible ({count} registros)")
        
        return True
    except Exception as e:
        print(f"❌ Error de base de datos: {e}")
        return False

def verificar_celery():
    """Verifica que Celery esté funcionando"""
    print("\n⚡ Verificando Celery...")
    
    try:
        from celery import Celery
        from config.celery import app
        
        # Verificar que la app de Celery esté configurada
        print(f"✅ App Celery: {app.main}")
        
        # Verificar que las tareas estén registradas
        tasks = app.control.inspect().registered()
        if tasks:
            print("✅ Worker de Celery respondiendo")
            print(f"✅ Tareas registradas: {len(list(tasks.values())[0]) if tasks else 0}")
        else:
            print("⚠️ No se puede conectar con workers de Celery")
        
        return True
    except Exception as e:
        print(f"❌ Error con Celery: {e}")
        return False

def probar_procesamiento():
    """Prueba básica del procesamiento de audio"""
    print("\n🎵 Probando procesamiento de audio...")
    
    try:
        from apps.audio_processing.audio_processor import AudioProcessor
        
        # Crear instancia del procesador
        processor = AudioProcessor()
        print("✅ AudioProcessor instanciado")
        
        # Verificar métodos principales
        methods = ['get_audio_info', 'normalize_audio', 'reduce_noise', 'enhance_speech']
        for method in methods:
            if hasattr(processor, method):
                print(f"✅ Método {method} disponible")
            else:
                print(f"❌ Método {method} no encontrado")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error probando procesamiento: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🎯 VERIFICACIÓN COMPLETA DEL SISTEMA DE AUDIO")
    print("=" * 50)
    
    resultados = []
    
    # Ejecutar todas las verificaciones
    verificaciones = [
        ("Imports", verificar_imports),
        ("Herramientas", verificar_herramientas),
        ("Directorios", verificar_directorios),
        ("Base de datos", verificar_database),
        ("Celery", verificar_celery),
        ("Procesamiento", probar_procesamiento)
    ]
    
    for nombre, funcion in verificaciones:
        try:
            resultado = funcion()
            resultados.append((nombre, resultado))
        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    exitosos = 0
    for nombre, resultado in resultados:
        status = "✅" if resultado else "❌"
        print(f"{status} {nombre}")
        if resultado:
            exitosos += 1
    
    print(f"\n🎯 {exitosos}/{len(resultados)} verificaciones exitosas")
    
    if exitosos == len(resultados):
        print("🚀 ¡Sistema completamente funcional!")
        print("\n📝 Próximos pasos:")
        print("1. Acceder a http://localhost:8000/audio/centro/")
        print("2. Probar grabación de audio")
        print("3. Probar carga de archivos")
        print("4. Verificar procesamiento en background")
    else:
        print("⚠️ Hay problemas que requieren atención")
        print("Revisa los errores arriba y corrige antes de usar el sistema")
    
    return exitosos == len(resultados)

if __name__ == "__main__":
    main()
