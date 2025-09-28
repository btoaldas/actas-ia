"""
Comando Django para resetear COMPLETAMENTE todo el sistema de actas
Borra toda la información y deja las actas en estado inicial de gestión
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Resetea COMPLETAMENTE todo el sistema de actas al estado inicial'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar que se quiere hacer el reset completo (DESTRUCTIVO)',
        )
    
    def handle(self, *args, **options):
        
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    '🚨 PELIGRO: Este comando ELIMINARÁ TODA la información procesada\n'
                    '💀 Esta operación es DESTRUCTIVA e IRREVERSIBLE\n'
                    '🔥 Todas las actas volverán al estado inicial de gestión\n\n'
                    'Para ejecutar, usar: --confirm\n'
                    'Ejemplo: python manage.py reset_sistema_completo --confirm'
                )
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                '🔥 INICIANDO RESET COMPLETO DEL SISTEMA\n'
                '=' * 60
            )
        )
        
        try:
            with transaction.atomic():
                # PASO 1: Limpiar portal ciudadano
                self._reset_portal_ciudadano()
                
                # PASO 2: Resetear gestión de actas  
                self._reset_gestion_actas()
                
                # PASO 3: Limpiar registros de auditoría
                self._limpiar_auditoria()
                
                # PASO 4: Limpiar procesamiento de audio
                self._limpiar_audio_processing()
                
            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 RESET COMPLETO EXITOSO\n'
                    '✅ Sistema reseteado al estado inicial de gestión\n'
                    '🎯 Todas las actas listas para edición/depuración\n'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'💥 ERROR EN RESET: {str(e)}')
            )
            logger.error(f"Error en reset completo: {str(e)}")
    
    def _reset_portal_ciudadano(self):
        """Resetea TODAS las actas del portal ciudadano"""
        self.stdout.write('🧹 Limpiando portal ciudadano...')
        
        from apps.pages.models import ActaMunicipal, VisualizacionActa, DescargaActa
        
        # Contar actas antes
        total_actas = ActaMunicipal.objects.count()
        self.stdout.write(f'📊 Actas a resetear: {total_actas}')
        
        # Eliminar registros de visualización y descarga
        visualizaciones = VisualizacionActa.objects.count()
        descargas = DescargaActa.objects.count()
        
        VisualizacionActa.objects.all().delete()
        DescargaActa.objects.all().delete()
        
        self.stdout.write(f'🗑️ Eliminados {visualizaciones} registros de visualización')
        self.stdout.write(f'🗑️ Eliminados {descargas} registros de descarga')
        
        # Resetear TODAS las actas del portal
        import os
        archivos_eliminados = 0
        
        for acta in ActaMunicipal.objects.all():
            # Eliminar archivos físicos
            for archivo in [acta.archivo_pdf, acta.archivo_word, acta.archivo_txt, acta.imagen_preview]:
                if archivo:
                    try:
                        if hasattr(archivo, 'path') and os.path.exists(archivo.path):
                            os.remove(archivo.path)
                            archivos_eliminados += 1
                        archivo.delete(save=False)
                    except Exception as e:
                        logger.warning(f"Error eliminando archivo: {str(e)}")
            
            # Resetear campos del acta
            acta.contenido = ""
            acta.resumen = ""
            acta.orden_del_dia = ""
            acta.acuerdos = ""
            acta.palabras_clave = ""
            acta.observaciones = ""
            acta.transcripcion_ia = False
            acta.precision_ia = None
            acta.tiempo_procesamiento = None
            acta.fecha_publicacion = None
            acta.asistentes = ""
            acta.ausentes = ""
            acta.acceso = 'publico'
            acta.activo = False  # Despublicar del portal
            acta.prioridad = 'normal'
            
            # Limpiar archivos
            acta.archivo_pdf = None
            acta.archivo_word = None
            acta.archivo_txt = None
            acta.imagen_preview = None
            
            acta.save()
        
        self.stdout.write(f'✅ {total_actas} actas reseteadas en portal ciudadano')
        self.stdout.write(f'🗑️ {archivos_eliminados} archivos físicos eliminados')
    
    def _reset_gestion_actas(self):
        """ELIMINA TODAS las actas de gestión manual y resetea al estado inicial"""
        self.stdout.write('🔄 Eliminando gestión de actas...')
        
        try:
            from gestion_actas.models import GestionActa, EstadoGestionActa, ProcesoRevision
            
            # Contar actas en gestión antes de eliminar
            total_gestion = GestionActa.objects.count()
            self.stdout.write(f'📊 Actas en gestión a ELIMINAR: {total_gestion}')
            
            # Eliminar TODOS los procesos de revisión primero
            procesos_revision = ProcesoRevision.objects.count()
            ProcesoRevision.objects.all().delete()
            self.stdout.write(f'🗑️ Eliminados {procesos_revision} procesos de revisión')
            
            # ELIMINAR COMPLETAMENTE todas las actas de gestión
            GestionActa.objects.all().delete()
            self.stdout.write(f'🔥 ELIMINADAS {total_gestion} actas de gestión manual')
            
            # Obtener o crear estado inicial para futuras actas
            estado_inicial, created = EstadoGestionActa.objects.get_or_create(
                codigo='en_edicion',
                defaults={
                    'nombre': 'En Edición/Depuración',
                    'descripcion': 'Acta en proceso de edición y depuración',
                    'color': '#6c757d',
                    'orden': 1,
                    'activo': True,
                    'permite_edicion': True,
                    'requiere_revision': False,
                    'visible_portal': False
                }
            )
            
            if created:
                self.stdout.write('📝 Estado "En Edición" preparado para nuevas actas')
            
        except ImportError:
            self.stdout.write('⚠️ Módulo gestion_actas no disponible')
    
    def _limpiar_auditoria(self):
        """Limpia registros de auditoría del sistema"""
        self.stdout.write('🧹 Limpiando registros de auditoría...')
        
        try:
            from apps.auditoria.models import LogAccion
            
            logs_count = LogAccion.objects.count()
            # Mantener solo logs críticos del sistema
            LogAccion.objects.filter(
                accion__in=['login', 'logout', 'error_critico']
            ).delete()
            
            self.stdout.write(f'🗑️ Limpiados registros de auditoría no críticos')
            
        except ImportError:
            self.stdout.write('ℹ️ Módulo auditoría no disponible')
    
    def _limpiar_audio_processing(self):
        """Limpia registros de procesamiento de audio"""
        self.stdout.write('🎵 Limpiando procesamiento de audio...')
        
        try:
            from apps.audio_processing.models import ProcesamientoAudio
            
            audio_count = ProcesamientoAudio.objects.count()
            ProcesamientoAudio.objects.all().delete()
            
            self.stdout.write(f'🗑️ Eliminados {audio_count} registros de procesamiento de audio')
            
        except ImportError:
            self.stdout.write('ℹ️ Módulo audio_processing no disponible')