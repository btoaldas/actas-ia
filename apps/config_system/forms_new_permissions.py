from django import forms
from django.contrib.auth.models import User
from .models_proxy import (
    SystemPermissionProxy as SystemPermission, 
    UserProfileProxy as UserProfile, 
    UserProfileAssignmentProxy as UserProfileAssignment,
    PermissionType
)


class SystemPermissionForm(forms.ModelForm):
    """Formulario para crear/editar permisos del sistema"""
    
    class Meta:
        model = SystemPermission
        fields = [
            'name', 'code', 'permission_type', 'url_pattern', 
            'view_name', 'app_name', 'description', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del permiso'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'menu.actas, view.actas_list, etc.'
            }),
            'permission_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'url_pattern': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/actas/, actas:list, etc.'
            }),
            'view_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'actas_list, actas_detail, etc.'
            }),
            'app_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'actas, users, config_system, etc.'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del permiso'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class UserProfileForm(forms.ModelForm):
    """Formulario para crear/editar perfiles de usuario"""
    
    permissions = forms.ModelMultipleChoiceField(
        queryset=SystemPermission.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        help_text="Selecciona los permisos que incluirá este perfil"
    )
    
    class Meta:
        model = UserProfile
        fields = ['name', 'description', 'permissions', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del perfil'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del perfil'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizar permisos por tipo para mejor visualización
        permissions_by_type = {}
        for permission in SystemPermission.objects.filter(is_active=True).order_by('permission_type', 'name'):
            ptype = permission.get_permission_type_display()
            if ptype not in permissions_by_type:
                permissions_by_type[ptype] = []
            permissions_by_type[ptype].append(permission)
        
        self.permissions_by_type = permissions_by_type


class UserProfileAssignmentForm(forms.ModelForm):
    """Formulario para asignar perfiles a usuarios"""
    
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        }),
        help_text="Usuario al que se asignará el perfil"
    )
    
    profile = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control select2'
        }),
        help_text="Perfil que se asignará al usuario"
    )
    
    class Meta:
        model = UserProfileAssignment
        fields = ['user', 'profile']


class BulkPermissionAssignmentForm(forms.Form):
    """Formulario para asignar permisos en lotes"""
    
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        help_text="Usuarios a los que se asignará el perfil"
    )
    
    profile = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        help_text="Perfil que se asignará a los usuarios seleccionados"
    )
    
    action = forms.ChoiceField(
        choices=[
            ('assign', 'Asignar perfil'),
            ('remove', 'Remover perfil'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='assign'
    )


class PermissionFilterForm(forms.Form):
    """Formulario para filtrar permisos"""
    
    permission_type = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + PermissionType.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    app_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por aplicación'
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar en nombre o código'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Solo activos'),
            ('false', 'Solo inactivos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class QuickProfileCreationForm(forms.Form):
    """Formulario rápido para crear perfiles comunes"""
    
    PROFILE_TEMPLATES = [
        ('admin', 'Administrador (Todos los permisos)'),
        ('viewer', 'Solo Lectura (Solo visualización)'),
        ('editor', 'Editor (Lectura + Edición)'),
        ('custom', 'Personalizado'),
    ]
    
    profile_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del perfil'
        })
    )
    
    profile_type = forms.ChoiceField(
        choices=PROFILE_TEMPLATES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='custom'
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Descripción del perfil'
        })
    )
    
    def create_profile(self):
        """Crea el perfil basado en la plantilla seleccionada"""
        cleaned_data = self.cleaned_data
        
        profile = UserProfile.objects.create(
            name=cleaned_data['profile_name'],
            description=cleaned_data.get('description', ''),
            is_active=True
        )
        
        profile_type = cleaned_data['profile_type']
        
        if profile_type == 'admin':
            # Asignar todos los permisos
            all_permissions = SystemPermission.objects.filter(is_active=True)
            profile.permissions.set(all_permissions)
            
        elif profile_type == 'viewer':
            # Solo permisos de visualización
            view_permissions = SystemPermission.objects.filter(
                is_active=True,
                permission_type=PermissionType.VIEW
            )
            profile.permissions.set(view_permissions)
            
        elif profile_type == 'editor':
            # Permisos de visualización + algunos de edición
            permissions = SystemPermission.objects.filter(
                is_active=True,
                permission_type__in=[PermissionType.VIEW, PermissionType.MENU]
            )
            profile.permissions.set(permissions)
        
        # Para 'custom' no asignamos permisos automáticamente
        
        return profile


# ==============================================
# FORMULARIOS DE GESTIÓN AVANZADA
# ==============================================

class UserManagementForm(forms.Form):
    """Formulario para gestión avanzada de usuarios"""
    
    profiles = forms.ModelMultipleChoiceField(
        queryset=UserProfile.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False,
        label='Perfiles asignados'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['profiles'].help_text = f'Selecciona los perfiles para {self.user.get_full_name() or self.user.username}'


class PermissionCreationForm(forms.ModelForm):
    """Formulario para crear permisos personalizados"""
    
    class Meta:
        model = SystemPermission
        fields = [
            'name', 'code', 'permission_type', 'url_pattern', 
            'view_name', 'app_name', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Acceso a reportes financieros'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: menu.reportes_financieros'
            }),
            'permission_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'url_pattern': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: /reportes/financieros/'
            }),
            'view_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: reportes_financieros'
            }),
            'app_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: reportes'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del permiso'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer todos los campos requeridos excepto algunos opcionales
        self.fields['url_pattern'].required = False
        self.fields['view_name'].required = False
        self.fields['app_name'].required = False
    
    def save(self, commit=True):
        permission = super().save(commit=False)
        permission.is_active = True
        permission.auto_generated = False
        
        if commit:
            permission.save()
        return permission


class ProfilePermissionAssignmentForm(forms.Form):
    """Formulario para asignar permisos específicos a un perfil"""
    
    permissions = forms.ModelMultipleChoiceField(
        queryset=SystemPermission.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label='Permisos disponibles'
    )
    
    def __init__(self, *args, **kwargs):
        self.profile = kwargs.pop('profile', None)
        super().__init__(*args, **kwargs)
        
        if self.profile:
            self.fields['permissions'].help_text = f'Selecciona los permisos para el perfil "{self.profile.name}"'
            
        # Ordenar permisos por tipo y nombre
        self.fields['permissions'].queryset = SystemPermission.objects.filter(
            is_active=True
        ).order_by('permission_type', 'name')


class BulkUserProfileAssignmentForm(forms.Form):
    """Formulario para asignación masiva de perfiles a usuarios"""
    
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Usuarios'
    )
    
    profile = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Perfil a asignar'
    )
    
    action = forms.ChoiceField(
        choices=[
            ('add', 'Agregar perfil (mantener existentes)'),
            ('replace', 'Reemplazar perfiles existentes'),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        }),
        initial='add',
        label='Acción'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar usuarios alfabéticamente
        self.fields['users'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name', 'username')


class AdvancedPermissionFilterForm(forms.Form):
    """Formulario avanzado para filtrar permisos"""
    
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, código, descripción...'
        })
    )
    
    permission_type = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + PermissionType.choices,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    app_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por aplicación'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    auto_generated = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Auto-generados'),
            ('false', 'Manuales'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
