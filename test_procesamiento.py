#!/usr/bin/env python
"""Script para crear un procesamiento de audio de prueba"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.audio_processing.models import ProcesamientoAudio, TipoReunion
from apps.audio_processing.tasks import procesar_audio_task
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

def main():
    # Verificar si existen tipos de reunión
    tipos = TipoReunion.objects.all()
    print(f'Tipos de reunión disponibles: {list(tipos.values_list("id", "nombre"))}')

    if not tipos.exists():
        # Crear un tipo de reunión de prueba
        tipo = TipoReunion.objects.create(
            nombre='Reunión de Prueba',
            descripcion='Tipo de reunión para pruebas de transcripción'
        )
        print(f'Tipo de reunión creado: {tipo.id} - {tipo.nombre}')
    else:
        tipo = tipos.first()
        print(f'Usando tipo existente: {tipo.id} - {tipo.nombre}')

    # Leer el archivo de prueba
    with open('/tmp/test_audio.wav', 'rb') as f:
        content = f.read()

    # Crear un archivo Django para el procesamiento
    audio_file = SimpleUploadedFile(
        name='test_audio.wav',
        content=content,
        content_type='audio/wav'
    )

    # Configurar participantes predefinidos como JSON
    participantes = [
        {
            'id': 0,
            'label': 'Test Speaker 1',
            'role': 'Presidente',
            'description': 'Hablante de prueba 1',
            'cedula': '1234567890',
            'titulo': 'Sr',
            'cargo': 'Presidente',
            'institucion': 'Test',
            'first_name': 'Test',
            'last_name': 'Speaker1',
            'can_vote': True,
            'has_voice': True,
            'can_sign': True,
            'attendance': True,
            'details': None,
            'actor_type': None
        }
    ]

    # Obtener usuario superadmin para el procesamiento
    try:
        usuario = User.objects.get(username='superadmin')
        print(f'Usando usuario: {usuario.username}')
    except User.DoesNotExist:
        print('Usuario superadmin no encontrado, usando primer usuario disponible')
        usuario = User.objects.first()
        if not usuario:
            print('No hay usuarios disponibles')
            return

    # Crear el procesamiento de audio
    procesamiento = ProcesamientoAudio.objects.create(
        titulo='Prueba de Estructura JSON Mejorada',
        archivo_audio=audio_file,
        tipo_reunion=tipo,
        usuario=usuario,
        estado='ingestado',
        participantes_detallados=participantes,
        descripcion='Audio de prueba para verificar nueva estructura JSON'
    )

    print(f'Procesamiento creado con ID: {procesamiento.id}')

    # Iniciar el procesamiento
    print(f'Iniciando procesamiento asincrono...')
    task = procesar_audio_task.delay(procesamiento.id)
    print(f'Task ID: {task.id}')
    print(f'URL para ver detalle: http://localhost:8000/audio/detalle/{procesamiento.id}/')

if __name__ == '__main__':
    main()