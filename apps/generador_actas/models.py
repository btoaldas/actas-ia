"""
Modelos para el módulo Generador de Actas con IA
Incluye proveedores de IA, segmentos de plantillas, plantillas y actas generadas
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
import json


class ProveedorIA(models.Model):
    """Configuración de proveedores de IA disponibles"""
    TIPO_PROVEEDOR = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic Claude'),
        ('deepseek', 'DeepSeek'),
        ('google', 'Google Gemini'),
        ('ollama', 'Ollama (Local)'),
        ('lmstudio', 'LM Studio (Local)'),
        ('groq', 'Groq'),
        ('generic1', 'Proveedor Genérico 1'),
        ('generic2', 'Proveedor Genérico 2'),
    ]
    
    # Identificación
    nombre = models.CharField(max_length=100, unique=True, help_text="Nombre descriptivo del proveedor")
    tipo = models.CharField(max_length=50, choices=TIPO_PROVEEDOR, help_text="Tipo de proveedor de IA")
    
    # Configuración de API
    api_key = models.CharField(max_length=500, blank=True, help_text="Clave API (se encripta en producción)")
    api_url = models.URLField(blank=True, help_text="URL base de la API")
    modelo = models.CharField(max_length=100, help_text="Modelo específico a usar")
    
    # Parámetros de generación
    temperatura = models.FloatField(default=0.7, help_text="Creatividad del modelo (0-1)")
    max_tokens = models.IntegerField(default=4000, help_text="Máximo de tokens por respuesta")
    timeout = models.IntegerField(default=60, help_text="Timeout en segundos")
    
    # Configuración adicional JSON
    configuracion_adicional = models.JSONField(default=dict, blank=True, help_text="Parámetros adicionales del proveedor")
    prompt_sistema_global = models.TextField(blank=True, help_text="Prompt de sistema global para este proveedor")
    
    # Estado y costos
    activo = models.BooleanField(default=True, help_text="Si está disponible para uso")
    costo_por_1k_tokens = models.DecimalField(max_digits=10, decimal_places=6, default=0, help_text="Costo estimado por 1000 tokens")
    
    # Métricas de uso
    total_llamadas = models.IntegerField(default=0, help_text="Total de llamadas realizadas")
    total_tokens_usados = models.BigIntegerField(default=0, help_text="Total de tokens consumidos")
    ultima_conexion_exitosa = models.DateTimeField(null=True, blank=True, help_text="Última conexión exitosa")
    ultimo_error = models.TextField(blank=True, help_text="Último error registrado")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='proveedores_ia_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Proveedor IA"
        verbose_name_plural = "Proveedores IA"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:proveedor_detail', kwargs={'pk': self.pk})
    
    @property
    def esta_configurado(self):
        """Verifica si el proveedor está correctamente configurado"""
        # Proveedores que requieren API key
        if self.tipo in ['openai', 'anthropic', 'deepseek', 'google', 'groq', 'generic1', 'generic2']:
            if not self.api_key:
                # Buscar en variables de entorno
                from django.conf import settings
                env_key = f"{self.tipo.upper()}_API_KEY"
                if not getattr(settings, env_key, None):
                    return False
        
        # Proveedores locales que requieren URL
        if self.tipo in ['ollama', 'lmstudio'] and not self.api_url:
            return False
            
        return bool(self.modelo)
    
    @property
    def api_key_masked(self):
        """Devuelve la API key enmascarada para mostrar en UI"""
        if not self.api_key:
            return "No configurada"
        if len(self.api_key) <= 8:
            return "*" * len(self.api_key)
        return f"{self.api_key[:4]}{'*' * (len(self.api_key) - 8)}{self.api_key[-4:]}"
    
    def obtener_configuracion_completa(self):
        """Obtiene la configuración completa incluyendo valores por defecto del .env"""
        from django.conf import settings
        
        config = {
            'tipo': self.tipo,
            'nombre': self.nombre,
            'modelo': self.modelo,
            'temperatura': self.temperatura,
            'max_tokens': self.max_tokens,
            'timeout': self.timeout,
            'configuracion_adicional': self.configuracion_adicional,
            'prompt_sistema_global': self.prompt_sistema_global,
        }
        
        # API Key (prioridad: BD > .env)
        if self.api_key:
            config['api_key'] = self.api_key
        else:
            env_key = f"{self.tipo.upper()}_API_KEY"
            config['api_key'] = getattr(settings, env_key, '')
        
        # API URL (prioridad: BD > .env)
        if self.api_url:
            config['api_url'] = self.api_url
        else:
            env_url = f"{self.tipo.upper()}_API_URL"
            config['api_url'] = getattr(settings, env_url, '')
        
        return config
    
    def actualizar_metricas(self, tokens_usados=0, exito=True, error=None):
        """Actualiza las métricas de uso del proveedor"""
        self.total_llamadas += 1
        if tokens_usados > 0:
            self.total_tokens_usados += tokens_usados
        
        if exito:
            self.ultima_conexion_exitosa = timezone.now()
            self.ultimo_error = ""
        else:
            self.ultimo_error = error or "Error desconocido"
        
        self.save(update_fields=['total_llamadas', 'total_tokens_usados', 
                                'ultima_conexion_exitosa', 'ultimo_error'])
    
    @classmethod
    def obtener_configuraciones_por_defecto(cls):
        """Obtiene las configuraciones por defecto desde el .env con fallbacks inteligentes"""
        from django.conf import settings
        
        # Configuraciones por defecto con fallbacks
        configuraciones_defecto = {
            'openai': {
                'api_url': 'https://api.openai.com/v1/chat/completions',
                'modelo': 'gpt-4o',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'anthropic': {
                'api_url': 'https://api.anthropic.com/v1/messages',
                'modelo': 'claude-3-5-sonnet-20241022',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'deepseek': {
                'api_url': 'https://api.deepseek.com/v1/chat/completions',
                'modelo': 'deepseek-chat',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'google': {
                'api_url': 'https://generativelanguage.googleapis.com/v1beta/models',
                'modelo': 'gemini-1.5-flash',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'groq': {
                'api_url': 'https://api.groq.com/openai/v1/chat/completions',
                'modelo': 'llama-3.1-70b-versatile',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'ollama': {
                'api_url': 'http://localhost:11434/api/chat',
                'modelo': 'llama3.2:3b',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'lmstudio': {
                'api_url': 'http://localhost:1234/v1/chat/completions',
                'modelo': 'lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'generic1': {
                'api_url': '',
                'modelo': 'custom-model-1',
                'temperatura': 0.7,
                'max_tokens': 4000
            },
            'generic2': {
                'api_url': '',
                'modelo': 'custom-model-2',
                'temperatura': 0.7,
                'max_tokens': 4000
            }
        }
        
        configuraciones = {}
        for tipo, nombre in cls.TIPO_PROVEEDOR:
            env_prefix = tipo.upper()
            
            # Usar configuración por defecto como base
            config_base = configuraciones_defecto.get(tipo, {})
            
            configuraciones[tipo] = {
                'api_key': getattr(settings, f'{env_prefix}_API_KEY', ''),
                'api_url': getattr(settings, f'{env_prefix}_API_URL', config_base.get('api_url', '')),
                'modelo': getattr(settings, f'{env_prefix}_DEFAULT_MODEL', config_base.get('modelo', '')),
                'temperatura': float(getattr(settings, f'{env_prefix}_DEFAULT_TEMPERATURE', config_base.get('temperatura', 0.7))),
                'max_tokens': int(getattr(settings, f'{env_prefix}_DEFAULT_MAX_TOKENS', config_base.get('max_tokens', 4000))),
            }
        
        return configuraciones


class SegmentoPlantilla(models.Model):
    """Segmentos reutilizables para construir plantillas de actas"""
    TIPO_SEGMENTO = [
        ('estatico', 'Estático - Contenido fijo'),
        ('dinamico', 'Dinámico - Procesado con IA'),
        ('hibrido', 'Híbrido - Estático + IA opcional')
    ]
    
    CATEGORIA_SEGMENTO = [
        ('encabezado', 'Encabezado'),
        ('titulo', 'Título'),
        ('fecha_hora', 'Fecha y Hora'), 
        ('participantes', 'Participantes/Asistencia'),
        ('orden_dia', 'Orden del Día'),
        ('introduccion', 'Introducción'),
        ('desarrollo', 'Desarrollo/Contenido'),
        ('transcripcion', 'Transcripción'),
        ('resumen', 'Resumen Ejecutivo'),
        ('acuerdos', 'Acuerdos/Resoluciones'),
        ('compromisos', 'Compromisos/Tareas'),
        ('seguimiento', 'Seguimiento'),
        ('cierre', 'Cierre'),
        ('firmas', 'Firmas/Validaciones'),
        ('anexos', 'Anexos/Documentos'),
        ('legal', 'Marco Legal'),
        ('otros', 'Otros')
    ]
    
    FORMATO_SALIDA = [
        ('texto', 'Texto plano'),
        ('html', 'HTML estructurado'),
        ('markdown', 'Markdown'),
        ('json', 'JSON estructurado'),
        ('tabla', 'Tabla/Lista'),
        ('personalizado', 'Formato personalizado')
    ]
    
    
    # Identificación y categorización
    codigo = models.CharField(max_length=50, unique=True, help_text="Código único del segmento (ej: TITULO_ACTA)")
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo del segmento")
    descripcion = models.TextField(help_text="Descripción del propósito y funcionamiento del segmento")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_SEGMENTO, help_text="Categoría del segmento")
    tipo = models.CharField(max_length=20, choices=TIPO_SEGMENTO, help_text="Tipo de procesamiento")
    
    # Configuración para segmentos ESTÁTICOS
    contenido_estatico = models.TextField(blank=True, help_text="Contenido fijo para segmentos estáticos (admite variables {{variable}})")
    formato_salida = models.CharField(max_length=20, choices=FORMATO_SALIDA, default='texto', help_text="Formato de salida del contenido")
    
    # Configuración para segmentos DINÁMICOS (IA)
    prompt_ia = models.TextField(blank=True, help_text="Prompt para segmentos dinámicos procesados con IA")
    prompt_sistema = models.TextField(blank=True, help_text="Prompt de sistema específico (opcional, override del proveedor)")
    proveedor_ia = models.ForeignKey('ProveedorIA', on_delete=models.SET_NULL, null=True, blank=True, 
                                   help_text="Proveedor IA para procesamiento (solo segmentos dinámicos)")
    
    # Estructura y validación de resultados
    estructura_json = models.JSONField(default=dict, blank=True, help_text="Estructura esperada del resultado JSON")
    validaciones_salida = models.JSONField(default=list, blank=True, help_text="Validaciones a aplicar en la salida")
    formato_validacion = models.CharField(max_length=50, blank=True, help_text="Patrón regex o formato específico")
    
    # Configuración de entrada y contexto
    parametros_entrada = models.JSONField(default=list, blank=True, help_text="Lista de parámetros requeridos del contexto")
    variables_personalizadas = models.JSONField(default=dict, blank=True, 
                                               help_text="Variables JSON personalizables por el usuario")
    contexto_requerido = models.JSONField(default=list, blank=True, help_text="Elementos de contexto requeridos (transcripcion, participantes, etc)")
    
    # Comportamiento y reutilización
    orden_defecto = models.IntegerField(default=0, help_text="Orden por defecto en plantillas")
    reutilizable = models.BooleanField(default=True, help_text="Si puede ser usado en múltiples plantillas")
    obligatorio = models.BooleanField(default=False, help_text="Si es obligatorio en todas las plantillas")
    activo = models.BooleanField(default=True, help_text="Si está disponible para uso")
    
    # Configuraciones avanzadas
    longitud_maxima = models.IntegerField(null=True, blank=True, help_text="Longitud máxima del resultado en caracteres")
    tiempo_limite_ia = models.IntegerField(default=60, help_text="Tiempo límite para procesamiento IA (segundos)")
    reintentos_ia = models.IntegerField(default=2, help_text="Número de reintentos en caso de error")
    
    # Métricas y monitoreo
    total_usos = models.IntegerField(default=0, help_text="Total de veces que se ha usado")
    total_errores = models.IntegerField(default=0, help_text="Total de errores en procesamiento")
    ultima_prueba = models.DateTimeField(null=True, blank=True, help_text="Última vez que se probó")
    ultimo_resultado_prueba = models.TextField(blank=True, help_text="Resultado de la última prueba")
    tiempo_promedio_procesamiento = models.FloatField(default=0.0, help_text="Tiempo promedio de procesamiento (segundos)")
    tasa_exito = models.FloatField(default=0.0, help_text="Porcentaje de procesamientos exitosos (0-100)")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='segmentos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Segmento de Plantilla"
        verbose_name_plural = "Segmentos de Plantilla"
        ordering = ['categoria', 'orden_defecto', 'nombre']
        indexes = [
            models.Index(fields=['categoria', 'activo']),
            models.Index(fields=['tipo', 'activo']),
            models.Index(fields=['codigo']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({dict(self.CATEGORIA_SEGMENTO).get(self.categoria, self.categoria)})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:detalle_segmento', kwargs={'pk': self.pk})
    
    @property
    def es_estatico(self):
        """Verifica si el segmento es completamente estático"""
        return self.tipo == 'estatico'
    
    @property
    def es_dinamico(self):
        """Verifica si el segmento requiere procesamiento IA"""
        return self.tipo in ['dinamico', 'hibrido']
    
    @property
    def es_hibrido(self):
        """Verifica si el segmento es híbrido (estático + IA opcional)"""
        return self.tipo == 'hibrido'
    
    @property
    def tiene_prompt(self):
        """Verifica si tiene prompt configurado para IA"""
        return bool(self.prompt_ia.strip())
    
    @property
    def tiene_contenido_estatico(self):
        """Verifica si tiene contenido estático configurado"""
        return bool(self.contenido_estatico.strip())
    
    @property
    def esta_configurado(self):
        """Verifica si el segmento está correctamente configurado"""
        if self.es_estatico and not self.tiene_contenido_estatico:
            return False
        if self.es_dinamico and (not self.tiene_prompt or not self.proveedor_ia):
            return False
        if self.es_hibrido and not self.tiene_contenido_estatico:
            return False
        return True
    
    @property
    def configuracion_ia_valida(self):
        """Verifica si la configuración de IA es válida"""
        if not self.es_dinamico:
            return True
        return bool(self.proveedor_ia and self.proveedor_ia.esta_configurado and self.tiene_prompt)
    
    @property
    def estado_salud(self):
        """Calcula el estado de salud del segmento basado en métricas"""
        if self.total_usos == 0:
            return 'sin_uso'
        
        if self.total_errores == 0:
            return 'excelente'
        
        tasa_error = (self.total_errores / self.total_usos) * 100
        
        if tasa_error < 5:
            return 'bueno'
        elif tasa_error < 15:
            return 'regular'
        else:
            return 'problematico'
    
    @property
    def variables_disponibles(self):
        """Obtiene lista de variables disponibles para el segmento"""
        variables_base = {
            'fecha_actual': {'tipo': 'date', 'descripcion': 'Fecha actual del sistema'},
            'hora_actual': {'tipo': 'time', 'descripcion': 'Hora actual del sistema'},
            'fecha_reunion': {'tipo': 'date', 'descripcion': 'Fecha de la reunión'},
            'hora_reunion': {'tipo': 'time', 'descripcion': 'Hora de la reunión'},
            'tipo_reunion': {'tipo': 'string', 'descripcion': 'Tipo de reunión'},
            'numero_acta': {'tipo': 'string', 'descripcion': 'Número del acta'},
            'lugar_reunion': {'tipo': 'string', 'descripcion': 'Lugar donde se realizó la reunión'},
            'participantes': {'tipo': 'array', 'descripcion': 'Lista de participantes'},
            'duracion': {'tipo': 'time', 'descripcion': 'Duración de la reunión'},
            'transcripcion': {'tipo': 'object', 'descripcion': 'Datos de transcripción completa'}
        }
        
        # Agregar variables personalizadas
        if self.variables_personalizadas:
            variables_base.update(self.variables_personalizadas)
        
        return variables_base
    
    def procesar_contenido_estatico(self, contexto=None):
        """Procesa el contenido estático reemplazando variables"""
        if not self.tiene_contenido_estatico:
            return ""
        
        contenido = self.contenido_estatico
        
        if contexto:
            # Reemplazar variables en formato {{variable}}
            import re
            variables = re.findall(r'\{\{(\w+)\}\}', contenido)
            
            for variable in variables:
                valor = contexto.get(variable, f'{{{{ERROR: {variable} no encontrado}}}}')
                contenido = contenido.replace(f'{{{{{variable}}}}}', str(valor))
        
        return contenido
    
    def generar_prompt_completo(self, contexto=None):
        """Genera el prompt completo para enviar a la IA"""
        if not self.es_dinamico:
            return ""
        
        prompt_partes = []
        
        # Prompt de sistema si existe
        if self.prompt_sistema:
            prompt_partes.append(f"SISTEMA: {self.prompt_sistema}")
        
        # Prompt principal
        if self.prompt_ia:
            prompt_partes.append(f"INSTRUCCIONES: {self.prompt_ia}")
        
        # Contexto de entrada
        if contexto:
            prompt_partes.append(f"CONTEXTO: {json.dumps(contexto, ensure_ascii=False, indent=2)}")
        
        # Estructura esperada si existe
        if self.estructura_json:
            prompt_partes.append(f"FORMATO_RESPUESTA: {json.dumps(self.estructura_json, ensure_ascii=False, indent=2)}")
        
        return "\n\n".join(prompt_partes)
    
    def validar_resultado(self, resultado):
        """Valida el resultado según las reglas configuradas"""
        errores = []
        
        # Validar longitud máxima
        if self.longitud_maxima and len(resultado) > self.longitud_maxima:
            errores.append(f"Resultado excede longitud máxima de {self.longitud_maxima} caracteres")
        
        # Validar formato si está configurado
        if self.formato_validacion:
            import re
            if not re.match(self.formato_validacion, resultado):
                errores.append(f"Resultado no cumple formato: {self.formato_validacion}")
        
        # Validaciones personalizadas
        if self.validaciones_salida:
            for validacion in self.validaciones_salida:
                tipo_val = validacion.get('tipo')
                if tipo_val == 'contiene_texto':
                    if validacion.get('valor') not in resultado:
                        errores.append(f"Resultado debe contener: {validacion.get('valor')}")
                elif tipo_val == 'longitud_minima':
                    if len(resultado) < int(validacion.get('valor', 0)):
                        errores.append(f"Resultado debe tener al menos {validacion.get('valor')} caracteres")
        
        return errores
    
    def actualizar_metricas_uso(self, tiempo_procesamiento=None, exito=True, error=None):
        """Actualiza las métricas de uso del segmento"""
        self.total_usos += 1
        if not exito:
            self.total_errores += 1
        
        # Calcular tasa de éxito
        self.tasa_exito = ((self.total_usos - self.total_errores) / self.total_usos) * 100
        
        self.ultima_prueba = timezone.now()
        
        if tiempo_procesamiento is not None:
            # Calcular promedio móvil
            if self.tiempo_promedio_procesamiento == 0:
                self.tiempo_promedio_procesamiento = tiempo_procesamiento
            else:
                self.tiempo_promedio_procesamiento = (
                    (self.tiempo_promedio_procesamiento * (self.total_usos - 1) + tiempo_procesamiento) / self.total_usos
                )
        
        if error:
            self.ultimo_resultado_prueba = f"ERROR: {error}"[:1000]
        elif exito:
            self.ultimo_resultado_prueba = "Procesamiento exitoso"
        
        self.save(update_fields=[
            'total_usos', 'total_errores', 'tasa_exito', 'ultima_prueba', 
            'ultimo_resultado_prueba', 'tiempo_promedio_procesamiento'
        ])
    
    def crear_copia(self, nuevo_codigo=None, nuevo_nombre=None):
        """Crea una copia del segmento con nuevo código y nombre"""
        nuevo_segmento = SegmentoPlantilla.objects.create(
            codigo=nuevo_codigo or f"{self.codigo}_COPIA",
            nombre=nuevo_nombre or f"{self.nombre} (Copia)",
            descripcion=self.descripcion,
            categoria=self.categoria,
            tipo=self.tipo,
            contenido_estatico=self.contenido_estatico,
            formato_salida=self.formato_salida,
            prompt_ia=self.prompt_ia,
            prompt_sistema=self.prompt_sistema,
            proveedor_ia=self.proveedor_ia,
            estructura_json=self.estructura_json,
            validaciones_salida=self.validaciones_salida,
            formato_validacion=self.formato_validacion,
            parametros_entrada=self.parametros_entrada,
            variables_personalizadas=self.variables_personalizadas,
            contexto_requerido=self.contexto_requerido,
            orden_defecto=self.orden_defecto,
            reutilizable=self.reutilizable,
            obligatorio=False,  # Las copias no son obligatorias por defecto
            longitud_maxima=self.longitud_maxima,
            tiempo_limite_ia=self.tiempo_limite_ia,
            reintentos_ia=self.reintentos_ia,
            usuario_creacion=self.usuario_creacion
        )
        return nuevo_segmento
    
    @classmethod
    def obtener_variables_comunes(cls):
        """Obtiene variables comunes sugeridas para segmentos"""
        return {
            'fecha': {'tipo': 'date', 'descripcion': 'Fecha de la reunión', 'ejemplo': '2025-09-27'},
            'hora_inicio': {'tipo': 'time', 'descripcion': 'Hora de inicio', 'ejemplo': '09:00'},
            'hora_fin': {'tipo': 'time', 'descripcion': 'Hora de finalización', 'ejemplo': '11:30'},
            'duracion': {'tipo': 'string', 'descripcion': 'Duración de la reunión', 'ejemplo': '2 horas 30 minutos'},
            'participantes': {'tipo': 'array', 'descripcion': 'Lista de participantes', 
                            'ejemplo': ['Juan Pérez - Alcalde', 'María García - Secretaria']},
            'lugar': {'tipo': 'string', 'descripcion': 'Lugar de la reunión', 'ejemplo': 'Sala de Juntas Principal'},
            'numero_acta': {'tipo': 'string', 'descripcion': 'Número del acta', 'ejemplo': 'ACTA-2025-001'},
            'tipo_reunion': {'tipo': 'string', 'descripcion': 'Tipo de reunión', 'ejemplo': 'Sesión Ordinaria'},
            'periodo': {'tipo': 'string', 'descripcion': 'Periodo administrativo', 'ejemplo': '2025-2026'},
            'quorum': {'tipo': 'boolean', 'descripcion': 'Si se alcanzó quórum', 'ejemplo': True},
            'temas_tratados': {'tipo': 'array', 'descripcion': 'Temas principales tratados', 
                             'ejemplo': ['Aprobación presupuesto 2025', 'Proyecto vial sector norte']},
            'decisiones': {'tipo': 'array', 'descripcion': 'Decisiones tomadas', 
                         'ejemplo': ['Aprobar presupuesto por unanimidad', 'Iniciar licitación proyecto vial']},
            'compromisos': {'tipo': 'array', 'descripcion': 'Compromisos asumidos',
                          'ejemplo': ['Presentar informe técnico - 15 días', 'Convocar audiencia pública - 30 días']},
            'proxima_reunion': {'tipo': 'date', 'descripcion': 'Fecha próxima reunión', 'ejemplo': '2025-10-04'},
            'transcripcion_completa': {'tipo': 'text', 'descripcion': 'Transcripción completa de la reunión'},
            'resumen_ejecutivo': {'tipo': 'text', 'descripcion': 'Resumen ejecutivo de la reunión'},
            'municipio': {'tipo': 'string', 'descripcion': 'Nombre del municipio', 'ejemplo': 'Pastaza'},
            'provincia': {'tipo': 'string', 'descripcion': 'Provincia', 'ejemplo': 'Pastaza'},
            'pais': {'tipo': 'string', 'descripcion': 'País', 'ejemplo': 'Ecuador'}
        }
    
    @classmethod
    def crear_segmento_defecto(cls, categoria, usuario):
        """Crea un segmento por defecto para una categoría específica"""
        templates_defecto = {
            'encabezado': {
                'codigo': f'ENCAB_{categoria.upper()}',
                'nombre': 'Encabezado de Acta',
                'descripcion': 'Encabezado institucional del acta',
                'tipo': 'estatico',
                'contenido_estatico': """ACTA N° {{numero_acta}}
{{tipo_reunion}} DEL GOBIERNO AUTÓNOMO DESCENTRALIZADO MUNICIPAL DE {{municipio}}

Fecha: {{fecha}}
Hora de inicio: {{hora_inicio}}
Lugar: {{lugar}}""",
                'formato_salida': 'texto'
            },
            'participantes': {
                'codigo': f'PART_{categoria.upper()}', 
                'nombre': 'Lista de Participantes',
                'descripcion': 'Lista detallada de participantes con cargos',
                'tipo': 'dinamico',
                'prompt_ia': 'Genera una lista formal de participantes basada en los datos proporcionados. Incluye nombres completos, cargos y estado de asistencia.',
                'formato_salida': 'html'
            },
            'resumen': {
                'codigo': f'RESUM_{categoria.upper()}',
                'nombre': 'Resumen Ejecutivo', 
                'descripcion': 'Resumen ejecutivo de los temas tratados',
                'tipo': 'dinamico',
                'prompt_ia': 'Genera un resumen ejecutivo conciso de los temas principales tratados en la reunión, destacando decisiones importantes y conclusiones.',
                'formato_salida': 'texto'
            }
        }
        
        template = templates_defecto.get(categoria, templates_defecto['resumen'])
        template['categoria'] = categoria
        template['usuario_creacion'] = usuario
        
        return cls.objects.create(**template)
    
    @classmethod  
    def obtener_estadisticas_uso(cls):
        """Obtiene estadísticas globales de uso de segmentos"""
        from django.db.models import Avg, Sum, Count, Max, Min
        
        stats = cls.objects.aggregate(
            total_segmentos=Count('id'),
            total_usos=Sum('total_usos'),
            total_errores=Sum('total_errores'),
            tiempo_promedio_global=Avg('tiempo_promedio_procesamiento'),
            tasa_exito_promedio=Avg('tasa_exito'),
            ultimo_uso=Max('ultima_prueba')
        )
        
        # Estadísticas por tipo
        stats_por_tipo = cls.objects.values('tipo').annotate(
            cantidad=Count('id'),
            usos=Sum('total_usos'),
            errores=Sum('total_errores')
        )
        
        # Estadísticas por categoría
        stats_por_categoria = cls.objects.values('categoria').annotate(
            cantidad=Count('id'),
            usos=Sum('total_usos'),
            activos=Count('id', filter=models.Q(activo=True))
        )
        
        return {
            'globales': stats,
            'por_tipo': list(stats_por_tipo),
            'por_categoria': list(stats_por_categoria)
        }


class PlantillaActa(models.Model):
    """Plantillas configurables para diferentes tipos de actas"""
    TIPO_ACTA = [
        ('ordinaria', 'Sesión Ordinaria'),
        ('extraordinaria', 'Sesión Extraordinaria'),
        ('audiencia', 'Audiencia Pública'),
        ('comision', 'Comisión'),
        ('directorio', 'Directorio'),
        ('asamblea', 'Asamblea'),
        ('otros', 'Otros')
    ]
    
    # Identificación
    codigo = models.CharField(max_length=50, unique=True, help_text="Código único de la plantilla")
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo de la plantilla")
    descripcion = models.TextField(help_text="Descripción del uso de la plantilla")
    tipo_acta = models.CharField(max_length=50, choices=TIPO_ACTA, help_text="Tipo de acta que genera")
    
    # Configuración de segmentos
    segmentos = models.ManyToManyField(SegmentoPlantilla, through='ConfiguracionSegmento', help_text="Segmentos que componen la plantilla")
    
    # Configuración de procesamiento
    prompt_global = models.TextField(help_text="Prompt para unificación final del acta")
    proveedor_ia_defecto = models.ForeignKey(ProveedorIA, on_delete=models.SET_NULL, null=True, blank=True, help_text="Proveedor IA por defecto")
    configuracion_procesamiento = models.JSONField(default=dict, blank=True, help_text="Configuración adicional de procesamiento")
    
    # Estado y versión
    activa = models.BooleanField(default=True, help_text="Si está disponible para uso")
    version = models.CharField(max_length=20, default='1.0', help_text="Versión de la plantilla")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='plantillas_creadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plantilla de Acta"
        verbose_name_plural = "Plantillas de Actas"
        ordering = ['tipo_acta', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_acta_display()})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:editar_plantilla', kwargs={'pk': self.pk})
    
    @property
    def segmentos_ordenados(self):
        """Obtiene los segmentos ordenados según configuración"""
        return self.configuracionsegmento_set.all().order_by('orden')
    
    @property
    def total_segmentos(self):
        """Total de segmentos en la plantilla"""
        return self.segmentos.count()
    
    @property
    def segmentos_dinamicos(self):
        """Total de segmentos que requieren IA"""
        return self.segmentos.filter(tipo__in=['dinamico', 'hibrido']).count()


class ConfiguracionSegmento(models.Model):
    """Configuración específica de un segmento dentro de una plantilla"""
    plantilla = models.ForeignKey(PlantillaActa, on_delete=models.CASCADE)
    segmento = models.ForeignKey(SegmentoPlantilla, on_delete=models.CASCADE)
    
    # Configuración específica para esta plantilla
    orden = models.IntegerField(help_text="Orden del segmento en la plantilla")
    obligatorio = models.BooleanField(default=False, help_text="Si es obligatorio en esta plantilla")
    prompt_personalizado = models.TextField(blank=True, help_text="Prompt específico para esta plantilla")
    parametros_override = models.JSONField(default=dict, blank=True, help_text="Parámetros que sobrescriben los del segmento")
    
    class Meta:
        verbose_name = "Configuración de Segmento"
        verbose_name_plural = "Configuraciones de Segmentos"
        ordering = ['plantilla', 'orden']
        unique_together = ['plantilla', 'orden']
    
    def __str__(self):
        return f"{self.plantilla.nombre} - {self.segmento.nombre} (Orden: {self.orden})"
    
    @property
    def prompt_efectivo(self):
        """Obtiene el prompt a usar (personalizado o del segmento)"""
        return self.prompt_personalizado or self.segmento.prompt_ia


class ActaGenerada(models.Model):
    """Actas generadas a partir de transcripciones usando IA"""
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('pendiente', 'Pendiente de Procesamiento'),
        ('procesando', 'Procesando'),
        ('procesando_segmentos', 'Procesando Segmentos'),
        ('unificando', 'Unificando Contenido'),
        ('revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('publicado', 'Publicado'),
        ('rechazado', 'Rechazado'),
        ('error', 'Error en Procesamiento')
    ]
    
    # Identificación
    numero_acta = models.CharField(max_length=50, unique=True, help_text="Número único del acta")
    titulo = models.CharField(max_length=300, help_text="Título del acta")
    
    # Referencias a otros módulos
    transcripcion = models.ForeignKey('transcripcion.Transcripcion', on_delete=models.CASCADE, help_text="Transcripción base")
    plantilla = models.ForeignKey(PlantillaActa, on_delete=models.PROTECT, help_text="Plantilla usada")
    proveedor_ia = models.ForeignKey(ProveedorIA, on_delete=models.PROTECT, help_text="Proveedor IA usado")
    
    # Datos procesados
    segmentos_procesados = models.JSONField(default=dict, blank=True, help_text="Resultado del procesamiento de segmentos")
    contenido_borrador = models.TextField(blank=True, help_text="Borrador inicial del acta")
    contenido_final = models.TextField(blank=True, help_text="Versión final del acta")
    contenido_html = models.TextField(blank=True, help_text="Versión HTML del acta")
    
    # Metadatos y métricas
    metadatos = models.JSONField(default=dict, blank=True, help_text="Metadatos adicionales")
    metricas_procesamiento = models.JSONField(default=dict, blank=True, help_text="Métricas de tiempo, tokens, costo")
    historial_cambios = models.JSONField(default=list, blank=True, help_text="Historial de modificaciones")
    
    # Estado y tracking
    estado = models.CharField(max_length=30, choices=ESTADO_CHOICES, default='borrador', help_text="Estado actual del acta")
    progreso = models.IntegerField(default=0, help_text="Progreso de procesamiento (0-100)")
    task_id_celery = models.CharField(max_length=255, blank=True, help_text="ID de tarea Celery")
    mensajes_error = models.TextField(blank=True, help_text="Mensajes de error durante procesamiento")
    
    # Fechas importantes
    fecha_sesion = models.DateTimeField(help_text="Fecha de la sesión/reunión")
    fecha_procesamiento = models.DateTimeField(null=True, blank=True, help_text="Fecha de inicio de procesamiento")
    fecha_revision = models.DateTimeField(null=True, blank=True, help_text="Fecha de revisión")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, help_text="Fecha de aprobación")
    fecha_publicacion = models.DateTimeField(null=True, blank=True, help_text="Fecha de publicación")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='actas_creadas')
    usuario_revision = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actas_revisadas')
    usuario_aprobacion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actas_aprobadas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Acta Generada"
        verbose_name_plural = "Actas Generadas"
        ordering = ['-fecha_sesion', '-fecha_creacion']
        permissions = [
            ("can_approve_acta", "Puede aprobar actas"),
            ("can_publish_acta", "Puede publicar actas"),
            ("can_review_acta", "Puede revisar actas"),
        ]
    
    def __str__(self):
        return f"{self.numero_acta} - {self.titulo}"
    
    def get_absolute_url(self):
        return reverse('generador_actas:detalle_acta', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        # Asegurar que fecha_sesion tenga un valor
        if not self.fecha_sesion:
            self.fecha_sesion = timezone.now()
        
        # Generar número de acta si no existe
        if not self.numero_acta:
            year = self.fecha_sesion.year
            last_acta = ActaGenerada.objects.filter(
                numero_acta__startswith=f"ACTA-{year}-"
            ).order_by('-numero_acta').first()
            
            if last_acta:
                try:
                    last_num = int(last_acta.numero_acta.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            
            self.numero_acta = f"ACTA-{year}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def estado_display_class(self):
        """Clase CSS para mostrar el estado"""
        classes = {
            'borrador': 'badge-secondary',
            'pendiente': 'badge-info',
            'procesando': 'badge-primary',
            'procesando_segmentos': 'badge-primary',
            'unificando': 'badge-primary',
            'revision': 'badge-warning',
            'aprobado': 'badge-success',
            'publicado': 'badge-success',
            'rechazado': 'badge-danger',
            'error': 'badge-danger'
        }
        return classes.get(self.estado, 'badge-secondary')
    
    @property
    def puede_procesar(self):
        """Verifica si el acta puede ser procesada"""
        return self.estado in ['borrador', 'error']
    
    @property
    def puede_revisar(self):
        """Verifica si el acta puede ser revisada"""
        return self.estado == 'revision'
    
    @property
    def puede_aprobar(self):
        """Verifica si el acta puede ser aprobada"""
        return self.estado == 'revision'
    
    def agregar_historial(self, accion, usuario, detalles=None):
        """Agrega una entrada al historial de cambios"""
        entrada = {
            'fecha': timezone.now().isoformat(),
            'usuario': usuario.username,
            'accion': accion,
            'detalles': detalles or {}
        }
        self.historial_cambios.append(entrada)
        self.save(update_fields=['historial_cambios'])


# =========================
# MODELOS PARA OPERACIONES DE SISTEMA
# =========================

class OperacionSistema(models.Model):
    """Modelo para trackear operaciones asíncronas del sistema"""
    TIPOS_OPERACION = [
        ('backup', 'Backup del Sistema'),
        ('export_config', 'Exportación de Configuraciones'),
        ('restart_services', 'Reinicio de Servicios'),
        ('preview_template', 'Vista Previa de Plantilla'),
        ('export_template', 'Exportación de Plantilla'),
        ('reset_config', 'Reset de Configuraciones'),
        ('test_providers', 'Prueba de Proveedores IA'),
        ('duplicate_segment', 'Duplicar Segmento'),
        ('duplicate_template', 'Duplicar Plantilla'),
    ]
    
    ESTADOS = [
        ('pending', 'Pendiente'),
        ('running', 'Ejecutando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=50, choices=TIPOS_OPERACION)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    
    # Estado y progreso
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pending')
    progreso = models.IntegerField(default=0, help_text="Progreso en porcentaje (0-100)")
    mensaje_estado = models.TextField(blank=True, help_text="Mensaje descriptivo del estado actual")
    
    # Datos de la operación
    parametros_entrada = models.JSONField(default=dict, help_text="Parámetros de entrada de la operación")
    resultado = models.JSONField(default=dict, blank=True, help_text="Resultado de la operación")
    logs = models.JSONField(default=list, help_text="Logs detallados de la operación")
    
    # Archivos generados
    archivo_resultado = models.FileField(upload_to='operaciones_sistema/', blank=True, null=True)
    url_descarga = models.URLField(blank=True, help_text="URL de descarga del resultado")
    
    # Metadatos
    task_id = models.CharField(max_length=255, blank=True, help_text="ID de la tarea Celery")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    tiempo_ejecucion = models.DurationField(null=True, blank=True)
    
    # Configuración
    expira_en = models.DateTimeField(null=True, blank=True, help_text="Fecha de expiración del resultado")
    notificar_usuario = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
        indexes = [
            models.Index(fields=['usuario', '-fecha_inicio']),
            models.Index(fields=['tipo', 'estado']),
            models.Index(fields=['task_id']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.titulo} ({self.get_estado_display()})"
    
    def agregar_log(self, nivel, mensaje, detalles=None):
        """Agrega una entrada de log a la operación"""
        entrada = {
            'timestamp': timezone.now().isoformat(),
            'nivel': nivel,
            'mensaje': mensaje,
            'detalles': detalles or {}
        }
        self.logs.append(entrada)
        self.save(update_fields=['logs'])
    
    def actualizar_progreso(self, progreso, mensaje=""):
        """Actualiza el progreso de la operación"""
        self.progreso = progreso
        if mensaje:
            self.mensaje_estado = mensaje
        self.save(update_fields=['progreso', 'mensaje_estado'])
    
    def marcar_completado(self, resultado=None):
        """Marca la operación como completada"""
        self.estado = 'completed'
        self.fecha_finalizacion = timezone.now()
        self.tiempo_ejecucion = self.fecha_finalizacion - self.fecha_inicio
        if resultado:
            self.resultado = resultado
        self.save()
    
    def marcar_fallido(self, error):
        """Marca la operación como fallida"""
        self.estado = 'failed'
        self.fecha_finalizacion = timezone.now()
        self.tiempo_ejecucion = self.fecha_finalizacion - self.fecha_inicio
        self.mensaje_estado = str(error)
        self.agregar_log('error', f"Operación fallida: {error}")
        self.save()


class ConfiguracionSistema(models.Model):
    """Modelo para almacenar configuraciones del sistema con versionado"""
    
    # Identificación
    clave = models.CharField(max_length=100, unique=True, help_text="Clave única de configuración")
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo")
    descripcion = models.TextField(blank=True)
    
    # Valor y metadatos
    valor = models.JSONField(help_text="Valor de la configuración")
    valor_por_defecto = models.JSONField(help_text="Valor por defecto")
    tipo_dato = models.CharField(max_length=50, default='string', choices=[
        ('string', 'Texto'),
        ('integer', 'Número entero'),
        ('float', 'Número decimal'),
        ('boolean', 'Verdadero/Falso'),
        ('json', 'JSON'),
        ('list', 'Lista'),
    ])
    
    # Validación
    validacion = models.JSONField(default=dict, blank=True, help_text="Reglas de validación")
    es_requerido = models.BooleanField(default=False)
    es_publico = models.BooleanField(default=False, help_text="Si es visible en APIs públicas")
    
    # Versionado
    version = models.IntegerField(default=1)
    historial_valores = models.JSONField(default=list, help_text="Historial de cambios de valor")
    
    # Auditoría
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='configuraciones_creadas')
    usuario_modificacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='configuraciones_modificadas', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['clave']
        indexes = [
            models.Index(fields=['clave']),
            models.Index(fields=['es_publico']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.clave})"
    
    def actualizar_valor(self, nuevo_valor, usuario):
        """Actualiza el valor guardando el historial"""
        # Guardar valor anterior en historial
        entrada_historial = {
            'timestamp': timezone.now().isoformat(),
            'valor_anterior': self.valor,
            'valor_nuevo': nuevo_valor,
            'usuario': usuario.username,
            'version': self.version
        }
        self.historial_valores.append(entrada_historial)
        
        # Actualizar valor actual
        self.valor = nuevo_valor
        self.version += 1
        self.usuario_modificacion = usuario
        self.save()
    
    def restaurar_por_defecto(self, usuario):
        """Restaura el valor por defecto"""
        self.actualizar_valor(self.valor_por_defecto, usuario)


class LogOperacion(models.Model):
    """Logs detallados de operaciones del sistema"""
    
    NIVELES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    operacion = models.ForeignKey(OperacionSistema, on_delete=models.CASCADE, related_name='logs_detallados')
    timestamp = models.DateTimeField(auto_now_add=True)
    nivel = models.CharField(max_length=20, choices=NIVELES)
    mensaje = models.TextField()
    contexto = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['operacion', '-timestamp']),
            models.Index(fields=['nivel']),
        ]
    
    def __str__(self):
        return f"{self.operacion.titulo} - {self.nivel}: {self.mensaje[:50]}"


class EjecucionPlantilla(models.Model):
    """Registro de cada ejecución de una plantilla para generar un acta"""
    ESTADO_EJECUCION = [
        ('iniciada', 'Iniciada'),
        ('procesando_segmentos', 'Procesando Segmentos'),
        ('editando_resultados', 'Editando Resultados'),
        ('unificando', 'Unificando Acta'),
        ('completada', 'Completada'),
        ('error', 'Error'),
        ('cancelada', 'Cancelada'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo de la ejecución")
    
    # Relaciones principales
    plantilla = models.ForeignKey(PlantillaActa, on_delete=models.CASCADE, related_name='ejecuciones')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ejecuciones_plantillas')
    transcripcion = models.ForeignKey('audio_processing.ProcesamientoAudio', on_delete=models.CASCADE, 
                                    null=True, blank=True, help_text="Transcripción utilizada como fuente")
    
    # Configuración de ejecución
    proveedor_ia_global = models.ForeignKey(ProveedorIA, on_delete=models.PROTECT, 
                                          help_text="IA utilizada para todos los segmentos")
    variables_contexto = models.JSONField(default=dict, blank=True, 
                                        help_text="Variables específicas para esta ejecución")
    configuracion_overrides = models.JSONField(default=dict, blank=True,
                                              help_text="Sobrescribir configuración por segmento")
    
    # Estado y progreso
    estado = models.CharField(max_length=50, choices=ESTADO_EJECUCION, default='iniciada')
    progreso_actual = models.IntegerField(default=0, help_text="Segmentos procesados")
    progreso_total = models.IntegerField(default=0, help_text="Total de segmentos")
    
    # Metadatos de procesamiento
    tiempo_inicio = models.DateTimeField(auto_now_add=True)
    tiempo_fin = models.DateTimeField(null=True, blank=True)
    tiempo_total_segundos = models.IntegerField(null=True, blank=True)
    
    # Resultados y errores
    resultados_parciales = models.JSONField(default=dict, blank=True,
                                          help_text="Resumen de resultados por segmento")
    errores = models.JSONField(default=list, blank=True, help_text="Errores encontrados")
    logs_procesamiento = models.TextField(blank=True, help_text="Logs detallados del proceso")
    
    # Configuración de unificación
    prompt_unificacion_override = models.TextField(blank=True, 
                                                 help_text="Override del prompt de unificación")
    resultado_unificacion = models.TextField(blank=True, help_text="Acta unificada generada")
    
    class Meta:
        verbose_name = "Ejecución de Plantilla"
        verbose_name_plural = "Ejecuciones de Plantillas"
        ordering = ['-tiempo_inicio']
        indexes = [
            models.Index(fields=['estado', '-tiempo_inicio']),
            models.Index(fields=['usuario', '-tiempo_inicio']),
            models.Index(fields=['plantilla', '-tiempo_inicio']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - {self.plantilla.nombre} ({self.get_estado_display()})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:ver_ejecucion', kwargs={'pk': self.pk})
    
    @property
    def duracion_formateada(self):
        """Duración formateada de la ejecución"""
        if not self.tiempo_total_segundos:
            return "En proceso"
        
        horas = self.tiempo_total_segundos // 3600
        minutos = (self.tiempo_total_segundos % 3600) // 60
        segundos = self.tiempo_total_segundos % 60
        
        if horas > 0:
            return f"{horas}h {minutos}m {segundos}s"
        elif minutos > 0:
            return f"{minutos}m {segundos}s"
        else:
            return f"{segundos}s"
    
    @property
    def porcentaje_progreso(self):
        """Progreso como porcentaje"""
        if self.progreso_total == 0:
            return 0
        return int((self.progreso_actual / self.progreso_total) * 100)
    
    def marcar_completada(self):
        """Marca la ejecución como completada y calcula tiempos"""
        self.estado = 'completada'
        self.tiempo_fin = timezone.now()
        if self.tiempo_inicio:
            delta = self.tiempo_fin - self.tiempo_inicio
            self.tiempo_total_segundos = int(delta.total_seconds())
        self.save()
    
    def agregar_error(self, error_mensaje, segmento=None):
        """Agrega un error al log de errores"""
        error_info = {
            'timestamp': timezone.now().isoformat(),
            'mensaje': error_mensaje,
            'segmento': segmento.codigo if segmento else None
        }
        if not self.errores:
            self.errores = []
        self.errores.append(error_info)
        self.save()


class ResultadoSegmento(models.Model):
    """Resultado del procesamiento de cada segmento dentro de una ejecución"""
    ESTADO_RESULTADO = [
        ('pendiente', 'Pendiente'),
        ('procesando', 'Procesando'),
        ('completado', 'Completado'),
        ('editado', 'Editado Manualmente'),
        ('error', 'Error'),
        ('omitido', 'Omitido'),
    ]
    
    # Relaciones
    ejecucion = models.ForeignKey(EjecucionPlantilla, on_delete=models.CASCADE, related_name='resultados')
    segmento = models.ForeignKey(SegmentoPlantilla, on_delete=models.CASCADE)
    
    # Configuración utilizada
    orden_procesamiento = models.IntegerField(help_text="Orden en que se procesó")
    proveedor_ia_usado = models.ForeignKey(ProveedorIA, on_delete=models.PROTECT, null=True, blank=True)
    prompt_usado = models.TextField(help_text="Prompt final enviado a la IA")
    configuracion_ia = models.JSONField(default=dict, blank=True, help_text="Parámetros IA utilizados")
    
    # Resultados
    estado = models.CharField(max_length=50, choices=ESTADO_RESULTADO, default='pendiente')
    resultado_crudo = models.TextField(blank=True, help_text="Respuesta cruda de la IA")
    resultado_procesado = models.TextField(blank=True, help_text="Resultado limpio y procesado")
    resultado_editado = models.TextField(blank=True, help_text="Versión editada manualmente")
    
    # Metadatos de procesamiento
    tiempo_procesamiento = models.DateTimeField(null=True, blank=True)
    tiempo_total_ms = models.IntegerField(null=True, blank=True, help_text="Tiempo de procesamiento en ms")
    tokens_utilizados = models.IntegerField(null=True, blank=True, help_text="Tokens consumidos")
    costo_estimado = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Control de versiones y edición
    version_resultado = models.IntegerField(default=1, help_text="Versión del resultado")
    usuario_ultima_edicion = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_ultima_edicion = models.DateTimeField(auto_now=True)
    
    # Metadatos adicionales
    metadatos_ia = models.JSONField(default=dict, blank=True, help_text="Metadatos de respuesta IA")
    notas_edicion = models.TextField(blank=True, help_text="Notas del usuario sobre ediciones")
    
    class Meta:
        verbose_name = "Resultado de Segmento"
        verbose_name_plural = "Resultados de Segmentos"
        ordering = ['ejecucion', 'orden_procesamiento']
        unique_together = ['ejecucion', 'segmento']
        indexes = [
            models.Index(fields=['ejecucion', 'orden_procesamiento']),
            models.Index(fields=['estado']),
            models.Index(fields=['segmento']),
        ]
    
    def __str__(self):
        return f"{self.segmento.nombre} - {self.ejecucion.nombre} ({self.get_estado_display()})"
    
    @property
    def resultado_final(self):
        """Obtiene el resultado final (editado si existe, sino procesado)"""
        return self.resultado_editado or self.resultado_procesado or self.resultado_crudo
    
    @property
    def fue_editado(self):
        """Indica si el resultado fue editado manualmente"""
        return bool(self.resultado_editado and self.usuario_ultima_edicion)
    
    def marcar_como_editado(self, nuevo_contenido, usuario):
        """Marca el resultado como editado manualmente"""
        self.resultado_editado = nuevo_contenido
        self.usuario_ultima_edicion = usuario
        self.estado = 'editado'
        self.version_resultado += 1
        self.save()


class ActaBorrador(models.Model):
    """Acta borrador generada a partir de una ejecución de plantilla"""
    ESTADO_BORRADOR = [
        ('generando', 'Generando'),
        ('borrador', 'Borrador'),
        ('revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('publicado', 'Publicado'),
        ('archivado', 'Archivado'),
    ]
    
    FORMATO_SALIDA = [
        ('html', 'HTML'),
        ('markdown', 'Markdown'),
        ('docx', 'Word Document'),
        ('pdf', 'PDF'),
    ]
    
    # Identificación
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    titulo = models.CharField(max_length=300, help_text="Título del acta generada")
    numero_acta = models.CharField(max_length=50, blank=True, help_text="Número oficial del acta")
    
    # Relaciones
    ejecucion = models.OneToOneField(EjecucionPlantilla, on_delete=models.CASCADE, related_name='acta_borrador')
    usuario_creacion = models.ForeignKey(User, on_delete=models.PROTECT, related_name='actas_borradores_creadas')
    
    # Contenido del acta
    contenido_html = models.TextField(help_text="Contenido del acta en HTML")
    contenido_markdown = models.TextField(blank=True, help_text="Versión Markdown del acta")
    resumen_ejecutivo = models.TextField(blank=True, help_text="Resumen ejecutivo del acta")
    
    # Metadatos del documento
    fecha_acta = models.DateField(help_text="Fecha oficial del acta")
    lugar_sesion = models.CharField(max_length=200, blank=True, help_text="Lugar donde se realizó la sesión")
    participantes = models.JSONField(default=list, blank=True, help_text="Lista de participantes")
    
    # Estado y workflow
    estado = models.CharField(max_length=50, choices=ESTADO_BORRADOR, default='borrador')
    version = models.CharField(max_length=20, default='1.0')
    
    # Control de versiones
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)
    usuario_ultima_modificacion = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                                   null=True, blank=True,
                                                   related_name='actas_borradores_modificadas')
    
    # Configuración de formato
    formato_preferido = models.CharField(max_length=20, choices=FORMATO_SALIDA, default='html')
    configuracion_formato = models.JSONField(default=dict, blank=True, 
                                           help_text="Configuración específica de formato")
    
    # Archivos generados
    archivo_pdf = models.FileField(upload_to='actas/pdf/', blank=True, null=True)
    archivo_docx = models.FileField(upload_to='actas/docx/', blank=True, null=True)
    
    # Metadatos de calidad y procesamiento
    calidad_estimada = models.FloatField(null=True, blank=True, help_text="Calidad estimada del acta (0-1)")
    tiempo_generacion_segundos = models.IntegerField(null=True, blank=True)
    
    # Comentarios y revisiones
    comentarios_revision = models.TextField(blank=True, help_text="Comentarios de revisión")
    historial_cambios = models.JSONField(default=list, blank=True, help_text="Historial de cambios")
    
    class Meta:
        verbose_name = "Acta Borrador"
        verbose_name_plural = "Actas Borrador"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado', '-fecha_creacion']),
            models.Index(fields=['usuario_creacion', '-fecha_creacion']),
            models.Index(fields=['fecha_acta']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.numero_acta} ({self.get_estado_display()})"
    
    def get_absolute_url(self):
        return reverse('generador_actas:ver_acta_borrador', kwargs={'pk': self.pk})
    
    @property
    def tiempo_generacion_formateado(self):
        """Tiempo de generación formateado"""
        if not self.tiempo_generacion_segundos:
            return "No disponible"
        
        minutos = self.tiempo_generacion_segundos // 60
        segundos = self.tiempo_generacion_segundos % 60
        
        if minutos > 0:
            return f"{minutos}m {segundos}s"
        else:
            return f"{segundos}s"
    
    def generar_numero_acta(self):
        """Genera un número de acta automático si no existe"""
        if not self.numero_acta:
            fecha = self.fecha_acta or timezone.now().date()
            año = fecha.year
            # Contar actas del mismo año
            count = ActaBorrador.objects.filter(fecha_acta__year=año).count()
            self.numero_acta = f"ACTA-{año}-{count + 1:03d}"
            self.save()
    
    def agregar_cambio_historial(self, usuario, descripcion, tipo_cambio='modificacion'):
        """Agrega un cambio al historial"""
        cambio = {
            'timestamp': timezone.now().isoformat(),
            'usuario': usuario.username,
            'tipo': tipo_cambio,
            'descripcion': descripcion,
            'version': self.version
        }
        if not self.historial_cambios:
            self.historial_cambios = []
        self.historial_cambios.append(cambio)
        self.save()