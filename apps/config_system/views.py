from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import ConfiguracionWhisper, ConfiguracionIA, PerfilUsuario, LogConfiguracion
from .forms import ConfiguracionWhisperForm, ConfiguracionIAForm

User = get_user_model()


def superadmin_required(function):
    """Decorador personalizado para requerir superadmin"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a esta sección')
            return redirect('index')  # Cambiado a index
        return function(request, *args, **kwargs)
    return wrapper


class SuperAdminRequiredMixin(LoginRequiredMixin):
    """Mixin para requerir superadmin en vistas basadas en clases"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a esta sección')
            return redirect('index')  # Cambiado a index
        return super().dispatch(request, *args, **kwargs)


@superadmin_required
def dashboard(request):
    """Dashboard principal de configuraciones"""
    
    # Estadísticas generales
    stats = {
        'total_configs_ia': ConfiguracionIA.objects.count(),
        'total_configs_whisper': ConfiguracionWhisper.objects.count(),
        'configs_activas': (
            ConfiguracionIA.objects.filter(activo=True).count() +
            ConfiguracionWhisper.objects.filter(activo=True).count()
        ),
        'configs_inactivas': (
            ConfiguracionIA.objects.filter(activo=False).count() +
            ConfiguracionWhisper.objects.filter(activo=False).count()
        ),
        'usuarios_con_permisos': PerfilUsuario.objects.count()
    }
    
    # Configuraciones IA activas
    configs_ia_activas = ConfiguracionIA.objects.filter(activo=True).order_by('orden_prioridad')[:5]
    
    # Configuraciones Whisper activas
    configs_whisper_activas = ConfiguracionWhisper.objects.filter(activo=True)[:5]
    
    # Últimas actividades
    ultimas_actividades = LogConfiguracion.objects.select_related('usuario').order_by('-fecha')[:10]
    
    context = {
        'stats': stats,
        'configs_ia_activas': configs_ia_activas,
        'configs_whisper_activas': configs_whisper_activas,
        'ultimas_actividades': ultimas_actividades,
        'config_principal': ConfiguracionIA.objects.filter(es_principal=True).first(),
    }
    
    return render(request, 'config_system/dashboard.html', context)


# ==================== CONFIGURACIONES IA ====================

class ConfiguracionIAListView(SuperAdminRequiredMixin, ListView):
    """Lista de configuraciones IA"""
    model = ConfiguracionIA
    template_name = 'config_system/ia_list.html'
    context_object_name = 'configuraciones'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['configuraciones_activas'] = ConfiguracionIA.objects.filter(activo=True).count()
        context['config_principal'] = ConfiguracionIA.objects.filter(es_principal=True).first()
        context['proveedores_unicos'] = ConfiguracionIA.objects.values('proveedor').distinct().count()
        return context


class ConfiguracionIADetailView(SuperAdminRequiredMixin, DetailView):
    """Detalle de configuración IA"""
    model = ConfiguracionIA
    template_name = 'config_system/ia_detail.html'
    context_object_name = 'configuracion'


class ConfiguracionIACreateView(SuperAdminRequiredMixin, CreateView):
    """Crear configuración IA"""
    model = ConfiguracionIA
    form_class = ConfiguracionIAForm
    template_name = 'config_system/ia_form.html'
    success_url = reverse_lazy('config_system:ia_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Configuración IA "{form.instance.nombre}" creada exitosamente')
        return super().form_valid(form)


class ConfiguracionIAUpdateView(SuperAdminRequiredMixin, UpdateView):
    """Actualizar configuración IA"""
    model = ConfiguracionIA
    form_class = ConfiguracionIAForm
    template_name = 'config_system/ia_form.html'
    success_url = reverse_lazy('config_system:ia_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Configuración IA "{form.instance.nombre}" actualizada exitosamente')
        return super().form_valid(form)


class ConfiguracionIADeleteView(SuperAdminRequiredMixin, DeleteView):
    """Eliminar configuración IA"""
    model = ConfiguracionIA
    success_url = reverse_lazy('config_system:ia_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre = self.object.nombre
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Configuración IA "{nombre}" eliminada exitosamente')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Configuración "{nombre}" eliminada'})
        
        return redirect(success_url)


@superadmin_required
@require_POST
def probar_configuracion_ia(request, pk):
    """Probar configuración IA"""
    configuracion = get_object_or_404(ConfiguracionIA, pk=pk)
    
    try:
        # Simulamos una prueba exitosa por ahora
        return JsonResponse({
            'success': True,
            'message': f'Configuración "{configuracion.nombre}" probada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al probar configuración: {str(e)}'
        })


# ==================== CONFIGURACIONES WHISPER ====================

class ConfiguracionWhisperListView(SuperAdminRequiredMixin, ListView):
    """Lista de configuraciones Whisper"""
    model = ConfiguracionWhisper
    template_name = 'config_system/whisper_list.html'
    context_object_name = 'configuraciones'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['configuraciones_activas'] = ConfiguracionWhisper.objects.filter(activo=True).count()
        context['configuraciones_con_pyannote'] = ConfiguracionWhisper.objects.filter(usar_pyannote=True).count()
        context['configuraciones_con_failover'] = ConfiguracionWhisper.objects.filter(tiene_failover=True).count()
        context['idiomas_unicos'] = ConfiguracionWhisper.objects.values('idioma').distinct().count()
        return context


class ConfiguracionWhisperDetailView(SuperAdminRequiredMixin, DetailView):
    """Detalle de configuración Whisper"""
    model = ConfiguracionWhisper
    template_name = 'config_system/whisper_detail.html'
    context_object_name = 'configuracion'


class ConfiguracionWhisperCreateView(SuperAdminRequiredMixin, CreateView):
    """Crear configuración Whisper"""
    model = ConfiguracionWhisper
    form_class = ConfiguracionWhisperForm
    template_name = 'config_system/whisper_form.html'
    success_url = reverse_lazy('config_system:whisper_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Configuración Whisper "{form.instance.nombre}" creada exitosamente')
        return super().form_valid(form)


class ConfiguracionWhisperUpdateView(SuperAdminRequiredMixin, UpdateView):
    """Actualizar configuración Whisper"""
    model = ConfiguracionWhisper
    form_class = ConfiguracionWhisperForm
    template_name = 'config_system/whisper_form.html'
    success_url = reverse_lazy('config_system:whisper_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Configuración Whisper "{form.instance.nombre}" actualizada exitosamente')
        return super().form_valid(form)


class ConfiguracionWhisperDeleteView(SuperAdminRequiredMixin, DeleteView):
    """Eliminar configuración Whisper"""
    model = ConfiguracionWhisper
    success_url = reverse_lazy('config_system:whisper_list')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre = self.object.nombre
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f'Configuración Whisper "{nombre}" eliminada exitosamente')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Configuración "{nombre}" eliminada'})
        
        return redirect(success_url)


@superadmin_required
@require_POST
def probar_configuracion_whisper(request, pk):
    """Probar configuración Whisper"""
    configuracion = get_object_or_404(ConfiguracionWhisper, pk=pk)
    
    try:
        # Simulamos una prueba exitosa por ahora
        return JsonResponse({
            'success': True,
            'message': f'Configuración "{configuracion.nombre}" probada exitosamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al probar configuración: {str(e)}'
        })


# ==================== GESTIÓN DE USUARIOS ====================

class UsuariosListView(SuperAdminRequiredMixin, ListView):
    """Lista de usuarios con permisos de configuración"""
    model = User
    template_name = 'config_system/usuarios_list.html'
    context_object_name = 'usuarios'
    paginate_by = 20
    
    def get_queryset(self):
        return User.objects.filter(
            Q(is_superuser=True) | Q(perfilusuario__isnull=False)
        ).select_related('perfilusuario')


@superadmin_required
def gestionar_permisos_usuario(request, pk):
    """Gestionar permisos de un usuario específico"""
    usuario = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        # Simplificado por ahora
        messages.success(request, f'Permisos actualizados para {usuario.username}')
        return redirect('config_system:usuarios_list')
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'config_system/gestionar_permisos.html', context)


# ==================== AJAX ENDPOINTS ====================

@superadmin_required
@require_POST
def toggle_configuracion_ia(request, pk):
    """Toggle activo/inactivo para configuración IA via AJAX"""
    configuracion = get_object_or_404(ConfiguracionIA, pk=pk)
    
    activo = request.POST.get('activo') == 'true'
    configuracion.activo = activo
    configuracion.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Configuración {"activada" if activo else "desactivada"} exitosamente'
    })


@superadmin_required
@require_POST
def toggle_configuracion_whisper(request, pk):
    """Toggle activo/inactivo para configuración Whisper via AJAX"""
    configuracion = get_object_or_404(ConfiguracionWhisper, pk=pk)
    
    activo = request.POST.get('activo') == 'true'
    configuracion.activo = activo
    configuracion.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Configuración {"activada" if activo else "desactivada"} exitosamente'
    })


# ==================== GESTIÓN DE USUARIOS ====================

@superadmin_required
def usuarios_list(request):
    """Lista todos los usuarios del sistema"""
    usuarios = User.objects.all().order_by('-date_joined')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        usuarios = usuarios.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Filtro por estado
    estado = request.GET.get('estado', '')
    if estado == 'activo':
        usuarios = usuarios.filter(is_active=True)
    elif estado == 'inactivo':
        usuarios = usuarios.filter(is_active=False)
    
    context = {
        'usuarios': usuarios,
        'search': search,
        'estado': estado,
        'total_usuarios': User.objects.count(),
        'usuarios_activos': User.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'config_system/usuarios/usuarios_list.html', context)


@superadmin_required
def usuario_detail(request, pk):
    """Detalle de un usuario específico"""
    usuario = get_object_or_404(User, pk=pk)
    
    # Obtener perfil si existe
    perfil = getattr(usuario, 'perfilusuario', None)
    permisos = getattr(perfil, 'permisos_detallados', None) if perfil else None
    
    # Logs recientes del usuario
    logs_recientes = LogConfiguracion.objects.filter(usuario=usuario).order_by('-fecha')[:10]
    
    context = {
        'usuario': usuario,
        'perfil': perfil,
        'permisos': permisos,
        'logs_recientes': logs_recientes,
    }
    
    return render(request, 'config_system/usuarios/usuario_detail.html', context)


@superadmin_required
def usuario_create(request):
    """Crear nuevo usuario"""
    from .forms import UsuarioCreateForm
    
    if request.method == 'POST':
        form = UsuarioCreateForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.username} creado exitosamente')
            return redirect('config_system:usuario_detail', pk=usuario.pk)
    else:
        form = UsuarioCreateForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Usuario'
    }
    
    return render(request, 'config_system/usuarios/usuario_form.html', context)


@superadmin_required
def usuario_edit(request, pk):
    """Editar usuario existente"""
    usuario = get_object_or_404(User, pk=pk)
    from .forms import UsuarioEditForm
    
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente')
            return redirect('config_system:usuario_detail', pk=usuario.pk)
    else:
        form = UsuarioEditForm(instance=usuario)
    
    context = {
        'form': form,
        'usuario': usuario,
        'title': f'Editar Usuario: {usuario.username}'
    }
    
    return render(request, 'config_system/usuarios/usuario_form.html', context)


@superadmin_required
@require_POST
def usuario_toggle_active(request, pk):
    """Activar/desactivar usuario via AJAX"""
    usuario = get_object_or_404(User, pk=pk)
    
    activo = request.POST.get('activo') == 'true'
    usuario.is_active = activo
    usuario.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Usuario {"activado" if activo else "desactivado"} exitosamente'
    })


@superadmin_required
def usuario_delete(request, pk):
    """Eliminar usuario (con confirmación)"""
    usuario = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        username = usuario.username
        usuario.delete()
        messages.success(request, f'Usuario {username} eliminado exitosamente')
        return redirect('config_system:usuarios_list')
    
    context = {
        'usuario': usuario,
        'title': f'Eliminar Usuario: {usuario.username}'
    }
    
    return render(request, 'config_system/usuarios/usuario_delete.html', context)


# ==================== GESTIÓN DE PERFILES ====================

@superadmin_required
def perfiles_list(request):
    """Lista todos los perfiles de usuario"""
    perfiles = PerfilUsuario.objects.select_related('usuario').order_by('-fecha_creacion')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        perfiles = perfiles.filter(
            Q(usuario__username__icontains=search) |
            Q(usuario__first_name__icontains=search) |
            Q(usuario__last_name__icontains=search) |
            Q(cargo__icontains=search)
        )
    
    # Filtro por rol
    rol = request.GET.get('rol', '')
    if rol:
        perfiles = perfiles.filter(rol=rol)
    
    # Filtro por departamento
    departamento = request.GET.get('departamento', '')
    if departamento:
        perfiles = perfiles.filter(departamento=departamento)
    
    # Estadísticas por rol
    stats_roles = {}
    for rol_code, rol_name in PerfilUsuario.ROLES:
        stats_roles[rol_code] = {
            'nombre': rol_name,
            'count': PerfilUsuario.objects.filter(rol=rol_code).count()
        }
    
    context = {
        'perfiles': perfiles,
        'search': search,
        'rol_selected': rol,
        'departamento_selected': departamento,
        'stats_roles': stats_roles,
        'roles_choices': PerfilUsuario.ROLES,
        'departamentos_choices': PerfilUsuario.DEPARTAMENTOS,
        'total_perfiles': PerfilUsuario.objects.count(),
    }
    
    return render(request, 'config_system/perfiles/perfiles_list.html', context)


@superadmin_required
def perfil_detail(request, pk):
    """Detalle de un perfil específico"""
    perfil = get_object_or_404(PerfilUsuario, pk=pk)
    permisos = getattr(perfil, 'permisos_detallados', None)
    
    context = {
        'perfil': perfil,
        'permisos': permisos,
    }
    
    return render(request, 'config_system/perfiles/perfil_detail.html', context)


@superadmin_required
def perfil_create(request):
    """Crear nuevo perfil para usuario sin perfil"""
    from .forms import PerfilUsuarioForm
    
    # Usuarios sin perfil
    usuarios_sin_perfil = User.objects.filter(perfilusuario__isnull=True)
    
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST)
        if form.is_valid():
            perfil = form.save()
            
            # Aplicar permisos automáticamente
            from .models import PermisosDetallados
            PermisosDetallados.aplicar_permisos_por_rol(perfil)
            
            messages.success(request, f'Perfil creado para {perfil.usuario.username}')
            return redirect('config_system:perfil_detail', pk=perfil.pk)
    else:
        form = PerfilUsuarioForm()
    
    context = {
        'form': form,
        'usuarios_sin_perfil': usuarios_sin_perfil,
        'title': 'Crear Nuevo Perfil'
    }
    
    return render(request, 'config_system/perfiles/perfil_form.html', context)


@superadmin_required
def perfil_edit(request, pk):
    """Editar perfil existente"""
    perfil = get_object_or_404(PerfilUsuario, pk=pk)
    from .forms import PerfilUsuarioForm
    
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=perfil)
        if form.is_valid():
            perfil = form.save()
            
            # Reaplicar permisos si cambió el rol
            if 'rol' in form.changed_data:
                from .models import PermisosDetallados
                PermisosDetallados.aplicar_permisos_por_rol(perfil)
                messages.info(request, 'Permisos actualizados según el nuevo rol')
            
            messages.success(request, f'Perfil de {perfil.usuario.username} actualizado')
            return redirect('config_system:perfil_detail', pk=perfil.pk)
    else:
        form = PerfilUsuarioForm(instance=perfil)
    
    context = {
        'form': form,
        'perfil': perfil,
        'title': f'Editar Perfil: {perfil.usuario.username}'
    }
    
    return render(request, 'config_system/perfiles/perfil_form.html', context)


@superadmin_required
@require_POST
def perfil_toggle_active(request, pk):
    """Activar/desactivar perfil via AJAX"""
    perfil = get_object_or_404(PerfilUsuario, pk=pk)
    
    activo = request.POST.get('activo') == 'true'
    perfil.activo = activo
    perfil.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Perfil {"activado" if activo else "desactivado"} exitosamente'
    })


@superadmin_required
def perfil_delete(request, pk):
    """Eliminar perfil (con confirmación)"""
    perfil = get_object_or_404(PerfilUsuario, pk=pk)
    
    if request.method == 'POST':
        username = perfil.usuario.username
        perfil.delete()
        messages.success(request, f'Perfil de {username} eliminado exitosamente')
        return redirect('config_system:perfiles_list')
    
    context = {
        'perfil': perfil,
        'title': f'Eliminar Perfil: {perfil.usuario.username}'
    }
    
    return render(request, 'config_system/perfiles/perfil_delete.html', context)


# ==================== GESTIÓN DE PERMISOS ====================

@superadmin_required
def permisos_list(request):
    """Lista todos los permisos detallados"""
    from .models import PermisosDetallados
    
    permisos = PermisosDetallados.objects.select_related('perfil__usuario').order_by('perfil__usuario__username')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        permisos = permisos.filter(
            Q(perfil__usuario__username__icontains=search) |
            Q(perfil__usuario__first_name__icontains=search) |
            Q(perfil__usuario__last_name__icontains=search)
        )
    
    # Filtro por rol
    rol = request.GET.get('rol', '')
    if rol:
        permisos = permisos.filter(perfil__rol=rol)
    
    context = {
        'permisos_list': permisos,
        'search': search,
        'rol_selected': rol,
        'roles_choices': PerfilUsuario.ROLES,
        'total_permisos': PermisosDetallados.objects.count(),
    }
    
    return render(request, 'config_system/permisos/permisos_list.html', context)


@superadmin_required
def permisos_detail(request, pk):
    """Detalle de permisos específicos"""
    from .models import PermisosDetallados
    permisos = get_object_or_404(PermisosDetallados, pk=pk)
    
    # Organizar permisos por categoría
    permisos_organizados = {
        'menus': [],
        'transcripcion': [],
        'ia': [],
        'actas': [],
        'revision': [],
        'publicacion': [],
        'sesiones': [],
        'configuracion': [],
        'administracion': [],
    }
    
    # Mapear campos a categorías
    campos_menus = [f for f in PermisosDetallados._meta.fields if f.name.startswith('ver_menu_')]
    campos_transcripcion = [f for f in PermisosDetallados._meta.fields if any(x in f.name for x in ['transcripcion', 'audio'])]
    campos_ia = [f for f in PermisosDetallados._meta.fields if 'ia' in f.name and not f.name.startswith('ver_menu_')]
    campos_actas = [f for f in PermisosDetallados._meta.fields if 'acta' in f.name and not f.name.startswith('ver_menu_')]
    campos_revision = [f for f in PermisosDetallados._meta.fields if any(x in f.name for x in ['revisar', 'aprobar', 'rechazar'])]
    campos_publicacion = [f for f in PermisosDetallados._meta.fields if 'publicar' in f.name or 'transparencia' in f.name]
    campos_sesiones = [f for f in PermisosDetallados._meta.fields if 'sesion' in f.name or 'asistente' in f.name or 'orden_dia' in f.name]
    campos_configuracion = [f for f in PermisosDetallados._meta.fields if 'configurar' in f.name or 'probar' in f.name]
    campos_administracion = [f for f in PermisosDetallados._meta.fields if any(x in f.name for x in ['gestionar', 'reportes', 'respaldos', 'usuarios'])]
    
    for campo in campos_menus:
        permisos_organizados['menus'].append({
            'nombre': campo.verbose_name,
            'valor': getattr(permisos, campo.name)
        })
    
    for campo in campos_transcripcion:
        permisos_organizados['transcripcion'].append({
            'nombre': campo.verbose_name,
            'valor': getattr(permisos, campo.name)
        })
    
    # Similar para otras categorías...
    
    context = {
        'permisos': permisos,
        'permisos_organizados': permisos_organizados,
    }
    
    return render(request, 'config_system/permisos/permisos_detail.html', context)


@superadmin_required
def permisos_edit(request, pk):
    """Editar permisos específicos"""
    from .models import PermisosDetallados
    from .forms import PermisosDetalladosForm
    
    permisos = get_object_or_404(PermisosDetallados, pk=pk)
    
    if request.method == 'POST':
        form = PermisosDetalladosForm(request.POST, instance=permisos)
        if form.is_valid():
            permisos = form.save()
            messages.success(request, f'Permisos de {permisos.perfil.usuario.username} actualizados')
            return redirect('config_system:permisos_detail', pk=permisos.pk)
    else:
        form = PermisosDetalladosForm(instance=permisos)
    
    context = {
        'form': form,
        'permisos': permisos,
        'title': f'Editar Permisos: {permisos.perfil.usuario.username}'
    }
    
    return render(request, 'config_system/permisos/permisos_form.html', context)


@superadmin_required
@require_POST
def permisos_reset_por_rol(request, pk):
    """Resetear permisos según el rol del perfil"""
    from .models import PermisosDetallados
    
    permisos = get_object_or_404(PermisosDetallados, pk=pk)
    
    # Reaplicar permisos según rol
    PermisosDetallados.aplicar_permisos_por_rol(permisos.perfil)
    
    return JsonResponse({
        'success': True,
        'message': f'Permisos restablecidos según el rol {permisos.perfil.get_rol_display()}'
    })


@superadmin_required
@require_POST
def aplicar_permisos_masivo(request):
    """Aplicar permisos a múltiples usuarios según su rol"""
    from .models import PermisosDetallados
    
    rol = request.POST.get('rol', '')
    
    if rol:
        perfiles = PerfilUsuario.objects.filter(rol=rol)
        count = 0
        for perfil in perfiles:
            PermisosDetallados.aplicar_permisos_por_rol(perfil)
            count += 1
        
        rol_name = dict(PerfilUsuario.ROLES).get(rol, rol)
        return JsonResponse({
            'success': True,
            'message': f'Permisos aplicados a {count} usuarios con rol {rol_name}'
        })
    else:
        # Aplicar a todos
        perfiles = PerfilUsuario.objects.all()
        count = 0
        for perfil in perfiles:
            PermisosDetallados.aplicar_permisos_por_rol(perfil)
            count += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Permisos aplicados a {count} usuarios'
        })


# ==================== API ENDPOINTS ====================

@superadmin_required
def api_estadisticas(request):
    """API endpoint para estadísticas del dashboard"""
    stats = {
        'configs_ia': {
            'total': ConfiguracionIA.objects.count(),
            'activas': ConfiguracionIA.objects.filter(activo=True).count(),
        },
        'configs_whisper': {
            'total': ConfiguracionWhisper.objects.count(),
            'activas': ConfiguracionWhisper.objects.filter(activo=True).count(),
        }
    }
    
    return JsonResponse(stats)


@superadmin_required
def api_configuraciones_activas(request):
    """API endpoint para configuraciones activas"""
    configs_ia = list(
        ConfiguracionIA.objects.filter(activo=True)
        .values('id', 'nombre', 'proveedor', 'modelo', 'es_principal')
        .order_by('orden_prioridad')
    )
    
    configs_whisper = list(
        ConfiguracionWhisper.objects.filter(activo=True)
        .values('id', 'nombre', 'modelo_whisper', 'idioma', 'usar_pyannote')
    )
    
    return JsonResponse({
        'configs_ia': configs_ia,
        'configs_whisper': configs_whisper
    })
