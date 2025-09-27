@echo off
chcp 65001 >nul
title Detener Sistema Actas IA
color 0C
echo.
echo ==========================================
echo   DETENIENDO SISTEMA ACTAS IA
echo ==========================================
echo.

REM Verificar Docker
echo [1/4] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está disponible
    pause
    exit /b 1
)
echo [OK] Docker disponible

REM Verificar Docker Compose
echo [2/4] Verificando Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose no disponible
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker-compose
) else (
    set COMPOSE_CMD=docker compose
)
echo [OK] Docker Compose disponible

REM Determinar archivo de configuración
if exist "docker-compose.simple.yml" (
    set COMPOSE_FILE=docker-compose.simple.yml
) else if exist "docker-compose.yml" (
    set COMPOSE_FILE=docker-compose.yml
) else (
    echo [ERROR] No se encuentra archivo Docker Compose
    pause
    exit /b 1
)

REM Detener servicios
echo [3/4] Deteniendo servicios Docker...
%COMPOSE_CMD% -f %COMPOSE_FILE% down --remove-orphans
if errorlevel 1 (
    echo [WARNING] Algunos errores al detener, continuando...
)
echo [OK] Servicios detenidos

REM Limpiar recursos (opcional)
echo [4/4] Limpiando recursos no utilizados...
choice /c SN /m "¿Deseas limpiar volúmenes y redes no utilizadas? (S/N)"
if errorlevel 2 goto :skip_cleanup
if errorlevel 1 goto :cleanup

:cleanup
docker volume prune -f
docker network prune -f
echo [OK] Recursos limpiados

:skip_cleanup
echo.
echo ==========================================
echo   SISTEMA DETENIDO CORRECTAMENTE
echo ==========================================
echo.
echo El sistema ha sido detenido completamente.
echo Para iniciarlo nuevamente ejecuta: iniciar_sistema_corregido.bat
echo.
pause