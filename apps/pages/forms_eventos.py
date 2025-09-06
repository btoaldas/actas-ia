from django import forms
from django.contrib.auth.models import User
from .models import EventoMunicipal, DocumentoEvento


class EventoForm(forms.ModelForm):
    """Formulario para crear y editar eventos municipales"""
    
    class Meta:
        model = EventoMunicipal
        fields = [
            'titulo', 'descripcion', 'tipo', 'fecha_inicio', 'fecha_fin',
            'ubicacion', 'direccion', 'responsable', 'visibilidad', 'estado',
            'capacidad_maxima', 'asistentes_invitados', 'imagen_evento'
        ]
        
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del evento',
                'maxlength': 200
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción detallada del evento',
                'rows': 4
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_inicio': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'fecha_fin': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sala de sesiones, Auditorio, etc.'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dirección del evento (opcional)'
            }),
            'responsable': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del responsable del evento'
            }),
            'visibilidad': forms.Select(attrs={
                'class': 'form-select'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            }),
            'capacidad_maxima': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': '0 = sin límite'
            }),
            'asistentes_invitados': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 8
            }),
            'imagen_evento': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        
        labels = {
            'titulo': 'Título del evento',
            'descripcion': 'Descripción',
            'tipo': 'Tipo de evento',
            'fecha_inicio': 'Fecha y hora de inicio',
            'fecha_fin': 'Fecha y hora de fin',
            'ubicacion': 'Ubicación',
            'direccion': 'Dirección completa',
            'responsable': 'Responsable del evento',
            'visibilidad': 'Visibilidad',
            'estado': 'Estado',
            'capacidad_maxima': 'Capacidad máxima',
            'asistentes_invitados': 'Invitar usuarios',
            'imagen_evento': 'Imagen del evento'
        }
        
        help_texts = {
            'capacidad_maxima': 'Dejar en 0 para no limitar la capacidad',
            'asistentes_invitados': 'Usuarios específicos que pueden ver eventos privados',
            'imagen_evento': 'Imagen opcional para el evento (JPG, PNG)'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo usuarios activos para invitaciones
        self.fields['asistentes_invitados'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
        
        # Mejorar display de usuarios
        user_choices = []
        for user in self.fields['asistentes_invitados'].queryset:
            display_name = user.get_full_name() if user.get_full_name() else user.username
            user_choices.append((user.id, f"{display_name} ({user.username})"))
        
        self.fields['asistentes_invitados'].choices = user_choices
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_fin <= fecha_inicio:
                raise forms.ValidationError("La fecha de fin debe ser posterior a la fecha de inicio")
        
        return cleaned_data


class DocumentoEventoForm(forms.ModelForm):
    """Formulario para subir documentos de eventos"""
    
    class Meta:
        model = DocumentoEvento
        fields = ['nombre', 'descripcion', 'archivo', 'es_publico']
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del documento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del documento (opcional)',
                'rows': 3
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx'
            }),
            'es_publico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'archivo': 'Archivo',
            'es_publico': 'Documento público'
        }
        
        help_texts = {
            'archivo': 'Formatos permitidos: PDF, Word, Excel, PowerPoint',
            'es_publico': 'Marcar si el documento puede ser visto por todos los usuarios'
        }
