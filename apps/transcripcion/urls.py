from django.urls import path
from . import views

app_name = 'transcripcion'

urlpatterns = [
    # Vista principal
    path('', views.lista_transcripciones, name='lista'),
    path('lista/', views.lista_transcripciones, name='lista_transcripciones'),
    
    # Gestión de audios para transcribir
    path('audios-listos/', views.audios_listos_transcribir, name='audios_listos'),
    path('configurar/<int:audio_id>/', views.configurar_transcripcion, name='configurar'),
    
    # Gestión de transcripciones
    path('iniciar/<int:procesamiento_id>/', views.iniciar_transcripcion, name='iniciar'),
    path('detalle/<int:transcripcion_id>/', views.detalle_transcripcion, name='detalle'),
    path('reiniciar/<int:transcripcion_id>/', views.reiniciar_transcripcion, name='reiniciar'),
    
    # Visualización de resultados
    path('resultado/<int:transcripcion_id>/', views.vista_resultado_transcripcion, name='vista_resultado'),
    
    # Exportación
    path('exportar/<int:transcripcion_id>/<str:formato>/', views.exportar_transcripcion, name='exportar'),
    
    # APIs para edición
    path('api/estado/<int:transcripcion_id>/', views.estado_transcripcion, name='api_estado'),
    path('api/editar/<int:transcripcion_id>/', views.editar_segmento, name='api_editar_segmento'),
    path('api/hablantes/<int:transcripcion_id>/', views.gestionar_hablantes, name='api_gestionar_hablantes'),
]
