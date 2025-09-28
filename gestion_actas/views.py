from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q, Count, Prefetch
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import json
import logging

from .models import (
    GestionActa, EstadoGestionActa, ProcesoRevision, 
    RevisionIndividual, HistorialCambios, ConfiguracionExportacion
)
# from generador_actas.models import ActaGenerada  # Comentado temporalmente


User = get_user_model()
logger = logging.getLogger(__name__)


def enviar_notificacion_revision(proceso_revision):
    """
    Envía notificaciones por correo electrónico a los revisores asignados
    """
    try:
        acta = proceso_revision.gestion_acta
        revisores = [revision.revisor for revision in proceso_revision.revisiones.all()]
        
        # Preparar el contexto para el template del email
        contexto = {
            'acta_titulo': acta.titulo if hasattr(acta, 'titulo') else f'Acta #{acta.id}',
            'acta_numero': f'#{acta.id}',
            'solicitante': proceso_revision.iniciado_por.get_full_name() or proceso_revision.iniciado_por.username,
            'fecha_limite': proceso_revision.fecha_limite,
            'requiere_unanimidad': proceso_revision.requiere_unanimidad,
            'observaciones': proceso_revision.observaciones,
            'url_revision': f'{settings.SITE_URL}/gestion-actas/acta/{acta.id}/' if hasattr(settings, 'SITE_URL') else f'http://localhost:8000/gestion-actas/acta/{acta.id}/',
            'fecha_envio': timezone.now().strftime('%d/%m/%Y %H:%M')
        }
        
        # Template del email
        asunto = f'[Actas Municipales] Nueva revisión asignada - {contexto["acta_titulo"]}'
        
        mensaje_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(45deg, #007bff, #0056b3); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                    <h2 style="margin: 0;">🔔 Nueva Revisión de Acta</h2>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-radius: 0 0 8px 8px;">
                    <p>Estimado/a revisor/a,</p>
                    
                    <p>Se le ha asignado una nueva acta para revisión en el Sistema de Actas Municipales.</p>
                    
                    <div style="background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #007bff; border-radius: 4px;">
                        <h3 style="margin-top: 0; color: #007bff;">📋 Detalles del Acta</h3>
                        <p><strong>Título:</strong> {contexto["acta_titulo"]}</p>
                        <p><strong>Número:</strong> {contexto["acta_numero"]}</p>
                        <p><strong>Solicitado por:</strong> {contexto["solicitante"]}</p>
                        <p><strong>Enviado el:</strong> {contexto["fecha_envio"]}</p>
                        {'<p><strong>Fecha límite:</strong> ' + proceso_revision.fecha_limite.strftime('%d/%m/%Y %H:%M') + '</p>' if proceso_revision.fecha_limite else ''}
                        <p><strong>Tipo de aprobación:</strong> {'Unanimidad (todos deben aprobar)' if proceso_revision.requiere_unanimidad else 'Mayoría'}</p>
                    </div>
                    
                    {f'<div style="background: #fff3cd; padding: 10px; margin: 15px 0; border-radius: 4px; border-left: 4px solid #ffc107;"><p><strong>📝 Instrucciones:</strong><br>{proceso_revision.observaciones}</p></div>' if proceso_revision.observaciones else ''}
                    
                    <div style="text-align: center; margin: 25px 0;">
                        <a href="{contexto["url_revision"]}" 
                           style="background: #28a745; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                            🔍 Revisar Acta Ahora
                        </a>
                    </div>
                    
                    <div style="background: #e9ecef; padding: 10px; margin: 15px 0; border-radius: 4px; font-size: 0.9em;">
                        <p><strong>Acciones disponibles:</strong></p>
                        <ul>
                            <li>✅ <strong>Aprobar:</strong> Si el contenido es correcto</li>
                            <li>❌ <strong>Rechazar:</strong> Si requiere modificaciones (debe incluir comentarios)</li>
                        </ul>
                    </div>
                    
                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 20px 0;">
                    
                    <p style="font-size: 0.9em; color: #6c757d;">
                        Este es un mensaje automático del Sistema de Actas Municipales.<br>
                        Si tiene problemas para acceder al sistema, contacte al administrador.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Versión de texto plano
        mensaje_texto = f"""
Nueva Revisión de Acta Asignada

Estimado/a revisor/a,

Se le ha asignado una nueva acta para revisión en el Sistema de Actas Municipales.

DETALLES DEL ACTA:
- Título: {contexto["acta_titulo"]}
- Número: {contexto["acta_numero"]}
- Solicitado por: {contexto["solicitante"]}
- Enviado el: {contexto["fecha_envio"]}
{f'- Fecha límite: {proceso_revision.fecha_limite.strftime("%d/%m/%Y %H:%M")}' if proceso_revision.fecha_limite else ''}
- Tipo de aprobación: {'Unanimidad (todos deben aprobar)' if proceso_revision.requiere_unanimidad else 'Mayoría'}

{f'INSTRUCCIONES: {proceso_revision.observaciones}' if proceso_revision.observaciones else ''}

Para revisar el acta, ingrese al siguiente enlace:
{contexto["url_revision"]}

ACCIONES DISPONIBLES:
- Aprobar: Si el contenido es correcto
- Rechazar: Si requiere modificaciones (debe incluir comentarios)

---
Este es un mensaje automático del Sistema de Actas Municipales.
        """
        
        # Enviar email a cada revisor
        emails_enviados = 0
        emails_fallidos = []
        
        for revisor in revisores:
            if revisor.email:
                try:
                    send_mail(
                        subject=asunto,
                        message=mensaje_texto,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[revisor.email],
                        html_message=mensaje_html,
                        fail_silently=False
                    )
                    emails_enviados += 1
                    logger.info(f'Email de revisión enviado exitosamente a {revisor.email}')
                except Exception as e:
                    emails_fallidos.append({
                        'revisor': revisor.get_full_name() or revisor.username,
                        'email': revisor.email,
                        'error': str(e)
                    })
                    logger.error(f'Error enviando email a {revisor.email}: {str(e)}')
            else:
                emails_fallidos.append({
                    'revisor': revisor.get_full_name() or revisor.username,
                    'email': 'Sin email configurado',
                    'error': 'Usuario sin email'
                })
        
        return {
            'exitoso': True,
            'emails_enviados': emails_enviados,
            'emails_fallidos': emails_fallidos,
            'total_revisores': len(revisores)
        }
        
    except Exception as e:
        logger.error(f'Error general enviando notificaciones de revisión: {str(e)}')
        return {
            'exitoso': False,
            'error': str(e),
            'emails_enviados': 0,
            'emails_fallidos': [],
            'total_revisores': 0
        }


@login_required
def listado_actas(request):
    """Vista principal del listado de actas con TODA la información rica del proyecto"""
    
    # Obtener filtros desde GET
    filtro_estado = request.GET.get('estado', '')
    filtro_busqueda = request.GET.get('q', '')
    filtro_fecha_desde = request.GET.get('fecha_desde', '')
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '')
    filtro_tipo_reunion = request.GET.get('tipo_reunion', '')
    
    # Query base con TODA la información rica optimizada
    actas = GestionActa.objects.select_related(
        'estado',
        'usuario_editor',
        'proceso_revision',
        # Información rica del acta generada
        'acta_generada',
        'acta_generada__transcripcion', 
        'acta_generada__transcripcion__procesamiento_audio',
        'acta_generada__transcripcion__procesamiento_audio__tipo_reunion',
        'acta_generada__plantilla',
        'acta_generada__proveedor_ia',
        'acta_generada__usuario_creacion'
    ).prefetch_related(
        Prefetch('proceso_revision__revisiones', 
                 queryset=RevisionIndividual.objects.select_related('revisor'))
    )
    
    # Aplicar filtros
    if filtro_estado:
        actas = actas.filter(estado__codigo=filtro_estado)
    
    if filtro_tipo_reunion:
        actas = actas.filter(
            acta_generada__transcripcion__procesamiento_audio__tipo_reunion__codigo=filtro_tipo_reunion
        )
    
    if filtro_busqueda:
        actas = actas.filter(
            Q(contenido_editado__icontains=filtro_busqueda) |
            Q(observaciones__icontains=filtro_busqueda) |
            # Buscar también en información del acta generada
            Q(acta_generada__titulo__icontains=filtro_busqueda) |
            Q(acta_generada__numero_acta__icontains=filtro_busqueda) |
            Q(acta_generada__transcripcion__procesamiento_audio__participantes__icontains=filtro_busqueda) |
            Q(acta_generada__transcripcion__procesamiento_audio__ubicacion__icontains=filtro_busqueda)
        )
    
    if filtro_fecha_desde:
        actas = actas.filter(fecha_creacion__date__gte=filtro_fecha_desde)
        
    if filtro_fecha_hasta:
        actas = actas.filter(fecha_creacion__date__lte=filtro_fecha_hasta)
    
    # Ordenamiento por defecto
    actas = actas.order_by('-fecha_creacion')
    
    # Paginación
    paginator = Paginator(actas, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estados para el filtro
    estados = EstadoGestionActa.objects.filter(activo=True).order_by('orden')
    
    # Tipos de reunión para el filtro (desde audio_processing)
    from apps.audio_processing.models import TipoReunion
    tipos_reunion = TipoReunion.objects.all().order_by('nombre')
    
    # Estadísticas básicas
    stats = {
        'total': actas.count(),
        'en_edicion': actas.filter(estado__codigo__in=['generada', 'en_edicion']).count(),
        'en_revision': actas.filter(estado__codigo__in=['enviada_revision', 'en_revision']).count(),
        'aprobadas': actas.filter(estado__codigo='aprobada').count(),
        'publicadas': actas.filter(estado__codigo='publicada').count(),
    }
    
    context = {
        'page_obj': page_obj,
        'estados': estados,
        'tipos_reunion': tipos_reunion,
        'filtros': {
            'estado': filtro_estado,
            'busqueda': filtro_busqueda,
            'fecha_desde': filtro_fecha_desde,
            'fecha_hasta': filtro_fecha_hasta,
            'tipo_reunion': filtro_tipo_reunion,
        },
        'stats': stats,
        'page_title': 'Gestión de Actas Municipales',
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/'},
            {'title': 'Gestión de Actas', 'active': True}
        ]
    }
    
    return render(request, 'gestion_actas/listado.html', context)


@login_required
def editor_acta(request, acta_id):
    """Vista del editor de actas con texto enriquecido"""
    
    acta = get_object_or_404(GestionActa, id=acta_id)
    
    # Verificar permisos de edición basado en el estado
    if not acta.estado.permite_edicion:
        messages.error(request, f'Esta acta no puede ser editada porque está en estado "{acta.estado.nombre}". '
                                f'Solo se pueden editar actas en estados que lo permitan.')
        return redirect('gestion_actas:ver', acta_id=acta.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Guardar contenido anterior para el historial
                contenido_anterior = acta.contenido_editado
                titulo_anterior = acta.titulo if hasattr(acta, 'titulo') else ''
                
                # Actualizar contenido
                acta.contenido_editado = request.POST.get('contenido_html', acta.contenido_editado)
                acta.observaciones = request.POST.get('observaciones', '')
                acta.usuario_editor = request.user
                
                # Actualizar título en acta_generada si existe
                nuevo_titulo = request.POST.get('titulo', '').strip()
                if nuevo_titulo and acta.acta_generada:
                    acta.acta_generada.titulo = nuevo_titulo
                    acta.acta_generada.save()
                
                # Actualizar estado si es necesario
                if acta.estado.codigo == 'generada':
                    estado_edicion = EstadoGestionActa.objects.get(codigo='en_edicion')
                    acta.estado = estado_edicion
                
                acta.save()
                
                # Crear entrada en historial si hubo cambios significativos
                cambios_realizados = []
                
                if contenido_anterior != acta.contenido_editado:
                    cambios_realizados.append('contenido')
                
                if titulo_anterior != nuevo_titulo and acta.acta_generada:
                    cambios_realizados.append('titulo')
                
                if cambios_realizados:
                    descripcion_cambios = f"Edición de {' y '.join(cambios_realizados)} por {request.user.get_full_name() or request.user.username}"
                    
                    HistorialCambios.objects.create(
                        gestion_acta=acta,
                        usuario=request.user,
                        tipo_cambio='edicion_contenido',
                        descripcion=descripcion_cambios,
                        datos_adicionales={
                            'cambios_realizados': cambios_realizados,
                            'titulo_anterior': titulo_anterior,
                            'titulo_nuevo': nuevo_titulo,
                            'contenido_modificado': 'contenido' in cambios_realizados,
                            'longitud_anterior': len(contenido_anterior),
                            'longitud_nueva': len(acta.contenido_editado),
                            'timestamp': timezone.now().isoformat()
                        },
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                    )
                
                messages.success(request, '¡Acta guardada exitosamente!')
                
                # Si se solicita enviar a revisión
                if 'enviar_revision' in request.POST:
                    return redirect('gestion_actas:configurar_revision', acta_id=acta.id)
                
                return redirect('gestion_actas:editor', acta_id=acta.id)
                
        except Exception as e:
            messages.error(request, f'Error al guardar: {e}')
    
    # Obtener historial reciente
    historial = acta.historial_cambios.select_related('usuario').order_by('-fecha_cambio')[:10]
    
    context = {
        'acta': acta,
        'historial': historial,
        # 'puede_enviar_revision': acta.puede_enviar_a_revision(),  # Simplificado por ahora
        'puede_enviar_revision': True,
        'page_title': f'Editando: Acta #{acta.id}',
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/'},
            {'title': 'Gestión de Actas', 'url': reverse('gestion_actas:listado')},
            {'title': f'Acta #{acta.id}', 'active': True}
        ]
    }
    
    return render(request, 'gestion_actas/editor.html', context)


@login_required
def configurar_revision(request, acta_id):
    """Vista para configurar el proceso de revisión"""
    
    acta = get_object_or_404(GestionActa, id=acta_id)
    
    # Verificar si puede enviar a revisión
    if acta.estado.codigo in ['aprobada', 'publicada', 'archivada']:
        messages.error(request, 'Esta acta no puede ser enviada a revisión debido a su estado actual.')
        return redirect('gestion_actas:listado')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Obtener datos del formulario
                usuarios_ids = request.POST.getlist('revisores')
                tipo_aprobacion = request.POST.get('tipo_aprobacion', 'unanimidad')
                fecha_limite = request.POST.get('fecha_limite')
                instrucciones = request.POST.get('instrucciones', '')
                
                if not usuarios_ids:
                    messages.error(request, 'Debe seleccionar al menos un revisor.')
                    return redirect(request.path)
                
                # Verificar si ya existe un proceso activo
                if hasattr(acta, 'proceso_revision') and acta.proceso_revision:
                    messages.error(request, 'Esta acta ya tiene un proceso de revisión activo.')
                    return redirect('gestion_actas:listado')
                
                # Crear proceso de revisión
                proceso = ProcesoRevision.objects.create(
                    gestion_acta=acta,
                    iniciado_por=request.user,
                    revision_paralela=True,  # Siempre paralelo por ahora
                    requiere_unanimidad=(tipo_aprobacion == 'unanimidad'),
                    fecha_limite=fecha_limite if fecha_limite else None,
                    observaciones=instrucciones
                )
                
                # Crear revisiones individuales
                for usuario_id in usuarios_ids:
                    usuario = User.objects.get(id=usuario_id)
                    RevisionIndividual.objects.create(
                        proceso_revision=proceso,
                        revisor=usuario,
                        revisado=False
                    )
                
                # Actualizar estado del acta
                try:
                    estado_enviada = EstadoGestionActa.objects.get(codigo='en_revision')
                except EstadoGestionActa.DoesNotExist:
                    # Crear estado si no existe
                    estado_enviada = EstadoGestionActa.objects.create(
                        codigo='en_revision',
                        nombre='En Revisión',
                        descripcion='Acta enviada a proceso de revisión',
                        color='#ffc107',
                        es_final=False,
                        permite_edicion=False
                    )
                
                acta.estado = estado_enviada
                acta.save()
                
                # Registrar en historial
                HistorialCambios.objects.create(
                    gestion_acta=acta,
                    usuario=request.user,
                    tipo_cambio='envio_revision',
                    descripcion=f'Enviada a revisión con {len(usuarios_ids)} revisores ({tipo_aprobacion})',
                    datos_adicionales={
                        'revisores': [{'id': u.id, 'nombre': u.get_full_name() or u.username} 
                                    for u in User.objects.filter(id__in=usuarios_ids)],
                        'tipo_aprobacion': tipo_aprobacion,
                        'fecha_limite': fecha_limite,
                        'instrucciones': instrucciones
                    }
                )
                
                # Enviar notificaciones por email a los revisores
                resultado_email = enviar_notificacion_revision(proceso)
                
                # Mensaje de éxito con información del envío de emails
                mensaje_base = f'¡Acta enviada a revisión exitosamente!'
                if resultado_email['exitoso'] and resultado_email['emails_enviados'] > 0:
                    mensaje_base += f' Se enviaron {resultado_email["emails_enviados"]} notificaciones por correo.'
                    if resultado_email['emails_fallidos']:
                        mensaje_base += f' ({len(resultado_email["emails_fallidos"])} fallaron - revisar logs)'
                elif resultado_email['emails_fallidos']:
                    mensaje_base += f' ADVERTENCIA: No se pudieron enviar {len(resultado_email["emails_fallidos"])} correos.'
                else:
                    mensaje_base += f' Se asignaron {len(usuarios_ids)} revisores.'
                
                messages.success(request, mensaje_base)
                return redirect('gestion_actas:listado')
                
        except Exception as e:
            messages.error(request, f'Error al enviar a revisión: {str(e)}')
            print(f"Error configurar_revision: {e}")  # Para debugging
    
    # Obtener TODOS los usuarios disponibles para revisión (incluir a todos)
    usuarios_revisores = User.objects.filter(
        is_active=True
    ).order_by('first_name', 'last_name', 'username')
    
    # Opcional: Comentar la siguiente línea si quieres que el usuario actual pueda auto-asignarse como revisor
    # usuarios_revisores = usuarios_revisores.exclude(id=request.user.id)
    
    # Priorizar usuarios con grupos de revisión, pero incluir a TODOS los demás también
    grupos_revisores = ['Revisor Actas', 'Admin Actas', 'Secretario', 'Alcalde', 'Administradores Municipales', 'Concejales', 'Secretarios de Concejo', 'Operadores Técnicos', 'Ciudadanos']
    
    # Separar usuarios por grupos para mejor organización
    usuarios_con_grupos = usuarios_revisores.filter(groups__name__in=grupos_revisores).distinct()
    usuarios_sin_grupos = usuarios_revisores.exclude(groups__name__in=grupos_revisores)
    
    # Combinar: primero los que tienen grupos, luego superusuarios/staff, luego el resto
    usuarios_finales = list(usuarios_con_grupos) + list(usuarios_sin_grupos.filter(is_superuser=True)) + list(usuarios_sin_grupos.filter(is_staff=True)) + list(usuarios_sin_grupos.exclude(is_superuser=True, is_staff=True))
    
    # Eliminar duplicados manteniendo orden
    usuarios_revisores_unicos = []
    ids_vistos = set()
    for usuario in usuarios_finales:
        if usuario.id not in ids_vistos:
            usuarios_revisores_unicos.append(usuario)
            ids_vistos.add(usuario.id)
    
    context = {
        'acta': acta,
        'usuarios_revisores': usuarios_revisores_unicos,
        'page_title': f'Configurar Revisión: {acta.titulo}',
    }
    
    return render(request, 'gestion_actas/configurar_revision.html', context)


@login_required
def activar_edicion(request, acta_id):
    """Vista para reactivar edición en casos de emergencia (solo superusuarios)"""
    
    # Verificar permisos (solo superusuarios pueden activar edición)
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('gestion_actas:listado')
    
    acta = get_object_or_404(GestionActa, id=acta_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. CANCELAR PROCESO DE REVISIÓN ACTIVO (si existe)
                proceso_revision = getattr(acta, 'proceso_revision', None)
                if proceso_revision and not proceso_revision.completado:
                    # Marcar proceso como cancelado
                    proceso_revision.completado = True
                    proceso_revision.aprobado = False
                    proceso_revision.fecha_completado = timezone.now()
                    proceso_revision.save()
                    
                    # Registrar cancelación de revisiones individuales
                    from .models import RevisionIndividual
                    revisiones = RevisionIndividual.objects.filter(
                        proceso_revision=proceso_revision, 
                        revisado=False
                    )
                    revisiones_canceladas = revisiones.count()
                    revisiones.update(
                        revisado=True,
                        aprobado=False,
                        fecha_revision=timezone.now(),
                        comentarios='Proceso cancelado por reactivación de emergencia'
                    )
                
                # 2. CAMBIAR ESTADO A "EN_EDICION" 
                try:
                    estado_edicion = EstadoGestionActa.objects.get(codigo='en_edicion')
                except EstadoGestionActa.DoesNotExist:
                    messages.error(request, 'Estado "en_edicion" no encontrado en el sistema.')
                    return redirect('gestion_actas:ver', acta_id=acta.id)
                
                estado_anterior = acta.estado
                acta.estado = estado_edicion
                acta.save()
                
                # 3. REGISTRAR EN HISTORIAL la reactivación completa
                descripcion_cambio = f'Edición reactivada forzadamente por {request.user.get_full_name() or request.user.username}'
                if proceso_revision:
                    descripcion_cambio += f' - Proceso de revisión ID {proceso_revision.id} cancelado'
                    if 'revisiones_canceladas' in locals():
                        descripcion_cambio += f' ({revisiones_canceladas} revisiones pendientes canceladas)'
                
                HistorialCambios.objects.create(
                    gestion_acta=acta,
                    usuario=request.user,
                    tipo_cambio='reactivacion_edicion',
                    descripcion=descripcion_cambio,
                    datos_adicionales={
                        'estado_anterior': estado_anterior.nombre,
                        'estado_nuevo': estado_edicion.nombre,
                        'proceso_revision_cancelado': proceso_revision.id if proceso_revision else None,
                        'revisiones_canceladas': revisiones_canceladas if 'revisiones_canceladas' in locals() else 0,
                        'motivo': 'Reactivación de emergencia por superusuario',
                        'timestamp': timezone.now().isoformat(),
                        'ip_usuario': request.META.get('REMOTE_ADDR'),
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200]
                    }
                )
                
                # 4. MENSAJE DE ÉXITO
                mensaje_exito = f'¡Edición reactivada exitosamente! El acta cambió de "{estado_anterior.nombre}" a "{estado_edicion.nombre}"'
                if proceso_revision:
                    mensaje_exito += f' y se canceló el proceso de revisión activo.'
                else:
                    mensaje_exito += '.'
                    
                messages.success(request, mensaje_exito)
                return redirect('gestion_actas:editor', acta_id=acta.id)
                
        except Exception as e:
            messages.error(request, f'Error al reactivar edición: {str(e)}')
            return redirect('gestion_actas:ver', acta_id=acta.id)
    
    # GET: Mostrar confirmación
    context = {
        'acta': acta,
        'estado_actual': acta.estado,
        'page_title': f'Activar Edición - {acta.titulo if hasattr(acta, "titulo") else f"Acta #{acta.id}"}',
    }
    
    return render(request, 'gestion_actas/activar_edicion.html', context)


@login_required
def panel_revision(request, acta_id):
    """Vista del panel de revisión para revisores"""
    
    acta = get_object_or_404(GestionActa, id=acta_id)
    
    if not acta.proceso_revision:
        messages.error(request, 'Esta acta no tiene un proceso de revisión activo.')
        return redirect('gestion_actas:listado')
    
    # Verificar si el usuario es revisor
    revision_individual = acta.proceso_revision.revisiones.filter(usuario=request.user).first()
    
    if not revision_individual:
        messages.error(request, 'No tienes permisos para revisar esta acta.')
        return redirect('gestion_actas:listado')
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        comentarios = request.POST.get('comentarios', '')
        
        if accion in ['aprobado', 'rechazado']:
            try:
                with transaction.atomic():
                    # Actualizar revisión individual
                    revision_individual.estado = accion
                    revision_individual.comentarios = comentarios
                    revision_individual.fecha_revision = timezone.now()
                    revision_individual.save()
                    
                    # Verificar si el proceso está completo
                    acta.proceso_revision.verificar_completado()
                    
                    messages.success(request, f'¡Acta {accion} exitosamente!')
                    return redirect('gestion_actas:listado')
                    
            except Exception as e:
                messages.error(request, f'Error al procesar revisión: {e}')
    
    # Obtener otras revisiones (sin comentarios privados)
    otras_revisiones = acta.proceso_revision.revisiones.exclude(
        usuario=request.user
    ).select_related('usuario')
    
    context = {
        'acta': acta,
        'proceso': acta.proceso_revision,
        'mi_revision': revision_individual,
        'otras_revisiones': otras_revisiones,
        'puede_revisar': revision_individual.estado == 'pendiente',
        'page_title': f'Revisar: Acta #{acta.id}',
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/'},
            {'title': 'Gestión de Actas', 'url': reverse('gestion_actas:listado')},
            {'title': 'Revisión', 'active': True}
        ]
    }
    
    return render(request, 'gestion_actas/panel_revision.html', context)


@login_required
def ver_acta(request, acta_id):
    """Vista de solo lectura del acta con funcionalidad de revisión"""
    
    acta = get_object_or_404(GestionActa, id=acta_id)
    
    # Verificar si el usuario actual es un revisor de esta acta
    revision_individual = None
    if hasattr(acta, 'proceso_revision') and acta.proceso_revision:
        revision_individual = acta.proceso_revision.revisiones.filter(revisor=request.user).first()
    
    # Procesar formulario de revisión
    if request.method == 'POST' and revision_individual and not revision_individual.revisado:
        accion = request.POST.get('accion')
        comentarios = request.POST.get('comentarios', '').strip()
        
        if accion in ['aprobado', 'rechazado']:
            try:
                with transaction.atomic():
                    # Actualizar revisión individual
                    revision_individual.revisado = True
                    revision_individual.aprobado = (accion == 'aprobado')
                    revision_individual.comentarios = comentarios
                    revision_individual.fecha_revision = timezone.now()
                    revision_individual.save()
                    
                    # Registrar en historial
                    HistorialCambios.objects.create(
                        gestion_acta=acta,
                        usuario=request.user,
                        tipo_cambio='revision_completada',
                        descripcion=f'Revisión {accion} por {request.user.get_full_name() or request.user.username}',
                        datos_adicionales={
                            'accion': accion,
                            'comentarios': comentarios,
                            'fecha_revision': timezone.now().isoformat()
                        }
                    )
                    
                    # Verificar si el proceso de revisión está completo
                    proceso = acta.proceso_revision
                    proceso.verificar_completado()
                    
                    if accion == 'aprobado':
                        messages.success(request, '¡Acta aprobada exitosamente!')
                    else:
                        messages.warning(request, 'Acta rechazada. Se ha notificado al autor.')
                    
                    return redirect('gestion_actas:ver', acta_id=acta.id)
                    
            except Exception as e:
                messages.error(request, f'Error al procesar la revisión: {str(e)}')
    
    # Historial completo
    try:
        historial = acta.historial_cambios.select_related('usuario').order_by('-fecha_cambio')[:10]
    except AttributeError:
        historial = []
    
    context = {
        'acta': acta,
        'revision_individual': revision_individual,
        'historial': historial,
        'page_title': f'Acta: {acta.titulo}',
        'breadcrumbs': [
            {'title': 'Inicio', 'url': '/'},
            {'title': 'Gestión de Actas', 'url': reverse('gestion_actas:listado')},
            {'title': acta.titulo[:30] + '...' if len(acta.titulo) > 30 else acta.titulo, 'active': True}
        ]
    }
    
    return render(request, 'gestion_actas/ver_acta.html', context)


@login_required
@require_POST
def cambiar_estado_acta(request, acta_id):
    """Vista AJAX para cambiar estado de un acta"""
    
    try:
        acta = get_object_or_404(GestionActa, id=acta_id)
        nuevo_estado_codigo = request.POST.get('nuevo_estado')
        observaciones = request.POST.get('observaciones', '')
        
        # Verificar que el estado existe
        nuevo_estado = EstadoGestionActa.objects.get(codigo=nuevo_estado_codigo, activo=True)
        
        # Validar transición (básica)
        estado_anterior = acta.estado
        acta.estado = nuevo_estado
        acta.save()
        
        # Registrar cambio
        HistorialCambios.objects.create(
            gestion_acta=acta,
            usuario=request.user,
            tipo_cambio='cambio_estado',
            descripcion=f'Estado cambiado de "{estado_anterior.nombre}" a "{nuevo_estado.nombre}"',
            datos_adicionales={
                'estado_anterior': estado_anterior.codigo,
                'estado_nuevo': nuevo_estado.codigo,
                'observaciones': observaciones
            }
        )
        
        return JsonResponse({
            'success': True,
            'mensaje': f'Estado actualizado a "{nuevo_estado.nombre}"',
            'nuevo_estado': {
                'codigo': nuevo_estado.codigo,
                'nombre': nuevo_estado.nombre,
                'color': nuevo_estado.color
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def dashboard_revision(request):
    """Dashboard para revisores con sus tareas pendientes"""
    
    try:
        # Mis revisiones pendientes
        mis_revisiones = RevisionIndividual.objects.filter(
            revisor=request.user,
            revisado=False
        ).select_related(
            'proceso_revision__gestion_acta'
        )[:10]  # Limitar resultados
        
        # Revisiones completadas recientes
        mis_completadas = RevisionIndividual.objects.filter(
            revisor=request.user,
            revisado=True
        ).select_related(
            'proceso_revision__gestion_acta'
        ).order_by('-fecha_revision')[:5]  # Solo las 5 más recientes
        
        # Estadísticas básicas
        stats = {
            'pendientes': mis_revisiones.count(),
            'completadas_hoy': 0,  # Simplificado por ahora
            'total_revisiones': RevisionIndividual.objects.filter(revisor=request.user).count(),
            'aprobadas': RevisionIndividual.objects.filter(revisor=request.user, revisado=True, aprobado=True).count(),
            'rechazadas': RevisionIndividual.objects.filter(revisor=request.user, revisado=True, aprobado=False).count()
        }
        
    except Exception as e:
        # En caso de error, valores por defecto
        mis_revisiones = []
        mis_completadas = []
        stats = {
            'pendientes': 0,
            'completadas_hoy': 0,
            'total_revisiones': 0,
            'aprobadas': 0,
            'rechazadas': 0
        }
    
    context = {
        'mis_revisiones': mis_revisiones,
        'mis_completadas': mis_completadas,
        'stats': stats,
        'page_title': 'Dashboard de Revisiones',
    }
    
    return render(request, 'gestion_actas/dashboard_revision.html', context)


# Vista AJAX para autoguardado
@csrf_exempt
@login_required
@require_POST
def autoguardar_contenido(request, acta_id):
    """Autoguardado del contenido del acta cada cierto tiempo"""
    
    try:
        acta = get_object_or_404(GestionActa, id=acta_id)
        
        # Comentar verificación temporalmente para debug
        # if not acta.puede_editar():
        #     return JsonResponse({'success': False, 'error': 'Sin permisos de edición'})
        
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'Método no permitido'})
        
        data = json.loads(request.body)
        contenido = data.get('contenido_html', '')
        
        # CORREGIDO: usar contenido_editado (campo que SÍ existe)
        acta.contenido_editado = contenido
        acta.usuario_editor = request.user  # Campo correcto
        acta.fecha_ultima_edicion = timezone.now()
        acta.save()
        
        return JsonResponse({
            'success': True, 
            'timestamp': acta.fecha_ultima_edicion.strftime('%H:%M:%S'),
            'message': 'Autoguardado exitoso',
            'contenido_length': len(contenido)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})


@login_required
@require_POST
def publicar_acta(request, acta_id):
    """Vista para publicar un acta aprobada en el portal ciudadano"""
    
    try:
        acta = get_object_or_404(GestionActa, id=acta_id)
        
        # Verificar que el acta esté lista para publicación
        if acta.estado.codigo != 'lista_publicacion':
            messages.error(request, 'Esta acta no está lista para publicación.')
            return redirect('gestion_actas:listado')
        
        # Solo superusuarios pueden publicar por ahora
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para publicar actas.')
            return redirect('gestion_actas:listado')
        
        with transaction.atomic():
            # Cambiar estado a publicada
            estado_publicada = EstadoGestionActa.objects.get(codigo='publicada')
            acta.estado = estado_publicada
            acta.fecha_publicacion = timezone.now()
            acta.save()
            
            # Registrar en historial
            HistorialCambios.objects.create(
                gestion_acta=acta,
                usuario=request.user,
                tipo_cambio='publicacion',
                descripcion=f'Acta publicada en portal ciudadano por {request.user.get_full_name() or request.user.username}',
                datos_adicionales={
                    'fecha_publicacion': timezone.now().isoformat(),
                    'publicado_por': request.user.id
                }
            )
            
            # Sincronizar con el portal ciudadano
            acta_portal = _sincronizar_con_portal_ciudadano(acta, request.user)
            
            # Generar documentos en múltiples formatos
            documentos_generados = _generar_documentos_publicacion(acta, acta_portal)
            
            # Registrar actividad adicional
            if documentos_generados:
                HistorialCambios.objects.create(
                    gestion_acta=acta,
                    usuario=request.user,
                    tipo_cambio='documentos_generados',
                    descripcion=f'Documentos generados: {", ".join(documentos_generados.keys())}',
                    datos_adicionales=documentos_generados
                )
            
            # Enviar notificaciones por email
            try:
                from .email_notifications import enviar_notificacion_publicacion
                
                resultado_email = enviar_notificacion_publicacion(
                    acta_gestion=acta,
                    acta_portal=acta_portal,
                    usuario_publicador=request.user
                )
                
                if resultado_email:
                    HistorialCambios.objects.create(
                        gestion_acta=acta,
                        usuario=request.user,
                        tipo_cambio='notificacion_enviada',
                        descripcion='Notificaciones de publicación enviadas por email',
                        datos_adicionales={
                            'emails_enviados': True,
                            'fecha_envio': timezone.now().isoformat()
                        }
                    )
                    messages.success(
                        request, 
                        f'¡Acta "{acta.titulo}" publicada exitosamente en el Portal Ciudadano! '
                        f'Se han enviado notificaciones por email a los funcionarios municipales.'
                    )
                else:
                    messages.warning(
                        request,
                        f'Acta "{acta.titulo}" publicada exitosamente, pero hubo problemas enviando las notificaciones por email.'
                    )
                    
            except Exception as e:
                logger.error(f'Error enviando notificaciones por email: {str(e)}')
                messages.success(
                    request, 
                    f'¡Acta "{acta.titulo}" publicada exitosamente en el Portal Ciudadano! '
                    f'(Notificaciones por email no disponibles)'
                )
            
        return redirect('gestion_actas:listado')
        
    except EstadoGestionActa.DoesNotExist:
        messages.error(request, 'Error: Estado "publicada" no encontrado en el sistema.')
        return redirect('gestion_actas:listado')
    except Exception as e:
        logger.error(f'Error publicando acta {acta_id}: {str(e)}')
        messages.error(request, f'Error al publicar el acta: {str(e)}')
        return redirect('gestion_actas:listado')


# ============================================================================
# FUNCIONES AUXILIARES PARA PUBLICACIÓN EN PORTAL CIUDADANO
# ============================================================================

def _sincronizar_con_portal_ciudadano(gestion_acta, usuario):
    """Crear o actualizar ActaMunicipal en el portal ciudadano"""
    from apps.pages.models import ActaMunicipal, TipoSesion, EstadoActa
    import uuid
    
    try:
        # Obtener o crear tipo de sesión (default: ordinaria)
        tipo_sesion, _ = TipoSesion.objects.get_or_create(
            nombre='ordinaria',
            defaults={
                'descripcion': 'Sesión ordinaria municipal',
                'color': '#007bff',
                'icono': 'fas fa-file-alt'
            }
        )
        
        # Obtener o crear estado publicada
        estado_publicada, _ = EstadoActa.objects.get_or_create(
            nombre='publicada',
            defaults={
                'descripcion': 'Acta publicada en portal ciudadano',
                'color': '#28a745',
                'orden': 4
            }
        )
        
        # Verificar si ya existe un acta en el portal
        acta_portal = getattr(gestion_acta, 'acta_portal', None)
        
        if not acta_portal:
            # Crear nueva entrada en el portal ciudadano
            acta_portal = ActaMunicipal.objects.create(
                titulo=gestion_acta.titulo,
                numero_acta=gestion_acta.numero_acta or f"ACTA-{uuid.uuid4().hex[:8].upper()}",
                numero_sesion=f"SESION-{timezone.now().strftime('%Y%m%d')}",
                tipo_sesion=tipo_sesion,
                estado=estado_publicada,
                fecha_sesion=gestion_acta.fecha_creacion,
                fecha_publicacion=timezone.now(),
                resumen=(gestion_acta.observaciones or "Acta municipal generada automáticamente")[:500],  # Truncar a 500 caracteres
                contenido=gestion_acta.contenido_editado or "Sin contenido disponible",
                orden_del_dia="Orden del día según acta generada",
                acuerdos="Acuerdos tomados según el acta",
                acceso='publico',
                prioridad='normal',
                secretario=usuario,
                presidente="Alcalde Municipal",
                asistentes="Miembros del concejo municipal",
                transcripcion_ia=True,
                precision_ia=95.0,
                palabras_clave=f"acta municipal, sesión, {gestion_acta.titulo}",
                observaciones=f"Acta publicada desde sistema de gestión por {usuario.get_full_name() or usuario.username}",
                activo=True
            )
            
            # Vincular el acta del portal con la gestión
            gestion_acta.acta_portal = acta_portal
            gestion_acta.save()
        else:
            # Actualizar acta existente
            acta_portal.titulo = gestion_acta.titulo
            acta_portal.contenido = gestion_acta.contenido_editado or "Sin contenido disponible"
            acta_portal.resumen = (gestion_acta.observaciones or "Acta municipal actualizada")[:500]
            acta_portal.fecha_publicacion = timezone.now()
            acta_portal.estado = estado_publicada
            acta_portal.activo = True
            acta_portal.save()
        
        return acta_portal
        
    except Exception as e:
        logger.error(f'Error sincronizando con portal ciudadano: {str(e)}')
        return None


def _generar_documentos_publicacion(gestion_acta, acta_portal):
    """Generar documentos mejorados en múltiples formatos para descarga"""
    try:
        from .generador_documentos import generar_documentos_acta_mejorados
        from django.core.files import File
        from django.core.files.base import ContentFile
        import os
        
        # Usar el nuevo sistema de generación de documentos
        documentos_generados = generar_documentos_acta_mejorados(acta_portal)
        
        logger.info(f'Documentos generados para acta {acta_portal.numero_acta}: {list(documentos_generados.keys())}')
        
        # Guardar archivos en los campos del modelo ActaMunicipal
        archivos_guardados = {}
        
        # Guardar archivo PDF
        if 'pdf' in documentos_generados:
            pdf_info = documentos_generados['pdf']
            if os.path.exists(pdf_info['ruta']):
                with open(pdf_info['ruta'], 'rb') as pdf_file:
                    acta_portal.archivo_pdf.save(
                        pdf_info['nombre'],
                        ContentFile(pdf_file.read()),
                        save=False
                    )
                archivos_guardados['pdf'] = pdf_info['nombre']
                logger.info(f'PDF guardado en modelo: {pdf_info["nombre"]}')
        
        # Guardar archivo Word
        if 'word' in documentos_generados:
            word_info = documentos_generados['word']
            if os.path.exists(word_info['ruta']):
                with open(word_info['ruta'], 'rb') as word_file:
                    acta_portal.archivo_word.save(
                        word_info['nombre'],
                        ContentFile(word_file.read()),
                        save=False
                    )
                archivos_guardados['word'] = word_info['nombre']
                logger.info(f'Word guardado en modelo: {word_info["nombre"]}')
        
        # Guardar archivo TXT
        if 'txt' in documentos_generados:
            txt_info = documentos_generados['txt']
            if os.path.exists(txt_info['ruta']):
                with open(txt_info['ruta'], 'r', encoding='utf-8') as txt_file:
                    acta_portal.archivo_txt.save(
                        txt_info['nombre'],
                        ContentFile(txt_file.read().encode('utf-8')),
                        save=False
                    )
                archivos_guardados['txt'] = txt_info['nombre']
                logger.info(f'TXT guardado en modelo: {txt_info["nombre"]}')
        
        # Guardar el modelo una sola vez con todos los archivos
        if archivos_guardados:
            acta_portal.save()
            logger.info(f'Archivos guardados en ActaMunicipal {acta_portal.id}: {archivos_guardados}')
        
        return documentos_generados
        
    except Exception as e:
        logger.error(f'Error generando documentos mejorados: {str(e)}')
        return {}
        
        # 2. Generar archivo HTML
        nombre_html = f"{gestion_acta.numero_acta or 'ACTA'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        archivo_html = os.path.join(directorio_docs, nombre_html)
        
        contenido_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>{gestion_acta.titulo}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .metadata {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; }}
    </style>
</head>
<body>
    <h1>ACTA MUNICIPAL</h1>
    <div class="metadata">
        <strong>Número:</strong> {gestion_acta.numero_acta or 'N/A'}<br>
        <strong>Fecha:</strong> {gestion_acta.fecha_creacion.strftime('%d/%m/%Y %H:%M')}<br>
        <strong>Estado:</strong> Publicada<br>
    </div>
    <h2>Título</h2>
    <p>{gestion_acta.titulo}</p>
    <h2>Contenido</h2>
    <div>{contenido_completo.replace(chr(10), '<br>')}</div>
    <hr>
    <p><em>Documento generado automáticamente el {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}</em></p>
</body>
</html>"""
        
        with open(archivo_html, 'w', encoding='utf-8') as f:
            f.write(contenido_html)
        
        documentos_generados['html'] = {
            'ruta': archivo_html,
            'nombre': nombre_html,
            'tipo': 'text/html'
        }
        
        # 3. Si existe WeasyPrint, generar PDF
        try:
            import weasyprint
            nombre_pdf = f"{gestion_acta.numero_acta or 'ACTA'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            archivo_pdf = os.path.join(directorio_docs, nombre_pdf)
            
            # Generar PDF desde HTML
            html_doc = weasyprint.HTML(string=contenido_html)
            html_doc.write_pdf(archivo_pdf)
            
            documentos_generados['pdf'] = {
                'ruta': archivo_pdf,
                'nombre': nombre_pdf,
                'tipo': 'application/pdf'
            }
            
            # Asignar PDF al acta del portal
            if acta_portal:
                with open(archivo_pdf, 'rb') as pdf_file:
                    acta_portal.archivo_pdf.save(
                        nombre_pdf,
                        ContentFile(pdf_file.read()),
                        save=True
                    )
                    
        except ImportError:
            logger.warning("WeasyPrint no disponible - no se generará PDF")
        except Exception as pdf_error:
            logger.error(f"Error generando PDF: {str(pdf_error)}")
        
        return documentos_generados
        
    except Exception as e:
        logger.error(f'Error generando documentos: {str(e)}')
        return {}


def _formatear_contenido_acta(gestion_acta):
    """Formatear el contenido del acta para documentos"""
    contenido = []
    
    contenido.append("=" * 80)
    contenido.append("ACTA MUNICIPAL - MUNICIPIO DE PASTAZA")
    contenido.append("=" * 80)
    contenido.append("")
    
    contenido.append(f"Número de Acta: {gestion_acta.numero_acta or 'N/A'}")
    contenido.append(f"Título: {gestion_acta.titulo}")
    contenido.append(f"Fecha de Generación: {gestion_acta.fecha_creacion.strftime('%d de %B de %Y a las %H:%M:%S')}")
    contenido.append(f"Estado: {gestion_acta.estado.nombre if gestion_acta.estado else 'N/A'}")
    contenido.append("")
    contenido.append("-" * 80)
    contenido.append("CONTENIDO DEL ACTA")
    contenido.append("-" * 80)
    contenido.append("")
    
    # Agregar contenido principal
    if gestion_acta.contenido_editado:
        contenido.append(gestion_acta.contenido_editado)
    else:
        contenido.append("Sin contenido disponible.")
    
    contenido.append("")
    contenido.append("-" * 80)
    
    if gestion_acta.observaciones:
        contenido.append("OBSERVACIONES")
        contenido.append("-" * 80)
        contenido.append(gestion_acta.observaciones)
        contenido.append("")
    
    contenido.append("-" * 80)
    contenido.append("INFORMACIÓN ADICIONAL")
    contenido.append("-" * 80)
    contenido.append(f"Documento generado el: {timezone.now().strftime('%d de %B de %Y a las %H:%M:%S')}")
    contenido.append("Sistema de Gestión de Actas Municipales - Municipio de Pastaza")
    contenido.append("=" * 80)
    
    return "\n".join(contenido)

