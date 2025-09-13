#!/usr/bin/env python3
"""
Script para probar todas las modificaciones de transcripción
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
from apps.transcripcion.tasks import procesar_transcripcion_completa

def probar_transcripcion_88():
    """Prueba la transcripción 88 con las nuevas modificaciones"""
    
    print("🧪 PROBANDO TRANSCRIPCIÓN 88 CON MODIFICACIONES")
    print("=" * 60)
    
    try:
        # Verificar que existe la transcripción
        transcripcion = Transcripcion.objects.get(id=88)
        print(f"✅ Transcripción {transcripcion.id} encontrada")
        print(f"   - Estado actual: {transcripcion.estado}")
        print(f"   - Audio ID: {transcripcion.procesamiento_audio.id}")
        
        # Verificar participantes
        participantes = transcripcion.procesamiento_audio.participantes_detallados
        print(f"   - Participantes configurados: {len(participantes)}")
        for i, p in enumerate(participantes):
            print(f"     {i}: {p.get('nombres', 'Sin nombre')}")
        
        # Obtener configuración completa
        config = transcripcion.get_configuracion_completa()
        participantes_config = config.get('participantes_esperados', [])
        print(f"   - Participantes en configuración: {len(participantes_config)}")
        
        # Verificar que min_speakers = max_speakers = número de participantes
        min_speakers = config.get('min_speakers', 'No definido')
        max_speakers = config.get('max_speakers', 'No definido')
        print(f"   - min_speakers: {min_speakers}")
        print(f"   - max_speakers: {max_speakers}")
        
        print("\n🚀 INICIANDO PROCESAMIENTO CON CONFIGURACIÓN FORZADA")
        print("=" * 60)
        
        # Procesar con las nuevas modificaciones
        result = procesar_transcripcion_completa.delay(88)
        print(f"✅ Tarea iniciada con ID: {result.id}")
        print("⏳ Procesando... (puedes revisar logs del worker)")
        
        return True
        
    except Transcripcion.DoesNotExist:
        print("❌ Transcripción 88 no encontrada")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def verificar_configuracion():
    """Verifica que la configuración esté correcta"""
    
    print("\n🔍 VERIFICANDO CONFIGURACIÓN")
    print("=" * 60)
    
    try:
        transcripcion = Transcripcion.objects.get(id=88)
        config = transcripcion.get_configuracion_completa()
        
        participantes = config.get('participantes_esperados', [])
        min_speakers = config.get('min_speakers')
        max_speakers = config.get('max_speakers')
        
        print(f"Participantes esperados: {len(participantes)}")
        print(f"Min speakers: {min_speakers}")
        print(f"Max speakers: {max_speakers}")
        
        # Verificar que estén configurados para forzar el número exacto
        if participantes and len(participantes) >= 2:
            num_participantes = len(participantes)
            if min_speakers == num_participantes and max_speakers == num_participantes:
                print(f"✅ CONFIGURACIÓN CORRECTA: Forzando {num_participantes} speakers")
                return True
            else:
                print(f"⚠️ CONFIGURACIÓN SUBÓPTIMA: min={min_speakers}, max={max_speakers}, participantes={num_participantes}")
                return False
        else:
            print("⚠️ No hay suficientes participantes configurados")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando configuración: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 SCRIPT DE PRUEBA DE TRANSCRIPCIÓN MEJORADA")
    print("=" * 60)
    
    # Verificar configuración
    config_ok = verificar_configuracion()
    
    if config_ok:
        # Probar transcripción
        resultado = probar_transcripcion_88()
        
        if resultado:
            print("\n✅ PRUEBA INICIADA CORRECTAMENTE")
            print("💡 PRÓXIMOS PASOS:")
            print("   1. Revisar logs del worker: docker logs --tail=50 actas_celery_worker")
            print("   2. Verificar estructura: python verificar_estructura_completa.py")
            print("   3. Buscar mapeos: 'MAPEO: SPEAKER_XX → Nombre'")
        else:
            print("\n❌ PRUEBA FALLÓ")
    else:
        print("\n❌ CONFIGURACIÓN INCORRECTA")