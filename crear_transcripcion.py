#!/usr/bin/env python
"""Script para crear una transcripción y procesarla"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.audio_processing.models import ProcesamientoAudio
from apps.transcripcion.models import Transcripcion, EstadoTranscripcion
from apps.transcripcion.tasks import procesar_transcripcion_completa
from django.contrib.auth.models import User

def main():
    # Obtener el procesamiento
    proc = ProcesamientoAudio.objects.get(id=19)
    print(f'Procesamiento: {proc.titulo}')
    
    # Crear la transcripción
    transcripcion = Transcripcion.objects.create(
        procesamiento_audio=proc,
        usuario_creacion=proc.usuario,
        estado=EstadoTranscripcion.PENDIENTE
    )
    
    print(f'Transcripción creada con ID: {transcripcion.id}')
    
    # Iniciar procesamiento de transcripción
    task = procesar_transcripcion_completa.delay(transcripcion.id)
    print(f'Task de transcripción iniciada: {task.id}')
    print(f'URL transcripción: http://localhost:8000/transcripcion/detalle/{transcripcion.id}/')

if __name__ == '__main__':
    main()