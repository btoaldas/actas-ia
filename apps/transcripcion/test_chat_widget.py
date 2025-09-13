#!/usr/bin/env python
"""
Test para verificar la estructura correcta del conversacion_json para el widget de chat
"""
import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import ProcesamientoTranscripcion

def test_conversacion_json_structure():
    """Test para verificar que conversacion_json tiene la estructura correcta"""
    
    print("🧪 TEST: Estructura de conversacion_json para widget de chat")
    print("=" * 60)
    
    # Buscar una transcripción reciente con conversacion_json
    transcripciones = ProcesamientoTranscripcion.objects.filter(
        conversacion_json__isnull=False
    ).exclude(conversacion_json=[]).order_by('-fecha_creacion')[:3]
    
    if not transcripciones:
        print("❌ No se encontraron transcripciones con conversacion_json")
        return
    
    for i, transcripcion in enumerate(transcripciones, 1):
        print(f"\n📋 TRANSCRIPCIÓN {i}: ID {transcripcion.id}")
        print(f"   Estado: {transcripcion.estado}")
        print(f"   Fecha: {transcripcion.fecha_creacion}")
        
        # Verificar estructura
        conversacion = transcripcion.conversacion_json
        
        if not isinstance(conversacion, list):
            print(f"   ❌ ERROR: conversacion_json no es una lista, es {type(conversacion)}")
            continue
        
        print(f"   ✅ Es lista: {len(conversacion)} mensajes")
        
        if not conversacion:
            print("   ⚠️  Lista vacía")
            continue
        
        # Verificar primer mensaje
        primer_mensaje = conversacion[0]
        print(f"   📨 PRIMER MENSAJE:")
        
        campos_requeridos = ['hablante', 'texto', 'inicio', 'fin', 'color']
        for campo in campos_requeridos:
            valor = primer_mensaje.get(campo, 'MISSING')
            status = "✅" if campo in primer_mensaje else "❌"
            print(f"      {status} {campo}: {valor}")
        
        # Mostrar ejemplo del JSON
        print(f"   📄 ESTRUCTURA COMPLETA DEL PRIMER MENSAJE:")
        print(f"      {json.dumps(primer_mensaje, indent=8, ensure_ascii=False)}")
        
        # Verificar validez de datos
        hablante = primer_mensaje.get('hablante', '')
        texto = primer_mensaje.get('texto', '')
        inicio = primer_mensaje.get('inicio', 0)
        fin = primer_mensaje.get('fin', 0)
        
        print(f"   🔍 VALIDACIÓN DE DATOS:")
        print(f"      ✅ Hablante válido: {bool(hablante and hablante != 'Hablante Desconocido')}")
        print(f"      ✅ Texto válido: {bool(texto and texto != '[Sin texto]')}")
        print(f"      ✅ Tiempos válidos: {bool(inicio >= 0 and fin > inicio)}")
        
        if len(conversacion) > 1:
            print(f"   📊 RESUMEN DE TODOS LOS MENSAJES:")
            hablantes_unicos = set()
            textos_validos = 0
            tiempos_validos = 0
            
            for msg in conversacion:
                if msg.get('hablante'):
                    hablantes_unicos.add(msg.get('hablante'))
                if msg.get('texto') and msg.get('texto') != '[Sin texto]':
                    textos_validos += 1
                if msg.get('inicio', 0) >= 0 and msg.get('fin', 0) > msg.get('inicio', 0):
                    tiempos_validos += 1
            
            print(f"      👥 Hablantes únicos: {len(hablantes_unicos)} -> {list(hablantes_unicos)}")
            print(f"      📝 Mensajes con texto válido: {textos_validos}/{len(conversacion)}")
            print(f"      ⏱️  Mensajes con tiempos válidos: {tiempos_validos}/{len(conversacion)}")
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN: Si ves 'Hablante Desconocido' y '[Sin texto]', el problema está en la generación del JSON")

if __name__ == "__main__":
    test_conversacion_json_structure()