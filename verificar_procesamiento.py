#!/usr/bin/env python
"""Script para verificar el estado del procesamiento"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.audio_processing.models import ProcesamientoAudio
from apps.transcripcion.models import Transcripcion
import json

def main():
    # Verificar el procesamiento
    proc = ProcesamientoAudio.objects.get(id=19)
    print(f'Procesamiento: {proc.titulo}')
    print(f'Estado: {proc.estado}')
    print(f'Progreso: {proc.progreso}%')

    # Verificar transcripciones asociadas
    transcripciones = Transcripcion.objects.filter(procesamiento_audio=proc)
    print(f'Transcripciones encontradas: {transcripciones.count()}')

    for t in transcripciones:
        print(f'  - Transcripción {t.id}: {t.estado} ({t.progreso}%)')
        if t.conversacion_json:
            print(f'    Conversacion JSON keys: {list(t.conversacion_json.keys())}')
            if 'file_id' in t.conversacion_json:
                print(f'    File ID: {t.conversacion_json["file_id"]}')
            if 'speakers_detected' in t.conversacion_json:
                print(f'    Speakers detectados: {t.conversacion_json["speakers_detected"]}')
                
    # Si no hay transcripciones, iniciar transcripción manualmente
    if not transcripciones.exists():
        print('No hay transcripciones. Iniciando transcripción manualmente...')
        from apps.transcripcion.tasks import procesar_transcripcion_completa
        task = procesar_transcripcion_completa.delay(proc.id)
        print(f'Task de transcripción iniciada: {task.id}')

if __name__ == '__main__':
    main()