"""
Modelos para la gestión completa de actas municipales
Incluye depuración, revisión, aprobación y publicación
"""
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import uuid


class EstadoGestionActa(models.Model):
    """Estados del proceso de gestión de actas"""
    ESTADOS_CHOICES = [
        ('generada', 'Acta Generada'),
        ('en_edicion', 'En Edición/Depuración'),
        ('enviada_revision', 'Enviada para Revisión'),
        ('en_revision', 'En Proceso de Revisión'),
        ('aprobada', 'Aprobada por Revisores'),
        ('rechazada', 'Rechazada'),
        ('lista_publicacion', 'Lista para Publicación'),
        ('publicada', 'Publicada en Portal'),
        ('archivada', 'Archivada')
    ]
    
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Color hexadecimal para UI")
    orden = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    
    # Configuración de comportamiento
    permite_edicion = models.BooleanField(default=True)
    requiere_revision = models.BooleanField(default=False)
    visible_portal = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Estado de Gestión de Acta"
        verbose_name_plural = "Estados de Gestión de Actas"
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre


class GestionActa(models.Model):
    """Modelo principal para gestión del acta generada"""
    
    # Relación con el acta generada original
    acta_generada = models.OneToOneField(
        'generador_actas.ActaGenerada',
        on_delete=models.CASCADE,
        related_name='gestion',
        null=True, blank=True,
        help_text="Acta generada original de la cual deriva esta gestión"
    )
    
    # Estados y workflow
    estado = models.ForeignKey(
        EstadoGestionActa,
        on_delete=models.PROTECT,
        related_name='actas_gestion'
    )
    
    # Contenido editable
    contenido_editado = models.TextField(
        help_text="Contenido del acta editado por el usuario"
    )
    contenido_original_backup = models.TextField(
        blank=True,
        help_text="Backup del contenido original antes de editar"
    )
    
    # Información de gestión
    usuario_editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='actas_editadas',
        help_text="Usuario que editó el acta"
    )
    
    # Control de versiones
    version = models.IntegerField(default=1)
    cambios_realizados = models.JSONField(
        default=dict,
        help_text="Log de cambios realizados al acta"
    )
    
    # Fechas importantes
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_edicion = models.DateTimeField(auto_now=True)
    fecha_enviada_revision = models.DateTimeField(null=True, blank=True)
    fecha_aprobacion_final = models.DateTimeField(null=True, blank=True)
    fecha_publicacion = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    observaciones = models.TextField(
        blank=True,
        help_text="Observaciones generales sobre el proceso"
    )
    
    # Control de bloqueo de edición
    bloqueada_edicion = models.BooleanField(
        default=False,
        help_text="Si está bloqueada la edición (enviada a revisión)"
    )
    
    # Relación con el portal ciudadano
    acta_portal = models.OneToOneField(
        'pages.ActaMunicipal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Referencia al acta publicada en el portal ciudadano"
    )
    
    class Meta:
        verbose_name = "Gestión de Acta"
        verbose_name_plural = "Gestión de Actas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        if self.acta_generada:
            return f"Gestión: {self.acta_generada.titulo}"
        return f"Gestión de Acta #{self.pk}"
    
    def get_absolute_url(self):
        return reverse('gestion_actas:editar_acta', kwargs={'pk': self.pk})
    
    def puede_editarse(self):
        """Verifica si el acta puede editarse"""
        return not self.bloqueada_edicion and self.estado.permite_edicion
    
    @property
    def titulo(self):
        """Título del acta (desde acta_generada si existe)"""
        if self.acta_generada:
            return self.acta_generada.titulo
        return f"Acta en Gestión #{self.pk}"
    
    @property
    def numero_acta(self):
        """Número del acta (desde acta_generada si existe)"""
        if self.acta_generada:
            return self.acta_generada.numero_acta
        return f"GESTION-{self.pk}"
    
    @property
    def fecha_sesion(self):
        """Fecha de la sesión (desde acta_generada si existe)"""
        if self.acta_generada:
            return self.acta_generada.fecha_sesion
        return self.fecha_creacion
    
    def get_url_exportar_pdf(self):
        return reverse('gestion_actas:exportar_pdf', kwargs={'pk': self.pk})
    
    def get_url_exportar_word(self):
        return reverse('gestion_actas:exportar_word', kwargs={'pk': self.pk})
    
    def get_url_exportar_txt(self):
        return reverse('gestion_actas:exportar_txt', kwargs={'pk': self.pk})


class ProcesoRevision(models.Model):
    """Proceso de revisión de un acta"""
    
    gestion_acta = models.OneToOneField(
        GestionActa,
        on_delete=models.CASCADE,
        related_name='proceso_revision'
    )
    
    # Usuario que inició el proceso de revisión
    iniciado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='procesos_revision_iniciados'
    )
    
    # Fecha de inicio y configuración
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField(
        null=True, blank=True,
        help_text="Fecha límite para completar la revisión"
    )
    
    # Estado del proceso
    completado = models.BooleanField(default=False)
    aprobado = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    
    # Configuración de revisión
    revision_paralela = models.BooleanField(
        default=True,
        help_text="Si true: revisión paralela; si false: secuencial"
    )
    requiere_unanimidad = models.BooleanField(
        default=False,
        help_text="Si requiere aprobación unánime o por mayoría"
    )
    
    # Observaciones generales
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Proceso de Revisión"
        verbose_name_plural = "Procesos de Revisión"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Revisión de Acta #{self.gestion_acta.pk}"
    
    def get_estado_revision(self):
        """Obtiene el estado actual de la revisión"""
        revisiones = self.revisiones.all()
        total_revisores = revisiones.count()
        
        if total_revisores == 0:
            return 'sin_revisores'
        
        aprobaciones = revisiones.filter(aprobado=True).count()
        rechazos = revisiones.filter(aprobado=False, revisado=True).count()
        pendientes = revisiones.filter(revisado=False).count()
        
        # Si ya se completó el proceso
        if self.completado:
            return 'aprobado' if self.aprobado else 'rechazado'
        
        # Verificar condiciones de finalización
        if self.requiere_unanimidad:
            if rechazos > 0:
                return 'rechazado'
            elif aprobaciones == total_revisores:
                return 'aprobado'
        else:  # Por mayoría
            mayoria = (total_revisores // 2) + 1
            if aprobaciones >= mayoria:
                return 'aprobado'
            elif rechazos >= mayoria:
                return 'rechazado'
        
        return 'en_proceso'
    
    def puede_completarse(self):
        """Verifica si el proceso puede completarse automáticamente"""
        estado = self.get_estado_revision()
        return estado in ['aprobado', 'rechazado']
    
    def verificar_completado(self):
        """Verifica si el proceso puede completarse y lo completa automáticamente"""
        if self.puede_completarse():
            return self.completar_proceso()
        return False
    
    def completar_proceso(self):
        """Completa el proceso de revisión automáticamente"""
        if not self.puede_completarse():
            return False
        
        estado = self.get_estado_revision()
        self.completado = True
        self.aprobado = (estado == 'aprobado')
        self.fecha_completado = timezone.now()
        self.save()
        
        # Actualizar estado de la gestión del acta
        if self.aprobado:
            estado_obj = EstadoGestionActa.objects.get(codigo='lista_publicacion')
            self.gestion_acta.estado = estado_obj
            self.gestion_acta.fecha_aprobacion_final = timezone.now()
        else:
            estado_obj = EstadoGestionActa.objects.get(codigo='rechazada')
            self.gestion_acta.estado = estado_obj
            self.gestion_acta.bloqueada_edicion = False  # Permite re-edición
        
        self.gestion_acta.save()
        return True


class RevisionIndividual(models.Model):
    """Revisión individual por parte de un revisor"""
    
    proceso_revision = models.ForeignKey(
        ProcesoRevision,
        on_delete=models.CASCADE,
        related_name='revisiones'
    )
    
    revisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='revisiones_realizadas'
    )
    
    # Estado de la revisión
    revisado = models.BooleanField(default=False)
    aprobado = models.BooleanField(default=False)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_revision = models.DateTimeField(null=True, blank=True)
    
    # Comentarios y observaciones
    comentarios = models.TextField(
        blank=True,
        help_text="Comentarios del revisor"
    )
    observaciones_tecnicas = models.TextField(
        blank=True,
        help_text="Observaciones técnicas sobre el contenido"
    )
    
    # Información adicional
    tiempo_revision_minutos = models.IntegerField(
        null=True, blank=True,
        help_text="Tiempo dedicado a la revisión en minutos"
    )
    
    class Meta:
        verbose_name = "Revisión Individual"
        verbose_name_plural = "Revisiones Individuales"
        unique_together = ['proceso_revision', 'revisor']
        ordering = ['fecha_asignacion']
    
    def __str__(self):
        estado = "Aprobada" if self.aprobado else ("Rechazada" if self.revisado else "Pendiente")
        return f"Revisión de {self.revisor.get_full_name() or self.revisor.username} - {estado}"
    
    def realizar_revision(self, aprobado, comentarios="", observaciones_tecnicas=""):
        """Realiza la revisión"""
        self.revisado = True
        self.aprobado = aprobado
        self.fecha_revision = timezone.now()
        self.comentarios = comentarios
        self.observaciones_tecnicas = observaciones_tecnicas
        self.save()
        
        # Verificar si el proceso puede completarse
        if self.proceso_revision.puede_completarse():
            self.proceso_revision.completar_proceso()


class HistorialCambios(models.Model):
    """Historial detallado de cambios en el acta"""
    
    gestion_acta = models.ForeignKey(
        GestionActa,
        on_delete=models.CASCADE,
        related_name='historial_cambios'
    )
    
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cambios_realizados'
    )
    
    # Información del cambio
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    tipo_cambio = models.CharField(
        max_length=50,
        choices=[
            ('edicion_contenido', 'Edición de Contenido'),
            ('cambio_estado', 'Cambio de Estado'),
            ('envio_revision', 'Envío a Revisión'),
            ('aprobacion', 'Aprobación'),
            ('rechazo', 'Rechazo'),
            ('publicacion', 'Publicación'),
            ('exportacion', 'Exportación'),
        ]
    )
    
    descripcion = models.TextField()
    datos_adicionales = models.JSONField(
        default=dict,
        help_text="Datos adicionales sobre el cambio"
    )
    
    # Metadatos
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Historial de Cambios"
        verbose_name_plural = "Historial de Cambios"
        ordering = ['-fecha_cambio']
    
    def __str__(self):
        return f"{self.tipo_cambio} por {self.usuario.username} - {self.fecha_cambio.strftime('%d/%m/%Y %H:%M')}"


class ConfiguracionExportacion(models.Model):
    """Configuración para exportación de actas"""
    
    # Configuración PDF
    pdf_header_enabled = models.BooleanField(default=True)
    pdf_footer_enabled = models.BooleanField(default=True)
    pdf_watermark = models.CharField(max_length=200, blank=True)
    pdf_template = models.CharField(
        max_length=100,
        default='oficial',
        choices=[
            ('oficial', 'Plantilla Oficial'),
            ('simple', 'Plantilla Simple'),
            ('completa', 'Plantilla Completa'),
        ]
    )
    
    # Configuración Word
    word_template_path = models.CharField(max_length=500, blank=True)
    word_styles_enabled = models.BooleanField(default=True)
    
    # Configuración TXT
    txt_encoding = models.CharField(
        max_length=20,
        default='utf-8',
        choices=[
            ('utf-8', 'UTF-8'),
            ('latin-1', 'Latin-1'),
            ('ascii', 'ASCII'),
        ]
    )
    txt_line_endings = models.CharField(
        max_length=10,
        default='lf',
        choices=[
            ('lf', 'LF (Unix)'),
            ('crlf', 'CRLF (Windows)'),
            ('cr', 'CR (Mac)'),
        ]
    )
    
    # Metadatos generales
    incluir_metadatos = models.BooleanField(default=True)
    incluir_firma_digital = models.BooleanField(default=False)
    
    # Configuración activa
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración de Exportación"
        verbose_name_plural = "Configuraciones de Exportación"
        ordering = ['-activa', '-fecha_creacion']
    
    def __str__(self):
        return f"Config. Exportación {'(Activa)' if self.activa else '(Inactiva)'}"
    
    @classmethod
    def get_active_config(cls):
        """Obtiene la configuración activa"""
        return cls.objects.filter(activa=True).first()
