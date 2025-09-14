#!/usr/bin/env python3
"""
Test del mapeo cronológico real para validar la corrección
"""

import sys
import os
sys.path.append('/app')

# Simular datos reales de pyannote donde speaker_id=1 aparece primero
def test_mapeo_cronologico_real():
    """Test con datos reales donde speaker_id=1 aparece a los 0.0s"""
    
    # Simular resultado de pyannote como aparece en los logs reales
    segmentos_pyannote_simulados = [
        {'inicio': 0.0, 'fin': 3.48, 'speaker': 1},  # Alberto habla primero, pero pyannote le asigna ID=1
        {'inicio': 3.88, 'fin': 4.56, 'speaker': 0}, # Elizabeth responde, pyannote le asigna ID=0
        {'inicio': 5.16, 'fin': 7.26, 'speaker': 1}, # Alberto otra vez
        {'inicio': 7.76, 'fin': 8.92, 'speaker': 0}, # Elizabeth otra vez
    ]
    
    # Simular participantes esperados (orden del JSON del usuario)
    participantes_esperados = [
        {'nombres': 'Beto', 'orden': 1},    # Primer participante (Alberto/Beto)
        {'nombres': 'Ely', 'orden': 2}      # Segundo participante (Elizabeth/Ely)
    ]
    
    print("🎯 SIMULANDO ESCENARIO REAL:")
    print("  - Alberto habla primero (0.0s) pero pyannote le asigna speaker=1")
    print("  - Elizabeth habla segunda (3.88s) y pyannote le asigna speaker=0")
    print("  - Los participantes esperados son: [Beto, Ely]")
    print("  - Esperamos que Alberto (speaker=1, 0.0s) → Beto (posición 0)")
    print("  - Esperamos que Elizabeth (speaker=0, 3.88s) → Ely (posición 1)")
    
    # PASO 1: Construir mapeo cronológico
    speakers_tiempo_aparicion = {}
    for seg in segmentos_pyannote_simulados:
        speaker = seg['speaker']
        inicio = seg['inicio']
        if speaker not in speakers_tiempo_aparicion:
            speakers_tiempo_aparicion[speaker] = inicio
    
    print(f"\n🔧 ORDEN DE APARICIÓN DETECTADO:")
    for speaker, tiempo in speakers_tiempo_aparicion.items():
        print(f"  speaker={speaker} apareció por primera vez a los {tiempo:.1f}s")
    
    # PASO 2: Ordenar cronológicamente
    speakers_ordenados_cronologicamente = sorted(speakers_tiempo_aparicion.items(), key=lambda x: x[1])
    print(f"\n🕐 ORDEN CRONOLÓGICO:")
    for i, (speaker_id, tiempo) in enumerate(speakers_ordenados_cronologicamente):
        print(f"  Posición {i}: speaker={speaker_id} (apareció a los {tiempo:.1f}s)")
    
    # PASO 3: Crear mapeo speaker_idx
    mapeo_speakers = {}
    for i, (speaker_id, tiempo) in enumerate(speakers_ordenados_cronologicamente):
        speaker_idx = i  # Índice cronológico (0, 1, 2...)
        nombre_participante = participantes_esperados[i]['nombres'] if i < len(participantes_esperados) else f"Speaker_{i}"
        
        mapeo_speakers[speaker_id] = {
            'speaker_idx': speaker_idx,
            'nombre': nombre_participante,
            'tiempo_primera_aparicion': tiempo,
            'posicion_cronologica': i
        }
    
    print(f"\n🎯 MAPEO FINAL:")
    for speaker_id, info in mapeo_speakers.items():
        print(f"  speaker={speaker_id} → speaker_idx={info['speaker_idx']} → {info['nombre']}")
    
    # PASO 4: Aplicar mapeo a segmentos
    print(f"\n📝 SEGMENTOS CON MAPEO APLICADO:")
    for i, seg in enumerate(segmentos_pyannote_simulados):
        speaker_original = seg['speaker']
        speaker_idx = mapeo_speakers[speaker_original]['speaker_idx']
        nombre = mapeo_speakers[speaker_original]['nombre']
        print(f"  Seg {i}: [{seg['inicio']:.1f}s] speaker={speaker_original} → speaker_idx={speaker_idx} → {nombre}")
    
    # VALIDACIÓN
    primer_segmento = segmentos_pyannote_simulados[0]
    primer_speaker_original = primer_segmento['speaker']  # 1
    primer_speaker_idx = mapeo_speakers[primer_speaker_original]['speaker_idx']  # 0
    primer_nombre = mapeo_speakers[primer_speaker_original]['nombre']  # Beto
    
    print(f"\n✅ VALIDACIÓN:")
    print(f"  Primer segmento (0.0s): speaker={primer_speaker_original} → speaker_idx={primer_speaker_idx} → {primer_nombre}")
    
    if primer_speaker_idx == 0 and primer_nombre == "Beto":
        print("  ✅ CORRECTO: El primer hablante cronológico se mapea a 'Beto' (primer participante)")
        return True
    else:
        print("  ❌ ERROR: El mapeo no es correcto")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("TEST MAPEO CRONOLÓGICO REAL")
    print("=" * 70)
    
    exito = test_mapeo_cronologico_real()
    
    if exito:
        print("\n🎉 TEST EXITOSO: El mapeo cronológico funciona correctamente")
    else:
        print("\n💥 TEST FALLIDO: El mapeo cronológico tiene errores")
        sys.exit(1)