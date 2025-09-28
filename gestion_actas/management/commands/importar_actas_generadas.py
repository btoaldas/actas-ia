"""
Comando para importar las actas generadas del módulo anterior
al sistema de gestión de actas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.generador_actas.models import ActaGenerada
from gestion_actas.models import GestionActa, EstadoGestionActa


class Command(BaseCommand):
    help = 'Importa las actas generadas del módulo anterior al sistema de gestión'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la importación incluso si ya existe una gestión para el acta',
        )
        
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando importación de actas generadas...'))
        
        # Obtener el estado de edición/depuración
        try:
            estado_edicion = EstadoGestionActa.objects.get(codigo='en_edicion')
        except EstadoGestionActa.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    'Error: No se encontró el estado "en_edicion". '
                    'Asegúrate de ejecutar "init_estados_gestion" primero.'
                )
            )
            return
        
        # Obtener todas las actas generadas
        actas_generadas = ActaGenerada.objects.all()
        total_actas = actas_generadas.count()
        
        if total_actas == 0:
            self.stdout.write(self.style.WARNING('No se encontraron actas generadas para importar.'))
            return
        
        self.stdout.write(f'Encontradas {total_actas} actas generadas.')
        
        importadas = 0
        ya_existian = 0
        errores = 0
        
        for acta_generada in actas_generadas:
            try:
                # Verificar si ya existe una gestión para esta acta
                if hasattr(acta_generada, 'gestion'):
                    if not options['force']:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  - Acta "{acta_generada.titulo}" ya tiene gestión asociada. Omitida.'
                            )
                        )
                        ya_existian += 1
                        continue
                    else:
                        # Si forzamos, eliminamos la gestión existente
                        acta_generada.gestion.delete()
                        self.stdout.write(
                            self.style.WARNING(
                                f'  - Eliminada gestión existente para "{acta_generada.titulo}"'
                            )
                        )
                
                # Crear nueva gestión para esta acta
                gestion_acta = GestionActa.objects.create(
                    acta_generada=acta_generada,
                    estado=estado_edicion,
                    contenido_editado=acta_generada.contenido_final or acta_generada.contenido_borrador or '',
                    contenido_original_backup=acta_generada.contenido_final or acta_generada.contenido_borrador or '',
                    usuario_editor=acta_generada.usuario_creacion,
                    version=1,
                    cambios_realizados={
                        'importado_desde_generador': True,
                        'fecha_importacion': timezone.now().isoformat(),
                        'estado_original': acta_generada.estado
                    },
                    observaciones=f'Importado automáticamente desde generador_actas. Estado original: {acta_generada.estado}'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ Importada: "{acta_generada.titulo}" '
                        f'(ID: {gestion_acta.pk}, Estado: {acta_generada.estado})'
                    )
                )
                importadas += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'  ❌ Error al importar "{acta_generada.titulo}": {str(e)}'
                    )
                )
                errores += 1
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'📊 RESUMEN DE IMPORTACIÓN:'))
        self.stdout.write(f'  • Total actas encontradas: {total_actas}')
        self.stdout.write(self.style.SUCCESS(f'  • Actas importadas: {importadas}'))
        if ya_existian > 0:
            self.stdout.write(self.style.WARNING(f'  • Ya existían: {ya_existian}'))
        if errores > 0:
            self.stdout.write(self.style.ERROR(f'  • Errores: {errores}'))
        
        if importadas > 0:
            self.stdout.write('\n' + self.style.SUCCESS(
                '🎉 Importación completada exitosamente. '
                'Las actas están disponibles en http://localhost:8000/gestion-actas/'
            ))