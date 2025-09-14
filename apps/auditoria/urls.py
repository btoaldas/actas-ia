"""
URLs para la app de auditoría
"""
from django.urls import path
from . import views
from . import debug_views

app_name = 'auditoria'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_auditoria, name='dashboard'),
    
    # Vistas de logs
    path('logs/sistema/', views.logs_sistema, name='logs_sistema'),
    path('logs/navegacion/', views.logs_navegacion, name='logs_navegacion'),
    
    # Vista de auditoría
    path('auditoria/cambios/', views.auditoria_cambios, name='auditoria_cambios'),
    
    # APIs
    path('api/estadisticas/', views.api_estadisticas_auditoria, name='api_estadisticas'),
    path('api/eventos/', views.api_ultimos_eventos, name='api_ultimos_eventos'),
    path('api/detalle/<int:log_id>/<str:tipo>/', views.detalle_log, name='detalle_log'),
    
    # Vista de eventos en tiempo real
    path('eventos/', views.eventos_tiempo_real, name='eventos_tiempo_real'),
    
    # Debug de sesiones y cookies
    path('debug/session/', debug_views.debug_session_info, name='debug_session'),
    path('debug/session/api/', debug_views.session_debug_api, name='session_debug_api'),
    path('debug/session/clear/', debug_views.clear_session_data, name='clear_session_data'),
    path('debug/sessions/', debug_views.debug_all_sessions, name='debug_all_sessions'),
    path('debug/session/test/', debug_views.test_session_modification, name='test_session'),
    path('debug/cookies/', debug_views.cookie_test_view, name='cookie_test'),
    path('log-activity/', debug_views.log_frontend_activity, name='log_frontend_activity'),
]
