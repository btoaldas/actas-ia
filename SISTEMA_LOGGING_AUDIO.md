# 📋 Sistema de Logging y Auditoría - Audio Processing

## 🎯 **IMPLEMENTACIÓN COMPLETADA**

Se ha implementado un **sistema completo de logging y auditoría** para el módulo de procesamiento de audio que registra automáticamente todas las acciones del usuario en las tablas de auditoría de la base de datos.

---

## 🔧 **COMPONENTES IMPLEMENTADOS**

### 1. **Helper de Logging** (`apps/audio_processing/logging_helper.py`)

**Funciones principales:**
- `log_sistema()` - Logs generales del sistema  
- `log_navegacion()` - Navegación del usuario
- `log_admin_action()` - Acciones administrativas
- `log_archivo_operacion()` - Operaciones con archivos
- `log_procesamiento_audio()` - Específico para procesamiento de audio
- `log_error_procesamiento()` - Errores del módulo

**Características:**
- ✅ Inserción directa en BD usando SQL crudo para evitar problemas con modelos unmanaged
- ✅ Manejo de errores con fallback a logging de Python
- ✅ Extracción automática de IP, User Agent, y datos de request
- ✅ Soporte para requests anónimos y autenticados

### 2. **Middleware de Auditoría** (`apps/audio_processing/audit_middleware.py`)

**Funcionalidades:**
- ✅ Captura automática de todas las URLs del módulo `audio_processing`
- ✅ Medición de tiempo de respuesta
- ✅ Mapeo de URLs a acciones descriptivas
- ✅ Logging selectivo solo para acciones importantes
- ✅ Manejo de errores sin afectar la aplicación

### 3. **Vistas con Logging Integrado**

**Vistas modificadas:**
- ✅ `lista_procesamientos()` - Log de listado con filtros aplicados
- ✅ `detalle_procesamiento()` - Log de visualización de detalles
- ✅ `confirmar_eliminar_procesamiento()` - Log de confirmación
- ✅ `eliminar_procesamiento()` - Log completo de eliminación
- ✅ `editar_procesamiento()` - Log de edición con cambios
- ✅ `api_procesar_audio()` - Log de creación de procesamientos

**Datos capturados:**
- 📝 Información del procesamiento afectado
- 📝 Campos modificados (antes/después)
- 📝 Metadatos del archivo
- 📝 Tiempo de operación
- 📝 Errores y stack traces
- 📝 Información del usuario y sessión

### 4. **Comando de Testing** (`test_audio_logging`)

**Pruebas disponibles:**
```bash
docker exec -it actas_web python manage.py test_audio_logging --test-type=all
docker exec -it actas_web python manage.py test_audio_logging --test-type=sistema
docker exec -it actas_web python manage.py test_audio_logging --test-type=admin
docker exec -it actas_web python manage.py test_audio_logging --test-type=archivo
docker exec -it actas_web python manage.py test_audio_logging --test-type=procesamiento
```

---

## 📊 **TABLAS DE AUDITORÍA UTILIZADAS**

### **logs.sistema_logs**
- Logs generales del sistema
- Nivel, categoría, subcategoría
- Datos extra en JSON
- Tiempo de respuesta
- Información de request

### **logs.navegacion_usuarios**  
- Navegación específica del usuario
- URLs visitadas y acciones
- Tiempo de permanencia
- Datos de formularios
- Elementos interactuados

### **logs.admin_logs**
- Acciones administrativas CRUD
- Campos modificados
- Valores anteriores/nuevos
- Información de la operación

### **logs.archivo_logs**
- Operaciones con archivos
- Upload, download, delete
- Metadatos del archivo
- Resultado de la operación

---

## 🎯 **ACCIONES AUDITADAS**

### **📋 Navegación y Acceso**
- ✅ Listado de procesamientos (con filtros)
- ✅ Visualización de detalles  
- ✅ Acceso al centro de audio
- ✅ Acceso a APIs y estadísticas

### **✏️ Operaciones CRUD**
- ✅ **Crear procesamiento**: Archivo, metadatos, configuración
- ✅ **Editar procesamiento**: Campos modificados, valores antes/después
- ✅ **Eliminar procesamiento**: Confirmación + eliminación real
- ✅ **Ver procesamiento**: Acceso a detalles y logs

### **📁 Operaciones con Archivos**
- ✅ **Upload de audio**: Tamaño, tipo, metadatos FFmpeg
- ✅ **Eliminación de archivos**: Cuando se elimina procesamiento  
- ✅ **Procesamiento de audio**: Inicio y estados

### **🚨 Errores y Problemas**
- ✅ **Errores de validación**: Formularios, tipos de archivo
- ✅ **Errores de procesamiento**: Stack traces completos
- ✅ **Intentos no autorizados**: Acceso denegado
- ✅ **Fallos del sistema**: Problemas de BD, Celery, etc.

---

## 🔍 **CÓMO MONITOREAR**

### **1. Desde Django Admin**
Acceder a las tablas de auditoría a través del admin de Django (si están registradas)

### **2. Consultas SQL Directas**
```sql
-- Logs recientes del módulo de audio
SELECT * FROM logs.sistema_logs 
WHERE modulo = 'audio_processing' 
ORDER BY timestamp DESC LIMIT 50;

-- Navegación de un usuario específico
SELECT * FROM logs.navegacion_usuarios 
WHERE usuario_id = 1 
AND url_visitada LIKE '%audio%'
ORDER BY timestamp DESC;

-- Acciones administrativas
SELECT * FROM logs.admin_logs 
WHERE modelo_afectado = 'ProcesamientoAudio'
ORDER BY timestamp DESC;

-- Operaciones con archivos
SELECT * FROM logs.archivo_logs 
WHERE operacion IN ('UPLOAD', 'DELETE')
ORDER BY timestamp DESC;
```

### **3. Logs por Categorías**
```sql
-- Procesamientos creados
SELECT * FROM logs.sistema_logs 
WHERE categoria = 'PROCESAMIENTO_CREADO';

-- Procesamientos eliminados  
SELECT * FROM logs.sistema_logs 
WHERE categoria = 'PROCESAMIENTO_ELIMINADO';

-- Errores del módulo
SELECT * FROM logs.sistema_logs 
WHERE categoria LIKE '%ERROR%' 
AND modulo = 'audio_processing';
```

---

## ⚡ **RENDIMIENTO Y CONFIGURACIÓN**

### **Optimizaciones Aplicadas**
- ✅ Inserción SQL directa (más rápida que ORM)
- ✅ Logging asíncrono cuando es posible
- ✅ Filtrado selectivo de acciones importantes
- ✅ Manejo de errores sin afectar UX
- ✅ Fallback a logging de Python si falla BD

### **Configuración de Logs**
Los logs se configuran en `settings.py`:
```python
LOGGING = {
    'loggers': {
        'audio_processing': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        }
    }
}
```

---

## 🚀 **PRÓXIMOS PASOS**

1. **Activar el middleware** en `settings.py`:
```python
MIDDLEWARE = [
    # ... otros middlewares
    'apps.audio_processing.audit_middleware.AudioProcessingAuditMiddleware',
]
```

2. **Probar el sistema** con el comando de testing:
```bash
docker exec -it actas_web python manage.py test_audio_logging
```

3. **Verificar logs en la base de datos** después de usar la aplicación

4. **Configurar alertas** para errores críticos (opcional)

---

## ✅ **ESTADO ACTUAL**

- ✅ **Helper de logging**: Implementado y funcional
- ✅ **Middleware de auditoría**: Implementado 
- ✅ **Vistas con logging**: Todas las vistas críticas tienen logging
- ✅ **Comando de testing**: Disponible para pruebas
- ✅ **Documentación**: Completa

**El sistema está listo para usar. Solo falta activar el middleware en settings.py y probar.**
