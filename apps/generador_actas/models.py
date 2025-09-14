"""
Modelos para el módulo Generador de Actas con IA
Incluye proveedores de IA, segmentos de plantillas, plantillas y actas generadas
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import json


class ProveedorIA(models.Model):
    """Configuración de proveedores de IA disponibles"""
    TIPO_PROVEEDOR = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic Claude'),
        ('deepseek', 'DeepSeek'),
        ('google', 'Google Gemini'),
        ('ollama', 'Ollama (Local)'),
        ('lmstudio', 'LM Studio (Local)'),
        ('groq', 'Groq'),
        ('generic1', 'Proveedor Genérico 1'),
        ('generic2', 'Proveedor Genérico 2'),
    ]
    
    # Identificación
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre descriptivo del proveedor")
    tipo = models.CharField(max_length=50, choices=TIPO_PROVEEDOR, help_text="Tipo de proveedor de IA")
    
    # Configuración de API
    api_key = models.CharField(max_length=500, blank=True, help_text="Clave API (se encripta en producción)")
    api_url = models.URLField(blank=True, help_text="URL base de la API")
    modelo = models.CharField(max_length=100, help_text="Modelo específico a usar")
    
    # Parámetros de generación
    temperatura = models.FloatField(default=0.7, help_text="Creatividad del modelo (0-1)")
    max_tokens = models.IntegerField(default=4000, help_text="Máximo de tokens por respuesta")
    timeout = models.IntegerField(default=60, help_text="Timeout en segundos")
    
    # Configuración adicional JSON
    configuracion_adicional = models.JSONField(default=dict, blank=True, help_text="Parámetros adicionales del proveedor")
    prompt_sistema_global = models.TextField(blank=True, help_text="Prompt de sistema global para este proveedor")
    
    # Estado y costos
    activo = models.BooleanField(default=True, help_text="Si está disponible para uso")
    costo_por_1k_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0, help_text="Costo estimado por 1000 tokens")
    
    # Métricas de uso
    total_llamadas = models.IntegerField(default=0, help_text="Total de llamadas realizadas")
    total_tokens_usados = models.BigIntegerField(default=0, help_text="Total de tokens consumidos")
    ultima_conexion_exitosa = models.DateTimeField(null=True, blank=True, help_text="Última conexión exitosa")
    ultimo_error = models.TextField(blank=True, help_text="Último error registrado")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='proveedores_ia_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proveedor IA"
        verbose_name_plural = "Proveedores IA"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:proveedor_detail', kwargs={'pk': self.pk})
    
    @property
    def esta_configurado(self):
        """Verifica si el proveedor está correctamente configurado"""
        # Proveedores que requieren API key
        if self.tipo in ['openai', 'anthropic', 'deepseek', 'google', 'groq', 'generic1', 'generic2']:
            if not self.api_key:
                # Buscar en variables de entorno
                from django.conf import settings
                env_key = f"{self.tipo.upper()}_API_KEY"
                if not getattr(settings, env_key, None):
                    return False
        
        # Proveedores locales que requieren URL
        if self.tipo in ['ollama', 'lmstudio'] and not self.api_url:
            return False
            
        return bool(self.modelo)
    
    @property
    def api_key_masked(self):
        """Devuelve la API key enmascarada para mostrar en UI"""
        if not self.api_key:
            return "No configurada"
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}{'*' * (len(self.api_key) - 8)}{self.api_key[-4:]}"
    
    def obtener_configuracion_completa(self):
        """Obtiene la configuración completa incluyendo valores por defecto del .env"""
        from django.conf import settings
        
        config = {
            'tipo': self.tipo,
            'nombre': self.nombre,
            'modelo': self.modelo,
            'temperatura': self.temperatura,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'configuracion_adicional': self.configuracion_adicional,
            'prompt_sistema_global': self.prompt_sistema_global,
        }
        
        # API Key (prioridad: BD > .env)
        if self.api_key:
            config['api_key'] = self.api_key
        else:
            env_key = f"{self.tipo.upper()}_API_KEY"
            config['api_key'] = getattr(settings, env_key, '')
        
        # API URL (prioridad: BD > .env)
        if self.api_url:
            config['api_url'] = self.api_url
        else:
            env_url = f"{self.tipo.upper()}_API_URL"
            config['api_url'] = getattr(settings, env_url, '')
        
        return config
    
    def actualizar_metricas(self, tokens_usados=0, exito=True, error=None):
        """Actualiza las métricas de uso del proveedor"""
        self.total_llamadas += 1
        if tokens_usados > 0:
            self.total_tokens_usados += tokens_usados
        
        if exito:
            self.ultima_conexion_exitosa = timezone.now()
            self.ultimo_error = ""
        else:
            self.ultimo_error = error or "Error desconocido"
        
        self.save(update_fields=['total_llamadas', 'total_tokens_usados', 
                                'ultima_conexion_exitosa', 'ultimo_error'])
    
    @classmethod
    def obtener_configuraciones_por_defecto(cls):
        """Obtiene las configuraciones por defecto desde el .env"""
        from django.conf import settings
        
        configuraciones = {}
        for tipo, nombre in cls.TIPO_PROVEEDOR:
            env_prefix = tipo.upper()
            configuraciones[tipo] = {
                'api_key': getattr(settings, f'{env_prefix}_API_KEY', ''),
                'api_url': getattr(settings, f'{env_prefix}_API_URL', ''),
                'modelo': getattr(settings, f'{env_prefix}_DEFAULT_MODEL', ''),
                'temperatura': float(getattr(settings, f'{env_prefix}_DEFAULT_TEMPERATURE', 0.7)),
                'max_tokens': int(getattr(settings, f'{env_prefix}_DEFAULT_MAX_TOKENS', 4000)),
            }
        
        return configuraciones


class SegmentoPlantilla(models.Model):
    """Segmentos reutilizables para construir plantillas de actas"""
    TIPO_SEGMENTO = [
        ('estatico', 'Estático'),
        ('dinamico', 'Dinámico con IA'),
        ('hibrido', 'Híbrido')
    ]
    
    CATEGORIA_SEGMENTO = [
        ('encabezado', 'Encabezado'),
        ('titulo', 'Título'),
        ('fecha', 'Fecha'),
        ('asistentes', 'Asistentes'),
        ('orden_dia', 'Orden del Día'),
        ('introduccion', 'Introducción'),
        ('desarrollo', 'Desarrollo'),
        ('resoluciones', 'Resoluciones'),
        ('compromisos', 'Compromisos'),
        ('cierre', 'Cierre'),
        ('firmas', 'Firmas'),
        ('anexos', 'Anexos'),
        ('otros', 'Otros')
    ]
    
    # Identificación
    codigo = models.CharField(max_length=50, unique=True, help_text="Código único del segmento")
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo del segmento")
    descripcion = models.TextField(help_text="Descripción del propósito del segmento")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_SEGMENTO, help_text="Categoría del segmento")
    tipo = models.CharField(max_length=20, choices=TIPO_SEGMENTO, help_text="Tipo de procesamiento")
    
    # Configuración de procesamiento IA
    prompt_ia = models.TextField(blank=True, help_text="Prompt para segmentos dinámicos")
    estructura_json = models.JSONField(default=dict, blank=True, help_text="Estructura esperada del resultado")
    componentes = models.JSONField(default=dict, blank=True, help_text="Componentes del segmento")
    parametros_entrada = models.JSONField(default=list, blank=True, help_text="Parámetros requeridos del contexto")
    
    # Configuración visual y comportamiento
    orden_defecto = models.IntegerField(default=0, help_text="Orden por defecto en plantillas")
    reutilizable = models.BooleanField(default=True, help_text="Si puede ser usado en múltiples plantillas")
    obligatorio = models.BooleanField(default=False, help_text="Si es obligatorio en todas las plantillas")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='segmentos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Segmento de Plantilla"
        verbose_name_plural = "Segmentos de Plantilla"
        ordering = ['categoria', 'orden_defecto', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:editar_segmento', kwargs={'pk': self.pk})
    
    @property
    def es_dinamico(self):
        """Verifica si el segmento requiere procesamiento IA"""
        return self.tipo in ['dinamico', 'hibrido']
    
    @property
    def tiene_prompt(self):
        """Verifica si tiene prompt configurado"""
        return bool(self.prompt_ia.strip())


class PlantillaActa(models.Model):
    """Plantillas configurables para diferentes tipos de actas"""
    TIPO_ACTA = [
        ('ordinaria', 'Sesión Ordinaria'),
        ('extraordinaria', 'Sesión Extraordinaria'),
        ('audiencia', 'Audiencia Pública'),
        ('comision', 'Comisión'),
        ('directorio', 'Directorio'),
        ('asamblea', 'Asamblea'),
        ('otros', 'Otros')
    ]
    
    # Identificación
    codigo = models.CharField(max_length=50, unique=True, help_text="Código único de la plantilla")
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo de la plantilla")
    descripcion = models.TextField(help_text="Descripción del uso de la plantilla")
    tipo_acta = models.CharField(max_length=50, choices=TIPO_ACTA, help_text="Tipo de acta que genera")
    
    # Configuración de segmentos
    segmentos = models.ManyToManyField(SegmentoPlantilla, through='ConfiguracionSegmento', help_text="Segmentos que componen la plantilla")
    
    # Configuración de procesamiento
    prompt_global = models.TextField(help_text="Prompt para unificación final del acta")
    proveedor_ia_defecto = models.ForeignKey(ProveedorIA, on_delete=models.SET_NULL, null=True, blank=True, help_text="Proveedor IA por defecto")
    configuracion_procesamiento = models.JSONField(default=dict, blank=True, help_text="Configuración adicional de procesamiento")
    
    # Estado y versión
    activa = models.BooleanField(default=True, help_text="Si está disponible para uso")
    version = models.CharField(max_length=20, default='1.0', help_text="Versión de la plantilla")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='plantillas_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla de Acta"
        verbose_name_plural = "Plantillas de Actas"
        ordering = ['tipo_acta', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_acta_display()})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:editar_plantilla', kwargs={'pk': self.pk})
    
    @property
    def segmentos_ordenados(self):
        """Obtiene los segmentos ordenados según configuración"""
        return self.configuracionsegmento_set.all().order_by('orden')
    
    @property
    def total_segmentos(self):
        """Total de segmentos en la plantilla"""
        return self.segmentos.count()
    
    @property
    def segmentos_dinamicos(self):
        """Total de segmentos que requieren IA"""
        return self.segmentos.filter(tipo__in=['dinamico', 'hibrido']).count()


class ConfiguracionSegmento(models.Model):
    """Configuración específica de un segmento dentro de una plantilla"""
    plantilla = models.ForeignKey(PlantillaActa, on_delete=models.CASCADE)
    segmento = models.ForeignKey(SegmentoPlantilla, on_delete=models.CASCADE)
    
    # Configuración específica para esta plantilla
    orden = models.IntegerField(help_text="Orden del segmento en la plantilla")
    obligatorio = models.BooleanField(default=False, help_text="Si es obligatorio en esta plantilla")
    prompt_personalizado = models.TextField(blank=True, help_text="Prompt específico para esta plantilla")
    parametros_override = models.JSONField(default=dict, blank=True, help_text="Parámetros que sobrescriben los del segmento")
    
    class Meta:
        verbose_name = "Configuración de Segmento"
        verbose_name_plural = "Configuraciones de Segmentos"
        ordering = ['plantilla', 'orden']
        unique_together = ['plantilla', 'orden']
    
    def __str__(self):
        return f"{self.plantilla.nombre} - {self.segmento.nombre} (Orden: {self.orden})"
    
    @property
    def prompt_efectivo(self):
        """Obtiene el prompt a usar (personalizado o del segmento)"""
        return self.prompt_personalizado or self.segmento.prompt_ia


class ActaGenerada(models.Model):
    """Actas generadas a partir de transcripciones usando IA"""
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente de Procesamiento'),
        ('procesando', 'Procesando'),
        ('procesando_segmentos', 'Procesando Segmentos'),
        ('unificando', 'Unificando Contenido'),
        ('revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('publicado', 'Publicado'),
        ('rechazado', 'Rechazado'),
        ('error', 'Error en Procesamiento')
    ]
    
    # Identificación
    numero_acta = models.CharField(max_length=50, unique=True, help_text="Número único del acta")
    titulo = models.CharField(max_length=300, help_text="Título del acta")
    
    # Referencias a otros módulos
    transcripcion = models.ForeignKey('transcripcion.Transcripcion', on_delete=models.CASCADE, help_text="Transcripción base")
    plantilla = models.ForeignKey(PlantillaActa, on_delete=models.PROTECT, help_text="Plantilla usada")
    proveedor_ia = models.ForeignKey(ProveedorIA, on_delete=models.PROTECT, help_text="Proveedor IA usado")
    
    # Datos procesados
    segmentos_procesados = models.JSONField(default=dict, blank=True, help_text="Resultado del procesamiento de segmentos")
    contenido_borrador = models.TextField(blank=True, help_text="Borrador inicial del acta")
    contenido_final = models.TextField(blank=True, help_text="Versión final del acta")
    contenido_html = models.TextField(blank=True, help_text="Versión HTML del acta")
    
    # Metadatos y métricas
    metadatos = models.JSONField(default=dict, blank=True, help_text="Metadatos adicionales")
    metricas_procesamiento = models.JSONField(default=dict, blank=True, help_text="Métricas de tiempo, tokens, costo")
    historial_cambios = models.JSONField(default=list, blank=True, help_text="Historial de modificaciones")
    
    # Estado y tracking
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='borrador', help_text="Estado actual del acta")
    progreso = models.IntegerField(default=0, help_text="Progreso de procesamiento (0-100)")
    task_id_celery = models.CharField(max_length=255, blank=True, help_text="ID de tarea Celery")
    mensajes_error = models.TextField(blank=True, help_text="Mensajes de error durante procesamiento")
    
    # Fechas importantes
    fecha_sesion = models.DateTimeField(help_text="Fecha de la sesión/reunión")
    fecha_procesamiento = models.DateTimeField(null=True, blank=True, help_text="Fecha de inicio de procesamiento")
    fecha_revision = models.DateTimeField(null=True, blank=True, help_text="Fecha de revisión")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, help_text="Fecha de aprobación")
    fecha_publicacion = models.DateTimeField(null=True, blank=True, help_text="Fecha de publicación")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='actas_creadas')
    usuario_revision = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actas_revisadas')
    usuario_aprobacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actas_aprobadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Acta Generada"
        verbose_name_plural = "Actas Generadas"
        ordering = ['-fecha_sesion', '-fecha_creacion']
        permissions = [
            ("can_approve_acta", "Puede aprobar actas"),
            ("can_publish_acta", "Puede publicar actas"),
            ("can_review_acta", "Puede revisar actas"),
        ]
    
    def __str__(self):
        return f"{self.numero_acta} - {self.titulo}"
    
    def get_absolute_url(self):
        return reverse('generador_actas:detalle_acta', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Generar número de acta si no existe
        if not self.numero_acta:
            year = self.fecha_sesion.year if self.fecha_sesion else timezone.now().year
            last_acta = ActaGenerada.objects.filter(
                numero_acta__startswith=f"ACTA-{year}-"
            ).order_by('-numero_acta').first()
            
            if last_acta:
                try:
                    last_num = int(last_acta.numero_acta.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.numero_acta = f"ACTA-{year}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def estado_display_class(self):
        """Clase CSS para mostrar el estado"""
        classes = {
            'borrador': 'badge-secondary',
            'pendiente': 'badge-info',
            'procesando': 'badge-primary',
            'procesando_segmentos': 'badge-primary',
            'unificando': 'badge-primary',
            'revision': 'badge-warning',
            'aprobado': 'badge-success',
            'publicado': 'badge-success',
            'rechazado': 'badge-danger',
            'error': 'badge-danger'
        }
        return classes.get(self.estado, 'badge-secondary')
    
    @property
    def puede_procesar(self):
        """Verifica si el acta puede ser procesada"""
        return self.estado in ['borrador', 'error']
    
    @property
    def puede_revisar(self):
        """Verifica si el acta puede ser revisada"""
        return self.estado == 'revision'
    
    @property
    def puede_aprobar(self):
        """Verifica si el acta puede ser aprobada"""
        return self.estado == 'revision'
    
    def agregar_historial(self, accion, usuario, detalles=None):
        """Agrega una entrada al historial de cambios"""
        entrada = {
            'fecha': timezone.now().isoformat(),
            'usuario': usuario.username,
            'accion': accion,
            'detalles': detalles or {}
        }
        self.historial_cambios.append(entrada)
        self.save(update_fields=['historial_cambios'])


# =========================
# MODELOS PARA OPERACIONES DE SISTEMA
# =========================

class OperacionSistema(models.Model):
    """Modelo para trackear operaciones asíncronas del sistema"""
    TIPOS_OPERACION = [
        ('backup', 'Backup del Sistema'),
        ('export_config', 'Exportación de Configuraciones'),
        ('restart_services', 'Reinicio de Servicios'),
        ('preview_template', 'Vista Previa de Plantilla'),
        ('export_template', 'Exportación de Plantilla'),
        ('reset_config', 'Reset de Configuraciones'),
        ('test_providers', 'Prueba de Proveedores IA'),
        ('duplicate_segment', 'Duplicar Segmento'),
        ('duplicate_template', 'Duplicar Plantilla'),
    ]
    
    ESTADOS = [
        ('pending', 'Pendiente'),
        ('running', 'Ejecutando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=50, choices=TIPOS_OPERACION)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    # Estado y progreso
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pending')
    progreso = models.IntegerField(default=0, help_text="Progreso en porcentaje (0-100)")
    mensaje_estado = models.TextField(blank=True, help_text="Mensaje descriptivo del estado actual")
    
    # Datos de la operación
    parametros_entrada = models.JSONField(default=dict, help_text="Parámetros de entrada de la operación")
    resultado = models.JSONField(default=dict, blank=True, help_text="Resultado de la operación")
    logs = models.JSONField(default=list, help_text="Logs detallados de la operación")
    
    # Archivos generados
    archivo_resultado = models.FileField(upload_to='operaciones_sistema/', blank=True, null=True)
    url_descarga = models.URLField(blank=True, help_text="URL de descarga del resultado")
    
    # Metadatos
    task_id = models.CharField(max_length=255, blank=True, help_text="ID de la tarea Celery")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    tiempo_ejecucion = models.DurationField(null=True, blank=True)
    
    # Configuración
    expira_en = models.DateTimeField(null=True, blank=True, help_text="Fecha de expiración del resultado")
    notificar_usuario = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['usuario', '-fecha_inicio']),
            models.Index(fields=['tipo', 'estado']),
            models.Index(fields=['task_id']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo} ({self.get_estado_display()})"
    
    def agregar_log(self, nivel, mensaje, detalles=None):
        """Agrega una entrada de log a la operación"""
        entrada = {
            'timestamp': timezone.now().isoformat(),
            'nivel': nivel,
            'mensaje': mensaje,
            'detalles': detalles or {}
        }
        self.logs.append(entrada)
        self.save(update_fields=['logs'])
    
    def actualizar_progreso(self, progreso, mensaje=""):
        """Actualiza el progreso de la operación"""
        self.progreso = progreso
        if mensaje:
            self.mensaje_estado = mensaje
        self.save(update_fields=['progreso', 'mensaje_estado'])
    
    def marcar_completado(self, resultado=None):
        """Marca la operación como completada"""
        self.estado = 'completed'
        self.fecha_finalizacion = timezone.now()
        self.tiempo_ejecucion = self.fecha_finalizacion - self.fecha_inicio
        if resultado:
            self.resultado = resultado
        self.save()
    
    def marcar_fallido(self, error):
        """Marca la operación como fallida"""
        self.estado = 'failed'
        self.fecha_finalizacion = timezone.now()
        self.tiempo_ejecucion = self.fecha_finalizacion - self.fecha_inicio
        self.mensaje_estado = str(error)
        self.agregar_log('error', f"Operación fallida: {error}")
        self.save()


class ConfiguracionSistema(models.Model):
    """Modelo para almacenar configuraciones del sistema con versionado"""
    
    # Identificación
    clave = models.CharField(max_length=100, unique=True, help_text="Clave única de configuración")
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo")
    descripcion = models.TextField(blank=True)
    
    # Valor y metadatos
    valor = models.JSONField(help_text="Valor de la configuración")
    valor_por_defecto = models.JSONField(help_text="Valor por defecto")
    tipo_dato = models.CharField(max_length=50, default='string', choices=[
        ('string', 'Texto'),
        ('integer', 'Número entero'),
        ('float', 'Número decimal'),
        ('boolean', 'Verdadero/Falso'),
        ('json', 'JSON'),
        ('list', 'Lista'),
    ])
    
    # Validación
    validacion = models.JSONField(default=dict, blank=True, help_text="Reglas de validación")
    es_requerido = models.BooleanField(default=False)
    es_publico = models.BooleanField(default=False, help_text="Si es visible en APIs públicas")
    
    # Versionado
    version = models.IntegerField(default=1)
    historial_valores = models.JSONField(default=list, help_text="Historial de cambios de valor")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='configuraciones_creadas')
    usuario_modificacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='configuraciones_modificadas', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['clave']
        indexes = [
            models.Index(fields=['clave']),
            models.Index(fields=['es_publico']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.clave})"
    
    def actualizar_valor(self, nuevo_valor, usuario):
        """Actualiza el valor guardando el historial"""
        # Guardar valor anterior en historial
        entrada_historial = {
            'timestamp': timezone.now().isoformat(),
            'valor_anterior': self.valor,
            'valor_nuevo': nuevo_valor,
            'usuario': usuario.username,
            'version': self.version
        }
        self.historial_valores.append(entrada_historial)
        
        # Actualizar valor actual
        self.valor = nuevo_valor
        self.version += 1
        self.usuario_modificacion = usuario
        self.save()
    
    def restaurar_por_defecto(self, usuario):
        """Restaura el valor por defecto"""
        self.actualizar_valor(self.valor_por_defecto, usuario)


class LogOperacion(models.Model):
    """Logs detallados de operaciones del sistema"""
    
    NIVELES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    operacion = models.ForeignKey(OperacionSistema, on_delete=models.CASCADE, related_name='logs_detallados')
    timestamp = models.DateTimeField(auto_now_add=True)
    nivel = models.CharField(max_length=20, choices=NIVELES)
    mensaje = models.TextField()
    contexto = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['operacion', '-timestamp']),
            models.Index(fields=['nivel']),
        ]
    
    def __str__(self):
        return f"{self.operacion.titulo} - {self.nivel}: {self.mensaje[:50]}"