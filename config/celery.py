"""
Configuración de Celery para el Sistema de Actas Municipales de Pastaza
"""

import os
from celery import Celery

# Configurar Django settings para Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Crear la aplicación Celery
app = Celery('actas_municipales_pastaza')

# Configurar Celery usando la configuración de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en todas las aplicaciones Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Tarea de debug para probar Celery"""
    print('Request: {0!r}'.format(self.request))

# ============================================================================
# Configurar signals de auditoría para Celery
# ============================================================================

def setup_celery_logging():
    """Configurar el sistema de logging para Celery"""
    try:
        # Importar y configurar el sistema de logging de Celery
        from helpers.celery_logging import (
            task_prerun_handler, task_postrun_handler, task_failure_handler,
            task_retry_handler, task_success_handler, worker_ready_handler,
            worker_shutdown_handler
        )
        
        # Los signals ya están conectados en el archivo helpers/celery_logging.py
        # Esta función existe para asegurar que se importen al inicializar Celery
        print("✅ Sistema de auditoría Celery configurado correctamente")
        
    except ImportError as e:
        print(f"⚠️  No se pudo cargar el sistema de auditoría Celery: {e}")

# Configurar logging al importar este módulo
setup_celery_logging()
