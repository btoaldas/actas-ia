from django.apps import AppConfig


class TranscripcionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.transcripcion'
    verbose_name = 'Transcripción y Diarización'
    
    def ready(self):
        import apps.transcripcion.signals
