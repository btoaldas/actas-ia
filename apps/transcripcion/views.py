from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
import json
import logging

from apps.audio_processing.models import ProcesamientoAudio
from .models import (
    Transcripcion, EstadoTranscripcion, ConfiguracionTranscripcion,
    HistorialEdicion, ConfiguracionHablante
)
from .tasks import procesar_transcripcion_completa
from .logging_helper import (
    log_transcripcion_navegacion, log_transcripcion_accion,
    log_transcripcion_admin, log_transcripcion_edicion,
    log_transcripcion_error
)

logger = logging.getLogger(__name__)


@login_required
def lista_transcripciones(request):
    """
    Vista principal que lista audios listos para transcribir y transcripciones existentes
    """
    try:
        log_transcripcion_navegacion(request, None, 'lista_transcripciones')
        
        # Audios procesados listos para transcribir
        audios_listos = ProcesamientoAudio.objects.filter(
            estado='completado'
        ).exclude(
            transcripcion__isnull=False  # Excluir los que ya tienen transcripción
        ).order_by('-created_at')
        
        # Transcripciones existentes
        transcripciones = Transcripcion.objects.select_related(
            'procesamiento_audio', 'configuracion_utilizada', 'usuario_creacion'
        ).order_by('-fecha_creacion')
        
        # Filtros
        estado_filtro = request.GET.get('estado')
        busqueda = request.GET.get('q')
        
        if estado_filtro:
            transcripciones = transcripciones.filter(estado=estado_filtro)
        
        if busqueda:
            transcripciones = transcripciones.filter(
                Q(procesamiento_audio__titulo__icontains=busqueda) |
                Q(texto_completo__icontains=busqueda) |
                Q(procesamiento_audio__tipo_reunion__nombre__icontains=busqueda)
            )
        
        # Paginación
        paginator = Paginator(transcripciones, 10)
        page_number = request.GET.get('page')
        transcripciones_page = paginator.get_page(page_number)
        
        # Estadísticas rápidas
        estadisticas = {
            'audios_pendientes': audios_listos.count(),
            'transcripciones_activas': transcripciones.filter(
                estado__in=[EstadoTranscripcion.EN_PROCESO, EstadoTranscripcion.TRANSCRIBIENDO, 
                           EstadoTranscripcion.DIARIZANDO, EstadoTranscripcion.PROCESANDO]
            ).count(),
            'completadas_hoy': transcripciones.filter(
                estado=EstadoTranscripcion.COMPLETADO,
                fecha_actualizacion__date=timezone.now().date()
            ).count(),
            'con_errores': transcripciones.filter(estado=EstadoTranscripcion.ERROR).count(),
        }
        
        context = {
            'audios_listos': audios_listos[:5],  # Solo mostrar primeros 5
            'transcripciones': transcripciones_page,
            'estados_transcripcion': EstadoTranscripcion.choices,
            'estadisticas': estadisticas,
            'estado_filtro': estado_filtro,
            'busqueda': busqueda,
        }
        
        return render(request, 'transcripcion/lista_transcripciones.html', context)
        
    except Exception as e:
        logger.error(f"Error en lista_transcripciones: {str(e)}")
        log_transcripcion_error(None, 'vista_error', str(e), {'vista': 'lista_transcripciones'})
        messages.error(request, f"Error al cargar transcripciones: {str(e)}")
        return render(request, 'transcripcion/lista_transcripciones.html', {'transcripciones': []})


@login_required
def audios_listos_transcribir(request):
    """
    Vista que muestra todos los audios procesados listos para transcribir
    """
    try:
        # Audios procesados sin transcripción
        audios_query = ProcesamientoAudio.objects.filter(
            estado='completado'
        ).exclude(
            transcripcion__isnull=False
        ).select_related('tipo_reunion', 'usuario')
        
        # Filtros
        tipo_reunion_filtro = request.GET.get('tipo_reunion')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        busqueda = request.GET.get('q')
        
        if tipo_reunion_filtro:
            audios_query = audios_query.filter(tipo_reunion_id=tipo_reunion_filtro)
        
        if fecha_desde:
            audios_query = audios_query.filter(created_at__date__gte=fecha_desde)
        
        if fecha_hasta:
            audios_query = audios_query.filter(created_at__date__lte=fecha_hasta)
        
        if busqueda:
            audios_query = audios_query.filter(
                Q(titulo__icontains=busqueda) |
                Q(descripcion__icontains=busqueda)
            )
        
        # Ordenar por fecha de procesamiento
        audios_listos = audios_query.order_by('-fecha_procesamiento')
        
        # Paginación
        paginator = Paginator(audios_listos, 12)
        page_number = request.GET.get('page')
        audios_page = paginator.get_page(page_number)
        
        # Obtener tipos de reunión para filtro
        from apps.audio_processing.models import TipoReunion
        tipos_reunion = TipoReunion.objects.all()
        
        # Configuración por defecto
        try:
            config_defecto = ConfiguracionTranscripcion.get_configuracion_defecto()
        except:
            config_defecto = None
        
        context = {
            'audios_listos': audios_page,
            'tipos_reunion': tipos_reunion,
            'config_defecto': config_defecto,
            'tipo_reunion_filtro': tipo_reunion_filtro,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'busqueda': busqueda,
            'total_audios': audios_query.count(),
        }
        
        return render(request, 'transcripcion/audios_listos.html', context)
        
    except Exception as e:
        logger.error(f"Error en audios_listos_transcribir: {str(e)}")
        messages.error(request, f"Error al cargar audios: {str(e)}")
        return render(request, 'transcripcion/audios_listos.html', {'audios_listos': []})


@login_required
def configurar_transcripcion(request, audio_id):
    """
    Vista para configurar parámetros de transcripción de un audio específico
    """
    try:
        # Debug: Añadir logging básico
        logger.info(f"Accediendo a configurar_transcripcion con audio_id: {audio_id}")
        
        audio = get_object_or_404(ProcesamientoAudio, id=audio_id, estado='completado')
        logger.info(f"Audio encontrado: {audio.titulo}")
        
        # Verificar que no tenga transcripción ya
        if hasattr(audio, 'transcripcion'):
            messages.warning(request, 'Este audio ya tiene una transcripción en proceso.')
            return redirect('transcripcion:detalle', transcripcion_id=audio.transcripcion.id)
        
        # Obtener configuraciones disponibles
        configuraciones = ConfiguracionTranscripcion.objects.filter(activa=True)
        logger.info(f"Configuraciones encontradas: {configuraciones.count()}")
        
        # Usar configuración por defecto o crear una básica
        try:
            config_defecto = ConfiguracionTranscripcion.get_configuracion_defecto()
        except:
            # Si no hay configuración por defecto, crear una básica
            config_defecto, created = ConfiguracionTranscripcion.objects.get_or_create(
                nombre='Básica',
                defaults={
                    'descripcion': 'Configuración básica temporal',
                    'modelo_whisper': 'base',
                    'temperatura': 0.0,
                    'idioma_principal': 'es',
                    'usar_vad': True,
                    'vad_filtro': 'silero',
                    'min_hablantes': 1,
                    'max_hablantes': 4,
                    'umbral_clustering': 0.7,
                    'chunk_duracion': 30,
                    'usar_gpu': False,
                    'filtro_ruido': True,
                    'normalizar_audio': True,
                    'activa': True,
                }
            )
            if created:
                logger.info("Configuración básica creada automáticamente")
        
        logger.info(f"Configuración por defecto: {config_defecto.nombre}")
        
        if request.method == 'POST':
            logger.info("Procesando formulario POST")
            # Procesar formulario de configuración
            config_id = request.POST.get('configuracion_base')  # Corregido: coincide con el nombre del campo HTML
            parametros_custom = {}
            
            # Obtener datos del formulario para parámetros personalizados
            titulo_transcripcion = request.POST.get('titulo_transcripcion', audio.titulo)
            descripcion_transcripcion = request.POST.get('descripcion_transcripcion', '')
            
            # Obtener configuración seleccionada
            if config_id and config_id != 'custom':
                config_seleccionada = get_object_or_404(ConfiguracionTranscripcion, 
                                                       id=config_id, activa=True)
                # Para configuraciones predefinidas, tomar parámetros del template pero permitir modificaciones
                parametros_custom = {
                    'modelo_whisper': request.POST.get('modelo_whisper', config_seleccionada.modelo_whisper),
                    'idioma_principal': request.POST.get('idioma_principal', config_seleccionada.idioma_principal),
                    'temperatura': float(request.POST.get('temperatura', config_seleccionada.temperatura)),
                    'usar_vad': request.POST.get('usar_vad') == 'on',
                    'vad_filtro': request.POST.get('vad_filtro', config_seleccionada.vad_filtro),
                    'min_hablantes': int(request.POST.get('min_hablantes', config_seleccionada.min_hablantes)),
                    'max_hablantes': int(request.POST.get('max_hablantes', config_seleccionada.max_hablantes)),
                    'umbral_clustering': float(request.POST.get('umbral_clustering', config_seleccionada.umbral_clustering)),
                    'chunk_duracion': int(request.POST.get('chunk_duracion', config_seleccionada.chunk_duracion)),
                    'overlap_duracion': int(request.POST.get('overlap_duracion', config_seleccionada.overlap_duracion)),
                    'usar_gpu': request.POST.get('usar_gpu') == 'on',
                    'filtro_ruido': request.POST.get('filtro_ruido') == 'on',
                    'normalizar_audio': request.POST.get('normalizar_audio') == 'on',
                    'usar_enhanced_diarization': request.POST.get('usar_enhanced_diarization') == 'on',
                }
            else:
                # Configuración completamente personalizada
                config_seleccionada = None
                parametros_custom = {
                    'modelo_whisper': request.POST.get('modelo_whisper', 'base'),
                    'idioma_principal': request.POST.get('idioma_principal', 'es'),
                    'temperatura': float(request.POST.get('temperatura', 0.0)),
                    'usar_vad': request.POST.get('usar_vad') == 'on',
                    'vad_filtro': request.POST.get('vad_filtro', 'silero'),
                    'min_hablantes': int(request.POST.get('min_hablantes', 1)),
                    'max_hablantes': int(request.POST.get('max_hablantes', 8)),
                    'umbral_clustering': float(request.POST.get('umbral_clustering', 0.7)),
                    'chunk_duracion': int(request.POST.get('chunk_duracion', 30)),
                    'overlap_duracion': int(request.POST.get('overlap_duracion', 2)),
                    'usar_gpu': request.POST.get('usar_gpu') == 'on',
                    'filtro_ruido': request.POST.get('filtro_ruido') == 'on',
                    'normalizar_audio': request.POST.get('normalizar_audio') == 'on',
                    'usar_enhanced_diarization': request.POST.get('usar_enhanced_diarization') == 'on',
                }
            
            # Crear la transcripción
            transcripcion = Transcripcion.objects.create(
                procesamiento_audio=audio,
                configuracion_utilizada=config_seleccionada,
                usuario_creacion=request.user,
                estado=EstadoTranscripcion.PENDIENTE,
                parametros_personalizados=parametros_custom
            )
            
            # Iniciar procesamiento asíncrono
            try:
                task = procesar_transcripcion_completa.delay(transcripcion.id)
                transcripcion.task_id_celery = task.id
                transcripcion.save()
                
                log_transcripcion_accion(transcripcion, 'transcripcion_iniciada', 
                                       {'configuracion': config_seleccionada.nombre if config_seleccionada else 'Personalizada'},
                                       request.user)
                
                # Si es petición AJAX, devolver JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return JsonResponse({
                        'success': True,
                        'transcripcion_id': transcripcion.id,
                        'task_id': task.id,
                        'mensaje': f'Transcripción iniciada correctamente. ID: {transcripcion.id}'
                    })
                
                messages.success(request, f'Transcripción iniciada correctamente. ID: {transcripcion.id}')
                return redirect('transcripcion:detalle', transcripcion_id=transcripcion.id)
                
            except Exception as e:
                logger.error(f"Error al iniciar tarea de transcripción: {str(e)}")
                transcripcion.estado = EstadoTranscripcion.ERROR
                transcripcion.mensaje_error = f"Error al iniciar procesamiento: {str(e)}"
                transcripcion.save()
                
                # Si es petición AJAX, devolver error en JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                    return JsonResponse({
                        'success': False,
                        'error': f"Error al iniciar transcripción: {str(e)}"
                    })
                
                messages.error(request, f"Error al iniciar transcripción: {str(e)}")
        
        context = {
            'audio': audio,
            'configuraciones': configuraciones,
            'configuracion_seleccionada': config_defecto,
        }
        
        return render(request, 'transcripcion/configurar_transcripcion.html', context)
        
    except Exception as e:
        logger.error(f"Error en configurar_transcripcion: {str(e)}")
        messages.error(request, f"Error: {str(e)}")
        # En caso de error, intentar mostrar la página con contexto mínimo
        try:
            context = {
                'audio': get_object_or_404(ProcesamientoAudio, id=audio_id, estado='completado'),
                'configuraciones': ConfiguracionTranscripcion.objects.filter(activa=True),
                'configuracion_seleccionada': ConfiguracionTranscripcion.get_configuracion_defecto(),
            }
            return render(request, 'transcripcion/configurar_transcripcion.html', context)
        except:
            return redirect('transcripcion:audios_listos')


@login_required
@require_http_methods(["POST"])
def iniciar_transcripcion(request, procesamiento_id):
    """
    Inicia el proceso de transcripción para un audio procesado
    """
    try:
        procesamiento = get_object_or_404(ProcesamientoAudio, id=procesamiento_id)
        
        # Verificar que el audio esté procesado
        if procesamiento.estado != 'completado':
            return JsonResponse({
                'success': False,
                'error': 'El audio debe estar completamente procesado antes de transcribir'
            })
        
        # Verificar que no exista ya una transcripción
        if hasattr(procesamiento, 'transcripcion'):
            return JsonResponse({
                'success': False,
                'error': 'Este audio ya tiene una transcripción en proceso o completada'
            })
        
        # Obtener configuración activa
        configuracion = ConfiguracionTranscripcion.get_configuracion_activa()
        if not configuracion:
            return JsonResponse({
                'success': False,
                'error': 'No hay una configuración de transcripción activa. Contacte al administrador.'
            })
        
        # Crear transcripción
        transcripcion = Transcripcion.objects.create(
            procesamiento_audio=procesamiento,
            configuracion_utilizada=configuracion,
            usuario_creacion=request.user,
            estado=EstadoTranscripcion.PENDIENTE
        )
        
        log_transcripcion_accion(
            transcripcion, 
            'creacion', 
            {
                'configuracion_id': configuracion.id,
                'configuracion_nombre': configuracion.nombre
            },
            request.user
        )
        
        # Iniciar tarea de procesamiento
        task = procesar_transcripcion_completa.delay(transcripcion.id)
        transcripcion.task_id_celery = task.id
        transcripcion.save()
        
        log_transcripcion_accion(
            transcripcion,
            'inicio_procesamiento',
            {'task_id': task.id},
            request.user
        )
        
        return JsonResponse({
            'success': True,
            'transcripcion_id': transcripcion.id,
            'task_id': task.id,
            'message': 'Transcripción iniciada correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error al iniciar transcripción: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })


@login_required
def configurar_transcripcion_legacy(request, procesamiento_id):
    """
    Vista legacy para configurar parámetros de transcripción antes de iniciar el proceso
    (DEPRECADA - usar configurar_transcripcion con audio_id)
    """
    try:
        procesamiento = get_object_or_404(ProcesamientoAudio, id=procesamiento_id)
        
        # Verificar que el audio esté procesado
        if procesamiento.estado != 'completado':
            messages.error(request, 'El audio debe estar completamente procesado antes de transcribir')
            return redirect('transcripcion:lista')
        
        # Verificar que no exista ya una transcripción
        if hasattr(procesamiento, 'transcripcion'):
            messages.warning(request, 'Este audio ya tiene una transcripción en proceso o completada')
            return redirect('transcripcion:detalle', transcripcion_id=procesamiento.transcripcion.id)
        
        # Obtener configuraciones disponibles
        configuraciones = ConfiguracionTranscripcion.objects.filter(activa=True).order_by('-fecha_creacion')
        configuracion_activa = ConfiguracionTranscripcion.get_configuracion_activa()
        
        if request.method == 'POST':
            # Procesar formulario de configuración
            config_id = request.POST.get('configuracion_id')
            configuracion = get_object_or_404(ConfiguracionTranscripcion, id=config_id, activa=True)
            
            # Parámetros personalizados opcionales
            parametros_custom = {}
            if request.POST.get('custom_modelo_whisper'):
                parametros_custom['modelo_whisper'] = request.POST.get('custom_modelo_whisper')
            if request.POST.get('custom_idioma'):
                parametros_custom['idioma_principal'] = request.POST.get('custom_idioma')
            if request.POST.get('custom_min_hablantes'):
                parametros_custom['min_hablantes'] = int(request.POST.get('custom_min_hablantes'))
            if request.POST.get('custom_max_hablantes'):
                parametros_custom['max_hablantes'] = int(request.POST.get('custom_max_hablantes'))
            
            # Crear transcripción con configuración seleccionada
            transcripcion = Transcripcion.objects.create(
                procesamiento_audio=procesamiento,
                configuracion_utilizada=configuracion,
                usuario_creacion=request.user,
                estado=EstadoTranscripcion.PENDIENTE,
                parametros_personalizados=parametros_custom
            )
            
            log_transcripcion_accion(
                transcripcion, 
                'configuracion_completada', 
                {
                    'configuracion_id': configuracion.id,
                    'configuracion_nombre': configuracion.nombre,
                    'parametros_custom': parametros_custom
                },
                request.user
            )
            
            # Si se marca "iniciar_inmediatamente", lanzar el proceso
            if request.POST.get('iniciar_inmediatamente'):
                task = procesar_transcripcion_completa.delay(transcripcion.id)
                transcripcion.task_id_celery = task.id
                transcripcion.save()
                
                log_transcripcion_accion(
                    transcripcion,
                    'inicio_procesamiento_inmediato',
                    {'task_id': task.id},
                    request.user
                )
                
                messages.success(request, f'Transcripción iniciada correctamente con configuración "{configuracion.nombre}"')
            else:
                messages.success(request, f'Transcripción configurada correctamente. Puede iniciarla cuando desee.')
            
            return redirect('transcripcion:detalle', transcripcion_id=transcripcion.id)
        
        # GET - Mostrar formulario de configuración
        log_transcripcion_navegacion(
            request, 
            None, 
            'configurar_transcripcion',
            {'procesamiento_id': procesamiento_id}
        )
        
        # Obtener información de configuración global del sistema
        from django.conf import settings
        configuracion_global = getattr(settings, 'TRANSCRIPCION_CONFIG', {})
        
        context = {
            'procesamiento': procesamiento,
            'configuraciones': configuraciones,
            'configuracion_activa': configuracion_activa,
            'configuracion_global': configuracion_global,
            'modelos_whisper': ConfiguracionTranscripcion._meta.get_field('modelo_whisper').choices,
            'idiomas': ConfiguracionTranscripcion._meta.get_field('idioma_principal').choices,
        }
        
        return render(request, 'transcripcion/configurar_transcripcion.html', context)
        
    except Exception as e:
        logger.error(f"Error en configurar_transcripcion: {str(e)}")
        log_transcripcion_error(None, 'vista_error', str(e), {'vista': 'configurar_transcripcion'})
        messages.error(request, 'Error al acceder a la configuración de transcripción')
        return redirect('transcripcion:lista')


@login_required
def detalle_transcripcion(request, transcripcion_id):
    """
    Vista detallada de una transcripción con interfaz de chat y reproductor
    """
    try:
        transcripcion = get_object_or_404(
            Transcripcion.objects.select_related('procesamiento_audio', 'configuracion_utilizada'),
            id=transcripcion_id
        )
        
        log_transcripcion_navegacion(
            request, 
            transcripcion, 
            'detalle_transcripcion',
            {'transcripcion_id': transcripcion_id}
        )
        
        # Configuraciones de hablantes
        hablantes_config = {
            config.speaker_id: config 
            for config in transcripcion.configuracion_hablantes.all()
        }
        
        # Historial de ediciones
        historial = transcripcion.historial_ediciones.select_related('usuario').order_by('-fecha_edicion')[:10]
        
        # Formatear JSON para visualización
        import json
        try:
            transcripcion_json_formatted = json.dumps(transcripcion.transcripcion_json or {}, indent=2, ensure_ascii=False)
        except:
            transcripcion_json_formatted = "{}"
            
        try:
            diarizacion_json_formatted = json.dumps(transcripcion.diarizacion_json or {}, indent=2, ensure_ascii=False)
        except:
            diarizacion_json_formatted = "{}"
            
        try:
            conversacion_json_formatted = json.dumps(transcripcion.conversacion_json or {}, indent=2, ensure_ascii=False)
        except:
            conversacion_json_formatted = "{}"
        
        context = {
            'transcripcion': transcripcion,
            'conversacion': transcripcion.conversacion_json,
            'hablantes_config': hablantes_config,
            'historial_ediciones': historial,
            'estados_transcripcion': EstadoTranscripcion.choices,
            'puede_editar': transcripcion.esta_completado,
            'archivo_audio_url': transcripcion.procesamiento_audio.get_archivo_url(),
            # JSON formateados para visualización
            'transcripcion_json_formatted': transcripcion_json_formatted,
            'diarizacion_json_formatted': diarizacion_json_formatted,
            'conversacion_json_formatted': conversacion_json_formatted,
        }
        
        return render(request, 'transcripcion/detalle_transcripcion.html', context)
        
    except Exception as e:
        logger.error(f"Error en detalle_transcripcion: {str(e)}")
        log_transcripcion_error(transcripcion, 'vista_error', str(e), {'vista': 'detalle_transcripcion'})
        messages.error(request, f"Error al cargar transcripción: {str(e)}")
        return redirect('transcripcion:lista')


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def editar_segmento(request, transcripcion_id):
    """
    Edita un segmento específico de la transcripción
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if not transcripcion.esta_completado:
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden editar transcripciones completadas'
            })
        
        data = json.loads(request.body)
        segmento_id = data.get('segmento_id')
        tipo_edicion = data.get('tipo_edicion')
        nuevo_valor = data.get('nuevo_valor')
        comentario = data.get('comentario', '')
        
        # Buscar segmento en la conversación
        conversacion = transcripcion.conversacion_json.copy()
        segmento_encontrado = None
        indice_segmento = None
        
        for i, segmento in enumerate(conversacion):
            if segmento['id'] == segmento_id:
                segmento_encontrado = segmento.copy()
                indice_segmento = i
                break
        
        if not segmento_encontrado:
            return JsonResponse({
                'success': False,
                'error': 'Segmento no encontrado'
            })
        
        # Aplicar edición según tipo
        valor_anterior = {}
        valor_nuevo = {}
        
        if tipo_edicion == 'texto':
            valor_anterior['texto'] = segmento_encontrado['texto']
            conversacion[indice_segmento]['texto'] = nuevo_valor
            valor_nuevo['texto'] = nuevo_valor
            
        elif tipo_edicion == 'hablante':
            valor_anterior['hablante'] = segmento_encontrado['hablante']
            conversacion[indice_segmento]['hablante'] = nuevo_valor
            valor_nuevo['hablante'] = nuevo_valor
            
        elif tipo_edicion == 'tiempo':
            valor_anterior['inicio'] = segmento_encontrado['inicio']
            valor_anterior['fin'] = segmento_encontrado['fin']
            conversacion[indice_segmento]['inicio'] = nuevo_valor['inicio']
            conversacion[indice_segmento]['fin'] = nuevo_valor['fin']
            conversacion[indice_segmento]['duracion'] = nuevo_valor['fin'] - nuevo_valor['inicio']
            valor_nuevo['inicio'] = nuevo_valor['inicio']
            valor_nuevo['fin'] = nuevo_valor['fin']
        
        # Marcar como editado
        conversacion[indice_segmento]['editado'] = True
        conversacion[indice_segmento]['timestamp_edicion'] = timezone.now().isoformat()
        
        # Incrementar versión
        transcripcion.version_actual += 1
        transcripcion.editado_manualmente = True
        transcripcion.fecha_ultima_edicion = timezone.now()
        transcripcion.usuario_ultima_edicion = request.user
        transcripcion.conversacion_json = conversacion
        transcripcion.save()
        
        # Registrar edición
        cambios = {
            'segmento_id': segmento_id,
            'valor_anterior': valor_anterior,
            'valor_nuevo': valor_nuevo,
            'ip_address': request.META.get('REMOTE_ADDR')
        }
        
        historial = log_transcripcion_edicion(
            transcripcion,
            request.user,
            tipo_edicion,
            cambios,
            comentario
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Segmento editado correctamente',
            'nueva_version': transcripcion.version_actual,
            'historial_id': historial.id if historial else None
        })
        
    except Exception as e:
        logger.error(f"Error al editar segmento: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def gestionar_hablantes(request, transcripcion_id):
    """
    Gestiona la configuración de hablantes (renombrar, fusionar, etc.)
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        data = json.loads(request.body)
        accion = data.get('accion')
        
        if accion == 'renombrar':
            speaker_id = data.get('speaker_id')
            nuevo_nombre = data.get('nuevo_nombre')
            cargo = data.get('cargo', '')
            organizacion = data.get('organizacion', '')
            color = data.get('color', '#007bff')
            
            # Actualizar o crear configuración de hablante
            config, created = ConfiguracionHablante.objects.update_or_create(
                transcripcion=transcripcion,
                speaker_id=speaker_id,
                defaults={
                    'nombre_real': nuevo_nombre,
                    'cargo': cargo,
                    'organizacion': organizacion,
                    'color_chat': color,
                    'confirmado_por_usuario': True
                }
            )
            
            # Actualizar mapeo en transcripción
            hablantes_identificados = transcripcion.hablantes_identificados.copy()
            hablantes_identificados[speaker_id] = nuevo_nombre
            transcripcion.hablantes_identificados = hablantes_identificados
            transcripcion.save()
            
            log_transcripcion_edicion(
                transcripcion,
                request.user,
                'hablante',
                {
                    'accion': 'renombrar',
                    'speaker_id': speaker_id,
                    'nuevo_nombre': nuevo_nombre,
                    'configuracion_id': config.id
                },
                f"Hablante {speaker_id} renombrado a {nuevo_nombre}"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Hablante renombrado a "{nuevo_nombre}"'
            })
        
        elif accion == 'fusionar':
            speaker_origen = data.get('speaker_origen')
            speaker_destino = data.get('speaker_destino')
            
            # Actualizar todos los segmentos del hablante origen
            conversacion = transcripcion.conversacion_json.copy()
            segmentos_cambiados = 0
            
            for segmento in conversacion:
                if segmento['hablante'] == speaker_origen:
                    segmento['hablante'] = speaker_destino
                    segmento['editado'] = True
                    segmento['timestamp_edicion'] = timezone.now().isoformat()
                    segmentos_cambiados += 1
            
            transcripcion.conversacion_json = conversacion
            transcripcion.editado_manualmente = True
            transcripcion.fecha_ultima_edicion = timezone.now()
            transcripcion.usuario_ultima_edicion = request.user
            transcripcion.version_actual += 1
            transcripcion.save()
            
            log_transcripcion_edicion(
                transcripcion,
                request.user,
                'fusion',
                {
                    'speaker_origen': speaker_origen,
                    'speaker_destino': speaker_destino,
                    'segmentos_afectados': segmentos_cambiados
                },
                f"Fusión de {speaker_origen} en {speaker_destino}"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Hablantes fusionados. {segmentos_cambiados} segmentos actualizados.'
            })
        
        return JsonResponse({
            'success': False,
            'error': 'Acción no válida'
        })
        
    except Exception as e:
        logger.error(f"Error en gestión de hablantes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })


@login_required
@require_http_methods(["GET"])
def estado_transcripcion(request, transcripcion_id):
    """
    API para obtener el estado actual de una transcripción con todos los detalles
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        # Datos básicos de estado
        response_data = {
            'success': True,
            'transcripcion_id': transcripcion.id,
            'estado': transcripcion.estado,
            'estado_display': transcripcion.get_estado_display(),
            'progreso_porcentaje': transcripcion.progreso_porcentaje,
            'mensaje_estado': getattr(transcripcion, 'mensaje_estado', ''),
            'mensaje_error': transcripcion.mensaje_error,
            'completado': transcripcion.esta_completado,
            'tiene_error': transcripcion.tiene_error,
            'task_id': transcripcion.task_id_celery,
            'fecha_creacion': transcripcion.fecha_creacion.isoformat() if transcripcion.fecha_creacion else None,
            'fecha_actualizacion': transcripcion.fecha_actualizacion.isoformat() if transcripcion.fecha_actualizacion else None,
            'fecha_inicio': transcripcion.tiempo_inicio_proceso.isoformat() if transcripcion.tiempo_inicio_proceso else None,
            'fecha_fin': transcripcion.tiempo_fin_proceso.isoformat() if transcripcion.tiempo_fin_proceso else None,
        }
        
        # Estadísticas
        response_data['estadisticas'] = {
            'numero_hablantes': transcripcion.numero_hablantes,
            'numero_segmentos': transcripcion.numero_segmentos,
            'palabras_totales': transcripcion.palabras_totales,
            'duracion_total': transcripcion.duracion_total,
            'confianza_promedio': transcripcion.confianza_promedio
        }
        
        # Si está completado, incluir todos los resultados
        if transcripcion.estado == EstadoTranscripcion.COMPLETADO:
            response_data.update({
                'texto_completo': transcripcion.texto_completo,
                'transcripcion_json': transcripcion.transcripcion_json,
                'conversacion_json': transcripcion.conversacion_json,
                'diarizacion_json': transcripcion.diarizacion_json,
                'estadisticas_json': transcripcion.estadisticas_json,
                'hablantes_detectados': transcripcion.hablantes_detectados,
                'hablantes_identificados': transcripcion.hablantes_identificados,
                'palabras_clave': transcripcion.palabras_clave,
                'temas_detectados': transcripcion.temas_detectados,
                'parametros_personalizados': transcripcion.parametros_personalizados
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error al obtener estado: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def audio_estado_transcripcion(request, audio_id):
    """
    API para verificar si un audio tiene transcripción activa o completada
    """
    try:
        audio = get_object_or_404(ProcesamientoAudio, id=audio_id)
        
        # Buscar transcripción existente para este audio
        transcripcion = Transcripcion.objects.filter(
            procesamiento_audio=audio
        ).order_by('-fecha_creacion').first()
        
        if not transcripcion:
            return JsonResponse({
                'success': True,
                'transcripcion_activa': False,
                'mensaje': 'No hay transcripción para este audio'
            })
        
        # Si hay transcripción, devolver su estado
        response_data = {
            'success': True,
            'transcripcion_activa': True,
            'transcripcion_id': transcripcion.id,
            'estado': transcripcion.estado,
            'progreso_porcentaje': transcripcion.progreso_porcentaje,
            'task_id': transcripcion.task_id_celery,
            'fecha_inicio': transcripcion.tiempo_inicio_proceso.isoformat() if transcripcion.tiempo_inicio_proceso else None,
        }
        
        # Si está completado, incluir resultados básicos
        if transcripcion.estado == EstadoTranscripcion.COMPLETADO:
            response_data.update({
                'numero_hablantes': transcripcion.numero_hablantes,
                'palabras_totales': transcripcion.palabras_totales,
                'duracion_total': transcripcion.duracion_total,
                'confianza_promedio': transcripcion.confianza_promedio,
                'texto_completo': transcripcion.texto_completo,
                'transcripcion_json': transcripcion.transcripcion_json,
                'conversacion_json': transcripcion.conversacion_json,
                'estadisticas_json': transcripcion.estadisticas_json
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error al verificar estado de audio: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_http_methods(["POST"])
def reiniciar_transcripcion(request, transcripcion_id):
    """
    Reinicia una transcripción que falló o necesita reprocesamiento
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if transcripcion.estado not in [EstadoTranscripcion.ERROR, EstadoTranscripcion.CANCELADO]:
            return JsonResponse({
                'success': False,
                'error': 'Solo se pueden reiniciar transcripciones con error o canceladas'
            })
        
        # Limpiar datos previos
        transcripcion.estado = EstadoTranscripcion.PENDIENTE
        transcripcion.progreso_porcentaje = 0
        transcripcion.mensaje_error = ''
        transcripcion.texto_completo = ''
        transcripcion.transcripcion_json = {}
        transcripcion.diarizacion_json = {}
        transcripcion.conversacion_json = []
        transcripcion.estadisticas_json = {}
        transcripcion.tiempo_inicio_proceso = None
        transcripcion.tiempo_fin_proceso = None
        transcripcion.save()
        
        log_transcripcion_accion(
            transcripcion,
            'reinicio',
            {'usuario_reinicio': request.user.username},
            request.user
        )
        
        # Iniciar nuevo procesamiento
        task = procesar_transcripcion_completa.delay(transcripcion.id)
        transcripcion.task_id_celery = task.id
        transcripcion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Transcripción reiniciada correctamente',
            'task_id': task.id
        })
        
    except Exception as e:
        logger.error(f"Error al reiniciar transcripción: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def vista_resultado_transcripcion(request, transcripcion_id):
    """
    Vista que muestra el resultado completo de una transcripción
    con timeline, texto formateado, hablantes y estadísticas
    """
    try:
        transcripcion = get_object_or_404(
            Transcripcion.objects.select_related(
                'procesamiento_audio', 
                'configuracion', 
                'usuario_creacion'
            ),
            id=transcripcion_id
        )
        
        # Verificar que está completada
        if transcripcion.estado != EstadoTranscripcion.COMPLETADO:
            messages.warning(request, 'La transcripción aún no está completada.')
            return redirect('transcripcion:audios_listos')
        
        # Procesar datos para la vista
        resultado_final = transcripcion.resultado_final or {}
        segmentos = resultado_final.get('segmentos_combinados', [])
        hablantes = transcripcion.hablantes_detectados or {}
        
        # Estadísticas básicas
        estadisticas = {
            'duracion_total': getattr(transcripcion, 'duracion_total', 0),
            'num_palabras': len(transcripcion.texto_completo.split()) if transcripcion.texto_completo else 0,
            'num_segmentos': len(segmentos),
            'num_hablantes': transcripcion.num_hablantes,
            'duracion_procesamiento': None
        }
        
        if transcripcion.fecha_inicio_procesamiento and transcripcion.fecha_completado:
            duracion = transcripcion.fecha_completado - transcripcion.fecha_inicio_procesamiento
            estadisticas['duracion_procesamiento'] = duracion.total_seconds()
        
        # Preparar timeline para visualización
        timeline_data = []
        for i, segmento in enumerate(segmentos):
            timeline_data.append({
                'id': i,
                'inicio': segmento.get('inicio', 0),
                'fin': segmento.get('fin', 0),
                'duracion': segmento.get('duracion', 0),
                'hablante': segmento.get('hablante', 'Desconocido'),
                'hablante_nombre': hablantes.get(segmento.get('hablante'), segmento.get('hablante')),
                'texto': segmento.get('texto', ''),
                'confianza': segmento.get('confianza', 0.0)
            })
        
        # Estadísticas por hablante
        estadisticas_hablantes = {}
        for hablante_id, hablante_nombre in hablantes.items():
            segmentos_hablante = [s for s in segmentos if s.get('hablante') == hablante_id]
            tiempo_total = sum(s.get('duracion', 0) for s in segmentos_hablante)
            palabras_hablante = sum(len(s.get('texto', '').split()) for s in segmentos_hablante)
            
            estadisticas_hablantes[hablante_id] = {
                'nombre': hablante_nombre,
                'tiempo_total': tiempo_total,
                'porcentaje_tiempo': (tiempo_total / estadisticas['duracion_total'] * 100) if estadisticas['duracion_total'] > 0 else 0,
                'num_segmentos': len(segmentos_hablante),
                'num_palabras': palabras_hablante,
                'promedio_palabras_segmento': palabras_hablante / len(segmentos_hablante) if segmentos_hablante else 0
            }
        
        context = {
            'transcripcion': transcripcion,
            'timeline_data': timeline_data,
            'estadisticas': estadisticas,
            'estadisticas_hablantes': estadisticas_hablantes,
            'hablantes': hablantes,
            'configuracion_usada': transcripcion.configuracion,
            'datos_whisper': transcripcion.datos_whisper or {},
            'datos_pyannote': transcripcion.datos_pyannote or {},
            'puede_editar': True,
            'archivo_audio_disponible': bool(
                transcripcion.procesamiento_audio.archivo_audio or 
                transcripcion.procesamiento_audio.archivo_mejorado
            )
        }
        
        return render(request, 'transcripcion/vista_resultado.html', context)
        
    except Exception as e:
        logger.error(f"Error en vista_resultado_transcripcion: {str(e)}")
        messages.error(request, f"Error al cargar resultado: {str(e)}")
        return redirect('transcripcion:audios_listos')


@login_required
@require_http_methods(["GET"])
def exportar_transcripcion(request, transcripcion_id, formato):
    """
    Exporta una transcripción en diferentes formatos (TXT, JSON, SRT)
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if transcripcion.estado != EstadoTranscripcion.COMPLETADO:
            messages.error(request, 'Solo se pueden exportar transcripciones completadas')
            return redirect('transcripcion:vista_resultado', transcripcion_id=transcripcion_id)
        
        audio_titulo = transcripcion.procesamiento_audio.titulo or f"transcripcion_{transcripcion_id}"
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        
        if formato == 'txt':
            # Exportar como texto plano
            filename = f"{audio_titulo}_{timestamp}.txt"
            response = HttpResponse(content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Formatear texto con hablantes y timestamps
            contenido = f"TRANSCRIPCIÓN: {audio_titulo}\n"
            contenido += f"Fecha de procesamiento: {transcripcion.fecha_completado.strftime('%d/%m/%Y %H:%M:%S')}\n"
            contenido += f"Duración: {getattr(transcripcion, 'duracion_total', 0):.2f} segundos\n"
            contenido += f"Número de hablantes: {transcripcion.num_hablantes}\n"
            contenido += f"Configuración: {transcripcion.configuracion.nombre if transcripcion.configuracion else 'Personalizada'}\n"
            contenido += "\n" + "="*80 + "\n\n"
            
            # Agregar transcripción formateada
            if transcripcion.texto_completo:
                contenido += transcripcion.texto_completo
            else:
                # Formatear desde segmentos
                resultado_final = transcripcion.resultado_final or {}
                segmentos = resultado_final.get('segmentos_combinados', [])
                hablantes = transcripcion.hablantes_detectados or {}
                
                for segmento in segmentos:
                    timestamp_inicio = f"{segmento.get('inicio', 0):.2f}s"
                    hablante = hablantes.get(segmento.get('hablante'), segmento.get('hablante', 'Desconocido'))
                    texto = segmento.get('texto', '')
                    contenido += f"[{timestamp_inicio}] {hablante}: {texto}\n"
            
            response.write(contenido.encode('utf-8'))
            return response
        
        elif formato == 'json':
            # Exportar como JSON completo
            filename = f"{audio_titulo}_{timestamp}.json"
            response = HttpResponse(content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            data_export = {
                'metadatos': {
                    'titulo': audio_titulo,
                    'fecha_procesamiento': transcripcion.fecha_completado.isoformat(),
                    'duracion_total': getattr(transcripcion, 'duracion_total', 0),
                    'num_hablantes': transcripcion.num_hablantes,
                    'configuracion_usada': transcripcion.configuracion.nombre if transcripcion.configuracion else 'Personalizada',
                    'modelo_whisper': transcripcion.datos_whisper.get('modelo_usado') if transcripcion.datos_whisper else 'desconocido',
                    'usuario_procesamiento': transcripcion.usuario_creacion.username,
                    'version_transcripcion': getattr(transcripcion, 'version_actual', 1)
                },
                'hablantes': transcripcion.hablantes_detectados or {},
                'segmentos': transcripcion.resultado_final.get('segmentos_combinados', []) if transcripcion.resultado_final else [],
                'texto_completo': transcripcion.texto_completo,
                'estadisticas': transcripcion.estadisticas_procesamiento or {},
                'datos_whisper': transcripcion.datos_whisper or {},
                'datos_pyannote': transcripcion.datos_pyannote or {}
            }
            
            response.write(json.dumps(data_export, indent=2, ensure_ascii=False).encode('utf-8'))
            return response
        
        else:
            messages.error(request, f'Formato "{formato}" no soportado')
            return redirect('transcripcion:vista_resultado', transcripcion_id=transcripcion_id)
        
    except Exception as e:
        logger.error(f"Error al exportar transcripción: {str(e)}")
        messages.error(request, f"Error al exportar: {str(e)}")
        return redirect('transcripcion:vista_resultado', transcripcion_id=transcripcion_id)
        
    except Exception as e:
        logger.error(f"Error al reiniciar transcripción: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })
