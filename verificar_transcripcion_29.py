#!/usr/bin/env python
"""Script para verificar la transcripción 29"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
import json

def main():
    try:
        # Obtener la transcripción 29
        transcripcion = Transcripcion.objects.get(id=29)
        print(f'Transcripción 29: {transcripcion.id}')
        print(f'Estado: {transcripcion.estado}')
        print(f'Procesamiento ID: {transcripcion.procesamiento_audio_id}')
        
        # Verificar conversacion_json
        print('\n=== CONVERSACION JSON (transcripción 29) ===')
        if transcripcion.conversacion_json:
            print(f'Keys: {list(transcripcion.conversacion_json.keys())}')
            if 'dialogo' in transcripcion.conversacion_json:
                print(f'Dialogo entries: {len(transcripcion.conversacion_json["dialogo"])}')
            if 'turnos_conversacion' in transcripcion.conversacion_json:
                print(f'Turnos conversación: {len(transcripcion.conversacion_json["turnos_conversacion"])}')
            if 'file_id' in transcripcion.conversacion_json:
                print(f'File ID: {transcripcion.conversacion_json["file_id"]}')
            if 'speakers_detected' in transcripcion.conversacion_json:
                print(f'Speakers detectados: {transcripcion.conversacion_json["speakers_detected"]}')
            print('¿Tiene nueva estructura?', 'file_id' in transcripcion.conversacion_json and 'speakers' in transcripcion.conversacion_json)
        else:
            print('Sin conversacion_json')
        
        # Si no tiene la nueva estructura, regenerarla
        if transcripcion.conversacion_json and ('file_id' not in transcripcion.conversacion_json or 'speakers' not in transcripcion.conversacion_json):
            print('\n=== REGENERANDO ESTRUCTURA ===')
            from apps.transcripcion.tasks import procesar_transcripcion_completa
            # Cambiar estado a pendiente para forzar reprocesamiento
            transcripcion.estado = 'pendiente'
            transcripcion.save()
            # Iniciar reprocesamiento
            task = procesar_transcripcion_completa.delay(transcripcion.id)
            print(f'Task de reprocesamiento iniciada: {task.id}')
            
    except Transcripcion.DoesNotExist:
        print('Transcripción 29 no encontrada')

if __name__ == '__main__':
    main()