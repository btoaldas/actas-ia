"""
Vistas principales para el módulo generador de actas
Incluye dashboard, CRUD de plantillas y gestión de actas
"""
import json
import logging
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.transcripcion.models import Transcripcion
from .models import (
    ActaGenerada, ProveedorIA, PlantillaActa, 
    SegmentoPlantilla, ConfiguracionSegmento
)
from .services import GeneradorActasService, PlantillasService, EstadisticasService
from .forms import ActaGeneradaForm, PlantillaActaForm, ConfiguracionSegmentoFormSet

logger = logging.getLogger(__name__)


# ================== DASHBOARD ==================

@login_required
def dashboard_actas(request):
    """
    Dashboard principal del módulo generador de actas
    """
    try:
        # Obtener estadísticas del dashboard
        stats = EstadisticasService.obtener_resumen_dashboard()
        
        # Actas recientes
        actas_recientes = ActaGenerada.objects.select_related(
            'plantilla', 'proveedor_ia', 'usuario_creacion'
        ).order_by('-fecha_creacion')[:10]
        
        # Transcripciones disponibles para procesar
        transcripciones_disponibles = Transcripcion.objects.filter(
            conversacion_json__isnull=False,
            actagenerada__isnull=True  # Sin acta generada
        ).select_related('procesamiento_audio').order_by('-fecha_creacion')[:5]
        
        # Actas en procesamiento
        actas_procesando = ActaGenerada.objects.filter(
            estado__in=['en_cola', 'procesando', 'procesando_segmentos', 'unificando']
        ).select_related('plantilla', 'proveedor_ia')
        
        context = {
            'stats': stats,
            'actas_recientes': actas_recientes,
            'transcripciones_disponibles': transcripciones_disponibles,
            'actas_procesando': actas_procesando,
            'page_title': 'Generador de Actas IA',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador de Actas', 'active': True}
            ]
        }
        
        return render(request, 'generador_actas/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        messages.error(request, f"Error cargando el dashboard: {str(e)}")
        return render(request, 'generador_actas/dashboard.html', {
            'error': str(e),
            'page_title': 'Generador de Actas IA'
        })


# ================== ACTAS CRUD ==================

class ActasListView(LoginRequiredMixin, ListView):
    """
    Vista de listado de actas generadas con filtros y búsqueda
    """
    model = ActaGenerada
    template_name = 'generador_actas/actas_lista.html'
    context_object_name = 'actas'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ActaGenerada.objects.select_related(
            'plantilla', 'proveedor_ia', 'usuario_creacion', 'transcripcion'
        ).order_by('-fecha_creacion')
        
        # Filtros de búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero_acta__icontains=search) |
                Q(titulo__icontains=search) |
                Q(plantilla__nombre__icontains=search)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por proveedor IA
        proveedor = self.request.GET.get('proveedor')
        if proveedor:
            queryset = queryset.filter(proveedor_ia_id=proveedor)
        
        # Filtro por plantilla
        plantilla = self.request.GET.get('plantilla')
        if plantilla:
            queryset = queryset.filter(plantilla_id=plantilla)
        
        # Filtro por fecha
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if fecha_desde:
            try:
                fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_sesion__gte=fecha_desde)
            except ValueError:
                pass
        
        if fecha_hasta:
            try:
                fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_sesion__lte=fecha_hasta)
            except ValueError:
                pass
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Actas Generadas',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Actas', 'active': True}
            ],
            'estados_choices': ActaGenerada.ESTADO_CHOICES,
            'proveedores': ProveedorIA.objects.filter(activo=True),
            'plantillas': PlantillaActa.objects.filter(activa=True),
            'filtros_activos': {
                'search': self.request.GET.get('search', ''),
                'estado': self.request.GET.get('estado', ''),
                'proveedor': self.request.GET.get('proveedor', ''),
                'plantilla': self.request.GET.get('plantilla', ''),
                'fecha_desde': self.request.GET.get('fecha_desde', ''),
                'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
            }
        })
        return context


class ActaDetailView(LoginRequiredMixin, DetailView):
    """
    Vista detallada de un acta con toda la información
    """
    model = ActaGenerada
    template_name = 'generador_actas/acta_detail.html'
    context_object_name = 'acta'
    
    def get_object(self):
        obj = get_object_or_404(
            ActaGenerada.objects.select_related(
                'plantilla', 'proveedor_ia', 'usuario_creacion', 
                'transcripcion', 'transcripcion__procesamiento_audio'
            ).prefetch_related('historial_cambios'),
            pk=self.kwargs['pk']
        )
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        acta = context['acta']
        
        # Obtener estado del procesamiento
        estado_info = GeneradorActasService.obtener_estado_procesamiento(acta)
        
        # Información de segmentos si están disponibles
        segmentos_info = []
        if acta.segmentos_procesados:
            for key, segmento_data in acta.segmentos_procesados.items():
                segmentos_info.append(segmento_data)
            segmentos_info.sort(key=lambda x: x.get('orden', 0))
        
        context.update({
            'page_title': f'Acta {acta.numero_acta}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Actas', 'url': reverse('generador_actas:actas_list')},
                {'name': acta.numero_acta, 'active': True}
            ],
            'estado_info': estado_info,
            'segmentos_info': segmentos_info,
            'puede_editar': acta.estado in ['borrador', 'revision'],
            'puede_procesar': acta.puede_procesar,
            'puede_exportar': acta.contenido_final or acta.contenido_borrador
        })
        return context


@login_required
def crear_acta_desde_transcripcion(request, transcripcion_id):
    """
    Vista para crear una nueva acta desde una transcripción
    """
    transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
    
    # Validar transcripción
    es_valida, errores = GeneradorActasService.validar_transcripcion_para_acta(transcripcion)
    if not es_valida:
        messages.error(request, f"La transcripción no es válida: {', '.join(errores)}")
        return redirect('generador_actas:dashboard')
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            plantilla_id = request.POST.get('plantilla')
            proveedor_id = request.POST.get('proveedor_ia')
            titulo = request.POST.get('titulo', '').strip()
            
            # Validar campos requeridos
            if not plantilla_id or not proveedor_id:
                raise ValidationError("La plantilla y proveedor IA son requeridos")
            
            plantilla = get_object_or_404(PlantillaActa, id=plantilla_id, activa=True)
            proveedor = get_object_or_404(ProveedorIA, id=proveedor_id, activo=True)
            
            # Crear acta básica usando mock transcription (temporal)
            from django.utils import timezone
            mock_transcripcion = None  # Temporal hasta tener transcripción real
            
            # Crear acta básica
            acta = ActaGenerada.objects.create(
                plantilla=plantilla,
                proveedor_ia=proveedor,
                titulo=titulo or f"Acta generada - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                transcripcion=mock_transcripcion,
                estado='borrador',
                usuario_creacion=request.user
            )
            
            messages.success(request, f"Acta {acta.numero_acta} creada exitosamente")
            return redirect('generador_actas:acta_detail', pk=acta.pk)
            
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Error creando acta: {str(e)}")
            messages.error(request, f"Error creando acta: {str(e)}")
    
    # GET request - mostrar formulario
    plantillas_compatibles = GeneradorActasService.obtener_plantillas_compatibles(transcripcion)
    proveedores_activos = ProveedorIA.objects.filter(activo=True)
    
    context = {
        'transcripcion': transcripcion,
        'plantillas': plantillas_compatibles,
        'proveedores': proveedores_activos,
        'page_title': 'Crear Acta desde Transcripción',
        'breadcrumb': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Generador', 'url': reverse('generador_actas:dashboard')},
            {'name': 'Nueva Acta', 'active': True}
        ]
    }
    
    return render(request, 'generador_actas/crear_acta.html', context)


@login_required
@require_http_methods(["POST"])
def procesar_acta(request, acta_id):
    """
    Inicia el procesamiento asíncrono de un acta
    """
    try:
        acta = get_object_or_404(ActaGenerada, id=acta_id)
        
        # Verificar permisos
        if not acta.puede_procesar:
            return JsonResponse({
                'success': False,
                'message': f'El acta está en estado {acta.estado} y no puede ser procesada'
            })
        
        # Iniciar procesamiento
        task_id = GeneradorActasService.procesar_acta_asincrono(acta)
        
        return JsonResponse({
            'success': True,
            'task_id': task_id,
            'message': 'Procesamiento iniciado exitosamente'
        })
        
    except Exception as e:
        logger.error(f"Error iniciando procesamiento: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Error iniciando procesamiento: {str(e)}'
        })


@login_required
def estado_procesamiento(request, acta_id):
    """
    Obtiene el estado actual del procesamiento de un acta
    """
    try:
        acta = get_object_or_404(ActaGenerada, id=acta_id)
        estado_info = GeneradorActasService.obtener_estado_procesamiento(acta)
        
        return JsonResponse({
            'success': True,
            'data': estado_info
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo estado: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def exportar_acta(request, acta_id):
    """
    Exporta un acta en el formato solicitado
    """
    try:
        acta = get_object_or_404(ActaGenerada, id=acta_id)
        formato = request.GET.get('formato', 'txt')
        
        if formato not in ['txt', 'pdf', 'docx']:
            raise ValidationError("Formato no válido")
        
        # Exportar acta
        contenido = GeneradorActasService.exportar_acta(acta, formato)
        
        # Configurar response
        filename = f"acta_{acta.numero_acta}.{formato}"
        content_types = {
            'txt': 'text/plain',
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        response = HttpResponse(contenido, content_type=content_types[formato])
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exportando acta: {str(e)}")
        messages.error(request, f"Error exportando acta: {str(e)}")
        return redirect('generador_actas:acta_detail', pk=acta_id)


# ================== PLANTILLAS CRUD ==================

class PlantillasListView(LoginRequiredMixin, ListView):
    """
    Vista de listado de plantillas de actas
    """
    model = PlantillaActa
    template_name = 'generador_actas/plantillas_lista.html'
    context_object_name = 'plantillas'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = PlantillaActa.objects.annotate(
            segmentos_count=Count('configuracionsegmento'),
            actas_count=Count('actagenerada')
        ).order_by('-fecha_creacion')
        
        # Filtro de búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(tipo_acta__icontains=search)
            )
        
        # Filtro por tipo
        tipo_acta = self.request.GET.get('tipo_acta')
        if tipo_acta:
            queryset = queryset.filter(tipo_acta=tipo_acta)
        
        # Filtro por estado
        activa = self.request.GET.get('activa')
        if activa == '1':
            queryset = queryset.filter(activa=True)
        elif activa == '0':
            queryset = queryset.filter(activa=False)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Plantillas de Actas',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Plantillas', 'active': True}
            ],
            'tipos_acta': PlantillaActa.TIPO_ACTA,
            'filtros_activos': {
                'search': self.request.GET.get('search', ''),
                'tipo_acta': self.request.GET.get('tipo_acta', ''),
                'activa': self.request.GET.get('activa', ''),
            }
        })
        return context


class PlantillaDetailView(LoginRequiredMixin, DetailView):
    """
    Vista detallada de una plantilla
    """
    model = PlantillaActa
    template_name = 'generador_actas/plantilla_detail.html'
    context_object_name = 'plantilla'
    
    def get_object(self):
        return get_object_or_404(
            PlantillaActa.objects.prefetch_related(
                'configuracionsegmento_set__segmento'
            ),
            pk=self.kwargs['pk']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plantilla = context['plantilla']
        
        # Configuraciones de segmentos ordenadas
        configuraciones = plantilla.configuracionsegmento_set.all().order_by('orden')
        
        # Estadísticas de uso
        actas_generadas = plantilla.actagenerada_set.count()
        actas_recientes = plantilla.actagenerada_set.order_by('-fecha_creacion')[:5]
        
        context.update({
            'page_title': plantilla.nombre,
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'name': plantilla.nombre, 'active': True}
            ],
            'configuraciones': configuraciones,
            'actas_generadas': actas_generadas,
            'actas_recientes': actas_recientes
        })
        return context


@login_required
def duplicar_plantilla(request, plantilla_id):
    """
    Duplica una plantilla existente
    """
    try:
        plantilla_origen = get_object_or_404(PlantillaActa, id=plantilla_id)
        
        if request.method == 'POST':
            nuevo_nombre = request.POST.get('nombre', '').strip()
            if not nuevo_nombre:
                raise ValidationError("El nombre es requerido")
            
            # Verificar que no exista otra plantilla con el mismo nombre
            if PlantillaActa.objects.filter(nombre=nuevo_nombre).exists():
                raise ValidationError("Ya existe una plantilla con ese nombre")
            
            # Duplicar plantilla
            nueva_plantilla = PlantillasService.duplicar_plantilla(
                plantilla_origen, nuevo_nombre, request.user
            )
            
            messages.success(request, f"Plantilla '{nuevo_nombre}' duplicada exitosamente")
            return redirect('generador_actas:plantilla_detail', pk=nueva_plantilla.pk)
        
        # GET request - mostrar formulario
        context = {
            'plantilla_origen': plantilla_origen,
            'page_title': f'Duplicar: {plantilla_origen.nombre}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'name': 'Duplicar', 'active': True}
            ]
        }
        
        return render(request, 'generador_actas/duplicar_plantilla.html', context)
        
    except ValidationError as e:
        messages.error(request, str(e))
        return redirect('generador_actas:plantilla_detail', pk=plantilla_id)
    except Exception as e:
        logger.error(f"Error duplicando plantilla: {str(e)}")
        messages.error(request, f"Error duplicando plantilla: {str(e)}")
        return redirect('generador_actas:plantilla_detail', pk=plantilla_id)


# ================== TRANSCRIPCIONES ==================

@login_required
def transcripciones_disponibles(request):
    """
    Vista de transcripciones disponibles para generar actas
    """
    try:
        # Transcripciones sin acta generada
        transcripciones = Transcripcion.objects.filter(
            conversacion_json__isnull=False,
            actragenerada__isnull=True
        ).select_related(
            'procesamiento_audio',
            'procesamiento_audio__tipo_reunion'
        ).order_by('-fecha_creacion')
        
        # Filtros
        search = request.GET.get('search')
        if search:
            transcripciones = transcripciones.filter(
                Q(procesamiento_audio__nombre_archivo__icontains=search) |
                Q(procesamiento_audio__ubicacion__icontains=search)
            )
        
        # Paginación
        paginator = Paginator(transcripciones, 10)
        page = request.GET.get('page')
        
        try:
            transcripciones_page = paginator.page(page)
        except PageNotAnInteger:
            transcripciones_page = paginator.page(1)
        except EmptyPage:
            transcripciones_page = paginator.page(paginator.num_pages)
        
        context = {
            'transcripciones': transcripciones_page,
            'page_title': 'Transcripciones Disponibles',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Transcripciones', 'active': True}
            ],
            'search': search or ''
        }
        
        return render(request, 'generador_actas/transcripciones_disponibles.html', context)
        
    except Exception as e:
        logger.error(f"Error cargando transcripciones: {str(e)}")
        messages.error(request, f"Error cargando transcripciones: {str(e)}")
        return redirect('generador_actas:dashboard')


# ================== VISTAS DE PROVEEDORES IA ==================

class ProveedoresListView(LoginRequiredMixin, ListView):
    """Vista de listado de proveedores IA"""
    model = ProveedorIA
    template_name = 'generador_actas/proveedores_lista.html'
    context_object_name = 'proveedores'
    paginate_by = 20
    
    def get_queryset(self):
        """Aplicar filtros y búsqueda"""
        queryset = ProveedorIA.objects.all().order_by('-fecha_creacion')
        
        # Filtro por búsqueda
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(tipo__icontains=search)
            )
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo', '')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        # Filtro por estado
        activo = self.request.GET.get('activo', '')
        if activo:
            queryset = queryset.filter(activo=activo == '1')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Dashboard de Proveedores IA',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Proveedores IA', 'active': True}
            ],
            'search': self.request.GET.get('search', ''),
            'tipo_filter': self.request.GET.get('tipo', ''),
            'activo_filter': self.request.GET.get('activo', ''),
            'tipos_proveedor': ProveedorIA.TIPO_PROVEEDOR,
            'stats': {
                'total': ProveedorIA.objects.count(),
                'activos': ProveedorIA.objects.filter(activo=True).count(),
                'inactivos': ProveedorIA.objects.filter(activo=False).count(),
            }
        })
        return context


class ProveedorDetailView(LoginRequiredMixin, DetailView):
    """Vista de detalle de proveedor IA"""
    model = ProveedorIA
    template_name = 'generador_actas/proveedor_detail.html'
    context_object_name = 'proveedor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proveedor = self.get_object()
        
        context.update({
            'page_title': f'Proveedor IA: {proveedor.nombre}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Proveedores', 'url': reverse('generador_actas:proveedores_lista')},
                {'name': proveedor.nombre, 'active': True}
            ],
            'actas_procesadas': ActaGenerada.objects.filter(proveedor_ia=proveedor).count(),
            'plantillas_usando': PlantillaActa.objects.filter(proveedor_ia_defecto=proveedor).count()
        })
        return context


class CrearProveedorView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo proveedor IA"""
    model = ProveedorIA
    template_name = 'generador_actas/proveedor_form.html'
    fields = ['nombre', 'tipo', 'api_key', 'modelo', 'temperatura', 'max_tokens', 'activo', 'configuracion_adicional']
    success_url = reverse_lazy('generador_actas:proveedores_lista')
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, f'Proveedor IA "{form.instance.nombre}" creado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Crear Proveedor IA',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Proveedores', 'url': reverse('generador_actas:proveedores_lista')},
                {'name': 'Crear', 'active': True}
            ],
            'form_title': 'Crear Nuevo Proveedor IA',
            'submit_text': 'Crear Proveedor'
        })
        return context


class EditarProveedorView(LoginRequiredMixin, UpdateView):
    """Vista para editar un proveedor IA"""
    model = ProveedorIA
    template_name = 'generador_actas/proveedor_form.html'
    fields = ['nombre', 'tipo', 'api_key', 'modelo', 'temperatura', 'max_tokens', 'activo', 'configuracion_adicional']
    success_url = reverse_lazy('generador_actas:proveedores_lista')
    
    def form_valid(self, form):
        messages.success(self.request, f'Proveedor IA "{form.instance.nombre}" actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proveedor = self.get_object()
        context.update({
            'page_title': f'Editar Proveedor: {proveedor.nombre}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Proveedores', 'url': reverse('generador_actas:proveedores_lista')},
                {'name': 'Editar', 'active': True}
            ],
            'form_title': f'Editar Proveedor: {proveedor.nombre}',
            'submit_text': 'Actualizar Proveedor'
        })
        return context


class EliminarProveedorView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un proveedor IA"""
    model = ProveedorIA
    template_name = 'generador_actas/proveedor_confirm_delete.html'
    success_url = reverse_lazy('generador_actas:proveedores_lista')
    
    def delete(self, request, *args, **kwargs):
        proveedor = self.get_object()
        messages.success(request, f'Proveedor IA "{proveedor.nombre}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ================== VISTAS DE SEGMENTOS ==================

class SegmentosListView(LoginRequiredMixin, ListView):
    """Vista de listado de segmentos de plantillas"""
    model = SegmentoPlantilla
    template_name = 'generador_actas/segmentos_lista.html'
    context_object_name = 'segmentos'
    paginate_by = 20
    
    def get_queryset(self):
        """Aplicar filtros y búsqueda"""
        queryset = SegmentoPlantilla.objects.all().order_by('categoria', 'nombre')
        
        # Filtro por búsqueda
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(categoria__icontains=search)
            )
        
        # Filtro por categoría
        categoria = self.request.GET.get('categoria', '')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo', '')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Dashboard de Segmentos de Actas',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Segmentos', 'active': True}
            ],
            'search': self.request.GET.get('search', ''),
            'categoria_filter': self.request.GET.get('categoria', ''),
            'tipo_filter': self.request.GET.get('tipo', ''),
            'categorias': SegmentoPlantilla.CATEGORIA_SEGMENTO,
            'tipos': SegmentoPlantilla.TIPO_SEGMENTO,
            'stats': {
                'total': SegmentoPlantilla.objects.count(),
                'dinamicos': SegmentoPlantilla.objects.filter(tipo='dinamico').count(),
                'estaticos': SegmentoPlantilla.objects.filter(tipo='estatico').count(),
                'hibridos': SegmentoPlantilla.objects.filter(tipo='hibrido').count(),
            }
        })
        return context


class SegmentoDetailView(LoginRequiredMixin, DetailView):
    """Vista de detalle de segmento"""
    model = SegmentoPlantilla
    template_name = 'generador_actas/segmento_detail.html'
    context_object_name = 'segmento'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        segmento = self.get_object()
        
        context.update({
            'page_title': f'Segmento: {segmento.nombre}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Segmentos', 'url': reverse('generador_actas:segmentos_lista')},
                {'name': segmento.nombre, 'active': True}
            ],
            'plantillas_usando': ConfiguracionSegmento.objects.filter(segmento=segmento).count()
        })
        return context


class CrearSegmentoView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo segmento"""
    model = SegmentoPlantilla
    template_name = 'generador_actas/segmento_form.html'
    fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'tipo', 'prompt_ia', 'estructura_json', 'componentes', 'parametros_entrada']
    success_url = reverse_lazy('generador_actas:segmentos_lista')
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, f'Segmento "{form.instance.nombre}" creado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Crear Segmento de Acta',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Segmentos', 'url': reverse('generador_actas:segmentos_lista')},
                {'name': 'Crear', 'active': True}
            ],
            'form_title': 'Crear Nuevo Segmento',
            'submit_text': 'Crear Segmento'
        })
        return context


class EditarSegmentoView(LoginRequiredMixin, UpdateView):
    """Vista para editar un segmento"""
    model = SegmentoPlantilla
    template_name = 'generador_actas/segmento_form.html'
    fields = ['codigo', 'nombre', 'descripcion', 'categoria', 'tipo', 'prompt_ia', 'estructura_json', 'componentes', 'parametros_entrada']
    success_url = reverse_lazy('generador_actas:segmentos_lista')
    
    def form_valid(self, form):
        messages.success(self.request, f'Segmento "{form.instance.nombre}" actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        segmento = self.get_object()
        context.update({
            'page_title': f'Editar Segmento: {segmento.nombre}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Segmentos', 'url': reverse('generador_actas:segmentos_lista')},
                {'name': 'Editar', 'active': True}
            ],
            'form_title': f'Editar Segmento: {segmento.nombre}',
            'submit_text': 'Actualizar Segmento'
        })
        return context


class EliminarSegmentoView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar un segmento"""
    model = SegmentoPlantilla
    template_name = 'generador_actas/segmento_confirm_delete.html'
    success_url = reverse_lazy('generador_actas:segmentos_lista')
    
    def delete(self, request, *args, **kwargs):
        segmento = self.get_object()
        messages.success(request, f'Segmento "{segmento.nombre}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ================== VISTAS DE PLANTILLAS (EXTENDIDAS) ==================

class CrearPlantillaView(LoginRequiredMixin, CreateView):
    """Vista para crear una nueva plantilla"""
    model = PlantillaActa
    template_name = 'generador_actas/plantilla_form.html'
    fields = ['codigo', 'nombre', 'descripcion', 'tipo_acta', 'prompt_global', 'proveedor_ia_defecto', 'activa']
    success_url = reverse_lazy('generador_actas:plantillas_lista')
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        messages.success(self.request, f'Plantilla "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Crear Plantilla de Acta',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'name': 'Crear', 'active': True}
            ],
            'form_title': 'Crear Nueva Plantilla',
            'submit_text': 'Crear Plantilla',
            'segmentos_disponibles': SegmentoPlantilla.objects.all().order_by('categoria', 'nombre')
        })
        return context


class EditarPlantillaView(LoginRequiredMixin, UpdateView):
    """Vista para editar una plantilla"""
    model = PlantillaActa
    template_name = 'generador_actas/plantilla_form.html'
    fields = ['codigo', 'nombre', 'descripcion', 'tipo_acta', 'prompt_global', 'proveedor_ia_defecto', 'activa']
    success_url = reverse_lazy('generador_actas:plantillas_lista')
    
    def form_valid(self, form):
        messages.success(self.request, f'Plantilla "{form.instance.nombre}" actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plantilla = self.get_object()
        context.update({
            'page_title': f'Editar Plantilla: {plantilla.nombre}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'name': 'Editar', 'active': True}
            ],
            'form_title': f'Editar Plantilla: {plantilla.nombre}',
            'submit_text': 'Actualizar Plantilla',
            'segmentos_disponibles': SegmentoPlantilla.objects.all().order_by('categoria', 'nombre'),
            'segmentos_configurados': ConfiguracionSegmento.objects.filter(plantilla=plantilla).order_by('orden')
        })
        return context


class EliminarPlantillaView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar una plantilla"""
    model = PlantillaActa
    template_name = 'generador_actas/plantilla_confirm_delete.html'
    success_url = reverse_lazy('generador_actas:plantillas_lista')
    
    def delete(self, request, *args, **kwargs):
        plantilla = self.get_object()
        messages.success(request, f'Plantilla "{plantilla.nombre}" eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ================== VISTAS DE ACTAS (EXTENDIDAS) ==================

class CrearActaView(LoginRequiredMixin, CreateView):
    """Vista para crear una nueva acta IA"""
    model = ActaGenerada
    template_name = 'generador_actas/acta_form.html'
    fields = ['numero_acta', 'titulo', 'plantilla', 'transcripcion', 'proveedor_ia']
    success_url = reverse_lazy('generador_actas:actas_lista')
    
    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        form.instance.estado = 'borrador'
        messages.success(self.request, f'Acta "{form.instance.numero_acta}" creada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Crear Acta IA',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Actas', 'url': reverse('generador_actas:actas_lista')},
                {'name': 'Crear', 'active': True}
            ],
            'form_title': 'Crear Nueva Acta con IA',
            'submit_text': 'Crear Acta',
            'plantillas_activas': PlantillaActa.objects.filter(activa=True),
            'proveedores_activos': ProveedorIA.objects.filter(activo=True),
            'transcripciones_disponibles': Transcripcion.objects.filter(estado='completada').order_by('-fecha_creacion')[:50]
        })
        return context


class EditarActaView(LoginRequiredMixin, UpdateView):
    """Vista para editar una acta IA"""
    model = ActaGenerada
    template_name = 'generador_actas/acta_form.html'
    fields = ['numero_acta', 'titulo', 'plantilla', 'transcripcion', 'proveedor_ia']
    success_url = reverse_lazy('generador_actas:actas_lista')
    
    def form_valid(self, form):
        messages.success(self.request, f'Acta "{form.instance.numero_acta}" actualizada exitosamente.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        acta = self.get_object()
        context.update({
            'page_title': f'Editar Acta: {acta.numero_acta}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Actas', 'url': reverse('generador_actas:actas_lista')},
                {'name': 'Editar', 'active': True}
            ],
            'form_title': f'Editar Acta: {acta.numero_acta}',
            'submit_text': 'Actualizar Acta',
            'plantillas_activas': PlantillaActa.objects.filter(activa=True),
            'proveedores_activos': ProveedorIA.objects.filter(activo=True),
            'transcripciones_disponibles': Transcripcion.objects.filter(estado='completada').order_by('-fecha_creacion')[:50]
        })
        return context


class EliminarActaView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar una acta IA"""
    model = ActaGenerada
    template_name = 'generador_actas/acta_confirm_delete.html'
    success_url = reverse_lazy('generador_actas:actas_lista')
    
    def delete(self, request, *args, **kwargs):
        acta = self.get_object()
        messages.success(request, f'Acta "{acta.numero_acta}" eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)


# ================== VISTA DE CONFIGURACIÓN ==================

class ConfiguracionView(LoginRequiredMixin, DetailView):
    """Vista de configuración global del sistema"""
    template_name = 'generador_actas/configuracion.html'
    
    def get_object(self):
        # Esta vista no tiene un objeto específico, solo muestra configuración global
        return None
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Configuración Global del Generador IA',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Configuración', 'active': True}
            ],
            'stats_generales': {
                'total_proveedores': ProveedorIA.objects.count(),
                'proveedores_activos': ProveedorIA.objects.filter(activo=True).count(),
                'total_segmentos': SegmentoPlantilla.objects.count(),
                'total_plantillas': PlantillaActa.objects.count(),
                'plantillas_activas': PlantillaActa.objects.filter(activa=True).count(),
                'total_actas': ActaGenerada.objects.count(),
                'actas_completadas': ActaGenerada.objects.filter(estado='aprobado').count(),
            },
            'configuracion_sistema': {
                'celery_activo': True,  # TODO: Verificar estado real de Celery
                'redis_activo': True,   # TODO: Verificar estado real de Redis
                'version': '1.0.0',
                'ultima_actualizacion': timezone.now(),
            }
        })
        return context


# ================== OPERACIONES DEL SISTEMA ==================

@login_required
def operaciones_sistema(request):
    """
    Vista principal para gestión de operaciones del sistema
    """
    from .models import OperacionSistema
    
    # Filtros de búsqueda
    estado_filtro = request.GET.get('estado', '')
    tipo_filtro = request.GET.get('tipo', '')
    
    # Operaciones del usuario actual (o todas si es admin)
    if request.user.is_staff:
        operaciones = OperacionSistema.objects.all()
    else:
        operaciones = OperacionSistema.objects.filter(usuario=request.user)
    
    # Aplicar filtros
    if estado_filtro:
        operaciones = operaciones.filter(estado=estado_filtro)
    if tipo_filtro:
        operaciones = operaciones.filter(tipo=tipo_filtro)
    
    # Ordenar por más reciente
    operaciones = operaciones.order_by('-fecha_inicio')
    
    # Paginación
    paginator = Paginator(operaciones, 20)
    page = request.GET.get('page')
    try:
        operaciones_page = paginator.page(page)
    except PageNotAnInteger:
        operaciones_page = paginator.page(1)
    except EmptyPage:
        operaciones_page = paginator.page(paginator.num_pages)
    
    # Estadísticas rápidas
    stats = {
        'total': operaciones.count() if request.user.is_staff else OperacionSistema.objects.filter(usuario=request.user).count(),
        'en_progreso': operaciones.filter(estado__in=['pending', 'queued', 'running']).count(),
        'completadas': operaciones.filter(estado='completed').count(),
        'fallidas': operaciones.filter(estado='failed').count(),
    }
    
    context = {
        'operaciones': operaciones_page,
        'stats': stats,
        'estado_filtro': estado_filtro,
        'tipo_filtro': tipo_filtro,
        'estados_disponibles': [
            ('pending', 'Pendiente'),
            ('queued', 'En Cola'),
            ('running', 'Ejecutándose'),
            ('completed', 'Completado'),
            ('failed', 'Fallido'),
            ('cancelled', 'Cancelado')
        ],
        'tipos_disponibles': [
            ('backup_sistema', 'Backup del Sistema'),
            ('exportar_configuraciones', 'Exportar Configuraciones'),
            ('reiniciar_servicios', 'Reiniciar Servicios'),
            ('probar_proveedores', 'Probar Proveedores IA')
        ],
        'breadcrumb': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
            {'name': 'Operaciones del Sistema', 'active': True}
        ]
    }
    
    return render(request, 'generador_actas/operaciones_sistema.html', context)


@login_required
def detalle_operacion(request, operacion_id):
    """
    Vista detallada de una operación específica
    """
    from .models import OperacionSistema
    
    operacion = get_object_or_404(OperacionSistema, id=operacion_id)
    
    # Verificar permisos
    if not request.user.is_staff and operacion.usuario != request.user:
        raise PermissionDenied("No tienes permisos para ver esta operación")
    
    context = {
        'operacion': operacion,
        'puede_cancelar': operacion.estado in ['pending', 'queued', 'running'],
        'tiene_resultado': operacion.estado == 'completed' and operacion.archivo_resultado,
        'logs_formateados': _formatear_logs(operacion.logs) if operacion.logs else [],
        'breadcrumb': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
            {'name': 'Operaciones', 'url': reverse('generador_actas:operaciones_sistema')},
            {'name': f'Operación #{str(operacion.id)[:8]}', 'active': True}
        ]
    }
    
    return render(request, 'generador_actas/detalle_operacion.html', context)


@login_required
@require_http_methods(["POST"])
def iniciar_operacion_sistema(request):
    """
    Vista para iniciar operaciones del sistema desde formularios HTML
    """
    try:
        tipo_operacion = request.POST.get('tipo')
        if not tipo_operacion:
            messages.error(request, 'Tipo de operación requerido')
            return redirect('generador_actas:operaciones_sistema')
        
        # Preparar parámetros según el tipo
        parametros = {}
        
        if tipo_operacion == 'backup_sistema':
            parametros = {
                'incluir_media': request.POST.get('incluir_media') == 'on',
                'incluir_logs': request.POST.get('incluir_logs') == 'on'
            }
        elif tipo_operacion == 'exportar_configuraciones':
            parametros = {
                'formato': request.POST.get('formato', 'json'),
                'incluir_sensibles': request.POST.get('incluir_sensibles') == 'on'
            }
        elif tipo_operacion == 'reiniciar_servicios':
            servicios = request.POST.getlist('servicios')
            parametros = {
                'servicios': servicios if servicios else ['celery', 'redis']
            }
        elif tipo_operacion == 'probar_proveedores':
            proveedor_ids = request.POST.getlist('proveedor_ids')
            parametros = {
                'proveedor_ids': [int(pid) for pid in proveedor_ids if pid.isdigit()] if proveedor_ids else None
            }
        
        # Crear la operación
        from .models import OperacionSistema
        operacion = OperacionSistema.objects.create(
            tipo=tipo_operacion,
            titulo=_get_titulo_operacion(tipo_operacion),
            descripcion=_get_descripcion_operacion(tipo_operacion, parametros),
            parametros_entrada=parametros,
            usuario=request.user,
            estado='pending'
        )
        
        # Iniciar tarea asíncrona
        task_id = _iniciar_tarea_asincrona(tipo_operacion, operacion.id, parametros)
        
        if task_id:
            operacion.task_id = task_id
            operacion.estado = 'queued'
            operacion.save()
            
            messages.success(request, f'Operación "{operacion.titulo}" iniciada exitosamente')
        else:
            operacion.marcar_fallido('No se pudo iniciar la tarea asíncrona')
            messages.error(request, 'Error al iniciar la operación')
        
        return redirect('generador_actas:detalle_operacion', operacion_id=operacion.id)
        
    except Exception as e:
        logger.error(f"Error iniciando operación: {str(e)}")
        messages.error(request, f'Error interno: {str(e)}')
        return redirect('generador_actas:operaciones_sistema')


@login_required
def configuracion_avanzada(request):
    """
    Vista para configuración avanzada del sistema
    """
    from .models import ConfiguracionSistema
    
    if request.method == 'POST':
        try:
            # Procesar formulario de configuración
            for key, value in request.POST.items():
                if key.startswith('config_'):
                    config_key = key.replace('config_', '')
                    config, created = ConfiguracionSistema.objects.get_or_create(
                        clave=config_key,
                        defaults={
                            'nombre': config_key.replace('_', ' ').title(),
                            'valor': value,
                            'tipo_dato': 'string'
                        }
                    )
                    if not created:
                        config.valor = value
                        config.save()
            
            messages.success(request, 'Configuración actualizada exitosamente')
            return redirect('generador_actas:configuracion_avanzada')
            
        except Exception as e:
            logger.error(f"Error actualizando configuración: {str(e)}")
            messages.error(request, f'Error actualizando configuración: {str(e)}')
    
    # Obtener configuraciones existentes
    configuraciones = ConfiguracionSistema.objects.filter(es_publico=True).order_by('clave')
    
    # Configuraciones por categorías
    config_por_categoria = {}
    for config in configuraciones:
        categoria = config.clave.split('_')[0] if '_' in config.clave else 'general'
        if categoria not in config_por_categoria:
            config_por_categoria[categoria] = []
        config_por_categoria[categoria].append(config)
    
    context = {
        'configuraciones': configuraciones,
        'config_por_categoria': config_por_categoria,
        'stats_sistema': {
            'total_configuraciones': configuraciones.count(),
            'configuraciones_modificadas': configuraciones.filter(
                valor__isnull=False
            ).exclude(valor='').count(),
        },
        'breadcrumb': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
            {'name': 'Configuración Avanzada', 'active': True}
        ]
    }
    
    return render(request, 'generador_actas/configuracion_avanzada.html', context)


# ================== FUNCIONES AUXILIARES ==================

def _formatear_logs(logs):
    """
    Formatea los logs para mostrar en la interfaz
    """
    if not logs or not isinstance(logs, list):
        return []
    
    logs_formateados = []
    for log in logs[-20:]:  # Mostrar solo los últimos 20
        try:
            # Formatear timestamp si existe
            timestamp = log.get('timestamp', '')
            if timestamp:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp_formateado = dt.strftime('%d/%m/%Y %H:%M:%S')
            else:
                timestamp_formateado = 'N/A'
            
            logs_formateados.append({
                'nivel': log.get('nivel', 'info'),
                'mensaje': log.get('mensaje', ''),
                'timestamp': timestamp_formateado,
                'css_class': _get_log_css_class(log.get('nivel', 'info'))
            })
        except:
            # Si hay error parseando, mostrar raw
            logs_formateados.append({
                'nivel': 'info',
                'mensaje': str(log),
                'timestamp': 'N/A',
                'css_class': 'text-secondary'
            })
    
    return logs_formateados


def _get_log_css_class(nivel):
    """
    Retorna la clase CSS para el nivel de log
    """
    clases = {
        'error': 'text-danger',
        'warning': 'text-warning', 
        'info': 'text-primary',
        'debug': 'text-secondary',
        'success': 'text-success'
    }
    return clases.get(nivel, 'text-secondary')


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


def _iniciar_tarea_asincrona(tipo_operacion, operacion_id, parametros):
    """
    Inicia la tarea asíncrona correspondiente y retorna el task ID
    """
    try:
        from .tasks import (
            crear_backup_sistema, exportar_configuraciones,
            reiniciar_servicios_sistema, probar_proveedores_ia
        )
        
        if tipo_operacion == 'backup_sistema':
            task = crear_backup_sistema.delay(
                str(operacion_id),
                parametros.get('incluir_media', True),
                parametros.get('incluir_logs', False)
            )
        elif tipo_operacion == 'exportar_configuraciones':
            task = exportar_configuraciones.delay(
                str(operacion_id),
                parametros.get('formato', 'json'),
                parametros.get('incluir_sensibles', False)
            )
        elif tipo_operacion == 'reiniciar_servicios':
            task = reiniciar_servicios_sistema.delay(
                str(operacion_id),
                parametros.get('servicios', ['celery', 'redis'])
            )
        elif tipo_operacion == 'probar_proveedores':
            task = probar_proveedores_ia.delay(
                str(operacion_id),
                parametros.get('proveedor_ids', None)
            )
        else:
            return None
        
        return task.id
        
    except Exception as e:
        logger.error(f"Error iniciando tarea asíncrona: {str(e)}")
        return None