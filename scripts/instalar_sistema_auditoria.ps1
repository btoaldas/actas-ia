# ============================================================================
# Script de instalación del sistema de auditoría - PowerShell
# Archivo: scripts\instalar_sistema_auditoria.ps1
# ============================================================================

param(
    [switch]$IncluirTablasUsuarios,
    [switch]$SoloMostrar,
    [string]$ExcluirTablas = "",
    [switch]$ActivarFrontend,
    [switch]$ActivarCelery
)

Write-Host "🔧 Instalador del Sistema de Auditoría - Actas Municipales" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan

# Función para verificar si Django está disponible
function Test-DjangoAvailable {
    try {
        & python manage.py check --quiet
        return $true
    }
    catch {
        return $false
    }
}

# Función para verificar si PostgreSQL está funcionando
function Test-PostgreSQLConnection {
    try {
        & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT 1')
print('Connection OK')
"
        return $true
    }
    catch {
        return $false
    }
}

# Verificar requisitos previos
Write-Host "📋 Verificando requisitos previos..." -ForegroundColor Yellow

if (-not (Test-DjangoAvailable)) {
    Write-Host "❌ Django no está disponible o hay errores en la configuración" -ForegroundColor Red
    exit 1
}

if (-not (Test-PostgreSQLConnection)) {
    Write-Host "❌ No se puede conectar a PostgreSQL" -ForegroundColor Red
    Write-Host "   Asegúrate de que el servicio Docker esté funcionando:" -ForegroundColor Yellow
    Write-Host "   docker-compose up -d" -ForegroundColor Gray
    exit 1
}

Write-Host "✅ Requisitos verificados correctamente" -ForegroundColor Green

# Paso 1: Ejecutar migraciones del sistema de auditoría
Write-Host ""
Write-Host "📊 Paso 1: Creando tablas del sistema de auditoría..." -ForegroundColor Yellow

try {
    Write-Host "Ejecutando migración SQL..." -ForegroundColor Gray
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

# Leer y ejecutar el script SQL
with open('scripts/migrations/2025-09-06_sistema_logs_auditoria.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()

with connection.cursor() as cursor:
    cursor.execute(sql_script)
    
print('✅ Tablas de auditoría creadas correctamente')
"
    
    Write-Host "✅ Tablas del sistema de auditoría creadas" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error creando tablas de auditoría: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Paso 2: Configurar triggers de auditoría
Write-Host ""
Write-Host "⚡ Paso 2: Configurando triggers de auditoría..." -ForegroundColor Yellow

$comandoSetup = "python manage.py setup_auditoria"

if ($SoloMostrar) {
    $comandoSetup += " --solo-mostrar"
}

if ($IncluirTablasUsuarios) {
    $comandoSetup += " --incluir-tablas-sistema"
}

if ($ExcluirTablas -ne "") {
    $comandoSetup += " --excluir-tablas `"$ExcluirTablas`""
}

try {
    Write-Host "Ejecutando: $comandoSetup" -ForegroundColor Gray
    Invoke-Expression $comandoSetup
    
    if (-not $SoloMostrar) {
        Write-Host "✅ Triggers de auditoría configurados" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Error configurando triggers: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Paso 3: Instalar dependencias adicionales
if (-not $SoloMostrar) {
    Write-Host ""
    Write-Host "📦 Paso 3: Instalando dependencias adicionales..." -ForegroundColor Yellow
    
    try {
        # Instalar user-agents para parsing de User Agent
        & pip install user-agents
        Write-Host "✅ Dependencia 'user-agents' instalada" -ForegroundColor Green
        
        # Verificar que psycopg2 esté instalado para PostgreSQL
        & python -c "import psycopg2; print('psycopg2 OK')" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Instalando psycopg2-binary..." -ForegroundColor Gray
            & pip install psycopg2-binary
        }
        Write-Host "✅ Dependencias de base de datos verificadas" -ForegroundColor Green
        
    }
    catch {
        Write-Host "⚠️  Advertencia: Algunas dependencias no se pudieron instalar" -ForegroundColor Yellow
        Write-Host "   Puedes instalarlas manualmente: pip install user-agents psycopg2-binary" -ForegroundColor Gray
    }
}

# Paso 4: Crear directorio de logs
if (-not $SoloMostrar) {
    Write-Host ""
    Write-Host "📁 Paso 4: Configurando directorios de logs..." -ForegroundColor Yellow
    
    $logsDir = "logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
        Write-Host "✅ Directorio de logs creado: $logsDir" -ForegroundColor Green
    } else {
        Write-Host "✅ Directorio de logs ya existe" -ForegroundColor Green
    }
    
    # Crear archivos de log iniciales
    $logFiles = @(
        "actas_general.log",
        "auditoria.log", 
        "celery_audit.log",
        "frontend_audit.log",
        "errores_sistema.log"
    )
    
    foreach ($logFile in $logFiles) {
        $logPath = Join-Path $logsDir $logFile
        if (-not (Test-Path $logPath)) {
            New-Item -ItemType File -Path $logPath -Force | Out-Null
        }
    }
    
    Write-Host "✅ Archivos de log inicializados" -ForegroundColor Green
}

# Paso 5: Configurar frontend (opcional)
if ($ActivarFrontend -and -not $SoloMostrar) {
    Write-Host ""
    Write-Host "🌐 Paso 5: Configurando logging frontend..." -ForegroundColor Yellow
    
    # Verificar que el archivo JavaScript existe
    $jsFile = "static\js\frontend-audit-logger.js"
    if (Test-Path $jsFile) {
        Write-Host "✅ Script de auditoría frontend encontrado" -ForegroundColor Green
        
        # Verificar que las URLs de API están configuradas
        try {
            & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.urls import reverse
print('API URL:', reverse('frontend_logs_api'))
"
            Write-Host "✅ URLs de API configuradas correctamente" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠️  Advertencia: URLs de API no están configuradas" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠️  Archivo JavaScript de auditoría no encontrado" -ForegroundColor Yellow
    }
}

# Paso 6: Configurar Celery (opcional)
if ($ActivarCelery -and -not $SoloMostrar) {
    Write-Host ""
    Write-Host "⚙️  Paso 6: Verificando configuración de Celery..." -ForegroundColor Yellow
    
    try {
        & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from helpers.celery_logging import CeleryAuditLogger
print('✅ Sistema de logging Celery configurado')
"
        Write-Host "✅ Logging de Celery configurado correctamente" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Advertencia: Error en configuración de Celery logging" -ForegroundColor Yellow
    }
}

# Paso 7: Verificación final
if (-not $SoloMostrar) {
    Write-Host ""
    Write-Host "🔍 Paso 7: Verificación final del sistema..." -ForegroundColor Yellow
    
    try {
        & python manage.py setup_auditoria --solo-mostrar > $null
        
        # Verificar que las tablas de auditoría existen
        & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    # Verificar esquemas
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM information_schema.schemata 
        WHERE schema_name IN ('logs', 'auditoria')
    \"\"\")
    esquemas = cursor.fetchone()[0]
    
    # Verificar tablas
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema IN ('logs', 'auditoria')
    \"\"\")
    tablas = cursor.fetchone()[0]
    
    # Verificar función de auditoría
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM information_schema.routines 
        WHERE routine_schema = 'auditoria' 
        AND routine_name = 'registrar_cambio_automatico'
    \"\"\")
    funcion = cursor.fetchone()[0]
    
    print(f'Esquemas: {esquemas}/2')
    print(f'Tablas: {tablas}')
    print(f'Función de auditoría: {funcion}/1')
    
    if esquemas == 2 and tablas >= 8 and funcion == 1:
        print('✅ Sistema de auditoría instalado correctamente')
    else:
        print('⚠️ Sistema de auditoría instalado parcialmente')
"
        Write-Host "✅ Verificación completada" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  Advertencia: No se pudo verificar completamente la instalación" -ForegroundColor Yellow
    }
}

# Resumen final
Write-Host ""
Write-Host "🎉 Instalación del Sistema de Auditoría Completada" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

if (-not $SoloMostrar) {
    Write-Host ""
    Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
    Write-Host "1. Reinicia los servicios Django y Celery:" -ForegroundColor White
    Write-Host "   docker-compose restart actas_web actas_celery" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Incluye el script de auditoría en tus templates:" -ForegroundColor White
    Write-Host "   {% include 'includes/frontend_audit_script.html' %}" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Verifica los logs en tiempo real:" -ForegroundColor White
    Write-Host "   Get-Content logs\auditoria.log -Wait" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. Accede a las estadísticas de auditoría:" -ForegroundColor White
    Write-Host "   http://localhost:8000/api/frontend-stats/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "5. Para limpiar logs antiguos (después de 90 días):" -ForegroundColor White
    Write-Host '   python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute(''SELECT * FROM logs.limpiar_logs_antiguos(90)''); print(''Logs limpiados'')"' -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "✨ El sistema de auditoría está listo para usar!" -ForegroundColor Green
    Write-Host "   Todas las actividades de usuarios, navegación, errores y cambios" -ForegroundColor White
    Write-Host "   en la base de datos serán registrados automáticamente." -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "Para instalar realmente el sistema, ejecuta:" -ForegroundColor Cyan
    Write-Host ".\scripts\instalar_sistema_auditoria.ps1" -ForegroundColor Gray
}
