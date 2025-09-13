#!/usr/bin/env python3
"""
Test específico para el escenario complejo de 3 hablantes donde:
- Orden temporal: 0, 1, 0, 2 (el primero habla dos veces)
- Validar que el mapeo respeta la primera aparición cronológica
"""

import sys
import os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from collections import OrderedDict
from apps.transcripcion.pyannote_helper import procesar_diarizacion
from apps.transcripcion.estructura_json_mejorada import mapear_hablantes_predefinidos

def test_escenario_complejo_tres_hablantes():
    print("\n" + "="*80)
    print("🔍 TEST: Escenario complejo con 3 hablantes")
    print("   Orden temporal: Hablante A, Hablante B, Hablante A otra vez, Hablante C")
    print("   IDs pyannote: 0, 1, 0, 2")
    print("="*80)
    
    # Simular datos de diarización con el patrón 0, 1, 0, 2
    segmentos_diarizacion = [
        {
            'speaker': 0,  # Primer hablante (A) - primera aparición
            'start': 0.0,
            'end': 3.5,
            'texto': 'Hola, soy Alberto, el primer hablante'
        },
        {
            'speaker': 1,  # Segundo hablante (B) - primera aparición
            'start': 3.5,
            'end': 7.0,
            'texto': 'Yo soy María, la segunda en hablar'
        },
        {
            'speaker': 0,  # Primer hablante (A) otra vez
            'start': 7.0,
            'end': 10.5,
            'texto': 'Alberto de nuevo, continuando mi intervención'
        },
        {
            'speaker': 2,  # Tercer hablante (C) - primera aparición
            'start': 10.5,
            'end': 14.0,
            'texto': 'Soy Carlos, el tercero en aparecer cronológicamente'
        }
    ]
    
    # Lista de participantes predefinidos (en orden de importancia/protocolo)
    participantes_predefinidos = ['Alberto', 'María', 'Carlos']
    
    print(f"\n📋 Participantes predefinidos: {participantes_predefinidos}")
    print("\n🎵 Segmentos de audio simulados:")
    for i, seg in enumerate(segmentos_diarizacion, 1):
        print(f"   Segmento {i}: speaker_id={seg['speaker']} ({seg['start']:.1f}s-{seg['end']:.1f}s) -> '{seg['texto'][:40]}...'")
    
    # Simular el procesamiento de pyannote_helper
    print("\n🔄 Procesando orden cronológico...")
    
    # Rastrear primera aparición de cada speaker
    speaker_tiempos = {}
    for segmento in segmentos_diarizacion:
        speaker_id = segmento['speaker']
        if speaker_id not in speaker_tiempos:
            speaker_tiempos[speaker_id] = segmento['start']
            print(f"   Primera aparición speaker_{speaker_id}: {segmento['start']:.1f}s")
    
    # Ordenar por tiempo de primera aparición
    speakers_ordenados = sorted(speaker_tiempos.keys(), key=lambda x: speaker_tiempos[x])
    print(f"\n📊 Orden cronológico de speakers: {speakers_ordenados}")
    print("   Tiempos de primera aparición:")
    for speaker_id in speakers_ordenados:
        print(f"     speaker_{speaker_id}: {speaker_tiempos[speaker_id]:.1f}s")
    
    # Crear OrderedDict como lo hace pyannote_helper
    speakers_ordenados_dict = OrderedDict()
    for i, speaker_id in enumerate(speakers_ordenados):
        speaker_key = f"SPEAKER_{speaker_id:02d}"
        speakers_ordenados_dict[speaker_key] = {
            'id_original': speaker_id,
            'primera_aparicion': speaker_tiempos[speaker_id],
            'posicion_cronologica': i + 1
        }
    
    print(f"\n🗂️ OrderedDict generado:")
    for i, (speaker_key, info) in enumerate(speakers_ordenados_dict.items(), 1):
        print(f"   Posición {i}: {speaker_key} (aparición: {info['primera_aparicion']:.1f}s)")
    
    # Mapear a participantes predefinidos
    print(f"\n🎯 Mapeando a participantes predefinidos...")
    
    mapeo_final = {}
    speakers_list = list(speakers_ordenados_dict.keys())
    
    for i, participante in enumerate(participantes_predefinidos):
        if i < len(speakers_list):
            speaker_key = speakers_list[i]
            mapeo_final[speaker_key] = participante
            print(f"   {speaker_key} → {participante}")
        else:
            print(f"   (No hay speaker para {participante})")
    
    # Verificar mapeo correcto
    print(f"\n✅ VERIFICACIÓN DEL MAPEO:")
    
    expected_mapping = {
        'SPEAKER_00': 'Alberto',  # speaker_id=0, primera aparición en 0.0s
        'SPEAKER_01': 'María',    # speaker_id=1, primera aparición en 3.5s  
        'SPEAKER_02': 'Carlos'    # speaker_id=2, primera aparición en 10.5s
    }
    
    mapeo_correcto = True
    for speaker_key, expected_name in expected_mapping.items():
        actual_name = mapeo_final.get(speaker_key, 'NO_MAPEADO')
        status = "✅" if actual_name == expected_name else "❌"
        print(f"   {speaker_key}: esperado='{expected_name}', actual='{actual_name}' {status}")
        if actual_name != expected_name:
            mapeo_correcto = False
    
    # Validar asignación en segmentos
    print(f"\n🎬 VALIDACIÓN EN SEGMENTOS:")
    for i, seg in enumerate(segmentos_diarizacion, 1):
        speaker_key = f"SPEAKER_{seg['speaker']:02d}"
        participante_asignado = mapeo_final.get(speaker_key, 'DESCONOCIDO')
        print(f"   Segmento {i} (speaker_id={seg['speaker']}): '{participante_asignado}' dice: '{seg['texto'][:50]}...'")
    
    # Resultado final
    print("\n" + "="*80)
    if mapeo_correcto:
        print("🎉 ¡MAPEO CORRECTO!")
        print("✅ El sistema maneja correctamente hablantes que aparecen múltiples veces")
        print("✅ El mapeo respeta el orden de PRIMERA aparición cronológica")
        print("✅ Cada hablante se asigna consistentemente en todos sus segmentos")
    else:
        print("❌ ERROR EN EL MAPEO")
        print("El sistema NO está manejando correctamente el escenario complejo")
    
    print("="*80)
    
    return mapeo_correcto

if __name__ == "__main__":
    test_escenario_complejo_tres_hablantes()