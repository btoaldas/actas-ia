"""
Comando para crear datos de prueba de audio procesado
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.audio_processing.models import ProcesamientoAudio, TipoReunion
import os
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Crea datos de prueba de audios procesados para transcripción'

    def handle(self, *args, **options):
        # Obtener o crear usuario admin
        try:
            usuario = User.objects.get(username='admin')
        except User.DoesNotExist:
            usuario = User.objects.create_user(
                username='admin',
                email='admin@puyo.gob.ec',
                password='AdminPuyo2025!',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Usuario admin creado.'))

        # Obtener o crear tipo de reunión
        tipo_reunion, created = TipoReunion.objects.get_or_create(
            nombre='Sesión Ordinaria',
            defaults={
                'descripcion': 'Sesión ordinaria del concejo municipal',
                'activo': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Tipo de reunión creado.'))

        # Crear audios de prueba
        audios_prueba = [
            {
                'titulo': 'Sesión Ordinaria - 01 Septiembre 2025',
                'descripcion': 'Reunión ordinaria del concejo municipal para tratar temas de presupuesto',
                'duracion': 6330,  # 01:45:30 en segundos
                'duracion_seg': 6330.0,
                'sample_rate': 44100,
                'bit_rate': 192,
                'progreso': 100,
            },
            {
                'titulo': 'Sesión Extraordinaria - Proyectos de Agua',
                'descripcion': 'Sesión especial para aprobar proyectos de agua potable y alcantarillado',
                'duracion': 7965,  # 02:12:45 en segundos
                'duracion_seg': 7965.0,
                'sample_rate': 48000,
                'bit_rate': 256,
                'progreso': 100,
            },
            {
                'titulo': 'Comisión de Desarrollo - Agosto 2025',
                'descripcion': 'Reunión de la comisión de desarrollo urbano y rural',
                'duracion': 4995,  # 01:23:15 en segundos
                'duracion_seg': 4995.0,
                'sample_rate': 44100,
                'bit_rate': 128,
                'progreso': 100,
            }
        ]

        created_count = 0
        for audio_data in audios_prueba:
            # Verificar si ya existe
            if not ProcesamientoAudio.objects.filter(titulo=audio_data['titulo']).exists():
                audio = ProcesamientoAudio.objects.create(
                    titulo=audio_data['titulo'],
                    descripcion=audio_data['descripcion'],
                    duracion=audio_data['duracion'],
                    duracion_seg=audio_data['duracion_seg'],
                    estado='completado',
                    tipo_reunion=tipo_reunion,
                    usuario=usuario,
                    sample_rate=audio_data['sample_rate'],
                    bit_rate=audio_data['bit_rate'],
                    progreso=audio_data['progreso'],
                    fecha_procesamiento=datetime.now() - timedelta(days=created_count),
                    metadatos_originales={'formato': 'mp3', 'canales': 2},
                    metadatos_procesamiento={'mejorado': True, 'filtros_aplicados': ['ruido', 'eco']},
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Audio de prueba "{audio.titulo}" creado.')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Proceso completado. {created_count} audios de prueba creados.'
            )
        )
