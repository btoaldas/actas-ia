"""
Comando para inicializar configuraciones de transcripción
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.transcripcion.models import ConfiguracionTranscripcion

User = get_user_model()


class Command(BaseCommand):
    help = 'Inicializa configuraciones de transcripción por defecto'

    def handle(self, *args, **options):
        # Obtener un superusuario para asignar como creador
        superuser = User.objects.filter(is_superuser=True).first()
        if not superuser:
            self.stdout.write(
                self.style.ERROR('No se encontró ningún superusuario. Creando configuraciones sin usuario.')
            )
            usuario_creacion = None
        else:
            usuario_creacion = superuser
            self.stdout.write(
                self.style.SUCCESS(f'Usando superusuario "{superuser.username}" como creador')
            )
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
                'usuario_creacion': usuario_creacion,  # Asignar usuario
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
                'usuario_creacion': usuario_creacion,  # Asignar usuario
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
                'usuario_creacion': usuario_creacion,  # Asignar usuario
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
