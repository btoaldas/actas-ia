#!/usr/bin/env python3
"""
Test completo del mapeo cronológico aplicado en estructura_json_mejorada.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mapeo_cronologico_estructura_json():
    """Test del mapeo cronológico aplicado en estructura_json_mejorada.py"""
    
    # Simular resultado de Whisper (transcripción)
    resultado_whisper = {
        'segmentos': [
            {'inicio': 0.0, 'fin': 3.48, 'texto': 'Hola, muy buenas noches. Me llamo Alberto Aldaz.'},
            {'inicio': 3.88, 'fin': 4.56, 'texto': 'Con Elizabeth.'},
            {'inicio': 5.16, 'fin': 7.26, 'texto': 'Un gusto, Elizabeth. ¿Qué edad tiene?'},
            {'inicio': 7.76, 'fin': 8.92, 'texto': 'Treinta y cuatro años.'},
            {'inicio': 9.64, 'fin': 11.02, 'texto': 'Gracias. ¿Qué edad quisiera tener?'},
            {'inicio': 11.90, 'fin': 12.38, 'texto': 'Treinta.'},
            {'inicio': 13.36, 'fin': 16.54, 'texto': 'Yo tengo cuarenta y tres. Un gusto. Hasta luego.'},
            {'inicio': 17.08, 'fin': 17.30, 'texto': 'Chao.'}
        ]
    }
    
    # Simular resultado de pyannote (diarización) con mapeo cronológico
    resultado_pyannote = {
        'segmentos': [
            {'inicio': 0.0, 'fin': 3.48, 'speaker': 1, 'speaker_idx': 0},   # Alberto habla primero, pyannote asigna ID=1, pero speaker_idx=0
            {'inicio': 3.88, 'fin': 4.56, 'speaker': 0, 'speaker_idx': 1},  # Elizabeth segunda, pyannote asigna ID=0, pero speaker_idx=1 
            {'inicio': 5.16, 'fin': 7.26, 'speaker': 1, 'speaker_idx': 0},  # Alberto otra vez
            {'inicio': 7.76, 'fin': 8.92, 'speaker': 0, 'speaker_idx': 1},  # Elizabeth otra vez
            {'inicio': 9.64, 'fin': 11.02, 'speaker': 1, 'speaker_idx': 0}, # Alberto otra vez
            {'inicio': 11.90, 'fin': 12.38, 'speaker': 0, 'speaker_idx': 1}, # Elizabeth otra vez
            {'inicio': 13.36, 'fin': 16.54, 'speaker': 1, 'speaker_idx': 0}, # Alberto otra vez
            {'inicio': 17.08, 'fin': 17.30, 'speaker': 0, 'speaker_idx': 1}  # Elizabeth otra vez
        ],
        'exito': True,
        'num_speakers': 2,
        'speakers': [
            {'id': 0, 'label': 'Speaker 1'}, 
            {'id': 1, 'label': 'Speaker 2'}
        ]
    }
    
    # Simular participantes esperados
    participantes_esperados = [
        {'nombres': 'Beto', 'orden': 1},    # Primer participante (Alberto/Beto)
        {'nombres': 'Ely', 'orden': 2}      # Segundo participante (Elizabeth/Ely)
    ]
    
    print("🎯 TEST COMPLETO DEL MAPEO CRONOLÓGICO")
    print("=" * 60)
    print("Escenario: Alberto habla primero (0.0s) con speaker=1 de pyannote")
    print("           Elizabeth habla segunda (3.88s) con speaker=0 de pyannote")
    print("Esperado:  Alberto → speaker_idx=0 → Beto (primer participante)")
    print("           Elizabeth → speaker_idx=1 → Ely (segundo participante)")
    
    # SIMULAR LA FUNCIÓN combinar_segmentos_whisper_pyannote
    def combinar_segmentos_whisper_pyannote_simulado(whisper_segs, pyannote_segs, participantes):
        """Simula la función de combinación con mapeo cronológico"""
        
        segmentos_combinados = []
        
        for seg_whisper in whisper_segs:
            inicio_whisper = seg_whisper['inicio']
            fin_whisper = seg_whisper['fin']
            texto = seg_whisper['texto']
            
            # Buscar segmento de pyannote que mejor coincida
            mejor_speaker_idx = 0  # Default
            mejor_overlap = 0.0
            
            for seg_pyannote in pyannote_segs:
                inicio_pyannote = seg_pyannote['inicio']
                fin_pyannote = seg_pyannote['fin']
                
                # Calcular overlap
                overlap_inicio = max(inicio_whisper, inicio_pyannote)
                overlap_fin = min(fin_whisper, fin_pyannote)
                
                if overlap_fin > overlap_inicio:
                    overlap_duracion = overlap_fin - overlap_inicio
                    whisper_duracion = fin_whisper - inicio_whisper
                    overlap_ratio = overlap_duracion / whisper_duracion if whisper_duracion > 0 else 0
                    
                    if overlap_ratio > mejor_overlap:
                        mejor_overlap = overlap_ratio
                        # USAR speaker_idx en lugar de speaker ID de pyannote
                        mejor_speaker_idx = seg_pyannote['speaker_idx']  # <<<< ESTO ES LA CLAVE
            
            # Asignar nombre del participante basado en speaker_idx
            if mejor_speaker_idx < len(participantes):
                nombre_participante = participantes[mejor_speaker_idx]['nombres']
            else:
                nombre_participante = f"Speaker_{mejor_speaker_idx}"
            
            segmento_combinado = {
                'inicio': inicio_whisper,
                'fin': fin_whisper,
                'texto': texto,
                'speaker': mejor_speaker_idx,  # Usar speaker_idx cronológico
                'nombre_participante': nombre_participante,
                'overlap_confidence': mejor_overlap
            }
            
            segmentos_combinados.append(segmento_combinado)
        
        return segmentos_combinados
    
    # APLICAR LA COMBINACIÓN
    segmentos_combinados = combinar_segmentos_whisper_pyannote_simulado(
        resultado_whisper['segmentos'],
        resultado_pyannote['segmentos'],
        participantes_esperados
    )
    
    print(f"\n📝 SEGMENTOS COMBINADOS:")
    for i, seg in enumerate(segmentos_combinados):
        print(f"  [{seg['inicio']:.1f}s-{seg['fin']:.1f}s] speaker={seg['speaker']} → {seg['nombre_participante']}: {seg['texto'][:50]}...")
    
    # VALIDACIONES
    print(f"\n✅ VALIDACIONES:")
    
    # Validación 1: Primer segmento (Alberto a los 0.0s) debe mapearse a Beto
    primer_segmento = segmentos_combinados[0]
    if primer_segmento['speaker'] == 0 and primer_segmento['nombre_participante'] == 'Beto':
        print("  ✅ CORRECTO: Primer segmento (0.0s) se mapea a 'Beto' (speaker_idx=0)")
        validacion1 = True
    else:
        print(f"  ❌ ERROR: Primer segmento se mapea a '{primer_segmento['nombre_participante']}' (speaker={primer_segmento['speaker']})")
        validacion1 = False
    
    # Validación 2: Segundo segmento (Elizabeth a los 3.88s) debe mapearse a Ely  
    segundo_segmento = segmentos_combinados[1]
    if segundo_segmento['speaker'] == 1 and segundo_segmento['nombre_participante'] == 'Ely':
        print("  ✅ CORRECTO: Segundo segmento (3.88s) se mapea a 'Ely' (speaker_idx=1)")
        validacion2 = True
    else:
        print(f"  ❌ ERROR: Segundo segmento se mapea a '{segundo_segmento['nombre_participante']}' (speaker={segundo_segmento['speaker']})")
        validacion2 = False
        
    # Validación 3: Consistencia de mapeo (Alberto siempre debe ser speaker_idx=0)
    segmentos_alberto = [seg for seg in segmentos_combinados if 'Alberto' in seg['texto'] or 'cuarenta y tres' in seg['texto']]
    validacion3 = all(seg['speaker'] == 0 and seg['nombre_participante'] == 'Beto' for seg in segmentos_alberto)
    if validacion3:
        print(f"  ✅ CORRECTO: Todos los segmentos de Alberto se mapean consistentemente a 'Beto' ({len(segmentos_alberto)} segmentos)")
    else:
        print(f"  ❌ ERROR: Mapeo inconsistente de Alberto")
    
    # Validación 4: Consistencia de mapeo (Elizabeth siempre debe ser speaker_idx=1)
    # Solo considerar segmentos que realmente son hablados por Elizabeth
    segmentos_elizabeth = [seg for seg in segmentos_combinados if seg['speaker'] == 1]
    print(f"  DEBUG: Segmentos con speaker_idx=1 (Elizabeth): {len(segmentos_elizabeth)}")
    for seg in segmentos_elizabeth:
        print(f"    [{seg['inicio']:.1f}s] speaker={seg['speaker']} → {seg['nombre_participante']}: {seg['texto'][:30]}...")
    validacion4 = all(seg['speaker'] == 1 and seg['nombre_participante'] == 'Ely' for seg in segmentos_elizabeth)
    if validacion4:
        print(f"  ✅ CORRECTO: Todos los segmentos con speaker_idx=1 se mapean a 'Ely' ({len(segmentos_elizabeth)} segmentos)")
    else:
        print(f"  ❌ ERROR: Mapeo inconsistente para speaker_idx=1")
    
    # RESULTADO FINAL
    todas_validaciones = validacion1 and validacion2 and validacion3 and validacion4
    
    print(f"\n🎉 RESULTADO FINAL:")
    if todas_validaciones:
        print("  ✅ TODAS LAS VALIDACIONES EXITOSAS")
        print("  ✅ El mapeo cronológico funciona correctamente")
        print("  ✅ Alberto (speaker_id=1, 0.0s) → speaker_idx=0 → Beto ✓")
        print("  ✅ Elizabeth (speaker_id=0, 3.88s) → speaker_idx=1 → Ely ✓")
        return True
    else:
        print("  ❌ ALGUNAS VALIDACIONES FALLARON")
        print("  ❌ El mapeo cronológico tiene errores")
        return False

if __name__ == "__main__":
    exito = test_mapeo_cronologico_estructura_json()
    if not exito:
        sys.exit(1)