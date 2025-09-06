# 🔍 Sistema de Logs y Auditoría - Actas Municipales

## 📋 Descripción General

Este sistema proporciona **auditoría completa y logging automático** para todas las actividades del sistema de Actas Municipales, incluyendo:

- 🔐 **Accesos y autenticación** de usuarios
- 🌐 **Navegación** y actividad en páginas web  
- 🔄 **Cambios en base de datos** (automático con triggers)
- ⚙️ **Procesos en segundo plano** (Celery)
- 🖥️ **Actividad frontend** (JavaScript)
- ❌ **Errores del sistema** y excepciones
- 📊 **Métricas de rendimiento**

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA DE AUDITORÍA                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   BACKEND   │  │  FRONTEND   │  │   CELERY    │        │
│  │ (Django)    │  │ (JavaScript)│  │  (Tasks)    │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │               │
│  ┌──────▼──────────────────▼────────────────▼─────────────┐ │
│  │              MIDDLEWARE DE AUDITORÍA                  │ │
│  └─────────────────────────┬─────────────────────────────┘ │
│                            │                               │
│  ┌─────────────────────────▼─────────────────────────────┐ │
│  │                   BASE DE DATOS                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │ │
│  │  │ logs.*      │  │auditoria.*  │  │  triggers    │  │ │
│  │  │ (8 tablas)  │  │ (cambios)   │  │ (automático) │  │ │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Tablas de la Base de Datos

### Esquema `logs`
1. **`logs.sistema_logs`** - Logs generales del sistema
2. **`logs.acceso_usuarios`** - Login/logout y accesos
3. **`logs.navegacion_usuarios`** - Páginas visitadas y navegación
4. **`logs.celery_logs`** - Tareas en segundo plano
5. **`logs.api_logs`** - Llamadas a APIs
6. **`logs.archivo_logs`** - Subida/descarga de archivos
7. **`logs.errores_sistema`** - Errores y excepciones
8. **`logs.admin_logs`** - Cambios de configuración

### Esquema `auditoria`
1. **`auditoria.cambios_bd`** - Cambios automáticos en BD (INSERT/UPDATE/DELETE)

## 🚀 Instalación y Configuración

### Paso 1: Instalación Automática
```powershell
# Instalación completa con verificación
.\scripts\instalar_sistema_auditoria.ps1

# Solo mostrar qué se haría sin instalar
.\scripts\instalar_sistema_auditoria.ps1 -SoloMostrar

# Incluir auditoría en tablas de usuarios Django
.\scripts\instalar_sistema_auditoria.ps1 -IncluirTablasUsuarios

# Activar logging frontend y Celery
.\scripts\instalar_sistema_auditoria.ps1 -ActivarFrontend -ActivarCelery
```

### Paso 2: Configuración Manual (si es necesario)

1. **Ejecutar migración SQL:**
```bash
python manage.py shell -c "
from django.db import connection
with open('scripts/migrations/2025-09-06_sistema_logs_auditoria.sql', 'r') as f:
    with connection.cursor() as cursor:
        cursor.execute(f.read())
"
```

2. **Configurar triggers de auditoría:**
```bash
python manage.py setup_auditoria
```

3. **Incluir frontend en templates:**
```html
<!-- En tu template base -->
{% include 'includes/frontend_audit_script.html' %}
```

## 📈 Uso del Sistema

### Logging Automático

El sistema registra **automáticamente**:
- ✅ Todas las requests HTTP (GET, POST, PUT, DELETE)
- ✅ Accesos de usuarios (login, logout, intentos fallidos)
- ✅ Navegación entre páginas
- ✅ Cambios en cualquier tabla de la BD
- ✅ Errores y excepciones
- ✅ Tareas Celery (inicio, fin, errores)

### Logging Manual

Para casos específicos, usa estas funciones:

#### Python/Django
```python
from helpers.auditoria_middleware import log_activity

# Decorador para funciones
@log_activity(categoria='ACTA', subcategoria='CREATE', mensaje='Nueva acta creada')
def crear_acta(request):
    # tu código aquí
    pass

# Logging directo
from django.db import connection
import json

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT logs.registrar_log_sistema(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        'INFO',  # nivel
        'ACTA',  # categoria  
        'CREATE',  # subcategoria
        'Acta municipal creada exitosamente',  # mensaje
        request.user.id,  # usuario_id
        request.session.session_key,  # session_id
        get_client_ip(request),  # ip_address
        json.dumps({'acta_id': 123}),  # datos_extra
        'pages',  # modulo
        request.get_full_path(),  # url
        'POST',  # metodo_http
        500,  # tiempo_respuesta_ms
        201   # codigo_respuesta
    ])
```

#### JavaScript/Frontend
```javascript
// Eventos personalizados
logCustomEvent('ACTA_CREATED', 'MUNICIPAL', { 
    acta_id: 123, 
    tipo: 'ordinaria' 
});

// Archivos
logFileUpload('acta_2025_01.pdf', 1024000, 'application/pdf');
logFileDownload('acta_2025_01.pdf', '/media/actas/acta_2025_01.pdf');

// Búsquedas
logSearch('presupuesto 2025', 15);
```

#### Celery (Tareas)
```python
from helpers.celery_logging import logged_task

# Decorador automático
@logged_task
def procesar_acta(self, user_id, acta_data):
    # tu código aquí
    return resultado

# Logging manual
from helpers.celery_logging import CeleryAuditLogger

CeleryAuditLogger.log_celery_task(
    task_id='unique-task-id',
    task_name='procesar_acta', 
    estado='SUCCESS',
    usuario_que_inicio_id=1,
    resultado={'processed': True}
)
```

## 📊 Consultas y Reportes

### Vistas Predefinidas

```sql
-- Actividad de usuarios (últimos 30 días)
SELECT * FROM logs.vista_actividad_usuarios;

-- Errores recientes (últimos 7 días)  
SELECT * FROM logs.vista_errores_recientes;

-- Páginas más visitadas (últimos 30 días)
SELECT * FROM logs.vista_paginas_populares;
```

### Consultas Personalizadas

```sql
-- Top 10 usuarios más activos
SELECT 
    u.username,
    COUNT(*) as total_acciones,
    MAX(s.timestamp) as ultimo_acceso
FROM logs.sistema_logs s
JOIN auth_user u ON s.usuario_id = u.id
WHERE s.timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY u.id, u.username
ORDER BY total_acciones DESC
LIMIT 10;

-- Errores por día (último mes)
SELECT 
    DATE(timestamp) as fecha,
    nivel_error,
    COUNT(*) as total_errores
FROM logs.errores_sistema
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(timestamp), nivel_error
ORDER BY fecha DESC, nivel_error;

-- Cambios en tabla específica
SELECT 
    timestamp,
    operacion,
    username,
    campos_modificados,
    valores_anteriores,
    valores_nuevos
FROM auditoria.cambios_bd c
LEFT JOIN auth_user u ON c.usuario_id = u.id
WHERE tabla = 'pages_acta'  -- cambiar por tu tabla
ORDER BY timestamp DESC
LIMIT 50;

-- Sesiones más largas
SELECT 
    usuario_id,
    username,
    session_id,
    MIN(timestamp) as inicio_sesion,
    MAX(timestamp) as fin_sesion,
    EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))/60 as duracion_minutos
FROM logs.navegacion_usuarios n
LEFT JOIN auth_user u ON n.usuario_id = u.id
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY usuario_id, username, session_id
HAVING COUNT(*) > 5
ORDER BY duracion_minutos DESC
LIMIT 20;
```

## 🔧 APIs de Estadísticas

### Estadísticas Frontend
```bash
# GET /api/frontend-stats/?dias=7
curl "http://localhost:8000/api/frontend-stats/?dias=7"
```

### Timeline de Usuario
```bash
# GET /api/user-activity-timeline/?user_id=1&dias=1
curl "http://localhost:8000/api/user-activity-timeline/?user_id=1&dias=1"
```

## 🧹 Mantenimiento

### Limpiar Logs Antiguos

```sql
-- Limpiar logs mayores a 90 días
SELECT * FROM logs.limpiar_logs_antiguos(90);

-- Ver resultados de limpieza
SELECT tabla, registros_eliminados 
FROM logs.limpiar_logs_antiguos(90);
```

### PowerShell
```powershell
# Limpiar logs de demostración
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT * FROM logs.limpiar_logs_antiguos(90)')
    for row in cursor.fetchall():
        print(f'Tabla: {row[0]}, Eliminados: {row[1]}')
"
```

### Configurar Limpieza Automática (Cron)

```bash
# Agregar a crontab (Linux) o Task Scheduler (Windows)
# Ejecutar cada domingo a las 3 AM
0 3 * * 0 cd /path/to/actas.ia && python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); import django; django.setup(); from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT logs.limpiar_logs_antiguos(90)')"
```

## 📁 Archivos del Sistema

```
scripts/
├── migrations/
│   └── 2025-09-06_sistema_logs_auditoria.sql     # Crear tablas y funciones
├── instalar_sistema_auditoria.ps1                # Script de instalación
└── demo_sistema_auditoria.ps1                    # Script de demostración

helpers/
├── auditoria_middleware.py                       # Middleware Django
└── celery_logging.py                            # Logging para Celery

apps/
├── tasks/management/commands/
│   └── setup_auditoria.py                       # Comando Django
└── dyn_api/
    ├── views_frontend_logs.py                   # API para frontend
    └── urls.py                                  # URLs de API

templates/includes/
└── frontend_audit_script.html                   # Template para frontend

static/js/
└── frontend-audit-logger.js                     # JavaScript de auditoría

logs/                                            # Directorio de logs
├── actas_general.log
├── auditoria.log  
├── celery_audit.log
├── frontend_audit.log
└── errores_sistema.log
```

## 🧪 Pruebas y Demostración

### Ejecutar Demo
```powershell
# Demostración completa
.\scripts\demo_sistema_auditoria.ps1

# Solo estadísticas básicas
.\scripts\demo_sistema_auditoria.ps1 -TipoDemo basico

# Solo reportes
.\scripts\demo_sistema_auditoria.ps1 -TipoDemo reportes
```

### Verificar Estado
```bash
# Verificar configuración
python manage.py setup_auditoria --solo-mostrar

# Ver logs en tiempo real
Get-Content logs\auditoria.log -Wait

# Estadísticas rápidas
.\scripts\demo_sistema_auditoria.ps1 -TipoDemo reportes
```

## ⚡ Optimización y Rendimiento

### Índices Automáticos
El sistema crea automáticamente índices optimizados para:
- Búsquedas por usuario y fecha
- Filtros por categoría y nivel de error
- Consultas de rendimiento
- Análisis de sesiones

### Configuración de Retención
En `settings.py` puedes configurar:
```python
AUDITORIA_CONFIG = {
    'RETENTION_DAYS_NAVIGATION': 60,    # Navegación: 2 meses
    'RETENTION_DAYS_SYSTEM_LOGS': 90,   # Logs sistema: 3 meses  
    'RETENTION_DAYS_ACCESS_LOGS': 180,  # Accesos: 6 meses
    'RETENTION_DAYS_AUDIT_CHANGES': 365,# Cambios BD: 1 año
    'RETENTION_DAYS_ERROR_LOGS': 180,   # Errores: 6 meses
}
```

## 🔒 Seguridad y Privacidad

### Datos Sensibles
El sistema **automáticamente** excluye de los logs:
- Contraseñas y campos de autenticación
- Tokens de API y secretos
- Números de tarjetas de crédito
- Números de cédula y documentos
- Campos marcados como sensibles

### Control de Acceso
- Los logs solo son accesibles por **staff users**
- Las APIs requieren autenticación
- Los errores se registran sin datos sensibles
- IPs y user agents se registran para auditoría

## 🚨 Troubleshooting

### Problemas Comunes

1. **Middleware no registra eventos**
   ```python
   # Verificar que esté en MIDDLEWARE en settings.py
   "helpers.auditoria_middleware.AuditoriaMiddleware",
   ```

2. **Frontend no envía logs**
   ```html
   <!-- Verificar que esté incluido en el template -->
   {% include 'includes/frontend_audit_script.html' %}
   ```

3. **Triggers no funcionan**
   ```bash
   # Ejecutar comando de configuración
   python manage.py setup_auditoria
   ```

4. **Error de conexión a BD**
   ```bash
   # Verificar que PostgreSQL esté funcionando
   docker-compose ps
   ```

### Logs de Debug
```python
# Activar logging debug en settings.py
LOGGING['loggers']['auditoria']['level'] = 'DEBUG'
LOGGING['loggers']['frontend_audit']['level'] = 'DEBUG'
LOGGING['loggers']['celery_audit']['level'] = 'DEBUG'
```

## 📚 Recursos Adicionales

- 📄 **CHANGELOG.md** - Historial de cambios
- 🔧 **GUIA_RAPIDA.md** - Guía rápida de uso (en scripts/)
- 📊 **Vistas de PostgreSQL** - Reportes predefinidos
- 🔍 **APIs REST** - Endpoints para integración

---

**✨ ¡El sistema de auditoría está listo para proteger y monitorear todas las actividades del Sistema de Actas Municipales de Pastaza!**
