"""
Serializers para API REST del módulo generador de actas
Incluye serializers para plantillas, ejecuciones y resultados
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    PlantillaActa, SegmentoPlantilla, EjecucionPlantilla, 
    ResultadoSegmento, ActaBorrador, ProveedorIA
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer básico para usuarios"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ProveedorIASerializer(serializers.ModelSerializer):
    """Serializer para proveedores de IA"""
    
    class Meta:
        model = ProveedorIA
        fields = [
            'id', 'nombre', 'tipo', 'modelo', 'activo',
            'temperatura', 'max_tokens', 'costo_por_1k_tokens'
        ]
        read_only_fields = ['id']


class SegmentoPlantillaSerializer(serializers.ModelSerializer):
    """Serializer para segmentos de plantilla"""
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    
    class Meta:
        model = SegmentoPlantilla
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'categoria', 'categoria_display',
            'tipo', 'tipo_display', 'contenido_estatico', 'prompt_dinamico',
            'variables_requeridas', 'activo', 'fecha_creacion'
        ]
        read_only_fields = ['id', 'fecha_creacion', 'categoria_display', 'tipo_display']


class PlantillaActaSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de acta"""
    usuario_creacion = UserSerializer(read_only=True)
    proveedor_ia_defecto = ProveedorIASerializer(read_only=True)
    tipo_acta_display = serializers.CharField(source='get_tipo_acta_display', read_only=True)
    segmentos_ordenados = serializers.SerializerMethodField()
    total_segmentos = serializers.ReadOnlyField()
    segmentos_dinamicos = serializers.ReadOnlyField()
    
    class Meta:
        model = PlantillaActa
        fields = [
            'id', 'codigo', 'nombre', 'descripcion', 'tipo_acta', 'tipo_acta_display',
            'prompt_global', 'proveedor_ia_defecto', 'activa', 'version',
            'usuario_creacion', 'fecha_creacion', 'fecha_actualizacion',
            'segmentos_ordenados', 'total_segmentos', 'segmentos_dinamicos'
        ]
        read_only_fields = [
            'id', 'fecha_creacion', 'fecha_actualizacion', 'tipo_acta_display',
            'segmentos_ordenados', 'total_segmentos', 'segmentos_dinamicos'
        ]
    
    def get_segmentos_ordenados(self, obj):
        """Obtiene los segmentos ordenados con su configuración"""
        configuraciones = obj.segmentos_ordenados
        return [
            {
                'segmento': SegmentoPlantillaSerializer(config.segmento).data,
                'orden': config.orden,
                'obligatorio': config.obligatorio,
                'variables_personalizadas': config.variables_personalizadas
            }
            for config in configuraciones
        ]


class PlantillaActaCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para crear/actualizar plantillas"""
    
    class Meta:
        model = PlantillaActa
        fields = [
            'codigo', 'nombre', 'descripcion', 'tipo_acta',
            'prompt_global', 'proveedor_ia_defecto', 'activa', 'version'
        ]
    
    def validate_codigo(self, value):
        """Valida que el código sea único"""
        if self.instance and self.instance.codigo == value:
            return value
        
        if PlantillaActa.objects.filter(codigo=value).exists():
            raise serializers.ValidationError("Ya existe una plantilla con este código")
        return value


class ResultadoSegmentoSerializer(serializers.ModelSerializer):
    """Serializer para resultados de segmento"""
    segmento = SegmentoPlantillaSerializer(read_only=True)
    proveedor_ia_usado = ProveedorIASerializer(read_only=True)
    usuario_ultima_edicion = UserSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    resultado_final = serializers.ReadOnlyField()
    fue_editado = serializers.ReadOnlyField()
    
    class Meta:
        model = ResultadoSegmento
        fields = [
            'id', 'segmento', 'orden_procesamiento', 'proveedor_ia_usado',
            'estado', 'estado_display', 'resultado_crudo', 'resultado_procesado',
            'resultado_editado', 'resultado_final', 'fue_editado',
            'tiempo_procesamiento', 'tiempo_total_ms', 'tokens_utilizados',
            'costo_estimado', 'version_resultado', 'usuario_ultima_edicion',
            'fecha_ultima_edicion', 'notas_edicion'
        ]
        read_only_fields = [
            'id', 'segmento', 'proveedor_ia_usado', 'resultado_crudo',
            'resultado_procesado', 'tiempo_procesamiento', 'tiempo_total_ms',
            'tokens_utilizados', 'costo_estimado', 'version_resultado',
            'usuario_ultima_edicion', 'fecha_ultima_edicion', 'estado_display',
            'resultado_final', 'fue_editado'
        ]


class EjecucionPlantillaSerializer(serializers.ModelSerializer):
    """Serializer para ejecuciones de plantilla"""
    plantilla = PlantillaActaSerializer(read_only=True)
    usuario = UserSerializer(read_only=True)
    proveedor_ia_global = ProveedorIASerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    duracion_formateada = serializers.ReadOnlyField()
    porcentaje_progreso = serializers.ReadOnlyField()
    resultados = ResultadoSegmentoSerializer(many=True, read_only=True)
    
    class Meta:
        model = EjecucionPlantilla
        fields = [
            'id', 'nombre', 'plantilla', 'usuario', 'transcripcion',
            'proveedor_ia_global', 'variables_contexto', 'estado', 'estado_display',
            'progreso_actual', 'progreso_total', 'porcentaje_progreso',
            'tiempo_inicio', 'tiempo_fin', 'tiempo_total_segundos',
            'duracion_formateada', 'resultados_parciales', 'errores',
            'resultado_unificacion', 'resultados'
        ]
        read_only_fields = [
            'id', 'plantilla', 'usuario', 'estado', 'progreso_actual', 'progreso_total',
            'tiempo_inicio', 'tiempo_fin', 'tiempo_total_segundos',
            'resultados_parciales', 'errores', 'resultado_unificacion',
            'estado_display', 'duracion_formateada', 'porcentaje_progreso', 'resultados'
        ]


class EjecucionPlantillaCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevas ejecuciones"""
    
    class Meta:
        model = EjecucionPlantilla
        fields = ['nombre', 'transcripcion', 'proveedor_ia_global', 'variables_contexto']
    
    def validate_variables_contexto(self, value):
        """Valida que las variables de contexto sean un diccionario válido"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Las variables de contexto deben ser un objeto JSON")
        return value


class ActaBorradorSerializer(serializers.ModelSerializer):
    """Serializer para actas borrador"""
    ejecucion = EjecucionPlantillaSerializer(read_only=True)
    usuario_creacion = UserSerializer(read_only=True)
    usuario_ultima_modificacion = UserSerializer(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    tiempo_generacion_formateado = serializers.ReadOnlyField()
    
    class Meta:
        model = ActaBorrador
        fields = [
            'id', 'titulo', 'numero_acta', 'ejecucion', 'usuario_creacion',
            'contenido_html', 'contenido_markdown', 'resumen_ejecutivo',
            'fecha_acta', 'lugar_sesion', 'participantes', 'estado', 'estado_display',
            'version', 'fecha_creacion', 'fecha_ultima_modificacion',
            'usuario_ultima_modificacion', 'formato_preferido',
            'archivo_pdf', 'archivo_docx', 'calidad_estimada',
            'tiempo_generacion_segundos', 'tiempo_generacion_formateado',
            'comentarios_revision', 'historial_cambios'
        ]
        read_only_fields = [
            'id', 'ejecucion', 'usuario_creacion', 'numero_acta',
            'fecha_creacion', 'fecha_ultima_modificacion', 
            'usuario_ultima_modificacion', 'estado_display',
            'archivo_pdf', 'archivo_docx', 'calidad_estimada',
            'tiempo_generacion_segundos', 'tiempo_generacion_formateado',
            'historial_cambios'
        ]


class EjecucionEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de ejecuciones"""
    total_ejecuciones = serializers.IntegerField()
    ejecuciones_exitosas = serializers.IntegerField()
    ejecuciones_errores = serializers.IntegerField()
    tiempo_promedio = serializers.FloatField()
    plantilla_mas_usada = serializers.CharField()
    proveedor_mas_usado = serializers.CharField()
    estados_distribucion = serializers.DictField()


class PlantillaEstadisticasSerializer(serializers.Serializer):
    """Serializer para estadísticas de plantillas"""
    total_plantillas = serializers.IntegerField()
    plantillas_activas = serializers.IntegerField()
    segmentos_promedio = serializers.FloatField()
    tipo_acta_distribucion = serializers.DictField()
    plantillas_populares = PlantillaActaSerializer(many=True)


# Serializers para configuración de segmentos en plantillas
class ConfiguracionSegmentoSerializer(serializers.Serializer):
    """Serializer para configurar segmentos en plantilla"""
    segmento_id = serializers.IntegerField()
    orden = serializers.IntegerField(min_value=1)
    obligatorio = serializers.BooleanField(default=False)
    variables_personalizadas = serializers.DictField(default=dict)
    
    def validate_segmento_id(self, value):
        """Valida que el segmento existe"""
        try:
            SegmentoPlantilla.objects.get(id=value)
        except SegmentoPlantilla.DoesNotExist:
            raise serializers.ValidationError("El segmento especificado no existe")
        return value


class PlantillaSegmentosConfigSerializer(serializers.Serializer):
    """Serializer para configurar múltiples segmentos en plantilla"""
    segmentos = ConfiguracionSegmentoSerializer(many=True)
    
    def validate_segmentos(self, value):
        """Valida la lista de segmentos"""
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un segmento")
        
        # Validar que no hay órdenes duplicados
        ordenes = [s['orden'] for s in value]
        if len(ordenes) != len(set(ordenes)):
            raise serializers.ValidationError("No puede haber órdenes duplicados")
        
        # Validar que no hay segmentos duplicados
        segmentos_ids = [s['segmento_id'] for s in value]
        if len(segmentos_ids) != len(set(segmentos_ids)):
            raise serializers.ValidationError("No puede haber segmentos duplicados")
        
        return value