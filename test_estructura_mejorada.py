#!/usr/bin/env python3
"""
Script para probar la nueva estructura mejorada con segmentos 
formato: inicio, hablante, texto
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
from apps.transcripcion.tasks import procesar_transcripcion_completa
import json

def verificar_estructura_mejorada(transcripcion_id):
    """Verifica que la estructura tenga el formato correcto"""
    
    print(f"🔍 VERIFICANDO ESTRUCTURA MEJORADA - Transcripción {transcripcion_id}")
    print("=" * 70)
    
    try:
        transcripcion = Transcripcion.objects.get(id=transcripcion_id)
        
        print(f"✅ Transcripción encontrada:")
        print(f"   - ID: {transcripcion.id}")
        print(f"   - Estado: {transcripcion.estado}")  
        print(f"   - Audio ID: {transcripcion.procesamiento_audio.id}")
        print(f"   - Número hablantes: {transcripcion.numero_hablantes}")
        
        # Verificar estructura JSON
        conv_json = transcripcion.conversacion_json
        if not conv_json:
            print("❌ conversacion_json está vacío")
            return False
            
        print(f"\n📋 ESTRUCTURA CONVERSACION_JSON:")
        print(f"   - Tipo: {type(conv_json)}")
        
        if isinstance(conv_json, dict):
            print(f"   - Campos disponibles: {list(conv_json.keys())}")
            
            # 1. VERIFICAR CABECERA
            if 'cabecera' in conv_json:
                cabecera = conv_json['cabecera']
                print(f"   ✅ Cabecera presente:")
                print(f"      - Audio info: {'audio' in cabecera}")
                print(f"      - Transcripción info: {'transcripcion' in cabecera}")
                print(f"      - Hablantes: {len(cabecera.get('hablantes', {}))}")
                print(f"      - Mapeo hablantes: {cabecera.get('mapeo_hablantes', {})}")
            else:
                print("   ❌ No hay cabecera")
                
            # 2. VERIFICAR CONVERSACIÓN
            if 'conversacion' in conv_json:
                conversacion = conv_json['conversacion']
                print(f"   ✅ Conversación presente: {len(conversacion)} segmentos")
                
                if len(conversacion) > 0:
                    primer_seg = conversacion[0]
                    print(f"   📝 Primer segmento:")
                    print(f"      - Campos: {list(primer_seg.keys())}")
                    print(f"      - inicio: {primer_seg.get('inicio', 'NO')}")
                    print(f"      - hablante: {primer_seg.get('hablante', 'NO')}")
                    print(f"      - texto: {primer_seg.get('texto', 'NO')[:50]}...")
                    
                    # Verificar que TODOS los segmentos tengan los campos requeridos
                    campos_requeridos = ['inicio', 'hablante', 'texto']
                    segmentos_validos = 0
                    for i, seg in enumerate(conversacion):
                        if all(campo in seg for campo in campos_requeridos):
                            segmentos_validos += 1
                        else:
                            print(f"      ⚠️ Segmento {i} incompleto: {list(seg.keys())}")
                            
                    print(f"   ✅ Segmentos válidos: {segmentos_validos}/{len(conversacion)}")
            else:
                print("   ❌ No hay conversación")
                
            # 3. VERIFICAR TEXTO ESTRUCTURADO
            if 'texto_estructurado' in conv_json:
                texto_est = conv_json['texto_estructurado']
                lineas = texto_est.split('\n') if texto_est else []
                print(f"   ✅ Texto estructurado: {len(lineas)} líneas")
                
                if len(lineas) > 0:
                    print(f"   📄 Primera línea: {lineas[0]}")
                    if len(lineas) > 1:
                        print(f"   📄 Segunda línea: {lineas[1]}")
                        
                    # Verificar formato: Tiempo,Hablante,Texto
                    formato_correcto = 0
                    for linea in lineas[:5]:  # Solo primeras 5
                        partes = linea.split(',', 2)  # Máximo 3 partes
                        if len(partes) >= 3:
                            formato_correcto += 1
                    print(f"   ✅ Líneas con formato correcto: {formato_correcto}/{min(5, len(lineas))}")
            else:
                print("   ❌ No hay texto estructurado")
                
            # 4. VERIFICAR METADATA
            if 'metadata' in conv_json:
                metadata = conv_json['metadata']
                print(f"   ✅ Metadata presente: {len(metadata)} campos")
                print(f"      - Estructura segmentos: {metadata.get('estructura_segmentos', 'NO')}")
            else:
                print("   ❌ No hay metadata")
                
        else:
            print("   ❌ conversacion_json no es un diccionario")
            
        print(f"\n📊 RESUMEN:")
        tiene_cabecera = isinstance(conv_json, dict) and 'cabecera' in conv_json
        tiene_conversacion = isinstance(conv_json, dict) and 'conversacion' in conv_json
        tiene_texto_est = isinstance(conv_json, dict) and 'texto_estructurado' in conv_json
        
        print(f"   - Cabecera: {'✅' if tiene_cabecera else '❌'}")
        print(f"   - Conversación: {'✅' if tiene_conversacion else '❌'}")
        print(f"   - Texto estructurado: {'✅' if tiene_texto_est else '❌'}")
        
        if tiene_cabecera and tiene_conversacion and tiene_texto_est:
            print("\n🎉 ESTRUCTURA COMPLETA Y CORRECTA!")
            return True
        else:
            print("\n⚠️ ESTRUCTURA INCOMPLETA")
            return False
            
    except Transcripcion.DoesNotExist:
        print(f"❌ Transcripción {transcripcion_id} no encontrada")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def procesar_y_verificar(transcripcion_id):
    """Procesa una transcripción y verifica la nueva estructura"""
    
    print(f"🚀 PROCESANDO Y VERIFICANDO TRANSCRIPCIÓN {transcripcion_id}")
    print("=" * 70)
    
    # 1. Procesar
    print("⏳ Iniciando procesamiento...")
    result = procesar_transcripcion_completa.delay(transcripcion_id)
    print(f"✅ Tarea iniciada: {result.id}")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Esperar ~60-80 segundos para que termine")
    print("   2. Ejecutar verificación:")
    print(f"      python /app/test_estructura_mejorada.py {transcripcion_id}")
    
    return result.id

if __name__ == "__main__":
    if len(sys.argv) > 1:
        transcripcion_id = int(sys.argv[1])
        
        if len(sys.argv) > 2 and sys.argv[2] == 'procesar':
            # Procesar primero
            procesar_y_verificar(transcripcion_id)
        else:
            # Solo verificar
            verificar_estructura_mejorada(transcripcion_id)
    else:
        print("Uso:")
        print("  python test_estructura_mejorada.py 93           # Solo verificar")
        print("  python test_estructura_mejorada.py 93 procesar  # Procesar y verificar")