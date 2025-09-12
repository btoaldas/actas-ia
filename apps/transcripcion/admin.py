from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    ConfiguracionTranscripcion, Transcripcion, 
    HistorialEdicion, ConfiguracionHablante
)


@admin.register(ConfiguracionTranscripcion)
class ConfiguracionTranscripcionAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'activa', 'modelo_whisper', 'idioma_principal', 
        'min_hablantes', 'max_hablantes', 'fecha_actualizacion'
    ]
    list_filter = ['activa', 'modelo_whisper', 'idioma_principal', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'activa', 'usuario_creacion')
        }),
        ('Configuración Whisper', {
            'fields': ('modelo_whisper', 'idioma_principal', 'temperatura'),
            'description': 'Configuración para el motor de transcripción Whisper'
        }),
        ('Configuración Diarización', {
            'fields': ('modelo_diarizacion', 'min_hablantes', 'max_hablantes'),
            'description': 'Configuración para la diarización con pyannote'
        }),
        ('Procesamiento', {
            'fields': ('segmentacion_minima', 'umbral_confianza'),
            'description': 'Parámetros de procesamiento y calidad'
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        
        # Si se marca como activa, desactivar las demás
        if obj.activa:
            ConfiguracionTranscripcion.objects.filter(activa=True).update(activa=False)
        
        super().save_model(request, obj, form, change)


class ConfiguracionHablanteInline(admin.TabularInline):
    model = ConfiguracionHablante
    extra = 0
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fields = [
        'speaker_id', 'nombre_real', 'cargo', 'organizacion', 
        'color_chat', 'confirmado_por_usuario'
    ]


class HistorialEdicionInline(admin.TabularInline):
    model = HistorialEdicion
    extra = 0
    readonly_fields = ['fecha_edicion', 'usuario', 'tipo_edicion', 'version']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Transcripcion)
class TranscripcionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_nombre_archivo', 'estado', 'numero_hablantes',
        'numero_segmentos', 'progreso_porcentaje', 'editado_manualmente',
        'fecha_creacion', 'acciones_admin'
    ]
    list_filter = [
        'estado', 'editado_manualmente', 'fecha_creacion',
        'configuracion_utilizada__modelo_whisper'
    ]
    search_fields = [
        'procesamiento_audio__nombre_archivo',
        'texto_completo',
        'procesamiento_audio__tipo_reunion__nombre'
    ]
    readonly_fields = [
        'id_transcripcion', 'fecha_creacion', 'fecha_actualizacion',
        'tiempo_inicio_proceso', 'tiempo_fin_proceso', 'duracion_proceso',
        'task_id_celery', 'progreso_porcentaje'
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'id_transcripcion', 'procesamiento_audio', 'estado',
                'configuracion_utilizada', 'usuario_creacion'
            )
        }),
        ('Resultados de Transcripción', {
            'fields': ('texto_completo', 'mostrar_transcripcion_json'),
            'classes': ('collapse',)
        }),
        ('Resultados de Diarización', {
            'fields': ('mostrar_diarizacion_json', 'hablantes_detectados', 'hablantes_identificados'),
            'classes': ('collapse',)
        }),
        ('Conversación Estructurada', {
            'fields': ('mostrar_conversacion_json',),
            'classes': ('collapse',)
        }),
        ('Estadísticas', {
            'fields': (
                'numero_hablantes', 'numero_segmentos', 'palabras_totales',
                'duracion_total', 'confianza_promedio', 'mostrar_estadisticas_json'
            ),
            'classes': ('collapse',)
        }),
        ('Análisis', {
            'fields': ('palabras_clave', 'temas_detectados'),
            'classes': ('collapse',)
        }),
        ('Control de Procesamiento', {
            'fields': (
                'tiempo_inicio_proceso', 'tiempo_fin_proceso', 'duracion_proceso',
                'progreso_porcentaje', 'task_id_celery', 'mensaje_error'
            ),
            'classes': ('collapse',)
        }),
        ('Versionado y Edición', {
            'fields': (
                'version_actual', 'editado_manualmente', 'fecha_ultima_edicion',
                'usuario_ultima_edicion'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ConfiguracionHablanteInline, HistorialEdicionInline]
    
    def get_nombre_archivo(self, obj):
        return obj.procesamiento_audio.nombre_archivo
    get_nombre_archivo.short_description = 'Archivo de Audio'
    get_nombre_archivo.admin_order_field = 'procesamiento_audio__nombre_archivo'
    
    def acciones_admin(self, obj):
        if obj.pk:
            detalle_url = reverse('transcripcion:detalle', args=[obj.pk])
            html = f'<a href="{detalle_url}" class="button" target="_blank">Ver Detalle</a>'
            
            if obj.estado == 'error':
                reiniciar_url = reverse('admin:transcripcion_transcripcion_actions')
                html += f' <a href="{reiniciar_url}?transcripcion_id={obj.pk}&action=reiniciar" class="button">Reiniciar</a>'
            
            return format_html(html)
        return '-'
    acciones_admin.short_description = 'Acciones'
    
    def mostrar_transcripcion_json(self, obj):
        if obj.transcripcion_json:
            json_str = json.dumps(obj.transcripcion_json, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', json_str)
        return 'No disponible'
    mostrar_transcripcion_json.short_description = 'JSON Transcripción'
    
    def mostrar_diarizacion_json(self, obj):
        if obj.diarizacion_json:
            json_str = json.dumps(obj.diarizacion_json, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', json_str)
        return 'No disponible'
    mostrar_diarizacion_json.short_description = 'JSON Diarización'
    
    def mostrar_conversacion_json(self, obj):
        if obj.conversacion_json:
            # Mostrar solo primeros 3 segmentos para no sobrecargar
            preview = obj.conversacion_json[:3]
            json_str = json.dumps(preview, indent=2, ensure_ascii=False)
            total = len(obj.conversacion_json)
            return format_html(
                '<pre style="max-height: 300px; overflow-y: auto;">{}</pre><p><strong>Mostrando 3 de {} segmentos</strong></p>',
                json_str, total
            )
        return 'No disponible'
    mostrar_conversacion_json.short_description = 'JSON Conversación (Preview)'
    
    def mostrar_estadisticas_json(self, obj):
        if obj.estadisticas_json:
            json_str = json.dumps(obj.estadisticas_json, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', json_str)
        return 'No disponible'
    mostrar_estadisticas_json.short_description = 'JSON Estadísticas'
    
    def duracion_proceso(self, obj):
        if obj.tiempo_inicio_proceso and obj.tiempo_fin_proceso:
            duracion = obj.tiempo_fin_proceso - obj.tiempo_inicio_proceso
            return f"{duracion.total_seconds():.2f} segundos"
        return 'N/A'
    duracion_proceso.short_description = 'Duración Proceso'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(HistorialEdicion)
class HistorialEdicionAdmin(admin.ModelAdmin):
    list_display = [
        'transcripcion', 'version', 'tipo_edicion', 'usuario',
        'fecha_edicion', 'comentario_corto'
    ]
    list_filter = ['tipo_edicion', 'fecha_edicion', 'usuario']
    search_fields = [
        'transcripcion__procesamiento_audio__nombre_archivo',
        'comentario', 'usuario__username'
    ]
    readonly_fields = ['fecha_edicion']
    
    fieldsets = (
        ('Información de Edición', {
            'fields': ('transcripcion', 'version', 'tipo_edicion', 'segmento_id')
        }),
        ('Cambios Realizados', {
            'fields': ('mostrar_valor_anterior', 'mostrar_valor_nuevo', 'comentario')
        }),
        ('Metadatos', {
            'fields': ('usuario', 'fecha_edicion', 'ip_address'),
            'classes': ('collapse',)
        })
    )
    
    def comentario_corto(self, obj):
        if obj.comentario:
            return obj.comentario[:50] + '...' if len(obj.comentario) > 50 else obj.comentario
        return '-'
    comentario_corto.short_description = 'Comentario'
    
    def mostrar_valor_anterior(self, obj):
        if obj.valor_anterior:
            json_str = json.dumps(obj.valor_anterior, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', json_str)
        return 'No disponible'
    mostrar_valor_anterior.short_description = 'Valor Anterior'
    
    def mostrar_valor_nuevo(self, obj):
        if obj.valor_nuevo:
            json_str = json.dumps(obj.valor_nuevo, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', json_str)
        return 'No disponible'
    mostrar_valor_nuevo.short_description = 'Valor Nuevo'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ConfiguracionHablante)
class ConfiguracionHablanteAdmin(admin.ModelAdmin):
    list_display = [
        'transcripcion', 'speaker_id', 'nombre_real', 'cargo',
        'confirmado_por_usuario', 'numero_intervenciones', 'tiempo_total_hablando'
    ]
    list_filter = ['confirmado_por_usuario', 'fecha_creacion']
    search_fields = [
        'nombre_real', 'cargo', 'organizacion',
        'transcripcion__procesamiento_audio__nombre_archivo'
    ]
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Identificación', {
            'fields': ('transcripcion', 'speaker_id', 'nombre_real')
        }),
        ('Información Personal', {
            'fields': ('cargo', 'organizacion')
        }),
        ('Configuración Visual', {
            'fields': ('color_chat', 'avatar_url')
        }),
        ('Estadísticas', {
            'fields': (
                'tiempo_total_hablando', 'numero_intervenciones',
                'palabras_promedio_por_intervencion'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('confirmado_por_usuario', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
