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





class TestProveedorForm(forms.Form):
      

    def clean(self):
        """Validación global del formulario para manejar API key según checkbox"""
        cleaned_data = super().clean()
        api_key = cleaned_data.get('api_key')
        usar_env = cleaned_data.get('usar_env_api_key', False)
        tipo = cleaned_data.get('tipo', '')
        
        if usar_env:
            # Si usa .env, limpiar el campo api_key para evitar errores de validación
            cleaned_data['api_key'] = ''
        else:
            # Si no usa .env, API key es obligatoria
            if not api_key or api_key.strip() == '':
                self.add_error('api_key', 
                    'Debe proporcionar una API Key personalizada o marcar "Usar configuración del .env"'
                )

        return cleaned_data

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
    usar_env_api_key = forms.BooleanField(
        required=False,
        initial=True,
        label="Usar configuración del .env",
        help_text="Si está marcado, se usará la API key del archivo .env. Si no, usar la API key personalizada.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
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
                'placeholder': 'Clave API del proveedor (dejar vacío para usar .env)',
                'required': False  # Explícitamente no requerido
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
        
        # El campo api_key NUNCA es requerido por defecto - la validación se hace en clean()
        self.fields['api_key'].required = False
        
        # Remover cualquier validación requerida del widget también
        if 'required' in self.fields['api_key'].widget.attrs:
            del self.fields['api_key'].widget.attrs['required']
        
        # Configurar el campo de API key y checkbox según si es creación o edición
        if self.instance.pk:
            # Modo edición
            if self.instance.api_key:
                # Tiene API key personalizada, checkbox desmarcado
                self.fields['usar_env_api_key'].initial = False
                self.fields['api_key'].widget.attrs.update({
                    'placeholder': 'API Key personalizada configurada'
                })
                self.fields['api_key'].help_text = 'API Key personalizada del proveedor'
                # Mostrar la key actual (o parte de ella)
                if len(self.instance.api_key) > 8:
                    masked_key = self.instance.api_key[:4] + '••••••••••••••••••••••••••••••••••••••••••••••••••••••' + self.instance.api_key[-4:]
                else:
                    masked_key = '••••••••••••••••••••••••••••••••••••••••••••••••••••••'
                self.initial['api_key'] = masked_key
            else:
                # No tiene API key, usa .env, checkbox marcado
                self.fields['usar_env_api_key'].initial = True
                self.fields['api_key'].widget.attrs.update({
                    'placeholder': 'Se usará la configuración del .env'
                })
                self.fields['api_key'].help_text = 'Campo deshabilitado - se usa configuración del .env'
                self.initial['api_key'] = ''
        else:
            # Modo creación - por defecto usar .env
            self.fields['usar_env_api_key'].initial = True
            self.fields['api_key'].widget.attrs.update({
                'placeholder': 'Se usará la configuración del .env'
            })
            self.fields['api_key'].help_text = 'Campo deshabilitado - se usa configuración del .env'
            # Cargar valores por defecto si es un nuevo proveedor
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
        """Validación global del formulario para manejar API key según checkbox"""
        cleaned_data = super().clean()
        api_key = cleaned_data.get('api_key')
        usar_env = cleaned_data.get('usar_env_api_key', False)
        tipo = cleaned_data.get('tipo', '')
        
        # Validación de API Key según el checkbox
        if usar_env:
            # Si usa .env, verificar que existe configuración para proveedores remotos
            if tipo in ['openai', 'anthropic', 'deepseek', 'google', 'groq', 'generic1', 'generic2']:
                env_key = f"{tipo.upper()}_API_KEY"
                if not getattr(settings, env_key, None):
                    self.add_error('usar_env_api_key', 
                        f'No se encontró {env_key} en la configuración del .env. '
                        f'Configure la variable o desmarque "Usar configuración del .env".'
                    )
            # Si usa .env, limpiar el campo api_key para evitar errores de validación
            cleaned_data['api_key'] = ''
        else:
            # Si no usa .env, API key es obligatoria
            if not api_key or api_key.strip() == '':
                self.add_error('api_key', 
                    'Debe proporcionar una API Key personalizada o marcar "Usar configuración del .env"'
                )
        
        # Validaciones específicas por tipo de proveedor
        api_url = cleaned_data.get('api_url')
        modelo = cleaned_data.get('modelo')
        
        if tipo in ['ollama', 'lmstudio']:
            if not api_url:
                self.add_error('api_url', 
                    f'URL del servicio requerida para {dict(ProveedorIA.TIPO_PROVEEDOR)[tipo]}'
                )
        
        # Validar modelo
        if not modelo:
            self.add_error('modelo', 'El modelo es requerido')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # IMPORTANTE: Manejar API Key según checkbox
        usar_env = self.cleaned_data.get('usar_env_api_key', False)
        tipo = self.cleaned_data.get('tipo', '')
        
        if usar_env and tipo:
            # Copiar API key del .env a la base de datos
            import os
            env_key = f"{tipo.upper()}_API_KEY"
            api_key_value = os.environ.get(env_key, '')
            
            if api_key_value:
                # Guardar la API key del .env en la instancia
                instance.api_key = api_key_value
                print(f"✅ API Key copiada del .env para {tipo}: {env_key[:10]}...")
            else:
                # Si no hay valor en .env, usar una cadena especial que indique esto
                instance.api_key = f"ENV_{env_key}_NOT_FOUND"
                print(f"⚠️  No se encontró {env_key} en .env")
        elif not usar_env:
            # Si no usa .env, mantener la API key personalizada proporcionada
            # (esto ya viene en instance.api_key del super().save())
            print(f"✅ Usando API Key personalizada para {tipo}")
        
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

    def clean_search(self):
        search = self.cleaned_data.get('search')
        tipo_acta = self.cleaned_data.get('tipo_acta')
        
        # Si hay búsqueda por texto, validar que no haya otros filtros
        if search and (tipo_acta or self.cleaned_data.get('activa')):
            raise ValidationError("Si se especifica una búsqueda por texto, no debe haber otros filtros aplicados")
        
        return search

    def clean_fecha_desde(self):
        fecha_desde = self.cleaned_data.get('fecha_desde')
        fecha_hasta = self.cleaned_data.get('fecha_hasta')
        
        # Validar rango de fechas
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'")
        
        return fecha_desde
    
    def clean_fecha_hasta(self):
        fecha_hasta = self.cleaned_data.get('fecha_hasta')
        fecha_desde = self.cleaned_data.get('fecha_desde')
        
        # Validar rango de fechas
        if fecha_hasta and fecha_desde and fecha_hasta < fecha_desde:
            raise ValidationError("La fecha 'Hasta' no puede ser menor que la fecha 'Desde'")
        
        return fecha_hasta


# ==================== FORMULARIOS PARA SEGMENTOS DE PLANTILLA ====================

class SegmentoPlantillaForm(forms.ModelForm):
    """Formulario para crear y editar segmentos de plantilla"""
    
    class Meta:
        model = SegmentoPlantilla
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria', 'tipo',
            'prompt_ia', 'proveedor_ia', 'estructura_json', 'componentes',
            'parametros_entrada', 'variables_personalizadas',
            'orden_defecto', 'reutilizable', 'obligatorio', 'activo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del segmento (ej: ENCAB_001)'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo del segmento'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el propósito y función de este segmento'
            }),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleCamposIA(this.value)'
            }),
            'prompt_ia': forms.Textarea(attrs={
                'class': 'form-control prompt-field',
                'rows': 8,
                'placeholder': 'Prompt para procesamiento con IA (solo para segmentos dinámicos)'
            }),
            'proveedor_ia': forms.Select(attrs={
                'class': 'form-control proveedor-field'
            }),
            'estructura_json': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 6,
                'placeholder': '{"campo1": "valor", "campo2": ["lista", "valores"]}'
            }),
            'componentes': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 4,
                'placeholder': '{"texto": "contenido", "variables": ["var1", "var2"]}'
            }),
            'parametros_entrada': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 3,
                'placeholder': '["param1", "param2", "param3"]'
            }),
            'variables_personalizadas': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 5,
                'placeholder': '{"fecha": "2025-01-01", "lugar": "Sala Principal"}'
            }),
            'orden_defecto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1'
            }),
            'reutilizable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'obligatorio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo proveedores IA activos
        self.fields['proveedor_ia'].queryset = ProveedorIA.objects.filter(activo=True)
        self.fields['proveedor_ia'].required = False
        
        # Configurar campos requeridos según el tipo
        if self.instance and self.instance.pk:
            if self.instance.es_dinamico:
                self.fields['prompt_ia'].required = True
                self.fields['proveedor_ia'].required = True
    
    def clean_estructura_json(self):
        """Validar que el JSON de estructura sea válido"""
        estructura = self.cleaned_data.get('estructura_json')
        if estructura:
            try:
                if isinstance(estructura, str):
                    json.loads(estructura)
            except json.JSONDecodeError:
                raise ValidationError("La estructura JSON no es válida")
        return estructura
    
    def clean_componentes(self):
        """Validar que el JSON de componentes sea válido"""
        componentes = self.cleaned_data.get('componentes')
        if componentes:
            try:
                if isinstance(componentes, str):
                    json.loads(componentes)
            except json.JSONDecodeError:
                raise ValidationError("Los componentes JSON no son válidos")
        return componentes
    
    def clean_parametros_entrada(self):
        """Validar que los parámetros de entrada sean válidos"""
        parametros = self.cleaned_data.get('parametros_entrada')
        if parametros:
            try:
                if isinstance(parametros, str):
                    parsed = json.loads(parametros)
                    if not isinstance(parsed, list):
                        raise ValidationError("Los parámetros de entrada deben ser una lista")
            except json.JSONDecodeError:
                raise ValidationError("Los parámetros de entrada JSON no son válidos")
        return parametros
    
    def clean_variables_personalizadas(self):
        """Validar que las variables personalizadas sean válidas"""
        variables = self.cleaned_data.get('variables_personalizadas')
        if variables:
            try:
                if isinstance(variables, str):
                    parsed = json.loads(variables)
                    if not isinstance(parsed, dict):
                        raise ValidationError("Las variables personalizadas deben ser un objeto JSON")
            except json.JSONDecodeError:
                raise ValidationError("Las variables personalizadas JSON no son válidas")
        return variables
    
    def clean(self):
        """Validación global del formulario"""
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        prompt_ia = cleaned_data.get('prompt_ia')
        proveedor_ia = cleaned_data.get('proveedor_ia')
        
        # Validaciones para segmentos dinámicos
        if tipo in ['dinamico', 'hibrido']:
            if not prompt_ia or not prompt_ia.strip():
                self.add_error('prompt_ia', 'El prompt IA es obligatorio para segmentos dinámicos')
            
            if not proveedor_ia:
                self.add_error('proveedor_ia', 'Debe seleccionar un proveedor IA para segmentos dinámicos')
        
        return cleaned_data


class SegmentoFiltroForm(forms.Form):
    """Formulario para filtrar segmentos de plantilla"""
    
    ORDENAMIENTO_CHOICES = [
        ('nombre', 'Nombre (A-Z)'),
        ('-nombre', 'Nombre (Z-A)'),
        ('categoria', 'Categoría (A-Z)'),
        ('-categoria', 'Categoría (Z-A)'),
        ('tipo', 'Tipo (A-Z)'),
        ('-tipo', 'Tipo (Z-A)'),
        ('total_usos', 'Menos usados'),
        ('-total_usos', 'Más usados'),
        ('fecha_creacion', 'Más antiguos'),
        ('-fecha_creacion', 'Más recientes'),
        ('fecha_actualizacion', 'Menos actualizados'),
        ('-fecha_actualizacion', 'Más actualizados'),
        ('orden_defecto', 'Orden por defecto'),
        ('-tiempo_promedio_procesamiento', 'Más lentos'),
        ('tiempo_promedio_procesamiento', 'Más rápidos'),
    ]
    
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, código o descripción...'
        })
    )
    
    categoria = forms.ChoiceField(
        choices=[('', 'Todas las categorías')] + SegmentoPlantilla.CATEGORIA_SEGMENTO,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tipo = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + SegmentoPlantilla.TIPO_SEGMENTO,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    proveedor_ia = forms.ModelChoiceField(
        queryset=ProveedorIA.objects.filter(activo=True),
        required=False,
        empty_label="Todos los proveedores",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    activo = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reutilizable = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Reutilizables'), ('false', 'No reutilizables')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    obligatorio = forms.ChoiceField(
        choices=[('', 'Todos'), ('true', 'Obligatorios'), ('false', 'Opcionales')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    ordenar_por = forms.ChoiceField(
        choices=ORDENAMIENTO_CHOICES,
        initial='-fecha_actualizacion',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class PruebaSegmentoForm(forms.Form):
    """Formulario para probar segmentos de plantilla"""
    
    segmento = forms.ModelChoiceField(
        queryset=SegmentoPlantilla.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Selecciona el segmento a probar"
    )
    
    datos_contexto = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': '''Ejemplo de datos de contexto:
{
    "fecha_reunion": "2025-01-15",
    "participantes": ["Juan Pérez", "María García", "Carlos López"],
    "lugar": "Sala de Juntas Principal",
    "hora_inicio": "09:00",
    "temas": ["Presupuesto 2025", "Nuevos proyectos"],
    "tipo_reunion": "Ordinaria"
}'''
        }),
        help_text="Datos de contexto en formato JSON para la prueba"
    )
    
    usar_celery = forms.BooleanField(
        initial=False,
        required=False,
        help_text="Procesar con Celery (asíncrono) en lugar de procesamiento directo"
    )
    
    incluir_metricas = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Incluir métricas de tiempo y actualizar estadísticas del segmento"
    )
    
    def clean_datos_contexto(self):
        """Validar que los datos de contexto sean JSON válido"""
        datos = self.cleaned_data.get('datos_contexto')
        if datos:
            try:
                parsed_data = json.loads(datos)
                if not isinstance(parsed_data, dict):
                    raise ValidationError("Los datos de contexto deben ser un objeto JSON")
                return parsed_data
            except json.JSONDecodeError as e:
                raise ValidationError(f"JSON inválido: {str(e)}")
        return {}
    
    def clean(self):
        """Validación global del formulario"""
        cleaned_data = super().clean()
        segmento = cleaned_data.get('segmento')
        
        if segmento and segmento.es_dinamico and not segmento.esta_configurado:
            raise ValidationError(
                f"El segmento '{segmento.nombre}' no está correctamente configurado para pruebas dinámicas"
            )
        
        return cleaned_data


class VariablesSegmentoForm(forms.Form):
    """Formulario para definir variables de segmento de forma asistida"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar campos dinámicos para variables comunes
        variables_comunes = SegmentoPlantilla.obtener_variables_comunes()
        
        for var_name, var_info in variables_comunes.items():
            field_name = f"incluir_{var_name}"
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=f"Incluir {var_name}",
                help_text=f"{var_info['descripcion']} (Ej: {var_info['ejemplo']})"
            )
            
            # Campo para valor por defecto
            default_field_name = f"default_{var_name}"
            if var_info['tipo'] == 'date':
                self.fields[default_field_name] = forms.DateField(
                    required=False,
                    widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
                    label=f"Valor por defecto para {var_name}"
                )
            elif var_info['tipo'] == 'time':
                self.fields[default_field_name] = forms.TimeField(
                    required=False,
                    widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
                    label=f"Valor por defecto para {var_name}"
                )
            elif var_info['tipo'] == 'array':
                self.fields[default_field_name] = forms.CharField(
                    required=False,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                    label=f"Valores por defecto para {var_name} (JSON array)",
                    help_text=f"Ejemplo: {json.dumps(var_info['ejemplo'])}"
                )
            else:
                self.fields[default_field_name] = forms.CharField(
                    required=False,
                    widget=forms.TextInput(attrs={'class': 'form-control'}),
                    label=f"Valor por defecto para {var_name}"
                )
    
    variables_adicionales = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': '{"variable_custom": "valor", "otra_variable": ["lista", "valores"]}'
        }),
        help_text="Variables adicionales personalizadas en formato JSON"
    )
    
    def clean_variables_adicionales(self):
        """Validar variables adicionales"""
        variables = self.cleaned_data.get('variables_adicionales')
        if variables and variables.strip():
            try:
                parsed = json.loads(variables)
                if not isinstance(parsed, dict):
                    raise ValidationError("Las variables adicionales deben ser un objeto JSON")
                return parsed
            except json.JSONDecodeError:
                raise ValidationError("JSON inválido en variables adicionales")
        return {}
    
    def get_variables_json(self):
        """Genera el JSON de variables basado en los campos seleccionados"""
        if not self.is_valid():
            return {}
            
        variables = {}
        variables_comunes = SegmentoPlantilla.obtener_variables_comunes()
        
        for var_name, var_info in variables_comunes.items():
            incluir_field = f"incluir_{var_name}"
            default_field = f"default_{var_name}"
            
            if self.cleaned_data.get(incluir_field, False):
                default_value = self.cleaned_data.get(default_field)
                if default_value:
                    if var_info['tipo'] == 'array' and isinstance(default_value, str):
                        try:
                            default_value = json.loads(default_value)
                        except:
                            default_value = var_info['ejemplo']
                    elif var_info['tipo'] in ['date', 'time']:
                        default_value = str(default_value)
                    
                    variables[var_name] = default_value
                else:
                    variables[var_name] = var_info['ejemplo']
        
        # Agregar variables adicionales
        variables_adicionales = self.cleaned_data.get('variables_adicionales', {})
        if variables_adicionales:
            variables.update(variables_adicionales)
        
        return variables