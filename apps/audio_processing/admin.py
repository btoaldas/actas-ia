from django.contrib import admin
from .models import TipoReunion, ProcesamientoAudio, LogProcesamiento


@admin.register(TipoReunion)
class TipoReunionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'created_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['activo']


class LogProcesamientoInline(admin.TabularInline):
    model = LogProcesamiento
    extra = 0
    readonly_fields = ['timestamp', 'nivel', 'mensaje']


@admin.register(ProcesamientoAudio)
class ProcesamientoAudioAdmin(admin.ModelAdmin):
    list_display = [
        'titulo', 
        'tipo_reunion', 
        'estado', 
        'progreso',
        'usuario',
        'created_at',
        'duracion_formateada'
    ]
    list_filter = [
        'estado', 
        'tipo_reunion', 
        'created_at',
        'usuario'
    ]
    search_fields = ['titulo', 'descripcion', 'usuario__username']
    readonly_fields = [
        'duracion_formateada', 
        'created_at', 
        'fecha_procesamiento',
        'fecha_completado'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('titulo', 'tipo_reunion', 'descripcion', 'usuario')
        }),
        ('Archivo de Audio', {
            'fields': ('archivo_audio',)
        }),
        ('Metadatos', {
            'fields': (
                'duracion', 'duracion_formateada', 'formato', 
                'tamano_mb'
            )
        }),
        ('Estado y Progreso', {
            'fields': (
                'estado', 'progreso', 'mensaje_estado',
                'fecha_procesamiento', 'fecha_completado'
            )
        }),
        ('Configuración', {
            'fields': ('configuracion',),
            'classes': ('collapse',)
        }),
        ('Resultados', {
            'fields': ('resultado',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [LogProcesamientoInline]


@admin.register(LogProcesamiento)
class LogProcesamientoAdmin(admin.ModelAdmin):
    list_display = ['procesamiento', 'nivel', 'mensaje', 'timestamp']
    list_filter = ['nivel', 'timestamp']
    search_fields = ['procesamiento__titulo', 'mensaje']
    readonly_fields = ['timestamp']
