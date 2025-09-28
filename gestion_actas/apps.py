from django.apps import AppConfig


class GestionActasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_actas'
    
    def ready(self):
        """Importar señales cuando la app esté lista"""
        import gestion_actas.signals
