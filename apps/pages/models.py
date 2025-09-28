from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid
import os

def acta_upload_path(instance, filename):
    """Genera la ruta de almacenamiento dinámicamente basada en la fecha de creación"""
    from datetime import datetime
    fecha = instance.fecha_sesion or datetime.now()
    return f'repositorio/{fecha.year}/{fecha.month:02d}/{fecha.day:02d}/{fecha.hour:02d}/{filename}'

def acta_image_upload_path(instance, filename):
    """Ruta para subir imágenes de vista previa de actas"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('actas', 'imagenes', filename)

# Create your models here.

class Product(models.Model):
    id    = models.AutoField(primary_key=True)
    name  = models.CharField(max_length = 100) 
    info  = models.CharField(max_length = 100, default = '')
    price = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

class TipoSesion(models.Model):
    """Tipos de sesiones municipales"""
    TIPOS_CHOICES = [
        ('ordinaria', 'Sesión Ordinaria'),
        ('extraordinaria', 'Sesión Extraordinaria'),
        ('solemne', 'Sesión Solemne'),
        ('publica', 'Audiencia Pública'),
        ('comision', 'Comisión'),
    ]
    
    nombre = models.CharField(max_length=50, choices=TIPOS_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#6c757d", help_text="Color en formato hexadecimal")
    icono = models.CharField(max_length=50, default="fas fa-file-alt")
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Tipo de Sesión"
        verbose_name_plural = "Tipos de Sesiones"
        ordering = ['nombre']
    
    def __str__(self):
        return dict(self.TIPOS_CHOICES)[self.nombre]

class EstadoActa(models.Model):
    """Estados del proceso de las actas"""
    ESTADOS_CHOICES = [
        ('borrador', 'Borrador'),
        ('transcripcion', 'En Transcripción'),
        ('revision', 'En Revisión'),
        ('aprobada', 'Aprobada'),
        ('publicada', 'Publicada'),
        ('archivada', 'Archivada'),
    ]
    
    nombre = models.CharField(max_length=20, choices=ESTADOS_CHOICES, unique=True)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#6c757d")
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Estado de Acta"
        verbose_name_plural = "Estados de Actas"
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return dict(self.ESTADOS_CHOICES)[self.nombre]

class ActaMunicipal(models.Model):
    """Modelo principal para las actas municipales"""
    ACCESO_CHOICES = [
        ('publico', 'Acceso Público'),
        ('restringido', 'Acceso Restringido'),
        ('confidencial', 'Confidencial'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    # Información básica
    titulo = models.CharField(max_length=200, help_text="Título descriptivo del acta")
    numero_acta = models.CharField(max_length=50, unique=True, help_text="Número único del acta")
    numero_sesion = models.CharField(max_length=50, help_text="Número de la sesión")
    tipo_sesion = models.ForeignKey(TipoSesion, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoActa, on_delete=models.PROTECT)
    
    # Fechas y tiempos
    fecha_sesion = models.DateTimeField(help_text="Fecha y hora de la sesión")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    
    # Contenido
    resumen = models.TextField(help_text="Resumen ejecutivo del acta")
    contenido = models.TextField(blank=True, help_text="Contenido completo del acta")
    orden_del_dia = models.TextField(blank=True, help_text="Orden del día de la sesión")
    acuerdos = models.TextField(blank=True, help_text="Acuerdos tomados en la sesión")
    
    # Archivos
    archivo_pdf = models.FileField(
        upload_to=acta_upload_path, 
        null=True, blank=True,
        help_text="Archivo PDF del acta"
    )
    imagen_preview = models.ImageField(
        upload_to=acta_image_upload_path, 
        null=True, blank=True,
        help_text="Imagen de vista previa del acta"
    )
    
    # Control de acceso
    acceso = models.CharField(
        max_length=15, 
        choices=ACCESO_CHOICES, 
        default='publico',
        help_text="Nivel de acceso al documento"
    )
    prioridad = models.CharField(
        max_length=10, 
        choices=PRIORIDAD_CHOICES, 
        default='normal'
    )
    
    # Participantes
    secretario = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='actas_como_secretario',
        help_text="Secretario responsable del acta"
    )
    presidente = models.CharField(max_length=100, help_text="Presidente de la sesión")
    asistentes = models.TextField(blank=True, help_text="Lista de asistentes")
    ausentes = models.TextField(blank=True, help_text="Lista de ausentes")
    
    # Metadatos de IA
    transcripcion_ia = models.BooleanField(default=False, help_text="¿Fue transcrita por IA?")
    precision_ia = models.DecimalField(
        max_digits=5, decimal_places=2, 
        null=True, blank=True,
        help_text="Precisión de la transcripción IA (%)"
    )
    tiempo_procesamiento = models.DurationField(null=True, blank=True)
    
    # Campos adicionales
    palabras_clave = models.CharField(max_length=500, blank=True, help_text="Palabras clave separadas por comas")
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Acta Municipal"
        verbose_name_plural = "Actas Municipales"
        ordering = ['-fecha_sesion', '-fecha_creacion']
        indexes = [
            models.Index(fields=['numero_acta']),
            models.Index(fields=['fecha_sesion']),
            models.Index(fields=['estado']),
            models.Index(fields=['acceso']),
            models.Index(fields=['tipo_sesion']),
        ]
    
    def __str__(self):
        return f"{self.numero_acta} - {self.titulo}"
    
    def get_absolute_url(self):
        return reverse('acta_detail', kwargs={'pk': self.pk})
    
    @property
    def es_publico(self):
        return self.acceso == 'publico'
    
    @property
    def color_estado(self):
        return self.estado.color if self.estado else '#6c757d'
    
    @property
    def icono_acceso(self):
        icons = {
            'publico': 'fas fa-globe text-success',
            'restringido': 'fas fa-lock text-warning', 
            'confidencial': 'fas fa-shield-alt text-danger'
        }
        return icons.get(self.acceso, 'fas fa-file')
    
    @property
    def estado_publicacion(self):
        return self.estado.nombre in ['publicada', 'archivada']
    
    def puede_ver_usuario(self, user):
        """Determina si un usuario puede ver esta acta"""
        if self.acceso == 'publico':
            return True
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        
        # Aquí puedes agregar lógica adicional de permisos
        # basada en el sistema de permisos que ya tienes
        return False

    def get_palabras_clave_list(self):
        """Devuelve las palabras clave como lista"""
        if self.palabras_clave:
            return [palabra.strip() for palabra in self.palabras_clave.split(',') if palabra.strip()]
        return []

class VisualizacionActa(models.Model):
    """Registro de visualizaciones de actas"""
    acta = models.ForeignKey(ActaMunicipal, on_delete=models.CASCADE, related_name='visualizaciones')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    fecha_visualizacion = models.DateTimeField(auto_now_add=True)
    tiempo_lectura = models.DurationField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Visualización de Acta"
        verbose_name_plural = "Visualizaciones de Actas"
        ordering = ['-fecha_visualizacion']

class DescargaActa(models.Model):
    """Registro de descargas de documentos de actas"""
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('txt', 'Texto Plano'),
        ('word', 'Word Document'),
    ]
    
    acta = models.ForeignKey(ActaMunicipal, on_delete=models.CASCADE, related_name='descargas')
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    formato = models.CharField(max_length=10, choices=FORMATO_CHOICES, default='pdf')
    fecha_descarga = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Descarga de Acta"
        verbose_name_plural = "Descargas de Actas"
        ordering = ['-fecha_descarga']
        
    def __str__(self):
        return f"{self.acta} - {self.get_formato_display()} - {self.fecha_descarga}"

# ========================================================================
# MODELOS DE TRANSPARENCIA
# ========================================================================

class IndicadorTransparencia(models.Model):
    """Indicadores de transparencia municipal"""
    CATEGORIA_CHOICES = [
        ('participacion', 'Participación Ciudadana'),
        ('tiempo_respuesta', 'Tiempo de Respuesta'),
        ('publicacion', 'Publicación de Información'),
        ('cumplimiento', 'Cumplimiento Legal'),
        ('accesibilidad', 'Accesibilidad'),
        ('calidad', 'Calidad de la Información'),
    ]
    
    TIPO_CHOICES = [
        ('porcentaje', 'Porcentaje (%)'),
        ('numero', 'Número'),
        ('tiempo', 'Tiempo (días/horas)'),
        ('puntuacion', 'Puntuación (1-10)'),
    ]
    
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    icono = models.CharField(max_length=50, default='fas fa-chart-line')
    color = models.CharField(max_length=7, default='#007bff')
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Indicador de Transparencia"
        verbose_name_plural = "Indicadores de Transparencia"
        ordering = ['categoria', 'orden', 'nombre']
    
    def __str__(self):
        return self.nombre

class MetricaTransparencia(models.Model):
    """Valores históricos de métricas de transparencia"""
    indicador = models.ForeignKey(IndicadorTransparencia, on_delete=models.CASCADE, related_name='metricas')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    mes = models.PositiveIntegerField()  # 1-12
    año = models.PositiveIntegerField()
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Métrica de Transparencia"
        verbose_name_plural = "Métricas de Transparencia"
        ordering = ['-año', '-mes', '-fecha']
        unique_together = ['indicador', 'fecha']
    
    def __str__(self):
        return f"{self.indicador.nombre} - {self.fecha}: {self.valor}"

class EstadisticaMunicipal(models.Model):
    """Estadísticas generales del municipio"""
    CATEGORIA_CHOICES = [
        ('poblacion', 'Población'),
        ('economia', 'Economía'),
        ('servicios', 'Servicios Públicos'),
        ('infraestructura', 'Infraestructura'),
        ('medio_ambiente', 'Medio Ambiente'),
        ('social', 'Desarrollo Social'),
        ('gobierno', 'Gestión Gubernamental'),
    ]
    
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    valor = models.DecimalField(max_digits=15, decimal_places=2)
    unidad = models.CharField(max_length=50, help_text="Ej: habitantes, pesos, metros, %")
    fecha = models.DateField()
    fuente = models.CharField(max_length=200, help_text="Fuente de la información")
    descripcion = models.TextField(blank=True)
    icono = models.CharField(max_length=50, default='fas fa-chart-bar')
    color = models.CharField(max_length=7, default='#28a745')
    
    class Meta:
        verbose_name = "Estadística Municipal"
        verbose_name_plural = "Estadísticas Municipales"
        ordering = ['-fecha', 'categoria', 'nombre']
    
    def __str__(self):
        return f"{self.nombre}: {self.valor} {self.unidad}"

class ProyectoMunicipal(models.Model):
    """Proyectos y obras municipales"""
    ESTADO_CHOICES = [
        ('planificacion', 'En Planificación'),
        ('aprobado', 'Aprobado'),
        ('en_ejecucion', 'En Ejecución'),
        ('finalizado', 'Finalizado'),
        ('suspendido', 'Suspendido'),
        ('cancelado', 'Cancelado'),
    ]
    
    CATEGORIA_CHOICES = [
        ('infraestructura', 'Infraestructura'),
        ('servicios', 'Servicios Públicos'),
        ('social', 'Desarrollo Social'),
        ('cultura', 'Cultura y Recreación'),
        ('medio_ambiente', 'Medio Ambiente'),
        ('seguridad', 'Seguridad'),
        ('economia', 'Desarrollo Económico'),
    ]
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES)
    
    # Presupuesto
    presupuesto_total = models.DecimalField(max_digits=12, decimal_places=2)
    presupuesto_ejecutado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Fechas
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField()
    fecha_fin_real = models.DateField(null=True, blank=True)
    
    # Progreso
    porcentaje_avance = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Responsables
    responsable = models.CharField(max_length=100)
    contratista = models.CharField(max_length=100, blank=True)
    
    # Ubicación
    ubicacion = models.CharField(max_length=200)
    
    # Beneficiarios
    beneficiarios_estimados = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Proyecto Municipal"
        verbose_name_plural = "Proyectos Municipales"
        ordering = ['-fecha_inicio', 'nombre']
    
    def __str__(self):
        return self.nombre
    
    @property
    def porcentaje_presupuesto_ejecutado(self):
        if self.presupuesto_total > 0:
            return round((self.presupuesto_ejecutado / self.presupuesto_total) * 100, 2)
        return 0
    
    @property
    def color_estado(self):
        colores = {
            'planificacion': '#6c757d',
            'aprobado': '#007bff',
            'en_ejecucion': '#ffc107',
            'finalizado': '#28a745',
            'suspendido': '#fd7e14',
            'cancelado': '#dc3545',
        }
        return colores.get(self.estado, '#6c757d')

# ========================================================================
# MODELOS DE EVENTOS MUNICIPALES
# ========================================================================

def evento_documento_upload_path(instance, filename):
    """Genera ruta de subida para documentos de eventos con jerarquía de fechas"""
    from datetime import datetime
    import os
    
    # Obtener fecha del evento o fecha actual
    if hasattr(instance, 'evento') and instance.evento:
        fecha = instance.evento.fecha_inicio
    elif hasattr(instance, 'fecha_inicio'):
        fecha = instance.fecha_inicio
    else:
        fecha = datetime.now()
    
    # Crear estructura: media/eventos/YYYY/MM/tipo_evento/
    año = fecha.year
    mes = f"{fecha.month:02d}"
    
    # Obtener tipo de evento si está disponible
    if hasattr(instance, 'evento') and instance.evento:
        tipo_evento = instance.evento.tipo
    elif hasattr(instance, 'tipo'):
        tipo_evento = instance.tipo
    else:
        tipo_evento = 'general'
    
    # Limpiar nombre del archivo
    nombre, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_limpio = f"{timestamp}_{nombre[:50]}{ext}"
    
    return f'eventos/{año}/{mes}/{tipo_evento}/{filename_limpio}'

class EventoMunicipal(models.Model):
    """Eventos y reuniones municipales"""
    TIPO_CHOICES = [
        ('sesion_ordinaria', 'Sesión Ordinaria'),
        ('sesion_extraordinaria', 'Sesión Extraordinaria'),
        ('audiencia_publica', 'Audiencia Pública'),
        ('reunion_trabajo', 'Reunión de Trabajo'),
        ('capacitacion', 'Capacitación'),
        ('evento_publico', 'Evento Público'),
        ('otro', 'Otro'),
    ]
    
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('confirmado', 'Confirmado'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
        ('reprogramado', 'Reprogramado'),
    ]
    
    VISIBILIDAD_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
        ('restringido', 'Restringido'),
    ]
    
    # Información básica
    titulo = models.CharField(max_length=200, help_text="Título del evento")
    descripcion = models.TextField(help_text="Descripción detallada del evento")
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES, default='otro')
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='programado')
    visibilidad = models.CharField(max_length=15, choices=VISIBILIDAD_CHOICES, default='publico')
    
    # Fechas y ubicación
    fecha_inicio = models.DateTimeField(help_text="Fecha y hora de inicio")
    fecha_fin = models.DateTimeField(help_text="Fecha y hora de fin")
    ubicacion = models.CharField(max_length=200, help_text="Lugar del evento")
    direccion = models.TextField(blank=True, help_text="Dirección completa")
    
    # Organización
    organizador = models.ForeignKey(
        User, 
        on_delete=models.PROTECT, 
        related_name='eventos_organizados',
        help_text="Usuario organizador del evento"
    )
    responsable = models.CharField(max_length=100, help_text="Responsable del evento")
    
    # Participantes
    asistentes_invitados = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='eventos_invitado',
        help_text="Usuarios registrados invitados al evento"
    )
    invitados_externos = models.TextField(
        blank=True,
        help_text="Emails de invitados externos separados por comas"
    )
    asistentes_confirmados = models.ManyToManyField(
        User, 
        blank=True, 
        related_name='eventos_confirmado',
        help_text="Usuarios que confirmaron asistencia"
    )
    capacidad_maxima = models.PositiveIntegerField(default=0, help_text="Capacidad máxima del evento (0 = sin límite)")
    
    # Contenido adicional
    agenda = models.TextField(blank=True, help_text="Agenda u orden del día")
    requisitos = models.TextField(blank=True, help_text="Requisitos para asistir")
    observaciones = models.TextField(blank=True, help_text="Observaciones adicionales")
    
    # Archivos
    imagen_evento = models.ImageField(
        upload_to=evento_documento_upload_path, 
        null=True, blank=True,
        help_text="Imagen representativa del evento"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    # Notificaciones
    enviar_recordatorio = models.BooleanField(default=True, help_text="Enviar recordatorio por email")
    recordatorio_enviado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Evento Municipal"
        verbose_name_plural = "Eventos Municipales"
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['fecha_inicio']),
            models.Index(fields=['tipo']),
            models.Index(fields=['estado']),
            models.Index(fields=['visibilidad']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def es_publico(self):
        return self.visibilidad == 'publico'
    
    @property
    def color_tipo(self):
        colores = {
            'sesion_ordinaria': '#007bff',
            'sesion_extraordinaria': '#ffc107',
            'audiencia_publica': '#28a745',
            'reunion_trabajo': '#17a2b8',
            'capacitacion': '#6f42c1',
            'evento_publico': '#20c997',
            'otro': '#6c757d',
        }
        return colores.get(self.tipo, '#6c757d')
    
    @property
    def color_estado(self):
        colores = {
            'programado': '#6c757d',
            'confirmado': '#007bff',
            'en_curso': '#ffc107',
            'finalizado': '#28a745',
            'cancelado': '#dc3545',
            'reprogramado': '#fd7e14',
        }
        return colores.get(self.estado, '#6c757d')
    
    @property
    def icono_tipo(self):
        iconos = {
            'sesion_ordinaria': 'fas fa-calendar-check',
            'sesion_extraordinaria': 'fas fa-exclamation-triangle',
            'audiencia_publica': 'fas fa-users',
            'reunion_trabajo': 'fas fa-handshake',
            'capacitacion': 'fas fa-graduation-cap',
            'evento_publico': 'fas fa-calendar-star',
            'otro': 'fas fa-calendar',
        }
        return iconos.get(self.tipo, 'fas fa-calendar')
    
    def puede_ver_usuario(self, user):
        """Determina si un usuario puede ver este evento"""
        if self.visibilidad == 'publico':
            return True
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if self.visibilidad == 'privado':
            return user in self.asistentes_invitados.all() or user == self.organizador
        return False
    
    def puede_editar_usuario(self, user):
        """Determina si un usuario puede editar este evento"""
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return user == self.organizador
    
    @property
    def total_asistentes_confirmados(self):
        return self.asistentes_confirmados.count()
    
    @property
    def espacios_disponibles(self):
        if self.capacidad_maxima == 0:
            return "Sin límite"
        return max(0, self.capacidad_maxima - self.total_asistentes_confirmados)

class DocumentoEvento(models.Model):
    """Documentos asociados a eventos"""
    TIPO_DOCUMENTO_CHOICES = [
        ('agenda', 'Agenda'),
        ('acta', 'Acta'),
        ('presentacion', 'Presentación'),
        ('anexo', 'Anexo'),
        ('convocatoria', 'Convocatoria'),
        ('otro', 'Otro'),
    ]
    
    evento = models.ForeignKey(EventoMunicipal, on_delete=models.CASCADE, related_name='documentos')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, default='otro')
    archivo = models.FileField(upload_to=evento_documento_upload_path)
    es_publico = models.BooleanField(default=True, help_text="¿El documento es público?")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(User, on_delete=models.PROTECT)
    orden = models.PositiveIntegerField(default=0, help_text="Orden de visualización")
    
    class Meta:
        verbose_name = "Documento de Evento"
        verbose_name_plural = "Documentos de Eventos"
        ordering = ['orden', '-fecha_subida']
    
    def __str__(self):
        return f"{self.nombre} - {self.evento.titulo}"
    
    @property
    def tamaño_archivo(self):
        """Retorna el tamaño del archivo en formato legible"""
        if self.archivo and hasattr(self.archivo, 'size'):
            size = self.archivo.size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "N/A"
    
    @property
    def extension_archivo(self):
        """Retorna la extensión del archivo"""
        import os
        if self.archivo:
            return os.path.splitext(self.archivo.name)[1].lower()
        return ""
    
    @property
    def icono_tipo(self):
        """Retorna el icono apropiado según el tipo de archivo"""
        ext = self.extension_archivo
        if ext in ['.pdf']:
            return 'fas fa-file-pdf text-danger'
        elif ext in ['.doc', '.docx']:
            return 'fas fa-file-word text-primary'
        elif ext in ['.xls', '.xlsx']:
            return 'fas fa-file-excel text-success'
        elif ext in ['.ppt', '.pptx']:
            return 'fas fa-file-powerpoint text-warning'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'fas fa-file-image text-info'
        else:
            return 'fas fa-file text-secondary'

class AsistenciaEvento(models.Model):
    """Registro de asistencia a eventos"""
    TIPO_CHOICES = [
        ('confirmado', 'Confirmado'),
        ('presente', 'Presente'),
        ('ausente', 'Ausente'),
        ('tardanza', 'Tardanza'),
    ]
    
    evento = models.ForeignKey(EventoMunicipal, on_delete=models.CASCADE, related_name='asistencias')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='confirmado')
    fecha_confirmacion = models.DateTimeField(auto_now_add=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Asistencia a Evento"
        verbose_name_plural = "Asistencias a Eventos"
        unique_together = ['evento', 'usuario']
        ordering = ['-fecha_confirmacion']
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.evento.titulo} ({self.get_tipo_display()})"


class InvitacionExterna(models.Model):
    """Invitaciones por email a personas no registradas"""
    ESTADO_CHOICES = [
        ('enviada', 'Enviada'),
        ('vista', 'Vista'),
        ('confirmada', 'Confirmada'),
        ('rechazada', 'Rechazada'),
    ]
    
    evento = models.ForeignKey(EventoMunicipal, on_delete=models.CASCADE, related_name='invitaciones_externas')
    email = models.EmailField()
    nombre = models.CharField(max_length=100, blank=True)
    mensaje_personalizado = models.TextField(blank=True)
    token = models.CharField(max_length=100, unique=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='enviada')
    fecha_envio = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    enviado_por = models.ForeignKey(User, on_delete=models.PROTECT)
    
    class Meta:
        verbose_name = "Invitación Externa"
        verbose_name_plural = "Invitaciones Externas"
        unique_together = ['evento', 'email']
        ordering = ['-fecha_envio']
    
    def __str__(self):
        return f"{self.email} - {self.evento.titulo}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            import uuid
            self.token = str(uuid.uuid4())
        super().save(*args, **kwargs)