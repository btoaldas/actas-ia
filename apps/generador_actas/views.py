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
from django.db import transaction, models
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from helpers.util import normalizar_busqueda, crear_filtros_busqueda_multiple
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.transcripcion.models import Transcripcion
from .models import (
    ActaGenerada, ProveedorIA, PlantillaActa, 
    SegmentoPlantilla, ConfiguracionSegmento,
    EjecucionPlantilla, ResultadoSegmento, ActaBorrador
)
from .services import GeneradorActasService, PlantillasService, EstadisticasService
from .forms import ActaGeneradaForm, PlantillaActaForm, ConfiguracionSegmentoFormSet, ProveedorIAForm, TestProveedorForm, SegmentoPlantillaForm, PlantillaBasicaForm

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
            campos_busqueda = ['numero_acta', 'titulo', 'plantilla__nombre']
            filtros_busqueda = crear_filtros_busqueda_multiple(campos_busqueda, search)
            queryset = queryset.filter(filtros_busqueda)
        
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
            campos_busqueda = ['nombre', 'descripcion', 'tipo_acta']
            filtros_busqueda = crear_filtros_busqueda_multiple(campos_busqueda, search)
            queryset = queryset.filter(filtros_busqueda)
        
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
            campos_busqueda = ['procesamiento_audio__nombre_archivo', 'procesamiento_audio__ubicacion']
            filtros_busqueda = crear_filtros_busqueda_multiple(campos_busqueda, search)
            transcripciones = transcripciones.filter(filtros_busqueda)
        
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
            campos_busqueda = ['nombre', 'tipo']
            filtros_busqueda = crear_filtros_busqueda_multiple(campos_busqueda, search)
            queryset = queryset.filter(filtros_busqueda)
        
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
    template_name = 'generador_actas/lista_segmentos.html'
    context_object_name = 'segmentos'
    paginate_by = 20
    
    def get_queryset(self):
        """Aplicar filtros y búsqueda"""
        queryset = SegmentoPlantilla.objects.all().order_by('categoria', 'nombre')
        
        # Filtro por búsqueda
        search = self.request.GET.get('search', '')
        if search:
            campos_busqueda = ['nombre', 'descripcion', 'categoria']
            filtros_busqueda = crear_filtros_busqueda_multiple(campos_busqueda, search)
            queryset = queryset.filter(filtros_busqueda)
        
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
    template_name = 'generador_actas/segmentos/detalle.html'
    context_object_name = 'segmento'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        segmento = self.get_object()
        
        context.update({
            'page_title': f'Segmento: {segmento.nombre}',
            'breadcrumb': [
                {'name': 'Inicio', 'url': '/'},
                {'name': 'Generador IA', 'url': reverse('generador_actas:dashboard')},
                {'name': 'Segmentos', 'url': reverse('generador_actas:lista_segmentos')},
                {'name': segmento.nombre, 'active': True}
            ],
            'plantillas_usando': ConfiguracionSegmento.objects.filter(segmento=segmento).count()
        })
        return context


class CrearSegmentoView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo segmento"""
    model = SegmentoPlantilla
    form_class = SegmentoPlantillaForm  # ¡USAR EL FORMULARIO PERSONALIZADO!
    template_name = 'generador_actas/segmentos/crear.html'
    success_url = reverse_lazy('generador_actas:lista_segmentos')
    
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
                {'name': 'Segmentos', 'url': reverse('generador_actas:lista_segmentos')},
                {'name': 'Crear', 'active': True}
            ],
            'form_title': 'Crear Nuevo Segmento',
            'submit_text': 'Crear Segmento'
        })
        return context


class EditarSegmentoView(LoginRequiredMixin, UpdateView):
    """Vista para editar un segmento"""
    model = SegmentoPlantilla
    form_class = SegmentoPlantillaForm  # ¡USAR EL FORMULARIO PERSONALIZADO!
    template_name = 'generador_actas/segmentos/crear.html'
    success_url = reverse_lazy('generador_actas:lista_segmentos')
    
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
                {'name': 'Segmentos', 'url': reverse('generador_actas:lista_segmentos')},
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
    success_url = reverse_lazy('generador_actas:lista_segmentos')
    
    def delete(self, request, *args, **kwargs):
        segmento = self.get_object()
        messages.success(request, f'Segmento "{segmento.nombre}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


# ================== VISTAS DE PLANTILLAS (EXTENDIDAS) ==================
# NOTA: Las vistas principales de plantillas están más abajo en PlantillaCreateView y PlantillaUpdateView
    
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
    form_class = ActaGeneradaForm
    template_name = 'generador_actas/acta_form.html'
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
            'transcripciones_disponibles': Transcripcion.objects.filter(estado='completado').order_by('-fecha_creacion')[:50]
        })
        return context


class EditarActaView(LoginRequiredMixin, UpdateView):
    """Vista para editar una acta IA"""
    model = ActaGenerada
    form_class = ActaGeneradaForm
    template_name = 'generador_actas/acta_form.html'
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
            'transcripciones_disponibles': Transcripcion.objects.filter(estado='completado').order_by('-fecha_creacion')[:50]
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


# ================== GESTIÓN DE PROVEEDORES IA ==================

@login_required
def lista_proveedores_ia(request):
    """Vista para listar proveedores de IA"""
    
    # Filtros
    filtro_tipo = request.GET.get('tipo', '')
    filtro_activo = request.GET.get('activo', '')
    filtro_busqueda = request.GET.get('q', '')
    orden = request.GET.get('orden', 'nombre')  # Nuevo parámetro de ordenación
    
    # QuerySet base
    proveedores = ProveedorIA.objects.all()
    
    # Aplicar filtros
    if filtro_tipo:
        proveedores = proveedores.filter(tipo=filtro_tipo)
    
    if filtro_activo:
        activo_bool = filtro_activo.lower() == 'true'
        proveedores = proveedores.filter(activo=activo_bool)
    
    if filtro_busqueda:
        proveedores = proveedores.filter(
            Q(nombre__icontains=filtro_busqueda) |
            Q(modelo__icontains=filtro_busqueda)
        )
    
    # Aplicar ordenación
    ordenes_validos = {
        'nombre': 'nombre',
        '-nombre': '-nombre',
        'tipo': 'tipo',
        '-tipo': '-tipo',
        'fecha_creacion': 'fecha_creacion',
        '-fecha_creacion': '-fecha_creacion',
        'ultima_conexion': 'ultima_conexion_exitosa',
        '-ultima_conexion': '-ultima_conexion_exitosa',
        'total_llamadas': 'total_llamadas',
        '-total_llamadas': '-total_llamadas',
        'activo': 'activo',
        '-activo': '-activo'
    }
    
    if orden in ordenes_validos:
        proveedores = proveedores.order_by(ordenes_validos[orden])
    else:
        proveedores = proveedores.order_by('nombre')
    
    # Calcular métricas detalladas
    todos_proveedores = ProveedorIA.objects.all()
    total_proveedores = todos_proveedores.count()
    activos = todos_proveedores.filter(activo=True).count()
    inactivos = todos_proveedores.filter(activo=False).count()
    
    # Métricas adicionales
    con_errores = todos_proveedores.exclude(ultimo_error='').count()
    sin_configurar = sum(1 for p in todos_proveedores if not p.esta_configurado)
    total_llamadas_global = todos_proveedores.aggregate(
        total=Sum('total_llamadas')
    )['total'] or 0
    total_tokens_global = todos_proveedores.aggregate(
        total=Sum('total_tokens_usados')
    )['total'] or 0
    
    # Métricas por tipo
    tipos_stats = {}
    for tipo_code, tipo_name in ProveedorIA.TIPO_PROVEEDOR:
        count = todos_proveedores.filter(tipo=tipo_code).count()
        activos_tipo = todos_proveedores.filter(tipo=tipo_code, activo=True).count()
        if count > 0:
            tipos_stats[tipo_code] = {
                'nombre': tipo_name,
                'total': count,
                'activos': activos_tipo,
                'porcentaje': round((count / total_proveedores) * 100, 1) if total_proveedores > 0 else 0
            }
    
    # Proveedor más usado
    proveedor_mas_usado = todos_proveedores.filter(total_llamadas__gt=0).order_by('-total_llamadas').first()
    
    # Últimas conexiones
    ultimas_conexiones = todos_proveedores.exclude(
        ultima_conexion_exitosa__isnull=True
    ).order_by('-ultima_conexion_exitosa')[:5]
    
    context = {
        'proveedores': proveedores,
        'filtro_tipo': filtro_tipo,
        'filtro_activo': filtro_activo,
        'filtro_busqueda': filtro_busqueda,
        'orden': orden,
        'tipos_disponibles': ProveedorIA.TIPO_PROVEEDOR,
        'ordenes_disponibles': [
            ('nombre', 'Nombre A-Z'),
            ('-nombre', 'Nombre Z-A'),
            ('tipo', 'Tipo A-Z'),
            ('-tipo', 'Tipo Z-A'),
            ('-fecha_creacion', 'Más recientes'),
            ('fecha_creacion', 'Más antiguos'),
            ('-ultima_conexion', 'Última conexión'),
            ('-total_llamadas', 'Más usados'),
            ('total_llamadas', 'Menos usados'),
            ('activo', 'Activos primero'),
            ('-activo', 'Inactivos primero'),
        ],
        'page_title': 'Proveedores de IA',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Proveedores IA', 'url': ''}
        ],
        # Métricas básicas
        'stats_basicas': {
            'total': total_proveedores,
            'activos': activos,
            'inactivos': inactivos,
            'con_errores': con_errores,
        },
        # Métricas avanzadas
        'stats_avanzadas': {
            'sin_configurar': sin_configurar,
            'total_llamadas_global': total_llamadas_global,
            'total_tokens_global': total_tokens_global,
            'proveedor_mas_usado': proveedor_mas_usado,
            'tipos_stats': tipos_stats,
            'ultimas_conexiones': ultimas_conexiones,
        }
    }
    
    return render(request, 'generador_actas/proveedores_ia/lista.html', context)


@login_required
def crear_proveedor_ia(request):
    """Vista para crear un nuevo proveedor de IA"""
    
    if request.method == 'POST':
        form = ProveedorIAForm(request.POST)
        if form.is_valid():
            try:
                proveedor = form.save(commit=False)
                proveedor.usuario_creacion = request.user
                proveedor.save()
                
                messages.success(request, f'Proveedor "{proveedor.nombre}" creado exitosamente.')
                return redirect('generador_actas:proveedores_lista')
            except Exception as e:
                logger.error(f"Error creando proveedor: {str(e)}")
                messages.error(request, f'Error al crear el proveedor: {str(e)}')
    else:
        form = ProveedorIAForm()
    
    context = {
        'form': form,
        'page_title': 'Crear Proveedor IA',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Proveedores IA', 'url': reverse('generador_actas:proveedores_lista')},
            {'title': 'Crear', 'url': ''}
        ],
        'modelos_por_proveedor': json.dumps(ProveedorIAForm.obtener_modelos_por_proveedor())
    }
    
    return render(request, 'generador_actas/proveedores_ia/form.html', context)


@login_required
def editar_proveedor_ia(request, pk):
    """Vista para editar un proveedor de IA"""
    
    proveedor = get_object_or_404(ProveedorIA, pk=pk)
    
    if request.method == 'POST':
        form = ProveedorIAForm(request.POST, instance=proveedor)
        if form.is_valid():
            try:
                proveedor = form.save(commit=False)
                proveedor.usuario_modificacion = request.user
                proveedor.fecha_modificacion = timezone.now()
                proveedor.save()
                
                messages.success(request, f'Proveedor "{proveedor.nombre}" actualizado exitosamente.')
                return redirect('generador_actas:proveedores_lista')
            except Exception as e:
                logger.error(f"Error actualizando proveedor: {str(e)}")
                messages.error(request, f'Error al actualizar el proveedor: {str(e)}')
    else:
        form = ProveedorIAForm(instance=proveedor)
    
    context = {
        'form': form,
        'proveedor': proveedor,
        'page_title': f'Editar {proveedor.nombre}',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Proveedores IA', 'url': reverse('generador_actas:proveedores_lista')},
            {'title': 'Editar', 'url': ''}
        ],
        'modelos_por_proveedor': json.dumps(ProveedorIAForm.obtener_modelos_por_proveedor())
    }
    
    return render(request, 'generador_actas/proveedores_ia/form.html', context)


@login_required
def eliminar_proveedor_ia(request, pk):
    """Vista para eliminar un proveedor de IA"""
    proveedor = get_object_or_404(ProveedorIA, pk=pk)
    
    if request.method == 'POST':
        try:
            # Verificar si tiene actas asociadas
            actas_count = ActaGenerada.objects.filter(proveedor_ia=proveedor).count()
            if actas_count > 0:
                messages.error(
                    request, 
                    f'No se puede eliminar "{proveedor.nombre}" porque tiene {actas_count} actas asociadas.'
                )
                return redirect('generador_actas:proveedores_lista')
            
            nombre = proveedor.nombre
            proveedor.delete()
            messages.success(request, f'Proveedor "{nombre}" eliminado exitosamente.')
            
        except Exception as e:
            logger.error(f"Error eliminando proveedor: {str(e)}")
            messages.error(request, f'Error al eliminar el proveedor: {str(e)}')
    
    return redirect('generador_actas:proveedores_lista')


@csrf_exempt
@require_http_methods(["POST"])
def probar_conexion_proveedor(request):
    """API para probar la conexión con un proveedor de IA"""
    try:
        data = json.loads(request.body)
        proveedor_id = data.get('proveedor_id')
        prompt_prueba = data.get('prompt_prueba', 
            'Dime en JSON tu información real: {"tecnologia": "tu_nombre_real", "modelo": "modelo_real_usado", '
            '"empresa": "tu_empresa_real", "capacidades": "lo_que_puedes_hacer"}. Responde con datos verdaderos.'
        )
        
        if not proveedor_id:
            return JsonResponse({
                'success': False,
                'error': 'ID del proveedor requerido'
            }, status=400)
        
        proveedor = get_object_or_404(ProveedorIA, pk=proveedor_id)
        
        # Importar dinámicamente para evitar errores si no está disponible
        from .ia_providers import get_ia_provider
        
        # Obtener el proveedor y probar conexión
        provider = get_ia_provider(proveedor)
        
        # Ejecutar prueba de conexión con logging detallado
        import time
        
        # Paso 1: Validar conexión
        inicio = timezone.now()
        tiempo_inicio = time.time()
        
        resultado_conexion = provider.test_conexion()
        tiempo_conexion = round(time.time() - tiempo_inicio, 2)
        
        # Extraer datos del resultado de conexión
        exito_conexion = resultado_conexion.get('exito', False)
        mensaje_conexion = resultado_conexion.get('mensaje', 'Error desconocido')
        
        # Paso 2: Si hay prompt y conexión exitosa, ejecutarlo
        prueba_prompt_resultado = {}
        tiempo_total = tiempo_conexion
        
        if exito_conexion and prompt_prueba and prompt_prueba.strip():
            try:
                tiempo_prompt_inicio = time.time()
                
                # Intentar ejecutar el prompt personalizado
                if hasattr(provider, 'generar_respuesta'):
                    respuesta_ia = provider.generar_respuesta(prompt_prueba)
                    tiempo_prompt = round(time.time() - tiempo_prompt_inicio, 2)
                    tiempo_total = tiempo_conexion + tiempo_prompt
                    
                    prueba_prompt_resultado = {
                        'exito': True,
                        'respuesta': respuesta_ia.get('contenido', respuesta_ia.get('response', str(respuesta_ia))),
                        'tokens': respuesta_ia.get('tokens_usados'),
                        'modelo_usado': respuesta_ia.get('modelo_usado', proveedor.modelo),
                        'tiempo_respuesta': tiempo_prompt
                    }
                else:
                    # Fallback para proveedores antiguos
                    respuesta_raw = provider.procesar_prompt(prompt_prueba, {})
                    tiempo_prompt = round(time.time() - tiempo_prompt_inicio, 2)
                    tiempo_total = tiempo_conexion + tiempo_prompt
                    
                    prueba_prompt_resultado = {
                        'exito': True,
                        'respuesta': respuesta_raw.get('contenido', str(respuesta_raw)) if isinstance(respuesta_raw, dict) else str(respuesta_raw),
                        'tokens': respuesta_raw.get('tokens_usados') if isinstance(respuesta_raw, dict) else None,
                        'modelo_usado': proveedor.modelo,
                        'tiempo_respuesta': tiempo_prompt
                    }
                
                # Actualizar contador de llamadas
                proveedor.total_llamadas = (proveedor.total_llamadas or 0) + 1
                
            except Exception as e:
                tiempo_prompt = round(time.time() - tiempo_prompt_inicio, 2)
                tiempo_total = tiempo_conexion + tiempo_prompt
                
                prueba_prompt_resultado = {
                    'exito': False,
                    'error': f'Error ejecutando prompt: {str(e)}',
                    'tiempo_respuesta': tiempo_prompt
                }
        elif prompt_prueba and prompt_prueba.strip():
            prueba_prompt_resultado = {
                'exito': False,
                'error': 'Conexión falló, no se pudo ejecutar el prompt'
            }
        
        # Actualizar métricas del proveedor
        if exito_conexion:
            proveedor.ultima_conexion_exitosa = timezone.now()
            proveedor.ultimo_error = ""
        else:
            proveedor.ultimo_error = mensaje_conexion
        
        proveedor.save()
        
        # Preparar respuesta completa con todos los datos de logging
        response_data = {
            'success': exito_conexion,
            'mensaje': mensaje_conexion,
            'tiempo_respuesta': tiempo_total,
            'timestamp': timezone.now().isoformat(),
            'proveedor': {
                'id': proveedor.id,
                'nombre': proveedor.nombre,
                'tipo': proveedor.tipo,
                'modelo': proveedor.modelo,
                'api_url': proveedor.api_url if proveedor.api_url else 'Default',
            },
            'parametros_envio': {
                'proveedor_id': proveedor.id,
                'proveedor_nombre': proveedor.nombre,
                'proveedor_tipo': proveedor.tipo,
                'modelo': proveedor.modelo,
                'url_api': proveedor.api_url or 'Default',
                'prompt_length': len(prompt_prueba) if prompt_prueba else 0,
                'timestamp_envio': timezone.now().isoformat()
            },
            'prueba_prompt': prueba_prompt_resultado,
            'metricas': {
                'tiempo_respuesta_segundos': tiempo_total,
                'tiempo_conexion': tiempo_conexion,
                'caracteres_prompt': len(prompt_prueba) if prompt_prueba else 0,
                'exito_conexion': exito_conexion,
                'tokens_estimados': prueba_prompt_resultado.get('tokens'),
                'modelo_usado': prueba_prompt_resultado.get('modelo_usado', proveedor.modelo),
                'prompt_ejecutado': prueba_prompt_resultado.get('exito', False)
            },
            'resultado_completo': resultado_conexion
        }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido en la solicitud'
        }, status=400)
    except Exception as e:
        logger.error(f"Error probando conexión proveedor: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_modelos_proveedor(request, tipo_proveedor):
    """API para obtener modelos disponibles por tipo de proveedor"""
    try:
        # Usar modelos desde el formulario actualizado
        modelos_por_proveedor = ProveedorIAForm.obtener_modelos_por_proveedor()
        modelos = modelos_por_proveedor.get(tipo_proveedor, [])
        
        return JsonResponse({
            'success': True,
            'modelos': modelos,
            'tipo_proveedor': tipo_proveedor
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo modelos para {tipo_proveedor}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_configuracion_defecto(request, tipo_proveedor):
    """API para obtener configuración por defecto para un tipo de proveedor"""
    try:
        configuraciones = ProveedorIA.obtener_configuraciones_por_defecto()
        config = configuraciones.get(tipo_proveedor, {})
        
        return JsonResponse({
            'success': True,
            'configuracion': config,
            'tipo_proveedor': tipo_proveedor
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración para {tipo_proveedor}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def probar_conexion_proveedor_celery(request):
    """API para probar conexión usando Celery (procesamiento en segundo plano)"""
    try:
        data = json.loads(request.body)
        proveedor_id = data.get('proveedor_id')
        prompt_prueba = data.get('prompt_prueba', 
            'Responde con un JSON válido indicando información REAL sobre ti mismo. Formato: '
            '{"tecnologia": "ChatGPT/Claude/DeepSeek/etc", "modelo": "tu_modelo_real", "empresa": "OpenAI/Anthropic/etc", "capacidades": "describe_lo_que_puedes_hacer"}'
        )
        incluir_contexto = data.get('incluir_contexto', False)
        
        if not proveedor_id:
            return JsonResponse({
                'success': False,
                'error': 'ID del proveedor requerido'
            }, status=400)
        
        # Verificar que el proveedor existe
        proveedor = get_object_or_404(ProveedorIA, pk=proveedor_id)
        
        # Importar la tarea Celery
        from .tasks import procesar_prueba_ia_task
        
        # Iniciar tarea en segundo plano
        import uuid
        task_uuid = str(uuid.uuid4())
        
        # Enviar a Celery
        task = procesar_prueba_ia_task.delay(
            proveedor_id=proveedor_id,
            prompt_prueba=prompt_prueba,
            incluir_contexto=incluir_contexto,
            task_uuid=task_uuid
        )
        
        return JsonResponse({
            'success': True,
            'task_id': task.id,
            'task_uuid': task_uuid,
            'mensaje': 'Prueba iniciada en segundo plano',
            'proveedor': {
                'id': proveedor.id,
                'nombre': proveedor.nombre,
                'tipo': proveedor.tipo
            }
        })
        
    except Exception as e:
        logger.error(f"Error iniciando prueba Celery: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def obtener_progreso_prueba(request, task_id):
    """API para obtener el progreso de una prueba Celery"""
    try:
        from celery.result import AsyncResult
        from .tasks import obtener_progreso_tarea
        
        # Intentar obtener progreso del cache primero
        progreso = obtener_progreso_tarea(task_id)
        
        if progreso:
            return JsonResponse({
                'success': True,
                'progreso': progreso
            })
        
        # Si no hay progreso en cache, verificar Celery
        task_result = AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            return JsonResponse({
                'success': True,
                'progreso': {
                    'paso': 'PENDIENTE',
                    'detalle': 'Tarea en cola...',
                    'porcentaje': 0,
                    'task_id': task_id
                }
            })
        elif task_result.state == 'SUCCESS':
            return JsonResponse({
                'success': True,
                'resultado': task_result.result,
                'completado': True
            })
        elif task_result.state == 'FAILURE':
            return JsonResponse({
                'success': False,
                'error': str(task_result.info),
                'task_id': task_id
            })
        else:
            return JsonResponse({
                'success': True,
                'progreso': {
                    'paso': task_result.state,
                    'detalle': 'Procesando...',
                    'porcentaje': 50,
                    'task_id': task_id
                }
            })
            
    except Exception as e:
        logger.error(f"Error obteniendo progreso: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def test_proveedor_ia(request):
    """Vista para testing de proveedores"""
    
    if request.method == 'POST':
        form = TestProveedorForm(request.POST)
        if form.is_valid():
            # Redirigir a la página de proveedores con datos de prueba
            return redirect('generador_actas:proveedores_lista')
    else:
        form = TestProveedorForm()
    
    context = {
        'form': form,
        'page_title': 'Probar Proveedores IA',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Proveedores IA', 'url': reverse('generador_actas:proveedores_lista')},
            {'title': 'Probar', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/proveedores_ia/test.html', context)


# ================== VISTAS PARA SEGMENTOS DE PLANTILLA ==================

@login_required
def segmentos_dashboard(request):
    """Dashboard mejorado de segmentos de plantilla con métricas avanzadas"""
    try:
        from django.db.models import Avg, Sum, Count, Max, Min, Q, F, Case, When, FloatField
        
        # Métricas básicas
        stats_basicas = SegmentoPlantilla.objects.aggregate(
            total_segmentos=Count('id'),
            activos=Count('id', filter=Q(activo=True)),
            inactivos=Count('id', filter=Q(activo=False)),
            estaticos=Count('id', filter=Q(tipo='estatico')),
            dinamicos=Count('id', filter=Q(tipo='dinamico')),
            hibridos=Count('id', filter=Q(tipo='hibrido')),
        )
        
        # Métricas de uso y rendimiento
        stats_uso = SegmentoPlantilla.objects.aggregate(
            total_usos=Sum('total_usos') or 0,
            total_errores=Sum('total_errores') or 0,
            tiempo_promedio_global=Avg('tiempo_promedio_procesamiento') or 0.0,
            tasa_exito_promedio=Avg('tasa_exito') or 0.0,
            ultimo_uso=Max('ultima_prueba'),
        )
        
        # Distribución por categorías con estadísticas
        distribucion_categoria = SegmentoPlantilla.objects.values(
            'categoria'
        ).annotate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True)),
            usos=Sum('total_usos') or 0,
            errores=Sum('total_errores') or 0,
            tiempo_promedio=Avg('tiempo_promedio_procesamiento') or 0.0,
            tasa_exito=Avg('tasa_exito') or 0.0
        ).order_by('-total')
        
        # Agregar display names para categorías
        categoria_names = dict(SegmentoPlantilla.CATEGORIA_SEGMENTO)
        for item in distribucion_categoria:
            item['categoria_display'] = categoria_names.get(item['categoria'], item['categoria'])
            # Calcular tasa de error
            if item['usos'] > 0:
                item['tasa_error'] = round((item['errores'] / item['usos']) * 100, 1)
            else:
                item['tasa_error'] = 0.0
        
        # Distribución por tipos con estadísticas
        distribucion_tipo = SegmentoPlantilla.objects.values(
            'tipo'
        ).annotate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True)),
            usos=Sum('total_usos') or 0,
            errores=Sum('total_errores') or 0,
            tiempo_promedio=Avg('tiempo_promedio_procesamiento') or 0.0
        ).order_by('-total')
        
        # Agregar display names para tipos
        tipo_names = dict(SegmentoPlantilla.TIPO_SEGMENTO)
        for item in distribucion_tipo:
            item['tipo_display'] = tipo_names.get(item['tipo'], item['tipo'])
        
        # Segmentos más usados con detalles
        segmentos_populares = SegmentoPlantilla.objects.filter(
            total_usos__gt=0
        ).select_related('proveedor_ia', 'usuario_creacion').order_by('-total_usos', '-tasa_exito')[:10]
        
        # Segmentos recientes con configuración
        segmentos_recientes = SegmentoPlantilla.objects.select_related(
            'proveedor_ia', 'usuario_creacion'
        ).annotate(
            esta_configurado_calc=Case(
                When(Q(tipo='estatico') & Q(contenido_estatico__isnull=False) & ~Q(contenido_estatico=''), then=True),
                When(Q(tipo='dinamico') & Q(prompt_ia__isnull=False) & ~Q(prompt_ia='') & Q(proveedor_ia__isnull=False), then=True),
                When(Q(tipo='hibrido') & Q(contenido_estatico__isnull=False) & ~Q(contenido_estatico=''), then=True),
                default=False,
                output_field=models.BooleanField()
            )
        ).order_by('-fecha_creacion')[:10]
        
        # Segmentos con problemas
        segmentos_problemas = SegmentoPlantilla.objects.filter(
            Q(tasa_exito__lt=80) | Q(total_errores__gt=0) | Q(ultimo_resultado_prueba__icontains='error')
        ).select_related('proveedor_ia').order_by('-total_errores', 'tasa_exito')[:5]
        
        # Segmentos sin configurar
        segmentos_incompletos = SegmentoPlantilla.objects.filter(
            Q(Q(tipo='estatico') & (Q(contenido_estatico='') | Q(contenido_estatico__isnull=True))) |
            Q(Q(tipo='dinamico') & (Q(prompt_ia='') | Q(prompt_ia__isnull=True) | Q(proveedor_ia__isnull=True))) |
            Q(Q(tipo='hibrido') & (Q(contenido_estatico='') | Q(contenido_estatico__isnull=True)))
        ).select_related('usuario_creacion')[:5]
        
        # Proveedores IA más utilizados
        proveedores_stats = ProveedorIA.objects.filter(
            segmentoplantilla__isnull=False
        ).annotate(
            segmentos_count=Count('segmentoplantilla'),
            usos_totales=Sum('segmentoplantilla__total_usos'),
            errores_totales=Sum('segmentoplantilla__total_errores')
        ).filter(segmentos_count__gt=0).order_by('-usos_totales')[:5]
        
        # Estadísticas de salud general
        total_con_uso = stats_basicas['total_segmentos'] - SegmentoPlantilla.objects.filter(total_usos=0).count()
        
        context = {
            'stats': {
                **stats_basicas,
                **stats_uso,
                'total_con_uso': total_con_uso,
                'total_sin_uso': stats_basicas['total_segmentos'] - total_con_uso,
                'porcentaje_activos': round((stats_basicas['activos'] / max(stats_basicas['total_segmentos'], 1)) * 100, 1),
                'porcentaje_con_uso': round((total_con_uso / max(stats_basicas['total_segmentos'], 1)) * 100, 1),
                'tiempo_promedio_global': round(stats_uso['tiempo_promedio_global'], 2),
                'tasa_exito_promedio': round(stats_uso['tasa_exito_promedio'], 1),
            },
            'distribucion_categoria': distribucion_categoria,
            'distribucion_tipo': distribucion_tipo,
            'segmentos_populares': segmentos_populares,
            'segmentos_recientes': segmentos_recientes,
            'segmentos_problemas': segmentos_problemas,
            'segmentos_incompletos': segmentos_incompletos,
            'proveedores_stats': proveedores_stats,
            'page_title': 'Dashboard de Segmentos',
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Segmentos', 'url': ''}
            ]
        }
        
        return render(request, 'generador_actas/segmentos/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error en dashboard_segmentos: {str(e)}")
        messages.error(request, f"Error al cargar el dashboard de segmentos: {str(e)}")
        return redirect('generador_actas:dashboard')


@login_required 
def lista_segmentos(request):
    """Lista mejorada de segmentos con filtros avanzados y paginación"""
    from .forms import SegmentoFiltroForm
    
    try:
        form = SegmentoFiltroForm(request.GET)
        segmentos_qs = SegmentoPlantilla.objects.select_related(
            'proveedor_ia', 'usuario_creacion'
        ).prefetch_related()
        
        # Aplicar filtros si el formulario es válido
        if form.is_valid():
            # Filtro de búsqueda
            buscar = form.cleaned_data.get('buscar')
            if buscar:
                buscar_normalizado = normalizar_busqueda(buscar)
                segmentos_qs = segmentos_qs.filter(
                    Q(nombre__icontains=buscar_normalizado) |
                    Q(codigo__icontains=buscar_normalizado) |
                    Q(descripcion__icontains=buscar_normalizado)
                )
            
            # Filtro por categoría
            categoria = form.cleaned_data.get('categoria')
            if categoria:
                segmentos_qs = segmentos_qs.filter(categoria=categoria)
            
            # Filtro por tipo
            tipo = form.cleaned_data.get('tipo')
            if tipo:
                segmentos_qs = segmentos_qs.filter(tipo=tipo)
            
            # Filtro por proveedor IA
            proveedor_ia = form.cleaned_data.get('proveedor_ia')
            if proveedor_ia:
                segmentos_qs = segmentos_qs.filter(proveedor_ia=proveedor_ia)
            
            # Filtros de estado
            activo = form.cleaned_data.get('activo')
            if activo == 'true':
                segmentos_qs = segmentos_qs.filter(activo=True)
            elif activo == 'false':
                segmentos_qs = segmentos_qs.filter(activo=False)
            
            reutilizable = form.cleaned_data.get('reutilizable')
            if reutilizable == 'true':
                segmentos_qs = segmentos_qs.filter(reutilizable=True)
            elif reutilizable == 'false':
                segmentos_qs = segmentos_qs.filter(reutilizable=False)
            
            obligatorio = form.cleaned_data.get('obligatorio')
            if obligatorio == 'true':
                segmentos_qs = segmentos_qs.filter(obligatorio=True)
            elif obligatorio == 'false':
                segmentos_qs = segmentos_qs.filter(obligatorio=False)
            
            # Filtros avanzados
            estado_salud = form.cleaned_data.get('estado_salud')
            if estado_salud:
                if estado_salud == 'sin_uso':
                    segmentos_qs = segmentos_qs.filter(total_usos=0)
                elif estado_salud == 'excelente':
                    segmentos_qs = segmentos_qs.filter(total_usos__gt=0, total_errores=0)
                elif estado_salud == 'bueno':
                    segmentos_qs = segmentos_qs.filter(total_usos__gt=0, tasa_exito__gte=85, tasa_exito__lt=95)
                elif estado_salud == 'regular':
                    segmentos_qs = segmentos_qs.filter(total_usos__gt=0, tasa_exito__gte=70, tasa_exito__lt=85)
                elif estado_salud == 'problematico':
                    segmentos_qs = segmentos_qs.filter(total_usos__gt=0, tasa_exito__lt=70)
            
            # Filtros especiales
            if form.cleaned_data.get('solo_con_errores'):
                segmentos_qs = segmentos_qs.filter(total_errores__gt=0)
            
            if form.cleaned_data.get('solo_sin_uso'):
                segmentos_qs = segmentos_qs.filter(total_usos=0)
            
            if form.cleaned_data.get('configuracion_incompleta'):
                segmentos_qs = segmentos_qs.filter(
                    Q(Q(tipo='estatico') & (Q(contenido_estatico='') | Q(contenido_estatico__isnull=True))) |
                    Q(Q(tipo='dinamico') & (Q(prompt_ia='') | Q(prompt_ia__isnull=True) | Q(proveedor_ia__isnull=True))) |
                    Q(Q(tipo='hibrido') & (Q(contenido_estatico='') | Q(contenido_estatico__isnull=True)))
                )
            
            # Ordenamiento
            ordenar_por = form.cleaned_data.get('ordenar_por', '-fecha_actualizacion')
            if ordenar_por and ordenar_por.strip():  # Verificar que no esté vacío
                segmentos_qs = segmentos_qs.order_by(ordenar_por)
            else:
                segmentos_qs = segmentos_qs.order_by('-fecha_actualizacion')
        else:
            segmentos_qs = segmentos_qs.order_by('-fecha_actualizacion')
        
        # Paginación
        paginator = Paginator(segmentos_qs, 20)
        page = request.GET.get('page')
        
        try:
            segmentos = paginator.page(page)
        except PageNotAnInteger:
            segmentos = paginator.page(1)
        except EmptyPage:
            segmentos = paginator.page(paginator.num_pages)
        
        # Estadísticas de la consulta actual
        total_filtrados = segmentos_qs.count()
        stats_filtros = {
            'total_filtrados': total_filtrados,
            'total_activos': segmentos_qs.filter(activo=True).count(),
            'total_dinamicos': segmentos_qs.filter(tipo='dinamico').count(),
            'total_con_uso': segmentos_qs.filter(total_usos__gt=0).count(),
            'total_con_errores': segmentos_qs.filter(total_errores__gt=0).count(),
        }
        
        context = {
            'segmentos': segmentos,
            'form': form,
            'stats_filtros': stats_filtros,
            'page_title': 'Lista de Segmentos',
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Segmentos', 'url': reverse('generador_actas:segmentos_dashboard')},
                {'title': 'Lista', 'url': ''}
            ]
        }
        
        return render(request, 'generador_actas/segmentos/lista.html', context)
        
    except Exception as e:
        logger.error(f"Error en lista_segmentos: {str(e)}")
        messages.error(request, f"Error al cargar la lista de segmentos: {str(e)}")
        return redirect('generador_actas:segmentos_dashboard')


@login_required
def crear_segmento(request):
    """Crear nuevo segmento de plantilla"""
    from .forms import SegmentoPlantillaForm
    
    if request.method == 'POST':
        form = SegmentoPlantillaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    segmento = form.save(commit=False)
                    segmento.usuario_creacion = request.user
                    segmento.save()
                    
                    messages.success(request, f"Segmento '{segmento.nombre}' creado exitosamente")
                    return redirect('generador_actas:detalle_segmento', pk=segmento.pk)
                    
            except Exception as e:
                logger.error(f"Error al crear segmento: {str(e)}")
                messages.error(request, f"Error al crear el segmento: {str(e)}")
    else:
        form = SegmentoPlantillaForm()
    
    context = {
        'form': form,
        'page_title': 'Crear Segmento',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Segmentos', 'url': reverse('generador_actas:segmentos_dashboard')},
            {'title': 'Crear', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/segmentos/crear.html', context)


@login_required
def detalle_segmento(request, pk):
    """Vista detallada mejorada de un segmento con métricas y configuración"""
    try:
        segmento = get_object_or_404(SegmentoPlantilla.objects.select_related(
            'proveedor_ia', 'usuario_creacion'
        ), pk=pk)
        
        # Calcular métricas de rendimiento
        metricas = {
            'estado_salud': segmento.estado_salud,
            'esta_configurado': segmento.esta_configurado,
            'configuracion_ia_valida': segmento.configuracion_ia_valida,
            'porcentaje_exito': round(segmento.tasa_exito, 1),
            'tiempo_promedio': round(segmento.tiempo_promedio_procesamiento, 2),
            'total_procesados': segmento.total_usos,
            'total_errores': segmento.total_errores,
        }
        
        # Variables disponibles
        variables_disponibles = segmento.variables_disponibles
        
        # Plantillas que usan este segmento
        plantillas_usando = PlantillaActa.objects.filter(
            configuracionsegmento__segmento=segmento
        ).select_related().distinct()
        
        # Información de configuración
        config_info = {
            'tiene_contenido_estatico': segmento.tiene_contenido_estatico,
            'tiene_prompt_ia': segmento.tiene_prompt,
            'proveedor_configurado': segmento.proveedor_ia and segmento.proveedor_ia.esta_configurado if segmento.proveedor_ia else False,
            'estructura_definida': bool(segmento.estructura_json),
            'validaciones_activas': len(segmento.validaciones_salida) if segmento.validaciones_salida else 0,
            'parametros_entrada': len(segmento.parametros_entrada) if segmento.parametros_entrada else 0,
        }
        
        # Problemas detectados
        problemas = []
        if not segmento.esta_configurado:
            if segmento.es_estatico and not segmento.tiene_contenido_estatico:
                problemas.append("Segmento estático sin contenido definido")
            elif segmento.es_dinamico:
                if not segmento.tiene_prompt:
                    problemas.append("Segmento dinámico sin prompt de IA")
                if not segmento.proveedor_ia:
                    problemas.append("Segmento dinámico sin proveedor IA asignado")
                elif not segmento.proveedor_ia.esta_configurado:
                    problemas.append("Proveedor IA no está correctamente configurado")
            elif segmento.es_hibrido and not segmento.tiene_contenido_estatico:
                problemas.append("Segmento híbrido sin contenido estático base")
        
        if segmento.tasa_exito < 70 and segmento.total_usos > 0:
            problemas.append(f"Baja tasa de éxito ({segmento.tasa_exito:.1f}%)")
        
        if segmento.tiempo_promedio_procesamiento > 30:
            problemas.append(f"Tiempo de procesamiento elevado ({segmento.tiempo_promedio_procesamiento:.1f}s)")
        
        # Recomendaciones
        recomendaciones = []
        if segmento.total_usos == 0:
            recomendaciones.append("Considera probar este segmento para verificar su funcionamiento")
        
        if segmento.es_dinamico and not segmento.estructura_json:
            recomendaciones.append("Define una estructura JSON esperada para mejorar la consistencia")
        
        if segmento.es_dinamico and not segmento.validaciones_salida:
            recomendaciones.append("Agrega validaciones de salida para asegurar la calidad del resultado")
        
        if segmento.reutilizable and len(plantillas_usando) == 0:
            recomendaciones.append("Este segmento reutilizable no está siendo usado en ninguna plantilla")
        
        context = {
            'segmento': segmento,
            'object': segmento,  # Para compatibilidad con templates
            'metricas': metricas,
            'variables_disponibles': variables_disponibles,
            'plantillas_usando': plantillas_usando,
            'config_info': config_info,
            'problemas': problemas,
            'recomendaciones': recomendaciones,
            'page_title': f'Segmento: {segmento.nombre}',
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Segmentos', 'url': reverse('generador_actas:segmentos_dashboard')},
                {'title': segmento.nombre, 'url': ''}
            ]
        }
        
        return render(request, 'generador_actas/segmentos/detalle.html', context)
        
    except Exception as e:
        logger.error(f"Error en detalle_segmento {pk}: {str(e)}")
        messages.error(request, f"Error al cargar el detalle del segmento: {str(e)}")
        return redirect('generador_actas:lista_segmentos')


@login_required
def editar_segmento(request, pk):
    """Editar segmento existente con formulario mejorado"""
    from .forms import SegmentoPlantillaForm
    
    segmento = get_object_or_404(SegmentoPlantilla, pk=pk)
    
    if request.method == 'POST':
        form = SegmentoPlantillaForm(request.POST, instance=segmento)
        if form.is_valid():
            try:
                with transaction.atomic():
                    segmento = form.save()
                    messages.success(request, f"Segmento '{segmento.nombre}' actualizado exitosamente")
                    return redirect('generador_actas:detalle_segmento', pk=segmento.pk)
                    
            except Exception as e:
                logger.error(f"Error al actualizar segmento: {str(e)}")
                messages.error(request, f"Error al actualizar el segmento: {str(e)}")
    else:
        form = SegmentoPlantillaForm(instance=segmento)
    
    context = {
        'form': form,
        'segmento': segmento,
        'page_title': f'Editar: {segmento.nombre}',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Segmentos', 'url': reverse('generador_actas:segmentos_dashboard')},
            {'title': segmento.nombre, 'url': reverse('generador_actas:detalle_segmento', kwargs={'pk': segmento.pk})},
            {'title': 'Editar', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/segmentos/editar.html', context)


@login_required
def eliminar_segmento(request, pk):
    """Eliminar segmento (con confirmación)"""
    segmento = get_object_or_404(SegmentoPlantilla, pk=pk)
    
    if request.method == 'POST':
        try:
            nombre = segmento.nombre
            segmento.delete()
            messages.success(request, f"Segmento '{nombre}' eliminado exitosamente")
            return redirect('generador_actas:lista_segmentos')
            
        except Exception as e:
            logger.error(f"Error al eliminar segmento: {str(e)}")
            messages.error(request, f"Error al eliminar el segmento: {str(e)}")
            return redirect('generador_actas:detalle_segmento', pk=pk)
    
    context = {
        'segmento': segmento,
        'page_title': f'Eliminar: {segmento.nombre}',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Segmentos', 'url': reverse('generador_actas:segmentos_dashboard')},
            {'title': segmento.nombre, 'url': reverse('generador_actas:detalle_segmento', kwargs={'pk': segmento.pk})},
            {'title': 'Eliminar', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/segmentos/eliminar.html', context)


@login_required
def probar_segmento(request):
    """Interface para probar segmentos"""
    from .forms import PruebaSegmentoForm
    
    resultado = None
    
    if request.method == 'POST':
        form = PruebaSegmentoForm(request.POST)
        if form.is_valid():
            try:
                segmento = form.cleaned_data['segmento']
                datos_contexto = form.cleaned_data['datos_contexto']
                usar_celery = form.cleaned_data['usar_celery']
                incluir_metricas = form.cleaned_data['incluir_metricas']
                
                # Simular procesamiento del segmento
                import time
                tiempo_inicio = time.time()
                
                if segmento.es_dinamico:
                    # Para segmentos dinámicos, simular llamada a IA
                    json_completo = segmento.generar_json_completo(datos_contexto)
                    
                    if usar_celery:
                        # TODO: Implementar tarea Celery
                        resultado = {
                            'tipo': 'celery',
                            'mensaje': 'Tarea enviada a Celery para procesamiento asíncrono',
                            'task_id': 'simulated-task-id-123'
                        }
                    else:
                        # Procesamiento directo simulado
                        resultado = {
                            'tipo': 'directo',
                            'segmento': segmento.nombre,
                            'json_enviado': json_completo,
                            'respuesta_simulada': f"Contenido generado para {segmento.categoria}: Lorem ipsum content...",
                            'tiempo_procesamiento': round(time.time() - tiempo_inicio, 3)
                        }
                else:
                    # Para segmentos estáticos, usar las variables directamente
                    resultado = {
                        'tipo': 'estatico',
                        'segmento': segmento.nombre,
                        'variables_aplicadas': datos_contexto,
                        'contenido_final': f"Contenido estático con variables: {datos_contexto}",
                        'tiempo_procesamiento': round(time.time() - tiempo_inicio, 3)
                    }
                
                # Actualizar métricas si está habilitado
                if incluir_metricas and 'tiempo_procesamiento' in resultado:
                    segmento.actualizar_metricas_uso(
                        tiempo_procesamiento=resultado['tiempo_procesamiento'],
                        resultado_prueba=json.dumps(resultado, default=str)
                    )
                
                messages.success(request, "Prueba de segmento completada exitosamente")
                
            except Exception as e:
                logger.error(f"Error al probar segmento: {str(e)}")
                messages.error(request, f"Error al probar el segmento: {str(e)}")
                resultado = {
                    'tipo': 'error',
                    'error': str(e)
                }
    else:
        form = PruebaSegmentoForm()
    
    context = {
        'form': form,
        'resultado': resultado,
        'page_title': 'Probar Segmentos',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Segmentos', 'url': reverse('generador_actas:segmentos_dashboard')},
            {'title': 'Probar', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/segmentos/probar.html', context)


@require_http_methods(["POST"])
@csrf_exempt
@login_required
def api_probar_segmento(request):
    """API endpoint para probar segmentos vía AJAX"""
    try:
        data = json.loads(request.body)
        segmento_id = data.get('segmento_id')
        datos_contexto = data.get('datos_contexto', {})
        usar_celery = data.get('usar_celery', False)
        
        if not segmento_id:
            return JsonResponse({'error': 'ID de segmento requerido'}, status=400)
        
        segmento = SegmentoPlantilla.objects.get(pk=segmento_id, activo=True)
        
        # Procesamiento simulado
        import time
        tiempo_inicio = time.time()
        
        if segmento.es_dinamico:
            json_completo = segmento.generar_json_completo(datos_contexto)
            
            if usar_celery:
                # Usar tarea Celery real
                from .tasks import procesar_segmento_dinamico
                task = procesar_segmento_dinamico.apply_async(
                    args=[segmento.id, datos_contexto, {'usar_celery': True}]
                )
                resultado = {
                    'success': True,
                    'tipo': 'celery',
                    'task_id': task.id,
                    'mensaje': 'Procesamiento iniciado en segundo plano',
                    'status_url': f'/api/segmentos/task-status/{task.id}/'
                }
            else:
                resultado = {
                    'success': True,
                    'tipo': 'directo',
                    'contenido': f"Contenido dinámico generado para {segmento.nombre}",
                    'tiempo_procesamiento': round(time.time() - tiempo_inicio, 3),
                    'json_usado': json_completo
                }
        else:
            resultado = {
                'success': True,
                'tipo': 'estatico',
                'contenido': f"Contenido estático de {segmento.nombre}",
                'variables_aplicadas': datos_contexto,
                'tiempo_procesamiento': round(time.time() - tiempo_inicio, 3)
            }
        
        # Actualizar métricas
        if 'tiempo_procesamiento' in resultado:
            segmento.actualizar_metricas_uso(
                tiempo_procesamiento=resultado['tiempo_procesamiento'],
                resultado_prueba=json.dumps(resultado, default=str)
            )
        
        return JsonResponse(resultado)
        
    except SegmentoPlantilla.DoesNotExist:
        return JsonResponse({'error': 'Segmento no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en api_probar_segmento: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def asistente_variables(request):
    """Asistente para configurar variables de segmentos"""
    from .forms import VariablesSegmentoForm
    
    variables_json = None
    
    if request.method == 'POST':
        form = VariablesSegmentoForm(request.POST)
        if form.is_valid():
            variables_json = form.get_variables_json()
            messages.success(request, "Variables configuradas exitosamente")
    else:
        form = VariablesSegmentoForm()
    
    context = {
        'form': form,
        'variables_json': variables_json,
        'variables_comunes': SegmentoPlantilla.obtener_variables_comunes(),
        'page_title': 'Asistente de Variables',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Segmentos', 'url': reverse('generador_actas:segmentos_dashboard')},
            {'title': 'Asistente Variables', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/segmentos/asistente_variables.html', context)


# ============================================================================
# VISTAS PARA PLANTILLAS - MÓDULO COMPLETO DE EJECUCIÓN
# ============================================================================

from .models import EjecucionPlantilla, ResultadoSegmento, ActaBorrador
from .forms import (
    PlantillaBasicaForm, PlantillaSegmentosForm, PlantillaConfiguracionForm, 
    PlantillaEjecucionForm, SegmentoResultadoForm, ActaBorradorForm,
    EjecucionFiltroForm
)


class PlantillaListView(LoginRequiredMixin, ListView):
    """Vista de lista de plantillas con filtros y búsqueda"""
    model = PlantillaActa
    template_name = 'generador_actas/plantillas/lista.html'
    context_object_name = 'plantillas'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtra plantillas según parámetros de búsqueda"""
        queryset = PlantillaActa.objects.select_related('proveedor_ia_defecto', 'usuario_creacion')
        
        # Filtro por término de búsqueda
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(codigo__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Filtro por tipo de acta
        tipo_acta = self.request.GET.get('tipo_acta', '').strip()
        if tipo_acta:
            queryset = queryset.filter(tipo_acta=tipo_acta)
        
        # Filtro por estado (activa/inactiva)
        activa = self.request.GET.get('activa', '').strip()
        if activa == '1':
            queryset = queryset.filter(activa=True)
        elif activa == '0':
            queryset = queryset.filter(activa=False)
        
        return queryset.order_by('-fecha_actualizacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Plantillas de Actas',
            'search_query': self.request.GET.get('search', ''),
            'tipo_acta_filter': self.request.GET.get('tipo_acta', ''),
            'activa_filter': self.request.GET.get('activa', ''),
            'tipos_acta': PlantillaActa.TIPO_ACTA,
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Plantillas', 'url': ''}
            ]
        })
        return context


class PlantillaCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear nuevas plantillas (HTML puro, sin JavaScript)"""
    model = PlantillaActa
    form_class = PlantillaBasicaForm
    template_name = 'generador_actas/plantillas/crear_funcional.html'
    
    def form_valid(self, form):
        """Asocia el usuario de creación y procesa segmentos seleccionados"""
        form.instance.usuario_creacion = self.request.user
        response = super().form_valid(form)
        
        # Procesar segmentos seleccionados desde checkboxes (SIN JavaScript)
        segmentos_seleccionados = self.request.POST.getlist('segmentos_seleccionados')
        
        if segmentos_seleccionados:
            try:
                segmentos_data = []
                
                # Procesar cada segmento seleccionado
                for segmento_id in segmentos_seleccionados:
                    orden = self.request.POST.get(f'orden_{segmento_id}', 1)
                    obligatorio = self.request.POST.get(f'obligatorio_{segmento_id}') == 'on'
                    
                    segmentos_data.append({
                        'id': int(segmento_id),
                        'orden': int(orden) if orden else 1,
                        'obligatorio': obligatorio
                    })
                
                # Ordenar por orden especificado
                segmentos_data.sort(key=lambda x: x['orden'])
                
                # Procesar segmentos
                self._procesar_segmentos_plantilla(self.object, segmentos_data)
                
                messages.success(
                    self.request,
                    f'✅ Plantilla "{form.instance.nombre}" creada exitosamente con {len(segmentos_data)} segmentos configurados.'
                )
                
            except Exception as e:
                messages.warning(
                    self.request,
                    f'⚠️ Plantilla "{form.instance.nombre}" creada, pero hubo un error configurando los segmentos: {str(e)}'
                )
        else:
            messages.success(
                self.request,
                f'✅ Plantilla "{form.instance.nombre}" creada exitosamente. Puede agregar segmentos más tarde.'
            )
            
        return response
    
    def _procesar_segmentos_plantilla(self, plantilla, segmentos):
        """Procesa y guarda los segmentos de la plantilla"""
        from .models import ConfiguracionSegmento, SegmentoPlantilla
        
        # Eliminar configuraciones existentes
        plantilla.configuracionsegmento_set.all().delete()
        
        # Crear nuevas configuraciones
        for segmento_data in segmentos:
            try:
                segmento = SegmentoPlantilla.objects.get(id=segmento_data['id'])
                ConfiguracionSegmento.objects.create(
                    plantilla=plantilla,
                    segmento=segmento,
                    orden=segmento_data.get('orden', 1),
                    obligatorio=segmento_data.get('obligatorio', False),
                    prompt_personalizado=segmento_data.get('prompt_personalizado', ''),
                    parametros_override=segmento_data.get('parametros_override', {})
                )
            except SegmentoPlantilla.DoesNotExist:
                continue
    
    def get_success_url(self):
        """Redirige a configurar segmentos después de crear"""
        return reverse('generador_actas:configurar_segmentos_plantilla', kwargs={'plantilla_id': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Cargar segmentos disponibles de la BD
        segmentos_disponibles = SegmentoPlantilla.objects.filter(activo=True).order_by('categoria', 'nombre')
        
        context.update({
            'page_title': 'Nueva Plantilla',
            'segmentos_disponibles': segmentos_disponibles,
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'title': 'Nueva', 'url': ''}
            ]
        })
        return context


class PlantillaUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar plantillas existentes"""
    model = PlantillaActa
    form_class = PlantillaBasicaForm
    template_name = 'generador_actas/plantillas/crear_funcional.html'
    
    def get_success_url(self):
        return reverse('generador_actas:plantillas_lista')
    
    def form_valid(self, form):
        """Actualiza la plantilla y procesa segmentos"""
        import json
        
        response = super().form_valid(form)
        
        # Procesar datos de segmentos si se enviaron
        segmentos_data = self.request.POST.get('segmentos_data')
        if segmentos_data:
            try:
                segmentos = json.loads(segmentos_data)
                self._procesar_segmentos_plantilla(self.object, segmentos)
                messages.success(
                    self.request, 
                    f'Plantilla actualizada exitosamente con {len(segmentos)} segmentos configurados.'
                )
            except json.JSONDecodeError as e:
                messages.warning(
                    self.request,
                    f'Plantilla actualizada, pero hubo un error procesando los segmentos: {str(e)}'
                )
            except Exception as e:
                messages.warning(
                    self.request,
                    f'Plantilla actualizada, pero hubo un error configurando los segmentos: {str(e)}'
                )
        else:
            messages.success(self.request, 'Plantilla actualizada exitosamente')
            
        return response
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener segmentos actuales de la plantilla para precargar
        segmentos_actuales = []
        configuraciones = self.object.configuracionsegmento_set.select_related('segmento').order_by('orden')
        for config in configuraciones:
            segmentos_actuales.append({
                'id': config.segmento.id,
                'nombre': config.segmento.nombre,
                'tipo': config.segmento.tipo,
                'categoria': config.segmento.categoria,
                'descripcion': config.segmento.descripcion,
                'orden': config.orden,
                'obligatorio': getattr(config, 'obligatorio', False),
                'prompt_personalizado': config.prompt_personalizado or ''
            })
        
        context.update({
            'page_title': f'Editar Plantilla: {self.object.nombre}',
            'segmentos_disponibles': SegmentoPlantilla.objects.filter(activo=True).order_by('categoria', 'nombre'),
            'segmentos_actuales': json.dumps(segmentos_actuales),
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'title': 'Editar', 'url': ''}
            ]
        })
        return context


class PlantillaDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar plantillas con confirmación"""
    model = PlantillaActa
    template_name = 'generador_actas/plantillas/eliminar.html'
    success_url = reverse_lazy('generador_actas:plantillas_lista')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Análisis de impacto de eliminación
        ejecuciones_count = EjecucionPlantilla.objects.filter(plantilla=self.object).count()
        actas_generadas_count = self.object.actagenerada_set.count()
        
        context.update({
            'page_title': f'Eliminar Plantilla: {self.object.nombre}',
            'ejecuciones_count': ejecuciones_count,
            'actas_generadas_count': actas_generadas_count,
            'puede_eliminar': ejecuciones_count == 0 and actas_generadas_count == 0,
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'title': 'Eliminar', 'url': ''}
            ]
        })
        return context
    
    def delete(self, request, *args, **kwargs):
        """Previene eliminación si hay ejecuciones/actas asociadas"""
        self.object = self.get_object()
        
        # Verificar si se puede eliminar
        ejecuciones_count = EjecucionPlantilla.objects.filter(plantilla=self.object).count()
        actas_count = self.object.actagenerada_set.count()
        
        if ejecuciones_count > 0 or actas_count > 0:
            messages.error(
                request,
                f'No se puede eliminar la plantilla "{self.object.nombre}" porque tiene '
                f'{ejecuciones_count} ejecuciones y {actas_count} actas asociadas. '
                'Considere desactivarla en su lugar.'
            )
            return redirect('generador_actas:plantillas_lista')
        
        messages.success(request, f'Plantilla "{self.object.nombre}" eliminada exitosamente')
        return super().delete(request, *args, **kwargs)


@login_required
def configurar_segmentos_plantilla_old(request, pk):
    """Vista para configurar segmentos con drag & drop"""
    plantilla = get_object_or_404(PlantillaActa, pk=pk)
    
    if request.method == 'POST':
        form = PlantillaSegmentosForm(request.POST, plantilla=plantilla)
        
        if form.is_valid():
            segmentos_data = form.cleaned_data['segmentos_seleccionados']
            
            # Eliminar configuraciones existentes
            ConfiguracionSegmento.objects.filter(plantilla=plantilla).delete()
            
            # Crear nuevas configuraciones
            for segmento_config in segmentos_data:
                segmento = SegmentoPlantilla.objects.get(id=segmento_config['id'])
                ConfiguracionSegmento.objects.create(
                    plantilla=plantilla,
                    segmento=segmento,
                    orden=segmento_config['orden'],
                    obligatorio=segmento_config.get('obligatorio', False),
                    variables_personalizadas=segmento_config.get('variables_personalizadas', {})
                )
            
            messages.success(request, 'Configuración de segmentos actualizada exitosamente')
            return redirect('generador_actas:plantillas_lista')
    
    else:
        form = PlantillaSegmentosForm(plantilla=plantilla)
    
    # Obtener todos los segmentos disponibles para el drag & drop
    segmentos_disponibles = SegmentoPlantilla.objects.all().order_by('categoria', 'nombre')
    
    context = {
        'plantilla': plantilla,
        'form': form,
        'segmentos_disponibles': segmentos_disponibles,
        'page_title': f'Configurar Segmentos: {plantilla.nombre}',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
            {'title': 'Configurar Segmentos', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/plantillas/configurar_segmentos.html', context)


@login_required
def plantillas_dashboard(request):
    """Dashboard específico de plantillas con métricas"""
    
    # Estadísticas generales
    total_plantillas = PlantillaActa.objects.count()
    plantillas_activas = PlantillaActa.objects.filter(activa=True).count()
    total_ejecuciones = EjecucionPlantilla.objects.count()
    ejecuciones_mes = EjecucionPlantilla.objects.filter(
        tiempo_inicio__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Plantillas más usadas
    plantillas_populares = PlantillaActa.objects.annotate(
        total_ejecuciones=Count('ejecuciones')
    ).order_by('-total_ejecuciones')[:5]
    
    # Ejecuciones recientes
    ejecuciones_recientes = EjecucionPlantilla.objects.select_related(
        'plantilla', 'usuario', 'proveedor_ia_global'
    ).order_by('-tiempo_inicio')[:10]
    
    # Estadísticas por estado
    estados_stats = EjecucionPlantilla.objects.values('estado').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'page_title': 'Dashboard de Plantillas',
        'total_plantillas': total_plantillas,
        'plantillas_activas': plantillas_activas,
        'total_ejecuciones': total_ejecuciones,
        'ejecuciones_mes': ejecuciones_mes,
        'plantillas_populares': plantillas_populares,
        'ejecuciones_recientes': ejecuciones_recientes,
        'estados_stats': estados_stats,
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Dashboard Plantillas', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/plantillas/dashboard.html', context)


class EjecucionPlantillaCreateView(LoginRequiredMixin, CreateView):
    """Vista para iniciar ejecución de plantilla"""
    model = EjecucionPlantilla
    form_class = PlantillaEjecucionForm
    template_name = 'generador_actas/plantillas/ejecutar.html'
    
    def get_form_kwargs(self):
        """Pasa la plantilla al formulario"""
        kwargs = super().get_form_kwargs()
        plantilla_pk = self.kwargs.get('plantilla_pk')
        if plantilla_pk:
            kwargs['plantilla'] = get_object_or_404(PlantillaActa, pk=plantilla_pk)
        return kwargs
    
    def form_valid(self, form):
        """Configura la ejecución y la inicia"""
        plantilla_pk = self.kwargs.get('plantilla_pk')
        plantilla = get_object_or_404(PlantillaActa, pk=plantilla_pk)
        
        form.instance.plantilla = plantilla
        form.instance.usuario = self.request.user
        
        # Contar segmentos para el progreso
        total_segmentos = plantilla.segmentos.count()
        form.instance.progreso_total = total_segmentos
        
        response = super().form_valid(form)
        
        # TODO: Iniciar tarea Celery aquí
        messages.success(
            self.request,
            f'Ejecución iniciada: "{form.instance.nombre}". '
            'Se procesarán los segmentos en segundo plano.'
        )
        
        return response
    
    def get_success_url(self):
        return reverse('generador_actas:ver_ejecucion', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plantilla_pk = self.kwargs.get('plantilla_pk')
        plantilla = get_object_or_404(PlantillaActa, pk=plantilla_pk)
        
        context.update({
            'plantilla': plantilla,
            'page_title': f'Ejecutar Plantilla: {plantilla.nombre}',
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'title': 'Ejecutar', 'url': ''}
            ]
        })
        return context


class EjecucionDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver detalles de ejecución y editar resultados"""
    model = EjecucionPlantilla
    template_name = 'generador_actas/plantillas/ver_ejecucion.html'
    context_object_name = 'ejecucion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener resultados de segmentos
        resultados = ResultadoSegmento.objects.filter(
            ejecucion=self.object
        ).select_related('segmento').order_by('orden_procesamiento')
        
        context.update({
            'resultados': resultados,
            'page_title': f'Ejecución: {self.object.nombre}',
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Plantillas', 'url': reverse('generador_actas:plantillas_lista')},
                {'title': 'Ver Ejecución', 'url': ''}
            ]
        })
        return context


class EjecucionListView(LoginRequiredMixin, ListView):
    """Vista de lista de todas las ejecuciones con filtros"""
    model = EjecucionPlantilla
    template_name = 'generador_actas/plantillas/ejecuciones_lista.html'
    context_object_name = 'ejecuciones'
    paginate_by = 20
    
    def get_queryset(self):
        """Filtra ejecuciones según parámetros"""
        queryset = EjecucionPlantilla.objects.select_related(
            'plantilla', 'usuario', 'proveedor_ia_global'
        )
        
        # Aplicar filtros si existen
        form = EjecucionFiltroForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data.get('estado'):
                queryset = queryset.filter(estado=form.cleaned_data['estado'])
            
            if form.cleaned_data.get('plantilla'):
                queryset = queryset.filter(plantilla=form.cleaned_data['plantilla'])
            
            if form.cleaned_data.get('usuario'):
                queryset = queryset.filter(usuario=form.cleaned_data['usuario'])
            
            if form.cleaned_data.get('fecha_desde'):
                queryset = queryset.filter(tiempo_inicio__gte=form.cleaned_data['fecha_desde'])
            
            if form.cleaned_data.get('fecha_hasta'):
                fecha_hasta = form.cleaned_data['fecha_hasta']
                # Incluir todo el día
                fecha_hasta = fecha_hasta.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(tiempo_inicio__lte=fecha_hasta)
        
        return queryset.order_by('-tiempo_inicio')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'filtro_form': EjecucionFiltroForm(self.request.GET),
            'page_title': 'Todas las Ejecuciones',
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Ejecuciones', 'url': ''}
            ]
        })
        return context


@login_required
def editar_resultado_segmento(request, ejecucion_pk, resultado_pk):
    """Vista para editar resultado individual de segmento"""
    ejecucion = get_object_or_404(EjecucionPlantilla, pk=ejecucion_pk)
    resultado = get_object_or_404(ResultadoSegmento, pk=resultado_pk, ejecucion=ejecucion)
    
    if request.method == 'POST':
        form = SegmentoResultadoForm(request.POST, instance=resultado)
        if form.is_valid():
            # Marcar como editado
            resultado.marcar_como_editado(
                form.cleaned_data['resultado_editado'], 
                request.user
            )
            
            messages.success(request, 'Resultado del segmento actualizado exitosamente')
            return redirect('generador_actas:ver_ejecucion', pk=ejecucion.pk)
    else:
        form = SegmentoResultadoForm(instance=resultado)
    
    context = {
        'ejecucion': ejecucion,
        'resultado': resultado,
        'form': form,
        'page_title': f'Editar: {resultado.segmento.nombre}',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Ejecuciones', 'url': reverse('generador_actas:ejecuciones_lista')},
            {'title': ejecucion.nombre, 'url': reverse('generador_actas:ver_ejecucion', kwargs={'pk': ejecucion.pk})},
            {'title': 'Editar Segmento', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/plantillas/editar_resultado.html', context)


@login_required
def generar_acta_final(request, ejecucion_pk):
    """Vista para generar acta final a partir de resultados editados"""
    ejecucion = get_object_or_404(EjecucionPlantilla, pk=ejecucion_pk)
    
    # Verificar que todos los segmentos estén completados
    resultados_pendientes = ejecucion.resultados.exclude(
        estado__in=['completado', 'editado']
    ).count()
    
    if resultados_pendientes > 0:
        messages.error(
            request,
            f'No se puede generar el acta final. '
            f'Hay {resultados_pendientes} segmentos aún pendientes de procesamiento.'
        )
        return redirect('generador_actas:ver_ejecucion', pk=ejecucion.pk)
    
    if request.method == 'POST':
        # TODO: Iniciar tarea Celery para unificación final
        messages.info(
            request,
            'Generando acta final. Este proceso puede tomar unos minutos...'
        )
        return redirect('generador_actas:ver_ejecucion', pk=ejecucion.pk)
    
    # Vista de confirmación
    context = {
        'ejecucion': ejecucion,
        'total_segmentos': ejecucion.resultados.count(),
        'page_title': 'Generar Acta Final',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Ejecuciones', 'url': reverse('generador_actas:ejecuciones_lista')},
            {'title': ejecucion.nombre, 'url': reverse('generador_actas:ver_ejecucion', kwargs={'pk': ejecucion.pk})},
            {'title': 'Generar Acta Final', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/plantillas/generar_acta_final.html', context)


# ================== NUEVAS VISTAS FASE 2: DRAG & DROP + CELERY ==================

@login_required
def configurar_segmentos_plantilla(request, plantilla_id):
    """
    Vista para configurar segmentos de una plantilla con drag & drop
    """
    try:
        plantilla = get_object_or_404(PlantillaActa, pk=plantilla_id)
        
        if request.method == 'POST':
            # Procesar formulario de configuración
            return _procesar_configuracion_segmentos(request, plantilla)
        
        # GET - Mostrar interfaz de configuración
        configuraciones_existentes = ConfiguracionSegmento.objects.filter(
            plantilla=plantilla
        ).select_related('segmento', 'segmento__proveedor_ia').order_by('orden')
        
        # Obtener todos los segmentos disponibles
        segmentos_disponibles = SegmentoPlantilla.objects.filter(
            activo=True
        ).select_related('proveedor_ia').order_by('categoria', 'nombre')
        
        # Crear diccionarios por categoría
        segmentos_por_categoria = {}
        for segmento in segmentos_disponibles:
            categoria = segmento.get_categoria_display()
            if categoria not in segmentos_por_categoria:
                segmentos_por_categoria[categoria] = []
            segmentos_por_categoria[categoria].append(segmento)
        
        # IDs de segmentos ya configurados
        segmentos_configurados_ids = list(configuraciones_existentes.values_list('segmento_id', flat=True))
        
        context = {
            'plantilla': plantilla,
            'configuraciones': configuraciones_existentes,
            'segmentos_disponibles': segmentos_disponibles,
            'segmentos_por_categoria': segmentos_por_categoria,
            'segmentos_configurados_ids': segmentos_configurados_ids,
            'total_configuraciones': configuraciones_existentes.count(),
            'page_title': f'Configurar Segmentos: {plantilla.nombre}',
            'breadcrumbs': [
                {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
                {'title': 'Plantillas', 'url': reverse('generador_actas:lista_plantillas')},
                {'title': 'Configurar Segmentos', 'url': ''}
            ]
        }
        
        return render(request, 'generador_actas/plantillas/configurar_segmentos.html', context)
        
    except Exception as e:
        logger.error(f"Error en configurar_segmentos_plantilla: {e}")
        messages.error(request, f'Error: {str(e)}')
        return redirect('generador_actas:dashboard')


def _procesar_configuracion_segmentos(request, plantilla):
    """Procesa la configuración de segmentos vía POST"""
    try:
        accion = request.POST.get('accion')
        
        if accion == 'agregar_segmento':
            segmento_id = request.POST.get('segmento_id')
            if segmento_id:
                segmento = get_object_or_404(SegmentoPlantilla, pk=segmento_id)
                
                # Verificar que no esté ya configurado
                if not ConfiguracionSegmento.objects.filter(plantilla=plantilla, segmento=segmento).exists():
                    # Obtener el próximo orden
                    ultimo_orden = ConfiguracionSegmento.objects.filter(
                        plantilla=plantilla
                    ).aggregate(models.Max('orden'))['orden__max'] or 0
                    
                    ConfiguracionSegmento.objects.create(
                        plantilla=plantilla,
                        segmento=segmento,
                        orden=ultimo_orden + 1,
                        obligatorio=False,
                        prompt_personalizado=""
                    )
                    
                    messages.success(request, f'Segmento "{segmento.nombre}" agregado exitosamente')
                else:
                    messages.warning(request, f'El segmento "{segmento.nombre}" ya está configurado')
        
        elif accion == 'remover_segmento':
            configuracion_id = request.POST.get('configuracion_id')
            if configuracion_id:
                config = get_object_or_404(ConfiguracionSegmento, pk=configuracion_id, plantilla=plantilla)
                segmento_nombre = config.segmento.nombre
                config.delete()
                
                # Reordenar los segmentos restantes
                configuraciones_restantes = ConfiguracionSegmento.objects.filter(plantilla=plantilla).order_by('orden')
                for i, config in enumerate(configuraciones_restantes, 1):
                    config.orden = i
                    config.save()
                
                messages.success(request, f'Segmento "{segmento_nombre}" removido exitosamente')
        
        elif accion == 'actualizar_configuracion':
            configuracion_id = request.POST.get('configuracion_id')
            if configuracion_id:
                config = get_object_or_404(ConfiguracionSegmento, pk=configuracion_id, plantilla=plantilla)
                config.obligatorio = request.POST.get('obligatorio') == 'on'
                config.prompt_personalizado = request.POST.get('prompt_personalizado', '')
                config.save()
                
                messages.success(request, f'Configuración de "{config.segmento.nombre}" actualizada')
        
        return redirect('generador_actas:configurar_segmentos_plantilla', plantilla_id=plantilla.pk)
        
    except Exception as e:
        logger.error(f"Error procesando configuración de segmentos: {e}")
        messages.error(request, f'Error procesando configuración: {str(e)}')
        return redirect('generador_actas:configurar_segmentos_plantilla', plantilla_id=plantilla.pk)


@login_required
@require_http_methods(["POST"])
def api_actualizar_orden_segmentos(request, plantilla_id):
    """
    API endpoint para actualizar orden de segmentos via AJAX
    """
    plantilla = get_object_or_404(PlantillaActa, id=plantilla_id)
    
    # Verificar permisos
    if not request.user.has_perm('generador_actas.change_plantillaacta'):
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    try:
        data = json.loads(request.body)
        segmentos_orden = data.get('segmentos_orden', [])
        
        # Validar datos
        if not isinstance(segmentos_orden, list):
            return JsonResponse({
                'success': False, 
                'error': 'Datos inválidos'
            }, status=400)
        
        # Actualizar en transacción
        with transaction.atomic():
            updated_count = 0
            for item in segmentos_orden:
                segmento_id = item.get('segmento_id')
                nuevo_orden = item.get('orden')
                
                if not segmento_id or not isinstance(nuevo_orden, int):
                    continue
                
                try:
                    config_segmento = ConfiguracionSegmento.objects.get(
                        id=segmento_id,
                        plantilla=plantilla
                    )
                    config_segmento.orden = nuevo_orden
                    config_segmento.save()
                    updated_count += 1
                except ConfiguracionSegmento.DoesNotExist:
                    continue
        
        logger.info(f"Usuario {request.user} actualizó orden de {updated_count} segmentos en plantilla {plantilla.pk}")
        
        return JsonResponse({
            'success': True,
            'message': f'Orden actualizado para {updated_count} segmentos',
            'updated_count': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Error en api_actualizar_orden_segmentos: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def api_obtener_configuracion_segmento(request, config_id):
    """
    API endpoint para obtener datos de configuración de un segmento
    """
    try:
        config = get_object_or_404(ConfiguracionSegmento, pk=config_id)
        
        # Verificar permisos
        if not request.user.has_perm('generador_actas.view_configuracionsegmento'):
            return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
        
        return JsonResponse({
            'success': True,
            'configuracion': {
                'id': config.pk,
                'segmento_nombre': config.segmento.nombre,
                'obligatorio': config.obligatorio,
                'incluir_en_resumen': getattr(config, 'incluir_en_resumen', False),
                'orden': config.orden,
                'configuracion_adicional': getattr(config, 'configuracion_adicional', {}),
                'segmento_tipo': config.segmento.tipo,
                'segmento_descripcion': config.segmento.descripcion
            }
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo configuración de segmento {config_id}: {e}")
        return JsonResponse({
            'success': False, 
            'error': f'Error al obtener configuración: {str(e)}'
        }, status=500)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@login_required
def vista_previa_plantilla(request, plantilla_id):
    """
    Vista previa de la estructura de plantilla en formato JSON
    """
    plantilla = get_object_or_404(PlantillaActa, id=plantilla_id)
    
    # Obtener estructura completa
    configuraciones = ConfiguracionSegmento.objects.filter(
        plantilla=plantilla
    ).select_related('segmento', 'segmento__proveedor_ia').order_by('orden')
    
    # Construir JSON de estructura
    estructura = {
        'plantilla': {
            'id': plantilla.pk,
            'nombre': plantilla.nombre,
            'descripcion': plantilla.descripcion,
            'fecha_creacion': plantilla.fecha_creacion.isoformat() if plantilla.fecha_creacion else None,
            'total_segmentos': configuraciones.count()
        },
        'segmentos': []
    }
    
    for config in configuraciones:
        segmento = config.segmento
        segmento_data = {
            'id': config.pk,
            'segmento_id': segmento.pk,
            'nombre': segmento.nombre,
            'tipo': segmento.tipo,
            'categoria': segmento.categoria,
            'orden': config.orden,
            'obligatorio': config.obligatorio,
            'prompt_efectivo': config.prompt_efectivo,
            'configuracion': {
                'activo': segmento.activo,
                'proveedor_ia': segmento.proveedor_ia.nombre if segmento.proveedor_ia else None
            }
        }
        estructura['segmentos'].append(segmento_data)
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse(estructura, json_dumps_params={'indent': 2})
    
    # Vista HTML con JSON formateado
    context = {
        'plantilla': plantilla,
        'estructura_json': json.dumps(estructura, indent=2, ensure_ascii=False),
        'page_title': f'Vista Previa: {plantilla.nombre}',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': reverse('generador_actas:dashboard')},
            {'title': 'Plantillas', 'url': reverse('generador_actas:lista_plantillas')},
            {'title': plantilla.nombre, 'url': reverse('generador_actas:ver_plantilla', kwargs={'pk': plantilla.pk})},
            {'title': 'Vista Previa', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/plantillas/vista_previa.html', context)


# ================== VISTA SIMPLE PARA CREAR PLANTILLAS ==================

@login_required
def crear_plantilla_simple(request):
    """Vista simple para crear plantillas sin problemas de contexto"""
    
    if request.method == 'POST':
        form = PlantillaBasicaForm(request.POST)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.usuario_creacion = request.user
            plantilla.save()
            
            # Procesar segmentos seleccionados
            segmentos_seleccionados = request.POST.getlist('segmentos_seleccionados')
            segmentos_creados = 0
            
            for segmento_id in segmentos_seleccionados:
                try:
                    segmento = SegmentoPlantilla.objects.get(id=segmento_id)
                    orden = request.POST.get(f'orden_{segmento_id}', 1)
                    obligatorio = request.POST.get(f'obligatorio_{segmento_id}') == 'on'
                    
                    ConfiguracionSegmento.objects.create(
                        plantilla=plantilla,
                        segmento=segmento,
                        orden=int(orden),
                        obligatorio=obligatorio
                    )
                    segmentos_creados += 1
                except Exception as e:
                    print(f'Error procesando segmento {segmento_id}: {e}')
            
            messages.success(
                request, 
                f'✅ Plantilla "{plantilla.nombre}" creada con {segmentos_creados} segmentos.'
            )
            return redirect('generador_actas:plantillas_lista')
    else:
        form = PlantillaBasicaForm()
    
    # Obtener segmentos disponibles
    segmentos_disponibles = SegmentoPlantilla.objects.filter(activo=True).order_by('categoria', 'nombre')
    
    context = {
        'form': form,
        'segmentos_disponibles': segmentos_disponibles,
        'page_title': 'Nueva Plantilla',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': '/generador-actas/'},
            {'title': 'Plantillas', 'url': '/generador-actas/plantillas/'},
            {'title': 'Nueva', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/plantillas/crear_funcional.html', context)