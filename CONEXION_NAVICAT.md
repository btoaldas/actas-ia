# 🗄️ CONEXIÓN A BASE DE DATOS - NAVICAT

> ⚠️ **NOTA IMPORTANTE**: Si obtienes "Connection Refused" desde fuera de Docker, ejecuta:
> ```bash
> docker-compose restart db_postgres
> Start-Sleep 10  # Esperar 10 segundos
> ```
> Esto resuelve el problema común de Docker Desktop en Windows.

## 📋 **INFORMACIÓN DE CONEXIÓN POSTGRESQL**

### **Datos de Conexión Principal**
```
Tipo de Conexión: PostgreSQL
Host/Servidor:    localhost
Puerto:           5432
Base de Datos:    actas_municipales_pastaza
Usuario:          admin_actas
Contraseña:       actas_pastaza_2025
```

### **Usuario Adicional (Desarrollo)**
```
Usuario:          desarrollador_actas
Contraseña:       dev_actas_2025
```

---

## 🔧 **CONFIGURACIÓN PASO A PASO EN NAVICAT**

### **1. Crear Nueva Conexión**
1. Abrir Navicat
2. Hacer clic en "Connection" → "PostgreSQL"
3. Configurar los siguientes campos:

### **2. Configuración de Conexión**
```
Connection Name:  Actas IA - Municipio Pastaza
Host:            localhost  
Port:            5432
Database:        actas_municipales_pastaza
User Name:       admin_actas
Password:        actas_pastaza_2025
```

### **3. Configuraciones Avanzadas (Opcional)**
```
SSL Mode:        prefer
Connection Timeout: 30
Query Timeout:   30
```

---

## 🔍 **VERIFICAR CONEXIÓN**

### **Desde Terminal (Verificación previa)**
```bash
# Verificar que PostgreSQL esté corriendo
docker ps | findstr postgres

# Probar conexión directa (dentro de Docker)
docker exec -it actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "SELECT version();"

# Verificar que el puerto esté expuesto al host (Windows)
netstat -an | findstr :5432

# Si no aparece el puerto, reiniciar PostgreSQL:
docker-compose restart db_postgres
Start-Sleep 10
netstat -an | findstr :5432
```

### **Verificación de Conectividad TCP (sin psql)**
```bash
# Método 1: Usando PowerShell (recomendado)
Test-NetConnection -ComputerName localhost -Port 5432

# Resultado esperado: TcpTestSucceeded : True

# Método 2: Usando telnet
telnet localhost 5432

# Si telnet se conecta (aunque no muestre respuesta), la conexión TCP funciona
# Resultado esperado: NO aparece "Connection refused"
```

### **URL de Conexión Completa**
```
postgresql://admin_actas:actas_pastaza_2025@localhost:5432/actas_municipales_pastaza
```

---

## 📊 **ESTRUCTURA DE LA BASE DE DATOS**

### **Apps Django Principales**
- **`auth_*`** - Sistema de autenticación Django
- **`config_system_*`** - Usuarios, permisos, configuraciones
- **`audio_processing_*`** - Procesamiento de audio
- **`transcripcion_*`** - Transcripciones y diarización
- **`generador_actas_*`** - Generación de actas con IA
- **`pages_*`** - Actas municipales y portal ciudadano
- **`auditoria_*`** - Logs y auditoría del sistema

### **Tablas Importantes**
```sql
-- Usuarios del sistema
SELECT * FROM auth_user;

-- Perfiles y permisos
SELECT * FROM config_system_perfilusuario;

-- Procesamiento de audio
SELECT * FROM audio_processing_procesamientoaudio;

-- Transcripciones
SELECT * FROM transcripcion_transcripcioncompleta;

-- Actas generadas
SELECT * FROM generador_actas_actamunicipal;
```

---

## ⚠️ **TROUBLESHOOTING**

### **Error: "Connection Refused"**
```bash
# 1. Verificar que Docker esté corriendo
docker ps

# 2. Si no hay contenedores, iniciar sistema
.\iniciar_actas_ia.bat

# 3. SOLUCIÓN COMÚN: Reiniciar PostgreSQL si el puerto no está expuesto
docker-compose restart db_postgres

# 4. Esperar 10 segundos y verificar puerto
Start-Sleep 10
netstat -an | findstr :5432

# 5. Resultado esperado: debería mostrar
# TCP    0.0.0.0:5432           0.0.0.0:0              LISTENING
```

### **Error: Puerto 5432 no está disponible desde Windows**
Este es un problema común de Docker Desktop. **SOLUCIÓN:**
```bash
# Reiniciar específicamente el contenedor PostgreSQL
docker-compose restart db_postgres

# Verificar que el puerto esté escuchando (después de 10 segundos)
netstat -an | findstr :5432
```

Si el comando anterior muestra `TCP    0.0.0.0:5432` entonces ya está solucionado.

### **Error: "Authentication Failed"**
- Verificar usuario y contraseña exactos
- Usar `admin_actas` (no `admin_acta`)
- Contraseña: `actas_pastaza_2025` (exacta)

### **Error: "Database does not exist"**
```bash
# Verificar nombre de BD
docker exec -it actas_postgres psql -U admin_actas -l
```

### **Puerto Ocupado o No Disponible**
```bash
# Verificar puerto PostgreSQL
netstat -an | findstr :5432

# Reiniciar servicios si es necesario
docker-compose restart db_postgres
```

---

## 🔒 **SEGURIDAD Y ACCESOS**

### **Permisos del Usuario `admin_actas`**
- ✅ Superusuario de PostgreSQL
- ✅ Acceso completo a todas las tablas
- ✅ Permisos de creación y eliminación
- ✅ Acceso a schemas y funciones

### **Permisos del Usuario `desarrollador_actas`**
- ✅ Acceso de lectura/escritura
- ✅ Limitado a base de datos específica
- ❌ Sin permisos administrativos

---

## 📝 **QUERIES ÚTILES PARA NAVICAT**

### **Verificar Estado del Sistema**
```sql
-- Contar usuarios activos
SELECT COUNT(*) as usuarios_activos 
FROM auth_user 
WHERE is_active = true;

-- Ver últimos procesamientos de audio
SELECT titulo, estado, fecha_creacion 
FROM audio_processing_procesamientoaudio 
ORDER BY fecha_creacion DESC 
LIMIT 10;

-- Transcripciones recientes
SELECT estado, tiempo_inicio_proceso, duracion_audio
FROM transcripcion_transcripcioncompleta 
WHERE tiempo_inicio_proceso IS NOT NULL
ORDER BY tiempo_inicio_proceso DESC;

-- Estadísticas de la BD
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public' 
ORDER BY tablename;
```

### **Consultas de Auditoría**
```sql
-- Ver logs de auditoría
SELECT usuario_id, accion, timestamp, detalles 
FROM auditoria_registroauditoria 
ORDER BY timestamp DESC 
LIMIT 20;

-- Actividad de usuarios
SELECT 
    u.username,
    u.email,
    u.last_login,
    u.date_joined
FROM auth_user u 
ORDER BY last_login DESC NULLS LAST;
```

---

## 🚀 **COMANDOS RÁPIDOS DE CONEXIÓN**

### **Conexión Directa por Terminal**
```bash
# Conexión con psql (dentro de Docker)
docker exec -it actas_postgres psql -U admin_actas -d actas_municipales_pastaza

# Conexión externa (si PostgreSQL Client instalado)
psql -h localhost -p 5432 -U admin_actas -d actas_municipales_pastaza
```

### **Backup y Restore desde Navicat**
- **Backup:** Tools → Data Transfer → Export
- **Restore:** Tools → Data Transfer → Import
- **SQL Dump:** Tools → Data Transfer → Structure and Data

---

## 📞 **INFORMACIÓN DE SOPORTE**

### **Contenedor Docker**
```
Nombre del Contenedor: actas_postgres
Imagen: postgres:15-alpine
Estado: Debe estar "Up" y "Running"
```

### **Archivos de Configuración**
```
Docker Compose: docker-compose.yml
Variables de entorno: .env
Backup actual: backups/backup_completo_2025-09-27_16-11-33.sql
```

### **Logs de PostgreSQL**
```bash
# Ver logs del contenedor PostgreSQL
docker logs actas_postgres

# Ver logs en tiempo real
docker logs -f actas_postgres
```

---

## ✅ **VERIFICACIÓN FINAL**

Una vez conectado en Navicat, ejecutar esta query para verificar:

```sql
SELECT 
    current_database() as base_datos,
    current_user as usuario_actual,
    version() as version_postgresql,
    current_timestamp as fecha_conexion;
```

**Resultado esperado:**
```
base_datos: actas_municipales_pastaza
usuario_actual: admin_actas
version_postgresql: PostgreSQL 15.x
fecha_conexion: 2025-09-27 [timestamp actual]
```

---

## 📋 **RESUMEN RÁPIDO PARA NAVICAT**

```
🌐 Host:     localhost
🔌 Puerto:   5432
🗄️ BD:       actas_municipales_pastaza
👤 Usuario:  admin_actas
🔑 Clave:    actas_pastaza_2025
```

¡Ya tienes toda la información necesaria para conectarte! Si tienes algún problema con la conexión, hazme saber y te ayudo a solucionarlo.