from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import os
import mimetypes
import os
import logging
import traceback

from .models import ProcesamientoAudio, TipoReunion, LogProcesamiento
from .forms import SubirAudioForm, TipoReunionForm, FiltroProcesamientoForm, ConfiguracionProcesamientoForm, EditarProcesamientoForm
from .logging_helper import (
    log_sistema, log_navegacion, log_admin_action, log_archivo_operacion,
    log_procesamiento_audio, log_error_procesamiento
)

logger = logging.getLogger(__name__)


@login_required
def centro_audio(request):
    """Vista principal unificada para centro_audio_new.html"""
    from django.db.models import Count, Q
    
    # Tipos de reunión para el selector
    tipos_reunion = TipoReunion.objects.filter(activo=True)
    
    if request.user.is_authenticated:
        # Estadísticas del usuario autenticado
        user_procesamientos = ProcesamientoAudio.objects.filter(usuario=request.user)
        stats = user_procesamientos.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(estado='completado')),
            processing=Count('id', filter=Q(estado__in=['pendiente', 'procesando', 'transcribiendo'])),
            error=Count('id', filter=Q(estado='error')),
        )
        # Procesos recientes (últimos 5)
        recent_processes = user_procesamientos.order_by('-created_at')[:5]
        es_demo = False
    else:
        # Modo demo para usuarios no autenticados
        stats = {
            'total': 0,
            'completed': 0, 
            'processing': 0,
            'error': 0,
        }
        recent_processes = []
        es_demo = True

    context = {
        'title': 'Centro de Audio',
        'stats': stats,
        'recent_processes': recent_processes,
        'tipos_reunion': tipos_reunion,
        'es_demo': es_demo,
    }
    return render(request, 'audio_processing/centro_audio_new.html', context)


# (El API legacy de procesamiento ha sido retirado en favor de la nueva versión compatible con centro_audio_new)


# (API duplicada de estado eliminada; se mantiene una única implementación más abajo)


# Vista de lista de procesamientos
@login_required
def lista_procesamientos(request):
    """Lista paginada de procesamientos de audio con filtros completos"""
    # Debug: información del usuario actual
    logger.info(f"Lista procesamientos - Usuario: {request.user}, Autenticado: {request.user.is_authenticated}")
    
    # Log del acceso a la lista
    log_navegacion(
        request=request,
        accion_realizada='listar_procesamientos',
        elemento_interactuado='lista_procesamientos'
    )
    
    
    form = FiltroProcesamientoForm(request.GET)
    procesamientos = ProcesamientoAudio.objects.filter(usuario=request.user)    # Aplicar filtros de búsqueda
    titulo = request.GET.get('titulo', '').strip()
    tipo_reunion = request.GET.get('tipo_reunion', '')
    estado = request.GET.get('estado', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    orden = request.GET.get('orden', '-created_at')
    
    if titulo:
        procesamientos = procesamientos.filter(titulo__icontains=titulo)
    
    if tipo_reunion:
        procesamientos = procesamientos.filter(tipo_reunion_id=tipo_reunion)
    
    if estado:
        procesamientos = procesamientos.filter(estado=estado)
    
    if fecha_desde:
        from datetime import datetime
        try:
            fecha_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            procesamientos = procesamientos.filter(created_at__date__gte=fecha_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        from datetime import datetime
        try:
            fecha_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            procesamientos = procesamientos.filter(created_at__date__lte=fecha_obj)
        except ValueError:
            pass
    
    # Aplicar ordenación
    orden_valido = [
        '-created_at', 'created_at', '-fecha_reunion', 'fecha_reunion',
        'titulo', '-titulo', 'tipo_reunion', '-tipo_reunion',
        'estado', '-estado', '-duracion', 'duracion'
    ]
    if orden in orden_valido:
        procesamientos = procesamientos.order_by(orden)
    else:
        procesamientos = procesamientos.order_by('-created_at')
    
    # Agregar select_related para mejorar rendimiento
    procesamientos = procesamientos.select_related('tipo_reunion')
    
    # Contar total antes de paginar
    total_procesamientos = procesamientos.count()
    
    # Debug: cantidad de procesamientos encontrados
    logger.info(f"Procesamientos encontrados para {request.user}: {total_procesamientos}")
    
    # Paginación
    paginator = Paginator(procesamientos, 12)  # Grid 3x4
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener tipos de reunión para el formulario
    tipos_reunion = TipoReunion.objects.filter(activo=True)
    
    # Log del listado exitoso
    log_sistema(
        nivel='INFO',
        categoria='PROCESAMIENTO_LISTADO',
        subcategoria='LISTADO_EXITOSO',
        mensaje=f"Usuario listó {total_procesamientos} procesamientos",
        request=request,
        datos_extra={
            'total_procesamientos': total_procesamientos,
            'filtros_aplicados': {
                'titulo': titulo,
                'tipo_reunion': tipo_reunion,
                'estado': estado,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'orden': orden
            },
            'pagina': page_number or 1,
            'items_por_pagina': 12
        }
    )
    
    context = {
        'title': 'Lista de Procesamientos de Audio',
        'page_obj': page_obj,
        'form': form,
        'total_procesamientos': total_procesamientos,
        'tipos_reunion': tipos_reunion,
        'orden_actual': orden,
        # Pasar valores actuales para mantener en formulario
        'titulo_actual': titulo,
        'tipo_reunion_actual': tipo_reunion,
        'estado_actual': estado,
        'fecha_desde_actual': fecha_desde,
        'fecha_hasta_actual': fecha_hasta,
    }
    
    return render(request, 'audio_processing/lista_procesamientos.html', context)


@login_required
def detalle_procesamiento(request, id):
    """Vista de detalle de un procesamiento específico"""
    try:
        procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
        logs = LogProcesamiento.objects.filter(procesamiento=procesamiento).order_by('-timestamp')
        
        # Log del acceso al detalle
        log_procesamiento_audio(
            accion='ver',
            procesamiento=procesamiento,
            request=request,
            datos_adicionales={'logs_count': logs.count()}
        )
        
        context = {
            'title': f'Detalle - {procesamiento.titulo}',
            'procesamiento': procesamiento,
            'logs': logs,
            'puede_cancelar': procesamiento.estado in ['pendiente', 'procesando', 'transcribiendo', 'diarizando'],
            'puede_reiniciar': procesamiento.estado in ['error', 'cancelado']
        }
        return render(request, 'audio_processing/detalle_procesamiento.html', context)
    
    except Exception as e:
        log_error_procesamiento(
            error_msg=f"Error al mostrar detalle del procesamiento {id}: {str(e)}",
            request=request,
            stack_trace=traceback.format_exc()
        )
        messages.error(request, "Error al cargar el detalle del procesamiento.")
        return redirect('audio_processing:lista_procesamientos')


@login_required
@require_http_methods(["POST"])
def cancelar_procesamiento(request, id):
    """Cancelar un procesamiento en curso"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    if procesamiento.estado in ['pendiente', 'procesando', 'transcribiendo', 'diarizando']:
        procesamiento.estado = 'cancelado'
        procesamiento.save()
        
        # Crear log
        LogProcesamiento.objects.create(
            procesamiento=procesamiento,
            nivel='INFO',
            mensaje='Procesamiento cancelado por el usuario'
        )
        
        messages.success(request, 'Procesamiento cancelado exitosamente.')
    else:
        messages.error(request, 'No se puede cancelar este procesamiento.')
    
    return redirect('audio_processing:detalle_procesamiento', id=id)


@login_required
@require_http_methods(["POST"])
def reiniciar_procesamiento(request, id):
    """Reiniciar un procesamiento en cualquier estado"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    # Permitir reiniciar en cualquier estado excepto "procesando" activo
    if procesamiento.estado == 'procesando':
        # Verificar si realmente está procesando
        from .tasks import procesar_audio_task
        # Si no hay tarea activa, permitir reiniciar
        messages.warning(request, 'El procesamiento está en curso. Usa "Detener" primero si quieres reiniciarlo.')
        return redirect('audio_processing:detalle_procesamiento', id=id)
    
    # Resetear el procesamiento
    procesamiento.estado = 'pendiente'
    procesamiento.progreso = 0
    procesamiento.mensaje_estado = 'Listo para procesar'
    procesamiento.fecha_procesamiento = None
    procesamiento.fecha_completado = None
    procesamiento.resultado = None
    procesamiento.save()
    
    # Crear log
    LogProcesamiento.objects.create(
        procesamiento=procesamiento,
        nivel='info',
        mensaje='Procesamiento reiniciado por el usuario',
        detalles_json={'action': 'restart', 'user': str(request.user)}
    )
    
    # Iniciar nueva tarea
    from .tasks import procesar_audio_task
    task = procesar_audio_task.delay(procesamiento.id)
    
    messages.success(request, f'Procesamiento reiniciado exitosamente. Tarea: {task.id}')
    return redirect('audio_processing:detalle_procesamiento', id=id)


@login_required
@require_http_methods(["POST"]) 
def detener_procesamiento(request, id):
    """Detener un procesamiento en curso"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    if procesamiento.estado != 'procesando':
        messages.error(request, 'Este procesamiento no está en curso.')
        return redirect('audio_processing:detalle_procesamiento', id=id)
    
    # Cambiar estado a cancelado
    procesamiento.estado = 'cancelado'
    procesamiento.mensaje_estado = 'Procesamiento detenido por el usuario'
    procesamiento.save()
    
    # Crear log
    LogProcesamiento.objects.create(
        procesamiento=procesamiento,
        nivel='warning',
        mensaje='Procesamiento detenido por el usuario',
        detalles_json={'action': 'stop', 'user': str(request.user)}
    )
    
    # TODO: Implementar cancelación de tarea de Celery
    # from celery.task.control import revoke
    # revoke(task_id, terminate=True)
    
    messages.success(request, 'Procesamiento detenido exitosamente.')
    return redirect('audio_processing:detalle_procesamiento', id=id)


@login_required
@require_http_methods(["POST"])
def iniciar_procesamiento(request, id):
    """Iniciar un procesamiento pendiente"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    if procesamiento.estado != 'pendiente':
        messages.error(request, 'Este procesamiento no está pendiente.')
        return redirect('audio_processing:detalle_procesamiento', id=id)
    
    # Iniciar tarea
    from .tasks import procesar_audio_task
    task = procesar_audio_task.delay(procesamiento.id)
    
    # Crear log
    LogProcesamiento.objects.create(
        procesamiento=procesamiento,
        nivel='info',
        mensaje='Procesamiento iniciado manualmente por el usuario',
        detalles_json={'action': 'start', 'user': str(request.user), 'task_id': task.id}
    )
    
    messages.success(request, f'Procesamiento iniciado exitosamente. Tarea: {task.id}')
    return redirect('audio_processing:detalle_procesamiento', id=id)


@login_required
@require_http_methods(["GET"])
def confirmar_eliminar_procesamiento(request, id):
    """Mostrar página de confirmación para eliminar un procesamiento"""
    try:
        procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
        
        # Log del acceso a confirmación de eliminación
        log_procesamiento_audio(
            accion='confirmar_eliminar',
            procesamiento=procesamiento,
            request=request,
            datos_adicionales={'puede_eliminar': procesamiento.estado not in ['procesando', 'transcribiendo', 'diarizando']}
        )
        
        context = {
            'procesamiento': procesamiento,
            'title': f'Confirmar eliminación - {procesamiento.titulo}',
            'puede_eliminar': procesamiento.estado not in ['procesando', 'transcribiendo', 'diarizando']
        }
        
        return render(request, 'audio_processing/confirmar_eliminar.html', context)
    
    except Exception as e:
        log_error_procesamiento(
            error_msg=f"Error al mostrar confirmación de eliminación para procesamiento {id}: {str(e)}",
            request=request,
            stack_trace=traceback.format_exc()
        )
        messages.error(request, "Error al cargar la página de confirmación.")
        return redirect('audio_processing:lista_procesamientos')


@login_required
@require_http_methods(["POST"])
def eliminar_procesamiento(request, id):
    """Eliminar un procesamiento (solo si no está en proceso)"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    try:
        if procesamiento.estado not in ['procesando', 'transcribiendo', 'diarizando']:
            # Guardar información antes de eliminar para logging
            nombre = procesamiento.titulo
            archivo_path = procesamiento.archivo_audio.path if procesamiento.archivo_audio else None
            archivo_nombre = procesamiento.archivo_audio.name if procesamiento.archivo_audio else None
            archivo_size = procesamiento.archivo_audio.size if procesamiento.archivo_audio else 0
            
            # Log antes de eliminar
            log_procesamiento_audio(
                accion='eliminar',
                procesamiento=procesamiento,
                request=request,
                datos_adicionales={
                    'archivo_eliminado': archivo_nombre,
                    'archivo_size': archivo_size,
                    'archivo_path': archivo_path
                }
            )
            
            # Log de archivo si existe
            if archivo_path:
                log_archivo_operacion(
                    operacion='DELETE',
                    archivo_nombre=archivo_nombre or 'archivo_desconocido',
                    archivo_path=archivo_path,
                    archivo_size_bytes=archivo_size,
                    request=request,
                    resultado='SUCCESS'
                )
            
            # Eliminar el archivo físico si existe
            if archivo_path and os.path.exists(archivo_path):
                os.remove(archivo_path)
                
            # Log administrativo
            log_admin_action(
                request=request,
                modelo_afectado='ProcesamientoAudio',
                accion='DELETE',
                objeto_id=procesamiento.id,
                valores_anteriores={
                    'titulo': nombre,
                    'estado': procesamiento.estado,
                    'archivo': archivo_nombre
                }
            )
            
            # Eliminar el registro de la base de datos
            procesamiento.delete()
            
            messages.success(request, f'Procesamiento "{nombre}" eliminado exitosamente.')
            
            # Log de eliminación exitosa
            log_sistema(
                nivel='INFO',
                categoria='PROCESAMIENTO_ELIMINADO',
                subcategoria='ELIMINACION_EXITOSA',
                mensaje=f'Procesamiento "{nombre}" eliminado exitosamente',
                request=request,
                datos_extra={
                    'procesamiento_id': id,
                    'titulo': nombre,
                    'archivo_eliminado': archivo_nombre
                }
            )
            
            return redirect('audio_processing:lista_procesamientos')
            
        else:
            # Log de intento de eliminación no válido
            log_sistema(
                nivel='WARNING',
                categoria='PROCESAMIENTO_ERROR',
                subcategoria='ELIMINACION_DENEGADA',
                mensaje=f'Intento de eliminar procesamiento en estado: {procesamiento.estado}',
                request=request,
                datos_extra={
                    'procesamiento_id': procesamiento.id,
                    'titulo': procesamiento.titulo,
                    'estado': procesamiento.estado
                }
            )
            
            messages.error(request, 'No se puede eliminar un procesamiento que está en curso.')
            return redirect('audio_processing:detalle_procesamiento', id=id)
            
    except Exception as e:
        # Log del error
        log_error_procesamiento(
            error_msg=f'Error al eliminar procesamiento {id}: {str(e)}',
            procesamiento=procesamiento,
            request=request,
            stack_trace=traceback.format_exc()
        )
        
        messages.error(request, f'Error al eliminar el procesamiento: {str(e)}')
        return redirect('audio_processing:detalle_procesamiento', id=id)


@login_required
def editar_procesamiento(request, id):
    """Editar un procesamiento (solo datos básicos, no el audio)"""
    try:
        procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
        
        if request.method == 'POST':
            # Guardar valores anteriores para auditoría
            valores_anteriores = {
                'titulo': procesamiento.titulo,
                'descripcion': procesamiento.descripcion,
                'tipo_reunion': str(procesamiento.tipo_reunion) if procesamiento.tipo_reunion else None,
                'confidencial': procesamiento.confidencial,
                'participantes_detallados': procesamiento.participantes_detallados,
            }
            
            form = EditarProcesamientoForm(request.POST, instance=procesamiento)
            if form.is_valid():
                # Identificar campos modificados
                campos_modificados = []
                valores_nuevos = {}
                
                for field in form.changed_data:
                    campo_valor = getattr(procesamiento, field)
                    if field == 'tipo_reunion':
                        campo_valor = str(campo_valor) if campo_valor else None
                    campos_modificados.append(field)
                    valores_nuevos[field] = campo_valor
                
                form.save()
                
                # Log de edición exitosa
                log_procesamiento_audio(
                    accion='editar',
                    procesamiento=procesamiento,
                    request=request,
                    datos_adicionales={
                        'campos_modificados': campos_modificados,
                        'valores_anteriores': valores_anteriores,
                        'valores_nuevos': valores_nuevos
                    }
                )
                
                # Log administrativo
                log_admin_action(
                    request=request,
                    modelo_afectado='ProcesamientoAudio',
                    accion='UPDATE',
                    objeto_id=procesamiento.id,
                    campos_modificados=campos_modificados,
                    valores_anteriores=valores_anteriores,
                    valores_nuevos=valores_nuevos
                )
                
                messages.success(request, f'Procesamiento "{procesamiento.titulo}" actualizado exitosamente.')
                return redirect('audio_processing:detalle_procesamiento', id=id)
            else:
                # Log de validación fallida
                log_sistema(
                    nivel='WARNING',
                    categoria='PROCESAMIENTO_ERROR',
                    subcategoria='EDICION_VALIDACION_FALLIDA',
                    mensaje=f'Errores de validación al editar procesamiento {procesamiento.titulo}',
                    request=request,
                    datos_extra={
                        'procesamiento_id': procesamiento.id,
                        'errores_formulario': dict(form.errors)
                    }
                )
        else:
            # Log del acceso al formulario de edición
            log_navegacion(
                request=request,
                accion_realizada='editar_procesamiento_form',
                elemento_interactuado=f'procesamiento_{procesamiento.id}'
            )
            
            form = EditarProcesamientoForm(instance=procesamiento)
        
        context = {
            'title': f'Editar Procesamiento: {procesamiento.titulo}',
            'procesamiento': procesamiento,
            'form': form,
        }
        return render(request, 'audio_processing/editar_procesamiento.html', context)
    
    except Exception as e:
        log_error_procesamiento(
            error_msg=f'Error al editar procesamiento {id}: {str(e)}',
            request=request,
            stack_trace=traceback.format_exc()
        )
        messages.error(request, "Error al cargar el formulario de edición.")
        return redirect('audio_processing:lista_procesamientos')


@login_required
def tipos_reunion(request):
    """Gestión de tipos de reunión"""
    tipos = TipoReunion.objects.all().order_by('nombre')
    
    context = {
        'title': 'Tipos de Reunión',
        'tipos': tipos
    }
    return render(request, 'audio_processing/tipos_reunion.html', context)


@login_required
def crear_tipo_reunion(request):
    """Crear nuevo tipo de reunión"""
    if request.method == 'POST':
        form = TipoReunionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de reunión creado exitosamente.')
            return redirect('audio_processing:tipos_reunion')
    else:
        form = TipoReunionForm()
    
    context = {
        'title': 'Crear Tipo de Reunión',
        'form': form
    }
    return render(request, 'audio_processing/form_tipo_reunion.html', context)


@login_required
def editar_tipo_reunion(request, id):
    """Editar tipo de reunión existente"""
    tipo = get_object_or_404(TipoReunion, id=id)
    
    if request.method == 'POST':
        form = TipoReunionForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tipo de reunión actualizado exitosamente.')
            return redirect('audio_processing:tipos_reunion')
    else:
        form = TipoReunionForm(instance=tipo)
    
    context = {
        'title': f'Editar - {tipo.nombre}',
        'form': form,
        'tipo': tipo
    }
    return render(request, 'audio_processing/form_tipo_reunion.html', context)


@login_required
@require_http_methods(["POST"])
def eliminar_tipo_reunion(request, id):
    """Eliminar tipo de reunión"""
    tipo = get_object_or_404(TipoReunion, id=id)
    
    # Verificar si hay procesamientos asociados
    if ProcesamientoAudio.objects.filter(tipo_reunion=tipo).exists():
        messages.error(request, 'No se puede eliminar este tipo porque tiene procesamientos asociados.')
    else:
        nombre = tipo.nombre
        tipo.delete()
        messages.success(request, f'Tipo de reunión "{nombre}" eliminado exitosamente.')
    
    return redirect('audio_processing:tipos_reunion')


# APIs para frontend
# (API duplicada de estado eliminada; se mantiene una única implementación más abajo)


@login_required
def api_log_procesamiento(request, id):
    """API para obtener los logs de un procesamiento"""
    try:
        procesamiento = ProcesamientoAudio.objects.get(id=id, usuario=request.user)
        logs = LogProcesamiento.objects.filter(procesamiento=procesamiento).order_by('-timestamp')[:50]
        
        data = {
            'logs': [
                {
                    'fecha_hora': log.timestamp.isoformat(),
                    'nivel': log.nivel,
                    'mensaje': log.mensaje
                }
                for log in logs
            ]
        }
        return JsonResponse(data)
    except ProcesamientoAudio.DoesNotExist:
        return JsonResponse({'error': 'Procesamiento no encontrado'}, status=404)


@login_required
def api_progreso_procesamiento(request, id):
    """API para obtener información detallada del progreso"""
    try:
        procesamiento = ProcesamientoAudio.objects.get(id=id, usuario=request.user)
        data = {
            'id': procesamiento.id,
            'titulo': procesamiento.titulo,
            'estado': procesamiento.estado,
            'progreso': procesamiento.progreso,
            'fecha_inicio': procesamiento.fecha_procesamiento.isoformat() if procesamiento.fecha_procesamiento else None,
            'fecha_fin': procesamiento.fecha_completado.isoformat() if procesamiento.fecha_completado else None,
            'tiempo_estimado': procesamiento.duracion,
            'archivos_generados': {
                'audio_procesado': bool(procesamiento.archivo_mejorado),
                'transcripcion': bool(procesamiento.resultado),
                'acta': False  # Por implementar
            }
        }
        return JsonResponse(data)
    except ProcesamientoAudio.DoesNotExist:
        return JsonResponse({'error': 'Procesamiento no encontrado'}, status=404)


# Descarga de archivos
@login_required
def descargar_audio_original(request, id):
    """Descargar archivo de audio original"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    if not procesamiento.archivo_audio_original:
        raise Http404("Archivo no encontrado")
    
    file_path = procesamiento.archivo_audio_original.path
    if not os.path.exists(file_path):
        raise Http404("Archivo no encontrado en el sistema")
    
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type=mimetypes.guess_type(file_path)[0])
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response


@login_required
def descargar_audio_procesado(request, id):
    """Descargar archivo de audio procesado"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    if not procesamiento.archivo_mejorado:
        raise Http404("Archivo procesado no disponible")
    
    file_path = procesamiento.archivo_mejorado.path
    if not os.path.exists(file_path):
        raise Http404("Archivo no encontrado en el sistema")
    
    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type='audio/wav')
        response['Content-Disposition'] = f'attachment; filename="procesado_{os.path.basename(file_path)}"'
        return response


@login_required
def descargar_transcripcion(request, id):
    """Descargar transcripción en formato texto"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    if not procesamiento.resultado:
        raise Http404("Transcripción no disponible")
    
    # Extraer el texto de la transcripción del resultado JSON
    transcripcion_texto = ""
    if isinstance(procesamiento.resultado, dict):
        transcripcion_texto = procesamiento.resultado.get('transcripcion', str(procesamiento.resultado))
    else:
        transcripcion_texto = str(procesamiento.resultado)
    
    response = HttpResponse(transcripcion_texto, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="transcripcion_{procesamiento.id}.txt"'
    return response


@login_required
def descargar_acta(request, id):
    """Descargar acta generada"""
    procesamiento = get_object_or_404(ProcesamientoAudio, id=id, usuario=request.user)
    
    # Por implementar cuando se agregue generación de actas
    raise Http404("Función de actas aún no implementada")


# ===== APIs PARA EL NUEVO CENTRO DE AUDIO =====

@require_http_methods(["GET"])
def api_stats(request):
    """API para obtener estadísticas de procesamientos"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'success',
            'stats': {
                'total': 0,
                'completed': 0,
                'processing': 0,
                'error': 0
            }
        })
    
    from django.db.models import Count, Q
    
    user_procesamientos = ProcesamientoAudio.objects.filter(usuario=request.user)
    stats = user_procesamientos.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(estado='completado')),
        processing=Count('id', filter=Q(estado__in=['pendiente', 'procesando', 'transcribiendo'])),
        error=Count('id', filter=Q(estado='error'))
    )
    
    return JsonResponse({
        'status': 'success',
        'stats': stats
    })


@require_http_methods(["GET"])
def api_recent_processes(request):
    """API para obtener procesos recientes"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'success',
            'processes': []
        })
    
    recent_processes = ProcesamientoAudio.objects.filter(
        usuario=request.user
    ).order_by('-created_at')[:5]
    
    processes_data = []
    for proceso in recent_processes:
        proceso_data = {
            'id': proceso.id,
            'titulo': proceso.titulo or "Sin título",
            'estado': proceso.estado,
            'tipo_reunion': proceso.tipo_reunion.nombre if proceso.tipo_reunion else None,
            'fecha': proceso.created_at.strftime('%d/%m/%Y'),
            'hora': proceso.created_at.strftime('%H:%M'),
            'progreso': getattr(proceso, 'progreso', 0),
            'duracion': proceso.duracion_formateada if proceso.duracion else None,
            'tamano_mb': str(proceso.tamano_mb) if proceso.tamano_mb else None,
            'formato': proceso.formato or None,
            'sample_rate': proceso.sample_rate or None,
            'canales': proceso.canales or None,
            'audio_original_url': proceso.archivo_audio.url if proceso.archivo_audio else None,
            'audio_procesado_url': proceso.archivo_mejorado.url if proceso.archivo_mejorado else None,
            'tiene_audio_procesado': bool(proceso.archivo_mejorado),
        }
        processes_data.append(proceso_data)
    
    return JsonResponse({
        'status': 'success',
        'processes': processes_data
    })


@require_http_methods(["GET"])
def api_estado_procesamiento(request, id):
    """API para consultar el estado/progreso de un procesamiento"""
    try:
        proc = get_object_or_404(ProcesamientoAudio, id=id)
        # Nota: si hay control de permisos por usuario, se puede restringir aquí
        data = {
            'id': proc.id,
            'estado': proc.estado,
            'estado_display': proc.get_estado_display() if hasattr(proc, 'get_estado_display') else proc.estado,
            'progreso': getattr(proc, 'progreso', 0),
            'updated_at': proc.updated_at.isoformat() if hasattr(proc, 'updated_at') and proc.updated_at else None,
        }
        return JsonResponse(data)
    except Http404:
        return JsonResponse({'detail': 'No encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error en api_estado_procesamiento: {e}")
        return JsonResponse({'detail': 'Error interno'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt  # Será manejado por el token CSRF en el frontend
def api_procesar_audio(request):
    """API para procesar audio desde el centro de audio nuevo"""
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Usuario no autenticado'
        }, status=401)
    
    try:
        # Validar que hay archivo
        if 'archivo' not in request.FILES:
            return JsonResponse({
                'status': 'error',
                'message': 'No se proporcionó archivo de audio'
            }, status=400)
        
        archivo = request.FILES['archivo']
        
        # Validar tipo de archivo (más amplio para soportar webm de grabaciones)
        allowed_types = ['audio/mp3', 'audio/mpeg', 'audio/wav', 'audio/m4a', 'audio/ogg', 'audio/webm']
        file_extensions = ('.mp3', '.wav', '.m4a', '.ogg', '.webm')
        
        if archivo.content_type not in allowed_types and not archivo.name.lower().endswith(file_extensions):
            return JsonResponse({
                'status': 'error',
                'message': 'Tipo de archivo no válido. Usa MP3, WAV, M4A, OGG o WEBM.'
            }, status=400)
        
        # Validar tamaño (100MB)
        if archivo.size > 100 * 1024 * 1024:
            return JsonResponse({
                'status': 'error',
                'message': 'Archivo demasiado grande. Máximo 100MB.'
            }, status=400)
        
        # Obtener datos del formulario
        nombre_proceso = request.POST.get('nombre_proceso', '').strip()
        if not nombre_proceso:
            return JsonResponse({
                'status': 'error',
                'message': 'El nombre del proceso es requerido'
            }, status=400)
        
        # Crear el procesamiento con los campos de la nueva vista
        procesamiento = ProcesamientoAudio(
            usuario=request.user,
            archivo_audio=archivo,
            titulo=nombre_proceso,  # Mapear nombre_proceso a titulo
            participantes=request.POST.get('participantes_texto', ''),  # Texto libre como backup
            ubicacion=request.POST.get('ubicacion', ''),
            descripcion=request.POST.get('descripcion', ''),
            estado='pendiente'
        )
        
        # Procesar participantes detallados
        participantes_detallados_str = request.POST.get('participantes_detallados', '')
        if participantes_detallados_str:
            try:
                import json
                participantes_detallados = json.loads(participantes_detallados_str)
                procesamiento.participantes_detallados = participantes_detallados
            except json.JSONDecodeError:
                logger.warning(f"Error parsing participantes_detallados: {participantes_detallados_str}")
        
        # Manejar tipo de reunión
        tipo_reunion_value = request.POST.get('tipo_reunion')
        if tipo_reunion_value:
            try:
                # Intentar buscar por ID primero
                if tipo_reunion_value.isdigit():
                    tipo_reunion = TipoReunion.objects.get(id=tipo_reunion_value)
                else:
                    # Buscar por nombre o crear uno nuevo si no existe
                    tipo_reunion, created = TipoReunion.objects.get_or_create(
                        nombre=tipo_reunion_value,
                        defaults={'descripcion': f'Tipo de reunión: {tipo_reunion_value}'}
                    )
                procesamiento.tipo_reunion = tipo_reunion
            except TipoReunion.DoesNotExist:
                # Si no encuentra el ID, crear uno nuevo con el valor proporcionado
                tipo_reunion = TipoReunion.objects.create(
                    nombre=tipo_reunion_value,
                    descripcion=f'Tipo de reunión: {tipo_reunion_value}'
                )
                procesamiento.tipo_reunion = tipo_reunion
        
        # Manejar etiquetas
        etiquetas = request.POST.get('etiquetas', '').strip()
        if etiquetas:
            procesamiento.etiquetas = etiquetas
        
        # Manejar confidencialidad
        confidencial = request.POST.get('confidencial', 'false')
        procesamiento.confidencial = confidencial.lower() == 'true'
        
        # Extraer metadatos del archivo de audio
        try:
            import subprocess
            import json
            import tempfile
            import os
            
            # Guardar archivo temporalmente para analizar
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as temp_file:
                for chunk in archivo.chunks():
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            # Usar ffprobe para extraer metadatos
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams',
                temp_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                
                # Extraer información del primer stream de audio
                audio_stream = None
                for stream in metadata.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    # Guardar metadatos específicos
                    procesamiento.sample_rate = int(audio_stream.get('sample_rate', 0)) or None
                    procesamiento.canales = int(audio_stream.get('channels', 0)) or None
                    procesamiento.bit_rate = int(audio_stream.get('bit_rate', 0)) or None
                    procesamiento.codec = audio_stream.get('codec_name', '')
                    
                    # Duración
                    duration = float(audio_stream.get('duration', 0)) or float(metadata.get('format', {}).get('duration', 0))
                    if duration:
                        procesamiento.duracion_seg = duration
                        procesamiento.duracion = int(duration)
                
                # Formato y tamaño
                format_info = metadata.get('format', {})
                procesamiento.formato = format_info.get('format_name', '').split(',')[0] if format_info.get('format_name') else ''
                procesamiento.tamano_mb = round(archivo.size / (1024 * 1024), 2)
                
                # Guardar metadatos completos
                procesamiento.metadatos_originales = metadata
                
            # Limpiar archivo temporal
            os.unlink(temp_path)
            
        except Exception as metadata_error:
            logger.warning(f"Error extrayendo metadatos: {metadata_error}")
            # Fallback: solo tamaño y formato básico
            procesamiento.tamano_mb = round(archivo.size / (1024 * 1024), 2)
            procesamiento.formato = os.path.splitext(archivo.name)[1][1:].upper()
        
        # Información adicional del source
        source = request.POST.get('source', 'upload')  # 'record' o 'upload'
        
        procesamiento.save()
        
        # Log de creación exitosa
        log_procesamiento_audio(
            accion='crear',
            procesamiento=procesamiento,
            request=request,
            datos_adicionales={
                'source': source,
                'archivo_nombre': archivo.name,
                'archivo_size': archivo.size,
                'archivo_type': archivo.content_type,
                'metadatos': {
                    'tamano_mb': float(procesamiento.tamano_mb) if procesamiento.tamano_mb else None,
                    'duracion': procesamiento.duracion,
                    'formato': procesamiento.formato,
                    'sample_rate': procesamiento.sample_rate,
                    'canales': procesamiento.canales
                }
            }
        )
        
        # Log de archivo subido
        log_archivo_operacion(
            operacion='UPLOAD',
            archivo_nombre=archivo.name,
            archivo_path=procesamiento.archivo_audio.path if procesamiento.archivo_audio else '',
            archivo_size_bytes=archivo.size,
            archivo_tipo_mime=archivo.content_type,
            request=request,
            resultado='SUCCESS',
            metadatos={
                'source': source,
                'procesamiento_id': procesamiento.id,
                'titulo': procesamiento.titulo
            }
        )
        
        # Log administrativo
        log_admin_action(
            request=request,
            modelo_afectado='ProcesamientoAudio',
            accion='CREATE',
            objeto_id=procesamiento.id,
            valores_nuevos={
                'titulo': procesamiento.titulo,
                'estado': procesamiento.estado,
                'archivo': archivo.name,
                'usuario': request.user.username
            }
        )
        
        # Intentar iniciar procesamiento en background
        try:
            from .tasks import procesar_audio_task
            task = procesar_audio_task.delay(procesamiento.id)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Procesamiento iniciado exitosamente',
                'procesamiento_id': procesamiento.id,
                'task_id': str(task.id) if task else None,
                'metadatos': {
                    'tamano_mb': float(procesamiento.tamano_mb) if procesamiento.tamano_mb else None,
                    'duracion': procesamiento.duracion,
                    'formato': procesamiento.formato,
                    'sample_rate': procesamiento.sample_rate,
                    'canales': procesamiento.canales
                }
            })
            
        except Exception as celery_error:
            logger.warning(f"Celery no disponible, marcando como pendiente: {celery_error}")
            # Si Celery no está disponible, el procesamiento quedará pendiente
            return JsonResponse({
                'status': 'success',
                'message': 'Procesamiento en cola (Celery no disponible)',
                'procesamiento_id': procesamiento.id,
                'task_id': None,
                'metadatos': {
                    'tamano_mb': float(procesamiento.tamano_mb) if procesamiento.tamano_mb else None,
                    'duracion': procesamiento.duracion,
                    'formato': procesamiento.formato,
                    'sample_rate': procesamiento.sample_rate,
                    'canales': procesamiento.canales
                }
            })
        
    except Exception as e:
        # Log del error
        log_error_procesamiento(
            error_msg=f"Error en api_procesar_audio: {str(e)}",
            request=request,
            stack_trace=traceback.format_exc()
        )
        
        logger.error(f"Error en api_procesar_audio: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Error interno del servidor'
        }, status=500)
