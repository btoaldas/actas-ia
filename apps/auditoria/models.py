"""
Modelos para representar las tablas de auditoría y logs
Estos modelos usan unmanaged=True para conectarse a las tablas existentes
"""
from django.db import models
from django.contrib.auth.models import User


class SistemaLogs(models.Model):
    """Logs generales del sistema"""
    timestamp = models.DateTimeField(auto_now_add=True)
    nivel = models.CharField(max_length=20)
    categoria = models.CharField(max_length=50)
    subcategoria = models.CharField(max_length=100, blank=True, null=True)
    usuario_id = models.IntegerField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    mensaje = models.TextField()
    datos_extra = models.JSONField(blank=True, null=True)
    modulo = models.CharField(max_length=100, blank=True, null=True)
    url_solicitada = models.TextField(blank=True, null=True)
    metodo_http = models.CharField(max_length=10, blank=True, null=True)
    tiempo_respuesta_ms = models.IntegerField(blank=True, null=True)
    codigo_respuesta = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'logs"."sistema_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.nivel} - {self.categoria}: {self.mensaje[:50]}"


class NavegacionUsuarios(models.Model):
    """Logs de navegación de usuarios"""
    usuario_id = models.IntegerField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    url_visitada = models.TextField()
    url_anterior = models.TextField(blank=True, null=True)
    metodo_http = models.CharField(max_length=10, default='GET')
    parametros_get = models.JSONField(blank=True, null=True)
    parametros_post = models.JSONField(blank=True, null=True)
    tiempo_permanencia_ms = models.IntegerField(blank=True, null=True)
    accion_realizada = models.CharField(max_length=100, blank=True, null=True)
    elemento_interactuado = models.CharField(max_length=255, blank=True, null=True)
    datos_formulario = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    codigo_respuesta = models.IntegerField(default=200)

    class Meta:
        managed = False
        db_table = 'logs"."navegacion_usuarios'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Usuario {self.usuario_id}: {self.url_visitada}"


class ApiLogs(models.Model):
    """Logs de llamadas a la API"""
    timestamp = models.DateTimeField(auto_now_add=True)
    endpoint = models.CharField(max_length=255)
    metodo_http = models.CharField(max_length=10)
    usuario_id = models.IntegerField(blank=True, null=True)
    api_key_id = models.IntegerField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    parametros_query = models.JSONField(blank=True, null=True)
    payload_request = models.JSONField(blank=True, null=True)
    payload_response = models.JSONField(blank=True, null=True)
    codigo_respuesta = models.IntegerField(blank=True, null=True)
    tiempo_respuesta_ms = models.IntegerField(blank=True, null=True)
    tamaño_request_bytes = models.IntegerField(blank=True, null=True)
    tamaño_response_bytes = models.IntegerField(blank=True, null=True)
    version_api = models.CharField(max_length=20, blank=True, null=True)
    rate_limit_remaining = models.IntegerField(blank=True, null=True)
    error_mensaje = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs"."api_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.metodo_http} {self.endpoint}"


class ErroresSistema(models.Model):
    """Logs de errores del sistema"""
    timestamp = models.DateTimeField(auto_now_add=True)
    nivel_error = models.CharField(max_length=20)
    codigo_error = models.CharField(max_length=50, blank=True, null=True)
    mensaje_error = models.TextField()
    stack_trace = models.TextField(blank=True, null=True)
    url_error = models.TextField(blank=True, null=True)
    usuario_id = models.IntegerField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    datos_request = models.JSONField(blank=True, null=True)
    contexto_aplicacion = models.JSONField(blank=True, null=True)
    version_aplicacion = models.CharField(max_length=50, blank=True, null=True)
    entorno = models.CharField(max_length=20, default='production')
    resuelto = models.BooleanField(default=False)
    resuelto_por_id = models.IntegerField(blank=True, null=True)
    fecha_resolucion = models.DateTimeField(blank=True, null=True)
    notas_resolucion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs"."errores_sistema'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.nivel_error}: {self.mensaje_error[:50]}"


class AccesoUsuarios(models.Model):
    """Logs de acceso de usuarios"""
    timestamp = models.DateTimeField(auto_now_add=True)
    usuario_id = models.IntegerField()
    evento = models.CharField(max_length=50)  # LOGIN, LOGOUT, etc.
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    ubicacion_geografica = models.CharField(max_length=100, blank=True, null=True)
    dispositivo_tipo = models.CharField(max_length=50, blank=True, null=True)
    browser_info = models.JSONField(blank=True, null=True)
    metadatos = models.JSONField(blank=True, null=True)
    exitoso = models.BooleanField(default=True)
    razon_fallo = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs"."acceso_usuarios'
        ordering = ['-timestamp']

    def __str__(self):
        return f"Usuario {self.usuario_id}: {self.evento}"


class CeleryLogs(models.Model):
    """Logs de tareas Celery"""
    timestamp = models.DateTimeField(auto_now_add=True)
    task_id = models.CharField(max_length=255)
    task_name = models.CharField(max_length=255)
    estado = models.CharField(max_length=50)  # PENDING, STARTED, SUCCESS, FAILURE, etc.
    parametros_entrada = models.JSONField(blank=True, null=True)
    resultado = models.JSONField(blank=True, null=True)
    tiempo_ejecucion_ms = models.IntegerField(blank=True, null=True)
    worker_nombre = models.CharField(max_length=100, blank=True, null=True)
    queue_nombre = models.CharField(max_length=100, blank=True, null=True)
    prioridad = models.IntegerField(blank=True, null=True)
    intentos = models.IntegerField(default=1)
    mensaje_error = models.TextField(blank=True, null=True)
    metadatos = models.JSONField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs"."celery_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.task_name} ({self.estado})"


class ArchivoLogs(models.Model):
    """Logs de manejo de archivos"""
    timestamp = models.DateTimeField(auto_now_add=True)
    operacion = models.CharField(max_length=50)  # UPLOAD, DOWNLOAD, DELETE, etc.
    archivo_nombre = models.CharField(max_length=255)
    archivo_path = models.TextField()
    archivo_size_bytes = models.BigIntegerField()
    archivo_tipo_mime = models.CharField(max_length=100)
    usuario_id = models.IntegerField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    resultado = models.CharField(max_length=20)  # SUCCESS, ERROR
    mensaje_error = models.TextField(blank=True, null=True)
    metadatos = models.JSONField(blank=True, null=True)
    hash_archivo = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs"."archivo_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.operacion}: {self.archivo_nombre}"


class AdminLogs(models.Model):
    """Logs de actividad en panel administrativo"""
    timestamp = models.DateTimeField(auto_now_add=True)
    usuario_id = models.IntegerField()
    modelo_afectado = models.CharField(max_length=100)
    accion = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE, VIEW
    objeto_id = models.CharField(max_length=255, blank=True, null=True)
    campos_modificados = models.JSONField(blank=True, null=True)
    valores_anteriores = models.JSONField(blank=True, null=True)
    valores_nuevos = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    url_admin = models.TextField()
    tiempo_operacion_ms = models.IntegerField(blank=True, null=True)
    exitoso = models.BooleanField(default=True)
    mensaje_error = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logs"."admin_logs'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.accion} en {self.modelo_afectado}"


class CambiosBD(models.Model):
    """Auditoría de cambios en base de datos"""
    timestamp = models.DateTimeField(auto_now_add=True)
    esquema = models.CharField(max_length=50, default='public')
    tabla = models.CharField(max_length=100)
    operacion = models.CharField(max_length=20)  # INSERT, UPDATE, DELETE
    registro_id = models.IntegerField(blank=True, null=True)
    usuario_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    session_id = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    campos_modificados = models.JSONField(blank=True, null=True)  # Array de strings
    valores_anteriores = models.JSONField(blank=True, null=True)
    valores_nuevos = models.JSONField(blank=True, null=True)
    consulta_sql = models.TextField(blank=True, null=True)
    aplicacion = models.CharField(max_length=50, default='web')
    transaccion_id = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'auditoria"."cambios_bd'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.operacion} en {self.tabla}"
