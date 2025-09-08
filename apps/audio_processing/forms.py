from django import forms
from django.core.validators import FileExtensionValidator
from .models import ProcesamientoAudio, TipoReunion

class SubirAudioForm(forms.ModelForm):
    """Formulario mejorado para subir archivos de audio"""
    
    archivo = forms.FileField(
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp3', 'wav', 'mp4', 'm4a', 'webm', 'ogg', 'flac']
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'audio/*,.mp3,.wav,.mp4,.m4a,.webm,.ogg,.flac',
            'required': True
        })
    )
    
    class Meta:
        model = ProcesamientoAudio
        fields = ['titulo', 'tipo_reunion', 'descripcion', 'etiquetas', 'confidencial']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Concejo Municipal - Sesión Ordinaria',
                'required': True,
                'maxlength': 200
            }),
            'tipo_reunion': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción adicional sobre la reunión (opcional)'
            }),
            'etiquetas': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: presupuesto, obras públicas, urbanismo',
                'maxlength': 200
            }),
            'confidencial': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'titulo': 'Título de la Reunión',
            'tipo_reunion': 'Tipo de Reunión',
            'descripcion': 'Descripción Adicional',
            'etiquetas': 'Etiquetas (separadas por comas)',
            'confidencial': 'Proceso Confidencial'
        }
    
    def clean_archivo(self):
        """Validación mejorada del archivo de audio"""
        archivo = self.cleaned_data.get('archivo')
        if not archivo:
            raise forms.ValidationError("Archivo requerido")
        
        # Validar tamaño del archivo (máximo 100MB como sugiere la guía)
        if archivo.size > 100 * 1024 * 1024:
            raise forms.ValidationError('El archivo es demasiado grande. Máximo permitido: 100MB')
        
        # Validar extensión
        extensiones_permitidas = ['mp3', 'wav', 'mp4', 'm4a', 'webm', 'ogg', 'flac']
        extension = archivo.name.split('.')[-1].lower()
        if extension not in extensiones_permitidas:
            raise forms.ValidationError(
                f'Formato no soportado. Extensiones permitidas: {", ".join(extensiones_permitidas)}'
            )
        
        return archivo
    
    def clean_etiquetas(self):
        """Validación y limpieza de etiquetas"""
        etiquetas = self.cleaned_data.get('etiquetas', '')
        if etiquetas:
            # Limpiar y validar etiquetas
            etiquetas_list = [tag.strip() for tag in etiquetas.split(',') if tag.strip()]
            if len(etiquetas_list) > 10:
                raise forms.ValidationError('Máximo 10 etiquetas permitidas')
            return ', '.join(etiquetas_list)
        return etiquetas


class TipoReunionForm(forms.ModelForm):
    """Formulario para gestionar tipos de reunión"""
    
    class Meta:
        model = TipoReunion
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Concejo Municipal',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del tipo de reunión'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'nombre': 'Nombre del Tipo',
            'descripcion': 'Descripción',
            'activo': 'Activo'
        }


class FiltroProcesamientoForm(forms.Form):
    """Formulario para filtrar procesamientos de audio"""
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('transcribiendo', 'Transcribiendo'),
        ('diarizando', 'Diarizando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
        ('cancelado', 'Cancelado'),
    ]
    
    titulo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título...'
        })
    )
    
    tipo_reunion = forms.ModelChoiceField(
        queryset=TipoReunion.objects.filter(activo=True),
        required=False,
        empty_label='Todos los tipos',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class EditarProcesamientoForm(forms.ModelForm):
    """Formulario para editar datos básicos de un procesamiento"""
    
    class Meta:
        model = ProcesamientoAudio
        fields = ['titulo', 'tipo_reunion', 'descripcion', 'etiquetas', 'confidencial', 'participantes', 'participantes_detallados', 'ubicacion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Concejo Municipal - Sesión Ordinaria',
                'required': True,
                'maxlength': 200
            }),
            'tipo_reunion': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción adicional sobre la reunión (opcional)'
            }),
            'etiquetas': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: presupuesto, obras públicas, urbanismo',
                'maxlength': 200
            }),
            'confidencial': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'participantes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Lista de participantes (texto libre)'
            }),
            'participantes_detallados': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Información detallada de los participantes en formato JSON'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sala de Concejo Municipal',
                'maxlength': 200
            })
        }
        labels = {
            'titulo': 'Título de la Reunión',
            'tipo_reunion': 'Tipo de Reunión',
            'descripcion': 'Descripción Adicional',
            'etiquetas': 'Etiquetas (separadas por comas)',
            'confidencial': 'Proceso Confidencial',
            'participantes': 'Participantes (texto libre)',
            'participantes_detallados': 'Participantes detallados (JSON)',
            'ubicacion': 'Ubicación de la reunión'
        }
    
    def clean_etiquetas(self):
        """Validación y limpieza de etiquetas"""
        etiquetas = self.cleaned_data.get('etiquetas', '')
        if etiquetas:
            # Limpiar y validar etiquetas
            etiquetas_list = [tag.strip() for tag in etiquetas.split(',') if tag.strip()]
            if len(etiquetas_list) > 10:
                raise forms.ValidationError('Máximo 10 etiquetas permitidas')
            return ', '.join(etiquetas_list)
        return etiquetas


class ConfiguracionProcesamientoForm(forms.Form):
    """Formulario para configurar opciones de procesamiento"""
    
    CALIDAD_AUDIO_CHOICES = [
        ('baja', 'Baja (más rápido)'),
        ('media', 'Media (equilibrado)'),
        ('alta', 'Alta (mejor calidad)'),
    ]
    
    MODELO_TRANSCRIPCION_CHOICES = [
        ('whisper-tiny', 'Tiny (muy rápido, menos preciso)'),
        ('whisper-base', 'Base (rápido, precisión media)'),
        ('whisper-small', 'Small (equilibrado)'),
        ('whisper-medium', 'Medium (lento, muy preciso)'),
        ('whisper-large', 'Large (muy lento, máxima precisión)'),
    ]
    
    normalizar_audio = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Normalizar volumen del audio'
    )
    
    reducir_ruido = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Aplicar reducción de ruido'
    )
    
    calidad_audio = forms.ChoiceField(
        choices=CALIDAD_AUDIO_CHOICES,
        initial='media',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Calidad de procesamiento de audio'
    )
    
    modelo_transcripcion = forms.ChoiceField(
        choices=MODELO_TRANSCRIPCION_CHOICES,
        initial='whisper-base',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Modelo de transcripción'
    )
    
    diarizar_speakers = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Identificar diferentes oradores (diarización)'
    )
    
    generar_acta_automatica = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Generar acta automática con IA'
    )
