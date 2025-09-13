from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.audio_processing.models import ProcesamientoAudio
import uuid


class ConfiguracionTranscripcion(models.Model):
    """Configuración global para transcripción y diarización"""
    
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo de la configuración"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción detallada de la configuración"
    )
    activa = models.BooleanField(
        default=True,
        help_text="Si esta configuración está activa para usar"
    )
    
    # Configuración Whisper
    modelo_whisper = models.CharField(
        max_length=50,
        choices=[
            ('tiny', 'Tiny (39 MB) - Rápido, menor precisión'),
            ('base', 'Base (74 MB) - Balanceado'),
            ('small', 'Small (244 MB) - Buena precisión'),
            ('medium', 'Medium (769 MB) - Alta precisión'),
            ('large', 'Large (1550 MB) - Máxima precisión'),
            ('large-v2', 'Large V2 (1550 MB) - Versión optimizada'),
            ('large-v3', 'Large V3 (1550 MB) - Última versión'),
        ],
        default='base',
        help_text="Modelo de Whisper para transcripción"
    )
    idioma_principal = models.CharField(
        max_length=10,
        choices=[
            ('es', 'Español'),
            ('en', 'Inglés'),
            ('auto', 'Detección automática'),
        ],
        default='es'
    )
    temperatura = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Creatividad en la transcripción (0.0-1.0)"
    )
    usar_vad = models.BooleanField(
        default=True,
        help_text="Usar detección de actividad vocal (VAD)"
    )
    vad_filtro = models.CharField(
        max_length=20,
        choices=[
            ('silero', 'Silero (Recomendado)'),
            ('auditok', 'Auditok'),
        ],
        default='silero',
        help_text="Tipo de filtro VAD a utilizar"
    )
    
    # Configuración pyannote
    modelo_diarizacion = models.CharField(
        max_length=100,
        default='pyannote/speaker-diarization@2.1',
        help_text="Modelo de pyannote para diarización"
    )
    min_hablantes = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Número mínimo de hablantes esperados"
    )
    max_hablantes = models.IntegerField(
        default=8,
        validators=[MinValueValidator(2), MaxValueValidator(20)],
        help_text="Número máximo de hablantes esperados"
    )
    umbral_clustering = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.1), MaxValueValidator(1.0)],
        help_text="Umbral para clustering de hablantes (0.1-1.0)"
    )
    
    # Configuración de procesamiento
    chunk_duracion = models.IntegerField(
        default=30,
        validators=[MinValueValidator(10), MaxValueValidator(300)],
        help_text="Duración de chunks en segundos para procesamiento"
    )
    overlap_duracion = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        help_text="Duración de overlap entre chunks en segundos"
    )
    usar_gpu = models.BooleanField(
        default=False,
        help_text="Usar GPU si está disponible"
    )
    usar_enhanced_diarization = models.BooleanField(
        default=True,
        help_text="Usar características avanzadas de diarización"
    )
    
    # Configuración de calidad
    filtro_ruido = models.BooleanField(
        default=True,
        help_text="Aplicar filtro de reducción de ruido"
    )
    normalizar_audio = models.BooleanField(
        default=True,
        help_text="Normalizar volumen del audio antes de procesar"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='configuraciones_transcripcion_creadas'
    )
    
    class Meta:
        verbose_name = "Configuración de Transcripción"
        verbose_name_plural = "Configuraciones de Transcripción"
        ordering = ['-activa', '-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} ({'Activa' if self.activa else 'Inactiva'})"
    
    @classmethod
    def get_configuracion_defecto(cls):
        """Obtiene la configuración por defecto activa"""
        return cls.objects.filter(activa=True).first()
    
    def to_whisper_config(self):
        """Convierte a configuración para Whisper"""
        return {
            'model': self.modelo_whisper,
            'language': self.idioma_principal if self.idioma_principal != 'auto' else None,
            'temperature': self.temperatura,
            'use_vad': self.usar_vad,
            'vad_filter': self.vad_filtro,
            'chunk_length': self.chunk_duracion,
            'overlap_length': self.overlap_duracion,
        }
    
    def to_pyannote_config(self):
        """Convierte la configuración a formato pyannote"""
        return {
            'min_speakers': self.min_hablantes,
            'max_speakers': self.max_hablantes,
            'clustering_threshold': self.umbral_clustering,
            'enhanced_diarization': self.usar_enhanced_diarization,
            'chunk_duration': self.chunk_duracion,
            'overlap_duration': self.overlap_duracion,
        }

    def to_json(self):
        """Convierte la configuración completa a JSON para JavaScript"""
        import json
        return json.dumps({
            'modelo_whisper': self.modelo_whisper,
            'temperatura': float(self.temperatura),
            'idioma_principal': self.idioma_principal,
            'usar_vad': self.usar_vad,
            'vad_filtro': self.vad_filtro,
            'min_hablantes': self.min_hablantes,
            'max_hablantes': self.max_hablantes,
            'umbral_clustering': float(self.umbral_clustering),
            'usar_enhanced_diarization': self.usar_enhanced_diarization,
            'chunk_duracion': self.chunk_duracion,
            'overlap_duracion': self.overlap_duracion,
            'filtro_ruido': self.filtro_ruido,
            'normalizar_audio': self.normalizar_audio,
            'usar_gpu': self.usar_gpu,
        })

    @classmethod
    def get_configuracion_defecto(cls):
        """Obtiene la configuración activa por defecto"""
        return cls.objects.filter(activa=True).first() or cls.objects.first()
    min_hablantes = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Número mínimo de hablantes esperados"
    )
    max_hablantes = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Número máximo de hablantes esperados"
    )
    
    # Configuración de procesamiento
    segmentacion_minima = models.FloatField(
        default=1.0,
        help_text="Duración mínima de segmento en segundos"
    )
    umbral_confianza = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Umbral mínimo de confianza para aceptar transcripción"
    )
    
    # Metadatos
    activa = models.BooleanField(default=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='configuraciones_transcripcion_creadas'
    )

    class Meta:
        verbose_name = "Configuración de Transcripción"
        verbose_name_plural = "Configuraciones de Transcripción"
        ordering = ['-activa', '-fecha_actualizacion']

    def __str__(self):
        return f"{self.nombre} ({'Activa' if self.activa else 'Inactiva'})"

    @classmethod
    def get_configuracion_activa(cls):
        """Obtiene la configuración activa para transcripción"""
        return cls.objects.filter(activa=True).first()


class EstadoTranscripcion(models.TextChoices):
    """Estados posibles de una transcripción"""
    PENDIENTE = 'pendiente', 'Pendiente'
    EN_PROCESO = 'en_proceso', 'En Proceso'
    TRANSCRIBIENDO = 'transcribiendo', 'Transcribiendo'
    DIARIZANDO = 'diarizando', 'Diarizando'
    PROCESANDO = 'procesando', 'Procesando Resultados'
    COMPLETADO = 'completado', 'Completado'
    ERROR = 'error', 'Error'
    CANCELADO = 'cancelado', 'Cancelado'


class Transcripcion(models.Model):
    """Modelo principal para transcripciones"""
    
    # Identificación
    id_transcripcion = models.UUIDField(
        default=uuid.uuid4, 
        editable=False, 
        unique=True
    )
    
    # Relación con audio procesado
    procesamiento_audio = models.OneToOneField(
        ProcesamientoAudio,
        on_delete=models.CASCADE,
        related_name='transcripcion'
    )
    
    # Estado y configuración
    estado = models.CharField(
        max_length=20,
        choices=EstadoTranscripcion.choices,
        default=EstadoTranscripcion.PENDIENTE
    )
    configuracion_utilizada = models.ForeignKey(
        ConfiguracionTranscripcion,
        on_delete=models.PROTECT,
        null=True, blank=True
    )
    
    # Resultados de transcripción
    texto_completo = models.TextField(
        blank=True,
        help_text="Texto completo transcrito sin diarización"
    )
    transcripcion_json = models.JSONField(
        default=dict,
        help_text="Resultado estructurado de Whisper con timestamps"
    )
    
    # Resultados de diarización
    diarizacion_json = models.JSONField(
        default=dict,
        help_text="Resultado de pyannote con segmentos por hablante"
    )
    
    # Resultado combinado y editado
    conversacion_json = models.JSONField(
        default=list,
        help_text="Conversación estructurada con hablantes, tiempos y texto"
    )
    
    # Metadatos de hablantes
    hablantes_detectados = models.JSONField(
        default=list,
        help_text="Lista de hablantes detectados automáticamente"
    )
    hablantes_identificados = models.JSONField(
        default=dict,
        help_text="Mapeo de hablantes detectados a nombres reales"
    )
    
    # Estadísticas y métricas
    duracion_total = models.FloatField(null=True, blank=True)
    numero_hablantes = models.IntegerField(default=0)
    numero_segmentos = models.IntegerField(default=0)
    confianza_promedio = models.FloatField(null=True, blank=True)
    palabras_totales = models.IntegerField(default=0)
    
    # Análisis adicional
    estadisticas_json = models.JSONField(
        default=dict,
        help_text="Estadísticas detalladas: tiempo por hablante, densidad, etc."
    )
    palabras_clave = models.JSONField(
        default=list,
        help_text="Palabras clave extraídas del contenido"
    )
    temas_detectados = models.JSONField(
        default=list,
        help_text="Temas principales identificados"
    )
    
    # Control de procesamiento
    tiempo_inicio_proceso = models.DateTimeField(null=True, blank=True)
    tiempo_fin_proceso = models.DateTimeField(null=True, blank=True)
    mensaje_error = models.TextField(blank=True)
    progreso_porcentaje = models.IntegerField(default=0)
    task_id_celery = models.CharField(max_length=100, blank=True)
    parametros_personalizados = models.JSONField(
        default=dict,
        help_text="Parámetros personalizados que sobrescriben la configuración base"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='transcripciones_creadas'
    )
    
    # Versionado
    version_actual = models.IntegerField(default=1)
    editado_manualmente = models.BooleanField(default=False)
    fecha_ultima_edicion = models.DateTimeField(null=True, blank=True)
    usuario_ultima_edicion = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='transcripciones_editadas'
    )

    class Meta:
        verbose_name = "Transcripción"
        verbose_name_plural = "Transcripciones"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['procesamiento_audio']),
        ]

    def __str__(self):
        """Representación segura del objeto para evitar AttributeError.
        Usa campos existentes en ProcesamientoAudio.
        """
        try:
            titulo_audio = getattr(self.procesamiento_audio, 'titulo', None) or ''
        except Exception:
            titulo_audio = ''
        estado_display = ''
        try:
            estado_display = self.get_estado_display()
        except Exception:
            estado_display = str(getattr(self, 'estado', ''))
        base = "Transcripción"
        if titulo_audio:
            base += f" {titulo_audio}"
        if estado_display:
            base += f" - {estado_display}"
        return base

    @property
    def duracion_proceso(self):
        """Calcula la duración del proceso de transcripción"""
        if self.tiempo_inicio_proceso and self.tiempo_fin_proceso:
            return (self.tiempo_fin_proceso - self.tiempo_inicio_proceso).total_seconds()
        return None

    @property
    def esta_completado(self):
        """Verifica si la transcripción está completada"""
        return self.estado == EstadoTranscripcion.COMPLETADO

    @property
    def tiene_error(self):
        """Verifica si hay errores en la transcripción"""
        return self.estado == EstadoTranscripcion.ERROR

    def get_nombre_hablante(self, speaker_id):
        """Obtiene el nombre real de un hablante por su ID"""
        return self.hablantes_identificados.get(speaker_id, f"Hablante {speaker_id}")

    def get_configuracion_completa(self):
        """
        Combina la configuración base con los parámetros personalizados
        Retorna un diccionario con toda la configuración necesaria para el procesamiento
        """
        # Configuración base del modelo relacionado
        config_base = {}
        if self.configuracion_utilizada:
            config_base = {
                'modelo_whisper': self.configuracion_utilizada.modelo_whisper,
                'temperatura': self.configuracion_utilizada.temperatura,
                'idioma_principal': self.configuracion_utilizada.idioma_principal,
                'usar_vad': self.configuracion_utilizada.usar_vad,
                'vad_filtro': self.configuracion_utilizada.vad_filtro,
                'min_hablantes': self.configuracion_utilizada.min_hablantes,
                'max_hablantes': self.configuracion_utilizada.max_hablantes,
                'umbral_clustering': self.configuracion_utilizada.umbral_clustering,
                'chunk_duracion': self.configuracion_utilizada.chunk_duracion,
                'overlap_duracion': getattr(self.configuracion_utilizada, 'overlap_duracion', 5),
                'usar_gpu': self.configuracion_utilizada.usar_gpu,
                'filtro_ruido': self.configuracion_utilizada.filtro_ruido,
                'normalizar_audio': self.configuracion_utilizada.normalizar_audio,
                'usar_enhanced_diarization': getattr(self.configuracion_utilizada, 'usar_enhanced_diarization', False),
            }
        
        # Aplicar parámetros personalizados PRIMERO
        if self.parametros_personalizados:
            config_base.update(self.parametros_personalizados)
        
        # ✅ AGREGAR PARTICIPANTES DESDE EL PROCESAMIENTO DE AUDIO (DESPUÉS de parámetros personalizados)
        # Si hay participantes configurados, incluirlos directamente en la configuración
        # Esto sobrescribe cualquier valor vacío que pudiera haber en parámetros personalizados
        if (hasattr(self, 'procesamiento_audio') and 
            self.procesamiento_audio and 
            hasattr(self.procesamiento_audio, 'participantes_detallados') and 
            self.procesamiento_audio.participantes_detallados):
            
            participantes = self.procesamiento_audio.participantes_detallados
            config_base['participantes_esperados'] = participantes
            config_base['hablantes_predefinidos'] = participantes
            
            # También agregar metadatos útiles
            config_base['audio_id'] = self.procesamiento_audio.id
            config_base['usuario_id'] = self.usuario_creacion.id if self.usuario_creacion else None
            config_base['audio_titulo'] = getattr(self.procesamiento_audio, 'titulo', f'Audio {self.procesamiento_audio.id}')
        else:
            # Si no hay participantes, dejar arrays vacíos para que el sistema use detección automática
            # Solo si no están ya definidos en parámetros personalizados
            if 'participantes_esperados' not in config_base:
                config_base['participantes_esperados'] = []
            if 'hablantes_predefinidos' not in config_base:
                config_base['hablantes_predefinidos'] = []
        
        return config_base


class HistorialEdicion(models.Model):
    """Historial de ediciones manuales de transcripciones"""
    
    transcripcion = models.ForeignKey(
        Transcripcion,
        on_delete=models.CASCADE,
        related_name='historial_ediciones'
    )
    
    # Información de la edición
    version = models.IntegerField()
    tipo_edicion = models.CharField(
        max_length=50,
        choices=[
            ('texto', 'Edición de Texto'),
            ('hablante', 'Cambio de Hablante'),
            ('tiempo', 'Ajuste de Tiempo'),
            ('segmento', 'Modificación de Segmento'),
            ('fusion', 'Fusión de Segmentos'),
            ('division', 'División de Segmento'),
            ('eliminacion', 'Eliminación de Segmento'),
            ('adicion', 'Adición de Segmento'),
        ]
    )
    
    # Datos de la edición
    segmento_id = models.CharField(max_length=50, blank=True)
    valor_anterior = models.JSONField(default=dict)
    valor_nuevo = models.JSONField(default=dict)
    comentario = models.TextField(blank=True)
    
    # Metadatos
    fecha_edicion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Historial de Edición"
        verbose_name_plural = "Historial de Ediciones"
        ordering = ['-fecha_edicion']

    def __str__(self):
        return f"{self.get_tipo_edicion_display()} - v{self.version} por {self.usuario.username}"


class ConfiguracionHablante(models.Model):
    """Configuración y metadatos de hablantes para una transcripción"""
    
    transcripcion = models.ForeignKey(
        Transcripcion,
        on_delete=models.CASCADE,
        related_name='configuracion_hablantes'
    )
    
    # Identificación del hablante
    speaker_id = models.CharField(max_length=50)  # ID detectado por pyannote
    nombre_real = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100, blank=True)
    organizacion = models.CharField(max_length=100, blank=True)
    
    # Configuración de visualización
    color_chat = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Color hexadecimal para el chat"
    )
    avatar_url = models.URLField(blank=True)
    
    # Estadísticas
    tiempo_total_hablando = models.FloatField(default=0.0)
    numero_intervenciones = models.IntegerField(default=0)
    palabras_promedio_por_intervencion = models.FloatField(default=0.0)
    
    # Metadatos
    confirmado_por_usuario = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Hablante"
        verbose_name_plural = "Configuraciones de Hablantes"
        unique_together = [['transcripcion', 'speaker_id']]

    def __str__(self):
        return f"{self.nombre_real} ({self.speaker_id}) - {self.transcripcion}"
