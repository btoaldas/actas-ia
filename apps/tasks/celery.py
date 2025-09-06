# -*- encoding: utf-8 -*-
"""
Configuración de Celery para el Sistema de Actas Municipales de Pastaza
Copyright (c) 2025 - Municipio de Pastaza
"""

import os
from celery import Celery

# Configurar el módulo de settings por defecto para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Crear la aplicación Celery
app = Celery('actas_municipales_pastaza')

# Configuración desde Django settings con namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscovery de tareas desde todas las apps Django
app.autodiscover_tasks()

# Configuración adicional específica para el municipio
app.conf.update(
    # Configuración de colas específicas para actas municipales
    task_routes={
        'apps.tasks.tasks.procesar_audio_acta': {'queue': 'audio_processing'},
        'apps.tasks.tasks.generar_transcripcion': {'queue': 'transcription'},
        'apps.tasks.tasks.enviar_notificacion_email': {'queue': 'notifications'},
        'apps.tasks.tasks.generar_pdf_acta': {'queue': 'pdf_generation'},
        'apps.tasks.tasks.backup_database': {'queue': 'maintenance'},
    },
    
    # Configuración de zona horaria para Ecuador
    timezone='America/Guayaquil',
    enable_utc=True,
    
    # Configuración de tareas periódicas para el municipio
    beat_schedule={
        'limpieza_archivos_temporales': {
            'task': 'apps.tasks.tasks.limpiar_archivos_temporales',
            'schedule': 86400.0,  # Cada 24 horas
        },
        'backup_diario_bd': {
            'task': 'apps.tasks.tasks.backup_database',
            'schedule': 43200.0,  # Cada 12 horas
        },
        'verificar_actas_pendientes': {
            'task': 'apps.tasks.tasks.verificar_actas_pendientes',
            'schedule': 3600.0,  # Cada hora
        },
    },
)

@app.task(bind=True)
def debug_task(self):
    """Tarea de debug para verificar que Celery funciona"""
    print(f'🏛️ Celery funcionando: {self.request!r} - Municipio de Pastaza')
    return f'Celery funcionando correctamente para el Municipio de Pastaza'