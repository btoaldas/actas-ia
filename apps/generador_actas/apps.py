from django.apps import AppConfig


class GeneradorActasConfig(AppConfig):
    """
    Configuración de la aplicación Generador de Actas con IA
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.generador_actas'
    verbose_name = 'Generador de Actas con IA'
    
    def ready(self):
        """
        Se ejecuta cuando Django carga la aplicación
        """
        # Importar señales si las hay
        try:
            import apps.generador_actas.signals
        except ImportError:
            pass
            
        # Importar tareas para registro en Celery
        try:
            import apps.generador_actas.tasks
        except ImportError:
            pass