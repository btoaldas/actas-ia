"""
Configuración básica del Django Admin para el módulo Generador de Actas
Versión simplificada sin campos inexistentes
"""

from django.contrib import admin
from .models import (
    ProveedorIA, SegmentoPlantilla, PlantillaActa, 
    ConfiguracionSegmento, ActaGenerada, EjecucionPlantilla, ResultadoSegmento
)


@admin.register(ProveedorIA)
class ProveedorIAAdmin(admin.ModelAdmin):
    """Administración básica de Proveedores de IA"""
    list_display = ['nombre', 'tipo', 'activo', 'fecha_creacion']
    list_filter = ['tipo', 'activo', 'fecha_creacion']
    search_fields = ['nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    list_editable = ['activo']


@admin.register(SegmentoPlantilla)
class SegmentoPlantillaAdmin(admin.ModelAdmin):
    """Administración completa de Segmentos de Plantilla"""
    list_display = [
        'codigo', 'nombre', 'categoria', 'tipo', 'proveedor_ia', 
        'total_usos', 'activo', 'reutilizable', 'fecha_creacion'
    ]
    list_filter = [
        'categoria', 'tipo', 'activo', 'reutilizable', 'obligatorio',
        'proveedor_ia', 'fecha_creacion'
    ]
    search_fields = ['codigo', 'nombre', 'descripcion']
    readonly_fields = [
        'fecha_creacion', 'fecha_actualizacion', 'total_usos',
        'ultima_prueba', 'ultimo_resultado_prueba', 'tiempo_promedio_procesamiento'
    ]
    list_editable = ['activo', 'reutilizable']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('codigo', 'nombre', 'descripcion', 'categoria', 'tipo')
        }),
        ('Configuración IA', {
            'fields': ('proveedor_ia', 'prompt_ia', 'estructura_json'),
            'classes': ('collapse',)
        }),
        ('Configuración JSON', {
            'fields': ('componentes', 'parametros_entrada', 'variables_personalizadas'),
            'classes': ('collapse',)
        }),
        ('Comportamiento', {
            'fields': ('orden_defecto', 'reutilizable', 'obligatorio', 'activo')
        }),
        ('Métricas de Uso', {
            'fields': (
                'total_usos', 'ultima_prueba', 'ultimo_resultado_prueba',
                'tiempo_promedio_procesamiento'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('usuario_creacion', 'fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['marcar_activo', 'marcar_inactivo', 'resetear_metricas', 'probar_segmento']
    
    def marcar_activo(self, request, queryset):
        """Activar segmentos seleccionados"""
        count = queryset.update(activo=True)
        self.message_user(request, f"{count} segmentos marcados como activos")
    marcar_activo.short_description = "Marcar como activo"
    
    def marcar_inactivo(self, request, queryset):
        """Desactivar segmentos seleccionados"""
        count = queryset.update(activo=False)
        self.message_user(request, f"{count} segmentos marcados como inactivos")
    marcar_inactivo.short_description = "Marcar como inactivo"
    
    def resetear_metricas(self, request, queryset):
        """Resetear métricas de uso"""
        count = queryset.update(
            total_usos=0,
            tiempo_promedio_procesamiento=0.0,
            ultima_prueba=None,
            ultimo_resultado_prueba=''
        )
        self.message_user(request, f"Métricas reseteadas para {count} segmentos")
    resetear_metricas.short_description = "Resetear métricas de uso"
    
    def probar_segmento(self, request, queryset):
        """Redirigir a página de pruebas para segmentos seleccionados"""
        if queryset.count() == 1:
            segmento = queryset.first()
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(reverse('generador_actas:probar_segmento') + f'?segmento={segmento.pk}')
        else:
            self.message_user(request, "Selecciona solo un segmento para probar", level='warning')
    probar_segmento.short_description = "Probar segmento seleccionado"
    
    def save_model(self, request, obj, form, change):
        """Guardar con usuario de creación"""
        if not change:
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)


@admin.register(PlantillaActa)
class PlantillaActaAdmin(admin.ModelAdmin):
    """Administración básica de Plantillas de Acta"""
    list_display = ['nombre', 'tipo_acta', 'activa', 'fecha_creacion']
    list_filter = ['tipo_acta', 'activa', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    list_editable = ['activa']


@admin.register(ConfiguracionSegmento)
class ConfiguracionSegmentoAdmin(admin.ModelAdmin):
    """Administración básica de Configuración de Segmentos"""
    list_display = ['plantilla', 'segmento', 'orden', 'obligatorio']
    list_filter = ['obligatorio']
    list_editable = ['orden', 'obligatorio']


@admin.register(ActaGenerada)
class ActaGeneradaAdmin(admin.ModelAdmin):
    """Administración básica de Actas Generadas"""
    list_display = ['numero_acta', 'titulo', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['numero_acta', 'titulo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_creacion'


@admin.register(EjecucionPlantilla)
class EjecucionPlantillaAdmin(admin.ModelAdmin):
    """Administración de Ejecuciones de Plantilla"""
    list_display = ['nombre', 'plantilla', 'estado']
    list_filter = ['estado', 'plantilla']
    search_fields = ['nombre']


@admin.register(ResultadoSegmento)
class ResultadoSegmentoAdmin(admin.ModelAdmin):
    """Administración de Resultados de Segmento"""
    list_display = ['ejecucion', 'orden_procesamiento', 'estado']
    list_filter = ['estado']
    search_fields = ['ejecucion__nombre']