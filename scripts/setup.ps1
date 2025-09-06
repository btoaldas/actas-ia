# ============================================================================
# Script de Inicialización Completa - Sistema de Actas Municipales
# Fecha: 2025-09-06
# Descripción: Script para configurar completamente la base de datos
# ============================================================================

param(
    [switch]$IncludeTestData
)

Write-Host "🚀 Inicializando Sistema de Actas Municipales" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# Paso 1: Verificar Docker
Write-Host "1️⃣ Verificando contenedores Docker..." -ForegroundColor Yellow
try {
    $containers = docker ps --format "table {{.Names}}" | Select-String "actas_postgres"
    if (-not $containers) {
        Write-Host "❌ El contenedor PostgreSQL no está corriendo" -ForegroundColor Red
        Write-Host "Ejecutando: docker-compose up -d" -ForegroundColor Yellow
        docker-compose up -d
        Start-Sleep -Seconds 10
    } else {
        Write-Host "✅ Contenedor PostgreSQL corriendo" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ Error verificando Docker" -ForegroundColor Red
    exit 1
}

# Paso 2: Ejecutar migraciones Django
Write-Host ""
Write-Host "2️⃣ Ejecutando migraciones Django..." -ForegroundColor Yellow
try {
    docker exec actas_web python manage.py migrate
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Migraciones Django completadas" -ForegroundColor Green
    } else {
        Write-Host "❌ Error en migraciones Django" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error ejecutando migraciones Django" -ForegroundColor Red
}

# Paso 3: Crear superusuario
Write-Host ""
Write-Host "3️⃣ Creando usuarios iniciales..." -ForegroundColor Yellow
try {
    docker exec actas_web python manage.py crear_usuarios_iniciales
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Usuarios iniciales creados" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️ Error creando usuarios (posiblemente ya existen)" -ForegroundColor Yellow
}

# Paso 4: Ejecutar script de migración inicial
Write-Host ""
Write-Host "4️⃣ Ejecutando configuración inicial de BD..." -ForegroundColor Yellow
.\scripts\run_scripts.ps1 init

# Paso 5: Cargar datos iniciales
Write-Host ""
Write-Host "5️⃣ Cargando datos iniciales..." -ForegroundColor Yellow
.\scripts\run_scripts.ps1 data

# Paso 6: Cargar datos de prueba (opcional)
if ($IncludeTestData) {
    Write-Host ""
    Write-Host "6️⃣ Cargando datos de prueba..." -ForegroundColor Yellow
    .\scripts\run_scripts.ps1 test-data
}

# Paso 7: Verificar estado final
Write-Host ""
Write-Host "7️⃣ Verificando estado final..." -ForegroundColor Yellow
.\scripts\run_scripts.ps1 status

Write-Host ""
Write-Host "🎉 ¡Inicialización completada!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Servicios disponibles:" -ForegroundColor Blue
Write-Host "   • Aplicación web: http://localhost:8000" -ForegroundColor White
Write-Host "   • Nginx: http://localhost:80" -ForegroundColor White
Write-Host "   • Flower (Celery): http://localhost:5555" -ForegroundColor White
Write-Host "   • PostgreSQL: localhost:5432" -ForegroundColor White
Write-Host ""
Write-Host "👤 Usuarios por defecto:" -ForegroundColor Blue
Write-Host "   • admin / admin123" -ForegroundColor White
Write-Host "   • alcalde / alcalde123" -ForegroundColor White
Write-Host "   • secretario / secretario123" -ForegroundColor White
Write-Host ""
Write-Host "📁 Scripts disponibles:" -ForegroundColor Blue
Write-Host "   • .\scripts\run_scripts.ps1 help" -ForegroundColor White
Write-Host "   • .\scripts\run_scripts.ps1 backup" -ForegroundColor White
Write-Host "   • .\scripts\run_scripts.ps1 connect" -ForegroundColor White
Write-Host ""
