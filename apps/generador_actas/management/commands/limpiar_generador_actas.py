"""
Comando de gestión para limpiar datos del módulo Generador de Actas
Útil para desarrollo y testing
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.generador_actas.models import (
    ProveedorIA, SegmentoPlantilla, PlantillaActa, 
    ConfiguracionSegmento, ActaGenerada
)


class Command(BaseCommand):
    help = 'Limpia datos del módulo Generador de Actas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma la eliminación de datos',
        )
        parser.add_argument(
            '--actas-only',
            action='store_true',
            help='Solo eliminar actas generadas',
        )
        parser.add_argument(
            '--plantillas-only',
            action='store_true',
            help='Solo eliminar plantillas y configuraciones',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'Este comando eliminará datos. Usa --confirm para proceder.'
                )
            )
            return

        self.stdout.write(
            self.style.WARNING('Iniciando limpieza de datos...')
        )

        try:
            with transaction.atomic():
                if options['actas_only']:
                    self.limpiar_actas_generadas()
                elif options['plantillas_only']:
                    self.limpiar_plantillas()
                else:
                    self.limpiar_todo()

            self.stdout.write(
                self.style.SUCCESS('✓ Limpieza completada exitosamente')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la limpieza: {str(e)}')
            )
            raise

    def limpiar_actas_generadas(self):
        """Eliminar solo actas generadas"""
        count = ActaGenerada.objects.count()
        ActaGenerada.objects.all().delete()
        self.stdout.write(f'  ✓ Eliminadas {count} actas generadas')

    def limpiar_plantillas(self):
        """Eliminar plantillas y configuraciones"""
        # Las configuraciones se eliminan automáticamente por CASCADE
        count = PlantillaActa.objects.count()
        PlantillaActa.objects.all().delete()
        self.stdout.write(f'  ✓ Eliminadas {count} plantillas y sus configuraciones')

    def limpiar_todo(self):
        """Eliminar todos los datos del módulo"""
        # Orden importante para evitar errores de integridad referencial
        
        # 1. Actas generadas
        actas_count = ActaGenerada.objects.count()
        ActaGenerada.objects.all().delete()
        self.stdout.write(f'  ✓ Eliminadas {actas_count} actas generadas')
        
        # 2. Configuraciones de segmentos (se eliminan con plantillas por CASCADE)
        # 3. Plantillas
        plantillas_count = PlantillaActa.objects.count()
        PlantillaActa.objects.all().delete()
        self.stdout.write(f'  ✓ Eliminadas {plantillas_count} plantillas')
        
        # 4. Segmentos
        segmentos_count = SegmentoPlantilla.objects.count()
        SegmentoPlantilla.objects.all().delete()
        self.stdout.write(f'  ✓ Eliminados {segmentos_count} segmentos')
        
        # 5. Proveedores IA
        proveedores_count = ProveedorIA.objects.count()
        ProveedorIA.objects.all().delete()
        self.stdout.write(f'  ✓ Eliminados {proveedores_count} proveedores IA')
        
        self.stdout.write('  ✓ Todos los datos del módulo han sido eliminados')