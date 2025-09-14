#!/usr/bin/env python3
"""
Script para aplicar el fix de mapeo de participantes directamente 
a los datos existentes de la transcripción 88
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
import json

def fix_mapeo_participantes(transcripcion_id):
    """Aplica el fix de mapeo de participantes a una transcripción existente"""
    
    try:
        t = Transcripcion.objects.get(id=transcripcion_id)
        print(f'=== APLICANDO FIX A TRANSCRIPCION {transcripcion_id} ===')
        print(f'Estado actual: {t.estado}')
        print(f'Audio ID: {t.procesamiento_audio.id}')
        
        # Obtener participantes configurados
        participantes = t.procesamiento_audio.participantes_detallados
        print(f'Participantes configurados: {[p["nombres"] for p in participantes]}')
        
        if not participantes:
            print('❌ No hay participantes configurados')
            return False
        
        # Verificar si hay datos de diarización
        if not t.diarizacion_json or 'segmentos_hablantes' not in t.diarizacion_json:
            print('❌ No hay datos de diarización para procesar')
            return False
        
        segmentos_hablantes = t.diarizacion_json['segmentos_hablantes']
        print(f'Segmentos hablantes disponibles: {len(segmentos_hablantes)}')
        
        if not segmentos_hablantes:
            print('❌ No hay segmentos de hablantes')
            return False
        
        # PASO 1: Generar mapeo de hablantes corregido
        hablantes_mapeados = {}
        for i, participante in enumerate(participantes):
            hablantes_mapeados[str(i)] = {
                'nombre': participante['nombres'], 
                'participante': participante,
                'id': i
            }
        
        print('🎯 MAPEO GENERADO:')
        for speaker_id, info in hablantes_mapeados.items():
            print(f'  Speaker {speaker_id} → {info["nombre"]}')
        
        # PASO 2: Actualizar diarizacion_json con el mapeo correcto
        t.diarizacion_json['hablantes'] = hablantes_mapeados
        
        # PASO 3: Generar hablantes_detectados de los segmentos
        speakers_unicos = set()
        for seg in segmentos_hablantes:
            if 'speaker' in seg:
                speakers_unicos.add(seg['speaker'])
        
        hablantes_detectados = []
        for speaker_num in sorted(speakers_unicos):
            speaker_str = str(speaker_num)
            if speaker_str in hablantes_mapeados:
                hablantes_detectados.append(hablantes_mapeados[speaker_str]['nombre'])
            else:
                hablantes_detectados.append(f'Speaker_{speaker_num}')
        
        t.hablantes_detectados = hablantes_detectados
        print(f'✅ Hablantes detectados actualizados: {hablantes_detectados}')
        
        # PASO 4: Generar conversacion_json básica
        conversacion = []
        segmentos_ordenados = sorted(segmentos_hablantes, key=lambda x: x.get('inicio', 0))
        
        # Obtener texto completo y dividirlo aproximadamente por segmentos
        texto_completo = t.texto_completo or ''
        if texto_completo and len(segmentos_ordenados) > 0:
            # Estrategia simple: dividir texto por la cantidad de segmentos
            frases = texto_completo.split('. ')
            
            for i, seg in enumerate(segmentos_ordenados):
                speaker_num = seg.get('speaker', 0)
                speaker_str = str(speaker_num)
                
                # Obtener nombre del hablante
                if speaker_str in hablantes_mapeados:
                    nombre_hablante = hablantes_mapeados[speaker_str]['nombre']
                else:
                    nombre_hablante = f'Speaker_{speaker_num}'
                
                # Asignar texto aproximado (esto es una aproximación)
                if i < len(frases):
                    texto_mensaje = frases[i].strip()
                    if texto_mensaje:
                        conversacion.append({
                            'speaker': nombre_hablante,
                            'text': texto_mensaje,
                            'timestamp': seg.get('inicio', 0)
                        })
        
        t.conversacion_json = conversacion
        print(f'✅ Conversacion JSON generada: {len(conversacion)} mensajes')
        
        # PASO 5: Guardar cambios
        t.save()
        print('✅ Cambios guardados en la base de datos')
        
        # PASO 6: Mostrar resultado
        print('\n=== RESULTADO FINAL ===')
        print(f'Hablantes detectados: {len(t.hablantes_detectados)}')
        for i, h in enumerate(t.hablantes_detectados):
            print(f'  {i}: {h}')
        
        print(f'Conversacion JSON: {len(t.conversacion_json)} mensajes')
        if t.conversacion_json:
            print('Primeros 3 mensajes:')
            for i, msg in enumerate(t.conversacion_json[:3]):
                print(f'  {i+1}: {msg.get("speaker", "?")} - {msg.get("text", "")[:50]}...')
        
        return True
        
    except Exception as e:
        print(f'❌ Error aplicando fix: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Aplicar fix a transcripción 88
    success = fix_mapeo_participantes(88)
    if success:
        print('\n🎉 FIX APLICADO EXITOSAMENTE!')
        print('Ahora puedes verificar http://localhost:8000/transcripcion/detalle/88/')
    else:
        print('\n❌ Fix falló')