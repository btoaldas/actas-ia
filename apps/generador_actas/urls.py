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
    path('proveedores/', views.lista_proveedores_ia, name='proveedores_lista'),
    path('proveedores/crear/', views.crear_proveedor_ia, name='crear_proveedor_ia'),
    path('proveedores/<int:pk>/editar/', views.editar_proveedor_ia, name='editar_proveedor_ia'),
    path('proveedores/<int:pk>/eliminar/', views.eliminar_proveedor_ia, name='eliminar_proveedor_ia'),
    path('proveedores/test/', views.test_proveedor_ia, name='test_proveedor_ia'),
    
    # === SEGMENTOS DE PLANTILLA ===
    path('segmentos/', views.segmentos_dashboard, name='segmentos_dashboard'),
    path('segmentos/lista/', views.lista_segmentos, name='lista_segmentos'),
    path('segmentos/crear/', views.crear_segmento, name='crear_segmento'),
    path('segmentos/<int:pk>/', views.detalle_segmento, name='detalle_segmento'),
    path('segmentos/<int:pk>/editar/', views.editar_segmento, name='editar_segmento'),
    path('segmentos/<int:pk>/eliminar/', views.eliminar_segmento, name='eliminar_segmento'),
    path('segmentos/probar/', views.probar_segmento, name='probar_segmento'),
    path('segmentos/asistente-variables/', views.asistente_variables, name='asistente_variables'),
    
    # === PLANTILLAS ===
    path('plantillas/', views.PlantillasListView.as_view(), name='plantillas_lista'),
    path('plantillas/crear/', views.PlantillaCreateView.as_view(), name='crear_plantilla'),
    path('plantillas/crear-simple/', views.crear_plantilla_simple, name='crear_plantilla_simple'),
    path('plantillas/<int:pk>/', views.PlantillaDetailView.as_view(), name='plantilla_detail'),
    path('plantillas/<int:pk>/editar/', views.PlantillaUpdateView.as_view(), name='editar_plantilla'),
    path('plantillas/<int:pk>/eliminar/', views.EliminarPlantillaView.as_view(), name='eliminar_plantilla'),
    path('plantillas/<int:plantilla_id>/duplicar/', views.duplicar_plantilla, name='duplicar_plantilla'),
    
    # === ALIASES DE PLANTILLAS (mantener compatibilidad) ===
    path('plantillas/nuevo/', views.PlantillaListView.as_view(), name='lista_plantillas'),
    path('plantillas/nuevo/crear/', views.PlantillaCreateView.as_view(), name='plantilla_crear'),
    path('plantillas/nuevo/<int:pk>/editar/', views.PlantillaUpdateView.as_view(), name='plantilla_editar'),
    path('plantillas/nuevo/<int:pk>/eliminar/', views.PlantillaDeleteView.as_view(), name='plantilla_eliminar'),
    path('plantillas/nuevo/<int:pk>/', views.PlantillaDetailView.as_view(), name='ver_plantilla'),
    path('plantillas/nuevo/<int:plantilla_id>/configurar/', views.configurar_segmentos_plantilla, name='configurar_segmentos_plantilla'),
    path('plantillas/nuevo/<int:plantilla_id>/preview/', views.vista_previa_plantilla, name='vista_previa_plantilla'),
    path('plantillas/nuevo/dashboard/', views.plantillas_dashboard, name='plantillas_dashboard'),
    
    # === EJECUCIÓN DE PLANTILLAS ===
    path('ejecuciones/', views.EjecucionListView.as_view(), name='ejecuciones_lista'),
    path('ejecuciones/<uuid:pk>/', views.EjecucionDetailView.as_view(), name='ver_ejecucion'),
    path('plantillas/<int:plantilla_pk>/ejecutar/', views.EjecucionPlantillaCreateView.as_view(), name='plantilla_ejecutar'),
    path('ejecuciones/<uuid:ejecucion_pk>/segmento/<int:resultado_pk>/editar/', 
         views.editar_resultado_segmento, name='editar_resultado_segmento'),
    path('ejecuciones/<uuid:ejecucion_pk>/generar-acta/', 
         views.generar_acta_final, name='generar_acta_final'),
    
    # === ACTAS IA ===
    path('actas/', views.ActasListView.as_view(), name='actas_lista'),
    path('actas/crear/', views.CrearActaView.as_view(), name='crear_acta'),
    path('actas/<int:pk>/', views.ActaDetailView.as_view(), name='acta_detail'),
    path('actas/<int:pk>/editar/', views.EditarActaView.as_view(), name='editar_acta'),
    path('actas/<int:pk>/eliminar/', views.EliminarActaView.as_view(), name='eliminar_acta'),
    path('actas/<int:pk>/preview/', views.preview_acta, name='acta_preview'),  # ✅ URL faltante
    path('actas/<int:pk>/generar/', views.generar_acta, name='generar_acta'),  # ✅ URL faltante
    path('actas/estados/', views.estados_actas, name='estados_actas'),  # ✅ URL faltante
    path('actas/crear/<int:transcripcion_id>/', views.crear_acta_desde_transcripcion, name='crear_acta_desde_transcripcion'),
    path('actas/<int:acta_id>/procesar/', views.procesar_acta, name='procesar_acta'),
    path('actas/<int:acta_id>/estado/', views.estado_procesamiento, name='estado_procesamiento'),
    path('actas/<int:acta_id>/exportar/', views.exportar_acta, name='exportar_acta'),
    path('actas/<int:acta_id>/revertir/', views.revertir_acta, name='revertir_acta'),
    
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
        path('proveedores/probar-conexion/', views.probar_conexion_proveedor, name='api_probar_conexion_proveedor'),
        path('proveedores/probar-conexion-celery/', views.probar_conexion_proveedor_celery, name='api_probar_conexion_proveedor_celery'),
        path('proveedores/progreso-prueba/<str:task_id>/', views.obtener_progreso_prueba, name='api_progreso_prueba'),
        path('proveedores/modelos/<str:tipo_proveedor>/', views.obtener_modelos_proveedor, name='api_modelos_proveedor'),
        path('proveedores/configuracion/<str:tipo_proveedor>/', views.obtener_configuracion_defecto, name='api_configuracion_defecto'),
        
        # APIs de segmentos
        path('segmentos/probar/', views.api_probar_segmento, name='api_probar_segmento'),
        path('segmentos-disponibles/', api_views.api_segmentos_disponibles, name='api_segmentos_disponibles'),
        
        # APIs Fase 2: Drag & Drop
        path('plantillas/<int:plantilla_id>/orden-segmentos/', views.api_actualizar_orden_segmentos, name='api_actualizar_orden_segmentos'),
        path('obtener-configuracion-segmento/<int:config_id>/', views.api_obtener_configuracion_segmento, name='api_obtener_configuracion_segmento'),
        
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