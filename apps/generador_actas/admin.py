"""
Configuración básica del Django Admin para el módulo Generador de Actas
Versión simplificada sin campos inexistentes
"""

from django.contrib import admin
from .models import (
    ProveedorIA, SegmentoPlantilla, PlantillaActa, 
    ConfiguracionSegmento, ActaGenerada
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
    """Administración básica de Segmentos de Plantilla"""
    list_display = ['nombre', 'categoria', 'tipo', 'reutilizable', 'fecha_creacion']
    list_filter = ['categoria', 'tipo', 'reutilizable', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']


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