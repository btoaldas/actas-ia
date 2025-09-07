from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count
import json

from .models_proxy import (
    SystemPermissionProxy as SystemPermission, 
    UserProfileProxy as UserProfile, 
    UserProfileAssignmentProxy as UserProfileAssignment,
    PermissionDiscoveryProxy as PermissionDiscovery,
    user_has_permission_proxy as user_has_permission,
    get_user_permissions_proxy as get_user_permissions,
    PermissionType
)
from .forms_new_permissions import (
    SystemPermissionForm,
    UserProfileForm, 
    UserProfileAssignmentForm,
    BulkPermissionAssignmentForm,
    PermissionFilterForm,
    QuickProfileCreationForm,
    UserManagementForm,
    PermissionCreationForm,
    ProfilePermissionAssignmentForm
)
from .permissions import require_permission, PermissionMixin


# ==============================================
# VISTAS PRINCIPALES DEL SISTEMA DE PERMISOS
# ==============================================

@login_required
@require_permission('menu.permissions_system')
def permissions_dashboard(request):
    """Dashboard principal del sistema de permisos"""
    
    # Estadísticas generales
    stats = {
        'total_permissions': SystemPermission.objects.filter(is_active=True).count(),
        'total_profiles': UserProfile.objects.filter(is_active=True).count(),
        'total_assignments': UserProfileAssignment.objects.count(),
        'total_users_with_profiles': User.objects.filter(
            userprofileassignmentproxy_set__isnull=False
        ).distinct().count(),
    }
    
    # Permisos por tipo
    permissions_by_type = {}
    for ptype in PermissionType.values:
        count = SystemPermission.objects.filter(
            permission_type=ptype,
            is_active=True
        ).count()
        permissions_by_type[PermissionType(ptype).label] = count
    
    # Perfiles más usados
    popular_profiles = UserProfile.objects.annotate(
        usage_count=Count('userprofileassignmentproxy_set')
    ).filter(is_active=True).order_by('-usage_count')[:5]
    
    # Usuarios sin perfiles
    users_without_profiles = User.objects.filter(
        is_active=True,
        userprofileassignmentproxy_set__isnull=True
    ).exclude(is_superuser=True)[:10]
    
    context = {
        'stats': stats,
        'permissions_by_type': permissions_by_type,
        'popular_profiles': popular_profiles,
        'users_without_profiles': users_without_profiles,
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/dashboard.html', context)


# ==============================================
# GESTIÓN DE PERMISOS DEL SISTEMA
# ==============================================

@login_required
@require_permission('view.system_permissions_list')
def system_permissions_list(request):
    """Lista de permisos del sistema"""
    
    # Filtros
    filter_form = PermissionFilterForm(request.GET)
    permissions = SystemPermission.objects.all().order_by('permission_type', 'app_name', 'name')
    
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('permission_type'):
            permissions = permissions.filter(
                permission_type=filter_form.cleaned_data['permission_type']
            )
        
        if filter_form.cleaned_data.get('app_name'):
            permissions = permissions.filter(
                app_name__icontains=filter_form.cleaned_data['app_name']
            )
        
        if filter_form.cleaned_data.get('search'):
            search = filter_form.cleaned_data['search']
            permissions = permissions.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )
        
        if filter_form.cleaned_data.get('is_active'):
            is_active = filter_form.cleaned_data['is_active'] == 'true'
            permissions = permissions.filter(is_active=is_active)
    
    # Paginación
    paginator = Paginator(permissions, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': permissions.count(),
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Permisos del Sistema', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/system_permissions_list.html', context)


@login_required
@require_permission('view.system_permissions_create')
def system_permission_create(request):
    """Crear nuevo permiso del sistema"""
    
    if request.method == 'POST':
        form = SystemPermissionForm(request.POST)
        if form.is_valid():
            permission = form.save(commit=False)
            permission.auto_generated = False  # Permiso creado manualmente
            permission.save()
            
            messages.success(request, f'Permiso "{permission.name}" creado correctamente.')
            return redirect('config_system:new_permissions:system_list')
    else:
        form = SystemPermissionForm()
    
    context = {
        'form': form,
        'title': 'Crear Permiso del Sistema',
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Permisos del Sistema', 'url': '/config-system/new-permissions/system/'},
            {'name': 'Crear', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/system_permission_form.html', context)


@login_required
@require_permission('view.system_permissions_edit')
def system_permission_edit(request, permission_id):
    """Editar permiso del sistema"""
    
    permission = get_object_or_404(SystemPermission, id=permission_id)
    
    if request.method == 'POST':
        form = SystemPermissionForm(request.POST, instance=permission)
        if form.is_valid():
            form.save()
            messages.success(request, f'Permiso "{permission.name}" actualizado correctamente.')
            return redirect('config_system:new_permissions:system_list')
    else:
        form = SystemPermissionForm(instance=permission)
    
    context = {
        'form': form,
        'permission': permission,
        'title': f'Editar Permiso: {permission.name}',
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Permisos del Sistema', 'url': '/config-system/new-permissions/system/'},
            {'name': 'Editar', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/system_permission_form.html', context)


# ==============================================
# GESTIÓN DE PERFILES DE USUARIO
# ==============================================

@login_required
@require_permission('view.user_profiles_list')
def user_profiles_list(request):
    """Lista de perfiles de usuario"""
    
    profiles = UserProfile.objects.annotate(
        users_count=Count('userprofileassignmentproxy_set'),
        permissions_count=Count('permissions', filter=Q(permissions__is_active=True))
    ).order_by('-is_active', 'name')
    
    # Paginación
    paginator = Paginator(profiles, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Perfiles de Usuario', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/user_profiles_list.html', context)


@login_required
@require_permission('view.user_profiles_create')
def user_profile_create(request):
    """Crear nuevo perfil de usuario"""
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            profile = form.save()
            messages.success(request, f'Perfil "{profile.name}" creado correctamente.')
            return redirect('config_system:new_permissions:profiles_list')
    else:
        form = UserProfileForm()
    
    context = {
        'form': form,
        'title': 'Crear Perfil de Usuario',
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Perfiles', 'url': '/config-system/new-permissions/profiles/'},
            {'name': 'Crear', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/user_profile_form.html', context)


@login_required
@require_permission('view.user_profiles_edit')
def user_profile_edit(request, profile_id):
    """Editar perfil de usuario"""
    
    profile = get_object_or_404(UserProfile, id=profile_id)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Perfil "{profile.name}" actualizado correctamente.')
            return redirect('config_system:new_permissions:profiles_list')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'title': f'Editar Perfil: {profile.name}',
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Perfiles', 'url': '/config-system/new-permissions/profiles/'},
            {'name': 'Editar', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/user_profile_form.html', context)


# ==============================================
# ASIGNACIÓN DE PERFILES A USUARIOS
# ==============================================

@login_required
@require_permission('view.user_assignments_list')
def user_assignments_list(request):
    """Lista de asignaciones de perfiles a usuarios"""
    
    assignments = UserProfileAssignment.objects.select_related(
        'user', 'profile', 'assigned_by'
    ).order_by('-assigned_at')
    
    # Filtro por usuario
    search_user = request.GET.get('user')
    if search_user:
        assignments = assignments.filter(
            Q(user__username__icontains=search_user) |
            Q(user__first_name__icontains=search_user) |
            Q(user__last_name__icontains=search_user)
        )
    
    # Paginación
    paginator = Paginator(assignments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_user': search_user,
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Asignaciones', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/user_assignments_list.html', context)


@login_required
@require_permission('view.user_assignments_create')
def user_assignment_create(request):
    """Asignar perfil a usuario"""
    
    if request.method == 'POST':
        form = UserProfileAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            
            try:
                assignment.save()
                messages.success(
                    request, 
                    f'Perfil "{assignment.profile.name}" asignado a {assignment.user.get_full_name() or assignment.user.username}.'
                )
                return redirect('config_system:new_permissions:assignments_list')
            except Exception as e:
                messages.error(request, f'Error al asignar perfil: {str(e)}')
    else:
        form = UserProfileAssignmentForm()
    
    context = {
        'form': form,
        'title': 'Asignar Perfil a Usuario',
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Asignaciones', 'url': '/config-system/new-permissions/assignments/'},
            {'name': 'Crear', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/user_assignment_form.html', context)


# ==============================================
# UTILIDADES Y ACCIONES MASIVAS
# ==============================================

@login_required
@require_permission('view.permissions_discover')
def discover_permissions(request):
    """Descubrir y crear permisos automáticamente"""
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            with transaction.atomic():
                if action == 'discover':
                    # Solo descubrir nuevos permisos
                    discovered = PermissionDiscovery.discover_all_permissions()
                    
                elif action == 'recreate':
                    # Eliminar auto-generados y recrear
                    deleted_count = SystemPermission.objects.filter(auto_generated=True).delete()[0]
                    discovered = PermissionDiscovery.discover_all_permissions()
                    
                    messages.warning(request, f'Se eliminaron {deleted_count} permisos auto-generados.')
                
                # Contar nuevos permisos creados
                total_created = sum(len(perms) for perms in discovered.values())
                
                if total_created > 0:
                    messages.success(request, f'Se crearon {total_created} nuevos permisos.')
                else:
                    messages.info(request, 'No se encontraron nuevos permisos para crear.')
                
                return redirect('config_system:new_permissions:discover')
                
        except Exception as e:
            messages.error(request, f'Error al descubrir permisos: {str(e)}')
    
    # Estadísticas actuales
    stats = {
        'total_permissions': SystemPermission.objects.count(),
        'auto_generated': SystemPermission.objects.filter(auto_generated=True).count(),
        'manual': SystemPermission.objects.filter(auto_generated=False).count(),
        'by_type': {}
    }
    
    for ptype in PermissionType.values:
        stats['by_type'][PermissionType(ptype).label] = SystemPermission.objects.filter(
            permission_type=ptype
        ).count()
    
    context = {
        'stats': stats,
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Descubrir Permisos', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/discover_permissions.html', context)


@login_required
@require_permission('view.permissions_bulk_assign')
def bulk_assignment(request):
    """Asignación masiva de perfiles"""
    
    if request.method == 'POST':
        form = BulkPermissionAssignmentForm(request.POST)
        if form.is_valid():
            users = form.cleaned_data['users']
            profile = form.cleaned_data['profile']
            action = form.cleaned_data['action']
            
            success_count = 0
            error_count = 0
            
            for user in users:
                try:
                    if action == 'assign':
                        assignment, created = UserProfileAssignment.objects.get_or_create(
                            user=user,
                            profile=profile,
                            defaults={'assigned_by': request.user}
                        )
                        if created:
                            success_count += 1
                    
                    elif action == 'remove':
                        deleted = UserProfileAssignment.objects.filter(
                            user=user, 
                            profile=profile
                        ).delete()[0]
                        if deleted:
                            success_count += 1
                
                except Exception:
                    error_count += 1
            
            if success_count > 0:
                action_text = 'asignado' if action == 'assign' else 'removido'
                messages.success(
                    request, 
                    f'Perfil {action_text} a {success_count} usuarios correctamente.'
                )
            
            if error_count > 0:
                messages.warning(request, f'{error_count} asignaciones fallaron.')
            
            return redirect('config_system:new_permissions:bulk_assign')
    else:
        form = BulkPermissionAssignmentForm()
    
    context = {
        'form': form,
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Permisos', 'url': '/config-system/new-permissions/'},
            {'name': 'Asignación Masiva', 'url': None},
        ]
    }
    
    return render(request, 'config_system/new_permissions/bulk_assignment.html', context)


# ==============================================
# APIS Y VISTAS JSON
# ==============================================

@login_required
@require_http_methods(["GET"])
def user_permissions_api(request, user_id):
    """API para obtener permisos de un usuario específico"""
    
    user = get_object_or_404(User, id=user_id)
    permissions = get_user_permissions(user)
    
    data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name(),
            'is_superuser': user.is_superuser,
        },
        'permissions': [
            {
                'id': perm.id,
                'code': perm.code,
                'name': perm.name,
                'type': perm.permission_type,
                'app': perm.app_name,
            }
            for perm in permissions
        ]
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def check_permission_api(request):
    """API para verificar si un usuario tiene un permiso específico"""
    
    data = json.loads(request.body)
    user_id = data.get('user_id')
    permission_code = data.get('permission_code')
    
    user = get_object_or_404(User, id=user_id)
    has_permission = user_has_permission(user, permission_code)
    
    return JsonResponse({
        'has_permission': has_permission,
        'user_id': user_id,
        'permission_code': permission_code,
    })


# ==============================================
# VISTAS DE GESTIÓN AVANZADA DE USUARIOS
# ==============================================

@login_required
@require_permission('menu.user_management')
def user_management_list(request):
    """Lista de usuarios con gestión de perfiles"""
    
    # Búsqueda y filtros
    search_query = request.GET.get('search', '')
    profile_filter = request.GET.get('profile', '')
    status_filter = request.GET.get('status', '')
    
    users = User.objects.select_related().prefetch_related(
        'userprofileassignmentproxy_set__profile'
    )
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if profile_filter:
        users = users.filter(userprofileassignmentproxy_set__profile__id=profile_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Paginación
    paginator = Paginator(users.distinct(), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Datos adicionales
    profiles = UserProfile.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'profiles': profiles,
        'search_query': search_query,
        'profile_filter': profile_filter,
        'status_filter': status_filter,
        'total_users': users.distinct().count(),
    }
    
    return render(request, 'config_system/new_permissions/user_management_list.html', context)


@login_required
@require_permission('menu.user_management')
def user_profile_assignment(request, user_id):
    """Asignar/modificar perfiles de un usuario"""
    
    user = get_object_or_404(User, id=user_id)
    current_assignments = UserProfileAssignment.objects.filter(user=user)
    
    if request.method == 'POST':
        form = UserManagementForm(request.POST, user=user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Eliminar asignaciones actuales
                    current_assignments.delete()
                    
                    # Crear nuevas asignaciones
                    profiles = form.cleaned_data['profiles']
                    for profile in profiles:
                        UserProfileAssignment.objects.create(
                            user=user,
                            profile=profile,
                            assigned_by=request.user
                        )
                    
                    messages.success(
                        request, 
                        f'Perfiles actualizados correctamente para {user.get_full_name() or user.username}'
                    )
                    return redirect('config_system:new_permissions:user_management_list')
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar perfiles: {str(e)}')
    else:
        initial_profiles = [assignment.profile for assignment in current_assignments]
        form = UserManagementForm(user=user, initial={'profiles': initial_profiles})
    
    context = {
        'form': form,
        'user': user,
        'current_assignments': current_assignments,
        'all_profiles': UserProfile.objects.filter(is_active=True),
    }
    
    return render(request, 'config_system/new_permissions/user_profile_assignment.html', context)


# ==============================================
# VISTAS DE CREACIÓN Y GESTIÓN DE PERMISOS
# ==============================================

@login_required
@require_permission('menu.permission_creation')
def permission_creation(request):
    """Crear nuevos permisos personalizados"""
    
    if request.method == 'POST':
        form = PermissionCreationForm(request.POST)
        if form.is_valid():
            try:
                permission = form.save()
                messages.success(
                    request,
                    f'Permiso "{permission.name}" creado correctamente con código: {permission.code}'
                )
                return redirect('config_system:new_permissions:system_list')
            except Exception as e:
                messages.error(request, f'Error al crear permiso: {str(e)}')
    else:
        form = PermissionCreationForm()
    
    # Obtener permisos existentes por tipo para referencia
    permissions_by_type = {}
    for ptype in PermissionType.choices:
        permissions_by_type[ptype[0]] = SystemPermission.objects.filter(
            permission_type=ptype[0]
        )[:5]  # Solo primeros 5 como ejemplo
    
    context = {
        'form': form,
        'permissions_by_type': permissions_by_type,
        'permission_types': PermissionType.choices,
    }
    
    return render(request, 'config_system/new_permissions/permission_creation.html', context)


@login_required
@require_permission('menu.permission_creation') 
def discover_routes_permissions(request):
    """Descubrir y crear permisos automáticamente desde rutas"""
    
    if request.method == 'POST':
        try:
            # Usar el comando de descubrimiento existente
            from django.core.management import call_command
            from io import StringIO
            
            out = StringIO()
            call_command('discover_permissions', stdout=out)
            output = out.getvalue()
            
            messages.success(
                request,
                f'Descubrimiento de permisos completado: {output}'
            )
            
        except Exception as e:
            messages.error(request, f'Error en descubrimiento: {str(e)}')
        
        return redirect('config_system:new_permissions:discover_routes_permissions')
    
    # Mostrar información sobre el proceso
    context = {
        'apps_info': [
            {'name': 'config_system', 'description': 'Sistema de configuración'},
            {'name': 'pages', 'description': 'Páginas del sistema'},
            {'name': 'users', 'description': 'Gestión de usuarios'},
            {'name': 'tasks', 'description': 'Tareas del sistema'},
            {'name': 'charts', 'description': 'Gráficos y reportes'},
        ]
    }
    
    return render(request, 'config_system/new_permissions/discover_routes.html', context)


# ==============================================
# VISTAS DE GESTIÓN AVANZADA DE PERFILES
# ==============================================

@login_required
@require_permission('menu.profile_management')
def profile_management_advanced(request):
    """Gestión avanzada de perfiles con asignación de permisos"""
    
    profiles = UserProfile.objects.filter(is_active=True).annotate(
        user_count=Count('userprofileassignmentproxy_set'),
        permission_count=Count('permissions')
    )
    
    if request.method == 'POST':
        form = QuickProfileCreationForm(request.POST)
        if form.is_valid():
            try:
                profile = form.save(commit=False)
                profile.created_by = request.user
                profile.save()
                
                messages.success(
                    request,
                    f'Perfil "{profile.name}" creado correctamente'
                )
                return redirect('config_system:new_permissions:profile_permission_assignment', profile_id=profile.id)
                
            except Exception as e:
                messages.error(request, f'Error al crear perfil: {str(e)}')
    else:
        form = QuickProfileCreationForm()
    
    context = {
        'profiles': profiles,
        'form': form,
        'total_profiles': profiles.count(),
    }
    
    return render(request, 'config_system/new_permissions/profile_management_advanced.html', context)


@login_required
@require_permission('menu.profile_management')
def profile_permission_assignment(request, profile_id):
    """Asignar permisos específicos a un perfil"""
    
    profile = get_object_or_404(UserProfile, id=profile_id)
    current_permissions = profile.permissions.all()
    
    if request.method == 'POST':
        form = ProfilePermissionAssignmentForm(request.POST, profile=profile)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Actualizar permisos del perfil
                    profile.permissions.clear()
                    permissions = form.cleaned_data['permissions']
                    profile.permissions.set(permissions)
                    
                    messages.success(
                        request,
                        f'Permisos actualizados para el perfil "{profile.name}"'
                    )
                    return redirect('config_system:new_permissions:profile_management_advanced')
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar permisos: {str(e)}')
    else:
        form = ProfilePermissionAssignmentForm(
            profile=profile, 
            initial={'permissions': current_permissions}
        )
    
    # Organizar permisos por tipo para mejor visualización
    permissions_by_type = {}
    for ptype in PermissionType.choices:
        permissions_by_type[ptype[1]] = SystemPermission.objects.filter(
            permission_type=ptype[0],
            is_active=True
        ).order_by('name')
    
    context = {
        'form': form,
        'profile': profile,
        'current_permissions': current_permissions,
        'permissions_by_type': permissions_by_type,
        'users_with_profile': UserProfileAssignment.objects.filter(profile=profile).count(),
    }
    
    return render(request, 'config_system/new_permissions/profile_permission_assignment.html', context)


@login_required
@require_permission('menu.profile_management')
def profile_delete(request, profile_id):
    """Eliminar un perfil (soft delete)"""
    
    profile = get_object_or_404(UserProfile, id=profile_id)
    
    if request.method == 'POST':
        try:
            # Verificar si tiene usuarios asignados
            assigned_users = UserProfileAssignment.objects.filter(profile=profile).count()
            
            if assigned_users > 0:
                messages.warning(
                    request,
                    f'No se puede eliminar el perfil "{profile.name}" porque tiene {assigned_users} usuario(s) asignado(s)'
                )
            else:
                profile.is_active = False
                profile.save()
                messages.success(
                    request,
                    f'Perfil "{profile.name}" eliminado correctamente'
                )
        except Exception as e:
            messages.error(request, f'Error al eliminar perfil: {str(e)}')
    
    return redirect('config_system:new_permissions:profile_management_advanced')
