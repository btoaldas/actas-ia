"""
Formularios para el módulo generador de actas
Incluye formularios dinámicos e inteligentes para proveedores de IA
"""
import json
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import ActaGenerada, PlantillaActa, SegmentoPlantilla, ConfiguracionSegmento, ProveedorIA


class ProveedorIAForm(forms.ModelForm):
    """Formulario dinámico para proveedores de IA"""
    
    # Campos para configuración adicional JSON de forma amigable
    top_p = forms.FloatField(
        required=False, 
        initial=1.0, 
        min_value=0.0, 
        max_value=1.0,
        help_text="Controla la diversidad de respuestas (0.0-1.0)"
    )
    
    frequency_penalty = forms.FloatField(
        required=False, 
        initial=0.0, 
        min_value=-2.0, 
        max_value=2.0,
        help_text="Penaliza repetición de palabras (-2.0 a 2.0)"
    )
    
    presence_penalty = forms.FloatField(
        required=False, 
        initial=0.0, 
        min_value=-2.0, 
        max_value=2.0,
        help_text="Penaliza temas ya mencionados (-2.0 a 2.0)"
    )
    
    stream = forms.BooleanField(
        required=False, 
        initial=False,
        help_text="Transmisión en tiempo real de la respuesta"
    )
    
    stop_sequences = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Separar por comas: \\n, \\t, STOP'}),
        help_text="Secuencias que detienen la generación (separadas por comas)"
    )
    
    class Meta:
        model = ProveedorIA
        fields = [
            'nombre', 'tipo', 'api_key', 'api_url', 'modelo', 
            'temperatura', 'max_tokens', 'timeout', 'prompt_sistema_global',
            'costo_por_1k_tokens', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: OpenAI GPT-4 Principal'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_tipo_proveedor'
            }),
            'api_key': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dejar vacío para usar la del .env'
            }),
            'api_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL se completa automáticamente'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_modelo_proveedor',
                'list': 'modelos_disponibles'
            }),
            'temperatura': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.0',
                'max': '2.0',
                'step': '0.1'
            }),
            'max_tokens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '100',
                'max': '32000',
                'step': '100'
            }),
            'timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '300',
                'step': '10'
            }),
            'prompt_sistema_global': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Instrucciones adicionales para este proveedor...'
            }),
            'costo_por_1k_tokens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.000001'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar el widget de API key según si es edición o creación
        if self.instance.pk and self.instance.api_key:
            # Si es edición y tiene API key, mostrar placeholder especial
            self.fields['api_key'].widget.attrs.update({
                'placeholder': '••••••••••••••••••••••••••••••••••••••••••••••••••••••'
            })
            self.fields['api_key'].help_text = 'API Key configurada. Dejar vacío para mantener la actual, o escribir nueva clave para cambiarla.'
            self.fields['api_key'].required = False
        else:
            # Si es creación, usar placeholder normal
            self.fields['api_key'].widget.attrs.update({
                'placeholder': 'Clave API del proveedor (dejar vacío para usar .env)'
            })
            self.fields['api_key'].help_text = 'Dejar vacío para usar la configuración del .env'
        
        # Cargar valores por defecto si es un nuevo proveedor
        if not self.instance.pk:
            self._aplicar_valores_defecto()
        
        # Configurar campos según el proveedor existente
        if self.instance.pk and self.instance.configuracion_adicional:
            self._cargar_configuracion_adicional()
    
    def _aplicar_valores_defecto(self):
        """Aplica valores por defecto desde el .env"""
        configuraciones = ProveedorIA.obtener_configuraciones_por_defecto()
        
        # Si ya hay un tipo seleccionado, aplicar sus defaults
        tipo_inicial = self.data.get('tipo') or self.initial.get('tipo')
        if tipo_inicial and tipo_inicial in configuraciones:
            config = configuraciones[tipo_inicial]
            
            for campo, valor in config.items():
                if campo in self.fields and not self.initial.get(campo):
                    self.initial[campo] = valor
    
    def _cargar_configuracion_adicional(self):
        """Carga la configuración adicional JSON en campos separados"""
        config = self.instance.configuracion_adicional or {}
        
        for campo in ['top_p', 'frequency_penalty', 'presence_penalty', 'stream']:
            if campo in config:
                self.fields[campo].initial = config[campo]
        
        # Manejar stop_sequences como string
        if 'stop' in config and isinstance(config['stop'], list):
            self.fields['stop_sequences'].initial = ', '.join(config['stop'])
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        api_key = cleaned_data.get('api_key')
        api_url = cleaned_data.get('api_url')
        modelo = cleaned_data.get('modelo')
        
        # Validaciones específicas por tipo de proveedor
        if tipo in ['openai', 'anthropic', 'deepseek', 'google', 'groq', 'generic1', 'generic2']:
            if not api_key:
                # Verificar si existe en .env
                env_key = f"{tipo.upper()}_API_KEY"
                if not getattr(settings, env_key, None):
                    raise ValidationError({
                        'api_key': f'API Key requerida para {dict(ProveedorIA.TIPO_PROVEEDOR)[tipo]}'
                    })
        
        elif tipo in ['ollama', 'lmstudio']:
            if not api_url:
                raise ValidationError({
                    'api_url': f'URL del servicio requerida para {dict(ProveedorIA.TIPO_PROVEEDOR)[tipo]}'
                })
        
        # Validar modelo
        if not modelo:
            raise ValidationError({
                'modelo': 'El modelo es requerido'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Construir configuración adicional JSON desde campos separados
        configuracion_adicional = {}
        
        # Agregar parámetros opcionales si fueron especificados
        for campo in ['top_p', 'frequency_penalty', 'presence_penalty', 'stream']:
            valor = self.cleaned_data.get(campo)
            if valor is not None and valor != self.fields[campo].initial:
                configuracion_adicional[campo] = valor
        
        # Manejar stop_sequences
        stop_sequences = self.cleaned_data.get('stop_sequences')
        if stop_sequences:
            # Convertir string a lista
            stop_list = [seq.strip() for seq in stop_sequences.split(',') if seq.strip()]
            if stop_list:
                configuracion_adicional['stop'] = stop_list
        
        # Mantener configuración existente y agregar nuevos valores
        config_existente = instance.configuracion_adicional or {}
        config_existente.update(configuracion_adicional)
        instance.configuracion_adicional = config_existente
        
        if commit:
            instance.save()
        
        return instance
    
    @staticmethod
    def obtener_modelos_por_proveedor():
        """Obtiene los modelos disponibles por proveedor"""
        return {
            'openai': [
                'gpt-4o',
                'gpt-4o-mini',
                'gpt-4-turbo',
                'gpt-4',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k'
            ],
            'anthropic': [
                'claude-3-5-sonnet-20241022',
                'claude-3-5-haiku-20241022',
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307'
            ],
            'deepseek': [
                'deepseek-chat',
                'deepseek-coder',
                'deepseek-reasoning'
            ],
            'google': [
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-1.0-pro'
            ],
            'groq': [
                'llama-3.1-70b-versatile',
                'llama-3.1-8b-instant',
                'mixtral-8x7b-32768',
                'gemma2-9b-it'
            ],
            'ollama': [
                'llama3.2:3b',
                'llama3.2:1b',
                'llama3.1:8b',
                'llama3.1:70b',
                'mistral:7b',
                'mixtral:8x7b',
                'qwen2.5:7b',
                'gemma2:9b'
            ],
            'lmstudio': [
                'lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF',
                'lmstudio-ai/gemma-2b-it-GGUF',
                'microsoft/DialoGPT-medium',
                'microsoft/Phi-3-mini-4k-instruct-gguf'
            ],
            'generic1': ['custom-model-1', 'custom-model-2'],
            'generic2': ['custom-model-1', 'custom-model-2']
        }


class TestProveedorForm(forms.Form):
    """Formulario para probar conexión con proveedores"""
    
    proveedor = forms.ModelChoiceField(
        queryset=ProveedorIA.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Selecciona el proveedor a probar"
    )
    
    prompt_prueba = forms.CharField(
        initial="Responde únicamente con el siguiente JSON exacto: {\"status\": \"ok\", \"test\": \"exitoso\"}",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        help_text="Prompt para probar el proveedor"
    )
    
    incluir_contexto = forms.BooleanField(
        initial=False,
        required=False,
        help_text="Incluir contexto de prueba en la solicitud"
    )


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
    Formulario completo para configurar proveedores de IA
    """
    # Campos adicionales para configuración
    top_p = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '1',
            'step': '0.01'
        })
    )
    frequency_penalty = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '-2',
            'max': '2',
            'step': '0.01'
        })
    )
    presence_penalty = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '-2',
            'max': '2',
            'step': '0.01'
        })
    )
    stop_sequences = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: \\n\\n, \\n, . (separado por comas)'
        })
    )
    stream = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = ProveedorIA
        fields = [
            'nombre', 'tipo', 'api_key', 'api_url', 'modelo', 
            'temperatura', 'max_tokens', 'prompt_sistema_global',
            'costo_por_1k_tokens', 'activo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo del proveedor'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'api_key': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clave API del proveedor (dejar vacío para usar .env)'
            }),
            'api_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Se auto-completa según el tipo de proveedor'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'list': 'modelos_disponibles',
                'placeholder': 'ej: gpt-4o, claude-3-5-sonnet, deepseek-chat'
            }),
            'temperatura': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '2',
                'step': '0.1'
            }),
            'max_tokens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '100',
                'max': '8000'
            }),
            'prompt_sistema_global': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Instrucciones adicionales para este proveedor...'
            }),
            'costo_por_1k_tokens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.000001'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar valores por defecto si es un nuevo proveedor
        if not self.instance.pk:
            self._aplicar_valores_defecto()
        else:
            # Para instancias existentes, ocultar la API key real
            if self.instance.api_key:
                self.fields['api_key'].widget.attrs['placeholder'] = '••••••••••••••••'
                self.initial['api_key'] = ''  # No mostrar la key real
        
        # Configurar campos según el proveedor existente
        if self.instance.pk and self.instance.configuracion_adicional:
            self._cargar_configuracion_adicional()
    
    def _aplicar_valores_defecto(self):
        """Aplica valores por defecto desde el .env"""
        configuraciones = ProveedorIA.obtener_configuraciones_por_defecto()
        
        # Si ya hay un tipo seleccionado, aplicar sus defaults
        tipo_inicial = self.data.get('tipo') or self.initial.get('tipo')
        if tipo_inicial and tipo_inicial in configuraciones:
            config = configuraciones[tipo_inicial]
            
            for campo, valor in config.items():
                if campo in self.fields and not self.initial.get(campo):
                    self.initial[campo] = valor
    
    def _cargar_configuracion_adicional(self):
        """Carga la configuración adicional JSON en campos separados"""
        config = self.instance.configuracion_adicional or {}
        
        for campo in ['top_p', 'frequency_penalty', 'presence_penalty', 'stream']:
            if campo in config:
                self.fields[campo].initial = config[campo]
        
        # Manejar stop_sequences como string
        if 'stop' in config and isinstance(config['stop'], list):
            self.fields['stop_sequences'].initial = ', '.join(config['stop'])
    
    def clean_api_key(self):
        api_key = self.cleaned_data.get('api_key')
        tipo = self.cleaned_data.get('tipo')
        
        # Si es edición y no se proporciona API key, mantener la existente
        if self.instance.pk and not api_key:
            return self.instance.api_key
        
        # Validar que proveedores remotos tengan API key
        if tipo in ['openai', 'anthropic', 'deepseek', 'google', 'groq', 'generic1', 'generic2']:
            if not api_key and not self.instance.api_key:
                # Verificar si existe en .env
                env_key = f"{tipo.upper()}_API_KEY"
                if not getattr(settings, env_key, None):
                    raise ValidationError(f'API Key requerida para {dict(ProveedorIA.TIPO_PROVEEDOR)[tipo]}')
        
        return api_key
    
    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        api_url = cleaned_data.get('api_url')
        modelo = cleaned_data.get('modelo')
        
        # Validaciones específicas por tipo de proveedor
        if tipo in ['ollama', 'lmstudio']:
            if not api_url:
                raise ValidationError({
                    'api_url': f'URL del servicio requerida para {dict(ProveedorIA.TIPO_PROVEEDOR)[tipo]}'
                })
        
        # Validar modelo
        if not modelo:
            raise ValidationError({
                'modelo': 'El modelo es requerido'
            })
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Construir configuración adicional JSON desde campos separados
        configuracion_adicional = {}
        
        # Agregar parámetros opcionales si fueron especificados
        for campo in ['top_p', 'frequency_penalty', 'presence_penalty', 'stream']:
            valor = self.cleaned_data.get(campo)
            if valor is not None and valor != self.fields[campo].initial:
                configuracion_adicional[campo] = valor
        
        # Manejar stop_sequences
        stop_sequences = self.cleaned_data.get('stop_sequences')
        if stop_sequences:
            # Convertir string a lista
            stop_list = [seq.strip() for seq in stop_sequences.split(',') if seq.strip()]
            if stop_list:
                configuracion_adicional['stop'] = stop_list
        
        # Mantener configuración existente y agregar nuevos valores
        config_existente = instance.configuracion_adicional or {}
        config_existente.update(configuracion_adicional)
        instance.configuracion_adicional = config_existente
        
        if commit:
            instance.save()
        
        return instance
    
    @staticmethod
    def obtener_modelos_por_proveedor():
        """Obtiene los modelos disponibles por proveedor"""
        return {
            'openai': [
                'gpt-4o',
                'gpt-4o-mini',
                'gpt-4-turbo',
                'gpt-4',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k'
            ],
            'anthropic': [
                'claude-3-5-sonnet-20241022',
                'claude-3-5-haiku-20241022',
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307'
            ],
            'deepseek': [
                'deepseek-chat',
                'deepseek-coder',
                'deepseek-reasoning'
            ],
            'google': [
                'gemini-1.5-flash',
                'gemini-1.5-pro',
                'gemini-1.0-pro'
            ],
            'groq': [
                'llama-3.1-70b-versatile',
                'llama-3.1-8b-instant',
                'mixtral-8x7b-32768',
                'gemma2-9b-it'
            ],
            'ollama': [
                'llama3.2:3b',
                'llama3.2:1b',
                'llama3.1:8b',
                'llama3.1:70b',
                'mistral:7b',
                'mixtral:8x7b',
                'qwen2.5:7b',
                'gemma2:9b'
            ],
            'lmstudio': [
                'lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF',
                'lmstudio-ai/gemma-2b-it-GGUF',
                'microsoft/DialoGPT-medium',
                'microsoft/Phi-3-mini-4k-instruct-gguf'
            ],
            'generic1': ['custom-model-1', 'custom-model-2'],
            'generic2': ['custom-model-1', 'custom-model-2']
        }


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