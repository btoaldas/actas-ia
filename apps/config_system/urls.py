from django.urls import path
from . import views

app_name = 'config_system'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Configuraciones IA
    path('ia/', views.ConfiguracionIAListView.as_view(), name='ia_list'),
    path('ia/crear/', views.ConfiguracionIACreateView.as_view(), name='ia_create'),
    path('ia/<int:pk>/', views.ConfiguracionIADetailView.as_view(), name='ia_detail'),
    path('ia/<int:pk>/editar/', views.ConfiguracionIAUpdateView.as_view(), name='ia_edit'),
    path('ia/<int:pk>/eliminar/', views.ConfiguracionIADeleteView.as_view(), name='ia_delete'),
    path('ia/<int:pk>/probar/', views.probar_configuracion_ia, name='ia_test'),
    
    # Configuraciones Whisper
    path('whisper/', views.ConfiguracionWhisperListView.as_view(), name='whisper_list'),
    path('whisper/crear/', views.ConfiguracionWhisperCreateView.as_view(), name='whisper_create'),
    path('whisper/<int:pk>/', views.ConfiguracionWhisperDetailView.as_view(), name='whisper_detail'),
    path('whisper/<int:pk>/editar/', views.ConfiguracionWhisperUpdateView.as_view(), name='whisper_edit'),
    path('whisper/<int:pk>/eliminar/', views.ConfiguracionWhisperDeleteView.as_view(), name='whisper_delete'),
    path('whisper/<int:pk>/probar/', views.probar_configuracion_whisper, name='whisper_test'),
    
    # ==================== GESTIÓN DE USUARIOS ====================
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/crear/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/', views.usuario_detail, name='usuario_detail'),
    path('usuarios/<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_delete, name='usuario_delete'),
    path('usuarios/<int:pk>/toggle-active/', views.usuario_toggle_active, name='usuario_toggle_active'),
    
    # ==================== GESTIÓN DE PERFILES ====================
    path('perfiles/', views.perfiles_list, name='perfiles_list'),
    path('perfiles/crear/', views.perfil_create, name='perfil_create'),
    path('perfiles/<int:pk>/', views.perfil_detail, name='perfil_detail'),
    path('perfiles/<int:pk>/editar/', views.perfil_edit, name='perfil_edit'),
    path('perfiles/<int:pk>/eliminar/', views.perfil_delete, name='perfil_delete'),
    path('perfiles/<int:pk>/toggle-active/', views.perfil_toggle_active, name='perfil_toggle_active'),
    
    # ==================== GESTIÓN DE PERMISOS ====================
    path('permisos/', views.permisos_list, name='permisos_list'),
    path('permisos/<int:pk>/', views.permisos_detail, name='permisos_detail'),
    path('permisos/<int:pk>/editar/', views.permisos_edit, name='permisos_edit'),
    path('permisos/<int:pk>/reset-rol/', views.permisos_reset_por_rol, name='permisos_reset_rol'),
    path('permisos/aplicar-masivo/', views.aplicar_permisos_masivo, name='aplicar_permisos_masivo'),
    
    # Gestión de usuarios con permisos (legacy - mantener compatibilidad)
    path('usuarios-legacy/', views.UsuariosListView.as_view(), name='usuarios_list_legacy'),
    path('usuarios-legacy/<int:pk>/permisos/', views.gestionar_permisos_usuario, name='gestionar_permisos'),
    
    # AJAX endpoints
    path('toggle-ia/<int:pk>/', views.toggle_configuracion_ia, name='toggle_ia'),
    path('toggle-whisper/<int:pk>/', views.toggle_configuracion_whisper, name='toggle_whisper'),
    
    # API endpoints para estadísticas
    path('api/estadisticas/', views.api_estadisticas, name='api_estadisticas'),
    path('api/configuraciones-activas/', views.api_configuraciones_activas, name='api_configuraciones_activas'),
]
