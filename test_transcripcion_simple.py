#!/usr/bin/env python
"""
Script simple para probar la creación de transcripción directamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.audio_processing.models import ProcesamientoAudio
from apps.transcripcion.models import ConfiguracionTranscripcion, Transcripcion, EstadoTranscripcion
from apps.transcripcion.tasks import procesar_transcripcion_completa

User = get_user_model()

def test_transcripcion_directa():
    """Crear transcripción directamente sin usar la vista"""
    
    print("=== PRUEBA DIRECTA DE TRANSCRIPCIÓN ===\n")
    
    # 1. Obtener datos de prueba
    audio = ProcesamientoAudio.objects.filter(estado='completado').first()
    config = ConfiguracionTranscripcion.objects.filter(activa=True, nombre='Rápida').first()
    user = User.objects.filter(is_superuser=True).first()
    
    if not audio:
        print("❌ No hay audios completados")
        return False
        
    if not config:
        print("❌ No hay configuración 'Rápida'")
        return False
        
    if not user:
        print("❌ No hay superusuario")
        return False
    
    print(f"✅ Audio: {audio.titulo} (ID: {audio.id})")
    print(f"✅ Configuración: {config.nombre}")
    print(f"✅ Usuario: {user.username}")
    
    # 2. Crear transcripción directamente
    print("\n2. Creando transcripción...")
    
    parametros_custom = {
        'usar_gpu': False,
        'usar_vad': True,
        'vad_filtro': 'silero',
        'temperatura': 0.0,
        'filtro_ruido': True,
        'max_hablantes': 4,
        'min_hablantes': 1,
        'chunk_duracion': 30,
        'modelo_whisper': 'tiny',
        'idioma_principal': 'es',
        'normalizar_audio': True,
        'overlap_duracion': 5,
        'umbral_clustering': 0.7,
        'usar_enhanced_diarization': False
    }
    
    try:
        transcripcion = Transcripcion.objects.create(
            procesamiento_audio=audio,
            configuracion_utilizada=config,
            usuario_creacion=user,
            estado=EstadoTranscripcion.PENDIENTE,
            parametros_personalizados=parametros_custom
        )
        
        print(f"✅ Transcripción creada: ID={transcripcion.id}")
        
        # 3. Probar el método get_configuracion_completa
        print("\n3. Probando get_configuracion_completa...")
        
        configuracion_completa = transcripcion.get_configuracion_completa()
        print(f"✅ Configuración obtenida: {len(configuracion_completa)} parámetros")
        print(f"   - Modelo Whisper: {configuracion_completa.get('modelo_whisper')}")
        print(f"   - Idioma: {configuracion_completa.get('idioma_principal')}")
        print(f"   - GPU: {configuracion_completa.get('usar_gpu')}")
        
        # 4. Iniciar tarea de Celery
        print("\n4. Iniciando tarea de Celery...")
        
        try:
            task = procesar_transcripcion_completa.delay(transcripcion.id)
            transcripcion.task_id_celery = task.id
            transcripcion.save()
            
            print(f"✅ Tarea iniciada: {task.id}")
            
            # Verificar estado inicial
            print(f"   Estado inicial: {transcripcion.estado}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error al iniciar tarea: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ Error al crear transcripción: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def monitorear_progreso():
    """Monitorear el progreso de la transcripción más reciente"""
    
    print("\n=== MONITOREANDO PROGRESO ===\n")
    
    transcripcion = Transcripcion.objects.last()
    if not transcripcion:
        print("❌ No hay transcripciones para monitorear")
        return
    
    print(f"Transcripción ID: {transcripcion.id}")
    print(f"Estado: {transcripcion.estado}")
    print(f"Progreso: {transcripcion.progreso_porcentaje}%")
    print(f"Task ID: {transcripcion.task_id_celery}")
    
    if transcripcion.mensaje_error:
        print(f"Error: {transcripcion.mensaje_error}")
    
    if transcripcion.estado == EstadoTranscripcion.COMPLETADO:
        print(f"✅ COMPLETADO!")
        print(f"   Duración total: {transcripcion.duracion_total}s")
        print(f"   Hablantes: {transcripcion.numero_hablantes}")
        print(f"   Segmentos: {transcripcion.numero_segmentos}")
        print(f"   Palabras: {transcripcion.palabras_totales}")
        
        # Mostrar una muestra del texto
        if transcripcion.texto_completo:
            preview = transcripcion.texto_completo[:200] + "..." if len(transcripcion.texto_completo) > 200 else transcripcion.texto_completo
            print(f"   Texto: {preview}")

if __name__ == "__main__":
    success = test_transcripcion_directa()
    
    if success:
        print("\n✅ TRANSCRIPCIÓN INICIADA EXITOSAMENTE")
        print("\nPara monitorear el progreso, ejecuta:")
        print("docker exec -it actas_web python -c \"")
        print("import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup();")
        print("from apps.transcripcion.models import Transcripcion;")
        print("t = Transcripcion.objects.last();")
        print("print(f'Estado: {t.estado}, Progreso: {t.progreso_porcentaje}%, Error: {t.mensaje_error or \"None\"}')\"")
    else:
        print("\n❌ LA PRUEBA FALLÓ")
        sys.exit(1)