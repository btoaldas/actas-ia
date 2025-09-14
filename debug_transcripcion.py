#!/usr/bin/env python3
"""
Script para verificar el resultado FINAL después de TODOS los fixes
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
    
    print('=== VERIFICACION RESULTADO FINAL (TODOS LOS FIXES) ===')
    print(f'Estado: {t.estado}')
    print(f'Conversación JSON: {len(t.conversacion_json) if t.conversacion_json else 0} mensajes')
    print(f'Diarización JSON: {bool(t.diarizacion_json)}')
    
    if t.diarizacion_json:
        # Buscar múltiples campos donde pueden estar los hablantes
        campos_hablantes = ['hablantes', 'speakers', 'participantes', 'info_speakers']
        
        for campo in campos_hablantes:
            if campo in t.diarizacion_json:
                hablantes = t.diarizacion_json[campo]
                print(f'✅ Campo "{campo}" encontrado: {hablantes}')
                
                if hablantes and isinstance(hablantes, dict):
                    print(f'   📊 {len(hablantes)} hablantes mapeados:')
                    for speaker_id, info in hablantes.items():
                        if isinstance(info, dict):
                            nombre = info.get('nombre', info.get('label', speaker_id))
                            print(f'     - {speaker_id} → {nombre}')
                        else:
                            print(f'     - {speaker_id} → {info}')
        
        # Ver algunos segmentos para verificar que se aplicó el mapeo
        if 'segmentos' in t.diarizacion_json:
            segmentos = t.diarizacion_json['segmentos'][:3]
            print(f'\n=== PRIMEROS 3 SEGMENTOS (verificar nombres) ===')
            for i, seg in enumerate(segmentos):
                hablante = seg.get('hablante', seg.get('speaker', seg.get('speaker_name', 'N/A')))
                texto = seg.get('texto', '')[:50] + '...' if len(seg.get('texto', '')) > 50 else seg.get('texto', '')
                print(f'Seg {i+1}: {hablante} -> "{texto}"')
                
    if t.conversacion_json and len(t.conversacion_json) > 0:
        print(f'\n=== PRIMEROS 3 MENSAJES DE CONVERSACION ===')
        for i, msg in enumerate(t.conversacion_json[:3]):
            hablante = msg.get('hablante', msg.get('nombre', 'N/A'))
            texto = msg.get('texto', msg.get('mensaje', ''))
            if len(texto) > 50:
                texto = texto[:50] + '...'
            print(f'Msg {i+1}: {hablante} -> "{texto}"')
            
        # Ver si hay nombres reales en la conversación
        hablantes_conversacion = set()
        for msg in t.conversacion_json:
            hablante = msg.get('hablante', msg.get('nombre', 'N/A'))
            hablantes_conversacion.add(hablante)
        
        print(f'\n*** HABLANTES ÚNICOS EN CONVERSACIÓN: {sorted(hablantes_conversacion)} ***')
        
        # ¿Aparecen los nombres reales?
        nombres_reales = ['Beto', 'Ely', 'Alberto', 'Elizabeth']
        nombres_encontrados = []
        for nombre in nombres_reales:
            if any(nombre in h for h in hablantes_conversacion):
                nombres_encontrados.append(nombre)
                
        if nombres_encontrados:
            print(f'🎉 ¡ÉXITO! Nombres reales encontrados: {nombres_encontrados}')
        else:
            print(f'❌ PROBLEMA: No se encontraron nombres reales. Solo: {sorted(hablantes_conversacion)}')
    else:
        print('❌ No hay conversación JSON')
    
    # Verificar los participantes originales
    print(f'\n=== PARTICIPANTES ORIGINALES ===')
    participantes = t.procesamiento_audio.participantes_detallados
    for i, p in enumerate(participantes):
        nombre = p.get('nombres', 'Sin nombre')
        print(f'  - Configurado {i+1}: {nombre}')

if __name__ == '__main__':
    main()