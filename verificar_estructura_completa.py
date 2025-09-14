#!/usr/bin/env python3
"""
Script para verificar la nueva estructura completa de conversacion_json
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

def main():
    t = Transcripcion.objects.get(id=88)
    
    print('=== VERIFICACION DE ESTRUCTURA COMPLETA CON CABECERA ===')
    print(f'Estado: {t.estado}')
    
    if not t.conversacion_json:
        print('❌ No hay conversacion_json')
        return
        
    if isinstance(t.conversacion_json, list):
        print('⚠️ conversacion_json es lista (estructura antigua)')
        print(f'   Total mensajes: {len(t.conversacion_json)}')
        return
    
    # Nueva estructura esperada: {cabecera: {...}, conversacion: [...], metadata: {...}}
    if isinstance(t.conversacion_json, dict):
        print('✅ conversacion_json es diccionario (estructura nueva)')
        
        # Verificar campos principales
        cabecera = t.conversacion_json.get('cabecera', {})
        conversacion = t.conversacion_json.get('conversacion', [])
        metadata = t.conversacion_json.get('metadata', {})
        
        print(f'\n=== CABECERA ===')
        print(f'✅ Cabecera presente: {bool(cabecera)}')
        
        if cabecera:
            audio_info = cabecera.get('audio', {})
            transcripcion_info = cabecera.get('transcripcion', {})
            mapeo_hablantes = cabecera.get('mapeo_hablantes', {})
            participantes = cabecera.get('participantes_configurados', [])
            
            print(f'   Audio ID: {audio_info.get("id")}')
            print(f'   Audio título: {audio_info.get("titulo")}')
            print(f'   Transcripción ID: {transcripcion_info.get("id")}')
            print(f'   Usuario: {transcripcion_info.get("usuario_creacion")}')
            print(f'   Modelo: {transcripcion_info.get("modelo_whisper")}')
            print(f'   Participantes configurados: {len(participantes)}')
            print(f'   Mapeo de hablantes: {len(mapeo_hablantes)}')
            
            # Mostrar mapeo de hablantes
            if mapeo_hablantes:
                print(f'\n   🎯 MAPEO DE HABLANTES:')
                for hablante_id, info in mapeo_hablantes.items():
                    nombre = info.get('nombre_completo', info.get('nombre', 'Sin nombre'))
                    print(f'     {hablante_id} → {nombre}')
            
            # Mostrar participantes
            if participantes:
                print(f'\n   👥 PARTICIPANTES CONFIGURADOS:')
                for i, p in enumerate(participantes):
                    nombre = p.get('nombres', 'Sin nombre')
                    apellidos = p.get('apellidos', '')
                    nombre_completo = f"{nombre} {apellidos}".strip()
                    print(f'     {i}: {nombre_completo}')
        
        print(f'\n=== CONVERSACION ===')
        print(f'✅ Mensajes: {len(conversacion)}')
        
        if conversacion:
            # Analizar hablantes únicos
            hablantes_unicos = set()
            for msg in conversacion:
                hablante = msg.get('hablante', 'N/A')
                hablantes_unicos.add(hablante)
            
            print(f'   Hablantes únicos detectados: {sorted(hablantes_unicos)}')
            
            # Mostrar primeros 3 mensajes
            print(f'\n   📨 PRIMEROS 3 MENSAJES:')
            for i, msg in enumerate(conversacion[:3]):
                hablante = msg.get('hablante', 'N/A')
                texto = msg.get('texto', '')
                tiempo = msg.get('timestamp', 'N/A')
                texto_corto = texto[:40] + '...' if len(texto) > 40 else texto
                print(f'     {i+1}. {hablante} ({tiempo}): "{texto_corto}"')
            
            # ¿Se ven nombres reales?
            nombres_reales = ['Beto', 'Ely', 'Alberto', 'Elizabeth']
            nombres_encontrados = []
            for nombre in nombres_reales:
                if any(nombre in h for h in hablantes_unicos):
                    nombres_encontrados.append(nombre)
            
            if nombres_encontrados:
                print(f'\n   🎉 ¡ÉXITO! Nombres reales encontrados: {nombres_encontrados}')
            else:
                print(f'\n   ❌ No se encontraron nombres reales. Solo: {sorted(hablantes_unicos)}')
        
        print(f'\n=== METADATA ===')
        print(f'✅ Metadata presente: {bool(metadata)}')
        if metadata:
            print(f'   Total mensajes: {metadata.get("total_mensajes")}')
            print(f'   Hablantes detectados: {metadata.get("hablantes_detectados")}')
            print(f'   Duración total: {metadata.get("duracion_total")}s')
            print(f'   Versión estructura: {metadata.get("version_estructura")}')
            print(f'   Fecha generación: {metadata.get("fecha_generacion")}')

if __name__ == '__main__':
    main()