from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.transcripcion.models import ConfiguracionTranscripcion


class Command(BaseCommand):
    help = 'Inicializa la configuración por defecto del módulo de transcripción'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Inicializando configuración de transcripción...'))
        
        # Crear configuración por defecto si no existe
        config_default, created = ConfiguracionTranscripcion.objects.get_or_create(
            nombre='Configuración por Defecto',
            defaults={
                'descripcion': 'Configuración inicial del sistema de transcripción',
                'modelo_whisper': 'base',
                'idioma_principal': 'es',
                'temperatura': 0.0,
                'modelo_diarizacion': 'pyannote/speaker-diarization@2.1',
                'min_hablantes': 1,
                'max_hablantes': 10,
                'segmentacion_minima': 1.0,
                'umbral_confianza': 0.5,
                'activa': True,
                'usuario_creacion': User.objects.filter(is_superuser=True).first()
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Configuración por defecto creada: {config_default.nombre}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'✓ Configuración por defecto ya existe: {config_default.nombre}')
            )
        
        # Asegurar que hay una configuración activa
        if not ConfiguracionTranscripcion.objects.filter(activa=True).exists():
            config_default.activa = True
            config_default.save()
            self.stdout.write(
                self.style.SUCCESS('✓ Configuración marcada como activa')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🎯 Inicialización completada correctamente')
        )
