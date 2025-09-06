"""
Formularios para configuración SMTP
Sistema de Actas Municipales - Municipio de Pastaza
"""
from django import forms
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from .models import ConfiguracionSMTP, ConfiguracionEmail
from .smtp_service import smtp_service
import re


class ConfiguracionSMTPForm(forms.ModelForm):
    """Formulario para configurar proveedores SMTP"""
    
    password_smtp = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña SMTP'
        }),
        label="Contraseña SMTP"
    )
    
    class Meta:
        model = ConfiguracionSMTP
        fields = [
            'nombre', 'proveedor', 'activo', 'por_defecto', 'prioridad',
            'servidor_smtp', 'puerto', 'usuario_smtp', 'password_smtp',
            'usa_tls', 'usa_ssl', 'email_remitente', 'nombre_remitente',
            'limite_diario'
        ]
        
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Office 365 Principal'
            }),
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'por_defecto': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prioridad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100
            }),
            'servidor_smtp': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'smtp-mail.outlook.com'
            }),
            'puerto': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 65535
            }),
            'usuario_smtp': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'usuario@puyo.gob.ec'
            }),
            'usa_tls': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'usa_ssl': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_remitente': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'noreply@puyo.gob.ec'
            }),
            'nombre_remitente': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sistema Actas Municipales'
            }),
            'limite_diario': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10000
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si se está editando y hay un proveedor seleccionado, aplicar configuración predefinida
        if self.instance and self.instance.pk and self.instance.proveedor:
            config_predefinida = self.instance.configuracion_predefinida
            if config_predefinida:
                for field, value in config_predefinida.items():
                    if field in self.fields and not self.data.get(field):
                        self.fields[field].initial = value
    
    def clean_email_remitente(self):
        """Valida que el email remitente tenga un dominio válido"""
        email = self.cleaned_data.get('email_remitente')
        if email:
            # Verificar que el dominio sea válido para gobierno
            dominios_validos = ['puyo.gob.ec', 'pastaza.gob.ec', 'gmail.com', 'outlook.com']
            dominio = email.split('@')[1].lower() if '@' in email else ''
            
            if not any(dominio.endswith(d) for d in dominios_validos):
                raise ValidationError(
                    f"Use un dominio institucional válido. Dominios permitidos: {', '.join(dominios_validos)}"
                )
        
        return email
    
    def clean_puerto(self):
        """Valida que el puerto sea apropiado para SMTP"""
        puerto = self.cleaned_data.get('puerto')
        puertos_comunes = [25, 465, 587, 2525]
        
        if puerto not in puertos_comunes:
            self.add_error('puerto', 
                f"Puerto poco común para SMTP. Puertos recomendados: {', '.join(map(str, puertos_comunes))}"
            )
        
        return puerto
    
    def clean(self):
        """Validaciones generales"""
        cleaned_data = super().clean()
        usa_tls = cleaned_data.get('usa_tls')
        usa_ssl = cleaned_data.get('usa_ssl')
        puerto = cleaned_data.get('puerto')
        
        # No se puede usar TLS y SSL al mismo tiempo
        if usa_tls and usa_ssl:
            raise ValidationError("No se puede usar TLS y SSL simultáneamente")
        
        # Validar puerto según tipo de conexión
        if usa_ssl and puerto != 465:
            self.add_error('puerto', 'Para SSL se recomienda el puerto 465')
        elif usa_tls and puerto not in [587, 25]:
            self.add_error('puerto', 'Para TLS se recomienda el puerto 587')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Guarda la configuración y aplica configuración predefinida si es necesaria"""
        instance = super().save(commit=False)
        
        # Aplicar configuración predefinida si es un proveedor conocido
        if instance.proveedor and instance.proveedor != 'custom':
            config_predefinida = instance.configuracion_predefinida
            for field, value in config_predefinida.items():
                if hasattr(instance, field) and not getattr(instance, field, None):
                    setattr(instance, field, value)
        
        if commit:
            instance.save()
        
        return instance


class ConfiguracionEmailForm(forms.ModelForm):
    """Formulario para configuración general de emails"""
    
    class Meta:
        model = ConfiguracionEmail
        fields = [
            'nombre_aplicacion', 'logo_email', 'template_html_base',
            'pie_pagina', 'email_respuesta', 'email_soporte',
            'url_sistema', 'url_publica', 'reintentos_maximos',
            'tiempo_espera_reintento', 'sistema_activo'
        ]
        
        widgets = {
            'nombre_aplicacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sistema de Actas Municipales'
            }),
            'logo_email': forms.FileInput(attrs={'class': 'form-control-file'}),
            'template_html_base': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'style': 'font-family: monospace;'
            }),
            'pie_pagina': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8
            }),
            'email_respuesta': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'noreply@puyo.gob.ec'
            }),
            'email_soporte': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'soporte@puyo.gob.ec'
            }),
            'url_sistema': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'http://localhost:8000'
            }),
            'url_publica': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'http://puyo.gob.ec'
            }),
            'reintentos_maximos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10
            }),
            'tiempo_espera_reintento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 60,
                'max': 3600
            }),
            'sistema_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_template_html_base(self):
        """Valida que el template HTML tenga las variables necesarias"""
        template = self.cleaned_data.get('template_html_base')
        
        variables_requeridas = ['{{contenido}}', '{{asunto}}', '{{nombre_aplicacion}}']
        variables_faltantes = []
        
        for var in variables_requeridas:
            if var not in template:
                variables_faltantes.append(var)
        
        if variables_faltantes:
            raise ValidationError(
                f"El template debe contener las siguientes variables: {', '.join(variables_faltantes)}"
            )
        
        return template
    
    def clean_logo_email(self):
        """Valida el archivo de logo"""
        logo = self.cleaned_data.get('logo_email')
        
        if logo:
            # Verificar tamaño (máximo 2MB)
            if logo.size > 2 * 1024 * 1024:
                raise ValidationError("El logo no puede exceder 2MB")
            
            # Verificar tipo de archivo
            tipos_validos = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if logo.content_type not in tipos_validos:
                raise ValidationError("Solo se permiten imágenes JPG, PNG, GIF o WebP")
        
        return logo


class EmailTestForm(forms.Form):
    """Formulario para enviar emails de prueba"""
    
    email_destino = forms.EmailField(
        label="Email de destino",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'test@puyo.gob.ec'
        })
    )
    
    configuracion_smtp = forms.ModelChoiceField(
        queryset=ConfiguracionSMTP.objects.filter(activo=True),
        label="Configuración SMTP (opcional)",
        required=False,
        empty_label="Usar sistema automático",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    asunto = forms.CharField(
        label="Asunto",
        initial="🧪 Email de Prueba - Sistema Actas Municipales",
        widget=forms.TextInput(attrs={
            'class': 'form-control'
        })
    )
    
    mensaje_personalizado = forms.CharField(
        label="Mensaje personalizado (opcional)",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Mensaje adicional para incluir en la prueba...'
        })
    )
    
    def clean_email_destino(self):
        """Valida el email de destino"""
        email = self.cleaned_data.get('email_destino')
        
        # Validar que no sea un email masivo
        dominios_masivos = ['noreply', 'no-reply', 'donotreply']
        local_part = email.split('@')[0].lower() if '@' in email else ''
        
        if any(dominio in local_part for dominio in dominios_masivos):
            raise ValidationError("No se puede enviar email de prueba a direcciones de no-respuesta")
        
        return email
    
    def enviar_email_prueba(self):
        """Envía el email de prueba"""
        email_destino = self.cleaned_data['email_destino']
        configuracion_smtp = self.cleaned_data.get('configuracion_smtp')
        asunto = self.cleaned_data['asunto']
        mensaje_personalizado = self.cleaned_data.get('mensaje_personalizado', '')
        
        # Preparar contenido con variables ya procesadas
        from django.utils import timezone
        fecha_actual = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        config_nombre = configuracion_smtp.nombre if configuracion_smtp else 'Automática (failover)'
        
        contenido_html = f"""
        <h2>🧪 Email de Prueba</h2>
        <p>Este es un email de prueba del Sistema de Actas Municipales de Pastaza.</p>
        
        {f'<div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;"><h4>📝 Mensaje personalizado:</h4><p>{mensaje_personalizado}</p></div>' if mensaje_personalizado else ''}
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h4>ℹ️ Información del test:</h4>
            <ul>
                <li><strong>Fecha y hora:</strong> {fecha_actual}</li>
                <li><strong>Configuración SMTP:</strong> {config_nombre}</li>
                <li><strong>Email de destino:</strong> {email_destino}</li>
            </ul>
        </div>
        
        <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h4>✅ Funcionalidades verificadas:</h4>
            <ul>
                <li>Conexión SMTP establecida</li>
                <li>Autenticación exitosa</li>
                <li>Envío de email completado</li>
                <li>Template HTML renderizado correctamente</li>
                <li>Variables de template procesadas</li>
            </ul>
        </div>
        """
        
        variables = {
            'fecha_actual': fecha_actual
        }
        
        if configuracion_smtp:
            # Usar configuración específica - ya procesamos el HTML completamente
            return smtp_service._enviar_con_proveedor(
                configuracion_smtp, email_destino, asunto, None, 
                smtp_service._generar_html_desde_template(contenido_html, asunto, variables)
            )
        else:
            # Usar sistema automático
            return smtp_service.enviar_email(
                destinatario=email_destino,
                asunto=asunto,
                contenido=contenido_html,
                es_html=True,
                variables_template=variables
            )


class BusquedaLogsForm(forms.Form):
    """Formulario para buscar en los logs de email"""
    
    ESTADOS = [
        ('', 'Todos los estados'),
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('error', 'Error'),
        ('reintentando', 'Reintentando'),
    ]
    
    fecha_desde = forms.DateField(
        required=False,
        label="Fecha desde",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label="Fecha hasta",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    destinatario = forms.CharField(
        required=False,
        label="Destinatario",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@dominio.com'
        })
    )
    
    estado = forms.ChoiceField(
        choices=ESTADOS,
        required=False,
        label="Estado",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    configuracion_smtp = forms.ModelChoiceField(
        queryset=ConfiguracionSMTP.objects.all(),
        required=False,
        label="Configuración SMTP",
        empty_label="Todas las configuraciones",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        """Validaciones del formulario"""
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError("La fecha 'desde' no puede ser mayor que la fecha 'hasta'")
        
        return cleaned_data
