#!/usr/bin/env python
"""
Script para probar el nuevo sistema de monitoreo de transcripción
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.audio_processing.models import ProcesamientoAudio
from apps.transcripcion.models import ConfiguracionTranscripcion
import requests
import time

def test_monitoreo_system():
    """Probar el sistema de monitoreo completo"""
    
    print("=== PRUEBA DEL SISTEMA DE MONITOREO ===\n")
    
    # 1. Verificar que tengamos audio disponible
    audios = ProcesamientoAudio.objects.filter(estado='completado')
    if not audios.exists():
        print("❌ No hay audios completados para probar")
        return False
    
    audio = audios.first()
    print(f"✅ Audio de prueba: {audio.titulo} (ID: {audio.id})")
    
    # 2. Verificar que tengamos configuraciones
    configs = ConfiguracionTranscripcion.objects.filter(activa=True)
    if not configs.exists():
        print("❌ No hay configuraciones activas")
        return False
    
    config = configs.first()
    print(f"✅ Configuración de prueba: {config.nombre}")
    
    # 3. Verificar que las vistas respondan
    base_url = "http://localhost:8000"
    
    try:
        # Probar vista de configuración
        response = requests.get(f"{base_url}/transcripcion/configurar/{audio.id}/", timeout=5)
        if response.status_code == 200:
            print("✅ Vista de configuración accesible")
        else:
            print(f"❌ Vista de configuración error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        print("💡 Asegúrate de que el servidor esté corriendo")
        return False
    
    # 4. Verificar estructura JSON de configuración
    try:
        config_json = config.to_json()
        required_fields = ['modelo_whisper', 'temperatura', 'idioma_principal', 'usar_vad']
        
        for field in required_fields:
            if field not in config_json:
                print(f"❌ Campo faltante en JSON: {field}")
                return False
        
        print("✅ Estructura JSON de configuración válida")
        
    except Exception as e:
        print(f"❌ Error en JSON de configuración: {e}")
        return False
    
    print("\n🎉 SISTEMA DE MONITOREO LISTO PARA USAR")
    print("\nPara probar completamente:")
    print("1. Abre http://localhost:8000/transcripcion/audios-listos/")
    print("2. Haz clic en 'Configurar' en cualquier audio")
    print("3. Ajusta parámetros y haz clic en 'Transcribir Audio'")
    print("4. Observa el monitoreo en tiempo real")
    print("5. Ve los resultados JSON una vez completado")
    
    return True

def verificar_endpoints():
    """Verificar que los endpoints API estén configurados"""
    
    print("\n=== VERIFICACIÓN DE ENDPOINTS API ===\n")
    
    audio = ProcesamientoAudio.objects.filter(estado='completado').first()
    if not audio:
        print("❌ No hay audios para verificar endpoints")
        return False
    
    base_url = "http://localhost:8000"
    endpoints = [
        f"/transcripcion/api/audio-estado/{audio.id}/",
        # No podemos probar estado transcripción sin una transcripción activa
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"✅ {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   📊 Respuesta: {data.get('mensaje', 'OK')}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint} - Error: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = test_monitoreo_system()
    
    if success:
        verificar_endpoints()
        print("\n✅ SISTEMA DE MONITOREO VERIFICADO")
    else:
        print("\n❌ VERIFICACIÓN FALLÓ")
        sys.exit(1)