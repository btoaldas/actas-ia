# Copilot Instructions for Actas IA - Municipal Records Management System

## System Overview

**Actas IA** is a municipal records management system for Pastaza Municipality, Ecuador. It's a Django-based application with React frontend components that handles audio processing, meeting transcription, and municipal transparency features.

### Core Architecture

```
┌─ Django 4.2.9 Backend ──┐   ┌─ React/JS Frontend ─┐   ┌─ External Services ─┐
│ • OAuth (GitHub/Google) │   │ • AdminLTE 3.x      │   │ • PostgreSQL 15     │
│ • Audio Processing      │ ←→│ • WebRTC Recording  │ ←→│ • Redis (Celery)    │
│ • Celery Tasks          │   │ • Drag & Drop       │   │ • Docker Services   │
└─────────────────────────┘   └─────────────────────┘   └──────────────────────┘
```

## Key Development Patterns

### 1. Docker-First Development
**Always use Docker containers for development and migrations**. The system is designed to run exclusively in Docker:

```bash
# Start system (Windows)
iniciar_sistema.bat

# Start system (Linux/Mac)  
./iniciar_sistema.sh

# Execute migrations inside Docker
docker exec -it actas_web python manage.py migrate

# Create users inside Docker
docker exec -it actas_web python manage.py crear_usuarios_iniciales
```

### 2. Django App Structure
Apps follow a consistent pattern with specialized middleware stacking:

```python
# config/settings.py - Critical middleware order
MIDDLEWARE = [
    "apps.auditoria.session_middleware.AdvancedSessionMiddleware",
    "apps.audio_processing.middleware.AuditMiddleware", 
    "apps.audio_processing.middleware.AudioProcessingAuditMiddleware",
    "helpers.auditoria_middleware.AuditoriaMiddleware",
    # Standard Django middleware...
]
```

### 3. Audio Processing Pipeline
The core feature uses a multi-stage Celery pipeline:

```python
# apps/audio_processing/tasks.py
@shared_task(bind=True, max_retries=2)
def procesar_audio_task(self, procesamiento_id: int):
    # Pipeline: Upload → Metadata → Processing → Transcription → Completion
```

**Critical**: Audio processing must handle graceful degradation when Celery is unavailable.

### 4. Municipal-Specific Model Patterns
Models include municipal context fields:

```python
# Common pattern in models
class ProcesamientoAudio(models.Model):
    # Municipal context
    tipo_reunion = models.ForeignKey(TipoReunion, on_delete=models.PROTECT)
    participantes_detallados = models.JSONField(default=list)
    ubicacion = models.CharField(max_length=200, blank=True)
    confidencial = models.BooleanField(default=False)
    
    # Audio metadata with fallback handling
    metadatos_originales = models.JSONField(default=dict)
    metadatos_procesamiento = models.JSONField(default=dict)
```

## Development Commands

### Essential Docker Commands
```bash
# Initial setup with database migrations
docker-compose -f docker-compose.simple.yml up --build

# Execute custom management commands
docker exec -it actas_web python manage.py setup_new_permissions --drop-existing
docker exec -it actas_web python manage.py init_permissions_system

# Database operations
docker exec -it actas_postgres psql -U admin_actas -d actas_municipales_pastaza

# Check system status
docker-compose -f docker-compose.simple.yml ps
```

### Database Management
The system uses custom SQL scripts for complex operations:
```bash
# Windows
.\scripts\run_scripts.ps1 init
.\scripts\run_scripts.ps1 backup

# Linux/Mac
./scripts/run_scripts.sh init
./scripts/run_scripts.sh backup
```

## API Integration Patterns

### 1. Audio Processing API
Modern async pattern with graceful error handling:

```python
# apps/audio_processing/views.py
@require_http_methods(["POST"])
@csrf_exempt
def api_procesar_audio(request):
    # Validates: File type, size, authentication
    # Extracts: FFmpeg metadata with subprocess
    # Initiates: Celery task or marks as pending
    # Returns: Structured JSON with task_id
```

### 2. Authentication Flow
OAuth integration with fallback to Django admin:

```python
# OAuth providers configured in settings
INSTALLED_APPS = [
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.google',
]

# Access levels: superadmin/AdminPuyo2025!, admin_pastaza, alcalde, secretario
```

## Testing and Debugging

### System Health Checks
```bash
# Quick status verification
verificar_estado.bat  # Windows
./verificar_oauth.py  # OAuth configuration check

# Complete system test
./test_sistema_completo.sh
```

### Common Issue Resolution
1. **Migration conflicts**: Use custom management commands in Docker
2. **Celery unavailable**: Audio processing gracefully degrades to pending state
3. **OAuth setup**: Requires manual Django admin configuration post-deployment
4. **File upload issues**: Check Docker volume mounts for media files

## Municipal Context Requirements

### Data Sovereignty
- PostgreSQL database: `actas_municipales_pastaza`
- All user data stored locally
- No external API dependencies for core functionality
- Audit trail for all administrative actions

### Compliance Patterns
```python
# All admin models include audit trails
class SomeAdmin(admin.ModelAdmin):
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.usuario_creacion = request.user
        super().save_model(request, obj, form, change)
```

### Multi-Language Setup
System supports Spanish interface with AdminLTE theme customization focused on municipal use cases.

## Integration Points

- **Frontend**: React components embedded in Django templates with AdminLTE
- **Real-time**: WebRTC for audio recording, WebSocket for live updates
- **Background**: Celery with Redis for audio processing and scheduled tasks
- **Monitoring**: Flower dashboard at `localhost:5555` for task monitoring
- **External**: OAuth providers (GitHub/Google) for authentication options

## Security Considerations

- CSRF protection enabled for all forms
- File upload validation with FFmpeg metadata extraction
- Session-based authentication with OAuth fallback
- Audit middleware tracks all user actions
- Role-based access control through Django admin
