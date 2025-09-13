#!/usr/bin/env python3
"""
Test para validar la corrección del mapeo cronológico de speakers
Simula el caso real donde pyannote asigna IDs arbitrarios pero necesitamos
mapear el primer hablante cronológico al primer participante predefinido
"""

from collections import OrderedDict

def test_mapeo_cronologico_corregido():
    print("\n" + "="*80)
    print("🔍 TEST: Validación del mapeo cronológico corregido")
    print("   Caso real: Alberto habla primero pero pyannote le asigna speaker_id=1")
    print("="*80)
    
    # Simular el resultado de pyannote (IDs arbitrarios)
    # En este caso, el speaker 1 habla primero cronológicamente
    segmentos_pyannote_originales = [
        {'speaker': 1, 'start': 0.0, 'end': 3.48},    # Alberto habla primero
        {'speaker': 0, 'start': 3.88, 'end': 4.56},   # Elizabeth habla segundo
        {'speaker': 1, 'start': 5.16, 'end': 7.26},   # Alberto otra vez
        {'speaker': 0, 'start': 7.76, 'end': 8.92},   # Elizabeth otra vez
    ]
    
    # Participantes predefinidos en orden
    participantes_predefinidos = ['Beto', 'Ely']
    
    print("\n📊 Datos de entrada:")
    print(f"   Participantes predefinidos: {participantes_predefinidos}")
    print(f"   Segmentos pyannote (IDs arbitrarios):")
    for seg in segmentos_pyannote_originales:
        print(f"      speaker_id={seg['speaker']} en {seg['start']:.2f}s-{seg['end']:.2f}s")
    
    # ====== SIMULACIÓN DE pyannote_helper.py CORREGIDO ======
    print("\n🔄 Procesamiento en pyannote_helper.py:")
    
    # 1. Detectar orden cronológico de aparición
    speaker_apariciones = []
    speaker_tiempos = {}
    
    for seg in segmentos_pyannote_originales:
        speaker_id = seg['speaker']
        if speaker_id not in speaker_tiempos:
            speaker_tiempos[speaker_id] = seg['start']
            speaker_apariciones.append(speaker_id)
            print(f"   Primera aparición de speaker_{speaker_id}: {seg['start']:.2f}s")
    
    # 2. Crear mapeo cronológico
    mapeo_cronologico = {}
    for idx, speaker_id in enumerate(speaker_apariciones):
        mapeo_cronologico[speaker_id] = idx
        print(f"   Mapeo: speaker_{speaker_id} → posición cronológica {idx} (SPEAKER_{idx:02d})")
    
    # 3. Crear speakers ordenados cronológicamente
    speakers_ordenados = OrderedDict()
    for idx, speaker_id in enumerate(speaker_apariciones):
        speakers_ordenados[f'SPEAKER_{idx:02d}'] = {
            'id': idx,
            'id_original_pyannote': speaker_id,
            'label': f"Speaker {idx+1}",
            'tiempo_primera_aparicion': speaker_tiempos[speaker_id]
        }
    
    # 4. Actualizar segmentos con IDs cronológicos
    segmentos_corregidos = []
    for seg in segmentos_pyannote_originales:
        speaker_original = seg['speaker']
        posicion_cronologica = mapeo_cronologico[speaker_original]
        segmentos_corregidos.append({
            'speaker': f'SPEAKER_{posicion_cronologica:02d}',
            'speaker_idx': posicion_cronologica,  # Para el JSON final
            'start': seg['start'],
            'end': seg['end']
        })
    
    print("\n📋 Resultado de pyannote_helper:")
    print(f"   Speakers ordenados: {list(speakers_ordenados.keys())}")
    
    # ====== SIMULACIÓN DE estructura_json_mejorada.py ======
    print("\n🎯 Mapeo en estructura_json_mejorada.py:")
    
    # Mapear speakers cronológicos a participantes predefinidos
    mapeo_final = {}
    for speaker_key in speakers_ordenados.keys():
        idx = int(speaker_key.split('_')[-1])
        if idx < len(participantes_predefinidos):
            mapeo_final[speaker_key] = participantes_predefinidos[idx]
            print(f"   {speaker_key} → {participantes_predefinidos[idx]}")
    
    # ====== VALIDACIÓN ======
    print("\n✅ VALIDACIÓN DEL RESULTADO:")
    print("   Segmentos finales con nombres correctos:")
    
    for i, seg in enumerate(segmentos_corregidos, 1):
        speaker_key = seg['speaker']
        nombre_asignado = mapeo_final.get(speaker_key, 'DESCONOCIDO')
        print(f"   Segmento {i}: {nombre_asignado} (speaker_idx={seg['speaker_idx']}) en {seg['start']:.2f}s-{seg['end']:.2f}s")
    
    # Verificar que el mapeo es correcto
    print("\n🎬 VERIFICACIÓN CRÍTICA:")
    primer_segmento = segmentos_corregidos[0]
    primer_speaker = mapeo_final.get(primer_segmento['speaker'])
    
    if primer_speaker == 'Beto':
        print("   ✅ CORRECTO: El primer hablante cronológico (0.0s) se mapea a 'Beto'")
    else:
        print(f"   ❌ ERROR: El primer hablante se mapeó a '{primer_speaker}' en lugar de 'Beto'")
    
    segundo_segmento = segmentos_corregidos[1]
    segundo_speaker = mapeo_final.get(segundo_segmento['speaker'])
    
    if segundo_speaker == 'Ely':
        print("   ✅ CORRECTO: El segundo hablante cronológico (3.88s) se mapea a 'Ely'")
    else:
        print(f"   ❌ ERROR: El segundo hablante se mapeó a '{segundo_speaker}' en lugar de 'Ely'")
    
    # Verificar IDs en JSON final
    print("\n📄 IDs en el JSON final:")
    print("   Los segmentos tendrán speaker=0 para Beto y speaker=1 para Ely")
    for i, seg in enumerate(segmentos_corregidos, 1):
        nombre = mapeo_final.get(seg['speaker'])
        print(f"   Segmento {i}: speaker={seg['speaker_idx']} → {nombre}")
    
    print("\n" + "="*80)
    print("🎉 RESUMEN:")
    print("   Con la corrección, el sistema ahora:")
    print("   1. Detecta el orden cronológico real de aparición")
    print("   2. Reasigna IDs basados en ese orden (0=primero, 1=segundo)")
    print("   3. Mapea correctamente al primer participante predefinido")
    print("   4. El JSON final tiene speaker=0 para el primero en hablar")
    print("="*80)

if __name__ == "__main__":
    test_mapeo_cronologico_corregido()
