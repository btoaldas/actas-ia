"""
Formularios para el módulo generador de actas
"""
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import ActaGenerada, PlantillaActa, SegmentoPlantilla, ConfiguracionSegmento, ProveedorIA


class ActaGeneradaForm(forms.ModelForm):
    """
    Formulario para crear y editar actas generadas
    """
    class Meta:
        model = ActaGenerada
        fields = [
            'numero_acta', 'titulo', 'plantilla'
        ]
        widgets = {
            'numero_acta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número del acta (opcional, se genera automáticamente)'
            }),
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo del acta'
            }),
            'plantilla': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo plantillas activas
        self.fields['plantilla'].queryset = PlantillaActa.objects.filter(activa=True)


class PlantillaActaForm(forms.ModelForm):
    """
    Formulario para crear y editar plantillas de actas
    """
    class Meta:
        model = PlantillaActa
        fields = [
            'codigo', 'nombre', 'descripcion', 'tipo_acta', 'activa'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único de la plantilla'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo de la plantilla'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del uso y características de la plantilla'
            }),
            'tipo_acta': forms.Select(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            # Verificar unicidad excluyendo la instancia actual
            queryset = PlantillaActa.objects.filter(codigo=codigo)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Ya existe una plantilla con este código")
        
        return codigo


class ConfiguracionSegmentoForm(forms.ModelForm):
    """
    Formulario para configuración de segmentos en plantillas
    """
    class Meta:
        model = ConfiguracionSegmento
        fields = [
            'segmento', 'orden', 'obligatorio', 'prompt_personalizado', 'parametros_override'
        ]
        widgets = {
            'segmento': forms.Select(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'obligatorio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prompt_personalizado': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Prompt personalizado para este segmento (opcional)'
            }),
            'parametros_override': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '{"param1": "valor1", "param2": "valor2"} (JSON opcional)'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar segmentos
        self.fields['segmento'].queryset = SegmentoPlantilla.objects.all()

    def clean_parametros_override(self):
        parametros = self.cleaned_data.get('parametros_override')
        if parametros:
            try:
                import json
                json.loads(parametros)
            except json.JSONDecodeError:
                raise ValidationError("Los parámetros deben ser un JSON válido")
        
        return parametros


# FormSet para gestionar múltiples configuraciones de segmentos
ConfiguracionSegmentoFormSet = inlineformset_factory(
    PlantillaActa,
    ConfiguracionSegmento,
    form=ConfiguracionSegmentoForm,
    extra=1,
    can_delete=True,
    can_order=True
)


class SegmentoPlantillaForm(forms.ModelForm):
    """
    Formulario para crear y editar segmentos de plantillas
    """
    class Meta:
        model = SegmentoPlantilla
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria', 'tipo', 'prompt_ia'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del segmento'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del segmento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del propósito del segmento'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'prompt_ia': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Prompt base para generar este segmento con IA'
            })
        }

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            # Verificar unicidad excluyendo la instancia actual
            queryset = SegmentoPlantilla.objects.filter(codigo=codigo)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise ValidationError("Ya existe un segmento con este código")
        
        return codigo


class ProveedorIAForm(forms.ModelForm):
    """
    Formulario para configurar proveedores de IA
    """
    class Meta:
        model = ProveedorIA
        fields = [
            'nombre', 'tipo', 'api_key', 'modelo', 'temperatura', 'max_tokens', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo del proveedor'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'api_key': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clave API del proveedor'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ej: gpt-4, claude-3-sonnet, llama2'
            }),
            'temperatura': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0.0,
                'max': 1.0,
                'step': 0.1
            }),
            'max_tokens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 100,
                'max': 8000
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_api_key(self):
        api_key = self.cleaned_data.get('api_key')
        tipo = self.cleaned_data.get('tipo')
        
        # Validar que proveedores remotos tengan API key
        if tipo in ['openai', 'deepseek', 'anthropic', 'google'] and not api_key:
            raise ValidationError(f"El proveedor {tipo} requiere una clave API")
        
        return api_key


class BusquedaActasForm(forms.Form):
    """
    Formulario de búsqueda y filtrado para actas
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número, título o plantilla...'
        })
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + [
            ('pendiente', 'Pendiente'),
            ('procesando', 'Procesando'),
            ('completado', 'Completado'),
            ('error', 'Error'),
            ('cancelado', 'Cancelado')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    proveedor = forms.ModelChoiceField(
        queryset=ProveedorIA.objects.filter(activo=True),
        required=False,
        empty_label="Todos los proveedores",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    plantilla = forms.ModelChoiceField(
        queryset=PlantillaActa.objects.filter(activa=True),
        required=False,
        empty_label="Todas las plantillas",
        widget=forms.Select(attrs={'class': 'form-control'})
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


class BusquedaPlantillasForm(forms.Form):
    """
    Formulario de búsqueda y filtrado para plantillas
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, descripción o tipo...'
        })
    )
    
    tipo_acta = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + [
            ('ordinaria', 'Sesión Ordinaria'),
            ('extraordinaria', 'Sesión Extraordinaria'),
            ('audiencia', 'Audiencia Pública'),
            ('comision', 'Comisión'),
            ('directorio', 'Directorio'),
            ('asamblea', 'Asamblea'),
            ('otros', 'Otros')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    activa = forms.ChoiceField(
        choices=[('', 'Todas'), ('1', 'Activas'), ('0', 'Inactivas')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )