from django.urls import path
from . import views_new_permissions

app_name = 'new_permissions'

urlpatterns = [
    # Dashboard principal
    path('', views_new_permissions.permissions_dashboard, name='dashboard'),
    
    # Gestión de permisos del sistema
    path('system/', views_new_permissions.system_permissions_list, name='system_list'),
    path('system/create/', views_new_permissions.system_permission_create, name='system_create'),
    path('system/<int:permission_id>/edit/', views_new_permissions.system_permission_edit, name='system_edit'),
    
    # Gestión de perfiles de usuario
    path('profiles/', views_new_permissions.user_profiles_list, name='profiles_list'),
    path('profiles/create/', views_new_permissions.user_profile_create, name='profiles_create'),
    path('profiles/<int:profile_id>/edit/', views_new_permissions.user_profile_edit, name='profiles_edit'),
    
    # Asignaciones de perfiles a usuarios
    path('assignments/', views_new_permissions.user_assignments_list, name='assignments_list'),
    path('assignments/create/', views_new_permissions.user_assignment_create, name='assignments_create'),
    
    # Utilidades
    path('discover/', views_new_permissions.discover_permissions, name='discover'),
    path('bulk-assign/', views_new_permissions.bulk_assignment, name='bulk_assign'),
    path('bulk-assignment/', views_new_permissions.bulk_assignment, name='bulk_assignment'),
    
    # APIs
    path('api/user/<int:user_id>/permissions/', views_new_permissions.user_permissions_api, name='api_user_permissions'),
    path('api/check-permission/', views_new_permissions.check_permission_api, name='api_check_permission'),
    
    # ===== NUEVAS FUNCIONALIDADES AVANZADAS =====
    
    # Gestión avanzada de usuarios
    path('users/', views_new_permissions.user_management_list, name='user_management_list'),
    path('users/advanced/', views_new_permissions.user_management_list, name='user_management_advanced'),
    path('users/<int:user_id>/assign/', views_new_permissions.user_profile_assignment, name='user_profile_assignment'),
    
    # Creación y gestión de permisos
    path('permissions/create/', views_new_permissions.permission_creation, name='permission_creation'),
    path('permissions/discover-routes/', views_new_permissions.discover_routes_permissions, name='discover_routes_permissions'),
    
    # Gestión avanzada de perfiles
    path('profiles/advanced/', views_new_permissions.profile_management_advanced, name='profile_management_advanced'),
    path('profiles/<int:profile_id>/permissions/', views_new_permissions.profile_permission_assignment, name='profile_permission_assignment'),
    path('profiles/<int:profile_id>/delete/', views_new_permissions.profile_delete, name='profile_delete'),
]
