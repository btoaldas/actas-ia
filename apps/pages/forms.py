from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, SetPasswordForm, PasswordResetForm, UsernameField
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import EventoMunicipal, DocumentoEvento  # InvitacionExterna TEMPORALMENTE COMENTADO

class RegistrationForm(UserCreationForm):
  password1 = forms.CharField(
      label=_("Password"),
      widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
  )
  password2 = forms.CharField(
      label=_("Password Confirmation"),
      widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Retype password'}),
  )

  class Meta:
    model = User
    fields = ('username', 'email', )

    widgets = {
      'username': forms.TextInput(attrs={
          'class': 'form-control',
          'placeholder': 'Username'
      }),
      'email': forms.EmailInput(attrs={
          'class': 'form-control',
          'placeholder': 'Email'
      })
    }

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username'
    }))
    password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))


class UserPasswordResetForm(PasswordResetForm):
  email = forms.EmailField(widget=forms.EmailInput(attrs={
    'class': 'form-control',
    'placeholder': 'Email'
  }))

class UserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")
    

class UserPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Old Password'
    }), label='Old Password')
    new_password1 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'New Password'
    }), label="New Password")
    new_password2 = forms.CharField(max_length=50, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirm New Password'
    }), label="Confirm New Password")


class EventoForm(forms.ModelForm):
    fecha_inicio = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    fecha_fin = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=False
    )
    
    asistentes_invitados = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Invitar usuarios del sistema"
    )
    
    # Campo para invitaciones externas por email
    invitados_externos = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Ingrese emails separados por comas (ej: juan@puyo.gob.ec, maria@puyo.gob.ec)'
        }),
        required=False,
        label="Invitar por email (personas externas al sistema)"
    )
    
    class Meta:
        model = EventoMunicipal
        fields = ['titulo', 'descripcion', 'tipo', 'visibilidad', 'ubicacion', 
                 'fecha_inicio', 'fecha_fin', 'imagen_evento', 'asistentes_invitados', 'invitados_externos']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'visibilidad': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen_evento': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
    
    def clean_invitados_externos(self):
        """Valida y limpia los emails de invitados externos"""
        emails_text = self.cleaned_data.get('invitados_externos', '')
        if not emails_text.strip():
            return []
        
        emails = [email.strip() for email in emails_text.split(',') if email.strip()]
        valid_emails = []
        
        for email in emails:
            try:
                # Validar formato de email
                forms.EmailField().clean(email)
                valid_emails.append(email)
            except forms.ValidationError:
                raise forms.ValidationError(f'Email inválido: {email}')
        
        return valid_emails


class MultipleFileInput(forms.ClearableFileInput):
    """Widget personalizado para subida múltiple de archivos"""
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """Campo personalizado para subida múltiple de archivos"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result


class DocumentosEventoForm(forms.Form):
    """Formulario para subir múltiples documentos a un evento"""
    TIPO_DOCUMENTO_CHOICES = [
        ('agenda', 'Agenda'),
        ('acta', 'Acta'),
        ('presentacion', 'Presentación'),
        ('anexo', 'Anexo'),
        ('convocatoria', 'Convocatoria'),
        ('planos', 'Planos/DWG'),
        ('imagenes', 'Imágenes'),
        ('documentos', 'Documentos'),
        ('comprimidos', 'Archivos Comprimidos'),
        ('otro', 'Otro'),
    ]
    
    archivos = MultipleFileField(
        required=False,
        label="Documentos del evento",
        help_text="Seleccione múltiples archivos (PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, DWG, ZIP, RAR, etc.)",
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True,
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.dwg,.zip,.rar,.txt,.csv'
        })
    )
    
    tipo_documento = forms.ChoiceField(
        choices=TIPO_DOCUMENTO_CHOICES,
        initial='otro',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Tipo de documento",
        help_text="Clasificación de los documentos subidos"
    )
    
    es_publico = forms.BooleanField(
        required=False,
        initial=True,
        label="Documentos públicos",
        help_text="Marque si estos documentos son públicos y pueden ser vistos por todos los asistentes"
    )
    
    def clean_archivos(self):
        """Validar archivos subidos"""
        archivos = self.cleaned_data.get('archivos', [])
        if not archivos:
            return []
        
        # Si es un solo archivo, convertir a lista
        if not isinstance(archivos, list):
            archivos = [archivos]
        
        # Validar tamaño máximo (10 MB por archivo)
        max_size = 10 * 1024 * 1024  # 10 MB
        
        # Extensiones permitidas
        extensiones_permitidas = [
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.dwg', '.dxf', '.zip', '.rar', '.7z',
            '.txt', '.csv', '.rtf'
        ]
        
        archivos_validados = []
        for archivo in archivos:
            if archivo.size > max_size:
                raise forms.ValidationError(f'El archivo "{archivo.name}" es muy grande. Máximo 10 MB por archivo.')
            
            # Verificar extensión
            nombre_archivo = archivo.name.lower()
            extension_valida = any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas)
            
            if not extension_valida:
                raise forms.ValidationError(f'Tipo de archivo no permitido: "{archivo.name}". Extensiones permitidas: {", ".join(extensiones_permitidas)}')
            
            archivos_validados.append(archivo)
        
        return archivos_validados