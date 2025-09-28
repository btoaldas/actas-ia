from django.urls import path
from . import views

app_name = 'gestion_actas'

urlpatterns = [
    # Vistas principales
    path('', views.listado_actas, name='listado'),
    path('acta/<int:acta_id>/', views.ver_acta, name='ver'),
    path('acta/<int:acta_id>/editar/', views.editor_acta, name='editor'),
    
    # Proceso de revisión
    path('acta/<int:acta_id>/configurar-revision/', views.configurar_revision, name='configurar_revision'),
    path('acta/<int:acta_id>/revisar/', views.panel_revision, name='revisar'),
    path('dashboard-revision/', views.dashboard_revision, name='dashboard_revision'),
    
    # Funciones de emergencia/administración
    path('acta/<int:acta_id>/activar-edicion/', views.activar_edicion, name='activar_edicion'),
    path('acta/<int:acta_id>/publicar/', views.publicar_acta, name='publicar'),
    
    # APIs AJAX
    path('api/acta/<int:acta_id>/cambiar-estado/', views.cambiar_estado_acta, name='cambiar_estado'),
    path('api/acta/<int:acta_id>/autoguardar/', views.autoguardar_contenido, name='autoguardar'),
]