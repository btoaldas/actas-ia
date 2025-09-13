#!/usr/bin/env python
"""
Script para convertir la estructura actual de conversacion_json al formato esperado por el widget de chat
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
import json

def convertir_conversacion_json_a_chat(transcripcion_id):
    """Convierte el conversacion_json actual al formato esperado por el chat widget"""
    
    try:
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        
        print(f"🔄 CONVIRTIENDO TRANSCRIPCIÓN ID: {transcripcion.id}")
        print(f"📅 Fecha: {transcripcion.fecha_creacion}")
        print(f"📊 Estado: {transcripcion.estado}")
        
        # Verificar estructura actual
        conversacion_actual = transcripcion.conversacion_json
        print(f"📝 Tipo actual: {type(conversacion_actual)}")
        
        if isinstance(conversacion_actual, dict):
            # Extraer segmentos y hablantes
            segmentos_json = conversacion_actual.get('segmentos', [])
            hablantes_json = conversacion_actual.get('hablantes', {})
            
            print(f"📊 Segmentos encontrados: {len(segmentos_json)}")
            print(f"👥 Hablantes encontrados: {len(hablantes_json)}")
            
            # Generar paleta de colores para hablantes
            colores_hablantes = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6f42c1', '#e83e8c', '#fd7e14']
            hablantes_colores = {}
            
            conversacion_para_chat = []
            
            for i, segmento in enumerate(segmentos_json):
                # Obtener información del speaker
                speaker_id = str(segmento.get('speaker', 'unknown'))
                hablante_info = hablantes_json.get(speaker_id, {})
                
                # Construir nombre del hablante
                first_name = hablante_info.get('first_name', '')
                last_name = hablante_info.get('last_name', '')
                label = hablante_info.get('label', '')
                
                if first_name:
                    speaker_name = f"{first_name} {last_name}".strip()
                elif label:
                    speaker_name = label
                else:
                    speaker_name = f'Hablante {speaker_id}'
                
                # Asignar color consistente por hablante
                if speaker_id not in hablantes_colores:
                    color_index = len(hablantes_colores) % len(colores_hablantes)
                    hablantes_colores[speaker_id] = colores_hablantes[color_index]
                
                color = hablantes_colores[speaker_id]
                
                # Validar datos antes de crear mensaje
                inicio = float(segmento.get('start', 0.0))
                fin = float(segmento.get('end', 0.0))
                texto = segmento.get('text', '').strip()
                
                # Solo agregar si tiene contenido válido
                if texto and inicio >= 0 and fin > inicio:
                    mensaje_chat = {
                        'hablante': speaker_name,
                        'texto': texto,
                        'inicio': inicio,
                        'fin': fin,
                        'duracion': fin - inicio,
                        'confianza': segmento.get('speaker_confidence', 0.8),
                        'speaker_id': speaker_id,
                        'color': color,
                        'timestamp': f"{inicio:.1f}s - {fin:.1f}s"
                    }
                    
                    conversacion_para_chat.append(mensaje_chat)
                else:
                    print(f"⚠️  Segmento inválido omitido: speaker={speaker_id}, texto='{texto}', inicio={inicio}, fin={fin}")
            
            # Guardar conversación en formato correcto para el template
            print(f"💾 Guardando {len(conversacion_para_chat)} mensajes válidos...")
            
            # Guardar estructura original en diarizacion_json si no existe
            if not transcripcion.diarizacion_json:
                transcripcion.diarizacion_json = conversacion_actual
            
            # Actualizar conversacion_json al formato de chat
            transcripcion.conversacion_json = conversacion_para_chat
            transcripcion.save()
            
            print(f"✅ CONVERSIÓN COMPLETADA")
            print(f"📊 Mensajes generados: {len(conversacion_para_chat)}")
            
            if conversacion_para_chat:
                primer_mensaje = conversacion_para_chat[0]
                print(f"📨 PRIMER MENSAJE:")
                print(f"   👤 Hablante: {primer_mensaje['hablante']}")
                print(f"   💬 Texto: {primer_mensaje['texto'][:80]}...")
                print(f"   ⏱️  Tiempo: {primer_mensaje['inicio']}s - {primer_mensaje['fin']}s")
                print(f"   🎨 Color: {primer_mensaje['color']}")
                
                return True
        else:
            print(f"❌ conversacion_json no es un dict, es {type(conversacion_actual)}")
            return False
            
    except Transcripcion.DoesNotExist:
        print(f"❌ No se encontró transcripción con ID {transcripcion_id}")
        return False
    except Exception as e:
        print(f"❌ Error convirtiendo: {str(e)}")
        return False

if __name__ == "__main__":
    # Convertir transcripción ID 72
    exito = convertir_conversacion_json_a_chat(72)
    
    if exito:
        print("\n🎉 ¡CONVERSIÓN EXITOSA!")
        print("🌐 Ahora el widget de chat debería mostrar las conversaciones correctamente")
    else:
        print("\n💥 FALLÓ LA CONVERSIÓN")