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
    
    # Campo para invitaciones externas por email - TEMPORALMENTE COMENTADO
    # invitados_externos = forms.CharField(
    #     widget=forms.Textarea(attrs={
    #         'rows': 3,
    #         'class': 'form-control',
    #         'placeholder': 'Ingrese emails separados por comas (ej: juan@puyo.gob.ec, maria@puyo.gob.ec)'
    #     }),
    #     required=False,
    #     label="Invitar por email (personas externas al sistema)"
    # )
    
    class Meta:
        model = EventoMunicipal
        fields = ['titulo', 'descripcion', 'tipo', 'visibilidad', 'ubicacion', 
                 'fecha_inicio', 'fecha_fin', 'asistentes_invitados']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'visibilidad': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    # TEMPORALMENTE COMENTADO - clean_invitados_externos
    # def clean_invitados_externos(self):
    #     """Valida y limpia los emails de invitados externos"""
    #     emails_text = self.cleaned_data.get('invitados_externos', '')
    #     if not emails_text.strip():
    #         return []
    #     
    #     emails = [email.strip() for email in emails_text.split(',') if email.strip()]
    #     valid_emails = []
    #     
    #     for email in emails:
    #         try:
    #             # Validar formato de email
    #             forms.EmailField().clean(email)
    #             valid_emails.append(email)
    #         except forms.ValidationError:
    #             raise forms.ValidationError(f'Email inválido: {email}')
    #     
    #     return valid_emails