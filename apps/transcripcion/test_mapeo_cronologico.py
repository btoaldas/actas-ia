#!/usr/bin/env python3
"""
Test específico para validar mapeo cronológico correcto:

JSON del usuario:
1. Alberto (hablante 1)
2. Scarlleth (hablante 2) 
3. Ely (hablante 3)

Audio simulado:
1º habla alguien (0-5s) → debe ser Alberto
2º habla alguien diferente (10-15s) → debe ser Scarlleth
3º habla el primero otra vez (20-25s) → debe ser Alberto nuevamente
4º habla alguien nuevo (30-35s) → debe ser Ely

Resultado esperado:
- SPEAKER_00 (1ª aparición cronológica) → Alberto
- SPEAKER_01 (2ª aparición cronológica) → Scarlleth
- SPEAKER_02 (3ª aparición cronológica) → Ely
"""

import os
import sys
import django

# Setup Django path
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(app_dir)
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_mapeo_cronologico():
    print("🕐 TEST: Mapeo cronológico - Orden de aparición = Orden JSON")
    print()
    
    # JSON del usuario con participantes esperados
    participantes_json = [
        {
            'orden': 1,
            'nombres': 'Alberto',
            'apellidos': 'González',
            'nombre_completo': 'Alberto González',
            'cargo': 'Alcalde',
            'id': 'hablante_1'
        },
        {
            'orden': 2,
            'nombres': 'Scarlleth',
            'apellidos': 'Martínez',
            'nombre_completo': 'Scarlleth Martínez',
            'cargo': 'Secretaria',
            'id': 'hablante_2'
        },
        {
            'orden': 3,
            'nombres': 'Ely',
            'apellidos': 'Rodríguez',
            'nombre_completo': 'Ely Rodríguez',
            'cargo': 'Concejal',
            'id': 'hablante_3'
        }
    ]
    
    print("👥 PARTICIPANTES JSON DEL USUARIO:")
    for i, p in enumerate(participantes_json):
        print(f"   {i+1}. {p['nombre_completo']} ({p['cargo']})")
    
    print("\n🎤 AUDIO SIMULADO - Orden cronológico de aparición:")
    print("   0-5s:   Alguien habla por primera vez")
    print("   10-15s: Alguien DIFERENTE habla por primera vez") 
    print("   20-25s: El PRIMERO vuelve a hablar")
    print("   30-35s: Alguien NUEVO habla por primera vez")
    
    print("\n💭 EXPECTATIVA:")
    print("   1ª aparición cronológica → Alberto (pos 1 JSON)")
    print("   2ª aparición cronológica → Scarlleth (pos 2 JSON)")
    print("   3ª aparición cronológica → Ely (pos 3 JSON)")
    
    try:
        from apps.transcripcion.pyannote_helper import PyannoteProcessor
        from pyannote.core import Annotation, Segment
        
        # Simular detección de pyannote con el patrón cronológico
        diarizacion_simulada = Annotation()
        
        # Simular que pyannote detecta 3 speakers diferentes en este orden cronológico:
        # SPEAKER_00 aparece primero (0s), luego nuevamente (20s)
        # SPEAKER_01 aparece segundo (10s)
        # SPEAKER_02 aparece tercero (30s)
        
        diarizacion_simulada[Segment(0.0, 5.0)] = "SPEAKER_00"   # 1ª aparición cronológica
        diarizacion_simulada[Segment(10.0, 15.0)] = "SPEAKER_01" # 2ª aparición cronológica
        diarizacion_simulada[Segment(20.0, 25.0)] = "SPEAKER_00" # SPEAKER_00 vuelve a hablar
        diarizacion_simulada[Segment(30.0, 35.0)] = "SPEAKER_02" # 3ª aparición cronológica
        
        print("\n🤖 DETECCIÓN SIMULADA DE PYANNOTE:")
        print("   SPEAKER_00: 0-5s (1ª aparición), 20-25s (repite)")
        print("   SPEAKER_01: 10-15s (2ª aparición)")
        print("   SPEAKER_02: 30-35s (3ª aparición)")
        
        # Configuración con mapeo cronológico
        configuracion = {
            'tipo_mapeo_speakers': 'orden_json',
            'participantes_esperados': participantes_json
        }
        
        processor = PyannoteProcessor()
        resultado = processor._procesar_resultado_diarizacion_inteligente(
            diarizacion_simulada,
            participantes_json,
            [],
            configuracion
        )
        
        print("\n🎯 RESULTADO DEL MAPEO CRONOLÓGICO:")
        mapeo = resultado.get('mapeo_speakers', {})
        
        # Verificar mapeo cronológico correcto
        mapeo_esperado = {
            'SPEAKER_00': 'Alberto González',     # 1ª aparición (0s) → 1º en JSON
            'SPEAKER_01': 'Scarlleth Martínez',  # 2ª aparición (10s) → 2º en JSON
            'SPEAKER_02': 'Ely Rodríguez'        # 3ª aparición (30s) → 3º en JSON
        }
        
        mapeo_correcto = True
        for speaker_id, nombre_esperado in mapeo_esperado.items():
            if speaker_id in mapeo:
                nombre_obtenido = mapeo[speaker_id]['nombre']
                tiempo_aparicion = mapeo[speaker_id]['tiempo_primera_aparicion']
                orden_cronologico = mapeo[speaker_id].get('orden_cronologico', 'N/A')
                
                print(f"   {speaker_id} → {nombre_obtenido}")
                print(f"     ├─ 1ª aparición: {tiempo_aparicion}s")
                print(f"     └─ Orden cronológico: {orden_cronologico}")
                
                if nombre_obtenido == nombre_esperado:
                    print(f"     ✅ CORRECTO")
                else:
                    print(f"     ❌ ERROR: esperado {nombre_esperado}")
                    mapeo_correcto = False
            else:
                print(f"   ❌ {speaker_id} no encontrado en mapeo")
                mapeo_correcto = False
            print()
        
        if mapeo_correcto:
            print("🎉 MAPEO CRONOLÓGICO FUNCIONANDO CORRECTAMENTE")
            print("   ✅ 1ª aparición (0s) → Alberto González")
            print("   ✅ 2ª aparición (10s) → Scarlleth Martínez") 
            print("   ✅ 3ª aparición (30s) → Ely Rodríguez")
            print()
            print("📋 FLUJO COMPLETO SIMULADO:")
            print("   0-5s:   Alberto habla")
            print("   10-15s: Scarlleth habla")
            print("   20-25s: Alberto habla nuevamente (ya identificado)")
            print("   30-35s: Ely habla")
        else:
            print("❌ ERROR EN MAPEO CRONOLÓGICO")
            
        # Mostrar estructura de segmentos procesados
        segmentos = resultado.get('segmentos_procesados', [])
        print(f"\n📝 SEGMENTOS PROCESADOS ({len(segmentos)}):")
        for i, seg in enumerate(segmentos):
            speaker_original = seg.get('speaker_original', 'unknown')
            speaker_mapeado = mapeo.get(speaker_original, {}).get('nombre', 'Sin mapear')
            inicio = seg.get('inicio', 0)
            fin = seg.get('fin', 0)
            print(f"   {i+1}. {inicio:.1f}s-{fin:.1f}s: {speaker_mapeado} ({speaker_original})")
            
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("🎯 RESUMEN:")
    print("   - pyannote debe detectar EXACTAMENTE 3 speakers")
    print("   - 1ª aparición cronológica → 1er participante JSON")
    print("   - 2ª aparición cronológica → 2do participante JSON")
    print("   - 3ª aparición cronológica → 3er participante JSON")
    print("   - Después identifica correctamente cuando vuelven a hablar")

if __name__ == "__main__":
    test_mapeo_cronologico()