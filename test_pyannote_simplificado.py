#!/usr/bin/env python3
"""
Test del pyannote helper simplificado
"""

import sys
import os
sys.path.append('/app')

def test_pyannote_simplificado():
    """Test del nuevo sistema simplificado"""
    
    print("🎯 TEST PYANNOTE HELPER SIMPLIFICADO")
    print("=" * 50)
    
    # Simular resultado de pyannote (como si funcionara)
    segmentos_pyannote_simulados = [
        {'inicio': 0.0, 'fin': 3.48, 'speaker_id': 'SPEAKER_01', 'duracion': 3.48},
        {'inicio': 3.88, 'fin': 4.56, 'speaker_id': 'SPEAKER_00', 'duracion': 0.68},
        {'inicio': 5.16, 'fin': 7.26, 'speaker_id': 'SPEAKER_01', 'duracion': 2.10},
        {'inicio': 7.76, 'fin': 8.92, 'speaker_id': 'SPEAKER_00', 'duracion': 1.16},
    ]
    
    participantes = [
        {'nombres': 'Beto', 'orden': 1},
        {'nombres': 'Ely', 'orden': 2}
    ]
    
    print("Segmentos simulados de pyannote:")
    for seg in segmentos_pyannote_simulados:
        print(f"  [{seg['inicio']:.1f}s-{seg['fin']:.1f}s] {seg['speaker_id']}")
    
    print(f"\nParticipantes esperados: {[p['nombres'] for p in participantes]}")
    
    # Simular el mapeo cronológico del helper simplificado
    from apps.transcripcion.pyannote_helper_simple import PyannoteProcessor
    
    processor = PyannoteProcessor()
    segmentos_mapeados = processor._mapear_cronologicamente(segmentos_pyannote_simulados, participantes)
    
    print(f"\n📝 SEGMENTOS MAPEADOS:")
    for seg in segmentos_mapeados:
        print(f"  [{seg['inicio']:.1f}s-{seg['fin']:.1f}s] speaker={seg['speaker']} → {seg['speaker_name']} (original: {seg['speaker_id_original']})")
    
    # VALIDACIONES
    print(f"\n✅ VALIDACIONES:")
    
    # El primer segmento (0.0s) debe mapearse al primer participante
    primer_seg = segmentos_mapeados[0]
    if primer_seg['speaker'] == 0 and primer_seg['speaker_name'] == 'Beto':
        print("  ✅ Primer segmento (0.0s) se mapea a 'Beto' (speaker=0)")
        validacion1 = True
    else:
        print(f"  ❌ Primer segmento se mapea a '{primer_seg['speaker_name']}' (speaker={primer_seg['speaker']})")
        validacion1 = False
    
    # El segundo segmento (3.88s) debe mapearse al segundo participante
    segundo_seg = segmentos_mapeados[1]
    if segundo_seg['speaker'] == 1 and segundo_seg['speaker_name'] == 'Ely':
        print("  ✅ Segundo segmento (3.88s) se mapea a 'Ely' (speaker=1)")
        validacion2 = True
    else:
        print(f"  ❌ Segundo segmento se mapea a '{segundo_seg['speaker_name']}' (speaker={segundo_seg['speaker']})")
        validacion2 = False
    
    # Todos los segmentos de SPEAKER_01 deben mapearse a Beto (speaker=0)
    segmentos_speaker01 = [seg for seg in segmentos_mapeados if seg['speaker_id_original'] == 'SPEAKER_01']
    validacion3 = all(seg['speaker'] == 0 and seg['speaker_name'] == 'Beto' for seg in segmentos_speaker01)
    if validacion3:
        print(f"  ✅ Todos los segmentos de SPEAKER_01 se mapean a 'Beto' ({len(segmentos_speaker01)} segmentos)")
    else:
        print(f"  ❌ Mapeo inconsistente para SPEAKER_01")
    
    # Todos los segmentos de SPEAKER_00 deben mapearse a Ely (speaker=1)
    segmentos_speaker00 = [seg for seg in segmentos_mapeados if seg['speaker_id_original'] == 'SPEAKER_00']
    validacion4 = all(seg['speaker'] == 1 and seg['speaker_name'] == 'Ely' for seg in segmentos_speaker00)
    if validacion4:
        print(f"  ✅ Todos los segmentos de SPEAKER_00 se mapean a 'Ely' ({len(segmentos_speaker00)} segmentos)")
    else:
        print(f"  ❌ Mapeo inconsistente para SPEAKER_00")
    
    # RESULTADO FINAL
    todas_validaciones = validacion1 and validacion2 and validacion3 and validacion4
    
    print(f"\n🎉 RESULTADO:")
    if todas_validaciones:
        print("  ✅ MAPEO CRONOLÓGICO SIMPLIFICADO FUNCIONA PERFECTAMENTE")
        print("  ✅ SPEAKER_01 (0.0s primero) → speaker=0 → Beto")
        print("  ✅ SPEAKER_00 (3.88s segundo) → speaker=1 → Ely")
        return True
    else:
        print("  ❌ HAY ERRORES EN EL MAPEO")
        return False

if __name__ == "__main__":
    exito = test_pyannote_simplificado()
    if not exito:
        sys.exit(1)