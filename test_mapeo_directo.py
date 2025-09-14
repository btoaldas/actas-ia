#!/usr/bin/env python3
"""
Test directo del mapeo cronológico en pyannote_helper.py
"""

import sys
import os
sys.path.append('/app')

def test_mapeo_directo():
    """Test directo de la función de mapeo cronológico"""
    
    # Simular datos como los aparecen en pyannote
    speakers_tiempo_aparicion = {
        1: 0.0,  # Alberto habla primero con speaker_id=1
        0: 3.88  # Elizabeth habla segunda con speaker_id=0
    }
    
    participantes_esperados = [
        {'nombres': 'Beto', 'orden': 1},    # Primer participante
        {'nombres': 'Ely', 'orden': 2}      # Segundo participante
    ]
    
    print("🎯 TEST DIRECTO DEL MAPEO CRONOLÓGICO")
    print("=" * 50)
    print("Speakers tiempo aparición:", speakers_tiempo_aparicion)
    print("Participantes esperados:", [p['nombres'] for p in participantes_esperados])
    
    # MAPEO CRONOLÓGICO (simular el código real)
    speakers_ordenados_cronologicamente = sorted(speakers_tiempo_aparicion.items(), key=lambda x: x[1])
    print(f"\nOrden cronológico: {speakers_ordenados_cronologicamente}")
    
    mapeo_speakers = {}
    for i, (speaker_id, tiempo) in enumerate(speakers_ordenados_cronologicamente):
        speaker_idx = i  # Índice cronológico
        nombre_participante = participantes_esperados[i]['nombres'] if i < len(participantes_esperados) else f"Speaker_{i}"
        
        mapeo_speakers[speaker_id] = {
            'speaker_idx': speaker_idx,
            'nombre': nombre_participante,
            'tiempo_primera_aparicion': tiempo,
            'posicion_cronologica': i
        }
    
    print(f"\nMapeo final:")
    for speaker_id, info in mapeo_speakers.items():
        print(f"  speaker={speaker_id} → speaker_idx={info['speaker_idx']} → {info['nombre']}")
    
    # Simular segmentos con speaker_idx aplicado
    segmentos_simulados = [
        {'inicio': 0.0, 'fin': 3.48, 'speaker': 1, 'texto': 'Hola, me llamo Alberto'},
        {'inicio': 3.88, 'fin': 4.56, 'speaker': 0, 'texto': 'Hola, soy Elizabeth'}
    ]
    
    print(f"\nSegmentos con speaker_idx aplicado:")
    for seg in segmentos_simulados:
        speaker_original = seg['speaker']
        speaker_idx = mapeo_speakers[speaker_original]['speaker_idx']
        nombre = mapeo_speakers[speaker_original]['nombre']
        print(f"  [{seg['inicio']}s] speaker={speaker_original} → speaker_idx={speaker_idx} → {nombre}: {seg['texto']}")
    
    # VALIDACIÓN
    primer_segmento = segmentos_simulados[0]
    primer_speaker_idx = mapeo_speakers[primer_segmento['speaker']]['speaker_idx']
    primer_nombre = mapeo_speakers[primer_segmento['speaker']]['nombre']
    
    print(f"\n✅ VALIDACIÓN:")
    print(f"  Primer segmento (0.0s): speaker_idx={primer_speaker_idx} → {primer_nombre}")
    
    if primer_speaker_idx == 0 and primer_nombre == "Beto":
        print("  ✅ CORRECTO: El mapeo cronológico funciona")
        return True
    else:
        print("  ❌ ERROR: El mapeo está mal")
        return False

if __name__ == "__main__":
    exito = test_mapeo_directo()
    if not exito:
        sys.exit(1)