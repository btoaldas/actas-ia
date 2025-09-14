#!/usr/bin/env python3
"""
Script para reproducir y corregir el problema de mapeo de speakers
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion, ProcesamientoAudio, EstadoTranscripcion

def simular_problema_mapeo():
    print("🎯 SIMULANDO PROBLEMA DE MAPEO DE SPEAKERS")
    print("=" * 60)
    
    # Obtener el último procesamiento de audio
    procesamiento = ProcesamientoAudio.objects.order_by('-id').first()
    if not procesamiento:
        print("❌ No hay procesamiento de audio")
        return
    
    print(f"🎵 Procesamiento de Audio ID: {procesamiento.id}")
    participantes = procesamiento.participantes_detallados or []
    print(f"👥 Participantes predefinidos: {participantes}")
    
    # 1. SIMULAR RESULTADO DE WHISPER (como viene del ejemplo real)
    resultado_whisper = {
        "exito": True,
        "segmentos": [
            {
                "start": 0.0,
                "end": 3.48,
                "text": "Hola, muy buenas noches. Me llamo Alberto Aldaz. Un gusto. ¿Con quién tengo el gusto?",
                "confidence": 0.7198641765704584
            },
            {
                "start": 3.88,
                "end": 4.56,
                "text": "Con Elizabeth.",
                "confidence": 0.3
            },
            {
                "start": 5.16,
                "end": 7.26,
                "text": "Un gusto, Elizabeth. ¿Qué edad tiene?",
                "confidence": 0.3
            },
            {
                "start": 7.76,
                "end": 8.92,
                "text": "Treinta y cuatro años.",
                "confidence": 0.3
            }
        ],
        "metadatos_modelo": {
            "modelo": "whisper-medium",
            "device": "cpu",
            "languages": ["es"]
        },
        "parametros_aplicados": {
            "modelo_whisper": "medium",
            "idioma_principal": "es",
            "temperatura": 0.0
        }
    }
    
    # 2. SIMULAR RESULTADO DE PYANNOTE CORREGIDO
    # Ahora debe enviar los speakers en orden cronológico de aparición
    from collections import OrderedDict
    resultado_pyannote = {
        "exito": True,
        "hablantes": OrderedDict([
            ("SPEAKER_01", {
                "id": 1,
                "label": "Speaker 1", 
                "tiempo_primera_aparicion": 0.0  # Aparece primero
            }),
            ("SPEAKER_00", {
                "id": 0,
                "label": "Speaker 2",
                "tiempo_primera_aparicion": 3.88  # Aparece segundo
            })
        ]),
        "segmentos_hablantes": [
            {
                "inicio": 0.0,
                "fin": 3.48,
                "speaker": "SPEAKER_01",  # El primer segmento tiene speaker 1
                "confianza": 0.72
            },
            {
                "inicio": 3.88,
                "fin": 4.56,
                "speaker": "SPEAKER_00",  # El segundo segmento tiene speaker 0
                "confianza": 0.3
            },
            {
                "inicio": 5.16,
                "fin": 7.26,
                "speaker": "SPEAKER_01",  # Alberto sigue siendo speaker 1
                "confianza": 0.3
            },
            {
                "inicio": 7.76,
                "fin": 8.92,
                "speaker": "SPEAKER_00",  # Elizabeth sigue siendo speaker 0
                "confianza": 0.3
            }
        ],
        "num_hablantes": 2
    }
    
    print("\n🔍 ANÁLISIS DEL PROBLEMA:")
    print("Participantes JSON del usuario:")
    for i, p in enumerate(participantes):
        print(f"  {i}. {p.get('nombres', 'Sin nombre')} (índice {i})")
    
    print("\nSegmentos de Whisper + Pyannote:")
    for i, (seg_w, seg_p) in enumerate(zip(resultado_whisper["segmentos"], resultado_pyannote["segmentos_hablantes"])):
        print(f"  {i+1}. [{seg_w['start']:.1f}s] Speaker {seg_p['speaker']} dice: \"{seg_w['text'][:50]}...\"")
    
    print("\n❌ PROBLEMA ACTUAL:")
    print("  - El primer segmento (Alberto dice su nombre) tiene speaker SPEAKER_01")
    print("  - Pero en el mapeo por índice: SPEAKER_00 → Beto, SPEAKER_01 → Ely")
    print("  - RESULTADO: Alberto aparece como Ely ❌")
    
    print("\n✅ SOLUCIÓN APLICADA:")
    print("  - pyannote_helper.py ahora envía speakers en orden cronológico")
    print("  - Primer speaker en aparecer (SPEAKER_01 a 0.0s) → Primero en el Dict")
    print("  - Segundo speaker en aparecer (SPEAKER_00 a 3.88s) → Segundo en el Dict")
    print("  - estructura_json_mejorada.py mapea 1:1 sin reordenar")
    
    # 3. PROBAR LA CORRECCIÓN
    from apps.transcripcion.estructura_json_mejorada import mapear_hablantes_predefinidos
    
    print("\n🔧 PROBANDO CORRECCIÓN:")
    
    # Ahora los hablantes vienen en orden cronológico desde pyannote_helper
    hablantes_detectados = resultado_pyannote["hablantes"]  # Ya ordenado cronológicamente
    
    mapeo_corregido = mapear_hablantes_predefinidos(hablantes_detectados, participantes)
    
    print("Mapeo corregido:")
    for speaker_id, info in mapeo_corregido.items():
        print(f"  {speaker_id} → {info['label']} (ID final: {info['id']})")
    
    # 4. VERIFICAR RESULTADO
    print("\n🎯 VERIFICACIÓN:")
    primer_speaker = "SPEAKER_01"  # El que habla primero cronológicamente
    if primer_speaker in mapeo_corregido:
        nombre_asignado = mapeo_corregido[primer_speaker]['label']
        print(f"  Primer speaker ({primer_speaker}) → {nombre_asignado}")
        if 'Beto' in nombre_asignado:
            print("  ✅ CORRECTO: Alberto/Beto aparece como primer hablante")
        else:
            print("  ❌ INCORRECTO: Aún hay problema en el mapeo")
    
    # 5. VERIFICAR QUE EL ORDEN EN EL DICT ES CRONOLÓGICO
    print("\n📋 ORDEN EN EL DICCIONARIO:")
    for i, (speaker_id, speaker_info) in enumerate(hablantes_detectados.items()):
        tiempo = speaker_info.get('tiempo_primera_aparicion', 'N/A')
        print(f"  Posición {i+1}: {speaker_id} (aparición: {tiempo}s)")
        
    print("\n💡 RESUMEN:")
    speaker_ids = list(hablantes_detectados.keys())
    if len(speaker_ids) >= 2:
        primer_id = speaker_ids[0]
        segundo_id = speaker_ids[1]
        primer_nombre = mapeo_corregido[primer_id]['label']
        segundo_nombre = mapeo_corregido[segundo_id]['label']
        print(f"  - {primer_id} (posición 1 en dict) → {primer_nombre}")
        print(f"  - {segundo_id} (posición 2 en dict) → {segundo_nombre}")
        
        if 'Beto' in primer_nombre and 'Ely' in segundo_nombre:
            print("  🎉 ¡MAPEO CORRECTO!")
        else:
            print("  ❌ Mapeo aún incorrecto")
    
    return resultado_whisper, resultado_pyannote

if __name__ == "__main__":
    simular_problema_mapeo()