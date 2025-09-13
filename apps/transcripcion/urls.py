from django.urls import path
from . import views
from .views_dashboards import (
    dashboard_audios_transcribir,
    dashboard_transcripciones_hechas,
    proceso_transcripcion,
    detalle_transcripcion_dashboard,
    revertir_audios_por_transcribir,
    api_estado_transcripcion,
    api_actualizar_json,
    api_editar_segmento,
    api_eliminar_segmento,
    api_agregar_segmento,
    api_renombrar_hablantes,
    api_regenerar_transcripcion,
    api_agregar_hablante_nuevo,
    api_insertar_segmento_posicion
)
from .api_edicion_avanzada import (
    api_obtener_estructura_completa,
    api_editar_segmento_avanzado,
    api_agregar_segmento_avanzado,
    api_eliminar_segmento_avanzado,
    api_gestionar_hablantes_avanzado,
    api_guardar_estructura_completa
)
from .api_test import api_test_conectividad

app_name = 'transcripcion'

urlpatterns = [
    # Nuevos dashboards reorganizados
    path('', dashboard_audios_transcribir, name='index'),
    path('audios/', dashboard_audios_transcribir, name='audios_dashboard'),
    path('transcripciones/', dashboard_transcripciones_hechas, name='transcripciones_dashboard'),
    path('proceso/<int:audio_id>/', proceso_transcripcion, name='proceso_transcripcion'),
    path('detalle/<int:transcripcion_id>/', detalle_transcripcion_dashboard, name='detalle_transcripcion'),
    path('revertir/<int:transcripcion_id>/', revertir_audios_por_transcribir, name='revertir_audios_por_transcribir'),
    
    # API para consultar estado
    path('api/estado/<int:transcripcion_id>/', api_estado_transcripcion, name='api_estado_transcripcion'),
    
    # APIs para edición de transcripciones (básicas)
    path('api/actualizar-json/<int:transcripcion_id>/', api_actualizar_json, name='api_actualizar_json'),
    path('api/editar-segmento/<int:transcripcion_id>/', api_editar_segmento, name='api_editar_segmento'),
    path('api/eliminar-segmento/<int:transcripcion_id>/', api_eliminar_segmento, name='api_eliminar_segmento'),
    path('api/agregar-segmento/<int:transcripcion_id>/', api_agregar_segmento, name='api_agregar_segmento'),
    path('api/renombrar-hablantes/<int:transcripcion_id>/', api_renombrar_hablantes, name='api_renombrar_hablantes'),
    
    # APIs nuevas para funcionalidades avanzadas
    path('api/regenerar-transcripcion/<int:transcripcion_id>/', api_regenerar_transcripcion, name='api_regenerar_transcripcion'),
    path('api/agregar-hablante/<int:transcripcion_id>/', api_agregar_hablante_nuevo, name='api_agregar_hablante_nuevo'),
    path('api/insertar-segmento/<int:transcripcion_id>/', api_insertar_segmento_posicion, name='api_insertar_segmento_posicion'),
    
    # APIs para edición avanzada de transcripciones (nueva estructura JSON)
    path('api/v2/estructura/<int:transcripcion_id>/', api_obtener_estructura_completa, name='api_obtener_estructura'),
    path('api/v2/editar-segmento/<int:transcripcion_id>/', api_editar_segmento_avanzado, name='api_editar_segmento_v2'),
    path('api/v2/agregar-segmento/<int:transcripcion_id>/', api_agregar_segmento_avanzado, name='api_agregar_segmento_v2'),
    path('api/v2/eliminar-segmento/<int:transcripcion_id>/', api_eliminar_segmento_avanzado, name='api_eliminar_segmento_v2'),
    path('api/v2/gestionar-hablantes/<int:transcripcion_id>/', api_gestionar_hablantes_avanzado, name='api_gestionar_hablantes_v2'),
    path('api/v2/guardar-estructura/<int:transcripcion_id>/', api_guardar_estructura_completa, name='api_guardar_estructura_v2'),
    
    # API de test (sin autenticación)
    path('api/test/', api_test_conectividad, name='api_test'),
    
    # Vistas existentes (compatibilidad)
    path('lista/', views.lista_transcripciones, name='lista'),
    path('lista-transcripciones/', views.lista_transcripciones, name='lista_transcripciones'),
    
    # Gestión de audios para transcribir
    path('audios-listos/', views.audios_listos_transcribir, name='audios_listos'),
    path('configurar/<int:audio_id>/', views.configurar_transcripcion, name='configurar'),
    
    # Gestión de transcripciones
    path('iniciar/<int:procesamiento_id>/', views.iniciar_transcripcion, name='iniciar'),
    path('detalle-legacy/<int:transcripcion_id>/', views.detalle_transcripcion, name='detalle_legacy'),
    path('reiniciar/<int:transcripcion_id>/', views.reiniciar_transcripcion, name='reiniciar'),
    
    # Visualización de resultados
    path('resultado/<int:transcripcion_id>/', views.vista_resultado_transcripcion, name='vista_resultado'),
    
    # Exportación
    path('exportar/<int:transcripcion_id>/<str:formato>/', views.exportar_transcripcion, name='exportar'),
    
    # APIs para edición
    path('api/estado/<int:transcripcion_id>/', views.estado_transcripcion, name='api_estado'),
    path('api/audio-estado/<int:audio_id>/', views.audio_estado_transcripcion, name='api_audio_estado'),
    path('api/editar/<int:transcripcion_id>/', views.editar_segmento, name='api_editar_segmento'),
    path('api/hablantes/<int:transcripcion_id>/', views.gestionar_hablantes, name='api_gestionar_hablantes'),
]
