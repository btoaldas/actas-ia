from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os


class TipoReunion(models.Model):
    """Tipos de reunión parametrizables"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Reunión"
        verbose_name_plural = "Tipos de Reunión"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


def audio_upload_path(instance, filename):
    """Generar ruta de subida del audio con jerarquía de fechas"""
    fecha = timezone.now()
    year = fecha.strftime('%Y')
    month = fecha.strftime('%m')
    day = fecha.strftime('%d')
    
    # Limpiar el nombre del archivo
    name, ext = os.path.splitext(filename)
    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    
    return f'audio/{year}/{month}/{day}/{safe_name}_{instance.id or "temp"}{ext}'


class ProcesamientoAudio(models.Model):
    """Tabla principal para el procesamiento de audio"""
    
    # Estados posibles
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('transcribiendo', 'Transcribiendo'),
        ('diarizando', 'Diarizando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
        ('cancelado', 'Cancelado'),
    ]
    
    # Información básica
    titulo = models.CharField(max_length=200, help_text="Título descriptivo del proceso")
    tipo_reunion = models.ForeignKey(TipoReunion, on_delete=models.PROTECT)
    descripcion = models.TextField(blank=True, help_text="Descripción adicional del proceso")
    
    # Información de la reunión/proceso  
    participantes = models.TextField(blank=True, help_text="Lista de participantes (texto libre para compatibilidad)")
    participantes_detallados = models.JSONField(
        default=list, 
        blank=True, 
        help_text="Lista detallada de participantes con nombre, apellido, cargo, institución y orden"
    )
    ubicacion = models.CharField(max_length=200, blank=True, help_text="Ubicación donde se realizó la reunión")
    
    # Campos nuevos según la guía
    etiquetas = models.CharField(max_length=200, blank=True, help_text="Etiquetas separadas por comas")
    confidencial = models.BooleanField(default=False, help_text="Proceso confidencial")
    version_pipeline = models.CharField(max_length=20, default="v2.0", help_text="Versión del pipeline de procesamiento")
    
    # Audio
    archivo_audio = models.FileField(
        upload_to=audio_upload_path, 
        help_text="Archivo de audio original"
    )
    archivo_mejorado = models.FileField(
        upload_to='audio/mejorado/', 
        blank=True, 
        null=True, 
        help_text="Archivo de audio procesado y mejorado"
    )
    
    # Metadatos del audio original
    duracion = models.PositiveIntegerField(blank=True, null=True, help_text="Duración en segundos")
    duracion_seg = models.FloatField(blank=True, null=True, help_text="Duración exacta en segundos (decimal)")
    sample_rate = models.IntegerField(blank=True, null=True, help_text="Frecuencia de muestreo")
    formato = models.CharField(max_length=10, blank=True)
    tamano_mb = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    canales = models.IntegerField(blank=True, null=True, help_text="Número de canales de audio")
    bit_rate = models.IntegerField(blank=True, null=True, help_text="Bit rate del audio")
    codec = models.CharField(max_length=50, blank=True, help_text="Codec utilizado")
    metadatos_originales = models.JSONField(default=dict, blank=True, help_text="Metadatos completos del archivo original")
    metadatos_procesamiento = models.JSONField(default=dict, blank=True, help_text="Metadatos del pipeline de procesamiento")
    
    # Estado y control
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    progreso = models.PositiveSmallIntegerField(default=0, help_text="Progreso en porcentaje")
    mensaje_estado = models.TextField(blank=True, help_text="Mensaje detallado del estado actual")
    
    # Fechas de procesamiento
    fecha_procesamiento = models.DateTimeField(blank=True, null=True)
    fecha_completado = models.DateTimeField(blank=True, null=True)
    
    # Configuración de procesamiento
    configuracion = models.JSONField(default=dict, blank=True)
    
    # Resultados
    resultado = models.JSONField(blank=True, null=True)
    
    # Auditoría
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='procesamientos_audio')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Procesamiento de Audio"
        verbose_name_plural = "Procesamientos de Audio"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.titulo} - {self.get_estado_display()}"
    
    @property
    def duracion_formateada(self):
        """Devuelve la duración en formato HH:MM:SS"""
        if self.duracion:
            horas = self.duracion // 3600
            minutos = (self.duracion % 3600) // 60
            segundos = self.duracion % 60
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        return "00:00:00"
    
    def get_progreso_display(self):
        return f"{self.progreso}%"
    
    @property
    def esta_procesando(self):
        """Verifica si el audio está en proceso"""
        return self.estado in ['procesando', 'transcribiendo', 'diarizando']
    
    @property
    def tiene_audio_procesado(self):
        """Verifica si tiene audio procesado"""
        return bool(self.archivo_mejorado)


class LogProcesamiento(models.Model):
    """Log detallado del procesamiento"""
    procesamiento = models.ForeignKey(ProcesamientoAudio, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField(auto_now_add=True)
    nivel = models.CharField(max_length=10, choices=[
        ('info', 'Info'),
        ('warning', 'Warning'), 
        ('error', 'Error'),
        ('debug', 'Debug')
    ])
    mensaje = models.TextField()
    detalles_json = models.JSONField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Log de Procesamiento"
        verbose_name_plural = "Logs de Procesamiento"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.procesamiento.titulo} - {self.nivel} - {self.timestamp}"
