from django.urls import path
from . import views

app_name = 'config_system'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # ==================== CONFIGURACIONES SMTP ====================
    path('smtp/', views.smtp_list, name='smtp_list'),
    path('smtp/create/', views.smtp_create, name='smtp_create'),  # Cambié 'crear' por 'create'
    path('smtp/test/', views.smtp_test_form, name='smtp_test'),    # Cambié para formulario de test
    path('smtp/logs/', views.email_logs, name='smtp_logs'),       # Agregué ruta logs
    path('smtp/<int:pk>/', views.smtp_detail, name='smtp_detail'),
    path('smtp/<int:pk>/edit/', views.smtp_edit, name='smtp_edit'), # Cambié 'editar' por 'edit'
    path('smtp/<int:pk>/delete/', views.smtp_delete, name='smtp_delete'), # Cambié 'eliminar' por 'delete'
    path('smtp/<int:pk>/toggle-active/', views.smtp_toggle_active, name='smtp_toggle_active'),
    path('smtp/<int:pk>/set-default/', views.smtp_set_default, name='smtp_set_default'),
    path('smtp/<int:pk>/test/', views.smtp_test_single, name='smtp_test_single'),
    
    # Configuración general de email
    path('email-config/', views.email_config, name='email_config'),
    path('email-test/', views.email_test, name='email_test'),
    
    # Logs de envío
    path('email-logs/', views.email_logs, name='email_logs'),
    path('email-logs/<int:pk>/', views.email_log_detail, name='email_log_detail'),
    
    # Estadísticas SMTP
    path('smtp-stats/', views.smtp_stats, name='smtp_stats'),
    path('api/smtp-stats/', views.api_smtp_stats, name='api_smtp_stats'),
    
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
    
    # ==================== SISTEMA DE PERMISOS PERSONALIZADOS ====================
    # Dashboard de permisos
    path('permisos/dashboard/', views.permisos_dashboard, name='permisos_dashboard'),
    
    # Gestión de permisos personalizados
    path('permisos/', views.permisos_list, name='permisos_list'),
    path('permisos/crear/', views.permiso_create, name='permiso_create'),
    path('permisos/<int:pk>/', views.permiso_detail, name='permiso_detail'),
    path('permisos/<int:pk>/editar/', views.permiso_edit, name='permiso_edit'),
    path('permisos/<int:pk>/eliminar/', views.permiso_delete, name='permiso_delete'),
    
    # Gestión de perfiles de usuario
    path('perfiles/', views.perfiles_list, name='perfiles_list'),
    path('perfiles/crear/', views.perfil_create, name='perfil_create'),
    path('perfiles/<int:pk>/', views.perfil_detail, name='perfil_detail'),
    path('perfiles/<int:pk>/editar/', views.perfil_edit, name='perfil_edit'),
    path('perfiles/<int:pk>/eliminar/', views.perfil_delete, name='perfil_delete'),
    
    # Asignación de perfiles a usuarios
    path('usuarios-perfiles/', views.usuarios_perfiles_list, name='usuarios_perfiles_list'),
    path('usuarios-perfiles/asignar/', views.usuario_perfiles_asignar, name='usuario_perfiles_asignar'),
    path('usuarios-perfiles/<int:pk>/editar/', views.usuario_perfiles_edit, name='usuario_perfiles_edit'),
    path('usuarios-perfiles/<int:pk>/eliminar/', views.usuario_perfiles_delete, name='usuario_perfiles_delete'),
    path('usuarios-perfiles/asignacion-masiva/', views.asignacion_masiva, name='asignacion_masiva'),
    
    # Logs y auditoría
    path('permisos/logs/', views.logs_permisos, name='logs_permisos'),
    path('permisos/reportes/', views.reportes_permisos, name='reportes_permisos'),
    # path('permisos/analisis/', views.analisis_uso_permisos, name='analisis_uso_permisos'),
    
    # APIs para el sistema de permisos - TEMPORALMENTE COMENTADAS
    # path('api/permisos/verificar/', views.api_verificar_permiso, name='api_verificar_permiso'),
    # path('api/permisos/usuario/<int:user_id>/', views.api_permisos_usuario, name='api_permisos_usuario'),
    # path('api/perfiles/permisos/<int:perfil_id>/', views.api_permisos_perfil, name='api_permisos_perfil'),
    
    # ==================== GESTIÓN DE PERMISOS LEGACY ====================
    path('permisos-legacy/<int:pk>/', views.permisos_detail, name='permisos_detail_legacy'),
    path('permisos-legacy/<int:pk>/editar/', views.permisos_edit, name='permisos_edit_legacy'),
    path('permisos-legacy/<int:pk>/reset-rol/', views.permisos_reset_por_rol, name='permisos_reset_rol'),
    path('permisos-legacy/aplicar-masivo/', views.aplicar_permisos_masivo, name='aplicar_permisos_masivo'),
    
    # Gestión de usuarios con permisos (legacy - mantener compatibilidad)
    path('usuarios-legacy/', views.UsuariosListView.as_view(), name='usuarios_list_legacy'),
    path('usuarios-legacy/<int:pk>/permisos/', views.gestionar_permisos_usuario, name='gestionar_permisos'),
    
    # AJAX endpoints
    path('toggle-ia/<int:pk>/', views.toggle_configuracion_ia, name='toggle_ia'),
    path('toggle-whisper/<int:pk>/', views.toggle_configuracion_whisper, name='toggle_whisper'),
    
    # API endpoints para estadísticas
    path('api/estadisticas/', views.api_estadisticas, name='api_estadisticas'),
    path('api/configuraciones-activas/', views.api_configuraciones_activas, name='api_configuraciones_activas'),
    
    # ==================== NUEVO SISTEMA DE PERMISOS ====================
    # Incluir las nuevas URLs del sistema de permisos simplificado
]

# Agregar las URLs del nuevo sistema de permisos
from django.urls import include
from . import urls_new_permissions

# Agregar al final para evitar conflictos
urlpatterns += [
    path('new-permissions/', include(urls_new_permissions, namespace='new_permissions')),
]
