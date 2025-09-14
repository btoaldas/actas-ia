"""
Vistas para el dashboard de auditoría
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime, timedelta
from .models import (
    SistemaLogs, NavegacionUsuarios, ApiLogs, ErroresSistema,
    AccesoUsuarios, CeleryLogs, ArchivoLogs, AdminLogs, CambiosBD
)
from django.contrib.auth.models import User


@login_required
def dashboard_auditoria(request):
    """Dashboard principal de auditoría"""
    
    # Obtener estadísticas generales
    with connection.cursor() as cursor:
        # Estadísticas de hoy
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM logs.sistema_logs WHERE DATE(timestamp) = CURRENT_DATE) as logs_sistema,
                (SELECT COUNT(*) FROM logs.navegacion_usuarios WHERE DATE(timestamp) = CURRENT_DATE) as navegacion,
                (SELECT COUNT(*) FROM logs.api_logs WHERE DATE(timestamp) = CURRENT_DATE) as api_calls,
                (SELECT COUNT(*) FROM logs.errores_sistema WHERE DATE(timestamp) = CURRENT_DATE) as errores,
                (SELECT COUNT(*) FROM logs.acceso_usuarios WHERE DATE(timestamp) = CURRENT_DATE) as accesos,
                (SELECT COUNT(*) FROM auditoria.cambios_bd WHERE DATE(timestamp) = CURRENT_DATE) as cambios_bd
        """)
        estadisticas_hoy = cursor.fetchone()
        
        # Estadísticas de la semana
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM logs.sistema_logs WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as logs_sistema,
                (SELECT COUNT(*) FROM logs.navegacion_usuarios WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as navegacion,
                (SELECT COUNT(*) FROM logs.api_logs WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as api_calls,
                (SELECT COUNT(*) FROM logs.errores_sistema WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as errores,
                (SELECT COUNT(*) FROM logs.acceso_usuarios WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as accesos,
                (SELECT COUNT(*) FROM auditoria.cambios_bd WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days') as cambios_bd
        """)
        estadisticas_semana = cursor.fetchone()
    
    # Últimos eventos
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 'sistema' as tipo, nivel, categoria, mensaje, timestamp, usuario_id
            FROM logs.sistema_logs
            WHERE timestamp >= CURRENT_DATE
            ORDER BY timestamp DESC LIMIT 5
        """)
        ultimos_eventos = cursor.fetchall()
    
    context = {
        'estadisticas_hoy': {
            'logs_sistema': estadisticas_hoy[0],
            'navegacion': estadisticas_hoy[1],
            'api_calls': estadisticas_hoy[2],
            'errores': estadisticas_hoy[3],
            'accesos': estadisticas_hoy[4],
            'cambios_bd': estadisticas_hoy[5],
        },
        'estadisticas_semana': {
            'logs_sistema': estadisticas_semana[0],
            'navegacion': estadisticas_semana[1],
            'api_calls': estadisticas_semana[2],
            'errores': estadisticas_semana[3],
            'accesos': estadisticas_semana[4],
            'cambios_bd': estadisticas_semana[5],
        },
        'ultimos_eventos': ultimos_eventos,
        'parent': 'auditoria',
        'segment': 'dashboard'
    }
    
    return render(request, 'auditoria/dashboard.html', context)


@login_required
def logs_sistema(request):
    """Vista para logs del sistema"""
    
    # Filtros
    nivel = request.GET.get('nivel', '')
    categoria = request.GET.get('categoria', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Construir query base
    query = """
        SELECT id, timestamp, nivel, categoria, subcategoria, mensaje, 
               usuario_id, ip_address, metodo_http, codigo_respuesta
        FROM logs.sistema_logs
        WHERE 1=1
    """
    params = []
    
    # Aplicar filtros
    if nivel:
        query += " AND nivel = %s"
        params.append(nivel)
    
    if categoria:
        query += " AND categoria ILIKE %s"
        params.append(f'%{categoria}%')
    
    if fecha_desde:
        query += " AND DATE(timestamp) >= %s"
        params.append(fecha_desde)
    
    if fecha_hasta:
        query += " AND DATE(timestamp) <= %s"
        params.append(fecha_hasta)
    
    query += " ORDER BY timestamp DESC"
    
    # Ejecutar query con paginación
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        logs = cursor.fetchall()
    
    # Paginación
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener categorías para filtro
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT categoria FROM logs.sistema_logs ORDER BY categoria")
        categorias = [row[0] for row in cursor.fetchall()]
    
    context = {
        'logs': page_obj,
        'categorias': categorias,
        'filtros': {
            'nivel': nivel,
            'categoria': categoria,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        },
        'parent': 'auditoria',
        'segment': 'logs_sistema'
    }
    
    return render(request, 'auditoria/logs_sistema.html', context)


@login_required
def logs_navegacion(request):
    """Vista para logs de navegación"""
    
    # Filtros
    usuario_id = request.GET.get('usuario_id', '')
    url_filtro = request.GET.get('url', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Construir query
    query = """
        SELECT id, timestamp, usuario_id, url_visitada, url_anterior, 
               metodo_http, ip_address, codigo_respuesta
        FROM logs.navegacion_usuarios
        WHERE 1=1
    """
    params = []
    
    if usuario_id:
        query += " AND usuario_id = %s"
        params.append(usuario_id)
    
    if url_filtro:
        query += " AND url_visitada ILIKE %s"
        params.append(f'%{url_filtro}%')
    
    if fecha_desde:
        query += " AND DATE(timestamp) >= %s"
        params.append(fecha_desde)
    
    if fecha_hasta:
        query += " AND DATE(timestamp) <= %s"
        params.append(fecha_hasta)
    
    query += " ORDER BY timestamp DESC"
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        logs = cursor.fetchall()
    
    # Paginación
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'logs': page_obj,
        'filtros': {
            'usuario_id': usuario_id,
            'url': url_filtro,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        },
        'parent': 'auditoria',
        'segment': 'logs_navegacion'
    }
    
    return render(request, 'auditoria/logs_navegacion.html', context)


@login_required
def auditoria_cambios(request):
    """Vista para auditoría de cambios en BD"""
    
    # Filtros
    tabla = request.GET.get('tabla', '')
    operacion = request.GET.get('operacion', '')
    usuario_id = request.GET.get('usuario_id', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Construir query
    query = """
        SELECT id, timestamp, tabla, operacion, registro_id, usuario_id, 
               username, ip_address, campos_modificados
        FROM auditoria.cambios_bd
        WHERE 1=1
    """
    params = []
    
    if tabla:
        query += " AND tabla ILIKE %s"
        params.append(f'%{tabla}%')
    
    if operacion:
        query += " AND operacion = %s"
        params.append(operacion)
    
    if usuario_id:
        query += " AND usuario_id = %s"
        params.append(usuario_id)
    
    if fecha_desde:
        query += " AND DATE(timestamp) >= %s"
        params.append(fecha_desde)
    
    if fecha_hasta:
        query += " AND DATE(timestamp) <= %s"
        params.append(fecha_hasta)
    
    query += " ORDER BY timestamp DESC"
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        cambios = cursor.fetchall()
    
    # Paginación
    paginator = Paginator(cambios, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener tablas para filtro
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT tabla FROM auditoria.cambios_bd ORDER BY tabla")
        tablas = [row[0] for row in cursor.fetchall()]
    
    context = {
        'cambios': page_obj,
        'tablas': tablas,
        'filtros': {
            'tabla': tabla,
            'operacion': operacion,
            'usuario_id': usuario_id,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        },
        'parent': 'auditoria',
        'segment': 'auditoria_cambios'
    }
    
    return render(request, 'auditoria/auditoria_cambios.html', context)


@login_required
def api_estadisticas_auditoria(request):
    """API para obtener estadísticas para gráficos"""
    
    # Obtener datos de los últimos 7 días
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                DATE(timestamp) as fecha,
                COUNT(*) as total_logs
            FROM logs.sistema_logs 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(timestamp)
            ORDER BY fecha
        """)
        logs_por_dia = [{'fecha': row[0].strftime('%Y-%m-%d'), 'total': row[1]} for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT nivel, COUNT(*) as total
            FROM logs.sistema_logs 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY nivel
            ORDER BY total DESC
        """)
        logs_por_nivel = [{'nivel': row[0], 'total': row[1]} for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT categoria, COUNT(*) as total
            FROM logs.sistema_logs 
            WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY categoria
            ORDER BY total DESC
            LIMIT 10
        """)
        logs_por_categoria = [{'categoria': row[0], 'total': row[1]} for row in cursor.fetchall()]
    
    return JsonResponse({
        'logs_por_dia': logs_por_dia,
        'logs_por_nivel': logs_por_nivel,
        'logs_por_categoria': logs_por_categoria
    })


@login_required
def detalle_log(request, log_id, tipo='sistema'):
    """Vista de detalle de un log específico"""
    
    if tipo == 'sistema':
        query = "SELECT * FROM logs.sistema_logs WHERE id = %s"
    elif tipo == 'navegacion':
        query = "SELECT * FROM logs.navegacion_usuarios WHERE id = %s"
    elif tipo == 'api':
        query = "SELECT * FROM logs.api_logs WHERE id = %s"
    elif tipo == 'error':
        query = "SELECT * FROM logs.errores_sistema WHERE id = %s"
    elif tipo == 'cambio':
        query = "SELECT * FROM auditoria.cambios_bd WHERE id = %s"
    else:
        return JsonResponse({'error': 'Tipo de log no válido'}, status=400)
    
    with connection.cursor() as cursor:
        cursor.execute(query, [log_id])
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        
        if row:
            log_data = dict(zip(columns, row))
            # Convertir datetime a string para JSON
            for key, value in log_data.items():
                if isinstance(value, datetime):
                    log_data[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            
            return JsonResponse({'log': log_data})
        else:
            return JsonResponse({'error': 'Log no encontrado'}, status=404)


def obtener_ultimos_eventos_sistema(limit=5):
    """
    Obtiene los últimos eventos del sistema combinando múltiples fuentes
    """
    eventos = []
    
    try:
        with connection.cursor() as cursor:
            # Primero obtener eventos de Celery
            try:
                cursor.execute("""
                    SELECT 
                        task_name,
                        estado,
                        timestamp,
                        duracion_segundos
                    FROM logs.celery_logs 
                    WHERE task_name LIKE '%%audio%%' OR task_name LIKE '%%transcr%%'
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, [limit])
                
                celery_rows = cursor.fetchall()
                for row in celery_rows:
                    task_name, estado, timestamp, duracion = row
                    
                    tipo_tarea = "Audio" if "audio" in task_name.lower() else "Transcripción"
                    estado_icon = {
                        'SUCCESS': 'fas fa-check-circle text-success',
                        'FAILURE': 'fas fa-times-circle text-danger', 
                        'PENDING': 'fas fa-clock text-warning',
                        'STARTED': 'fas fa-play-circle text-info'
                    }.get(estado, 'fas fa-question-circle text-muted')
                    
                    eventos.append({
                        'tipo': 'celery',
                        'icono': estado_icon,
                        'titulo': f"{tipo_tarea} - {estado}",
                        'descripcion': f"Tarea: {task_name.split('.')[-1]}",
                        'timestamp': timestamp,
                        'tiempo_hace': tiempo_relativo(timestamp),
                        'metadata': {
                            'duracion_s': duracion
                        }
                    })
            except Exception:
                pass
            
            # Obtener archivos recientes (si existen)
            try:
                cursor.execute("""
                    SELECT 
                        operacion,
                        archivo_nombre,
                        timestamp,
                        resultado
                    FROM logs.archivo_logs 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, [limit])
                
                archivo_rows = cursor.fetchall()
                for row in archivo_rows:
                    operacion, nombre, timestamp, resultado = row
                    
                    icono = 'fas fa-upload text-primary' if operacion == 'UPLOAD' else 'fas fa-download text-info'
                    if resultado == 'ERROR':
                        icono = 'fas fa-exclamation-triangle text-danger'
                    
                    eventos.append({
                        'tipo': 'archivo',
                        'icono': icono,
                        'titulo': f"{operacion.title()} - {nombre[:30]}{'...' if len(nombre) > 30 else ''}",
                        'descripcion': f"Resultado: {resultado}",
                        'timestamp': timestamp,
                        'tiempo_hace': tiempo_relativo(timestamp),
                        'metadata': {
                            'resultado': resultado
                        }
                    })
            except Exception:
                pass
            
            # Obtener actividad del sistema general
            try:
                cursor.execute("""
                    SELECT 
                        categoria,
                        subcategoria,
                        mensaje,
                        timestamp,
                        nivel
                    FROM logs.sistema_logs 
                    WHERE categoria IN ('admin', 'api', 'auth', 'celery')
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, [limit])
                
                sistema_rows = cursor.fetchall()
                for row in sistema_rows:
                    categoria, subcategoria, mensaje, timestamp, nivel = row
                    
                    icono_map = {
                        'admin': 'fas fa-user-shield text-primary',
                        'api': 'fas fa-code text-info',
                        'auth': 'fas fa-sign-in-alt text-success',
                        'celery': 'fas fa-cogs text-warning'
                    }
                    
                    icono = icono_map.get(categoria, 'fas fa-info-circle text-muted')
                    if nivel in ['ERROR', 'CRITICAL']:
                        icono = 'fas fa-exclamation-triangle text-danger'
                    
                    eventos.append({
                        'tipo': 'sistema',
                        'icono': icono,
                        'titulo': f"{categoria.title()} - {subcategoria or 'Actividad'}",
                        'descripcion': f"{mensaje[:50]}..." if len(mensaje) > 50 else mensaje,
                        'timestamp': timestamp,
                        'tiempo_hace': tiempo_relativo(timestamp),
                        'metadata': {
                            'nivel': nivel
                        }
                    })
            except Exception:
                pass
            
            # Obtener algunos errores críticos si no hay mucha actividad
            if len(eventos) < limit:
                try:
                    cursor.execute("""
                        SELECT 
                            nivel_error,
                            mensaje_error,
                            timestamp,
                            resuelto
                        FROM logs.errores_sistema 
                        WHERE nivel_error IN ('ERROR', 'CRITICAL')
                        ORDER BY timestamp DESC 
                        LIMIT %s
                    """, [limit - len(eventos)])
                    
                    error_rows = cursor.fetchall()
                    for row in error_rows:
                        nivel, mensaje, timestamp, resuelto = row
                        
                        icono = 'fas fa-bug text-danger' if nivel == 'ERROR' else 'fas fa-skull text-danger'
                        if resuelto:
                            icono = 'fas fa-check-circle text-success'
                        
                        eventos.append({
                            'tipo': 'error',
                            'icono': icono,
                            'titulo': f"{nivel}: Error del sistema",
                            'descripcion': f"{mensaje[:50]}..." if len(mensaje) > 50 else mensaje,
                            'timestamp': timestamp,
                            'tiempo_hace': tiempo_relativo(timestamp),
                            'metadata': {
                                'resuelto': resuelto
                            }
                        })
                except Exception:
                    pass
                
    except Exception as e:
        # En caso de error, devolver lista vacía pero con un evento de error
        eventos = [{
            'tipo': 'system',
            'icono': 'fas fa-exclamation-triangle text-warning',
            'titulo': 'Sistema de monitoreo',
            'descripcion': 'No se pudieron cargar los eventos recientes',
            'timestamp': datetime.now(),
            'tiempo_hace': 'ahora',
            'metadata': {'error': str(e)}
        }]
    
    # Si no hay eventos, agregar un evento indicando sistema funcionando
    if not eventos:
        eventos = [{
            'tipo': 'system',
            'icono': 'fas fa-check-circle text-success',
            'titulo': 'Sistema funcionando',
            'descripcion': 'No hay actividad reciente para mostrar',
            'timestamp': datetime.now(),
            'tiempo_hace': 'ahora',
            'metadata': {}
        }]
    
    # Ordenar todos los eventos por timestamp y tomar los más recientes
    try:
        eventos.sort(key=lambda x: x['timestamp'], reverse=True)
    except:
        pass
        
    return eventos[:limit]


def tiempo_relativo(timestamp):
    """Convierte un timestamp a tiempo relativo (ej: 'hace 2 horas')"""
    if not timestamp:
        return "Desconocido"
    
    ahora = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
    diferencia = ahora - timestamp
    
    if diferencia.days > 0:
        return f"hace {diferencia.days} día{'s' if diferencia.days != 1 else ''}"
    elif diferencia.seconds > 3600:
        horas = diferencia.seconds // 3600
        return f"hace {horas} hora{'s' if horas != 1 else ''}"
    elif diferencia.seconds > 60:
        minutos = diferencia.seconds // 60
        return f"hace {minutos} minuto{'s' if minutos != 1 else ''}"
    else:
        return "hace un momento"


@login_required
def api_ultimos_eventos(request):
    """API endpoint para obtener los últimos eventos del sistema"""
    limit = int(request.GET.get('limit', 5))
    eventos = obtener_ultimos_eventos_sistema(limit)
    
    # Convertir datetime a string para JSON
    for evento in eventos:
        if isinstance(evento['timestamp'], datetime):
            evento['timestamp'] = evento['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    
    return JsonResponse({
        'eventos': eventos,
        'total': len(eventos),
        'timestamp_consulta': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


@login_required
def eventos_tiempo_real(request):
    """Vista para mostrar eventos del sistema en tiempo real"""
    limit = int(request.GET.get('limit', 20))
    eventos = obtener_ultimos_eventos_sistema(limit)
    
    context = {
        'eventos': eventos,
        'total_eventos': len(eventos),
        'parent': 'auditoria',
        'segment': 'eventos'
    }
    
    return render(request, 'auditoria/eventos_tiempo_real.html', context)
