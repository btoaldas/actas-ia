#!/usr/bin/env python3
"""
Script de debugging para entender el mapeo de speakers
"""
import os
import sys
import django
import json

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion, ProcesamientoAudio

def debug_speaker_mapping():
    print("🔍 DEBUGGING DE MAPEO DE SPEAKERS")
    print("=" * 60)
    
    # Buscar la transcripción más reciente
    transcripcion = Transcripcion.objects.order_by('-fecha_creacion').first()
    
    if not transcripcion:
        print("❌ No se encontró ninguna transcripción")
        return
    
    print(f"📄 Transcripción ID: {transcripcion.id}")
    print(f"🎵 Audio ID: {transcripcion.procesamiento_audio.id}")
    print(f"📅 Fecha: {transcripcion.fecha_creacion}")
    print(f"🔄 Estado: {transcripcion.estado}")
    print()
    
    # 1. HABLANTES PREDEFINIDOS
    participantes = transcripcion.procesamiento_audio.participantes_detallados or []
    print(f"👥 HABLANTES PREDEFINIDOS ({len(participantes)}):")
    for i, p in enumerate(participantes):
        nombre = p.get('first_name', p.get('nombres', f'Hablante {i+1}'))
        print(f"   {i}. {nombre} (posición {i} en array)")
    print()
    
    # 2. RESULTADO DE PYANNOTE 
    diarizacion = transcripcion.diarizacion_json
    print(f"🎯 RESULTADO PYANNOTE:")
    if 'hablantes' in diarizacion:
        print("   Hablantes detectados:")
        for k, v in diarizacion['hablantes'].items():
            print(f"     {k}: {v}")
    if 'segmentos_hablantes' in diarizacion:
        print(f"   Segmentos de diarización: {len(diarizacion['segmentos_hablantes'])}")
        if diarizacion['segmentos_hablantes']:
            primer_seg = diarizacion['segmentos_hablantes'][0]
            print(f"   Primer segmento: speaker={primer_seg.get('speaker')}, tiempo={primer_seg.get('inicio', 0):.1f}s")
    print()
    
    # 3. RESULTADO FINAL EN CONVERSACION_JSON
    conversacion = transcripcion.conversacion_json
    print(f"💬 CONVERSACIÓN FINAL ({len(conversacion)} segmentos):")
    if conversacion:
        primer_msg = conversacion[0]
        print(f"   Primer mensaje:")
        print(f"     Speaker ID: {primer_msg.get('speaker')}")
        print(f"     Hablante: {primer_msg.get('hablante')}")
        print(f"     Texto: {primer_msg.get('texto', '')[:50]}...")
        print(f"     Tiempo: {primer_msg.get('inicio')}s - {primer_msg.get('fin')}s")
    print()
    
    # 4. INFORMACIÓN DE HABLANTES FINAL
    if hasattr(transcripcion, 'hablantes_identificados') and transcripcion.hablantes_identificados:
        print(f"🏷️ HABLANTES IDENTIFICADOS:")
        for k, v in transcripcion.hablantes_identificados.items():
            print(f"   {k}: {v}")
        print()
    
    # 5. ANÁLISIS DEL PROBLEMA
    print(f"🔍 ANÁLISIS DEL PROBLEMA:")
    
    # Verificar si el primer segmento coincide con el primer hablante predefinido
    if conversacion and participantes:
        primer_texto = conversacion[0].get('texto', '').lower()
        primer_hablante_real = participantes[0].get('first_name', participantes[0].get('nombres', 'desconocido')).lower()
        primer_hablante_asignado = conversacion[0].get('hablante', 'desconocido').lower()
        
        print(f"   Primer texto dice: '{conversacion[0].get('texto', '')[:100]}...'")
        print(f"   Primer hablante predefinido: {primer_hablante_real}")
        print(f"   Hablante asignado: {primer_hablante_asignado}")
        
        if 'alberto' in primer_texto or 'beto' in primer_texto:
            print(f"   ✅ El texto corresponde a Alberto/Beto")
            if 'beto' in primer_hablante_asignado or 'alberto' in primer_hablante_asignado:
                print(f"   ✅ Mapeo CORRECTO")
            else:
                print(f"   ❌ Mapeo INCORRECTO - debería ser Beto/Alberto")
        else:
            print(f"   ⚠️ No se puede determinar automáticamente")
    
    # 6. TRANSCRIPCION_JSON (estructura mejorada)
    if hasattr(transcripcion, 'transcripcion_json') and transcripcion.transcripcion_json:
        t_json = transcripcion.transcripcion_json
        if 'segmentos' in t_json and t_json['segmentos']:
            print(f"\n📋 TRANSCRIPCION_JSON:")
            primer_seg = t_json['segmentos'][0]
            print(f"   Primer segmento:")
            print(f"     Speaker ID: {primer_seg.get('speaker')}")
            print(f"     Texto: {primer_seg.get('text', '')[:50]}...")
            print(f"     Tiempo: {primer_seg.get('start')}s - {primer_seg.get('end')}s")

if __name__ == "__main__":
    debug_speaker_mapping()