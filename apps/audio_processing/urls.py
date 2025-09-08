from django.urls import path
from . import views

app_name = 'audio_processing'

urlpatterns = [
    # Vista principal unificada (dashboard + grabación + subida)
    path('', views.centro_audio, name='centro_audio'),
    
    # APIs para el centro de audio
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/recent-processes/', views.api_recent_processes, name='api_recent_processes'),
    path('api/procesar/', views.api_procesar_audio, name='api_procesar_audio'),
    path('api/estado/<int:id>/', views.api_estado_procesamiento, name='api_estado_procesamiento'),
    
    # Vista de lista de procesamientos
    path('lista/', views.lista_procesamientos, name='lista_procesamientos'),
    
    # Vistas de detalle y gestión
    path('detalle/<int:id>/', views.detalle_procesamiento, name='detalle_procesamiento'),
    path('editar/<int:id>/', views.editar_procesamiento, name='editar_procesamiento'),
    path('confirmar-eliminar/<int:id>/', views.confirmar_eliminar_procesamiento, name='confirmar_eliminar_procesamiento'),
    path('eliminar/<int:id>/', views.eliminar_procesamiento, name='eliminar_procesamiento'),
    
    # Acciones de control de procesamientos
    path('reiniciar/<int:id>/', views.reiniciar_procesamiento, name='reiniciar_procesamiento'),
    path('detener/<int:id>/', views.detener_procesamiento, name='detener_procesamiento'),
    path('iniciar/<int:id>/', views.iniciar_procesamiento, name='iniciar_procesamiento'),
    
    # Gestión de tipos de reunión
    path('tipos-reunion/', views.tipos_reunion, name='tipos_reunion'),
    path('tipos-reunion/crear/', views.crear_tipo_reunion, name='crear_tipo_reunion'),
    path('tipos-reunion/editar/<int:id>/', views.editar_tipo_reunion, name='editar_tipo_reunion'),
    path('tipos-reunion/eliminar/<int:id>/', views.eliminar_tipo_reunion, name='eliminar_tipo_reunion'),
]
