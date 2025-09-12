from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.transcripcion.models import Transcripcion, ConfiguracionTranscripcion
from apps.transcripcion.tasks import procesar_transcripcion_completa
from apps.audio_processing.models import ProcesamientoAudio


class Command(BaseCommand):
    help = 'Comando de prueba para el sistema de transcripción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-type',
            type=str,
            choices=['simulacion', 'procesamiento', 'configuracion'],
            default='simulacion',
            help='Tipo de prueba a ejecutar'
        )
        parser.add_argument(
            '--audio-id',
            type=int,
            help='ID del audio procesado para crear transcripción de prueba'
        )

    def handle(self, *args, **options):
        test_type = options['test_type']
        
        if test_type == 'simulacion':
            self.test_simulacion()
        elif test_type == 'procesamiento':
            self.test_procesamiento(options.get('audio_id'))
        elif test_type == 'configuracion':
            self.test_configuracion()

    def test_simulacion(self):
        """Prueba de simulación sin procesamiento real"""
        self.stdout.write(self.style.SUCCESS('🎯 Iniciando prueba de simulación...'))
        
        # Verificar configuración activa
        config = ConfiguracionTranscripcion.get_configuracion_activa()
        if not config:
            self.stdout.write(self.style.ERROR('❌ No hay configuración activa'))
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Configuración activa: {config.nombre}')
        )
        
        # Buscar audios procesados sin transcripción
        audios_disponibles = ProcesamientoAudio.objects.filter(
            estado='completado'
        ).exclude(
            transcripcion__isnull=False
        )[:5]
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Audios disponibles para transcribir: {audios_disponibles.count()}')
        )
        
        for audio in audios_disponibles:
            self.stdout.write(f'  - {audio.titulo} ({audio.archivo_audio.name})')
        
        self.stdout.write(self.style.SUCCESS('🎉 Prueba de simulación completada'))

    def test_procesamiento(self, audio_id):
        """Prueba de procesamiento real con un audio específico"""
        if not audio_id:
            self.stdout.write(self.style.ERROR('❌ Debe especificar --audio-id'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'🎯 Iniciando prueba de procesamiento para audio ID: {audio_id}'))
        
        try:
            audio = ProcesamientoAudio.objects.get(id=audio_id)
            self.stdout.write(f'✓ Audio encontrado: {audio.titulo}')
            
            if audio.estado != 'completado':
                self.stdout.write(self.style.ERROR(f'❌ Audio no está completado (estado: {audio.estado})'))
                return
            
            if hasattr(audio, 'transcripcion'):
                self.stdout.write(self.style.WARNING('⚠️  Audio ya tiene transcripción'))
                return
            
            # Crear transcripción
            config = ConfiguracionTranscripcion.get_configuracion_activa()
            usuario = User.objects.filter(is_superuser=True).first()
            
            transcripcion = Transcripcion.objects.create(
                procesamiento_audio=audio,
                configuracion_utilizada=config,
                usuario_creacion=usuario
            )
            
            self.stdout.write(f'✓ Transcripción creada: ID {transcripcion.id}')
            
            # Iniciar procesamiento
            task = procesar_transcripcion_completa.delay(transcripcion.id)
            transcripcion.task_id_celery = task.id
            transcripcion.save()
            
            self.stdout.write(f'✓ Tarea de procesamiento iniciada: {task.id}')
            self.stdout.write(self.style.SUCCESS('🎉 Prueba de procesamiento iniciada'))
            
        except ProcesamientoAudio.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Audio con ID {audio_id} no encontrado'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error en procesamiento: {str(e)}'))

    def test_configuracion(self):
        """Prueba de configuración del sistema"""
        self.stdout.write(self.style.SUCCESS('🎯 Verificando configuración del sistema...'))
        
        # Verificar configuraciones
        configs = ConfiguracionTranscripcion.objects.all()
        self.stdout.write(f'✓ Configuraciones existentes: {configs.count()}')
        
        for config in configs:
            status = "ACTIVA" if config.activa else "Inactiva"
            self.stdout.write(f'  - {config.nombre} ({status})')
            self.stdout.write(f'    Whisper: {config.modelo_whisper}, Idioma: {config.idioma_principal}')
            self.stdout.write(f'    Hablantes: {config.min_hablantes}-{config.max_hablantes}')
        
        # Verificar transcripciones existentes
        transcripciones = Transcripcion.objects.all()
        self.stdout.write(f'✓ Transcripciones existentes: {transcripciones.count()}')
        
        estados_count = {}
        for t in transcripciones:
            estados_count[t.estado] = estados_count.get(t.estado, 0) + 1
        
        for estado, count in estados_count.items():
            self.stdout.write(f'  - {estado}: {count}')
        
        self.stdout.write(self.style.SUCCESS('🎉 Verificación de configuración completada'))
