#!/usr/bin/env python3
"""
Debug script para probar estructura_simple_directa en aislamiento
"""

import os
import sys
import django
import traceback

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
from apps.transcripcion.estructura_simple_directa import generar_estructura_simple

def debug_estructura(transcripcion_id):
    """Debug de estructura_simple_directa con transcripción real"""
    
    print(f"🔍 DEBUG ESTRUCTURA SIMPLE - Transcripción {transcripcion_id}")
    print("=" * 70)
    
    try:
        # Obtener transcripción
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        procesamiento_audio = transcripcion.procesamiento_audio
        
        print(f"✅ Datos cargados:")
        print(f"   - Transcripción ID: {transcripcion.id}")
        print(f"   - Audio ID: {procesamiento_audio.id}")
        print(f"   - Participantes: {procesamiento_audio.participantes_detallados}")
        
        # Crear datos simulados para whisper (basado en los logs)
        resultado_whisper = {
            'segmentos': [
                {'start': 0.0, 'end': 3.5, 'text': 'Hola, muy buenas noches. Me llamo Alberto Aldaz. Un gusto. ¿Con quién tengo el gusto?'},
                {'start': 3.9, 'end': 4.6, 'text': 'Con Elizabeth.'},
                {'start': 5.22, 'end': 7.28, 'text': 'Un gusto, Elizabeth. ¿Qué edad tiene?'},
                {'start': 7.8, 'end': 8.94, 'text': 'Treinta y cuatro años.'},
                {'start': 9.66, 'end': 11.04, 'text': 'Gracias. ¿Qué edad quisiera tener?'},
                {'start': 11.9, 'end': 12.42, 'text': 'Treinta.'},
                {'start': 13.4, 'end': 15.16, 'text': 'Yo tengo cuarenta y tres. Un gusto.'},
                {'start': 16.08, 'end': 16.56, 'text': 'Hasta luego.'},
                {'start': 17.12, 'end': 17.46, 'text': 'Chao.'}
            ]
        }
        
        # Crear datos simulados para pyannote 
        resultado_pyannote = {
            'exito': True,
            'speakers_detectados': 2,
            'segmentos_hablantes': [
                {'inicio': 0.0, 'fin': 3.5, 'speaker': 0, 'speaker_name': 'SPEAKER_00'},
                {'inicio': 3.9, 'fin': 4.6, 'speaker': 1, 'speaker_name': 'SPEAKER_01'},
                {'inicio': 5.22, 'fin': 7.28, 'speaker': 0, 'speaker_name': 'SPEAKER_00'},
                {'inicio': 7.8, 'fin': 8.94, 'speaker': 1, 'speaker_name': 'SPEAKER_01'},
                {'inicio': 9.66, 'fin': 11.04, 'speaker': 0, 'speaker_name': 'SPEAKER_00'},
                {'inicio': 11.9, 'fin': 12.42, 'speaker': 1, 'speaker_name': 'SPEAKER_01'},
                {'inicio': 13.4, 'fin': 15.16, 'speaker': 0, 'speaker_name': 'SPEAKER_00'},
                {'inicio': 16.08, 'fin': 16.56, 'speaker': 0, 'speaker_name': 'SPEAKER_00'},
                {'inicio': 17.12, 'fin': 17.46, 'speaker': 1, 'speaker_name': 'SPEAKER_01'},
            ]
        }
        
        print(f"📝 Datos preparados:")
        print(f"   - Whisper segmentos: {len(resultado_whisper['segmentos'])}")
        print(f"   - Pyannote segmentos: {len(resultado_pyannote['segmentos_hablantes'])}")
        
        # INTENTAR EJECUTAR LA FUNCIÓN PROBLEMÁTICA
        print(f"\n🔧 Ejecutando generar_estructura_simple()...")
        
        resultado = generar_estructura_simple(
            resultado_whisper=resultado_whisper,
            resultado_pyannote=resultado_pyannote,
            procesamiento_audio=procesamiento_audio,
            transcripcion=transcripcion
        )
        
        print(f"\n✅ ÉXITO! Estructura generada:")
        print(f"   - Cabecera: {'cabecera' in resultado}")
        print(f"   - Conversación: {len(resultado.get('conversacion', []))} segmentos")
        print(f"   - Texto estructurado: {'texto_estructurado' in resultado}")
        print(f"   - Metadata: {'metadata' in resultado}")
        
        if 'conversacion' in resultado and len(resultado['conversacion']) > 0:
            primer_seg = resultado['conversacion'][0]
            print(f"\n📝 Primer segmento:")
            print(f"   - inicio: {primer_seg.get('inicio')}")
            print(f"   - hablante: {primer_seg.get('hablante')}")
            print(f"   - texto: {primer_seg.get('texto', '')[:50]}...")
            
        return resultado
        
    except Exception as e:
        print(f"\n❌ ERROR CAPTURADO:")
        print(f"   - Tipo: {type(e).__name__}")
        print(f"   - Mensaje: {str(e)}")
        print(f"\n📋 STACK TRACE COMPLETO:")
        traceback.print_exc()
        
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        transcripcion_id = int(sys.argv[1])
        debug_estructura(transcripcion_id)
    else:
        print("Uso: python debug_estructura_directa.py 97")