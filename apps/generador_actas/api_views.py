"""
API views para operaciones AJAX y monitoreo en tiempo real
"""
import json
import logging
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ActaGenerada, ProveedorIA, PlantillaActa, SegmentoPlantilla
from .services import GeneradorActasService, EstadisticasService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def api_procesar_acta(request, acta_id):
    """
    API endpoint para iniciar procesamiento de acta
    """
    try:
        acta = get_object_or_404(ActaGenerada, id=acta_id)
        
        # Verificar permisos básicos
        if not acta.puede_procesar:
            return JsonResponse({
                'success': False,
                'message': f'El acta está en estado {acta.estado} y no puede ser procesada',
                'estado_actual': acta.estado
            })
        
        # Iniciar procesamiento asíncrono
        task_id = GeneradorActasService.procesar_acta_asincrono(acta)
        
        return JsonResponse({
            'success': True,
            'message': 'Procesamiento iniciado exitosamente',
            'task_id': task_id,
            'acta_id': acta.id,
            'numero_acta': acta.numero_acta
        })
        
    except ValidationError as e:
        logger.warning(f"Error de validación procesando acta {acta_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e),
            'error_type': 'validation'
        })
    except Exception as e:
        logger.error(f"Error inesperado procesando acta {acta_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error interno del servidor: {str(e)}',
            'error_type': 'server'
        })


@login_required
def api_estado_acta(request, acta_id):
    """
    API endpoint para consultar estado de procesamiento de acta
    """
    try:
        acta = get_object_or_404(ActaGenerada, id=acta_id)
        estado_info = GeneradorActasService.obtener_estado_procesamiento(acta)
        
        return JsonResponse({
            'success': True,
            'data': estado_info,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado de acta {acta_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_estados_multiple(request):
    """
    API endpoint para consultar estados de múltiples actas
    """
    try:
        # Obtener IDs de actas desde query params o POST data
        if request.method == 'GET':
            acta_ids = request.GET.get('ids', '').split(',')
        else:
            data = json.loads(request.body)
            acta_ids = data.get('acta_ids', [])
        
        # Filtrar IDs válidos
        acta_ids = [int(id_) for id_ in acta_ids if id_.strip().isdigit()]
        
        if not acta_ids:
            return JsonResponse({
                'success': False,
                'message': 'No se proporcionaron IDs válidos de actas'
            })
        
        # Obtener estados
        estados = {}
        for acta_id in acta_ids:
            try:
                acta = ActaGenerada.objects.get(id=acta_id)
                estados[acta_id] = {
                    'estado': acta.estado,
                    'progreso': acta.progreso,
                    'puede_procesar': acta.puede_procesar,
                    'tiene_contenido': bool(acta.contenido_final or acta.contenido_borrador),
                    'mensajes_error': acta.mensajes_error
                }
            except ActaGenerada.DoesNotExist:
                estados[acta_id] = {'error': 'Acta no encontrada'}
        
        return JsonResponse({
            'success': True,
            'data': estados,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estados múltiples: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_dashboard_stats(request):
    """
    API endpoint para estadísticas del dashboard
    """
    try:
        stats = EstadisticasService.obtener_resumen_dashboard()
        
        # Agregar información adicional
        stats['timestamp'] = timezone.now().isoformat()
        stats['usuario'] = request.user.username
        
        return JsonResponse({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas dashboard: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_plantillas_compatibles(request, transcripcion_id):
    """
    API endpoint para obtener plantillas compatibles con una transcripción
    """
    try:
        from apps.transcripcion.models import Transcripcion
        
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        plantillas = GeneradorActasService.obtener_plantillas_compatibles(transcripcion)
        
        plantillas_data = []
        for plantilla in plantillas:
            plantillas_data.append({
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'descripcion': plantilla.descripcion,
                'tipo_acta': plantilla.tipo_acta,
                'tipo_acta_display': plantilla.get_tipo_acta_display(),
                'segmentos_count': plantilla.configuracionsegmento_set.count(),
                'activa': plantilla.activa
            })
        
        return JsonResponse({
            'success': True,
            'data': plantillas_data,
            'count': len(plantillas_data)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo plantillas compatibles: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_validar_transcripcion(request, transcripcion_id):
    """
    API endpoint para validar si una transcripción puede generar actas
    """
    try:
        from apps.transcripcion.models import Transcripcion
        
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        es_valida, errores = GeneradorActasService.validar_transcripcion_para_acta(transcripcion)
        
        # Información adicional de la transcripción
        info_transcripcion = {
            'id': transcripcion.id,
            'fecha_creacion': transcripcion.fecha_creacion.isoformat(),
            'tiene_conversacion': bool(transcripcion.conversacion_json),
            'segmentos_count': len(transcripcion.conversacion_json.get('conversacion', [])) if transcripcion.conversacion_json else 0
        }
        
        if hasattr(transcripcion, 'procesamiento_audio'):
            audio = transcripcion.procesamiento_audio
            info_transcripcion.update({
                'nombre_archivo': audio.nombre_archivo,
                'duracion_segundos': audio.duracion_segundos,
                'tipo_reunion': audio.tipo_reunion.nombre if audio.tipo_reunion else None,
                'ubicacion': audio.ubicacion
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'es_valida': es_valida,
                'errores': errores,
                'transcripcion': info_transcripcion
            }
        })
        
    except Exception as e:
        logger.error(f"Error validando transcripción {transcripcion_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_segmentos_plantilla(request, plantilla_id):
    """
    API endpoint para obtener segmentos configurados de una plantilla
    """
    try:
        plantilla = get_object_or_404(PlantillaActa, id=plantilla_id)
        
        configuraciones = plantilla.configuracionsegmento_set.select_related(
            'segmento'
        ).order_by('orden')
        
        segmentos_data = []
        for config in configuraciones:
            segmentos_data.append({
                'id': config.id,
                'orden': config.orden,
                'activo': config.activo,
                'segmento': {
                    'id': config.segmento.id,
                    'nombre': config.segmento.nombre,
                    'descripcion': config.segmento.descripcion,
                    'categoria': config.segmento.categoria,
                    'es_dinamico': config.segmento.es_dinamico,
                    'tipo': 'dinamico' if config.segmento.es_dinamico else 'estatico'
                },
                'prompt_override': config.prompt_override,
                'parametros_override': config.parametros_override,
                'prompt_efectivo': config.prompt_efectivo[:200] + '...' if config.prompt_efectivo and len(config.prompt_efectivo) > 200 else config.prompt_efectivo
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'plantilla': {
                    'id': plantilla.id,
                    'nombre': plantilla.nombre,
                    'tipo_acta': plantilla.tipo_acta,
                    'prompt_global': plantilla.prompt_global[:200] + '...' if plantilla.prompt_global and len(plantilla.prompt_global) > 200 else plantilla.prompt_global
                },
                'segmentos': segmentos_data,
                'count': len(segmentos_data)
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo segmentos de plantilla {plantilla_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_probar_proveedor_ia(request, proveedor_id):
    """
    API endpoint para probar conexión con proveedor IA
    """
    try:
        proveedor = get_object_or_404(ProveedorIA, id=proveedor_id)
        
        # Probar conexión
        from .ia_providers import get_ia_provider
        
        try:
            ia_provider = get_ia_provider(proveedor)
            es_valido = ia_provider.validar_configuracion()
            
            if es_valido:
                # Probar con prompt simple
                prompt_test = "Responde únicamente 'OK' si puedes procesar este mensaje."
                contexto_test = {'test': True}
                
                respuesta = ia_provider.procesar_prompt(prompt_test, contexto_test)
                
                return JsonResponse({
                    'success': True,
                    'data': {
                        'conexion_valida': True,
                        'respuesta_test': respuesta[:100] + '...' if len(respuesta) > 100 else respuesta,
                        'proveedor': proveedor.nombre,
                        'tipo': proveedor.get_tipo_proveedor_display()
                    },
                    'message': 'Conexión exitosa con el proveedor IA'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'La configuración del proveedor no es válida',
                    'data': {
                        'conexion_valida': False,
                        'proveedor': proveedor.nombre
                    }
                })
                
        except Exception as provider_error:
            return JsonResponse({
                'success': False,
                'message': f'Error conectando con {proveedor.nombre}: {str(provider_error)}',
                'data': {
                    'conexion_valida': False,
                    'error_detalle': str(provider_error)
                }
            })
        
    except Exception as e:
        logger.error(f"Error probando proveedor IA {proveedor_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_previsualizar_contenido(request, acta_id):
    """
    API endpoint para previsualizar contenido de acta
    """
    try:
        acta = get_object_or_404(ActaGenerada, id=acta_id)
        
        # Determinar qué contenido mostrar
        contenido = acta.contenido_final or acta.contenido_borrador
        
        if not contenido:
            return JsonResponse({
                'success': False,
                'message': 'El acta no tiene contenido disponible para previsualizar'
            })
        
        # Información adicional
        info_contenido = {
            'tiene_contenido_final': bool(acta.contenido_final),
            'tiene_contenido_borrador': bool(acta.contenido_borrador),
            'longitud_caracteres': len(contenido),
            'longitud_palabras': len(contenido.split()),
            'lineas': len(contenido.split('\n')),
            'estado_acta': acta.estado,
            'fecha_actualizacion': acta.fecha_actualizacion.isoformat()
        }
        
        return JsonResponse({
            'success': True,
            'data': {
                'contenido': contenido,
                'info': info_contenido,
                'preview': contenido[:500] + '...' if len(contenido) > 500 else contenido
            }
        })
        
    except Exception as e:
        logger.error(f"Error previsualizando contenido de acta {acta_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_actividad_reciente(request):
    """
    API endpoint para obtener actividad reciente del sistema
    """
    try:
        # Parámetros de consulta
        limit = min(int(request.GET.get('limit', 10)), 50)  # Máximo 50
        horas = int(request.GET.get('horas', 24))  # Últimas 24 horas por defecto
        
        fecha_limite = timezone.now() - timedelta(hours=horas)
        
        # Actas recientes
        actas_recientes = ActaGenerada.objects.filter(
            fecha_creacion__gte=fecha_limite
        ).select_related(
            'usuario_creacion', 'plantilla', 'proveedor_ia'
        ).order_by('-fecha_creacion')[:limit]
        
        actividad = []
        for acta in actas_recientes:
            actividad.append({
                'tipo': 'acta_creada',
                'acta_id': acta.id,
                'numero_acta': acta.numero_acta,
                'titulo': acta.titulo,
                'estado': acta.estado,
                'usuario': acta.usuario_creacion.get_full_name() or acta.usuario_creacion.username,
                'fecha': acta.fecha_creacion.isoformat(),
                'plantilla': acta.plantilla.nombre,
                'proveedor_ia': acta.proveedor_ia.nombre
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'actividad': actividad,
                'count': len(actividad),
                'periodo_horas': horas,
                'fecha_consulta': timezone.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo actividad reciente: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_cancelar_procesamiento(request, acta_id):
    """
    API endpoint para cancelar procesamiento de acta
    """
    try:
        acta = get_object_or_404(ActaGenerada, id=acta_id)
        
        # Verificar que se puede cancelar
        if acta.estado not in ['en_cola', 'procesando', 'procesando_segmentos', 'unificando']:
            return JsonResponse({
                'success': False,
                'message': f'No se puede cancelar el procesamiento en estado {acta.estado}'
            })
        
        # Intentar cancelar tarea de Celery si existe
        if acta.task_id_celery:
            try:
                from celery.result import AsyncResult
                task_result = AsyncResult(acta.task_id_celery)
                task_result.revoke(terminate=True)
            except Exception as celery_error:
                logger.warning(f"Error cancelando tarea Celery: {celery_error}")
        
        # Actualizar estado del acta
        acta.estado = 'borrador'
        acta.progreso = 0
        acta.task_id_celery = None
        acta.mensajes_error = f"Procesamiento cancelado por {request.user.username}"
        acta.save()
        
        # Agregar al historial
        acta.agregar_historial(
            'procesamiento_cancelado',
            request.user,
            {'motivo': 'cancelacion_manual'}
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Procesamiento cancelado exitosamente',
            'estado_nuevo': acta.estado
        })
        
    except Exception as e:
        logger.error(f"Error cancelando procesamiento de acta {acta_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def api_sistema_salud(request):
    """
    API endpoint para verificar salud del sistema de generación de actas
    """
    try:
        salud = {
            'timestamp': timezone.now().isoformat(),
            'componentes': {}
        }
        
        # Verificar base de datos
        try:
            total_actas = ActaGenerada.objects.count()
            salud['componentes']['base_datos'] = {
                'estado': 'ok',
                'total_actas': total_actas
            }
        except Exception as db_error:
            salud['componentes']['base_datos'] = {
                'estado': 'error',
                'error': str(db_error)
            }
        
        # Verificar proveedores IA activos
        try:
            proveedores_activos = ProveedorIA.objects.filter(activo=True).count()
            salud['componentes']['proveedores_ia'] = {
                'estado': 'ok' if proveedores_activos > 0 else 'warning',
                'proveedores_activos': proveedores_activos
            }
        except Exception as provider_error:
            salud['componentes']['proveedores_ia'] = {
                'estado': 'error',
                'error': str(provider_error)
            }
        
        # Verificar plantillas activas
        try:
            plantillas_activas = PlantillaActa.objects.filter(activa=True).count()
            salud['componentes']['plantillas'] = {
                'estado': 'ok' if plantillas_activas > 0 else 'warning',
                'plantillas_activas': plantillas_activas
            }
        except Exception as template_error:
            salud['componentes']['plantillas'] = {
                'estado': 'error',
                'error': str(template_error)
            }
        
        # Verificar Celery (opcional)
        try:
            from celery import current_app
            inspector = current_app.control.inspect()
            workers = inspector.active()
            
            if workers:
                salud['componentes']['celery'] = {
                    'estado': 'ok',
                    'workers_activos': len(workers)
                }
            else:
                salud['componentes']['celery'] = {
                    'estado': 'warning',
                    'mensaje': 'No se detectaron workers activos'
                }
        except Exception:
            salud['componentes']['celery'] = {
                'estado': 'desconocido',
                'mensaje': 'No se pudo verificar estado de Celery'
            }
        
        # Estado general
        estados = [comp['estado'] for comp in salud['componentes'].values()]
        if 'error' in estados:
            salud['estado_general'] = 'error'
        elif 'warning' in estados:
            salud['estado_general'] = 'warning'
        else:
            salud['estado_general'] = 'ok'
        
        return JsonResponse({
            'success': True,
            'data': salud
        })
        
    except Exception as e:
        logger.error(f"Error verificando salud del sistema: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# =============================================
# APIS PARA OPERACIONES DEL SISTEMA
# =============================================

@login_required
@require_http_methods(["POST"])
def api_iniciar_operacion(request):
    """
    API para iniciar una operación del sistema
    """
    try:
        from .models import OperacionSistema
        from .tasks import (
            crear_backup_sistema, exportar_configuraciones, 
            reiniciar_servicios_sistema, probar_proveedores_ia
        )
        
        data = json.loads(request.body)
        tipo_operacion = data.get('tipo')
        parametros = data.get('parametros', {})
        
        if not tipo_operacion:
            return JsonResponse({
                'success': False,
                'message': 'Tipo de operación requerido'
            })
        
        # Crear registro de operación
        operacion = OperacionSistema.objects.create(
            tipo=tipo_operacion,
            titulo=_get_titulo_operacion(tipo_operacion),
            descripcion=_get_descripcion_operacion(tipo_operacion, parametros),
            parametros_entrada=parametros,
            usuario=request.user,
            estado='pending'
        )
        
        # Iniciar tarea según el tipo
        task = None
        if tipo_operacion == 'backup_sistema':
            task = crear_backup_sistema.delay(
                str(operacion.id),
                parametros.get('incluir_media', True),
                parametros.get('incluir_logs', False)
            )
        elif tipo_operacion == 'exportar_configuraciones':
            task = exportar_configuraciones.delay(
                str(operacion.id),
                parametros.get('formato', 'json'),
                parametros.get('incluir_sensibles', False)
            )
        elif tipo_operacion == 'reiniciar_servicios':
            task = reiniciar_servicios_sistema.delay(
                str(operacion.id),
                parametros.get('servicios', ['celery', 'redis'])
            )
        elif tipo_operacion == 'probar_proveedores':
            task = probar_proveedores_ia.delay(
                str(operacion.id),
                parametros.get('proveedor_ids', None)
            )
        else:
            operacion.marcar_fallido(f'Tipo de operación no soportado: {tipo_operacion}')
            return JsonResponse({
                'success': False,
                'message': f'Tipo de operación no soportado: {tipo_operacion}'
            })
        
        # Actualizar con task ID
        if task:
            operacion.task_id = task.id
            operacion.estado = 'queued'
            operacion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Operación iniciada exitosamente',
            'operacion_id': str(operacion.id),
            'task_id': task.id if task else None,
            'tipo': tipo_operacion
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido en el cuerpo de la petición'
        })
    except Exception as e:
        logger.error(f"Error iniciando operación: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error interno: {str(e)}'
        })


@login_required
@require_http_methods(["GET"])
def api_estado_operacion(request, operacion_id):
    """
    API para consultar el estado de una operación
    """
    try:
        from .models import OperacionSistema
        
        operacion = get_object_or_404(OperacionSistema, id=operacion_id)
        
        # Verificar permisos (usuario debe ser el dueño o admin)
        if operacion.usuario != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'message': 'Sin permisos para consultar esta operación'
            })
        
        # Preparar datos de respuesta
        data = {
            'id': str(operacion.id),
            'tipo': operacion.tipo,
            'titulo': operacion.titulo,
            'estado': operacion.estado,
            'progreso': operacion.progreso,
            'mensaje_estado': operacion.mensaje_estado,
            'fecha_inicio': operacion.fecha_inicio.isoformat() if operacion.fecha_inicio else None,
            'fecha_finalizacion': operacion.fecha_finalizacion.isoformat() if operacion.fecha_finalizacion else None,
            'duracion_segundos': operacion.duracion_segundos,
            'logs_recientes': operacion.logs[-10:] if operacion.logs else [],
            'tiene_archivo': bool(operacion.archivo_resultado and operacion.archivo_resultado.name),
            'resultado_disponible': operacion.estado == 'completed' and operacion.resultado_json
        }
        
        # Información adicional si está completado
        if operacion.estado == 'completed' and operacion.resultado_json:
            data['resultado_resumen'] = {
                'elementos_procesados': operacion.resultado_json.get('elementos_procesados', 0),
                'tamaño_archivo': operacion.resultado_json.get('tamaño_mb', 0),
                'formato': operacion.resultado_json.get('formato', 'N/A')
            }
        
        return JsonResponse({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error consultando estado de operación {operacion_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_descargar_resultado(request, operacion_id):
    """
    API para descargar el archivo resultado de una operación
    """
    try:
        from .models import OperacionSistema
        from django.http import HttpResponse, Http404
        
        operacion = get_object_or_404(OperacionSistema, id=operacion_id)
        
        # Verificar permisos
        if operacion.usuario != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'message': 'Sin permisos para descargar este archivo'
            })
        
        # Verificar que tiene archivo
        if not operacion.archivo_resultado or not operacion.archivo_resultado.name:
            raise Http404("El archivo no existe o la operación no generó resultados")
        
        # Preparar respuesta de descarga
        try:
            response = HttpResponse(operacion.archivo_resultado.read())
            filename = operacion.archivo_resultado.name.split('/')[-1]
            
            # Determinar content type
            if filename.endswith('.zip'):
                response['Content-Type'] = 'application/zip'
            elif filename.endswith('.json'):
                response['Content-Type'] = 'application/json'
            elif filename.endswith('.yaml'):
                response['Content-Type'] = 'application/x-yaml'
            elif filename.endswith('.html'):
                response['Content-Type'] = 'text/html'
            else:
                response['Content-Type'] = 'application/octet-stream'
            
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            logger.error(f"Error leyendo archivo resultado: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Error accediendo al archivo'
            })
        
    except Exception as e:
        logger.error(f"Error descargando resultado {operacion_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["POST"])
def api_cancelar_operacion(request, operacion_id):
    """
    API para cancelar una operación en curso
    """
    try:
        from .models import OperacionSistema
        from celery import current_app
        
        operacion = get_object_or_404(OperacionSistema, id=operacion_id)
        
        # Verificar permisos
        if operacion.usuario != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'message': 'Sin permisos para cancelar esta operación'
            })
        
        # Solo se pueden cancelar operaciones en ciertos estados
        if operacion.estado not in ['pending', 'queued', 'running']:
            return JsonResponse({
                'success': False,
                'message': f'No se puede cancelar una operación en estado {operacion.estado}'
            })
        
        # Intentar cancelar tarea de Celery
        cancelado = False
        if operacion.task_id:
            try:
                current_app.control.revoke(operacion.task_id, terminate=True)
                cancelado = True
            except Exception as e:
                logger.warning(f"No se pudo cancelar tarea Celery {operacion.task_id}: {str(e)}")
        
        # Marcar operación como cancelada
        operacion.estado = 'cancelled'
        operacion.fecha_finalizacion = timezone.now()
        operacion.mensaje_estado = 'Operación cancelada por el usuario'
        operacion.agregar_log('info', 'Operación cancelada por solicitud del usuario')
        operacion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Operación cancelada exitosamente',
            'task_cancelado': cancelado
        })
        
    except Exception as e:
        logger.error(f"Error cancelando operación {operacion_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_listar_operaciones(request):
    """
    API para listar operaciones del usuario
    """
    try:
        from .models import OperacionSistema
        
        # Parámetros de consulta
        estado = request.GET.get('estado', None)
        tipo = request.GET.get('tipo', None)
        limite = int(request.GET.get('limite', 20))
        offset = int(request.GET.get('offset', 0))
        
        # Filtros base
        queryset = OperacionSistema.objects.filter(usuario=request.user)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Ordenar por más reciente
        queryset = queryset.order_by('-fecha_inicio')
        
        # Contar total
        total = queryset.count()
        
        # Aplicar paginación
        operaciones = queryset[offset:offset + limite]
        
        # Serializar resultados
        data = []
        for op in operaciones:
            data.append({
                'id': str(op.id),
                'tipo': op.tipo,
                'titulo': op.titulo,
                'estado': op.estado,
                'progreso': op.progreso,
                'mensaje_estado': op.mensaje_estado,
                'fecha_inicio': op.fecha_inicio.isoformat() if op.fecha_inicio else None,
                'fecha_finalizacion': op.fecha_finalizacion.isoformat() if op.fecha_finalizacion else None,
                'duracion_segundos': op.duracion_segundos,
                'tiene_archivo': bool(op.archivo_resultado and op.archivo_resultado.name)
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'total': total,
            'limite': limite,
            'offset': offset,
            'tiene_mas': (offset + limite) < total
        })
        
    except Exception as e:
        logger.error(f"Error listando operaciones: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


# =============================================
# FUNCIONES AUXILIARES
# =============================================

def _get_titulo_operacion(tipo):
    """Retorna el título legible para un tipo de operación"""
    titulos = {
        'backup_sistema': 'Backup del Sistema',
        'exportar_configuraciones': 'Exportar Configuraciones',
        'reiniciar_servicios': 'Reiniciar Servicios',
        'probar_proveedores': 'Probar Proveedores IA',
        'generar_preview': 'Vista Previa de Plantilla',
        'exportar_plantilla': 'Exportar Plantilla',
        'reset_configuraciones': 'Restablecer Configuraciones'
    }
    return titulos.get(tipo, f'Operación {tipo}')


def _get_descripcion_operacion(tipo, parametros):
    """Genera una descripción detallada de la operación"""
    descripciones = {
        'backup_sistema': f"Backup completo del sistema. Incluye media: {parametros.get('incluir_media', True)}, logs: {parametros.get('incluir_logs', False)}",
        'exportar_configuraciones': f"Exportar configuraciones en formato {parametros.get('formato', 'json')}. Datos sensibles: {parametros.get('incluir_sensibles', False)}",
        'reiniciar_servicios': f"Reiniciar servicios: {', '.join(parametros.get('servicios', ['celery', 'redis']))}",
        'probar_proveedores': f"Probar conectividad de proveedores IA",
        'generar_preview': f"Generar vista previa de plantilla",
        'exportar_plantilla': f"Exportar plantilla del sistema",
        'reset_configuraciones': f"Restablecer configuraciones a valores por defecto"
    }
    return descripciones.get(tipo, f'Ejecutar operación {tipo} con parámetros: {parametros}')


@login_required
def api_segmentos_disponibles(request):
    """
    API endpoint para obtener segmentos disponibles para agregar a plantillas
    """
    try:
        segmentos = SegmentoPlantilla.objects.filter(
            activo=True
        ).order_by('categoria', 'nombre')
        
        segmentos_data = []
        for segmento in segmentos:
            segmentos_data.append({
                'id': segmento.id,
                'nombre': segmento.nombre,
                'codigo': segmento.codigo,
                'descripcion': segmento.descripcion,
                'categoria': segmento.categoria,
                'tipo': segmento.tipo,
                'formato_salida': segmento.formato_salida,
                'requiere_proveedor_ia': segmento.tipo in ['dinamico', 'hibrido'],
                'categoria_display': segmento.get_categoria_display(),
                'tipo_display': segmento.get_tipo_display()
            })
        
        return JsonResponse({
            'success': True,
            'segmentos': segmentos_data,
            'total': len(segmentos_data)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo segmentos disponibles: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Error al cargar segmentos disponibles'
        })