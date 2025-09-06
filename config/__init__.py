# Importar Celery app cuando Django se inicie
from .celery import app as celery_app

__all__ = ('celery_app',)