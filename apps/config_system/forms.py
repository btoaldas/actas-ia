from django import forms
from django.core.exceptions import ValidationError
import json

from .models import ConfiguracionWhisper, ConfiguracionIA


class ConfiguracionWhisperForm(forms.ModelForm):
    """Formulario para configuración de Whisper"""
    
    class Meta:
        model = ConfiguracionWhisper
        fields = [
            'nombre', 'activo', 'modelo_whisper', 'idioma', 'temperatura',
            'usar_vad', 'usar_pyannote', 'modelo_pyannote', 'min_speakers', 
            'max_speakers', 'tiene_failover', 'failover_metodo'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Whisper Principal'
            }),
            'modelo_whisper': forms.Select(attrs={'class': 'form-control'}),
            'idioma': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'es, en, fr, etc.'
            }),
            'temperatura': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '1'
            }),
            'modelo_pyannote': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'pyannote/speaker-diarization-3.1'
            }),
            'min_speakers': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'max_speakers': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20'
            }),
            'failover_metodo': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar clases CSS a checkboxes
        for field_name in ['activo', 'usar_vad', 'usar_pyannote', 'tiene_failover']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-check-input'
            })
    
    def clean_temperatura(self):
        temperatura = self.cleaned_data.get('temperatura')
        if temperatura < 0 or temperatura > 1:
            raise ValidationError('La temperatura debe estar entre 0 y 1')
        return temperatura
    
    def clean(self):
        cleaned_data = super().clean()
        min_speakers = cleaned_data.get('min_speakers')
        max_speakers = cleaned_data.get('max_speakers')
        
        if min_speakers and max_speakers and min_speakers > max_speakers:
            raise ValidationError('El mínimo de speakers no puede ser mayor al máximo')
        
        tiene_failover = cleaned_data.get('tiene_failover')
        failover_metodo = cleaned_data.get('failover_metodo')
        
        if tiene_failover and not failover_metodo:
            raise ValidationError('Si activas failover, debes seleccionar un método')
        
        return cleaned_data


class ConfiguracionIAForm(forms.ModelForm):
    """Formulario para configuración de IA"""
    
    # Campos adicionales para configuraciones específicas
    configuraciones_extra_json = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': '{"custom_param": "value", "another_param": 123}'
        }),
        required=False,
        help_text="Configuraciones adicionales en formato JSON"
    )
    
    class Meta:
        model = ConfiguracionIA
        fields = [
            'nombre', 'proveedor', 'activo', 'es_principal', 'api_key', 
            'base_url', 'modelo', 'temperatura', 'max_tokens', 'top_p',
            'frequency_penalty', 'presence_penalty', 'prompt_sistema',
            'prompt_generacion_acta', 'limite_requests_minuto', 
            'timeout_segundos', 'orden_prioridad'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: OpenAI GPT-4'
            }),
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'api_key': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'sk-...'
            }),
            'base_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'http://localhost:11434 (para Ollama)'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'gpt-4, deepseek-chat, llama2, etc.'
            }),
            'temperatura': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '2'
            }),
            'max_tokens': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'top_p': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0',
                'max': '1'
            }),
            'frequency_penalty': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '-2',
                'max': '2'
            }),
            'presence_penalty': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '-2',
                'max': '2'
            }),
            'prompt_sistema': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'prompt_generacion_acta': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'limite_requests_minuto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'timeout_segundos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5'
            }),
            'orden_prioridad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar clases CSS a checkboxes
        for field_name in ['activo', 'es_principal']:
            self.fields[field_name].widget.attrs.update({
                'class': 'form-check-input'
            })
        
        # Prellenar configuraciones extra si existen
        if self.instance and self.instance.pk and self.instance.configuraciones_extra:
            self.fields['configuraciones_extra_json'].initial = json.dumps(
                self.instance.configuraciones_extra, 
                indent=2, 
                ensure_ascii=False
            )
    
    def clean_configuraciones_extra_json(self):
        """Validar que las configuraciones extra sean JSON válido"""
        configuraciones_json = self.cleaned_data.get('configuraciones_extra_json', '').strip()
        
        if not configuraciones_json:
            return {}
        
        try:
            return json.loads(configuraciones_json)
        except json.JSONDecodeError as e:
            raise ValidationError(f'JSON inválido: {str(e)}')
    
    def clean_base_url(self):
        """Validar URL base según el proveedor"""
        base_url = self.cleaned_data.get('base_url', '').strip()
        proveedor = self.cleaned_data.get('proveedor')
        
        if proveedor == 'ollama' and not base_url:
            raise ValidationError('Ollama requiere una URL base (ej: http://localhost:11434)')
        
        return base_url
    
    def clean_api_key(self):
        """Validar API key según el proveedor"""
        api_key = self.cleaned_data.get('api_key', '').strip()
        proveedor = self.cleaned_data.get('proveedor')
        
        if proveedor in ['openai', 'deepseek', 'anthropic'] and not api_key:
            raise ValidationError(f'{proveedor.title()} requiere una API key')
        
        return api_key
    
    def clean_temperatura(self):
        temperatura = self.cleaned_data.get('temperatura')
        if temperatura < 0 or temperatura > 2:
            raise ValidationError('La temperatura debe estar entre 0 y 2')
        return temperatura
    
    def clean_top_p(self):
        top_p = self.cleaned_data.get('top_p')
        if top_p < 0 or top_p > 1:
            raise ValidationError('top_p debe estar entre 0 y 1')
        return top_p
    
    def save(self, commit=True):
        """Guardar configuraciones extra"""
        instance = super().save(commit=False)
        
        # Guardar configuraciones extra
        configuraciones_extra = self.cleaned_data.get('configuraciones_extra_json', {})
        instance.configuraciones_extra = configuraciones_extra
        
        if commit:
            instance.save()
        
        return instance


# ==================== FORMULARIOS DE ADMINISTRACIÓN ====================

class UsuarioCreateForm(forms.ModelForm):
    """Formulario para crear nuevo usuario"""
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        from django.contrib.auth import get_user_model
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError("Las contraseñas no coinciden")
        return password2
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")
        return password1
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UsuarioEditForm(forms.ModelForm):
    """Formulario para editar usuario existente"""
    
    class Meta:
        from django.contrib.auth import get_user_model
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PerfilUsuarioForm(forms.ModelForm):
    """Formulario para gestionar perfiles de usuario"""
    
    class Meta:
        from .models import PerfilUsuario
        model = PerfilUsuario
        fields = [
            'usuario', 'rol', 'departamento', 'cargo', 'telefono', 'extension',
            'limite_procesamiento_diario', 'limite_transcripcion_horas', 'activo'
        ]
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-control'}),
            'departamento': forms.Select(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'extension': forms.TextInput(attrs={'class': 'form-control'}),
            'limite_procesamiento_diario': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'limite_transcripcion_horas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando, no permitir cambiar usuario
        if self.instance.pk:
            self.fields['usuario'].disabled = True
        else:
            # Solo mostrar usuarios sin perfil
            from django.contrib.auth import get_user_model
            from .models import PerfilUsuario
            User = get_user_model()
            usuarios_sin_perfil = User.objects.filter(perfilusuario__isnull=True)
            self.fields['usuario'].queryset = usuarios_sin_perfil


class PermisosDetalladosForm(forms.ModelForm):
    """Formulario para editar permisos detallados"""
    
    class Meta:
        from .models import PermisosDetallados
        model = PermisosDetallados
        exclude = ['perfil', 'fecha_creacion', 'fecha_actualizacion']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Organizar campos por categorías para mejor UX
        self.campos_organizados = {
            'Menús de Navegación': [
                'ver_menu_dashboard', 'ver_menu_transcribir', 'ver_menu_procesar_actas',
                'ver_menu_revisar_actas', 'ver_menu_publicar_actas', 'ver_menu_gestionar_sesiones',
                'ver_menu_configurar_ia', 'ver_menu_configurar_whisper', 'ver_menu_gestionar_usuarios',
                'ver_menu_reportes', 'ver_menu_auditoria', 'ver_menu_transparencia'
            ],
            'Transcripción de Audio': [
                'subir_audio_transcripcion', 'iniciar_transcripcion', 'pausar_transcripcion',
                'cancelar_transcripcion', 'ver_progreso_transcripcion', 'descargar_transcripcion',
                'editar_transcripcion'
            ],
            'Procesamiento con IA': [
                'procesar_con_ia', 'seleccionar_modelo_ia', 'ajustar_parametros_ia',
                'ver_analisis_ia', 'regenerar_con_ia'
            ],
            'Gestión de Actas': [
                'crear_acta_nueva', 'editar_acta_borrador', 'editar_acta_revision',
                'eliminar_acta', 'cambiar_estado_acta', 'asignar_revisor', 'ver_historial_cambios'
            ],
            'Revisión y Aprobación': [
                'revisar_actas', 'aprobar_actas', 'rechazar_actas', 'solicitar_cambios',
                'agregar_comentarios', 'firmar_digitalmente'
            ],
            'Publicación': [
                'publicar_actas', 'despublicar_actas', 'programar_publicacion',
                'gestionar_portal_transparencia'
            ],
            'Gestión de Sesiones': [
                'crear_sesion', 'editar_sesion', 'eliminar_sesion',
                'gestionar_asistentes', 'gestionar_orden_dia'
            ],
            'Configuración del Sistema': [
                'configurar_modelos_ia', 'configurar_whisper', 'probar_configuraciones',
                'ver_logs_sistema'
            ],
            'Administración': [
                'gestionar_perfiles_usuarios', 'asignar_permisos', 'ver_reportes_uso',
                'ver_estadisticas', 'gestionar_respaldos'
            ]
        }
        
        # Aplicar widgets y clases CSS
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs.update({'class': 'form-check-input'})


class FiltroUsuariosForm(forms.Form):
    """Formulario para filtrar usuarios"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por username, nombre, email...'
        })
    )
    estado = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('activo', 'Activos'), ('inactivo', 'Inactivos')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class FiltroPerfilesForm(forms.Form):
    """Formulario para filtrar perfiles"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por usuario, cargo...'
        })
    )
    rol = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    departamento = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Cargar opciones dinámicamente
        from .models import PerfilUsuario
        
        rol_choices = [('', 'Todos los roles')] + list(PerfilUsuario.ROLES)
        self.fields['rol'].choices = rol_choices
        
        departamento_choices = [('', 'Todos los departamentos')] + list(PerfilUsuario.DEPARTAMENTOS)
        self.fields['departamento'].choices = departamento_choices


class AplicarPermisosMasivoForm(forms.Form):
    """Formulario para aplicar permisos masivamente"""
    rol = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    aplicar_a_todos = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        from .models import PerfilUsuario
        rol_choices = [('', 'Seleccionar rol específico')] + list(PerfilUsuario.ROLES)
        self.fields['rol'].choices = rol_choices
