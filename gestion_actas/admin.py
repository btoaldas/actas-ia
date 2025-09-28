from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    EstadoGestionActa, 
    GestionActa, 
    ProcesoRevision, 
    RevisionIndividual,
    HistorialCambios,
    ConfiguracionExportacion
)


@admin.register(EstadoGestionActa)
class EstadoGestionActaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'orden', 'permite_edicion', 'requiere_revision', 'visible_portal', 'activo']
    list_filter = ['activo', 'permite_edicion', 'requiere_revision', 'visible_portal']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['orden', 'nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'color')
        }),
        ('Configuración', {
            'fields': ('orden', 'activo')
        }),
        ('Comportamiento', {
            'fields': ('permite_edicion', 'requiere_revision', 'visible_portal')
        }),
    )


class HistorialCambiosInline(admin.TabularInline):
    model = HistorialCambios
    extra = 0
    readonly_fields = ['fecha_cambio', 'usuario', 'tipo_cambio', 'descripcion', 'ip_address']
    can_delete = False
    
    def has_add_permission(self, request, obj):
        return False


@admin.register(GestionActa)
class GestionActaAdmin(admin.ModelAdmin):
    list_display = [
        # 'acta_generada',  # Comentado temporalmente
        'estado', 
        'usuario_editor', 
        'version', 
        'bloqueada_edicion', 
        'fecha_creacion',
        'fecha_ultima_edicion'
    ]
    list_filter = [
        'estado', 
        'bloqueada_edicion', 
        'fecha_creacion', 
        'fecha_ultima_edicion'
    ]
    search_fields = [
        # 'acta_generada__numero_acta', 
        # 'acta_generada__titulo',
        'usuario_editor__username',
        'observaciones'
    ]
    readonly_fields = [
        'fecha_creacion', 
        'fecha_ultima_edicion', 
        'version',
        'contenido_original_backup'
    ]
    raw_id_fields = ['usuario_editor']  # 'acta_generada' comentado temporalmente
    
    inlines = [HistorialCambiosInline]
    
    fieldsets = (
        ('Información del Acta', {
            'fields': ('estado',)  # 'acta_generada' comentado temporalmente
        }),
        ('Gestión', {
            'fields': ('usuario_editor', 'version', 'bloqueada_edicion')
        }),
        ('Contenido', {
            'fields': ('contenido_editado', 'contenido_original_backup'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion', 
                'fecha_ultima_edicion', 
                'fecha_enviada_revision', 
                'fecha_aprobacion_final', 
                'fecha_publicacion'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('observaciones', 'cambios_realizados'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'acta_generada', 
            'estado', 
            'usuario_editor'
        )


class RevisionIndividualInline(admin.TabularInline):
    model = RevisionIndividual
    extra = 0
    readonly_fields = ['fecha_asignacion', 'fecha_revision', 'tiempo_revision_minutos']
    fields = [
        'revisor', 
        'revisado', 
        'aprobado', 
        'comentarios', 
        'observaciones_tecnicas',
        'fecha_asignacion', 
        'fecha_revision'
    ]


@admin.register(ProcesoRevision)
class ProcesoRevisionAdmin(admin.ModelAdmin):
    list_display = [
        'gestion_acta',
        'iniciado_por',
        'fecha_inicio',
        'completado',
        'aprobado',
        'get_estado_revision',
        'get_total_revisores'
    ]
    list_filter = [
        'completado', 
        'aprobado', 
        'revision_paralela', 
        'requiere_unanimidad',
        'fecha_inicio'
    ]
    search_fields = [
        'gestion_acta__acta_generada__numero_acta',
        'iniciado_por__username',
        'observaciones'
    ]
    readonly_fields = [
        'fecha_inicio', 
        'fecha_completado',
        'get_estado_revision',
        'get_total_revisores',
        'get_aprobaciones',
        'get_rechazos'
    ]
    
    inlines = [RevisionIndividualInline]
    
    fieldsets = (
        ('Proceso', {
            'fields': ('gestion_acta', 'iniciado_por')
        }),
        ('Configuración', {
            'fields': ('revision_paralela', 'requiere_unanimidad', 'fecha_limite')
        }),
        ('Estado', {
            'fields': (
                'completado', 
                'aprobado', 
                'fecha_inicio', 
                'fecha_completado',
                'get_estado_revision',
                'get_total_revisores',
                'get_aprobaciones',
                'get_rechazos'
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    def get_estado_revision(self, obj):
        estado = obj.get_estado_revision()
        color_map = {
            'sin_revisores': 'gray',
            'en_proceso': 'orange',
            'aprobado': 'green',
            'rechazado': 'red'
        }
        color = color_map.get(estado, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            estado.replace('_', ' ').title()
        )
    get_estado_revision.short_description = 'Estado Actual'
    
    def get_total_revisores(self, obj):
        return obj.revisiones.count()
    get_total_revisores.short_description = 'Total Revisores'
    
    def get_aprobaciones(self, obj):
        return obj.revisiones.filter(aprobado=True).count()
    get_aprobaciones.short_description = 'Aprobaciones'
    
    def get_rechazos(self, obj):
        return obj.revisiones.filter(aprobado=False, revisado=True).count()
    get_rechazos.short_description = 'Rechazos'


@admin.register(RevisionIndividual)
class RevisionIndividualAdmin(admin.ModelAdmin):
    list_display = [
        'proceso_revision',
        'revisor',
        'revisado',
        'aprobado',
        'fecha_asignacion',
        'fecha_revision'
    ]
    list_filter = [
        'revisado', 
        'aprobado', 
        'fecha_asignacion', 
        'fecha_revision'
    ]
    search_fields = [
        'proceso_revision__gestion_acta__acta_generada__numero_acta',
        'revisor__username',
        'revisor__first_name',
        'revisor__last_name',
        'comentarios'
    ]
    readonly_fields = [
        'fecha_asignacion', 
        'fecha_revision', 
        'tiempo_revision_minutos'
    ]
    
    fieldsets = (
        ('Revisión', {
            'fields': ('proceso_revision', 'revisor')
        }),
        ('Estado', {
            'fields': ('revisado', 'aprobado', 'fecha_asignacion', 'fecha_revision')
        }),
        ('Comentarios', {
            'fields': ('comentarios', 'observaciones_tecnicas'),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': ('tiempo_revision_minutos',),
            'classes': ('collapse',)
        }),
    )


@admin.register(HistorialCambios)
class HistorialCambiosAdmin(admin.ModelAdmin):
    list_display = [
        'gestion_acta',
        'usuario',
        'tipo_cambio',
        'fecha_cambio',
        'ip_address'
    ]
    list_filter = [
        'tipo_cambio',
        'fecha_cambio',
        'usuario'
    ]
    search_fields = [
        'gestion_acta__acta_generada__numero_acta',
        'usuario__username',
        'descripcion'
    ]
    readonly_fields = [
        'fecha_cambio',
        'gestion_acta',
        'usuario',
        'tipo_cambio',
        'descripcion',
        'datos_adicionales',
        'ip_address',
        'user_agent'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(ConfiguracionExportacion)
class ConfiguracionExportacionAdmin(admin.ModelAdmin):
    list_display = [
        'activa',
        'pdf_template',
        'pdf_header_enabled',
        'word_styles_enabled',
        'fecha_creacion',
        'fecha_actualizacion'
    ]
    list_filter = [
        'activa',
        'pdf_template',
        'pdf_header_enabled',
        'pdf_footer_enabled',
        'word_styles_enabled',
        'incluir_metadatos'
    ]
    
    fieldsets = (
        ('Estado', {
            'fields': ('activa',)
        }),
        ('Configuración PDF', {
            'fields': (
                'pdf_header_enabled',
                'pdf_footer_enabled',
                'pdf_watermark',
                'pdf_template'
            )
        }),
        ('Configuración Word', {
            'fields': ('word_template_path', 'word_styles_enabled')
        }),
        ('Configuración TXT', {
            'fields': ('txt_encoding', 'txt_line_endings')
        }),
        ('Metadatos', {
            'fields': ('incluir_metadatos', 'incluir_firma_digital')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def save_model(self, request, obj, form, change):
        # Solo permitir una configuración activa
        if obj.activa:
            ConfiguracionExportacion.objects.filter(activa=True).update(activa=False)
        super().save_model(request, obj, form, change)
