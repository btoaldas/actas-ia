from django.contrib import admin
from .models import (
    TipoSesion, EstadoActa, ActaMunicipal, 
    VisualizacionActa, DescargaActa, Product,
    IndicadorTransparencia, MetricaTransparencia,
    EstadisticaMunicipal, ProyectoMunicipal,
    EventoMunicipal, DocumentoEvento, AsistenciaEvento  # InvitacionExterna TEMPORALMENTE COMENTADO
)

# Register your models here.

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'info']
    search_fields = ['name', 'info']

@admin.register(TipoSesion)
class TipoSesionAdmin(admin.ModelAdmin):
    list_display = ['get_nombre_display', 'color', 'icono', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'nombre']
    search_fields = ['descripcion']
    list_editable = ['activo']
    
    def get_nombre_display(self, obj):
        return obj.get_nombre_display()
    get_nombre_display.short_description = 'Tipo de Sesión'

@admin.register(EstadoActa)
class EstadoActaAdmin(admin.ModelAdmin):
    list_display = ['get_nombre_display', 'color', 'orden', 'activo']
    list_filter = ['activo', 'nombre']
    list_editable = ['orden', 'activo']
    ordering = ['orden']
    
    def get_nombre_display(self, obj):
        return obj.get_nombre_display()
    get_nombre_display.short_description = 'Estado'

@admin.register(ActaMunicipal)
class ActaMunicipalAdmin(admin.ModelAdmin):
    list_display = [
        'numero_acta', 'titulo', 'tipo_sesion', 'estado', 
        'fecha_sesion', 'acceso', 'transcripcion_ia', 'activo'
    ]
    list_filter = [
        'tipo_sesion', 'estado', 'acceso', 'transcripcion_ia', 
        'activo', 'fecha_sesion', 'fecha_creacion'
    ]
    search_fields = [
        'numero_acta', 'titulo', 'resumen', 'contenido', 
        'presidente', 'palabras_clave'
    ]
    list_editable = ['activo']
    date_hierarchy = 'fecha_sesion'
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'numero_acta', 'titulo', 'tipo_sesion', 'estado',
                'numero_sesion', 'fecha_sesion', 'acceso', 'prioridad'
            )
        }),
        ('Contenido', {
            'fields': ('resumen', 'contenido', 'orden_del_dia', 'acuerdos')
        }),
        ('Participantes', {
            'fields': ('secretario', 'presidente', 'asistentes', 'ausentes')
        }),
        ('Archivos', {
            'fields': ('archivo_pdf', 'imagen_preview')
        }),
        ('Metadatos IA', {
            'fields': ('transcripcion_ia', 'precision_ia', 'tiempo_procesamiento'),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('palabras_clave', 'observaciones', 'activo'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_publicacion',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo objeto
            if not obj.secretario_id:
                obj.secretario = request.user
        super().save_model(request, obj, form, change)

@admin.register(VisualizacionActa)
class VisualizacionActaAdmin(admin.ModelAdmin):
    list_display = [
        'acta', 'usuario', 'ip_address', 'fecha_visualizacion'
    ]
    list_filter = ['fecha_visualizacion', 'acta__tipo_sesion']
    search_fields = ['acta__numero_acta', 'acta__titulo', 'usuario__username', 'ip_address']
    readonly_fields = ['acta', 'usuario', 'ip_address', 'user_agent', 'fecha_visualizacion']
    date_hierarchy = 'fecha_visualizacion'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(DescargaActa)
class DescargaActaAdmin(admin.ModelAdmin):
    list_display = [
        'acta', 'usuario', 'ip_address', 'fecha_descarga'
    ]
    list_filter = ['fecha_descarga', 'acta__tipo_sesion']
    search_fields = ['acta__numero_acta', 'acta__titulo', 'usuario__username', 'ip_address']
    readonly_fields = ['acta', 'usuario', 'ip_address', 'fecha_descarga']
    date_hierarchy = 'fecha_descarga'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

# ========================================================================
# ADMIN DE TRANSPARENCIA MUNICIPAL
# ========================================================================

@admin.register(IndicadorTransparencia)
class IndicadorTransparenciaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'tipo', 'color', 'orden', 'activo']
    list_filter = ['categoria', 'tipo', 'activo']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['orden', 'activo']
    ordering = ['categoria', 'orden']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'categoria', 'tipo')
        }),
        ('Presentación', {
            'fields': ('icono', 'color', 'orden', 'activo')
        }),
    )

@admin.register(MetricaTransparencia)
class MetricaTransparenciaAdmin(admin.ModelAdmin):
    list_display = ['indicador', 'valor', 'fecha', 'mes', 'año']
    list_filter = ['indicador__categoria', 'año', 'mes', 'fecha']
    search_fields = ['indicador__nombre', 'observaciones']
    date_hierarchy = 'fecha'
    ordering = ['-fecha']
    
    fieldsets = (
        ('Métrica', {
            'fields': ('indicador', 'valor', 'fecha')
        }),
        ('Información Adicional', {
            'fields': ('mes', 'año', 'observaciones'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if obj.fecha:
            obj.mes = obj.fecha.month
            obj.año = obj.fecha.year
        super().save_model(request, obj, form, change)

@admin.register(EstadisticaMunicipal)
class EstadisticaMunicipalAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'valor', 'unidad', 'fecha', 'fuente']
    list_filter = ['categoria', 'fecha', 'unidad']
    search_fields = ['nombre', 'descripcion', 'fuente']
    date_hierarchy = 'fecha'
    ordering = ['-fecha', 'categoria']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'categoria', 'valor', 'unidad', 'fecha')
        }),
        ('Fuente y Descripción', {
            'fields': ('fuente', 'descripcion')
        }),
        ('Presentación', {
            'fields': ('icono', 'color'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProyectoMunicipal)
class ProyectoMunicipalAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'categoria', 'estado', 'porcentaje_avance', 
        'presupuesto_total', 'fecha_inicio', 'responsable'
    ]
    list_filter = ['categoria', 'estado', 'fecha_inicio']
    search_fields = ['nombre', 'descripcion', 'responsable', 'contratista', 'ubicacion']
    date_hierarchy = 'fecha_inicio'
    ordering = ['-fecha_inicio']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'categoria', 'estado')
        }),
        ('Presupuesto', {
            'fields': ('presupuesto_total', 'presupuesto_ejecutado')
        }),
        ('Cronograma', {
            'fields': ('fecha_inicio', 'fecha_fin_estimada', 'fecha_fin_real', 'porcentaje_avance')
        }),
        ('Responsables y Ubicación', {
            'fields': ('responsable', 'contratista', 'ubicacion')
        }),
        ('Beneficiarios', {
            'fields': ('beneficiarios_estimados',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['porcentaje_presupuesto_ejecutado']
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.estado == 'finalizado':
            readonly.extend(['presupuesto_total', 'porcentaje_avance'])
        return readonly


# ========================================================================
# CONFIGURACIÓN ADMIN PARA EVENTOS MUNICIPALES
# ========================================================================

class DocumentoEventoInline(admin.TabularInline):
    model = DocumentoEvento
    extra = 1
    fields = ('nombre', 'tipo_documento', 'archivo', 'es_publico', 'orden')


# TEMPORALMENTE COMENTADO - InvitacionExternaInline
# class InvitacionExternaInline(admin.TabularInline):
#     model = InvitacionExterna
#     extra = 1
#     fields = ('email', 'nombre', 'estado')
#     readonly_fields = ('token', 'fecha_envio', 'fecha_respuesta')


class AsistenciaEventoInline(admin.TabularInline):
    model = AsistenciaEvento
    extra = 0
    fields = ('usuario', 'tipo', 'fecha_confirmacion')
    readonly_fields = ('fecha_confirmacion',)


@admin.register(EventoMunicipal)
class EventoMunicipalAdmin(admin.ModelAdmin):
    list_display = (
        'titulo', 'tipo', 'fecha_inicio', 'ubicacion', 
        'estado', 'visibilidad', 'organizador', 'total_asistentes_confirmados'
    )
    list_filter = ('tipo', 'estado', 'visibilidad', 'fecha_inicio', 'activo')
    search_fields = ('titulo', 'descripcion', 'ubicacion', 'organizador__username')
    date_hierarchy = 'fecha_inicio'
    ordering = ['-fecha_inicio']
    
    filter_horizontal = ('asistentes_invitados', 'asistentes_confirmados')
    inlines = [DocumentoEventoInline, AsistenciaEventoInline]  # InvitacionExternaInline TEMPORALMENTE COMENTADO
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'descripcion', 'tipo', 'organizador')
        }),
        ('Fechas y Horarios', {
            'fields': ('fecha_inicio', 'fecha_fin')
        }),
        ('Ubicación', {
            'fields': ('ubicacion', 'direccion')
        }),
        ('Configuración', {
            'fields': ('estado', 'visibilidad', 'capacidad_maxima')
        }),
        ('Participantes', {
            'fields': ('asistentes_invitados', 'asistentes_confirmados'),
            'classes': ('collapse',)
        }),
        ('Multimedia', {
            'fields': ('imagen_evento',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('activo', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'total_asistentes_confirmados')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(organizador=request.user)
        return qs
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.organizador = request.user
        super().save_model(request, obj, form, change)


@admin.register(DocumentoEvento)
class DocumentoEventoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'evento', 'fecha_subida', 'es_publico', 'get_tamaño_archivo')
    list_filter = ('es_publico', 'fecha_subida', 'evento__tipo')
    search_fields = ('nombre', 'descripcion', 'evento__titulo')
    date_hierarchy = 'fecha_subida'
    ordering = ['-fecha_subida']
    
    fieldsets = (
        ('Información del Documento', {
            'fields': ('nombre', 'descripcion', 'archivo', 'es_publico')
        }),
        ('Evento Relacionado', {
            'fields': ('evento',)
        }),
        ('Metadatos', {
            'fields': ('subido_por', 'fecha_subida'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('subido_por', 'fecha_subida')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.subido_por = request.user
        super().save_model(request, obj, form, change)
    
    def get_tamaño_archivo(self, obj):
        if obj.archivo and hasattr(obj.archivo, 'size'):
            size = obj.archivo.size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "N/A"
    get_tamaño_archivo.short_description = "Tamaño"


@admin.register(AsistenciaEvento)
class AsistenciaEventoAdmin(admin.ModelAdmin):
    list_display = ('evento', 'usuario', 'tipo', 'fecha_confirmacion')
    list_filter = ('tipo', 'fecha_confirmacion', 'evento__tipo')
    search_fields = ('evento__titulo', 'usuario__username', 'usuario__first_name', 'usuario__last_name')
    date_hierarchy = 'fecha_confirmacion'
    ordering = ['-fecha_confirmacion']
    
    fieldsets = (
        ('Asistencia', {
            'fields': ('evento', 'usuario', 'tipo')
        }),
        ('Información Adicional', {
            'fields': ('comentarios', 'fecha_confirmacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_confirmacion',)
