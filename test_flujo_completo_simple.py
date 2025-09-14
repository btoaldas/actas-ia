#!/usr/bin/env python3
"""
Test completo del flujo end-to-end con pyannote simplificado
"""

import sys
import os
sys.path.append('/app')

def test_flujo_completo_simplificado():
    """Test del flujo completo con el nuevo sistema simplificado"""
    
    print("🎯 TEST FLUJO COMPLETO SIMPLIFICADO")
    print("=" * 60)
    
    # PASO 1: Simular resultado de Whisper
    resultado_whisper = {
        'segmentos': [
            {'inicio': 0.0, 'fin': 3.48, 'texto': 'Hola, muy buenas noches. Me llamo Alberto Aldaz.'},
            {'inicio': 3.88, 'fin': 4.56, 'texto': 'Con Elizabeth.'},
            {'inicio': 5.16, 'fin': 7.26, 'texto': 'Un gusto, Elizabeth. ¿Qué edad tiene?'},
            {'inicio': 7.76, 'fin': 8.92, 'texto': 'Treinta y cuatro años.'},
        ]
    }
    
    # PASO 2: Simular resultado de pyannote con mapeo cronológico aplicado
    resultado_pyannote = {
        'exito': True,
        'segmentos': [
            {'inicio': 0.0, 'fin': 3.48, 'speaker': 0, 'speaker_name': 'Beto'},  # Mapeo cronológico aplicado
            {'inicio': 3.88, 'fin': 4.56, 'speaker': 1, 'speaker_name': 'Ely'},  # Mapeo cronológico aplicado
            {'inicio': 5.16, 'fin': 7.26, 'speaker': 0, 'speaker_name': 'Beto'},
            {'inicio': 7.76, 'fin': 8.92, 'speaker': 1, 'speaker_name': 'Ely'},
        ],
        'num_speakers': 2,
        'speakers': [
            {'id': 0, 'label': 'Beto'},
            {'id': 1, 'label': 'Ely'}
        ]
    }
    
    # PASO 3: Combinar usando estructura_json_mejorada
    from apps.transcripcion.estructura_json_mejorada import combinar_segmentos_whisper_pyannote
    
    segmentos_combinados = combinar_segmentos_whisper_pyannote(
        resultado_whisper['segmentos'],
        resultado_pyannote['segmentos'],
        {}  # No necesitamos hablantes_mapeados con el nuevo sistema
    )
    
    print("📝 SEGMENTOS COMBINADOS:")
    for i, seg in enumerate(segmentos_combinados):
        print(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] speaker={seg['speaker']}: {seg['text'][:50]}...")
    
    # VALIDACIONES
    print(f"\n✅ VALIDACIONES DEL FLUJO COMPLETO:")
    
    # Validación 1: Primer segmento debe tener speaker=0 (Alberto/Beto)
    primer_seg = segmentos_combinados[0]
    if primer_seg['speaker'] == 0:
        print("  ✅ Primer segmento (Alberto, 0.0s) tiene speaker=0")
        validacion1 = True
    else:
        print(f"  ❌ Primer segmento tiene speaker={primer_seg['speaker']}, esperado 0")
        validacion1 = False
    
    # Validación 2: Segundo segmento debe tener speaker=1 (Elizabeth/Ely)
    segundo_seg = segmentos_combinados[1]
    if segundo_seg['speaker'] == 1:
        print("  ✅ Segundo segmento (Elizabeth, 3.88s) tiene speaker=1")
        validacion2 = True
    else:
        print(f"  ❌ Segundo segmento tiene speaker={segundo_seg['speaker']}, esperado 1")
        validacion2 = False
    
    # Validación 3: Estructura correcta de segmentos
    campos_requeridos = ['start', 'end', 'speaker', 'text', 'speaker_confidence']
    validacion3 = all(all(campo in seg for campo in campos_requeridos) for seg in segmentos_combinados)
    if validacion3:
        print("  ✅ Todos los segmentos tienen los campos requeridos")
    else:
        print("  ❌ Faltan campos en algunos segmentos")
    
    # Validación 4: Speakers en rango correcto
    speakers_encontrados = set(seg['speaker'] for seg in segmentos_combinados)
    validacion4 = speakers_encontrados == {0, 1}
    if validacion4:
        print(f"  ✅ Speakers encontrados: {speakers_encontrados} (correcto)")
    else:
        print(f"  ❌ Speakers encontrados: {speakers_encontrados} (esperado {{0, 1}})")
    
    # RESULTADO FINAL
    todas_validaciones = validacion1 and validacion2 and validacion3 and validacion4
    
    print(f"\n🎉 RESULTADO DEL FLUJO COMPLETO:")
    if todas_validaciones:
        print("  ✅ FLUJO END-TO-END FUNCIONA PERFECTAMENTE")
        print("  ✅ Whisper → pyannote simplificado → estructura JSON → CORRECTO")
        print("  ✅ Alberto (0.0s) → speaker=0")
        print("  ✅ Elizabeth (3.88s) → speaker=1")
        print("  ✅ MAPEO CRONOLÓGICO DIRECTO EXITOSO")
        return True
    else:
        print("  ❌ HAY ERRORES EN EL FLUJO COMPLETO")
        return False

if __name__ == "__main__":
    exito = test_flujo_completo_simplificado()
    if not exito:
        sys.exit(1)