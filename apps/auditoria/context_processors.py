"""
Context processors para la app de auditoría
"""
from .views import obtener_ultimos_eventos_sistema
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta


def eventos_sistema_context(request):
    """
    Context processor que agrega los últimos eventos del sistema
    a todas las plantillas. Usa caché para optimizar rendimiento.
    """
    # Solo cargar para usuarios autenticados
    if not request.user.is_authenticated:
        return {'ultimos_eventos_sistema': []}
    
    # Usar caché para evitar consultas costosas en cada request
    cache_key = 'ultimos_eventos_sistema'
    eventos = cache.get(cache_key)
    
    if eventos is None:
        try:
            eventos = obtener_ultimos_eventos_sistema(5)
            # Cachear por 2 minutos
            cache.set(cache_key, eventos, 120)
        except Exception as e:
            # En caso de error, devolver lista vacía
            eventos = []
    
    return {
        'ultimos_eventos_sistema': eventos
    }


def estadisticas_resumen_context(request):
    """
    Context processor que agrega estadísticas resumidas del sistema
    """
    if not request.user.is_authenticated:
        return {'stats_sistema': {}}
    
    cache_key = 'stats_sistema_resumen'
    stats = cache.get(cache_key)
    
    if stats is None:
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                # Contar eventos de hoy por tipo
                cursor.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM logs.celery_logs WHERE DATE(timestamp) = CURRENT_DATE AND estado = 'SUCCESS') as tareas_exitosas,
                        (SELECT COUNT(*) FROM logs.celery_logs WHERE DATE(timestamp) = CURRENT_DATE AND estado = 'FAILURE') as tareas_fallidas,
                        (SELECT COUNT(*) FROM logs.archivo_logs WHERE DATE(timestamp) = CURRENT_DATE AND operacion = 'UPLOAD') as archivos_subidos,
                        (SELECT COUNT(*) FROM logs.errores_sistema WHERE DATE(timestamp) = CURRENT_DATE AND resuelto = false) as errores_pendientes
                """)
                result = cursor.fetchone()
                
                stats = {
                    'tareas_exitosas_hoy': result[0] or 0,
                    'tareas_fallidas_hoy': result[1] or 0,
                    'archivos_subidos_hoy': result[2] or 0,
                    'errores_pendientes': result[3] or 0,
                    'total_notificaciones': (result[1] or 0) + (result[3] or 0)  # Fallos + errores
                }
                
                # Cachear por 5 minutos
                cache.set(cache_key, stats, 300)
        except Exception as e:
            stats = {
                'tareas_exitosas_hoy': 0,
                'tareas_fallidas_hoy': 0,
                'archivos_subidos_hoy': 0,
                'errores_pendientes': 0,
                'total_notificaciones': 0
            }
    
    return {
        'stats_sistema': stats
    }


def ultimas_actas_publicadas_context(request):
    """
    Context processor que agrega las últimas actas publicadas
    para mostrar en el menú de notificaciones
    """
    if not request.user.is_authenticated:
        return {'ultimas_actas_publicadas': []}
    
    cache_key = 'ultimas_actas_publicadas'
    actas = cache.get(cache_key)
    
    if actas is None:
        try:
            # Importar aquí para evitar dependencias circulares
            from apps.pages.models import ActaMunicipal, EstadoActa
            
            # Obtener estado "publicada"
            estado_publicada = EstadoActa.objects.filter(nombre='publicada').first()
            
            if estado_publicada:
                # Obtener las 5 últimas actas publicadas
                actas_queryset = ActaMunicipal.objects.filter(
                    estado=estado_publicada,
                    activo=True,
                    acceso='publico'  # Solo actas públicas
                ).select_related(
                    'tipo_sesion', 'estado', 'secretario'
                ).order_by('-fecha_publicacion', '-fecha_sesion')[:5]
                
                actas = []
                for acta in actas_queryset:
                    # Calcular tiempo transcurrido
                    if acta.fecha_publicacion:
                        tiempo_diff = timezone.now() - acta.fecha_publicacion
                    else:
                        tiempo_diff = timezone.now() - acta.fecha_sesion
                    
                    if tiempo_diff.days > 0:
                        tiempo_hace = f"hace {tiempo_diff.days} día{'s' if tiempo_diff.days != 1 else ''}"
                    elif tiempo_diff.seconds > 3600:
                        horas = tiempo_diff.seconds // 3600
                        tiempo_hace = f"hace {horas} hora{'s' if horas != 1 else ''}"
                    else:
                        minutos = tiempo_diff.seconds // 60
                        tiempo_hace = f"hace {minutos} minuto{'s' if minutos != 1 else ''}"
                    
                    actas.append({
                        'id': acta.pk,
                        'titulo': acta.titulo,
                        'numero_acta': acta.numero_acta,
                        'tipo_sesion': acta.tipo_sesion.get_nombre_display() if acta.tipo_sesion else 'Sin tipo',
                        'fecha_sesion': acta.fecha_sesion,
                        'fecha_publicacion': acta.fecha_publicacion,
                        'secretario_nombre': acta.secretario.get_full_name() or acta.secretario.username,
                        'tiempo_hace': tiempo_hace,
                        'url': acta.get_absolute_url(),
                        'icono': acta.tipo_sesion.icono if acta.tipo_sesion else 'fas fa-file-alt',
                        'color': acta.tipo_sesion.color if acta.tipo_sesion else '#6c757d'
                    })
            else:
                actas = []
            
            # Cachear por 5 minutos
            cache.set(cache_key, actas, 300)
            
        except Exception as e:
            # En caso de error, devolver lista vacía
            actas = []
    
    return {
        'ultimas_actas_publicadas': actas
    }