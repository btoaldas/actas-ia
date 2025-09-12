"""
Comando para inicializar configuraciones de transcripción
"""
from django.core.management.base import BaseCommand
from apps.transcripcion.models import ConfiguracionTranscripcion


class Command(BaseCommand):
    help = 'Inicializa configuraciones de transcripción por defecto'

    def handle(self, *args, **options):
        configuraciones = [
            {
                'nombre': 'Rápida',
                'descripcion': 'Configuración rápida para pruebas y transcripciones urgentes',
                'modelo_whisper': 'tiny',
                'temperatura': 0.0,
                'idioma_principal': 'es',
                'usar_vad': True,
                'vad_filtro': 'silero',
                'min_hablantes': 1,
                'max_hablantes': 4,
                'umbral_clustering': 0.7,
                'chunk_duracion': 30,
                'usar_gpu': False,
                'filtro_ruido': True,
                'normalizar_audio': True,
                'activa': True,
            },
            {
                'nombre': 'Balanceada',
                'descripcion': 'Configuración equilibrada entre velocidad y precisión',
                'modelo_whisper': 'base',
                'temperatura': 0.0,
                'idioma_principal': 'es',
                'usar_vad': True,
                'vad_filtro': 'silero',
                'min_hablantes': 1,
                'max_hablantes': 6,
                'umbral_clustering': 0.7,
                'chunk_duracion': 30,
                'usar_gpu': True,
                'filtro_ruido': True,
                'normalizar_audio': True,
                'activa': True,
            },
            {
                'nombre': 'Precisa',
                'descripcion': 'Configuración de alta precisión para transcripciones oficiales',
                'modelo_whisper': 'large',
                'temperatura': 0.0,
                'idioma_principal': 'es',
                'usar_vad': True,
                'vad_filtro': 'silero',
                'min_hablantes': 1,
                'max_hablantes': 8,
                'umbral_clustering': 0.6,
                'chunk_duracion': 45,
                'usar_gpu': True,
                'filtro_ruido': True,
                'normalizar_audio': True,
                'activa': True,
            }
        ]

        created_count = 0
        for config_data in configuraciones:
            config, created = ConfiguracionTranscripcion.objects.get_or_create(
                nombre=config_data['nombre'],
                defaults=config_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Configuración "{config.nombre}" creada.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Configuración "{config.nombre}" ya existe.')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. {created_count} configuraciones nuevas creadas.'
            )
        )
