"""
Script para inicializar datos básicos del sistema de audio processing
"""
from django.core.management.base import BaseCommand
from apps.audio_processing.models import TipoReunion


class Command(BaseCommand):
    help = 'Inicializa datos básicos para el sistema de procesamiento de audio'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando datos básicos...')
        
        # Crear tipos de reunión básicos si no existen
        tipos_reunion = [
            {
                'nombre': 'Concejo Municipal',
                'descripcion': 'Sesiones ordinarias y extraordinarias del Concejo Municipal',
                'activo': True
            },
            {
                'nombre': 'Audiencia Pública',
                'descripcion': 'Audiencias públicas para participación ciudadana',
                'activo': True
            },
            {
                'nombre': 'Reunión de Comisión',
                'descripcion': 'Reuniones de las diferentes comisiones municipales',
                'activo': True
            },
            {
                'nombre': 'Cabildo Abierto',
                'descripcion': 'Cabildos abiertos para consulta ciudadana',
                'activo': True
            },
            {
                'nombre': 'Reunión Administrativa',
                'descripcion': 'Reuniones administrativas internas',
                'activo': True
            },
            {
                'nombre': 'Consulta Popular',
                'descripcion': 'Sesiones de consulta popular',
                'activo': True
            }
        ]
        
        for tipo_data in tipos_reunion:
            tipo, created = TipoReunion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(f'✓ Tipo de reunión creado: {tipo.nombre}')
            else:
                self.stdout.write(f'- Tipo de reunión existente: {tipo.nombre}')
        
        self.stdout.write(self.style.SUCCESS('✅ Datos básicos inicializados correctamente'))
