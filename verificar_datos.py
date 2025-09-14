#!/usr/bin/env python
"""Script para verificar los datos guardados en la transcripción"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
import json

def main():
    # Obtener la transcripción
    transcripcion = Transcripcion.objects.get(id=29)
    print(f'Transcripción: {transcripcion.id}')
    print(f'Estado: {transcripcion.estado}')
    
    # Verificar conversacion_json
    print('\n=== CONVERSACION JSON ===')
    if transcripcion.conversacion_json:
        print(f'Keys: {list(transcripcion.conversacion_json.keys())}')
        if 'file_id' in transcripcion.conversacion_json:
            print(f'File ID: {transcripcion.conversacion_json["file_id"]}')
        if 'speakers_detected' in transcripcion.conversacion_json:
            print(f'Speakers detectados: {transcripcion.conversacion_json["speakers_detected"]}')
        if 'hablantes' in transcripcion.conversacion_json:
            print(f'Hablantes: {transcripcion.conversacion_json["hablantes"]}')
        # Mostrar estructura completa de forma legible
        print(f'Estructura completa:')
        print(json.dumps(transcripcion.conversacion_json, indent=2, ensure_ascii=False))
    else:
        print('Sin conversacion_json')
    
    # Verificar transcripcion_json
    print('\n=== TRANSCRIPCION JSON ===')
    if transcripcion.transcripcion_json:
        print(f'Keys: {list(transcripcion.transcripcion_json.keys())}')
        print(f'Metadatos: {transcripcion.transcripcion_json.get("metadatos", {})}')
    else:
        print('Sin transcripcion_json')
    
    # Verificar diarizacion_json
    print('\n=== DIARIZACION JSON ===')
    if transcripcion.diarizacion_json:
        print(f'Keys: {list(transcripcion.diarizacion_json.keys())}')
        print(f'Hablantes: {transcripcion.diarizacion_json.get("hablantes", {})}')
    else:
        print('Sin diarizacion_json')

if __name__ == '__main__':
    main()