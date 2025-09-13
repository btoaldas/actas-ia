"""
Vistas reorganizadas para el módulo de transcripción
Flujo de 4 dashboards: Audios → Proceso → Transcripciones → Detalle
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
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
def dashboard_audios_transcribir(request):
    """
    Dashboard 1: Audios procesados listos para transcribir
    Muestra todos los audios que han completado el procesamiento y están 
    listos para ser transcritos
    """
    try:
        log_transcripcion_navegacion(request, None, 'dashboard_audios_transcribir')
        
        # Audios procesados completamente que NO tienen transcripción
        # Obtener IDs de audios que ya tienen transcripción
        from .models import Transcripcion
        transcripciones_existentes = Transcripcion.objects.values_list('procesamiento_audio_id', flat=True)
        
        # Audios completados que no están en la lista de transcripciones
        audios_query = ProcesamientoAudio.objects.filter(
            estado='completado'
        ).exclude(
            id__in=transcripciones_existentes
        ).select_related('tipo_reunion', 'usuario').order_by('-created_at')
        
        # Filtros
        tipo_reunion = request.GET.get('tipo')
        busqueda = request.GET.get('q')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if tipo_reunion and tipo_reunion != 'todos':
            audios_query = audios_query.filter(tipo_reunion_id=tipo_reunion)
            
        if busqueda:
            audios_query = audios_query.filter(
                Q(titulo__icontains=busqueda) |
                Q(descripcion__icontains=busqueda) |
                Q(participantes__icontains=busqueda)
            )
            
        if fecha_desde:
            audios_query = audios_query.filter(created_at__gte=fecha_desde)
            
        if fecha_hasta:
            audios_query = audios_query.filter(created_at__lte=fecha_hasta)
        
        # Paginación
        paginator = Paginator(audios_query, 12)  # 12 audios por página
        page_number = request.GET.get('page')
        audios_page = paginator.get_page(page_number)
        
        # Estadísticas del dashboard
        estadisticas = {
            'total_audios_listos': audios_query.count(),
            'total_audios_hoy': audios_query.filter(
                created_at__date=timezone.now().date()
            ).count(),
            'total_duracion_pendiente': sum([
                audio.duracion_seg or 0 for audio in audios_query
            ]),
            'tipos_reunion': audios_query.values('tipo_reunion__nombre').annotate(
                count=Count('id')
            ).order_by('-count')
        }
        
        # Tipos de reunión para filtro
        from apps.audio_processing.models import TipoReunion
        tipos_reunion = TipoReunion.objects.all()
        
        context = {
            'audios': audios_page,
            'estadisticas': estadisticas,
            'tipos_reunion': tipos_reunion,
            'filtro_tipo': tipo_reunion,
            'filtro_busqueda': busqueda,
            'filtro_fecha_desde': fecha_desde,
            'filtro_fecha_hasta': fecha_hasta,
            'titulo_pagina': 'Audios por Transcribir - Dashboard V2',
            'subtitulo': f'{estadisticas["total_audios_listos"]} audios procesados disponibles (Nueva arquitectura)'
        }
        
        return render(request, 'transcripcion/dashboard_audios.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard_audios_transcribir: {str(e)}")
        messages.error(request, f"Error al cargar audios: {str(e)}")
        
        # En caso de error, mostrar página vacía en lugar de redirigir
        context = {
            'audios': [],
            'estadisticas': {
                'total_audios_listos': 0,
                'total_audios_hoy': 0,
                'total_duracion_pendiente': 0,
                'tipos_reunion': []
            },
            'tipos_reunion': [],
            'titulo_pagina': 'Audios Listos para Transcribir',
            'subtitulo': 'Error al cargar datos'
        }
        return render(request, 'transcripcion/dashboard_audios.html', context)


@login_required  
def dashboard_transcripciones_hechas(request):
    """
    Dashboard 3: Transcripciones completadas y en proceso
    Muestra todas las transcripciones existentes con sus estados
    """
    try:
        log_transcripcion_navegacion(request, None, 'dashboard_transcripciones_hechas')
        
        # Transcripciones existentes (base)
        transcripciones_query = Transcripcion.objects.select_related(
            'procesamiento_audio', 'configuracion_utilizada', 'usuario_creacion'
        )
        
        # Filtros
        estado_filtro = request.GET.get('estado')
        busqueda = request.GET.get('q')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if estado_filtro and estado_filtro != 'todos':
            transcripciones_query = transcripciones_query.filter(estado=estado_filtro)
            
        if busqueda:
            transcripciones_query = transcripciones_query.filter(
                Q(procesamiento_audio__titulo__icontains=busqueda) |
                Q(procesamiento_audio__descripcion__icontains=busqueda) |
                Q(texto_completo__icontains=busqueda)
            )
            
        if fecha_desde:
            transcripciones_query = transcripciones_query.filter(fecha_creacion__gte=fecha_desde)
            
        if fecha_hasta:
            transcripciones_query = transcripciones_query.filter(fecha_creacion__lte=fecha_hasta)
        
        # Ordenación
        orden = request.GET.get('orden')  # ejemplos: -fecha_creacion, fecha_creacion, titulo, -titulo, tipo_reunion, -tipo_reunion, estado, -estado
        if orden:
            # Mapear campos amigables a campos reales
            mapping = {
                'fecha_creacion': 'fecha_creacion',
                '-fecha_creacion': '-fecha_creacion',
                'fecha_publicacion': 'fecha_creacion',  # no existe explicitamente; usar fecha_creacion como proxy
                '-fecha_publicacion': '-fecha_creacion',
                'titulo': 'procesamiento_audio__titulo',
                '-titulo': '-procesamiento_audio__titulo',
                'tipo_reunion': 'procesamiento_audio__tipo_reunion__nombre',
                '-tipo_reunion': '-procesamiento_audio__tipo_reunion__nombre',
                'estado': 'estado',
                '-estado': '-estado',
            }
            transcripciones_query = transcripciones_query.order_by(mapping.get(orden, '-fecha_creacion'))
        else:
            transcripciones_query = transcripciones_query.order_by('-fecha_creacion')

        # Paginación
        paginator = Paginator(transcripciones_query, 10)  # 10 transcripciones por página
        page_number = request.GET.get('page')
        transcripciones_page = paginator.get_page(page_number)
        
        # Estadísticas del dashboard
        estadisticas = {
            'total_transcripciones': transcripciones_query.count(),
            'completadas': transcripciones_query.filter(estado='completado').count(),
            'en_proceso': transcripciones_query.filter(
                estado__in=['pendiente', 'en_procesamiento', 'transcribiendo', 'diarizando']
            ).count(),
            'con_errores': transcripciones_query.filter(estado='error').count(),
            'transcripciones_hoy': transcripciones_query.filter(
                fecha_creacion__date=timezone.now().date()
            ).count(),
            'por_estado': transcripciones_query.values('estado').annotate(
                count=Count('id')
            ).order_by('-count')
        }
        
        # Tipos de reunión para filtro
        from apps.audio_processing.models import TipoReunion
        tipos_reunion = TipoReunion.objects.all()
        filtro_tipo = request.GET.get('tipo')

        context = {
            'transcripciones': transcripciones_page,
            'estadisticas': estadisticas,
            'estados_transcripcion': EstadoTranscripcion.choices,
            'tipos_reunion': tipos_reunion,
            'filtro_tipo': filtro_tipo,
            'filtro_estado': estado_filtro,
            'filtro_busqueda': busqueda,
            'filtro_fecha_desde': fecha_desde,
            'filtro_fecha_hasta': fecha_hasta,
            'titulo_pagina': 'Transcripciones Realizadas',
            'subtitulo': f'{estadisticas["total_transcripciones"]} transcripciones en total'
        }
        
        return render(request, 'transcripcion/dashboard_transcripciones.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard_transcripciones_hechas: {str(e)}")
        messages.error(request, f"Error al cargar transcripciones: {str(e)}")
        return render(request, 'transcripcion/dashboard_transcripciones.html', {
            'error': True,
            'titulo_pagina': 'Error',
            'subtitulo': 'No se pudieron cargar las transcripciones'
        })


@login_required
def proceso_transcripcion(request, audio_id):
    """
    Dashboard 2: Proceso de configuración y ejecución de transcripción
    Maneja todo el flujo desde configuración hasta inicio del procesamiento
    """
    try:
        audio = get_object_or_404(ProcesamientoAudio, id=audio_id, estado='completado')
        
        # Verificar si ya existe una transcripción para este audio
        transcripcion_existente = Transcripcion.objects.filter(
            procesamiento_audio=audio
        ).first()
        
        if transcripcion_existente:
            messages.info(request, 'Este audio ya tiene una transcripción asociada.')
            return redirect('transcripcion:detalle_transcripcion', 
                          transcripcion_id=transcripcion_existente.id)
        
        log_transcripcion_navegacion(request, None, 'proceso_transcripcion', 
                                   parametros={'audio_id': audio_id})
        
        if request.method == 'POST':
            try:
                # Obtener configuración
                configuracion = ConfiguracionTranscripcion.objects.filter(
                    activa=True
                ).first()
                
                if not configuracion:
                    # Crear configuración básica si no existe
                    configuracion = ConfiguracionTranscripcion.objects.create(
                        nombre="Configuración Automática",
                        descripcion="Configuración creada automáticamente",
                        usuario_creacion=request.user,
                        activa=True
                    )
                
                # Obtener datos del formulario con CONFIGURACIÓN ROBUSTA POR DEFECTO
                modelo_whisper = request.POST.get('modelo_whisper', configuracion.modelo_whisper)
                idioma = request.POST.get('idioma', configuracion.idioma_principal)
                
                # ===== DIARIZACIÓN OBLIGATORIAMENTE ACTIVA Y ROBUSTA =====
                diarizacion_activa = request.POST.get('diarizacion_activa', 'on') == 'on'
                if not diarizacion_activa:
                    # FORZAR activación para máxima eficacia
                    diarizacion_activa = True
                    logger.info("AUDIT - Diarización forzada a ACTIVA para máxima eficacia")
                
                max_hablantes = request.POST.get('numero_max_hablantes', configuracion.max_hablantes)
                
                # PARÁMETROS ROBUSTOS ADICIONALES para pyannote
                clustering_threshold = float(request.POST.get('clustering_threshold', '0.5'))  # Valor optimizado
                embedding_batch_size = int(request.POST.get('embedding_batch_size', '32'))
                segmentation_batch_size = int(request.POST.get('segmentation_batch_size', '32'))
                modelo_diarizacion = request.POST.get('modelo_diarizacion', 'pyannote/speaker-diarization-3.1')
                
                # Obtener participantes desde el formulario con estructura completa
                participantes_json = request.POST.get('participantes_json', '[]')
                num_hablantes_detectados = request.POST.get('num_hablantes_detectados', '0')
                
                try:
                    import json
                    participantes = json.loads(participantes_json) if participantes_json else []
                except:
                    participantes = []
                
                # Si no hay participantes en JSON, intentar recopilar del formulario tradicional
                if not participantes:
                    for i in range(1, 11):  # Máximo 10 participantes
                        nombres = request.POST.get(f'participante_nombres_{i}', '')
                        apellidos = request.POST.get(f'participante_apellidos_{i}', '')
                        cargo = request.POST.get(f'participante_cargo_{i}', '')
                        institucion = request.POST.get(f'participante_institucion_{i}', '')
                        id_hablante = request.POST.get(f'participante_id_{i}', f'hablante_{i}')
                        activo = request.POST.get(f'participante_activo_{i}') == 'on'
                        
                        if nombres.strip() or apellidos.strip():
                            participantes.append({
                                'orden': i,
                                'nombres': nombres.strip(),
                                'apellidos': apellidos.strip(),
                                'nombre_completo': f"{nombres} {apellidos}".strip(),
                                'cargo': cargo.strip(),
                                'institucion': institucion.strip(),
                                'id': id_hablante,
                                'activo': activo
                            })
                
                # Crear transcripción
                transcripcion = Transcripcion.objects.create(
                    procesamiento_audio=audio,
                    configuracion_utilizada=configuracion,
                    estado=EstadoTranscripcion.PENDIENTE,
                    usuario_creacion=request.user
                )
                
                # ===== CONFIGURACIÓN ROBUSTA PERSONALIZADA =====
                configuracion_personalizada = {
                    # Configuración básica
                    'modelo_whisper': modelo_whisper,
                    'idioma': idioma,
                    'diarizacion_activa': diarizacion_activa,  # Siempre True
                    
                    # Configuración de hablantes inteligente
                    'max_hablantes': int(max_hablantes) if max_hablantes else (len(participantes) + 2 if participantes else configuracion.max_hablantes),
                    'min_hablantes': max(1, len(participantes) - 1) if participantes else 1,
                    
                    # PARÁMETROS ROBUSTOS DE DIARIZACIÓN
                    'modelo_diarizacion': modelo_diarizacion,
                    'clustering_threshold': clustering_threshold,
                    'embedding_batch_size': embedding_batch_size,
                    'segmentation_batch_size': segmentation_batch_size,
                    'onset_threshold': 0.5,
                    'offset_threshold': 0.5,
                    'min_duration_on': 0.1,  # Mínimo 100ms para habla
                    'min_duration_off': 0.1,  # Mínimo 100ms para silencio
                    
                    # CONFIGURACIÓN DE MAPEO DE SPEAKERS
                    'tipo_mapeo_speakers': 'orden_json',  # Usar orden del JSON del usuario, no orden temporal
                    
                    # Información del audio y participantes
                    'participantes_esperados': participantes,
                    'hablantes_predefinidos': participantes,  # Alias para el backend
                    'audio_titulo': audio.titulo,
                    'audio_id': audio.id,
                    'usuario_id': request.user.id
                }
                
                # Actualizar metadatos de la transcripción Y parámetros personalizados
                transcripcion.metadatos_configuracion = configuracion_personalizada
                transcripcion.parametros_personalizados = configuracion_personalizada  # ¡ESTO ES CLAVE!
                transcripcion.save()
                
                # Iniciar tarea de transcripción
                try:
                    # Intentar importar la tarea de Celery
                    from apps.transcripcion.tasks import procesar_transcripcion_completa
                    
                    task_result = procesar_transcripcion_completa.apply_async(
                        args=[transcripcion.id]
                    )
                    
                    # Guardar ID de tarea en el campo correcto
                    transcripcion.task_id_celery = task_result.id
                    transcripcion.estado = EstadoTranscripcion.EN_PROCESO
                    transcripcion.save()
                    
                    logger.info(f"Tarea de transcripción iniciada: {task_result.id}")
                    
                except ImportError as e:
                    logger.warning(f"No se pudo importar la tarea de Celery: {str(e)}")
                    # Si no se puede importar, marcar como pendiente
                    transcripcion.estado = EstadoTranscripcion.PENDIENTE
                    transcripcion.save()
                    task_result = None
                    
                except Exception as e:
                    logger.warning(f"Celery no disponible, transcripción quedará pendiente: {str(e)}")
                    # Si Celery no está disponible, marcar como pendiente
                    transcripcion.estado = EstadoTranscripcion.PENDIENTE
                    transcripcion.save()
                    task_result = None
                
                # Log de acción
                log_transcripcion_accion(
                    transcripcion,
                    'transcripcion_iniciada',
                    {
                        'configuracion_id': configuracion.id,
                        'task_id': getattr(task_result, 'id', None) if 'task_result' in locals() else None,
                        'audio_titulo': audio.titulo,
                        'participantes_count': len(participantes),
                        'modelo_whisper': modelo_whisper,
                        'diarizacion_activa': diarizacion_activa
                    }
                )
                
                messages.success(request, f'Transcripción iniciada para "{audio.titulo}"')
                
                # Respuesta AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'transcripcion_id': transcripcion.id,
                        'task_id': getattr(task_result, 'id', None) if 'task_result' in locals() else None,
                        'mensaje': f'Transcripción iniciada para "{audio.titulo}"',
                        'redirect_to_progress': True
                    })
                
                # Para solicitudes normales, reconstruir contexto para mostrar progreso
                # Obtener configuraciones
                configuraciones = ConfiguracionTranscripcion.objects.filter(activa=True)
                
                # Reconstruir participantes con datos completos
                participantes_audio = getattr(audio, 'participantes_detallados', [])
                if not participantes_audio:
                    participantes_audio = []
                
                contexto = {
                    'audio': audio,
                    'configuraciones': configuraciones,
                    'configuracion_activa': configuracion,
                    'participantes': participantes_audio,
                    'transcripcion_iniciada': True,
                    'transcripcion_id': transcripcion.id,
                    'task_id': getattr(task_result, 'id', None) if 'task_result' in locals() else None,
                    'mostrar_progreso': True,
                    'titulo_pagina': 'Configurar Transcripción - Procesando',
                    'subtitulo': f'Procesando audio: {audio.titulo}'
                }
                
                messages.success(request, f'Transcripción iniciada para "{audio.titulo}". Monitoreando progreso...')
                return render(request, 'transcripcion/proceso_transcripcion.html', contexto)
                
            except Exception as e:
                logger.error(f"Error iniciando transcripción: {str(e)}")
                messages.error(request, f"Error al iniciar transcripción: {str(e)}")
                
                # Respuesta AJAX en caso de error
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
        
        
        # GET request - mostrar formulario de configuración
        configuracion_defecto = ConfiguracionTranscripcion.objects.filter(
            activa=True
        ).first()
        
        # Si no hay configuración activa, crear una básica
        if not configuracion_defecto:
            from django.contrib.auth.models import User
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                configuracion_defecto = ConfiguracionTranscripcion.objects.create(
                    nombre="Configuración por Defecto",
                    descripcion="Configuración automática del sistema",
                    usuario_creacion=admin_user,
                    activa=True
                )
        
        # ===== OPCIONES ROBUSTAS PARA EL TEMPLATE =====
        modelos_whisper = [
            {'value': 'tiny', 'label': 'Tiny (39 MB)', 'descripcion': 'Rápido, menor precisión'},
            {'value': 'base', 'label': 'Base (74 MB)', 'descripcion': 'Balanceado - RECOMENDADO', 'recomendado': True},
            {'value': 'small', 'label': 'Small (244 MB)', 'descripcion': 'Buena precisión'},
            {'value': 'medium', 'label': 'Medium (769 MB)', 'descripcion': 'Alta precisión'},
            {'value': 'large', 'label': 'Large (1550 MB)', 'descripcion': 'Máxima precisión'},
            {'value': 'large-v2', 'label': 'Large V2 (1550 MB)', 'descripcion': 'Versión optimizada'},
            {'value': 'large-v3', 'label': 'Large V3 (1550 MB)', 'descripcion': 'Última versión'},
        ]
        
        idiomas_disponibles = [
            {'value': 'es', 'label': 'Español', 'recomendado': True},
            {'value': 'en', 'label': 'Inglés'},
            {'value': 'auto', 'label': 'Detección automática'},
        ]
        
        # MODELOS DE DIARIZACIÓN ROBUSTOS - MEJORES OPCIONES
        modelos_diarizacion = [
            {'value': 'pyannote/speaker-diarization-3.1', 'label': 'Pyannote 3.1 (MÁXIMA EFICACIA)', 'descripcion': 'Última versión, máxima precisión', 'recomendado': True},
            {'value': 'pyannote/speaker-diarization@2.1', 'label': 'Pyannote 2.1 (Estable)', 'descripcion': 'Versión estable y probada'},
            {'value': 'pyannote/speaker-diarization', 'label': 'Pyannote Básico', 'descripcion': 'Versión básica'},
        ]
        
        # CONFIGURACIÓN ROBUSTA POR DEFECTO
        configuracion_robusta_defecto = {
            'diarizacion_activa': True,  # SIEMPRE ACTIVA
            'clustering_threshold': 0.5,  # Valor optimizado
            'embedding_batch_size': 32,
            'segmentation_batch_size': 32,
            'modelo_diarizacion': 'pyannote/speaker-diarization-3.1'  # Mejor modelo
        }
        
        # Obtener metadatos del audio y participantes detallados
        participantes_detectados = []
        
        # Priorizar participantes_detallados (estructura completa del módulo de audio)
        if hasattr(audio, 'participantes_detallados') and audio.participantes_detallados:
            for i, participante in enumerate(audio.participantes_detallados):
                participante_info = {
                    'id': f'hablante_{i+1}',
                    'orden': participante.get('orden', i+1),
                    'nombres': participante.get('nombres', ''),
                    'apellidos': participante.get('apellidos', ''),
                    'nombre_completo': f"{participante.get('nombres', '')} {participante.get('apellidos', '')}".strip(),
                    'cargo': participante.get('cargo', ''),
                    'institucion': participante.get('institucion', ''),
                    'activo': True
                }
                participantes_detectados.append(participante_info)
        
        # Si no hay participantes_detallados, usar metadatos_procesamiento como fallback
        elif hasattr(audio, 'metadatos_procesamiento') and audio.metadatos_procesamiento:
            participantes_info = audio.metadatos_procesamiento.get('participantes', [])
            if isinstance(participantes_info, list):
                for i, participante in enumerate(participantes_info):
                    participante_info = {
                        'id': f'hablante_{i+1}',
                        'orden': i+1,
                        'nombres': participante.get('nombres', ''),
                        'apellidos': participante.get('apellidos', ''),
                        'nombre_completo': participante.get('nombre', ''),
                        'cargo': participante.get('cargo', ''),
                        'institucion': participante.get('institucion', ''),
                        'activo': True
                    }
                    participantes_detectados.append(participante_info)
        
        # Como último recurso, usar el campo participantes (texto plano)
        elif audio.participantes:
            participantes_list = [p.strip() for p in audio.participantes.split(',') if p.strip()]
            for i, nombre in enumerate(participantes_list):
                participante_info = {
                    'id': f'hablante_{i+1}',
                    'orden': i+1,
                    'nombres': nombre,
                    'apellidos': '',
                    'nombre_completo': nombre,
                    'cargo': '',
                    'institucion': '',
                    'activo': True
                }
                participantes_detectados.append(participante_info)
        
        # Información adicional del audio para el contexto
        info_audio_extendida = {
            'duracion_segundos': getattr(audio, 'duracion_seg', 0),
            'sample_rate': audio.metadatos_procesamiento.get('processed_sample_rate', 16000) if audio.metadatos_procesamiento else 16000,
            'calidad_audio': audio.metadatos_procesamiento.get('compression_ratio', 1.0) if audio.metadatos_procesamiento else 1.0,
            'pipeline_version': audio.metadatos_procesamiento.get('pipeline_version', 'v1.0') if audio.metadatos_procesamiento else 'v1.0',
            'total_participantes_detectados': len(participantes_detectados)
        }
        
        context = {
            'audio': audio,
            'configuracion_defecto': configuracion_defecto,
            'configuracion_seleccionada': configuracion_defecto,
            'configuracion': {
                'modelos_whisper': modelos_whisper,
                'idiomas_disponibles': idiomas_disponibles,
                'modelos_diarizacion': modelos_diarizacion,
            },
            # ===== CONFIGURACIÓN ROBUSTA POR DEFECTO =====
            'configuracion_robusta': configuracion_robusta_defecto,
            'participantes_detectados': participantes_detectados,
            'info_audio_extendida': info_audio_extendida,
            'num_hablantes_sugerido': len(participantes_detectados) if participantes_detectados else configuracion_defecto.max_hablantes if configuracion_defecto else 3,
            'diarizacion_forzada_activa': True,  # Indicar que diarización es obligatoria
            'titulo_pagina': 'Configurar Transcripción - ROBUSTA',
            'subtitulo': f'Audio: {audio.titulo} (Diarización optimizada automática)',
            # Información adicional para el template
            'mejores_parametros': {
                'clustering_threshold_recomendado': 0.5,
                'batch_size_recomendado': 32,
                'modelo_recomendado': 'pyannote/speaker-diarization-3.1'
            }
        }
        
        return render(request, 'transcripcion/proceso_transcripcion.html', context)
        
    except Exception as e:
        logger.error(f"Error en proceso_transcripcion: {str(e)}")
        messages.error(request, f"Error en proceso de transcripción: {str(e)}")
        return redirect('transcripcion:audios_dashboard')


@login_required
def detalle_transcripcion_dashboard(request, transcripcion_id):
    """
    Vista de detalle de una transcripción específica con editor avanzado
    """
    try:
        # Obtener la transcripción
        transcripcion = get_object_or_404(
            Transcripcion.objects.select_related(
                'procesamiento_audio__usuario',
                'procesamiento_audio__tipo_reunion'
            ),
            id=transcripcion_id
        )
        
        # Obtener la estructura JSON completa (nueva estructura)
        estructura = getattr(transcripcion, 'conversacion_json', {}) or {}

        # Normalización robusta de la estructura esperada
        if not isinstance(estructura, dict):
            estructura = {"cabecera": {}, "conversacion": [], "texto_estructurado": "", "metadata": {}}

        # cabecera
        cabecera = estructura.get('cabecera', {})
        if not isinstance(cabecera, dict):
            cabecera = {}
        # mapeo_hablantes
        mapeo_hablantes = cabecera.get('mapeo_hablantes', {})
        if not isinstance(mapeo_hablantes, dict):
            # Si viene como lista o string, convertir a dict simple
            if isinstance(mapeo_hablantes, list):
                nuevo_map = {}
                for idx, item in enumerate(mapeo_hablantes, start=1):
                    key = str(idx)
                    if isinstance(item, dict):
                        nuevo_map[key] = item
                    else:
                        nuevo_map[key] = {"nombre": str(item)}
                mapeo_hablantes = nuevo_map
            elif isinstance(mapeo_hablantes, str):
                mapeo_hablantes = {"1": {"nombre": mapeo_hablantes}}
            else:
                mapeo_hablantes = {}
        # Refuerzo: asegurar que todos los valores sean dicts con al menos 'nombre'
        for k, v in list(mapeo_hablantes.items()):
            if isinstance(v, dict):
                # Si no tiene ninguna clave de nombre, intentar construirla
                if not any(key in v for key in ('nombre', 'nombre_real', 'nombre_completo')):
                    # Si tiene apellidos, combinar
                    nombre = v.get('nombre', None)
                    apellidos = v.get('apellidos', None)
                    if nombre and apellidos:
                        v['nombre'] = f"{nombre} {apellidos}".strip()
                    elif v.get('nombre_completo'):
                        v['nombre'] = v['nombre_completo']
                    else:
                        v['nombre'] = str(v)
            else:
                # Si no es dict, convertirlo
                mapeo_hablantes[k] = {'nombre': str(v)}
        cabecera['mapeo_hablantes'] = mapeo_hablantes
        estructura['cabecera'] = cabecera

        # conversacion
        conversacion = estructura.get('conversacion', [])
        if not isinstance(conversacion, list):
            conversacion = []
        estructura['conversacion'] = conversacion

        # texto_estructurado
        if not isinstance(estructura.get('texto_estructurado', ''), str):
            estructura['texto_estructurado'] = str(estructura.get('texto_estructurado', ''))

        # metadata
        metadata = estructura.get('metadata', {})
        if not isinstance(metadata, dict):
            metadata = {}
        estructura['metadata'] = metadata

        # URL del archivo de audio (preferir archivo_mejorado si existe)
        archivo_audio_url = None
        try:
            # Intentar primero con el archivo mejorado
            if hasattr(transcripcion.procesamiento_audio, 'archivo_mejorado') and transcripcion.procesamiento_audio.archivo_mejorado:
                archivo_audio_url = transcripcion.procesamiento_audio.archivo_mejorado.url
                logger.info(f"Usando archivo mejorado para transcripción {transcripcion_id}")
            # Fallback al archivo original
            elif hasattr(transcripcion.procesamiento_audio, 'archivo_audio') and transcripcion.procesamiento_audio.archivo_audio:
                archivo_audio_url = transcripcion.procesamiento_audio.archivo_audio.url
                logger.info(f"Usando archivo original para transcripción {transcripcion_id}")
        except Exception as e:
            logger.warning(f"No se pudo obtener URL de audio: {e}")

        # Preparar JSON formateados para el template (compatibilidad)
        import json
        try:
            transcripcion_json_formatted = json.dumps(getattr(transcripcion, 'transcripcion_json', {}) or {}, indent=2, ensure_ascii=False)
        except Exception:
            transcripcion_json_formatted = "{}"
        try:
            diarizacion_json_formatted = json.dumps(getattr(transcripcion, 'diarizacion_json', {}) or {}, indent=2, ensure_ascii=False)
        except Exception:
            diarizacion_json_formatted = "{}"
        try:
            conversacion_json_formatted = json.dumps(estructura, indent=2, ensure_ascii=False)
        except Exception:
            conversacion_json_formatted = "{}"

        context = {
            'titulo_pagina': f'Editor Avanzado: {transcripcion.procesamiento_audio.titulo}',
            'subtitulo': f'Edición completa de la transcripción realizada el {transcripcion.fecha_creacion.strftime("%d/%m/%Y")}',
            'transcripcion': transcripcion,
            'estructura': estructura,  # Nueva estructura para el editor
            'estructura_json': json.dumps(estructura, ensure_ascii=False),  # JSON string para JavaScript
            'archivo_audio_url': archivo_audio_url,
            # JSON formateados para compatibilidad
            'transcripcion_json_formatted': transcripcion_json_formatted,
            'diarizacion_json_formatted': diarizacion_json_formatted,
            'conversacion_json_formatted': conversacion_json_formatted,
        }
        
        # Usar el template simple que funciona 100%
        return render(request, 'transcripcion/detalle_simple.html', context)
        
    except Exception as e:
        logger.error(f"Error en detalle_transcripcion_dashboard: {str(e)}")
        messages.error(request, "Error al cargar el detalle de la transcripción")
        return redirect('transcripcion:transcripciones_dashboard')


@login_required
@require_http_methods(["POST"])
def revertir_audios_por_transcribir(request, transcripcion_id):
    """
    Revierte una transcripción ya creada para que el audio vuelva a estar disponible
    en el dashboard de "Audios por Transcribir". NO reprocesa nada, solo elimina la
    transcripción y ajusta el estado del audio a 'completado'.
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)

        # Proteger contra reversiones mientras hay procesamiento activo
        if transcripcion.estado in [
            EstadoTranscripcion.EN_PROCESO,
            EstadoTranscripcion.TRANSCRIBIENDO,
            EstadoTranscripcion.DIARIZANDO,
            EstadoTranscripcion.PROCESANDO,
        ]:
            messages.error(
                request,
                'No se puede revertir mientras la transcripción está en proceso.'
            )
            return redirect('transcripcion:detalle_transcripcion', transcripcion_id=transcripcion.id)

        procesamiento = transcripcion.procesamiento_audio

        # Audit trail antes de eliminar
        try:
            log_transcripcion_accion(
                transcripcion,
                'revertir_audios_por_transcribir',
                {
                    'procesamiento_id': procesamiento.id,
                    'estado_transcripcion': transcripcion.estado,
                    'estado_audio_previo': getattr(procesamiento, 'estado', None),
                },
                request.user
            )
        except Exception as e:
            logger.warning(f"No se pudo registrar log de acción antes de revertir: {e}")

        # Eliminar transcripción (cascadeará configuraciones y ediciones)
        transcripcion.delete()

        # Asegurar que el audio quede listo para dashboard de audios por transcribir
        try:
            if getattr(procesamiento, 'estado', None) != 'completado':
                procesamiento.estado = 'completado'
            # Opcionalmente normalizamos progreso/mensaje
            procesamiento.progreso = 100
            procesamiento.mensaje_estado = ''
            procesamiento.save(update_fields=['estado', 'progreso', 'mensaje_estado', 'updated_at'])
        except Exception as e:
            logger.warning(f"No se pudo actualizar estado del audio tras revertir: {e}")

        messages.success(
            request,
            'Transcripción revertida. El audio está nuevamente disponible para transcribir.'
        )
        return redirect('transcripcion:audios_dashboard')

    except Exception as e:
        logger.error(f"Error al revertir a audios por transcribir: {str(e)}")
        messages.error(request, f"Error al revertir: {str(e)}")
        return redirect('transcripcion:transcripciones_dashboard')


@login_required
def api_estado_transcripcion(request, transcripcion_id):
    """
    API para consultar el estado de una transcripción en tiempo real
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        # Obtener información del estado de Celery si existe task_id
        task_info = None
        if getattr(transcripcion, 'task_id_celery', None):
            try:
                from celery.result import AsyncResult
                result = AsyncResult(transcripcion.task_id_celery)
                task_info = {
                    'state': result.state,
                    'info': result.info if result.info else {},
                    'successful': result.successful(),
                    'failed': result.failed(),
                    'ready': result.ready()
                }
            except Exception as e:
                logger.warning(f"Error consultando estado de Celery: {e}")
                task_info = {'error': str(e)}
        
        # Preparar respuesta
        response_data = {
            'transcripcion_id': transcripcion.id,
            'estado': transcripcion.estado,
            'progreso': getattr(transcripcion, 'progreso', 0),
            'mensaje_estado': getattr(transcripcion, 'mensaje_estado', ''),
            'fecha_creacion': transcripcion.fecha_creacion.isoformat(),
            'fecha_inicio_procesamiento': transcripcion.fecha_inicio_procesamiento.isoformat() if hasattr(transcripcion, 'fecha_inicio_procesamiento') and transcripcion.fecha_inicio_procesamiento else None,
            'fecha_finalizacion': transcripcion.fecha_finalizacion.isoformat() if hasattr(transcripcion, 'fecha_finalizacion') and transcripcion.fecha_finalizacion else None,
            'task_info': task_info,
            'audio_titulo': transcripcion.procesamiento_audio.titulo,
            'duracion_audio': getattr(transcripcion.procesamiento_audio, 'duracion_segundos', 0),
            'es_completa': transcripcion.estado in ['completado', 'curada'],
            'tiene_errores': transcripcion.estado == 'error'
        }
        
        # Si está completada, agregar datos adicionales
        if transcripcion.estado in ['completado', 'curada']:
            # Obtener datos de conversación para el chat
            conversacion_json = getattr(transcripcion, 'conversacion_json', {})
            segmentos_conversacion = conversacion_json.get('segmentos', [])
            
            response_data.update({
                'texto_transcripcion': getattr(transcripcion, 'texto_transcripcion', ''),
                'num_hablantes': getattr(transcripcion, 'num_hablantes_detectados', 0),
                'segmentos_count': len(getattr(transcripcion, 'segmentos_hablantes', [])),
                'estadisticas': getattr(transcripcion, 'estadisticas_procesamiento', {}),
                'conversacion': {
                    'segmentos': segmentos_conversacion,
                    'hablantes': conversacion_json.get('hablantes', {}),
                    'metadatos': conversacion_json.get('metadatos', {})
                },
                'transcripcion_json': getattr(transcripcion, 'transcripcion_json', {}),
                'diarizacion_json': getattr(transcripcion, 'diarizacion_json', {}),
                'estadisticas_json': getattr(transcripcion, 'estadisticas_json', {})
            })
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error en api_estado_transcripcion: {str(e)}")
        return JsonResponse({
            'error': True,
            'mensaje': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_actualizar_json(request, transcripcion_id):
    """
    API para actualizar los datos JSON de una transcripción
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        import json
        json_data = json.loads(request.POST.get('json_data', '{}'))
        
        # Actualizar campos JSON según los datos recibidos
        if 'transcripcion' in json_data:
            transcripcion.transcripcion_json = json_data['transcripcion']
        
        if 'diarizacion' in json_data:
            transcripcion.diarizacion_json = json_data['diarizacion']
        
        if 'conversacion' in json_data:
            transcripcion.conversacion_json = json_data['conversacion']
            # Actualizar estadísticas basadas en la conversación
            transcripcion.numero_segmentos = len(json_data['conversacion'])
            hablantes_unicos = set(seg.get('hablante', 'Desconocido') for seg in json_data['conversacion'])
            transcripcion.numero_hablantes = len(hablantes_unicos)
        
        transcripcion.fecha_ultima_edicion = timezone.now()
        transcripcion.usuario_ultima_edicion = request.user
        transcripcion.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'JSON actualizado correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error en api_actualizar_json: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# @login_required  # Comentado temporalmente para debug
@require_http_methods(["POST"])
@csrf_exempt
def api_editar_segmento(request, transcripcion_id):
    """
    API para editar un segmento específico de la conversación
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        # Debug: Imprimir datos recibidos
        logger.info(f"Datos recibidos: {dict(request.POST)}")
        
        segmento_id = int(request.POST.get('segmento_id', -1))
        hablante = request.POST.get('hablante', '')
        texto = request.POST.get('texto', '')
        inicio = float(request.POST.get('inicio', 0))
        fin = float(request.POST.get('fin', 0))
        
        # Validaciones más específicas
        if segmento_id < 0:
            return JsonResponse({
                'success': False,
                'error': 'ID de segmento no válido'
            })
        
        # Validar que el segmento existe - CORREGIDO para estructura dict
        estructura = transcripcion.conversacion_json or {}
        conversacion = estructura.get('conversacion', []) if isinstance(estructura, dict) else []
        
        if segmento_id >= len(conversacion):
            return JsonResponse({
                'success': False,
                'error': f'Segmento {segmento_id} no encontrado. Total segmentos: {len(conversacion)}'
            })
        
        if not texto.strip():
            return JsonResponse({
                'success': False,
                'error': 'El texto no puede estar vacío'
            })
        
        if inicio >= fin:
            return JsonResponse({
                'success': False,
                'error': 'El tiempo de inicio debe ser menor al tiempo de fin'
            })
        
        # Actualizar segmento
        conversacion[segmento_id].update({
            'hablante': hablante,
            'texto': texto,
            'inicio': inicio,
            'fin': fin,
            'editado': True,
            'editado_por': request.user.username if request.user.is_authenticated else 'anonimo',
            'fecha_edicion': timezone.now().isoformat()
        })
        
        # Guardar estructura completa actualizada
        estructura['conversacion'] = conversacion
        transcripcion.conversacion_json = estructura
        transcripcion.fecha_ultima_edicion = timezone.now()
        if request.user.is_authenticated:
            transcripcion.usuario_ultima_edicion = request.user
        transcripcion.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Segmento editado correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error en api_editar_segmento: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# @login_required  # Comentado temporalmente para debug
@require_http_methods(["POST"])
@csrf_exempt
def api_eliminar_segmento(request, transcripcion_id):
    """
    API para eliminar un segmento de la conversación
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        # Debug: Imprimir datos recibidos
        logger.info(f"Datos recibidos para eliminar: {dict(request.POST)}")
        
        segmento_id = int(request.POST.get('segmento_id', -1))
        
        # Validaciones más específicas
        if segmento_id < 0:
            return JsonResponse({
                'success': False,
                'error': 'ID de segmento no válido'
            })
        
        # Validar que el segmento existe - CORREGIDO para estructura dict
        estructura = transcripcion.conversacion_json or {}
        conversacion = estructura.get('conversacion', []) if isinstance(estructura, dict) else []
        
        if segmento_id >= len(conversacion):
            return JsonResponse({
                'success': False,
                'error': f'Segmento {segmento_id} no encontrado. Total segmentos: {len(conversacion)}'
            })
        
        # Eliminar segmento
        conversacion.pop(segmento_id)
        
        # Guardar estructura completa actualizada
        estructura['conversacion'] = conversacion
        transcripcion.conversacion_json = estructura
        transcripcion.numero_segmentos = len(conversacion)
        transcripcion.fecha_ultima_edicion = timezone.now()
        if request.user.is_authenticated:
            transcripcion.usuario_ultima_edicion = request.user
        transcripcion.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Segmento eliminado correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error en api_eliminar_segmento: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_agregar_segmento(request, transcripcion_id):
    """
    API para agregar un nuevo segmento a la conversación
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        import json
        mensaje_data = json.loads(request.POST.get('mensaje', '{}'))
        
        # Crear nuevo segmento
        nuevo_segmento = {
            'hablante': mensaje_data.get('hablante', 'Nuevo Hablante'),
            'texto': mensaje_data.get('texto', ''),
            'inicio': float(mensaje_data.get('inicio', 0)),
            'fin': float(mensaje_data.get('fin', 0)),
            'color': mensaje_data.get('color', '#28a745'),
            'agregado_manualmente': True,
            'agregado_por': request.user.username,
            'fecha_adicion': timezone.now().isoformat()
        }
        
        # Agregar a la conversación
        conversacion = transcripcion.conversacion_json or []
        conversacion.append(nuevo_segmento)
        
        # Ordenar por tiempo de inicio
        conversacion.sort(key=lambda x: x.get('inicio', 0))
        
        transcripcion.conversacion_json = conversacion
        transcripcion.numero_segmentos = len(conversacion)
        transcripcion.fecha_ultima_edicion = timezone.now()
        transcripcion.usuario_ultima_edicion = request.user
        transcripcion.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Segmento agregado correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error en api_agregar_segmento: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_renombrar_hablantes(request, transcripcion_id):
    """
    API para renombrar hablantes en la conversación
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        import json
        cambios = json.loads(request.POST.get('cambios', '{}'))
        
        # Aplicar cambios a la conversación
        conversacion = transcripcion.conversacion_json or []
        for segmento in conversacion:
            hablante_actual = segmento.get('hablante', '')
            if hablante_actual in cambios:
                segmento['hablante'] = cambios[hablante_actual]
                segmento['hablante_editado'] = True
                segmento['editado_por'] = request.user.username
        
        # Actualizar mapeo de hablantes identificados
        hablantes_identificados = transcripcion.hablantes_identificados or {}
        for nombre_anterior, nombre_nuevo in cambios.items():
            if nombre_anterior in hablantes_identificados:
                hablantes_identificados[nombre_nuevo] = hablantes_identificados.pop(nombre_anterior)
            else:
                hablantes_identificados[nombre_nuevo] = {
                    'nombre_real': nombre_nuevo,
                    'color': f'hsl({hash(nombre_nuevo) % 360}, 70%, 50%)',
                    'editado_por': request.user.username
                }
        
        transcripcion.conversacion_json = conversacion
        transcripcion.hablantes_identificados = hablantes_identificados
        transcripcion.fecha_ultima_edicion = timezone.now()
        transcripcion.usuario_ultima_edicion = request.user
        transcripcion.save()
        
        return JsonResponse({
            'success': True,
            'mensaje': 'Hablantes renombrados correctamente'
        })
        
    except Exception as e:
        logger.error(f"Error en api_renombrar_hablantes: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# @login_required  # Comentado temporalmente para debug
@require_http_methods(["POST"])
@csrf_exempt
def api_regenerar_transcripcion(request, transcripcion_id):
    """
    Elimina la transcripción y todos sus datos, deja el audio listo para transcribir nuevamente.
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        procesamiento = transcripcion.procesamiento_audio

        # Eliminar historial y ediciones asociadas
        try:
            if hasattr(transcripcion, 'historial_ediciones'):
                transcripcion.historial_ediciones.all().delete()
        except Exception as e:
            logger.warning(f"No se pudo eliminar historial de ediciones: {e}")

        # Eliminar la transcripción
        transcripcion.delete()

        # Dejar el audio listo para transcribir
        try:
            procesamiento.estado = 'completado'
            procesamiento.progreso = 100
            procesamiento.mensaje_estado = ''
            procesamiento.save(update_fields=['estado', 'progreso', 'mensaje_estado', 'updated_at'])
        except Exception as e:
            logger.warning(f"No se pudo actualizar estado del audio tras regenerar: {e}")

        # Redirigir al dashboard de audios por transcribir
        return JsonResponse({
            'success': True,
            'mensaje': 'Transcripción eliminada. El audio está listo para ser transcrito nuevamente.',
            'redirect_url': '/transcripcion/audios/'
        })
    except Exception as e:
        logger.error(f"Error en api_regenerar_transcripcion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        
    except Exception as e:
        logger.error(f"Error en api_regenerar_transcripcion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# @login_required  # Comentado temporalmente para debug
@require_http_methods(["POST"])
@csrf_exempt
def api_agregar_hablante_nuevo(request, transcripcion_id):
    """
    API para agregar un nuevo hablante al mapeo de hablantes
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        # Debug: Imprimir datos recibidos
        logger.info(f"Datos recibidos para agregar hablante: {dict(request.POST)}")
        
        nombre = request.POST.get('nombre', '').strip()
        cargo = request.POST.get('cargo', '').strip()
        
        # Validaciones
        if not nombre:
            return JsonResponse({
                'success': False,
                'error': 'El nombre del hablante es obligatorio'
            })
        
        # Obtener estructura actual
        estructura = transcripcion.conversacion_json or {}
        if not isinstance(estructura, dict):
            estructura = {'cabecera': {}, 'conversacion': [], 'metadata': {}}
        
        # Obtener mapeo de hablantes actual
        cabecera = estructura.get('cabecera', {})
        mapeo_hablantes = cabecera.get('mapeo_hablantes', {})
        
        # Verificar si ya existe
        existe = any(
            h.get('nombre', '').lower() == nombre.lower() 
            for h in mapeo_hablantes.values()
            if isinstance(h, dict)
        )
        
        if existe:
            return JsonResponse({
                'success': False,
                'error': f'Ya existe un hablante con el nombre "{nombre}"'
            })
        
        # Generar nuevo ID
        ids_existentes = [int(k) for k in mapeo_hablantes.keys() if str(k).isdigit()]
        nuevo_id = str(max(ids_existentes) + 1 if ids_existentes else 1)
        
        # Agregar nuevo hablante
        nuevo_hablante = {
            'nombre': nombre,
            'cargo': cargo,
            'color': f'hsl({hash(nombre) % 360}, 70%, 50%)',
            'agregado_manualmente': True,
            'agregado_por': request.user.username if request.user.is_authenticated else 'anonimo',
            'fecha_agregado': timezone.now().isoformat()
        }
        
        mapeo_hablantes[nuevo_id] = nuevo_hablante
        
        # Actualizar estructura
        cabecera['mapeo_hablantes'] = mapeo_hablantes
        estructura['cabecera'] = cabecera
        
        # Guardar
        transcripcion.conversacion_json = estructura
        transcripcion.fecha_ultima_edicion = timezone.now()
        if request.user.is_authenticated:
            transcripcion.usuario_ultima_edicion = request.user
        transcripcion.save()
        
        # Crear historial (solo si hay usuario)
        try:
            if request.user.is_authenticated:
                version = transcripcion.historial_ediciones.count() + 1
                HistorialEdicion.objects.create(
                    transcripcion=transcripcion,
                    usuario=request.user,
                    version=version,
                    tipo_edicion='hablante',
                    segmento_id='',
                    valor_anterior={},
                    valor_nuevo={'hablante_agregado': nuevo_hablante},
                    comentario=f'Agregado hablante: {nombre}'
                )
            else:
                logger.warning('Historial no creado: usuario anónimo al agregar hablante')
        except Exception as e_hist:
            logger.warning(f"No se pudo registrar historial de hablante: {e_hist}")
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Hablante "{nombre}" agregado correctamente',
            'nuevo_hablante': {
                'id': nuevo_id,
                'nombre': nombre,
                'cargo': cargo
            }
        })
        
    except Exception as e:
        logger.error(f"Error en api_agregar_hablante_nuevo: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# @login_required  # Comentado temporalmente para debug
@require_http_methods(["POST"])
@csrf_exempt
def api_insertar_segmento_posicion(request, transcripcion_id):
    """
    API para insertar un nuevo segmento en una posición específica
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        # Debug: Imprimir datos recibidos
        logger.info(f"Datos recibidos para insertar segmento: {dict(request.POST)}")
        
        posicion = int(request.POST.get('posicion', 0))
        inicio = float(request.POST.get('inicio', 0))
        fin = float(request.POST.get('fin', 0))
        texto = request.POST.get('texto', '').strip()
        hablante_id = request.POST.get('hablante_id', '').strip()
        
        # Validaciones
        if inicio >= fin:
            return JsonResponse({
                'success': False,
                'error': 'El tiempo de inicio debe ser menor que el tiempo de fin'
            })
        
        if not texto:
            return JsonResponse({
                'success': False,
                'error': 'El texto del segmento es obligatorio'
            })
        
        if not hablante_id:
            return JsonResponse({
                'success': False,
                'error': 'Debe seleccionar un hablante'
            })
        
        # Obtener estructura actual
        estructura = transcripcion.conversacion_json or {}
        if not isinstance(estructura, dict):
            estructura = {'cabecera': {}, 'conversacion': [], 'metadata': {}}
        
        conversacion = estructura.get('conversacion', [])
        
        # Validar posición
        if posicion < 0 or posicion > len(conversacion):
            return JsonResponse({
                'success': False,
                'error': f'Posición inválida. Debe estar entre 0 y {len(conversacion)}'
            })
        
        # Verificar hablante: aceptar tanto ID como nombre
        mapeo_hablantes = estructura.get('cabecera', {}).get('mapeo_hablantes', {})
        # Normalizar llaves a string para comparación robusta
        mapeo_hablantes_str = {str(k): v for k, v in mapeo_hablantes.items()}
        hablante_nombre = None
        if hablante_id in mapeo_hablantes_str:
            # Caso 1: key es el ID
            info = mapeo_hablantes_str[hablante_id]
            if isinstance(info, dict):
                hablante_nombre = info.get('nombre') or info.get('nombre_real') or f'Hablante {hablante_id}'
            else:
                # A veces el mapeo puede ser string directo
                hablante_nombre = str(info)
        else:
            # Caso 2: el valor recibido es el nombre; buscar su ID
            for k, v in mapeo_hablantes_str.items():
                if (isinstance(v, dict) and v.get('nombre') == hablante_id) or (not isinstance(v, dict) and str(v) == hablante_id):
                    hablante_nombre = v.get('nombre') if isinstance(v, dict) else str(v)
                    hablante_id = str(k)
                    break
        
        if not hablante_nombre:
            return JsonResponse({'success': False, 'error': 'Hablante no encontrado en el mapeo actual'}, status=400)
        
        # Crear nuevo segmento
        nuevo_segmento = {
            'hablante': hablante_nombre,
            'hablante_id': hablante_id,
            'texto': texto,
            'inicio': inicio,
            'fin': fin,
            'confianza': 0.95,  # Asignar alta confianza a segmentos manuales
            'agregado_manualmente': True,
            'agregado_por': request.user.username if request.user.is_authenticated else 'anonimo',
            'fecha_agregado': timezone.now().isoformat()
        }
        
        # Insertar en la posición especificada
        conversacion.insert(posicion, nuevo_segmento)
        
        # Actualizar estructura
        estructura['conversacion'] = conversacion
        transcripcion.conversacion_json = estructura
        transcripcion.numero_segmentos = len(conversacion)
        transcripcion.fecha_ultima_edicion = timezone.now()
        if request.user.is_authenticated:
            transcripcion.usuario_ultima_edicion = request.user
        transcripcion.save()
        
        # Crear historial (solo si hay usuario)
        try:
            if request.user.is_authenticated:
                version = transcripcion.historial_ediciones.count() + 1
                HistorialEdicion.objects.create(
                    transcripcion=transcripcion,
                    usuario=request.user,
                    version=version,
                    tipo_edicion='adicion',
                    segmento_id=str(posicion),
                    valor_anterior={},
                    valor_nuevo={'segmento_insertado': nuevo_segmento, 'posicion': posicion},
                    comentario=f'Insertado segmento en posición {posicion}: "{texto[:50]}..."'
                )
            else:
                logger.warning('Historial no creado: usuario anónimo al insertar segmento')
        except Exception as e_hist:
            logger.warning(f"No se pudo registrar historial de inserción de segmento: {e_hist}")
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Segmento insertado correctamente en posición {posicion}',
            'nuevo_segmento': nuevo_segmento,
            'total_segmentos': len(conversacion)
        })
        
    except Exception as e:
        logger.error(f"Error en api_insertar_segmento_posicion: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)