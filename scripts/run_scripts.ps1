# ============================================================================
# Script de Ejecución de Scripts SQL - Sistema de Actas Municipales (PowerShell)
# Fecha: 2025-09-06
# Descripción: Script para ejecutar fácilmente los scripts SQL en Windows
# ============================================================================

param(
    [Parameter(Position=0)]
    [string]$Action = "help"
)

# Configuración de conexión
$DB_HOST = "localhost"
$DB_PORT = "5432"
$DB_NAME = "actas_municipales_pastaza"
$DB_USER = "admin_actas"
$DB_CONTAINER = "actas_postgres"

# Función para mostrar ayuda
function Show-Help {
    Write-Host "📋 Script de Gestión de Base de Datos - Sistema de Actas Municipales" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Uso: .\run_scripts.ps1 [OPCIÓN]" -ForegroundColor White
    Write-Host ""
    Write-Host "Opciones:" -ForegroundColor Yellow
    Write-Host "  init         - Ejecutar migración inicial" -ForegroundColor White
    Write-Host "  data         - Cargar datos iniciales" -ForegroundColor White
    Write-Host "  test-data    - Cargar datos de prueba" -ForegroundColor White
    Write-Host "  migrate      - Ejecutar mejoras de esquema" -ForegroundColor White
    Write-Host "  backup       - Crear backup de la base de datos" -ForegroundColor White
    Write-Host "  cleanup      - Ejecutar limpieza y optimización" -ForegroundColor White
    Write-Host "  status       - Verificar estado de la base de datos" -ForegroundColor White
    Write-Host "  connect      - Conectar directamente a la base de datos" -ForegroundColor White
    Write-Host "  help         - Mostrar esta ayuda" -ForegroundColor White
    Write-Host ""
    Write-Host "Ejemplos:" -ForegroundColor Green
    Write-Host "  .\run_scripts.ps1 init" -ForegroundColor White
    Write-Host "  .\run_scripts.ps1 data" -ForegroundColor White
    Write-Host "  .\run_scripts.ps1 backup" -ForegroundColor White
    Write-Host ""
}

# Función para verificar si Docker está corriendo
function Test-Docker {
    try {
        $containers = docker ps --format "table {{.Names}}" | Select-String $DB_CONTAINER
        if (-not $containers) {
            Write-Host "❌ Error: El contenedor $DB_CONTAINER no está corriendo" -ForegroundColor Red
            Write-Host "Ejecuta: docker-compose up -d" -ForegroundColor Yellow
            exit 1
        }
    }
    catch {
        Write-Host "❌ Error: Docker no está disponible" -ForegroundColor Red
        exit 1
    }
}

# Función para ejecutar script SQL
function Invoke-SqlScript {
    param(
        [string]$ScriptFile,
        [string]$Description
    )
    
    Write-Host "🚀 Ejecutando: $Description" -ForegroundColor Yellow
    
    if (-not (Test-Path $ScriptFile)) {
        Write-Host "❌ Error: Archivo $ScriptFile no encontrado" -ForegroundColor Red
        return $false
    }
    
    try {
        Get-Content $ScriptFile | docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Completado: $Description" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Error ejecutando: $Description" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando: $Description" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        return $false
    }
}

# Función para crear backup
function New-Backup {
    $backupDir = "backups"
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backup_actas_$timestamp.sql"
    
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir | Out-Null
    }
    
    Write-Host "💾 Creando backup de la base de datos..." -ForegroundColor Yellow
    
    try {
        docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME | Out-File -FilePath "$backupDir\$backupFile" -Encoding UTF8
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Backup creado: $backupDir\$backupFile" -ForegroundColor Green
            
            # Comprimir el backup
            Compress-Archive -Path "$backupDir\$backupFile" -DestinationPath "$backupDir\${backupFile}.zip"
            Remove-Item "$backupDir\$backupFile"
            Write-Host "📦 Backup comprimido: $backupDir\${backupFile}.zip" -ForegroundColor Green
        } else {
            Write-Host "❌ Error creando backup" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ Error creando backup: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Función para mostrar estado
function Show-Status {
    Write-Host "📊 Estado de la Base de Datos" -ForegroundColor Blue
    Write-Host ""
    
    # Verificar conexión
    try {
        docker exec $DB_CONTAINER pg_isready -U $DB_USER -d $DB_NAME | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Conexión: OK" -ForegroundColor Green
        } else {
            Write-Host "❌ Conexión: ERROR" -ForegroundColor Red
            return
        }
    }
    catch {
        Write-Host "❌ Conexión: ERROR" -ForegroundColor Red
        return
    }
    
    # Mostrar estadísticas básicas
    $query = @"
SELECT 
    'Usuarios registrados' as estadistica,
    COUNT(*) as cantidad
FROM auth_user
UNION ALL
SELECT 
    'Sesiones municipales' as estadistica,
    COUNT(*) as cantidad
FROM pages_sesion_municipal
UNION ALL
SELECT 
    'Documentos almacenados' as estadistica,
    COUNT(*) as cantidad
FROM file_manager_documento
UNION ALL
SELECT 
    'Tamaño de la BD (MB)' as estadistica,
    ROUND(pg_database_size('$DB_NAME')/1024/1024, 2) as cantidad;
"@
    
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c $query
}

# Función para conectar a la base de datos
function Connect-Database {
    Write-Host "🔌 Conectando a la base de datos..." -ForegroundColor Blue
    Write-Host "Para salir, escribe: \q" -ForegroundColor Yellow
    docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME
}

# Verificar que Docker esté corriendo
Test-Docker

# Procesar argumentos
switch ($Action.ToLower()) {
    "init" {
        Invoke-SqlScript "scripts\migrations\2025-09-06_inicial.sql" "Migración inicial"
    }
    "data" {
        Invoke-SqlScript "scripts\data\initial_data.sql" "Datos iniciales"
    }
    "test-data" {
        Invoke-SqlScript "scripts\data\test_data.sql" "Datos de prueba"
    }
    "migrate" {
        Invoke-SqlScript "scripts\migrations\2025-09-06_mejoras_esquema.sql" "Mejoras de esquema"
    }
    "backup" {
        New-Backup
    }
    "cleanup" {
        Invoke-SqlScript "scripts\maintenance\cleanup_optimization.sql" "Limpieza y optimización"
    }
    "status" {
        Show-Status
    }
    "connect" {
        Connect-Database
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host "❌ Opción no válida: $Action" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
