from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
import json

class ConfiguracionWhisper(models.Model):
    """Configuración para Whisper/Pyannote"""
    nombre = models.CharField(max_length=100, default="Whisper Principal")
    activo = models.BooleanField(default=True)
    
    # Configuraciones Whisper
    modelo_whisper = models.CharField(
        max_length=50,
        choices=[
            ('tiny', 'Tiny (39 MB)'),
            ('base', 'Base (74 MB)'),
            ('small', 'Small (244 MB)'),
            ('medium', 'Medium (769 MB)'),
            ('large', 'Large (1550 MB)'),
            ('large-v2', 'Large-v2 (1550 MB)'),
            ('large-v3', 'Large-v3 (1550 MB)'),
        ],
        default='base'
    )
    idioma = models.CharField(max_length=10, default='es')
    temperatura = models.FloatField(default=0.0)
    usar_vad = models.BooleanField(default=True, help_text="Voice Activity Detection")
    
    # Configuraciones Pyannote
    usar_pyannote = models.BooleanField(default=True)
    modelo_pyannote = models.CharField(max_length=100, default="pyannote/speaker-diarization-3.1")
    min_speakers = models.IntegerField(default=1)
    max_speakers = models.IntegerField(default=10)
    
    # Failover
    tiene_failover = models.BooleanField(default=False)
    failover_metodo = models.CharField(
        max_length=50,
        choices=[
            ('google_speech', 'Google Speech-to-Text'),
            ('azure_speech', 'Azure Speech Services'),
            ('aws_transcribe', 'AWS Transcribe'),
            ('manual', 'Transcripción Manual'),
        ],
        blank=True,
        null=True
    )
    
    # Metadatos
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración Whisper"
        verbose_name_plural = "Configuraciones Whisper"
        
    def __str__(self):
        return f"{self.nombre} ({'Activo' if self.activo else 'Inactivo'})"


class ConfiguracionIA(models.Model):
    """Configuración para IAs de generación de actas"""
    nombre = models.CharField(max_length=100)
    proveedor = models.CharField(
        max_length=50,
        choices=[
            ('openai', 'OpenAI'),
            ('deepseek', 'DeepSeek'),
            ('ollama', 'Ollama'),
            ('anthropic', 'Anthropic'),
        ]
    )
    activo = models.BooleanField(default=True)
    es_principal = models.BooleanField(default=False, help_text="IA principal para usar por defecto")
    
    # Configuración de conexión
    api_key = models.TextField(blank=True, help_text="API Key (se encripta automáticamente)")
    base_url = models.URLField(blank=True, help_text="URL base para APIs personalizadas (ej: Ollama)")
    
    # Configuración del modelo
    modelo = models.CharField(max_length=100, help_text="Nombre del modelo (ej: gpt-4, deepseek-chat)")
    temperatura = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=4000)
    top_p = models.FloatField(default=1.0)
    frequency_penalty = models.FloatField(default=0.0)
    presence_penalty = models.FloatField(default=0.0)
    
    # Configuraciones específicas por proveedor
    configuraciones_extra = models.JSONField(
        default=dict,
        blank=True,
        help_text="Configuraciones adicionales específicas del proveedor (JSON)"
    )
    
    # Prompts del sistema
    prompt_sistema = models.TextField(
        default="Eres un asistente especializado en la generación de actas municipales formales y precisas.",
        help_text="Prompt del sistema para este modelo"
    )
    prompt_generacion_acta = models.TextField(
        default="Genera un acta municipal formal basada en la siguiente transcripción de audio:",
        help_text="Prompt específico para generación de actas"
    )
    
    # Límites y restricciones
    limite_requests_minuto = models.IntegerField(default=60)
    timeout_segundos = models.IntegerField(default=30)
    
    # Metadatos
    orden_prioridad = models.IntegerField(default=1, help_text="Orden de prioridad (1 = más alta)")
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuración IA"
        verbose_name_plural = "Configuraciones IA"
        ordering = ['orden_prioridad', 'nombre']
        
    def __str__(self):
        return f"{self.nombre} ({self.proveedor}) - {'✓' if self.activo else '✗'}"
    
    def save(self, *args, **kwargs):
        # Solo una IA puede ser principal
        if self.es_principal:
            ConfiguracionIA.objects.filter(es_principal=True).update(es_principal=False)
        super().save(*args, **kwargs)
    
    def get_configuracion_completa(self):
        """Retorna la configuración completa para usar con la IA"""
        config = {
            'provider': self.proveedor,
            'model': self.modelo,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'temperature': self.temperatura,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'presence_penalty': self.presence_penalty,
            'timeout': self.timeout_segundos,
            'system_prompt': self.prompt_sistema,
            'acta_prompt': self.prompt_generacion_acta,
        }
        config.update(self.configuraciones_extra)
        return config


class PerfilUsuario(models.Model):
    """Perfiles y permisos de usuarios en el sistema de actas municipales"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    
    ROLES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador'),
        ('editor', 'Editor de Actas'),
        ('viewer', 'Solo Lectura'),
        ('secretario', 'Secretario Municipal'),
        ('alcalde', 'Alcalde'),
        ('concejal', 'Concejal'),
    ]
    
    DEPARTAMENTOS = [
        ('secretaria', 'Secretaría Municipal'),
        ('alcaldia', 'Alcaldía'),
        ('concejo', 'Concejo Municipal'),
        ('tesoreria', 'Tesorería'),
        ('obras', 'Obras Públicas'),
        ('desarrollo', 'Desarrollo Social'),
        ('ambiente', 'Medio Ambiente'),
        ('sistemas', 'Sistemas e IT'),
    ]
    
    rol = models.CharField(max_length=20, choices=ROLES, default='viewer', verbose_name="Rol")
    departamento = models.CharField(max_length=20, choices=DEPARTAMENTOS, blank=True, null=True, verbose_name="Departamento")
    cargo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cargo")
    telefono = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    extension = models.CharField(max_length=10, blank=True, null=True, verbose_name="Extensión")
    
    # Permisos específicos
    puede_configurar_ia = models.BooleanField(default=False, verbose_name="Puede configurar IA")
    puede_ver_configuraciones = models.BooleanField(default=False, verbose_name="Puede ver configuraciones")
    puede_gestionar_usuarios = models.BooleanField(default=False, verbose_name="Puede gestionar usuarios")
    puede_procesar_actas = models.BooleanField(default=False, verbose_name="Puede procesar actas")
    puede_publicar_actas = models.BooleanField(default=False, verbose_name="Puede publicar actas")
    puede_transcribir = models.BooleanField(default=False, verbose_name="Puede transcribir audio")
    puede_revisar_actas = models.BooleanField(default=False, verbose_name="Puede revisar actas")
    puede_aprobar_publicacion = models.BooleanField(default=False, verbose_name="Puede aprobar publicación")
    puede_gestionar_sesiones = models.BooleanField(default=False, verbose_name="Puede gestionar sesiones")
    
    # Límites operacionales
    limite_procesamiento_diario = models.IntegerField(default=10, verbose_name="Límite procesamiento diario")
    limite_transcripcion_horas = models.IntegerField(default=2, verbose_name="Límite transcripción (horas)")
    
    # Configuraciones personales
    configuraciones_ui = models.JSONField(default=dict, blank=True, verbose_name="Configuraciones UI")
    ultimo_acceso = models.DateTimeField(null=True, blank=True, verbose_name="Último acceso")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        
    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"
    
    def save(self, *args, **kwargs):
        # Auto-asignar permisos según el rol
        if self.rol == 'superadmin':
            self.puede_configurar_ia = True
            self.puede_ver_configuraciones = True
            self.puede_gestionar_usuarios = True
            self.puede_procesar_actas = True
            self.puede_publicar_actas = True
            self.puede_transcribir = True
            self.puede_revisar_actas = True
            self.puede_aprobar_publicacion = True
            self.puede_gestionar_sesiones = True
            self.limite_procesamiento_diario = 100
            self.limite_transcripcion_horas = 24
        elif self.rol == 'admin':
            self.puede_ver_configuraciones = True
            self.puede_procesar_actas = True
            self.puede_publicar_actas = True
            self.puede_transcribir = True
            self.puede_revisar_actas = True
            self.puede_aprobar_publicacion = True
            self.puede_gestionar_sesiones = True
            self.limite_procesamiento_diario = 50
            self.limite_transcripcion_horas = 8
        elif self.rol == 'editor':
            self.puede_procesar_actas = True
            self.puede_transcribir = True
            self.puede_revisar_actas = True
            self.limite_procesamiento_diario = 20
            self.limite_transcripcion_horas = 4
        elif self.rol == 'secretario':
            self.puede_procesar_actas = True
            self.puede_transcribir = True
            self.puede_revisar_actas = True
            self.puede_gestionar_sesiones = True
            self.limite_procesamiento_diario = 30
            self.limite_transcripcion_horas = 6
        elif self.rol in ['alcalde', 'concejal']:
            self.puede_revisar_actas = True
            self.puede_aprobar_publicacion = True
            self.limite_procesamiento_diario = 10
            self.limite_transcripcion_horas = 2
        
        super().save(*args, **kwargs)


class LogConfiguracion(models.Model):
    """Log de cambios en configuraciones"""
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tipo_configuracion = models.CharField(max_length=50)
    accion = models.CharField(
        max_length=20,
        choices=[
            ('create', 'Crear'),
            ('update', 'Actualizar'),
            ('delete', 'Eliminar'),
            ('activate', 'Activar'),
            ('deactivate', 'Desactivar'),
        ]
    )
    objeto_id = models.IntegerField()
    detalles = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Configuración"
        verbose_name_plural = "Logs de Configuraciones"
        ordering = ['-fecha']
        
    def __str__(self):
        return f"{self.usuario} - {self.accion} {self.tipo_configuracion} - {self.fecha}"


class PermisosDetallados(models.Model):
    """Modelo para gestionar permisos granulares del sistema"""
    perfil = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='permisos_detallados')
    
    # Permisos de Menús y Navegación
    ver_menu_dashboard = models.BooleanField(default=True, verbose_name="Ver menú Dashboard")
    ver_menu_transcribir = models.BooleanField(default=False, verbose_name="Ver menú Transcribir")
    ver_menu_procesar_actas = models.BooleanField(default=False, verbose_name="Ver menú Procesar Actas")
    ver_menu_revisar_actas = models.BooleanField(default=False, verbose_name="Ver menú Revisar Actas")
    ver_menu_publicar_actas = models.BooleanField(default=False, verbose_name="Ver menú Publicar Actas")
    ver_menu_gestionar_sesiones = models.BooleanField(default=False, verbose_name="Ver menú Gestionar Sesiones")
    ver_menu_configurar_ia = models.BooleanField(default=False, verbose_name="Ver menú Configurar IA")
    ver_menu_configurar_whisper = models.BooleanField(default=False, verbose_name="Ver menú Configurar Whisper")
    ver_menu_gestionar_usuarios = models.BooleanField(default=False, verbose_name="Ver menú Gestionar Usuarios")
    ver_menu_reportes = models.BooleanField(default=False, verbose_name="Ver menú Reportes")
    ver_menu_auditoria = models.BooleanField(default=False, verbose_name="Ver menú Auditoría")
    ver_menu_transparencia = models.BooleanField(default=False, verbose_name="Ver menú Portal Transparencia")
    
    # Permisos de Funcionalidades - Transcripción
    subir_audio_transcripcion = models.BooleanField(default=False, verbose_name="Subir audio para transcripción")
    iniciar_transcripcion = models.BooleanField(default=False, verbose_name="Iniciar proceso de transcripción")
    pausar_transcripcion = models.BooleanField(default=False, verbose_name="Pausar transcripción")
    cancelar_transcripcion = models.BooleanField(default=False, verbose_name="Cancelar transcripción")
    ver_progreso_transcripcion = models.BooleanField(default=False, verbose_name="Ver progreso de transcripción")
    descargar_transcripcion = models.BooleanField(default=False, verbose_name="Descargar transcripción")
    editar_transcripcion = models.BooleanField(default=False, verbose_name="Editar texto transcrito")
    
    # Permisos de Funcionalidades - Procesamiento IA
    procesar_con_ia = models.BooleanField(default=False, verbose_name="Procesar con IA")
    seleccionar_modelo_ia = models.BooleanField(default=False, verbose_name="Seleccionar modelo IA")
    ajustar_parametros_ia = models.BooleanField(default=False, verbose_name="Ajustar parámetros IA")
    ver_analisis_ia = models.BooleanField(default=False, verbose_name="Ver análisis de IA")
    regenerar_con_ia = models.BooleanField(default=False, verbose_name="Regenerar con IA")
    
    # Permisos de Funcionalidades - Gestión de Actas
    crear_acta_nueva = models.BooleanField(default=False, verbose_name="Crear acta nueva")
    editar_acta_borrador = models.BooleanField(default=False, verbose_name="Editar acta en borrador")
    editar_acta_revision = models.BooleanField(default=False, verbose_name="Editar acta en revisión")
    eliminar_acta = models.BooleanField(default=False, verbose_name="Eliminar acta")
    cambiar_estado_acta = models.BooleanField(default=False, verbose_name="Cambiar estado de acta")
    asignar_revisor = models.BooleanField(default=False, verbose_name="Asignar revisor")
    ver_historial_cambios = models.BooleanField(default=False, verbose_name="Ver historial de cambios")
    
    # Permisos de Funcionalidades - Revisión y Aprobación
    revisar_actas = models.BooleanField(default=False, verbose_name="Revisar actas")
    aprobar_actas = models.BooleanField(default=False, verbose_name="Aprobar actas")
    rechazar_actas = models.BooleanField(default=False, verbose_name="Rechazar actas")
    solicitar_cambios = models.BooleanField(default=False, verbose_name="Solicitar cambios")
    agregar_comentarios = models.BooleanField(default=False, verbose_name="Agregar comentarios")
    firmar_digitalmente = models.BooleanField(default=False, verbose_name="Firmar digitalmente")
    
    # Permisos de Funcionalidades - Publicación
    publicar_actas = models.BooleanField(default=False, verbose_name="Publicar actas")
    despublicar_actas = models.BooleanField(default=False, verbose_name="Despublicar actas")
    programar_publicacion = models.BooleanField(default=False, verbose_name="Programar publicación")
    gestionar_portal_transparencia = models.BooleanField(default=False, verbose_name="Gestionar portal transparencia")
    
    # Permisos de Funcionalidades - Sesiones
    crear_sesion = models.BooleanField(default=False, verbose_name="Crear sesión")
    editar_sesion = models.BooleanField(default=False, verbose_name="Editar sesión")
    eliminar_sesion = models.BooleanField(default=False, verbose_name="Eliminar sesión")
    gestionar_asistentes = models.BooleanField(default=False, verbose_name="Gestionar asistentes")
    gestionar_orden_dia = models.BooleanField(default=False, verbose_name="Gestionar orden del día")
    
    # Permisos de Configuración
    configurar_modelos_ia = models.BooleanField(default=False, verbose_name="Configurar modelos IA")
    configurar_whisper = models.BooleanField(default=False, verbose_name="Configurar Whisper")
    probar_configuraciones = models.BooleanField(default=False, verbose_name="Probar configuraciones")
    ver_logs_sistema = models.BooleanField(default=False, verbose_name="Ver logs del sistema")
    
    # Permisos de Administración
    gestionar_perfiles_usuarios = models.BooleanField(default=False, verbose_name="Gestionar perfiles usuarios")
    asignar_permisos = models.BooleanField(default=False, verbose_name="Asignar permisos")
    ver_reportes_uso = models.BooleanField(default=False, verbose_name="Ver reportes de uso")
    ver_estadisticas = models.BooleanField(default=False, verbose_name="Ver estadísticas")
    gestionar_respaldos = models.BooleanField(default=False, verbose_name="Gestionar respaldos")
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Permisos Detallados"
        verbose_name_plural = "Permisos Detallados"
        
    def __str__(self):
        return f"Permisos de {self.perfil.usuario.username}"
    
    @classmethod
    def aplicar_permisos_por_rol(cls, perfil):
        """Aplica permisos predeterminados según el rol del perfil"""
        permisos, created = cls.objects.get_or_create(perfil=perfil)
        
        # Reset todos los permisos a False
        for field in cls._meta.fields:
            if field.name.startswith(('ver_', 'subir_', 'iniciar_', 'pausar_', 'cancelar_', 
                                     'crear_', 'editar_', 'eliminar_', 'cambiar_', 'asignar_',
                                     'revisar_', 'aprobar_', 'rechazar_', 'solicitar_', 'agregar_',
                                     'firmar_', 'publicar_', 'despublicar_', 'programar_', 'gestionar_',
                                     'configurar_', 'probar_')):
                setattr(permisos, field.name, False)
        
        # Aplicar permisos según rol
        if perfil.rol == 'superadmin':
            # Superadmin tiene todos los permisos
            for field in cls._meta.fields:
                if field.name not in ['id', 'perfil', 'fecha_creacion', 'fecha_actualizacion']:
                    setattr(permisos, field.name, True)
                    
        elif perfil.rol == 'admin':
            # Administrador - permisos amplios excepto configuración de sistema
            permisos.ver_menu_dashboard = True
            permisos.ver_menu_transcribir = True
            permisos.ver_menu_procesar_actas = True
            permisos.ver_menu_revisar_actas = True
            permisos.ver_menu_publicar_actas = True
            permisos.ver_menu_gestionar_sesiones = True
            permisos.ver_menu_gestionar_usuarios = True
            permisos.ver_menu_reportes = True
            permisos.ver_menu_auditoria = True
            permisos.ver_menu_transparencia = True
            
            # Funcionalidades principales
            permisos.subir_audio_transcripcion = True
            permisos.iniciar_transcripcion = True
            permisos.ver_progreso_transcripcion = True
            permisos.descargar_transcripcion = True
            permisos.editar_transcripcion = True
            permisos.procesar_con_ia = True
            permisos.ver_analisis_ia = True
            permisos.regenerar_con_ia = True
            permisos.crear_acta_nueva = True
            permisos.editar_acta_borrador = True
            permisos.editar_acta_revision = True
            permisos.cambiar_estado_acta = True
            permisos.asignar_revisor = True
            permisos.ver_historial_cambios = True
            permisos.revisar_actas = True
            permisos.aprobar_actas = True
            permisos.solicitar_cambios = True
            permisos.agregar_comentarios = True
            permisos.publicar_actas = True
            permisos.programar_publicacion = True
            permisos.gestionar_portal_transparencia = True
            permisos.crear_sesion = True
            permisos.editar_sesion = True
            permisos.gestionar_asistentes = True
            permisos.gestionar_orden_dia = True
            permisos.gestionar_perfiles_usuarios = True
            permisos.ver_reportes_uso = True
            permisos.ver_estadisticas = True
            
        elif perfil.rol == 'secretario':
            # Secretario municipal - gestión completa de sesiones y actas
            permisos.ver_menu_dashboard = True
            permisos.ver_menu_transcribir = True
            permisos.ver_menu_procesar_actas = True
            permisos.ver_menu_revisar_actas = True
            permisos.ver_menu_gestionar_sesiones = True
            permisos.ver_menu_transparencia = True
            
            permisos.subir_audio_transcripcion = True
            permisos.iniciar_transcripcion = True
            permisos.ver_progreso_transcripcion = True
            permisos.descargar_transcripcion = True
            permisos.editar_transcripcion = True
            permisos.procesar_con_ia = True
            permisos.ver_analisis_ia = True
            permisos.crear_acta_nueva = True
            permisos.editar_acta_borrador = True
            permisos.cambiar_estado_acta = True
            permisos.ver_historial_cambios = True
            permisos.agregar_comentarios = True
            permisos.crear_sesion = True
            permisos.editar_sesion = True
            permisos.gestionar_asistentes = True
            permisos.gestionar_orden_dia = True
            
        elif perfil.rol == 'alcalde':
            # Alcalde - revisión y aprobación
            permisos.ver_menu_dashboard = True
            permisos.ver_menu_revisar_actas = True
            permisos.ver_menu_publicar_actas = True
            permisos.ver_menu_transparencia = True
            permisos.ver_menu_reportes = True
            
            permisos.ver_historial_cambios = True
            permisos.revisar_actas = True
            permisos.aprobar_actas = True
            permisos.rechazar_actas = True
            permisos.solicitar_cambios = True
            permisos.agregar_comentarios = True
            permisos.firmar_digitalmente = True
            permisos.publicar_actas = True
            permisos.gestionar_portal_transparencia = True
            permisos.ver_estadisticas = True
            
        elif perfil.rol == 'concejal':
            # Concejal - revisión limitada
            permisos.ver_menu_dashboard = True
            permisos.ver_menu_revisar_actas = True
            permisos.ver_menu_transparencia = True
            
            permisos.ver_historial_cambios = True
            permisos.revisar_actas = True
            permisos.agregar_comentarios = True
            permisos.firmar_digitalmente = True
            
        elif perfil.rol == 'editor':
            # Editor - procesamiento y edición
            permisos.ver_menu_dashboard = True
            permisos.ver_menu_transcribir = True
            permisos.ver_menu_procesar_actas = True
            
            permisos.subir_audio_transcripcion = True
            permisos.iniciar_transcripcion = True
            permisos.ver_progreso_transcripcion = True
            permisos.descargar_transcripcion = True
            permisos.editar_transcripcion = True
            permisos.procesar_con_ia = True
            permisos.ver_analisis_ia = True
            permisos.crear_acta_nueva = True
            permisos.editar_acta_borrador = True
            permisos.ver_historial_cambios = True
            permisos.agregar_comentarios = True
            
        elif perfil.rol == 'viewer':
            # Visualizador - solo lectura
            permisos.ver_menu_dashboard = True
            permisos.ver_menu_transparencia = True
            permisos.ver_historial_cambios = True
            
        permisos.save()
        return permisos


# ==================== MODELOS SMTP ====================

class ConfiguracionSMTP(models.Model):
    """Configuración de proveedores SMTP múltiples con failover"""
    nombre = models.CharField(max_length=100, verbose_name="Nombre del proveedor")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    por_defecto = models.BooleanField(default=False, verbose_name="Proveedor por defecto")
    prioridad = models.IntegerField(default=1, verbose_name="Prioridad (1=mayor prioridad)")
    
    # Configuración básica SMTP
    servidor_smtp = models.CharField(max_length=255, verbose_name="Servidor SMTP")
    puerto = models.IntegerField(default=587, verbose_name="Puerto")
    usuario_smtp = models.CharField(max_length=255, verbose_name="Usuario SMTP")
    password_smtp = models.CharField(max_length=255, verbose_name="Contraseña SMTP")
    
    # Configuración de seguridad
    usa_tls = models.BooleanField(default=True, verbose_name="Usar TLS")
    usa_ssl = models.BooleanField(default=False, verbose_name="Usar SSL")
    
    # Configuración de remitente
    email_remitente = models.EmailField(verbose_name="Email remitente")
    nombre_remitente = models.CharField(max_length=255, verbose_name="Nombre del remitente")
    
    # Límites
    limite_diario = models.IntegerField(default=1000, verbose_name="Límite diario de emails")
    emails_enviados_hoy = models.IntegerField(default=0, verbose_name="Emails enviados hoy")
    ultima_actualizacion_contador = models.DateField(auto_now=True, verbose_name="Última actualización contador")
    
    # Configuración específica por proveedor
    proveedor = models.CharField(
        max_length=50,
        choices=[
            ('office365', 'Office 365'),
            ('gmail', 'Gmail'),
            ('yahoo', 'Yahoo'),
            ('sendgrid', 'SendGrid'),
            ('mailgun', 'Mailgun'),
            ('ses', 'Amazon SES'),
            ('smtp2go', 'SMTP2GO'),
            ('custom', 'Personalizado'),
        ],
        default='office365',
        verbose_name="Tipo de proveedor"
    )
    
    # Configuraciones adicionales (JSON)
    configuraciones_extra = models.JSONField(default=dict, blank=True, verbose_name="Configuraciones adicionales")
    
    # Estado y monitoreo
    ultimo_test = models.DateTimeField(null=True, blank=True, verbose_name="Último test")
    test_exitoso = models.BooleanField(default=False, verbose_name="Último test exitoso")
    mensaje_error = models.TextField(blank=True, null=True, verbose_name="Último mensaje de error")
    
    # Metadatos
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Creado por")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")
    
    class Meta:
        verbose_name = "Configuración SMTP"
        verbose_name_plural = "Configuraciones SMTP"
        ordering = ['prioridad', 'nombre']
    
    def __str__(self):
        status = "✅" if self.activo else "❌"
        default = "⭐" if self.por_defecto else ""
        return f"{status} {default} {self.nombre} ({self.proveedor})"
    
    def save(self, *args, **kwargs):
        # Solo un proveedor puede ser por defecto
        if self.por_defecto:
            ConfiguracionSMTP.objects.filter(por_defecto=True).update(por_defecto=False)
        super().save(*args, **kwargs)
    
    def reset_contador_diario(self):
        """Resetea el contador diario si cambió el día"""
        from datetime import date
        if self.ultima_actualizacion_contador < date.today():
            self.emails_enviados_hoy = 0
            self.ultima_actualizacion_contador = date.today()
            self.save()
    
    def puede_enviar_email(self):
        """Verifica si puede enviar un email más"""
        self.reset_contador_diario()
        return self.activo and self.emails_enviados_hoy < self.limite_diario
    
    def incrementar_contador(self):
        """Incrementa el contador de emails enviados"""
        self.reset_contador_diario()
        self.emails_enviados_hoy += 1
        self.save()
    
    @property
    def configuracion_predefinida(self):
        """Retorna configuración predefinida según el proveedor"""
        configuraciones = {
            'office365': {
                'servidor_smtp': 'smtp-mail.outlook.com',
                'puerto': 587,
                'usa_tls': True,
                'usa_ssl': False,
            },
            'gmail': {
                'servidor_smtp': 'smtp.gmail.com',
                'puerto': 587,
                'usa_tls': True,
                'usa_ssl': False,
            },
            'yahoo': {
                'servidor_smtp': 'smtp.mail.yahoo.com',
                'puerto': 587,
                'usa_tls': True,
                'usa_ssl': False,
            },
            'sendgrid': {
                'servidor_smtp': 'smtp.sendgrid.net',
                'puerto': 587,
                'usa_tls': True,
                'usa_ssl': False,
            },
            'mailgun': {
                'servidor_smtp': 'smtp.mailgun.org',
                'puerto': 587,
                'usa_tls': True,
                'usa_ssl': False,
            },
            'ses': {
                'servidor_smtp': 'email-smtp.us-east-1.amazonaws.com',
                'puerto': 587,
                'usa_tls': True,
                'usa_ssl': False,
            },
            'smtp2go': {
                'servidor_smtp': 'mail.smtp2go.com',
                'puerto': 587,
                'usa_tls': True,
                'usa_ssl': False,
            }
        }
        return configuraciones.get(self.proveedor, {})


class ConfiguracionEmail(models.Model):
    """Configuración global del sistema de emails"""
    nombre_aplicacion = models.CharField(max_length=255, default="Sistema de Actas Municipales", verbose_name="Nombre de la aplicación")
    logo_email = models.ImageField(upload_to='config/email/', blank=True, null=True, verbose_name="Logo para emails")
    
    # Plantilla HTML base
    template_html_base = models.TextField(
        default="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{asunto}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #1e3a8a; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #666; }
        .logo { max-width: 200px; height: auto; }
    </style>
</head>
<body>
    <div class="header">
        {% if logo_url %}<img src="{{logo_url}}" alt="Logo" class="logo">{% endif %}
        <h1>{{nombre_aplicacion}}</h1>
    </div>
    <div class="content">
        {{contenido}}
    </div>
    <div class="footer">
        {{pie_pagina}}
    </div>
</body>
</html>
        """,
        verbose_name="Template HTML base"
    )
    
    # Pie de página
    pie_pagina = models.TextField(
        default="""
<p><strong>Municipio de Pastaza</strong><br>
Puyo, Pastaza - Ecuador<br>
Teléfono: (03) 2885-133<br>
Email: info@puyo.gob.ec</p>
<p><small>Este es un mensaje automático del Sistema de Actas Municipales. Por favor no responder a este email.</small></p>
        """,
        verbose_name="Pie de página"
    )
    
    # Configuración de envío
    email_respuesta = models.EmailField(default="noreply@puyo.gob.ec", verbose_name="Email de no respuesta")
    email_soporte = models.EmailField(default="soporte@puyo.gob.ec", verbose_name="Email de soporte")
    
    # URLs del sistema
    url_sistema = models.URLField(default="http://localhost:8000", verbose_name="URL del sistema")
    url_publica = models.URLField(default="http://puyo.gob.ec", verbose_name="URL pública del municipio")
    
    # Configuraciones de comportamiento
    reintentos_maximos = models.IntegerField(default=3, verbose_name="Máximo reintentos por email")
    tiempo_espera_reintento = models.IntegerField(default=300, verbose_name="Tiempo de espera entre reintentos (segundos)")
    
    # Control de activación
    sistema_activo = models.BooleanField(default=True, verbose_name="Sistema de emails activo")
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Configuración de Email"
        verbose_name_plural = "Configuración de Email"
    
    def __str__(self):
        return f"Configuración Email - {self.nombre_aplicacion}"
    
    def save(self, *args, **kwargs):
        # Solo debe existir una configuración
        if not self.pk and ConfiguracionEmail.objects.exists():
            self.pk = ConfiguracionEmail.objects.first().pk
        super().save(*args, **kwargs)


class LogEnvioEmail(models.Model):
    """Log de envíos de email para auditoría y debugging"""
    configuracion_smtp = models.ForeignKey(ConfiguracionSMTP, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Datos del email
    destinatario = models.EmailField(verbose_name="Destinatario")
    asunto = models.CharField(max_length=255, verbose_name="Asunto")
    contenido_texto = models.TextField(blank=True, verbose_name="Contenido en texto")
    contenido_html = models.TextField(blank=True, verbose_name="Contenido HTML")
    
    # Estado del envío
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('error', 'Error'),
        ('reintentando', 'Reintentando'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    
    # Detalles del resultado
    enviado_en = models.DateTimeField(null=True, blank=True)
    mensaje_error = models.TextField(blank=True, null=True)
    intentos_realizados = models.IntegerField(default=0)
    tiempo_procesamiento = models.FloatField(null=True, blank=True, verbose_name="Tiempo de procesamiento (segundos)")
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    usuario_solicitante = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Log de Envío de Email"
        verbose_name_plural = "Logs de Envío de Email"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.estado.upper()} - {self.destinatario} - {self.asunto[:50]}"
