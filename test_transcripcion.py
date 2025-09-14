#!/usr/bin/env python
"""
Script de prueba para el flujo completo de transcripción
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.audio_processing.models import ProcesamientoAudio
from apps.transcripcion.models import ConfiguracionTranscripcion, Transcripcion
from apps.transcripcion.views import configurar_transcripcion
from django.test import RequestFactory
from django.http import HttpRequest
import json

User = get_user_model()

def test_transcripcion_flow():
    """Probar el flujo completo de transcripción"""
    
    print("=== PRUEBA DEL FLUJO DE TRANSCRIPCIÓN ===\n")
    
    # 1. Verificar audios disponibles
    audios_completados = ProcesamientoAudio.objects.filter(estado='completado')
    print(f"1. Audios completados disponibles: {audios_completados.count()}")
    
    if not audios_completados.exists():
        print("❌ No hay audios completados para transcribir")
        return False
    
    # 2. Verificar configuraciones disponibles
    configs = ConfiguracionTranscripcion.objects.filter(activa=True)
    print(f"2. Configuraciones activas: {configs.count()}")
    
    if not configs.exists():
        print("❌ No hay configuraciones de transcripción disponibles")
        return False
    
    # 3. Seleccionar audio y configuración de prueba
    audio_prueba = audios_completados.first()
    config_prueba = configs.filter(nombre='Rápida').first()
    
    print(f"3. Usando audio: ID={audio_prueba.id}, Título='{audio_prueba.titulo}'")
    print(f"4. Usando configuración: '{config_prueba.nombre}' - {config_prueba.descripcion}")
    
    # 4. Simular petición POST
    factory = RequestFactory()
    
    # Crear un usuario de prueba
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ No se encontró superusuario")
        return False
    
    # Datos de la petición POST
    post_data = {
        'audio_ids': [str(audio_prueba.id)],
        'configuracion_base': str(config_prueba.id),
        'titulo_transcripcion': f'Transcripción de {audio_prueba.titulo}',
        'descripcion_transcripcion': 'Prueba automatizada del sistema de transcripción',
        'temperatura': '0.0',
        'idioma_principal': 'es',
        'usar_vad': 'true',
        'min_hablantes': '1',
        'max_hablantes': '4',
        'chunk_duracion': '30',
        'usar_gpu': 'false'
    }
    
    print(f"5. Datos POST preparados: {len(post_data)} parámetros")
    
    # Crear la petición
    request = factory.post('/transcripcion/configurar/', data=post_data)
    request.user = user
    
    print("6. Intentando procesar la petición de transcripción...")
    
    try:
        # Simular la vista
        from apps.transcripcion.views import configurar_transcripcion
        response = configurar_transcripcion(request, audio_prueba.id)
        
        print(f"7. Respuesta HTTP: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ La petición fue procesada exitosamente")
            
            # Verificar si se crearon resultados de transcripción
            transcripciones = Transcripcion.objects.filter(
                audio_procesamiento=audio_prueba
            ).order_by('-fecha_creacion')
            
            if transcripciones.exists():
                ultima = transcripciones.first()
                print(f"8. Transcripción creada: ID={ultima.id}, Estado='{ultima.estado}'")
                print(f"   Título: '{ultima.titulo}'")
                print(f"   Configuración: '{ultima.configuracion.nombre}'")
                return True
            else:
                print("8. ⚠️  No se encontraron resultados de transcripción creados")
                return False
                
        elif response.status_code == 302:
            print("✅ Redirección detectada (comportamiento normal)")
            
            # Verificar si se crearon resultados 
            transcripciones = Transcripcion.objects.filter(
                audio_procesamiento=audio_prueba
            ).order_by('-fecha_creacion')
            
            if transcripciones.exists():
                ultima = transcripciones.first()
                print(f"8. Transcripción creada: ID={ultima.id}, Estado='{ultima.estado}'")
                return True
            else:
                print("8. ⚠️  Redirección pero sin transcripción creada")
                return False
        else:
            print(f"❌ Error en la petición: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_system_status():
    """Verificar el estado del sistema"""
    print("=== ESTADO DEL SISTEMA ===\n")
    
    # Usuarios
    users = User.objects.count()
    superusers = User.objects.filter(is_superuser=True).count()
    print(f"Usuarios totales: {users} (Superusuarios: {superusers})")
    
    # Audios
    audios_total = ProcesamientoAudio.objects.count()
    audios_completados = ProcesamientoAudio.objects.filter(estado='completado').count()
    print(f"Audios totales: {audios_total} (Completados: {audios_completados})")
    
    # Configuraciones
    configs_total = ConfiguracionTranscripcion.objects.count()
    configs_activas = ConfiguracionTranscripcion.objects.filter(activa=True).count()
    print(f"Configuraciones: {configs_total} (Activas: {configs_activas})")
    
    # Transcripciones
    transcripciones = Transcripcion.objects.count()
    print(f"Transcripciones existentes: {transcripciones}")
    
    print()

if __name__ == "__main__":
    check_system_status()
    success = test_transcripcion_flow()
    
    if success:
        print("\n✅ PRUEBA COMPLETADA EXITOSAMENTE")
    else:
        print("\n❌ LA PRUEBA FALLÓ")
        sys.exit(1)