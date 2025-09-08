"""
Comando para probar el sistema de logging de audio processing
"""
from django.core.management.base import BaseCommand
from apps.audio_processing.logging_helper import (
    log_sistema, log_admin_action, log_archivo_operacion, log_procesamiento_audio
)
from apps.audio_processing.models import ProcesamientoAudio
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Probar el sistema de logging de audio processing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            type=str,
            default='all',
            help='Tipo de test: all, sistema, admin, archivo, procesamiento'
        )
    
    def handle(self, *args, **options):
        test_type = options['test_type']
        
        self.stdout.write(
            self.style.SUCCESS(f'Iniciando test de logging: {test_type}')
        )
        
        try:
            if test_type in ['all', 'sistema']:
                self._test_log_sistema()
            
            if test_type in ['all', 'admin']:
                self._test_log_admin()
            
            if test_type in ['all', 'archivo']:
                self._test_log_archivo()
            
            if test_type in ['all', 'procesamiento']:
                self._test_log_procesamiento()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Tests de logging completados exitosamente')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error en tests de logging: {e}')
            )
    
    def _test_log_sistema(self):
        """Test de logging del sistema"""
        self.stdout.write('🔍 Probando log del sistema...')
        
        log_sistema(
            nivel='INFO',
            categoria='TEST_SISTEMA',
            subcategoria='PRUEBA_COMANDO',
            mensaje='Test de logging del sistema desde comando de gestión',
            datos_extra={
                'test_data': 'Datos de prueba',
                'timestamp_test': '2025-09-07'
            },
            modulo='audio_processing_test'
        )
        
        self.stdout.write('  ✅ Log del sistema registrado')
    
    def _test_log_admin(self):
        """Test de logging administrativo"""
        self.stdout.write('🔍 Probando log administrativo...')
        
        log_admin_action(
            request=None,  # Sin request en comando
            modelo_afectado='ProcesamientoAudio',
            accion='TEST',
            objeto_id='test_123',
            campos_modificados=['titulo', 'estado'],
            valores_anteriores={'titulo': 'test_anterior', 'estado': 'pendiente'},
            valores_nuevos={'titulo': 'test_nuevo', 'estado': 'completado'}
        )
        
        self.stdout.write('  ✅ Log administrativo registrado')
    
    def _test_log_archivo(self):
        """Test de logging de archivos"""
        self.stdout.write('🔍 Probando log de archivos...')
        
        log_archivo_operacion(
            operacion='TEST_UPLOAD',
            archivo_nombre='test_audio.mp3',
            archivo_path='/test/path/test_audio.mp3',
            archivo_size_bytes=1024000,
            archivo_tipo_mime='audio/mpeg',
            resultado='SUCCESS',
            metadatos={
                'test': True,
                'duracion': 120,
                'calidad': 'alta'
            }
        )
        
        self.stdout.write('  ✅ Log de archivo registrado')
    
    def _test_log_procesamiento(self):
        """Test de logging específico de procesamiento"""
        self.stdout.write('🔍 Probando log de procesamiento...')
        
        # Buscar un procesamiento existente o crear uno mock
        try:
            procesamiento = ProcesamientoAudio.objects.first()
            if not procesamiento:
                # Crear un procesamiento mock para testing
                user = User.objects.first()
                if user:
                    procesamiento = ProcesamientoAudio.objects.create(
                        usuario=user,
                        titulo='Test Procesamiento para Logging',
                        estado='pendiente',
                        descripcion='Procesamiento creado para probar el sistema de logging'
                    )
                    self.stdout.write('  📝 Procesamiento de prueba creado')
            
            if procesamiento:
                log_procesamiento_audio(
                    accion='test',
                    procesamiento=procesamiento,
                    datos_adicionales={
                        'test_logging': True,
                        'comando_gestion': True
                    }
                )
                self.stdout.write('  ✅ Log de procesamiento registrado')
            else:
                self.stdout.write('  ⚠️  No se pudo crear procesamiento de prueba')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Error en test de procesamiento: {e}')
    
    def _verificar_logs_en_bd(self):
        """Verificar que los logs se guardaron correctamente"""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                # Verificar logs del sistema
                cursor.execute("SELECT COUNT(*) FROM logs.sistema_logs WHERE categoria LIKE '%TEST%'")
                count_sistema = cursor.fetchone()[0]
                
                # Verificar logs administrativos  
                cursor.execute("SELECT COUNT(*) FROM logs.admin_logs WHERE accion = 'TEST'")
                count_admin = cursor.fetchone()[0]
                
                # Verificar logs de archivos
                cursor.execute("SELECT COUNT(*) FROM logs.archivo_logs WHERE operacion = 'TEST_UPLOAD'")
                count_archivo = cursor.fetchone()[0]
                
                self.stdout.write(f'📊 Logs en BD:')
                self.stdout.write(f'  - Sistema: {count_sistema}')
                self.stdout.write(f'  - Admin: {count_admin}')
                self.stdout.write(f'  - Archivo: {count_archivo}')
                
        except Exception as e:
            self.stdout.write(f'❌ Error verificando logs en BD: {e}')
