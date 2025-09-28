"""
Formularios para el módulo generador de actas
Incluye formularios dinámicos e inteligentes para proveedores de IA
"""
import json
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import (
    ActaGenerada, PlantillaActa, SegmentoPlantilla, ConfiguracionSegmento, ProveedorIA,
    EjecucionPlantilla, ResultadoSegmento, ActaBorrador
)





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
    Formulario completo para crear y editar actas generadas
    """
    class Meta:
        model = ActaGenerada
        fields = [
            'numero_acta', 'titulo', 'plantilla', 'transcripcion', 'proveedor_ia'
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
            'plantilla': forms.Select(attrs={'class': 'form-control'}),
            'transcripcion': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccionar transcripción...'
            }),
            'proveedor_ia': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccionar proveedor IA...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo plantillas activas
        self.fields['plantilla'].queryset = PlantillaActa.objects.filter(activa=True)
        
        # Filtrar solo proveedores activos
        self.fields['proveedor_ia'].queryset = ProveedorIA.objects.filter(activo=True)
        
        # Filtrar solo transcripciones completadas
        from apps.transcripcion.models import Transcripcion
        self.fields['transcripcion'].queryset = Transcripcion.objects.filter(
            estado='completado'  # Cambiado de 'completada' a 'completado'
        ).order_by('-fecha_creacion')
        
        # Configurar campos opcionales
        self.fields['numero_acta'].required = False
        self.fields['transcripcion'].empty_label = "Seleccionar transcripción..."
        self.fields['proveedor_ia'].empty_label = "Seleccionar proveedor IA..."
        
        # Ayudas contextuales
        self.fields['transcripcion'].help_text = "Transcripción de audio que será procesada para generar el acta"
        self.fields['proveedor_ia'].help_text = "Proveedor de IA que procesará la transcripción"


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
    """Formulario mejorado y user-friendly para crear y editar segmentos de plantilla"""
    
    # Campo personalizado para estructura JSON
    estructura_json_helper = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': '''Ejemplo de estructura JSON esperada:
{
  "titulo": "string",
  "cuerpo": "string", 
  "integrantes": ["string"],
  "votaciones": [
    {"tema": "string", "resultado": "string"}
  ]
}'''
        }),
        help_text="Define la estructura JSON que esperas recibir de la IA (opcional pero recomendado)"
    )
    
    class Meta:
        model = SegmentoPlantilla
        fields = [
            # Identificación básica
            'codigo', 'nombre', 'descripcion', 'categoria', 'tipo',
            
            # Configuración de contenido estático
            'contenido_estatico', 'formato_salida',
            
            # Configuración de IA (dinámicos)
            'prompt_ia', 'prompt_sistema', 'proveedor_ia',
            
            # Estructura y validación
            'estructura_json', 'validaciones_salida', 'formato_validacion',
            
            # Configuración de entrada
            'parametros_entrada', 'variables_personalizadas', 'contexto_requerido',
            
            # Comportamiento
            'orden_defecto', 'reutilizable', 'obligatorio', 'activo',
            
            # Configuraciones avanzadas
            'longitud_maxima', 'tiempo_limite_ia', 'reintentos_ia'
        ]
        widgets = {
            # Identificación básica - Mejorada
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: TITULO_ACTA, PARTICIPANTES, RESUMEN_EJECUTIVO',
                'pattern': '[A-Z0-9_]+',
                'title': 'Solo mayúsculas, números y guiones bajos',
                'data-toggle': 'tooltip',
                'data-placement': 'top',
                'data-original-title': 'Código único que identifica al segmento'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título descriptivo y claro del segmento',
                'maxlength': '200'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Explica brevemente qué hace este segmento y cuándo se usa'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control',
                'data-toggle': 'tooltip',
                'data-placement': 'top',
                'data-original-title': 'Estático: texto fijo | Dinámico: procesado con IA | Híbrido: ambos'
            }),
            
            # Contenido estático - MEJORADO
            'contenido_estatico': forms.Textarea(attrs={
                'class': 'form-control contenido-estatico-field',
                'rows': 10,
                'placeholder': '''📝 Contenido estático del segmento:

• Usa {{variables}} para datos dinámicos como {{fecha}}, {{numero_acta}}
• Puedes usar formato HTML básico: <strong>, <em>, <br>
• Para centrar texto: <center>contenido</center>
• Para listas: <ul><li>item</li></ul>

Ejemplo completo:
<center><strong>ACTA N° {{numero_acta}}</strong></center>
<br>
Reunión: {{tipo_reunion}}
Fecha: {{fecha}}
<br>
Participantes:
{{lista_participantes}}''',
                'data-toggle': 'tooltip',
                'data-placement': 'top',
                'data-html': 'true',
                'data-original-title': 'Contenido fijo con variables dinámicas {{}} y HTML básico'
            }),
            'formato_salida': forms.Select(attrs={
                'class': 'form-control'
            }),
            
            # Configuración IA - MEJORADO
            'prompt_ia': forms.Textarea(attrs={
                'class': 'form-control prompt-ia-field',
                'rows': 12,
                'placeholder': '''🤖 Prompt para IA (Instrucciones claras y específicas):

IMPORTANTE: Siempre termina con esta instrucción:
"Responde únicamente en formato JSON válido, sin contexto adicional, sin explicaciones, sin resúmenes, directamente el JSON estructurado."

Ejemplo de prompt completo:

---
Analiza la transcripción adjunta y genera el segmento de participantes del acta municipal.

Necesito:
- titulo: Título de la sección (ej: "PARTICIPANTES")
- cuerpo: Lista detallada de participantes con sus roles
- integrantes: Array de nombres completos
- votaciones: Si hubo votaciones, incluir tema y resultado

Usa la información de la transcripción para extraer nombres, cargos y roles de cada participante.

Responde únicamente en formato JSON válido, sin contexto adicional, sin explicaciones, sin resúmenes, directamente el JSON estructurado.
---''',
                'data-toggle': 'tooltip',
                'data-placement': 'top',
                'data-html': 'true',
                'data-original-title': 'Instrucciones para que la IA genere este segmento. Sé específico sobre qué necesitas.'
            }),
            'prompt_sistema': forms.Textarea(attrs={
                'class': 'form-control prompt-sistema-field',
                'rows': 4,
                'placeholder': 'Prompt de sistema específico (opcional). Override del prompt global del proveedor.'
            }),
            'proveedor_ia': forms.Select(attrs={
                'class': 'form-control proveedor-ia-field'
            }),
            
            # Estructura y validación
            'estructura_json': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 6,
                'placeholder': 'Estructura esperada del resultado (JSON):\n\n{\n  "titulo": "string",\n  "contenido": "text",\n  "items": ["lista", "elementos"]\n}'
            }),
            'validaciones_salida': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 4,
                'placeholder': 'Validaciones a aplicar:\n\n[\n  {"tipo": "longitud_minima", "valor": 50},\n  {"tipo": "contiene_texto", "valor": "ACTA"}\n]'
            }),
            'formato_validacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Patrón regex (opcional): ^[A-Z].*\\.$'
            }),
            
            # Configuración de entrada
            'parametros_entrada': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 4,
                'placeholder': 'Parámetros requeridos:\n\n["transcripcion", "participantes", "fecha", "lugar"]'
            }),
            'variables_personalizadas': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 5,
                'placeholder': 'Variables personalizables:\n\n{\n  "municipio": "Pastaza",\n  "provincia": "Pastaza",\n  "cargo_autoridad": "Alcalde"\n}'
            }),
            'contexto_requerido': forms.Textarea(attrs={
                'class': 'form-control json-field',
                'rows': 3,
                'placeholder': '["audio_transcription", "speaker_diarization", "participants_list"]'
            }),
            
            # Comportamiento
            'orden_defecto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '999',
                'step': '1',
                'placeholder': '0'
            }),
            'reutilizable': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'obligatorio': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            
            # Configuraciones avanzadas
            'longitud_maxima': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1',
                'placeholder': 'Ej: 5000 (caracteres)'
            }),
            'tiempo_limite_ia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '300',
                'step': '5',
                'placeholder': '60'
            }),
            'reintentos_ia': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '5',
                'step': '1',
                'placeholder': '2'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # VALORES INICIALES para campos requeridos
        if not self.instance.pk:  # Solo para nuevos segmentos
            self.fields['formato_salida'].initial = 'html'
            self.fields['orden_defecto'].initial = 10
            self.fields['tiempo_limite_ia'].initial = 60
            self.fields['reintentos_ia'].initial = 2
            self.fields['activo'].initial = True
            self.fields['reutilizable'].initial = True
            self.fields['obligatorio'].initial = False
        
        # Filtrar solo proveedores activos para el campo ModelChoiceField
        self.fields['proveedor_ia'].queryset = ProveedorIA.objects.filter(activo=True)
        self.fields['proveedor_ia'].empty_label = "Seleccionar proveedor IA..."
        
        # Configurar campos requeridos basados en tipo
        if self.instance and self.instance.pk:
            self._configurar_campos_requeridos()
        
        # Ayuda contextual
        self.fields['codigo'].help_text = "Código único identificador (MAYÚSCULAS_CON_GUIONES)"
        self.fields['tipo'].help_text = "Estático: contenido fijo | Dinámico: procesado con IA | Híbrido: ambos"
        self.fields['categoria'].help_text = "Categoría funcional del segmento dentro del acta"
        self.fields['orden_defecto'].help_text = "Orden sugerido en plantillas (menor número = primero)"
        self.fields['tiempo_limite_ia'].help_text = "Tiempo máximo en segundos para procesamiento IA"
        self.fields['reintentos_ia'].help_text = "Número de reintentos en caso de error de IA"
    
    def _configurar_campos_requeridos(self):
        """Configura campos requeridos basado en el tipo de segmento"""
        if hasattr(self.instance, 'es_estatico') and self.instance.es_estatico:
            self.fields['contenido_estatico'].required = True
            self.fields['prompt_ia'].required = False
            self.fields['proveedor_ia'].required = False
        elif hasattr(self.instance, 'es_dinamico') and self.instance.es_dinamico:
            self.fields['prompt_ia'].required = True
            self.fields['proveedor_ia'].required = True
            self.fields['contenido_estatico'].required = False
        elif hasattr(self.instance, 'es_hibrido') and self.instance.es_hibrido:
            self.fields['contenido_estatico'].required = True
            # Prompt IA opcional para híbridos
    
    def clean(self):
        """Validación global del formulario"""
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        contenido_estatico = cleaned_data.get('contenido_estatico', '').strip()
        prompt_ia = cleaned_data.get('prompt_ia', '').strip()
        proveedor_ia = cleaned_data.get('proveedor_ia')
        
        # Validaciones por tipo
        if tipo == 'estatico':
            if not contenido_estatico:
                self.add_error('contenido_estatico', 'Los segmentos estáticos requieren contenido estático.')
        
        elif tipo == 'dinamico':
            if not prompt_ia:
                self.add_error('prompt_ia', 'Los segmentos dinámicos requieren un prompt de IA.')
            if not proveedor_ia:
                self.add_error('proveedor_ia', 'Los segmentos dinámicos requieren un proveedor de IA.')
        
        elif tipo == 'hibrido':
            if not contenido_estatico:
                self.add_error('contenido_estatico', 'Los segmentos híbridos requieren contenido estático base.')
        
        # Validar JSON fields
        campos_json = [
            ('estructura_json', 'estructura_json'),
            ('validaciones_salida', 'validaciones_salida'), 
            ('parametros_entrada', 'parametros_entrada'),
            ('variables_personalizadas', 'variables_personalizadas'),
            ('contexto_requerido', 'contexto_requerido')
        ]
        
        for campo, campo_clean in campos_json:
            valor = cleaned_data.get(campo_clean, '')
            if valor and valor.strip():
                try:
                    json.loads(valor)
                except json.JSONDecodeError as e:
                    self.add_error(campo_clean, f'JSON inválido: {str(e)}')
        
        return cleaned_data
    
    def clean_codigo(self):
        """Validación del código único"""
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        
        if not codigo:
            raise ValidationError("El código es obligatorio")
        
        # Verificar formato
        import re
        if not re.match(r'^[A-Z0-9_]+$', codigo):
            raise ValidationError("El código solo puede contener mayúsculas, números y guiones bajos")
        
        # Verificar unicidad excluyendo la instancia actual
        queryset = SegmentoPlantilla.objects.filter(codigo=codigo)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError(f"Ya existe un segmento con el código '{codigo}'")
        
        return codigo
    
    def clean_longitud_maxima(self):
        """Validación de longitud máxima"""
        longitud = self.cleaned_data.get('longitud_maxima')
        if longitud is not None and longitud <= 0:
            raise ValidationError("La longitud máxima debe ser mayor que 0")
        return longitud
    
    def clean_tiempo_limite_ia(self):
        """Validación del tiempo límite de IA"""
        tiempo = self.cleaned_data.get('tiempo_limite_ia', 60)
        if tiempo < 10 or tiempo > 300:
            raise ValidationError("El tiempo límite debe estar entre 10 y 300 segundos")
        return tiempo
    
    def clean_reintentos_ia(self):
        """Validación de reintentos de IA"""
        reintentos = self.cleaned_data.get('reintentos_ia', 2)
        if reintentos < 0 or reintentos > 5:
            raise ValidationError("Los reintentos deben estar entre 0 y 5")
        return reintentos
    
    def save(self, commit=True):
        """Guardar con procesamiento adicional y valores por defecto"""
        instance = super().save(commit=False)
        
        # VALORES POR DEFECTO para campos requeridos
        if not hasattr(instance, 'formato_salida') or not instance.formato_salida:
            instance.formato_salida = 'html'
        
        if not hasattr(instance, 'orden_defecto') or instance.orden_defecto is None:
            instance.orden_defecto = 10
        
        if not hasattr(instance, 'tiempo_limite_ia') or instance.tiempo_limite_ia is None:
            instance.tiempo_limite_ia = 60
        
        if not hasattr(instance, 'reintentos_ia') or instance.reintentos_ia is None:
            instance.reintentos_ia = 2
        
        # Normalizar campos JSON vacíos
        if not instance.estructura_json:
            instance.estructura_json = {}
        if not instance.validaciones_salida:
            instance.validaciones_salida = []
        if not instance.parametros_entrada:
            instance.parametros_entrada = []
        if not instance.variables_personalizadas:
            instance.variables_personalizadas = {}
        if not instance.contexto_requerido:
            instance.contexto_requerido = []
        
        # Limpiar campos según tipo
        if instance.tipo == 'estatico':
            instance.prompt_ia = ''
            instance.prompt_sistema = ''
            instance.proveedor_ia = None
        elif instance.tipo == 'dinamico':
            instance.contenido_estatico = ''
        
        if commit:
            instance.save()
            
        return instance


class SegmentoFiltroForm(forms.Form):
    """Formulario mejorado para filtrar y buscar segmentos de plantilla"""
    
    ORDENAMIENTO_CHOICES = [
        ('nombre', 'Nombre (A-Z)'),
        ('-nombre', 'Nombre (Z-A)'),
        ('categoria', 'Categoría'),
        ('-fecha_actualizacion', 'Más recientes'),
        ('fecha_creacion', 'Más antiguos'),
        ('-total_usos', 'Más usados'),
        ('total_usos', 'Menos usados'),
        ('-tasa_exito', 'Mayor tasa éxito'),
        ('tiempo_promedio_procesamiento', 'Más rápidos'),
        ('orden_defecto', 'Orden por defecto'),
    ]
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('true', 'Solo activos'),
        ('false', 'Solo inactivos'),
    ]
    
    REUTILIZABLE_CHOICES = [
        ('', 'Todos'),
        ('true', 'Reutilizables'),
        ('false', 'No reutilizables'),
    ]
    
    SALUD_CHOICES = [
        ('', 'Todos'),
        ('excelente', 'Excelente'),
        ('bueno', 'Bueno'),
        ('regular', 'Regular'),
        ('problematico', 'Problemático'),
        ('sin_uso', 'Sin uso'),
    ]
    
    # Búsqueda
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, código o descripción...',
            'data-toggle': 'tooltip',
            'data-placement': 'top',
            'title': 'Busca en nombre, código y descripción'
        })
    )
    
    # Filtros por categoría
    categoria = forms.ChoiceField(
        required=False,
        choices=[('', 'Todas las categorías')] + SegmentoPlantilla.CATEGORIA_SEGMENTO,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtros por tipo
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos los tipos')] + SegmentoPlantilla.TIPO_SEGMENTO,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro por proveedor IA
    proveedor_ia = forms.ModelChoiceField(
        required=False,
        queryset=ProveedorIA.objects.filter(activo=True),
        empty_label="Todos los proveedores",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtros de estado
    activo = forms.ChoiceField(
        required=False,
        choices=ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    reutilizable = forms.ChoiceField(
        required=False,
        choices=REUTILIZABLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    obligatorio = forms.ChoiceField(
        required=False,
        choices=REUTILIZABLE_CHOICES,  # Misma estructura
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtro por estado de salud
    estado_salud = forms.ChoiceField(
        required=False,
        choices=SALUD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Filtros por uso
    solo_con_errores = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    solo_sin_uso = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    configuracion_incompleta = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Ordenamiento
    ordenar_por = forms.ChoiceField(
        required=False,
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


# ============================================================================
# FORMULARIOS PARA PLANTILLAS - MÓDULO COMPLETO DE EJECUCIÓN
# ============================================================================

class PlantillaBasicaForm(forms.ModelForm):
    """Formulario para datos básicos de plantilla"""
    
    class Meta:
        model = PlantillaActa
        fields = ['codigo', 'nombre', 'descripcion', 'tipo_acta', 'prompt_global', 
                  'proveedor_ia_defecto', 'activa', 'version']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único (ej: PLANTILLA-ORD-001)'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo de la plantilla'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del propósito y uso de esta plantilla'
            }),
            'tipo_acta': forms.Select(attrs={'class': 'form-control'}),
            'prompt_global': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Prompt para la unificación final del acta. Use {segmentos} para incluir los resultados procesados.'
            }),
            'proveedor_ia_defecto': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccionar proveedor IA por defecto'
            }),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '1.0'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor_ia_defecto'].queryset = ProveedorIA.objects.filter(activo=True)
        self.fields['proveedor_ia_defecto'].empty_label = "Sin proveedor por defecto"
        
        # Ayudas contextuales
        self.fields['prompt_global'].help_text = """
        Prompt para unificar todos los segmentos procesados. Variables disponibles:<br>
        • {segmentos} - Resultados de todos los segmentos<br>
        • {transcripcion} - Transcripción original<br>
        • {fecha} - Fecha de la sesión<br>
        • {participantes} - Lista de participantes
        """


class PlantillaSegmentosForm(forms.Form):
    """Formulario para gestión drag & drop de segmentos"""
    segmentos_seleccionados = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        help_text="JSON con la configuración de segmentos"
    )
    
    def __init__(self, *args, **kwargs):
        plantilla = kwargs.pop('plantilla', None)
        super().__init__(*args, **kwargs)
        
        # Preparar datos para el frontend
        if plantilla:
            configuraciones = plantilla.segmentos_ordenados
            segmentos_data = []
            for config in configuraciones:
                segmentos_data.append({
                    'id': config.segmento.id,
                    'nombre': config.segmento.nombre,
                    'tipo': config.segmento.tipo,
                    'categoria': config.segmento.categoria,
                    'orden': config.orden,
                    'obligatorio': config.obligatorio,
                    'variables_personalizadas': config.variables_personalizadas
                })
            
            self.initial['segmentos_seleccionados'] = json.dumps(segmentos_data)
    
    def clean_segmentos_seleccionados(self):
        """Valida y procesa la configuración de segmentos"""
        segmentos_json = self.cleaned_data.get('segmentos_seleccionados', '[]')
        
        try:
            segmentos_data = json.loads(segmentos_json)
        except json.JSONDecodeError:
            raise ValidationError("Formato de datos de segmentos inválido")
        
        if not isinstance(segmentos_data, list):
            raise ValidationError("Los datos de segmentos deben ser una lista")
        
        # Validar estructura de cada segmento
        for i, segmento in enumerate(segmentos_data):
            required_fields = ['id', 'orden']
            for field in required_fields:
                if field not in segmento:
                    raise ValidationError(f"El segmento {i+1} no tiene el campo requerido: {field}")
            
            # Verificar que el segmento existe
            try:
                SegmentoPlantilla.objects.get(id=segmento['id'])
            except SegmentoPlantilla.DoesNotExist:
                raise ValidationError(f"El segmento con ID {segmento['id']} no existe")
        
        return segmentos_data


class PlantillaConfiguracionForm(forms.Form):
    """Formulario para configuración avanzada de la plantilla"""
    configuracion_procesamiento = forms.JSONField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Configuración adicional en formato JSON'
        }),
        help_text="Configuración avanzada de procesamiento (JSON)"
    )
    
    variables_globales = forms.JSONField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '{"variable": "valor"}'
        }),
        help_text="Variables globales disponibles para todos los segmentos"
    )
    
    timeout_global = forms.IntegerField(
        required=False,
        initial=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '30',
            'max': '1800'
        }),
        help_text="Timeout global en segundos (30-1800)"
    )
    
    reintentos_maximos = forms.IntegerField(
        required=False,
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '10'
        }),
        help_text="Número máximo de reintentos por segmento"
    )


class PlantillaEjecucionForm(forms.ModelForm):
    """Formulario para iniciar ejecución de plantilla"""
    
    class Meta:
        model = EjecucionPlantilla
        fields = ['nombre', 'transcripcion', 'proveedor_ia_global', 'variables_contexto']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre para esta ejecución (ej: Acta Sesión Ordinaria 2025-01-15)'
            }),
            'transcripcion': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': 'Seleccionar transcripción procesada'
            }),
            'proveedor_ia_global': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccionar IA para todos los segmentos'
            }),
            'variables_contexto': forms.Textarea(attrs={
                'class': 'form-control json-textarea',
                'rows': 6,
                'placeholder': '{"fecha_sesion": "2025-01-15", "lugar": "Sala de Sesiones", "tipo_reunion": "Ordinaria"}'
            })
        }
    
    def __init__(self, *args, **kwargs):
        plantilla = kwargs.pop('plantilla', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar transcripciones completadas
        from apps.audio_processing.models import ProcesamientoAudio
        self.fields['transcripcion'].queryset = ProcesamientoAudio.objects.filter(
            estado='completado'
        ).order_by('-created_at')
        
        # Filtrar proveedores activos
        self.fields['proveedor_ia_global'].queryset = ProveedorIA.objects.filter(activo=True)
        
        # Pre-llenar con proveedor por defecto
        if plantilla and plantilla.proveedor_ia_defecto:
            self.fields['proveedor_ia_global'].initial = plantilla.proveedor_ia_defecto
        
        # Ayudas y validaciones
        self.fields['transcripcion'].help_text = "Transcripción que se usará como fuente de datos para todos los segmentos"
        self.fields['proveedor_ia_global'].help_text = "Este proveedor procesará TODOS los segmentos dinámicos"
        self.fields['variables_contexto'].help_text = """
        Variables específicas para esta ejecución (JSON). Ejemplos:<br>
        • fecha_sesion, lugar, tipo_reunion<br>
        • participantes, presidente, secretario<br>
        • numero_acta, departamento
        """
    
    def clean_variables_contexto(self):
        """Valida que las variables de contexto sean JSON válido"""
        variables = self.cleaned_data.get('variables_contexto', '{}')
        
        if not variables:
            return {}
        
        try:
            if isinstance(variables, str):
                variables_dict = json.loads(variables)
            else:
                variables_dict = variables
        except (json.JSONDecodeError, TypeError):
            raise ValidationError("Las variables de contexto deben ser un JSON válido")
        
        if not isinstance(variables_dict, dict):
            raise ValidationError("Las variables de contexto deben ser un objeto JSON")
        
        return variables_dict


class SegmentoResultadoForm(forms.ModelForm):
    """Formulario para editar resultados de segmentos"""
    
    class Meta:
        model = ResultadoSegmento
        fields = ['resultado_editado', 'notas_edicion']
        widgets = {
            'resultado_editado': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'id': 'editor-tinymce'
            }),
            'notas_edicion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas sobre los cambios realizados...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-llenar con el resultado actual
        if self.instance and self.instance.pk:
            self.fields['resultado_editado'].initial = self.instance.resultado_final
            
        self.fields['resultado_editado'].help_text = """
        Editor de contenido del segmento. Puede editar libremente el texto generado por IA.
        """
        self.fields['notas_edicion'].help_text = "Opcional: Notas sobre los cambios realizados"


class ActaBorradorForm(forms.ModelForm):
    """Formulario para editar acta borrador final"""
    
    class Meta:
        model = ActaBorrador
        fields = ['titulo', 'numero_acta', 'fecha_acta', 'lugar_sesion', 
                  'participantes', 'contenido_html', 'resumen_ejecutivo', 
                  'comentarios_revision']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título del acta'
            }),
            'numero_acta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número oficial del acta (auto-generado si vacío)'
            }),
            'fecha_acta': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'lugar_sesion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Lugar donde se realizó la sesión'
            }),
            'participantes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '["Participante 1", "Participante 2"]'
            }),
            'contenido_html': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 20,
                'id': 'editor-acta-final'
            }),
            'resumen_ejecutivo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Resumen ejecutivo de los puntos principales...'
            }),
            'comentarios_revision': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comentarios de revisión...'
            })
        }
    
    def clean_participantes(self):
        """Valida que participantes sea una lista JSON válida"""
        participantes = self.cleaned_data.get('participantes', '[]')
        
        if isinstance(participantes, str):
            try:
                participantes_list = json.loads(participantes)
            except json.JSONDecodeError:
                raise ValidationError("Los participantes deben estar en formato JSON válido")
        else:
            participantes_list = participantes
        
        if not isinstance(participantes_list, list):
            raise ValidationError("Los participantes deben ser una lista")
        
        return participantes_list


class EjecucionFiltroForm(forms.Form):
    """Formulario para filtrar ejecuciones en el dashboard"""
    
    ESTADO_CHOICES = [('', 'Todos los estados')] + EjecucionPlantilla.ESTADO_EJECUCION
    
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    plantilla = forms.ModelChoiceField(
        queryset=PlantillaActa.objects.filter(activa=True),
        required=False,
        empty_label="Todas las plantillas",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    usuario = forms.ModelChoiceField(
        queryset=None,  # Se define en __init__
        required=False,
        empty_label="Todos los usuarios",
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
    
    def __init__(self, *args, **kwargs):
        from django.contrib.auth.models import User
        super().__init__(*args, **kwargs)
        self.fields['usuario'].queryset = User.objects.filter(
            ejecuciones_plantillas__isnull=False
        ).distinct().order_by('username')