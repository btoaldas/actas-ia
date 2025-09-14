"""
Configuración de URLs para el módulo generador de actas
"""
from django.urls import path, include
from . import views, api_views

app_name = 'generador_actas'

# URLs de vistas principales
urlpatterns = [
    # Dashboard
    path('', views.dashboard_actas, name='dashboard'),
    
    # === PROVEEDORES IA ===
    path('proveedores/', views.ProveedoresListView.as_view(), name='proveedores_lista'),
    path('proveedores/crear/', views.CrearProveedorView.as_view(), name='crear_proveedor'),
    path('proveedores/<int:pk>/', views.ProveedorDetailView.as_view(), name='proveedor_detail'),
    path('proveedores/<int:pk>/editar/', views.EditarProveedorView.as_view(), name='editar_proveedor'),
    path('proveedores/<int:pk>/eliminar/', views.EliminarProveedorView.as_view(), name='eliminar_proveedor'),
    
    # === SEGMENTOS ===
    path('segmentos/', views.SegmentosListView.as_view(), name='segmentos_lista'),
    path('segmentos/crear/', views.CrearSegmentoView.as_view(), name='crear_segmento'),
    path('segmentos/<int:pk>/', views.SegmentoDetailView.as_view(), name='segmento_detail'),
    path('segmentos/<int:pk>/editar/', views.EditarSegmentoView.as_view(), name='editar_segmento'),
    path('segmentos/<int:pk>/eliminar/', views.EliminarSegmentoView.as_view(), name='eliminar_segmento'),
    
    # === PLANTILLAS ===
    path('plantillas/', views.PlantillasListView.as_view(), name='plantillas_lista'),
    path('plantillas/crear/', views.CrearPlantillaView.as_view(), name='crear_plantilla'),
    path('plantillas/<int:pk>/', views.PlantillaDetailView.as_view(), name='plantilla_detail'),
    path('plantillas/<int:pk>/editar/', views.EditarPlantillaView.as_view(), name='editar_plantilla'),
    path('plantillas/<int:pk>/eliminar/', views.EliminarPlantillaView.as_view(), name='eliminar_plantilla'),
    path('plantillas/<int:plantilla_id>/duplicar/', views.duplicar_plantilla, name='duplicar_plantilla'),
    
    # === ACTAS IA ===
    path('actas/', views.ActasListView.as_view(), name='actas_lista'),
    path('actas/crear/', views.CrearActaView.as_view(), name='crear_acta'),
    path('actas/<int:pk>/', views.ActaDetailView.as_view(), name='acta_detail'),
    path('actas/<int:pk>/editar/', views.EditarActaView.as_view(), name='editar_acta'),
    path('actas/<int:pk>/eliminar/', views.EliminarActaView.as_view(), name='eliminar_acta'),
    path('actas/crear/<int:transcripcion_id>/', views.crear_acta_desde_transcripcion, name='crear_acta_desde_transcripcion'),
    path('actas/<int:acta_id>/procesar/', views.procesar_acta, name='procesar_acta'),
    path('actas/<int:acta_id>/estado/', views.estado_procesamiento, name='estado_procesamiento'),
    path('actas/<int:acta_id>/exportar/', views.exportar_acta, name='exportar_acta'),
    
    # === CONFIGURACION ===
    path('configuracion/', views.ConfiguracionView.as_view(), name='configuracion'),
    path('configuracion/avanzada/', views.configuracion_avanzada, name='configuracion_avanzada'),
    
    # === OPERACIONES DEL SISTEMA ===
    path('operaciones/', views.operaciones_sistema, name='operaciones_sistema'),
    path('operaciones/<uuid:operacion_id>/', views.detalle_operacion, name='detalle_operacion'),
    path('operaciones/iniciar/', views.iniciar_operacion_sistema, name='iniciar_operacion_sistema'),
    
    # Transcripciones (legacy)
    path('transcripciones/', views.transcripciones_disponibles, name='transcripciones_disponibles'),
    
    # APIs REST
    path('api/', include([
        # APIs de actas
        path('actas/<int:acta_id>/procesar/', api_views.api_procesar_acta, name='api_procesar_acta'),
        path('actas/<int:acta_id>/estado/', api_views.api_estado_acta, name='api_estado_acta'),
        path('actas/<int:acta_id>/cancelar/', api_views.api_cancelar_procesamiento, name='api_cancelar_procesamiento'),
        path('actas/<int:acta_id>/preview/', api_views.api_previsualizar_contenido, name='api_previsualizar_contenido'),
        path('actas/estados/', api_views.api_estados_multiple, name='api_estados_multiple'),
        
        # APIs de transcripciones
        path('transcripciones/<int:transcripcion_id>/validar/', api_views.api_validar_transcripcion, name='api_validar_transcripcion'),
        path('transcripciones/<int:transcripcion_id>/plantillas/', api_views.api_plantillas_compatibles, name='api_plantillas_compatibles'),
        
        # APIs de plantillas
        path('plantillas/<int:plantilla_id>/segmentos/', api_views.api_segmentos_plantilla, name='api_segmentos_plantilla'),
        
        # APIs de proveedores IA
        path('proveedores/<int:proveedor_id>/probar/', api_views.api_probar_proveedor_ia, name='api_probar_proveedor_ia'),
        
        # APIs de estadísticas y monitoreo
        path('dashboard/stats/', api_views.api_dashboard_stats, name='api_dashboard_stats'),
        path('actividad/', api_views.api_actividad_reciente, name='api_actividad_reciente'),
        path('salud/', api_views.api_sistema_salud, name='api_sistema_salud'),
        
        # APIs de operaciones del sistema
        path('operaciones/iniciar/', api_views.api_iniciar_operacion, name='api_iniciar_operacion'),
        path('operaciones/<uuid:operacion_id>/estado/', api_views.api_estado_operacion, name='api_estado_operacion'),
        path('operaciones/<uuid:operacion_id>/resultado/', api_views.api_descargar_resultado, name='api_descargar_resultado'),
        path('operaciones/<uuid:operacion_id>/cancelar/', api_views.api_cancelar_operacion, name='api_cancelar_operacion'),
        path('operaciones/', api_views.api_listar_operaciones, name='api_listar_operaciones'),
    ])),
]