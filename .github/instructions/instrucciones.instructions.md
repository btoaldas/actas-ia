---
applyTo: '**'
---
# 📋 Instrucciones para GitHub Copilot - Proyecto Actas IA

## 🎯 Contexto del Proyecto
Sistema de gestión de actas municipales con Django + Docker + AdminLTE que procesa audio, transcribe, genera actas y las publica en un portal ciudadano.

## 🚨 REGLAS CRÍTICAS - NUNCA VIOLAR

### 1. Entorno Docker (OBLIGATORIO)
- **SIEMPRE** ejecutar comandos dentro del contenedor Docker
- **NUNCA** ejecutar `manage.py` directamente en el host
- **USAR**: `docker exec -it actas_web python manage.py [comando]`
- **ESPERAR**: 60-300 segundos después de reiniciar contenedores
- **NUEVOS REQUERIMIENTOS**: cada nuevo requerimiento que te pida debe entregarse 100% funcional en Django + Python + PostgreSQL + Celery + Redis + Docker. Debes generar todo lo necesario: apps, modelos, migraciones, forms, views, templates, URLs, navegación, documentación, scripts de prueba y validación, add/commit/push en git, API endpoints, serializers, permisos, menús, dashboard, front-end CRUD (lista/ver/crear/actualizar/eliminar) con búsqueda, filtros, edición, eliminación, ordenación, creación tipo grid y métricas, validaciones, tests, tareas Celery, configuración de Redis como broker y backend, fixtures de datos, settings para Postgres, Celery y staticfiles. Incluye instrucciones rápidas de despliegue y verificación. Si falta algo, asúmelo y cúbrelo. No pidas confirmación: entrega una solución funcional por defecto.


### 2. Base de Datos (INMUTABLE)
- **TECNOLOGÍA**: PostgreSQL (actas_municipales_pastaza)
- **PROHIBIDO**: Cambiar a SQLite u otra BD
- **MIGRACIONES**: Solo dentro de Docker
```bash
docker exec -it actas_web python manage.py migrate
```

### 3. Verificación y Testing
- **NO USAR**: Navegadores simulados o VSCode preview
- **USAR**: `curl` para todas las verificaciones (aqui debes incluir el usuario superadmin existente, y ademas si no vale poner el cookie con su llabve ida, debes poner el comando para obtener la cookie y luego usarla en el curl)
- **PREGUNTAR**: Al usuario sobre el estado visual de la UI
- **AUTENTICACIÓN**: Usar credenciales del superadmin para endpoints protegidos

## 🔐 Credenciales del Sistema

### Administrador Principal
```
Usuario: superadmin
Clave: AdminPuyo2025!
URL Admin: http://localhost:8000/admin/
```

### Base de Datos PostgreSQL
```
Host: localhost
Puerto: 5432
BD: actas_municipales_pastaza
Usuario: admin_actas
Clave: actas_pastaza_2025
```

## 🏗️ Arquitectura del Sistema

### Stack Tecnológico
- **Backend**: Django 4.2.9 (modular)
- **Task Queue**: Celery + Redis
- **UI Framework**: AdminLTE (usar sus clases/componentes)
- **Audio Processing**: Whisper + pyannote
- **Database**: PostgreSQL
- **Container**: Docker Compose

- para cualquier cambio se debe trabakar con todos los entornocs y coenxiones posibles 

### Apps Principales
- `audio_processing` - Procesamiento de audio
- `transcripcion` - Transcripción y diarización
- `auditoria` - Logging y auditoría
- `pages/portal_ciudadano` - Portal público

### Pipeline de Procesamiento
```
Ingesta → Mejora Audio → Transcripción (Whisper) → 
Diarización (pyannote) → Curado → Generación Acta → 
Aprobación → Publicación → Archivo
```

## 📝 Flujo de Trabajo Operativo

### 1. Antes de Modificar Código
```bash
# Verificar estado actual
docker logs --tail=20 actas_web
docker logs --tail=20 actas_celery_worker
```

### 2. Al Modificar Código

#### Cambios de Backend/API
- NO reiniciar Docker si solo son cambios de código
- Esperar 60 segundos después de cambios significativos
- Verificar logs después de esperar

#### Cambios de Infraestructura
- Reiniciar Docker SOLO si hay cambios en:
  - Configuración de contenedores
  - Variables de entorno
  - Dependencias del sistema

### 3. Verificación con curl

#### Autenticación
```bash
# Obtener CSRF token
curl -c cookies.txt http://localhost:8000/admin/login/ | grep csrfmiddlewaretoken

# Login
curl -b cookies.txt -c cookies.txt -X POST \
  -d "username=superadmin&password=AdminPuyo2025!&csrfmiddlewaretoken=[TOKEN]" \
  http://localhost:8000/admin/login/
```

#### Verificar Endpoints
```bash
# Portal ciudadano
curl -I http://localhost:8000/portal-ciudadano/

# API (autenticado)
curl -b cookies.txt http://localhost:8000/api/[endpoint]/
```

## 🎨 Convenciones de Código

### Estructura de Archivos
- **JavaScript/CSS**: Separar en archivos `.js` y `.css` independientes
- **Templates**: Usar estructura de AdminLTE
- **Backups**: Guardar en `scripts/backup/YYYY-MM-DD_backup_[nombre].ext`

### Naming Conventions
- **Tareas Celery**: `procesar_audio_*`, `procesar_transcripcion_*`
- **Estados Workflow**: Ingestado → Optimizado → Transcrito → Curado → etc.
- **JSONFields**: Usar llaves semánticas `{"snr": 23.1, "modelo": "whisper-medium"}`

### Mejores Prácticas
1. **NO exponer credenciales** - Usar variables de entorno (.env)
2. **Reutilizar helpers existentes** antes de crear nuevos
3. **Usar clases AdminLTE** - No crear CSS personalizado innecesario
4. **Verificar FileFields** antes de usar `.url` o `.path`
5. **Optimizar queries** - usar `prefetch_related`/`select_related`

## 🔄 Proceso de Cambios

### 1. Desarrollo
```bash
# Hacer cambios en el código
# Esperar 60 segundos si son cambios significativos
docker logs --tail=50 actas_web
```

### 2. Migraciones (si aplica)
```bash
docker exec -it actas_web python manage.py makemigrations
docker exec -it actas_web python manage.py migrate
```

### 3. Verificación
```bash
# Verificar con curl
curl -b cookies.txt http://localhost:8000/[endpoint]/

# Revisar logs
docker logs --tail=20 actas_web
```

### 4. Git (Preguntar al usuario)
```bash
# SIEMPRE preguntar: "¿Deseas hacer add, commit y push?"
# Si responde SÍ:
git add .
git commit -m "[descripción del cambio]"
git push
```

## ⚠️ Comandos Docker Esenciales

```bash
# Ver logs en tiempo real
docker logs -f actas_web

# Ejecutar comandos Django
docker exec -it actas_web python manage.py [comando]

# Crear usuarios iniciales
docker exec -it actas_web python manage.py crear_usuarios_iniciales

# Inicializar permisos
docker exec -it actas_web python manage.py init_permissions_system

# Reiniciar contenedor (SOLO si necesario)
docker-compose restart actas_web
```

## 🚫 Errores Comunes a Evitar

1. **NO** usar `docker-compose.simple.yml` (no existe)
2. **NO** cambiar la BD a SQLite
3. **NO** ejecutar comandos fuera de Docker
4. **NO** abrir navegadores para probar
5. **NO** reiniciar Docker innecesariamente
6. **NO** verificar inmediatamente después de reiniciar (esperar 60s)
7. **NO** duplicar nombres de vistas
8. **NO** hardcodear rutas de media

## ✅ Checklist Final

Antes de terminar cualquier tarea, verificar:

- [ ] ¿Migraciones aplicadas en Docker?
- [ ] ¿Logs limpios sin errores nuevos?
- [ ] ¿Fallbacks implementados para servicios externos?
- [ ] ¿Respetadas las configuraciones del administrador?
- [ ] ¿Usadas clases AdminLTE existentes?
- [ ] ¿Endpoints probados con curl?
- [ ] ¿Celery probado conectado con requerimiento actual?
- [ ] Backend correctamente conectado a las APIs, frontend, Celery y base de datos?
- [ ] ¿Usuario confirmó funcionamiento visual?
- [ ] ¿Preguntar si hacer git add/commit/push?

## 📌 Recordatorio Final

**SIEMPRE**:
- Trabajar dentro de Docker
- Esperar tiempos prudenciales
- Verificar con curl
- Preguntar al usuario sobre el estado visual
- Solicitar confirmación para git push

**NUNCA**:
- Cambiar la base de datos
- Exponer credenciales
- Usar navegadores simulados
- Reiniciar Docker sin necesidad

---
*Estas instrucciones son críticas para el funcionamiento correcto del sistema. Seguirlas al pie de la letra garantiza estabilidad y productividad.*