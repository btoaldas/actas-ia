from django import forms
from django.contrib.auth.models import User
from .models import PermisoCustom, PerfilUsuario, UsuarioPerfil


class PermisoCustomForm(forms.ModelForm):
    """Formulario para crear/editar permisos personalizados"""
    
    class Meta:
        model = PermisoCustom
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria', 'nivel_acceso',
            'urls_permitidas', 'mostrar_en_menu', 'icono_menu', 'orden_menu', 
            'es_sistema', 'activo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ej: actas.crear, users.editar',
                'pattern': '[a-zA-Z0-9._-]+',
                'title': 'Solo letras, números, puntos, guiones y guiones bajos'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo del permiso'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del permiso...'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'nivel_acceso': forms.Select(attrs={'class': 'form-control'}),
            'urls_permitidas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '/actas/, /actas/crear/, /api/actas/'
            }),
            'icono_menu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'fas fa-file-alt, fas fa-users, etc.'
            }),
            'orden_menu': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '999'
            }),
            'mostrar_en_menu': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'es_sistema': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            # Convertir a minúsculas y reemplazar espacios
            codigo = codigo.lower().replace(' ', '_')
            # Validar formato
            import re
            if not re.match(r'^[a-z0-9._-]+$', codigo):
                raise forms.ValidationError(
                    'El código solo puede contener letras minúsculas, números, puntos, guiones y guiones bajos'
                )
        return codigo
    
    def clean_urls_permitidas(self):
        urls = self.cleaned_data.get('urls_permitidas', '')
        if urls:
            # Validar que sean URLs válidas
            url_list = [url.strip() for url in urls.split(',') if url.strip()]
            for url in url_list:
                if not url.startswith('/'):
                    raise forms.ValidationError(f'La URL "{url}" debe comenzar con "/"')
        return urls


class PerfilUsuarioForm(forms.ModelForm):
    """Formulario para crear/editar perfiles de usuario"""
    
    permisos = forms.ModelMultipleChoiceField(
        queryset=PermisoCustom.objects.filter(activo=True),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        help_text="Selecciona los permisos que tendrá este perfil"
    )
    
    class Meta:
        model = PerfilUsuario
        fields = [
            'nombre', 'descripcion', 'color', 'es_publico', 'nivel_jerarquia',
            'dashboard_personalizado', 'pagina_inicio', 'permisos', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del perfil'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del perfil...'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'nivel_jerarquia': forms.Select(
                choices=[
                    (0, 'Usuario Común'),
                    (1, 'Supervisor'),
                    (2, 'Administrador'),
                    (3, 'Super Administrador')
                ],
                attrs={'class': 'form-control'}
            ),
            'pagina_inicio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '/dashboard/, /actas/, etc.'
            }),
            'es_publico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dashboard_personalizado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizar permisos por categoría para mejor visualización
        if self.fields['permisos'].queryset:
            self.permisos_por_categoria = {}
            for permiso in self.fields['permisos'].queryset:
                categoria = permiso.get_categoria_display()
                if categoria not in self.permisos_por_categoria:
                    self.permisos_por_categoria[categoria] = []
                self.permisos_por_categoria[categoria].append(permiso)


class UsuarioPerfilForm(forms.ModelForm):
    """Formulario para asignar perfiles a usuarios"""
    
    usuario = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    perfil = forms.ModelChoiceField(
        queryset=PerfilUsuario.objects.filter(activo=True).order_by('nombre'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UsuarioPerfil
        fields = ['usuario', 'perfil', 'es_principal', 'fecha_expiracion', 'notas']
        widgets = {
            'fecha_expiracion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas sobre esta asignación...'
            }),
            'es_principal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BusquedaPermisosForm(forms.Form):
    """Formulario para búsqueda avanzada de permisos"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, nombre o descripción...'
        })
    )
    
    categoria = forms.ChoiceField(
        choices=[('', 'Todas las categorías')] + PermisoCustom.CATEGORIAS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    nivel_acceso = forms.ChoiceField(
        choices=[('', 'Todos los niveles')] + [
            ('leer', 'Solo Lectura'),
            ('escribir', 'Lectura y Escritura'),
            ('eliminar', 'Lectura, Escritura y Eliminación'),
            ('admin', 'Administración Completa'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    activo = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    es_sistema = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Del Sistema'), ('false', 'Personalizados')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BusquedaPerfilesForm(forms.Form):
    """Formulario para búsqueda avanzada de perfiles"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o descripción...'
        })
    )
    
    nivel_jerarquia = forms.ChoiceField(
        choices=[('', 'Todos los niveles')] + [
            ('0', 'Usuario Común'),
            ('1', 'Supervisor'),
            ('2', 'Administrador'),
            ('3', 'Super Administrador')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    activo = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    es_publico = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Públicos'), ('false', 'Privados')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AsignacionMasivaForm(forms.Form):
    """Formulario para asignación masiva de perfiles"""
    
    usuarios = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        widget=forms.CheckboxSelectMultiple(),
        help_text="Selecciona los usuarios a los que asignar el perfil"
    )
    
    perfil = forms.ModelChoiceField(
        queryset=PerfilUsuario.objects.filter(activo=True).order_by('nombre'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    es_principal = forms.BooleanField(
        required=False,
        help_text="¿Será el perfil principal para estos usuarios?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    notas = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notas sobre esta asignación masiva...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Organizar usuarios por grupos para mejor visualización
        self.usuarios_por_grupo = {
            'Superusuarios': User.objects.filter(is_superuser=True, is_active=True),
            'Staff': User.objects.filter(is_staff=True, is_superuser=False, is_active=True),
            'Usuarios Regulares': User.objects.filter(is_staff=False, is_superuser=False, is_active=True)
        }
