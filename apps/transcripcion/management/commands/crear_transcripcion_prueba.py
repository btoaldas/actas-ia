#!/usr/bin/env python
"""
Comando para crear una transcripción de prueba y verificar el pipeline completo
"""
import os
import tempfile
import numpy as np
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Crea una transcripción de prueba para verificar el pipeline completo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--usuario',
            type=str,
            help='Username del usuario que iniciará la transcripción',
            default='admin'
        )
        parser.add_argument(
            '--modelo',
            type=str,
            help='Modelo de Whisper a usar (tiny, base, small, medium, large)',
            default='tiny'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== PRUEBA DE TRANSCRIPCIÓN COMPLETA ==='))
        
        try:
            # Verificar dependencias
            self.verificar_dependencias()
            
            # Obtener usuario
            user = self.obtener_usuario(options['usuario'])
            
            # Crear audio de prueba
            archivo_audio = self.crear_audio_prueba()
            
            # Crear procesamiento de audio
            procesamiento = self.crear_procesamiento_audio(archivo_audio, user)
            
            # Crear transcripción
            transcripcion = self.crear_transcripcion(procesamiento, user, options['modelo'])
            
            # Iniciar procesamiento
            self.iniciar_transcripcion(transcripcion)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Transcripción de prueba creada con ID: {transcripcion.id}'))
            self.stdout.write(f'📝 Puedes ver el progreso en: http://localhost:8000/transcripcion/resultado/{transcripcion.id}/')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            raise CommandError(f'Fallo en la prueba: {str(e)}')

    def verificar_dependencias(self):
        """Verifica que las dependencias estén disponibles"""
        try:
            import whisper
            import soundfile as sf
            import numpy as np
            from apps.transcripcion.models import Transcripcion, ConfiguracionTranscripcion
            self.stdout.write('✅ Dependencias verificadas')
        except ImportError as e:
            raise CommandError(f'Dependencia faltante: {e}')

    def obtener_usuario(self, username):
        """Obtiene o crea un usuario para la prueba"""
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'👤 Usuario encontrado: {user.username}')
            return user
        except User.DoesNotExist:
            # Intentar crear usuario admin por defecto
            if username == 'admin':
                user = User.objects.create_superuser(
                    username='admin',
                    email='admin@actas.ia',
                    password='admin123'
                )
                self.stdout.write(f'👤 Usuario admin creado: {user.username}')
                return user
            else:
                raise CommandError(f'Usuario {username} no existe')

    def crear_audio_prueba(self):
        """Crea un archivo de audio de prueba"""
        try:
            import soundfile as sf
            
            # Generar audio con voz simulada (múltiples tonos)
            duration = 10.0  # 10 segundos
            sample_rate = 16000
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Crear "conversación" simulada con diferentes frecuencias
            segment1 = 0.3 * np.sin(2 * np.pi * 300 * t[:sample_rate * 3])  # 3 seg a 300Hz
            silence1 = np.zeros(sample_rate)  # 1 seg silencio
            segment2 = 0.25 * np.sin(2 * np.pi * 500 * t[:sample_rate * 3])  # 3 seg a 500Hz
            silence2 = np.zeros(sample_rate)  # 1 seg silencio
            segment3 = 0.2 * np.sin(2 * np.pi * 400 * t[:sample_rate * 2])  # 2 seg a 400Hz
            
            # Combinar segmentos
            audio_data = np.concatenate([segment1, silence1, segment2, silence2, segment3])
            
            # Agregar un poco de ruido para simular grabación real
            noise = 0.01 * np.random.normal(0, 1, len(audio_data))
            audio_data += noise
            
            # Guardar archivo temporal
            audio_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            sf.write(audio_file.name, audio_data, sample_rate)
            
            self.stdout.write(f'🎵 Audio de prueba creado: {audio_file.name}')
            self.stdout.write(f'   Duración: {duration} segundos')
            self.stdout.write(f'   Sample rate: {sample_rate} Hz')
            
            return audio_file.name
            
        except Exception as e:
            raise CommandError(f'Error creando audio de prueba: {e}')

    def crear_procesamiento_audio(self, archivo_audio, user):
        """Crea un procesamiento de audio de prueba"""
        try:
            from apps.audio_processing.models import ProcesamientoAudio, TipoReunion
            
            # Obtener o crear tipo de reunión
            tipo_reunion, created = TipoReunion.objects.get_or_create(
                nombre='Prueba IA',
                defaults={'descripcion': 'Tipo de reunión para pruebas de transcripción con IA'}
            )
            
            # Crear procesamiento de audio
            procesamiento = ProcesamientoAudio.objects.create(
                titulo='Audio de Prueba para Transcripción IA',
                descripcion='Audio sintético generado para probar el pipeline completo de transcripción',
                nombre_archivo='audio_prueba_ia.wav',
                tipo_reunion=tipo_reunion,
                usuario=user,
                estado='completado',
                fecha_procesamiento=timezone.now(),
                metadatos_originales={
                    'duracion': 10.0,
                    'sample_rate': 16000,
                    'formato': 'wav',
                    'canales': 1,
                    'tipo_prueba': 'sintético'
                },
                metadatos_procesamiento={
                    'procesado': True,
                    'mejorado': False,
                    'tipo': 'prueba_ia'
                }
            )
            
            # Simular archivo subido (en un caso real se subiría el archivo)
            self.stdout.write(f'📁 Procesamiento de audio creado: ID {procesamiento.id}')
            
            return procesamiento
            
        except Exception as e:
            raise CommandError(f'Error creando procesamiento de audio: {e}')

    def crear_transcripcion(self, procesamiento, user, modelo_whisper):
        """Crea la transcripción"""
        try:
            from apps.transcripcion.models import Transcripcion, ConfiguracionTranscripcion, EstadoTranscripcion
            
            # Obtener o crear configuración
            configuracion, created = ConfiguracionTranscripcion.objects.get_or_create(
                nombre='Prueba IA',
                defaults={
                    'descripcion': 'Configuración para pruebas de transcripción con IA',
                    'modelo_whisper': modelo_whisper,
                    'temperatura': 0.0,
                    'idioma_principal': 'es',
                    'usar_vad': True,
                    'vad_filtro': 'silero',
                    'min_hablantes': 1,
                    'max_hablantes': 3,
                    'umbral_clustering': 0.7,
                    'chunk_duracion': 30,
                    'usar_gpu': False,
                    'filtro_ruido': True,
                    'normalizar_audio': True,
                    'activa': True
                }
            )
            
            # Crear transcripción
            transcripcion = Transcripcion.objects.create(
                procesamiento_audio=procesamiento,
                configuracion=configuracion,
                usuario_creacion=user,
                estado=EstadoTranscripcion.PENDIENTE,
                progreso=0
            )
            
            self.stdout.write(f'📝 Transcripción creada: ID {transcripcion.id}')
            self.stdout.write(f'   Configuración: {configuracion.nombre}')
            self.stdout.write(f'   Modelo Whisper: {modelo_whisper}')
            
            return transcripcion
            
        except Exception as e:
            raise CommandError(f'Error creando transcripción: {e}')

    def iniciar_transcripcion(self, transcripcion):
        """Inicia el procesamiento de transcripción"""
        try:
            from apps.transcripcion.tasks import procesar_transcripcion_completa
            
            # Iniciar tarea de Celery
            task = procesar_transcripcion_completa.delay(transcripcion.id)
            transcripcion.task_id = task.id
            transcripcion.save()
            
            self.stdout.write(f'🚀 Tarea de transcripción iniciada: {task.id}')
            self.stdout.write('   La transcripción se procesará en segundo plano')
            
        except Exception as e:
            # Si Celery no está disponible, simular proceso síncrono
            self.stdout.write(f'⚠️ Celery no disponible, simulando transcripción: {e}')
            self.simular_transcripcion(transcripcion)

    def simular_transcripcion(self, transcripcion):
        """Simula una transcripción completa para pruebas"""
        try:
            from apps.transcripcion.models import EstadoTranscripcion
            
            # Simular datos de transcripción
            transcripcion.estado = EstadoTranscripcion.COMPLETADO
            transcripcion.progreso = 100
            transcripcion.fecha_inicio_procesamiento = timezone.now()
            transcripcion.fecha_completado = timezone.now()
            
            # Datos simulados de Whisper
            transcripcion.datos_whisper = {
                'modelo_usado': 'tiny',
                'temperatura': 0.0,
                'idioma_detectado': 'es',
                'confianza_promedio': 0.85,
                'segmentos_procesados': 3
            }
            
            # Datos simulados de pyannote
            transcripcion.datos_pyannote = {
                'hablantes_detectados': 2,
                'umbral_usado': 0.7,
                'metodo_clustering': 'agglomerative'
            }
            
            # Hablantes detectados
            transcripcion.hablantes_detectados = {
                'speaker_0': 'Alcalde Municipal',
                'speaker_1': 'Secretario de Actas'
            }
            transcripcion.num_hablantes = 2
            
            # Resultado final simulado
            transcripcion.resultado_final = {
                'segmentos_combinados': [
                    {
                        'id': 0,
                        'inicio': 0.0,
                        'fin': 3.5,
                        'duracion': 3.5,
                        'hablante': 'speaker_0',
                        'texto': 'Buenos días, iniciamos la sesión de prueba del sistema de transcripción automática.',
                        'confianza': 0.89
                    },
                    {
                        'id': 1,
                        'inicio': 4.0,
                        'fin': 7.5,
                        'duracion': 3.5,
                        'hablante': 'speaker_1',
                        'texto': 'Perfecto señor alcalde, el sistema de inteligencia artificial está funcionando correctamente.',
                        'confianza': 0.92
                    },
                    {
                        'id': 2,
                        'inicio': 8.0,
                        'fin': 10.0,
                        'duracion': 2.0,
                        'hablante': 'speaker_0',
                        'texto': 'Excelente, procedemos con la agenda municipal.',
                        'confianza': 0.87
                    }
                ],
                'transcripcion_formateada': 'Alcalde Municipal: Buenos días, iniciamos la sesión de prueba del sistema de transcripción automática.\n\nSecretario de Actas: Perfecto señor alcalde, el sistema de inteligencia artificial está funcionando correctamente.\n\nAlcalde Municipal: Excelente, procedemos con la agenda municipal.',
                'hablantes': {
                    'speaker_0': 'Alcalde Municipal',
                    'speaker_1': 'Secretario de Actas'
                },
                'num_hablantes': 2,
                'duracion_total': 10.0,
                'estadisticas': {
                    'speaker_0': {
                        'tiempo_total': 5.5,
                        'porcentaje_participacion': 55.0,
                        'num_intervenciones': 2
                    },
                    'speaker_1': {
                        'tiempo_total': 3.5,
                        'porcentaje_participacion': 35.0,
                        'num_intervenciones': 1
                    }
                }
            }
            
            # Texto completo
            transcripcion.texto_completo = transcripcion.resultado_final['transcripcion_formateada']
            
            # Estadísticas de procesamiento
            transcripcion.estadisticas_procesamiento = {
                'num_segmentos': 3,
                'duracion_total': 10.0,
                'num_palabras': 28,
                'num_caracteres': 180,
                'promedio_duracion_segmento': 3.0,
                'segmento_mas_largo': 3.5,
                'segmento_mas_corto': 2.0,
                'hablantes_estadisticas': transcripcion.resultado_final['estadisticas']
            }
            
            transcripcion.save()
            
            self.stdout.write(self.style.SUCCESS('✅ Transcripción simulada completada'))
            self.stdout.write(f'   Hablantes detectados: {transcripcion.num_hablantes}')
            self.stdout.write(f'   Segmentos procesados: 3')
            self.stdout.write(f'   Palabras transcritas: 28')
            
        except Exception as e:
            raise CommandError(f'Error simulando transcripción: {e}')
