#!/usr/bin/env python
"""
Comando para instalar dependencias de transcripción y verificar el sistema
"""
import os
import sys
import subprocess
import tempfile
import django
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Instala dependencias de IA para transcripción y verifica el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--solo-verificar',
            action='store_true',
            help='Solo verificar dependencias sin instalar'
        )
        parser.add_argument(
            '--instalar-cpu',
            action='store_true',
            help='Instalar versión CPU de PyTorch (más ligera)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== CONFIGURACIÓN DE TRANSCRIPCIÓN CON IA ==='))
        
        if not options['solo_verificar']:
            self.instalar_dependencias(options.get('instalar_cpu', False))
        
        self.verificar_dependencias()
        self.verificar_configuracion()
        self.stdout.write(self.style.SUCCESS('\n✅ Sistema de transcripción configurado correctamente'))

    def instalar_dependencias(self, cpu_only=False):
        """Instala las dependencias necesarias"""
        self.stdout.write('📦 Instalando dependencias de IA...')
        
        requirements_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'requirements.transcripcion.txt')
        
        if not os.path.exists(requirements_file):
            self.stdout.write(self.style.ERROR(f'❌ No se encontró {requirements_file}'))
            return
        
        try:
            # Instalar dependencias básicas
            self.stdout.write('   Instalando paquetes básicos...')
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', requirements_file
            ], check=True, capture_output=True)
            
            # Instalar PyTorch con soporte de CPU o GPU
            if cpu_only:
                self.stdout.write('   Instalando PyTorch (CPU only)...')
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 'torch', 'torchaudio', '--index-url', 
                    'https://download.pytorch.org/whl/cpu'
                ], check=True, capture_output=True)
            else:
                self.stdout.write('   Instalando PyTorch (GPU support)...')
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 'torch', 'torchaudio'
                ], check=True, capture_output=True)
            
            self.stdout.write(self.style.SUCCESS('✅ Dependencias instaladas correctamente'))
            
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'❌ Error instalando dependencias: {e}'))
            raise CommandError('Fallo en la instalación de dependencias')

    def verificar_dependencias(self):
        """Verifica que todas las dependencias estén disponibles"""
        self.stdout.write('\n🔍 Verificando dependencias...')
        
        dependencias = [
            ('whisper', 'OpenAI Whisper'),
            ('pyannote.audio', 'pyannote.audio'),
            ('torch', 'PyTorch'),
            ('torchaudio', 'TorchAudio'),
            ('transformers', 'Transformers'),
            ('librosa', 'Librosa'),
            ('soundfile', 'SoundFile'),
            ('numpy', 'NumPy')
        ]
        
        errores = []
        for modulo, nombre in dependencias:
            try:
                __import__(modulo)
                self.stdout.write(f'   ✅ {nombre}')
            except ImportError:
                self.stdout.write(f'   ❌ {nombre} - NO DISPONIBLE')
                errores.append(nombre)
        
        if errores:
            self.stdout.write(self.style.ERROR(f'\n❌ Dependencias faltantes: {", ".join(errores)}'))
            self.stdout.write('Ejecuta: python manage.py configurar_transcripcion_ai para instalar')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Todas las dependencias están disponibles'))

    def verificar_configuracion(self):
        """Verifica la configuración del sistema"""
        self.stdout.write('\n⚙️ Verificando configuración...')
        
        # Verificar GPU
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else 'Desconocida'
                self.stdout.write(f'   🎮 GPU disponible: {gpu_name} ({gpu_count} dispositivos)')
            else:
                self.stdout.write('   💻 Solo CPU disponible (GPU no detectada)')
        except:
            self.stdout.write('   ⚠️ No se pudo verificar GPU')
        
        # Verificar Whisper
        try:
            import whisper
            modelos = whisper.available_models()
            self.stdout.write(f'   🎤 Whisper disponible: {len(modelos)} modelos ({", ".join(modelos)})')
        except:
            self.stdout.write('   ❌ Whisper no disponible')
        
        # Verificar pyannote
        try:
            from pyannote.audio import Pipeline
            self.stdout.write('   🗣️ pyannote.audio disponible')
        except:
            self.stdout.write('   ❌ pyannote.audio no disponible')
        
        # Verificar configuraciones de transcripción
        try:
            from apps.transcripcion.models import ConfiguracionTranscripcion
            configs = ConfiguracionTranscripcion.objects.filter(activa=True).count()
            self.stdout.write(f'   ⚙️ Configuraciones activas: {configs}')
        except:
            self.stdout.write('   ⚠️ No se pudieron verificar configuraciones')

    def crear_configuracion_ejemplo(self):
        """Crea una configuración de ejemplo si no existe"""
        try:
            from apps.transcripcion.models import ConfiguracionTranscripcion
            
            if not ConfiguracionTranscripcion.objects.filter(activa=True).exists():
                config = ConfiguracionTranscripcion.objects.create(
                    nombre='IA Básica',
                    descripcion='Configuración básica para transcripción con IA',
                    modelo_whisper='base',
                    temperatura=0.0,
                    idioma_principal='es',
                    usar_vad=True,
                    vad_filtro='silero',
                    min_hablantes=1,
                    max_hablantes=4,
                    umbral_clustering=0.7,
                    chunk_duracion=30,
                    usar_gpu=False,
                    filtro_ruido=True,
                    normalizar_audio=True,
                    activa=True,
                    por_defecto=True
                )
                self.stdout.write(f'   ✅ Configuración de ejemplo creada: {config.nombre}')
            
        except Exception as e:
            self.stdout.write(f'   ⚠️ No se pudo crear configuración: {e}')

    def test_transcripcion_simple(self):
        """Prueba básica de transcripción"""
        self.stdout.write('\n🧪 Ejecutando prueba de transcripción...')
        
        try:
            # Crear archivo de audio de prueba simple
            import numpy as np
            import soundfile as sf
            
            # Generar tono simple de 2 segundos
            duration = 2.0
            sample_rate = 16000
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio_data = 0.3 * np.sin(2 * np.pi * 440 * t)  # Tono de 440Hz
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, sample_rate)
                
                # Probar Whisper
                import whisper
                model = whisper.load_model('tiny')
                result = model.transcribe(tmp_file.name)
                
                self.stdout.write(f'   ✅ Prueba Whisper completada')
                self.stdout.write(f'   📝 Texto detectado: "{result["text"]}"')
                
                # Limpiar archivo temporal
                os.unlink(tmp_file.name)
                
        except Exception as e:
            self.stdout.write(f'   ❌ Error en prueba: {e}')
