# 🏛️ Sistema de Actas Municipales - Municipio de Pastaza

Sistema integral para la gestión, procesamiento y publicación de actas municipales del Municipio de Pastaza (Puyo, Ecuador).

## 🚀 Características Principales

- **Grabación y Subida de Audio**: Interfaz para cargar archivos de audio de reuniones municipales
- **Transcripción Automática**: Procesamiento con Whisper AI para convertir audio a texto
- **Diarización de Hablantes**: Identificación automática de participantes con Pyannote
- **Procesamiento con IA**: Integración con OpenAI, DeepSeek, Anthropic y Ollama
- **Generación de Actas**: Conversión automática a formato de acta municipal formal
- **Sistema de Aprobaciones**: Flujo de trabajo para revisión y aprobación
- **Repositorio Público**: Publicación controlada con permisos y búsqueda avanzada
- **Procesamiento en Segundo Plano**: Celery y Redis para tareas asíncronas

## 🏗️ Arquitectura del Sistema

- **Backend**: Django 4.2.9 con PostgreSQL
- **Frontend**: Actas IA con Bootstrap
- **Procesamiento**: Celery + Redis
- **IA**: Whisper, Pyannote, OpenAI/DeepSeek/Anthropic/Ollama
- **Contenedorización**: Docker y Docker Compose

## 📋 Prerrequisitos

- Docker y Docker Compose
- Git
- Al menos 4GB de RAM disponible
- Puerto 8000, 5432 y 6379 disponibles

## 🚀 Inicio Rápido

### Opción 1: Script Automático (Recomendado para Windows)
```bash
# Ejecutar el script de inicio automático
iniciar_sistema.bat
```

### Opción 2: Comandos Manuales
```bash
# 1. Construir y levantar todos los servicios
docker-compose -f docker-compose.simple.yml build
docker-compose -f docker-compose.simple.yml up -d

# 2. Aplicar migraciones
docker-compose -f docker-compose.simple.yml exec web python manage.py migrate

# 3. Crear usuarios iniciales
docker-compose -f docker-compose.simple.yml exec web python manage.py crear_usuarios_iniciales

# 4. Verificar el funcionamiento
# Ir a http://localhost:8000
```

### ⏹️ Parar el Sistema
```bash
# Opción 1: Script automático
parar_sistema.bat

# Opción 2: Comando manual
docker-compose -f docker-compose.simple.yml down
```

## 👥 Usuarios Creados Automáticamente

El sistema crea automáticamente los siguientes usuarios:

| Usuario | Contraseña | Rol | Email |
|---------|------------|-----|-------|
| `superadmin` | `AdminPuyo2025!` | Super Administrador | admin@puyo.gob.ec |
| `alcalde.pastaza` | `AlcaldePuyo2025!` | Alcalde | alcalde@puyo.gob.ec |
| `secretario.concejo` | `SecretarioPuyo2025!` | Secretario del Concejo | secretario@puyo.gob.ec |
| `concejal1` | `ConcejalPuyo2025!` | Primer Concejal | concejal1@puyo.gob.ec |
| `concejal2` | `ConcejalPuyo2025!` | Segundo Concejal | concejal2@puyo.gob.ec |
| `operador.tecnico` | `TecnicoPuyo2025!` | Operador Técnico | tecnico@puyo.gob.ec |
| `ciudadano.demo` | `CiudadanoPuyo2025!` | Ciudadano Demo | ciudadano@ejemplo.com |

## 🗄️ Acceso a la Base de Datos

### Conexión Principal
- **Host**: localhost
- **Puerto**: 5432
- **Base de Datos**: actas_municipales_pastaza
- **Usuario**: admin_actas
- **Contraseña**: actas_pastaza_2025

### Usuario Adicional para Desarrollo
- **Usuario**: desarrollador_actas
- **Contraseña**: dev_actas_2025

### Cadena de Conexión
```
postgresql://admin_actas:actas_pastaza_2025@localhost:5432/actas_municipales_pastaza
```

## 🛠️ Comandos Útiles

### Docker
```bash
# Ver logs de todos los servicios
docker-compose -f docker-compose.dev.yml logs

# Ver logs de un servicio específico
docker-compose -f docker-compose.dev.yml logs web

# Reiniciar un servicio
docker-compose -f docker-compose.dev.yml restart web

# Parar todos los servicios
docker-compose -f docker-compose.dev.yml down

# Parar y eliminar volúmenes
docker-compose -f docker-compose.dev.yml down -v
```

### Django (dentro del contenedor)
```bash
# Ejecutar comandos Django
docker-compose -f docker-compose.dev.yml exec web python manage.py <comando>

# Crear migraciones
docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations

# Aplicar migraciones
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

# Crear superusuario adicional
docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser

# Recrear usuarios iniciales
docker-compose -f docker-compose.dev.yml exec web python manage.py crear_usuarios_iniciales --force
```

### Base de Datos
```bash
# Conectar a PostgreSQL
docker-compose -f docker-compose.dev.yml exec db_postgres psql -U admin_actas -d actas_municipales_pastaza

# Backup de la base de datos
docker-compose -f docker-compose.dev.yml exec db_postgres pg_dump -U admin_actas actas_municipales_pastaza > backup.sql

# Restaurar backup
docker-compose -f docker-compose.dev.yml exec -T db_postgres psql -U admin_actas actas_municipales_pastaza < backup.sql
```

## 📁 Estructura del Proyecto

```
actas.ia/
├── apps/                    # Aplicaciones Django
│   ├── charts/             # Gráficos y reportes
│   ├── dyn_api/            # APIs dinámicas
│   ├── dyn_dt/             # DataTables dinámicas
│   ├── file_manager/       # Gestor de archivos
│   ├── pages/              # Páginas principales
│   ├── react/              # Componentes React
│   ├── tasks/              # Tareas Celery
│   └── users/              # Gestión de usuarios
├── config/                 # Configuración Django
├── frontend/               # Frontend JavaScript
├── media/                  # Archivos subidos
│   ├── audios/            # Archivos de audio
│   ├── transcripciones/   # Transcripciones generadas
│   ├── actas/             # Actas procesadas
│   └── pdfs/              # PDFs generados
├── static/                 # Archivos estáticos
├── templates/              # Plantillas HTML
├── docker-compose.yml      # Producción
├── docker-compose.dev.yml  # Desarrollo
└── requirements.txt        # Dependencias Python
```

## 🔧 Configuración Adicional

### APIs de IA (Configurar después)
Para usar las funcionalidades de IA, agregar al archivo `.env`:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# DeepSeek
DEEPSEEK_API_KEY=...

# Anthropic
ANTHROPIC_API_KEY=...

# Ollama (local)
OLLAMA_URL=http://localhost:11434
```

### Configuración de Email
Para envío de correos electrónicos:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@puyo.gob.ec
EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion
```

## 🚀 Próximos Pasos

1. **Verificar Funcionamiento**: Asegurar que el template base funcione correctamente
2. **Modelos de Actas**: Crear modelos específicos para actas municipales
3. **Procesamiento de Audio**: Implementar Whisper y Pyannote
4. **Integración IA**: Conectar con APIs de procesamiento de texto
5. **Sistema de Aprobaciones**: Crear flujo de trabajo de aprobación
6. **Repositorio Público**: Implementar búsqueda y publicación

## 🆘 Solución de Problemas

### El contenedor web no inicia
```bash
# Ver logs detallados
docker-compose -f docker-compose.dev.yml logs web

# Reconstruir imagen
docker-compose -f docker-compose.dev.yml build --no-cache web
```

### Error de conexión a PostgreSQL
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose -f docker-compose.dev.yml ps

# Reiniciar PostgreSQL
docker-compose -f docker-compose.dev.yml restart db_postgres
```

### Problemas con migraciones
```bash
# Limpiar y recrear migraciones
docker-compose -f docker-compose.dev.yml exec web python manage.py migrate --fake-initial
```

## 📞 Soporte

Para soporte técnico del Sistema de Actas Municipales de Pastaza:
- **Email**: tecnico@puyo.gob.ec
- **Dominio**: puyo.gob.ec

---

**Municipio de Pastaza - Puyo, Ecuador** 🇪🇨
