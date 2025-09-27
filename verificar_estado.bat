@echo off
chcp 65001 >nul
title Verificar Estado - Actas IA
color 09
echo.
echo ==========================================
echo   VERIFICACIÓN ESTADO SISTEMA ACTAS IA
echo ==========================================
echo.

REM Verificar Docker
echo [DOCKER] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no disponible
    goto :end_check
) else (
    for /f "tokens=*" %%i in ('docker --version') do echo [OK] %%i
)

REM Verificar Docker Compose
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose no disponible
        set COMPOSE_CMD=
    ) else (
        set COMPOSE_CMD=docker-compose
        for /f "tokens=*" %%i in ('docker-compose --version') do echo [OK] %%i
    )
) else (
    set COMPOSE_CMD=docker compose
    for /f "tokens=*" %%i in ('docker compose version') do echo [OK] %%i
)

echo.
echo ==========================================
echo   ESTADO DE CONTENEDORES
echo ==========================================

REM Mostrar estado de contenedores del proyecto
echo [CONTENEDORES] Estado actual:
docker ps -a --filter "name=actas" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo ==========================================
echo   VERIFICACIÓN DE SERVICIOS
echo ==========================================

REM Verificar contenedores específicos
set SERVICES_OK=0
set SERVICES_TOTAL=4

echo [1/4] PostgreSQL (actas_postgres):
docker ps --filter "name=actas_postgres" --filter "status=running" | find "actas_postgres" >nul
if errorlevel 1 (
    echo [ERROR] PostgreSQL no está corriendo
) else (
    docker exec actas_postgres pg_isready -U admin_actas -d actas_municipales_pastaza >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] PostgreSQL corriendo pero no responde
    ) else (
        echo [OK] PostgreSQL funcionando correctamente
        set /a SERVICES_OK+=1
    )
)

echo [2/4] Redis (actas_redis):
docker ps --filter "name=actas_redis" --filter "status=running" | find "actas_redis" >nul
if errorlevel 1 (
    echo [ERROR] Redis no está corriendo
) else (
    docker exec actas_redis redis-cli ping >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Redis corriendo pero no responde
    ) else (
        echo [OK] Redis funcionando correctamente
        set /a SERVICES_OK+=1
    )
)

echo [3/4] Django Web (actas_web):
docker ps --filter "name=actas_web" --filter "status=running" | find "actas_web" >nul
if errorlevel 1 (
    echo [ERROR] Django Web no está corriendo
) else (
    echo [OK] Contenedor Django corriendo
    echo [INFO] Verificando conectividad HTTP...
    timeout /t 2 /nobreak >nul
    powershell -command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 5; if($r.StatusCode -eq 200) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Django Web corriendo pero HTTP no responde
        echo [INFO] Últimos logs del contenedor:
        docker logs actas_web --tail=5
    ) else (
        echo [OK] Django Web funcionando correctamente (HTTP 200)
        set /a SERVICES_OK+=1
    )
)

echo [4/4] Celery Worker (actas_celery):
docker ps --filter "name=actas_celery" --filter "status=running" | find "actas_celery" >nul
if errorlevel 1 (
    echo [WARNING] Celery Worker no está corriendo (opcional)
) else (
    echo [OK] Celery Worker corriendo
    set /a SERVICES_OK+=1
)

echo.
echo ==========================================
echo   VERIFICACIÓN DE PUERTOS
echo ==========================================
echo [PUERTOS] Verificando puertos del sistema:

netstat -an | find "LISTENING" | find ":8000" >nul
if errorlevel 1 (
    echo [ERROR] Puerto 8000 (Django) no está en uso
) else (
    echo [OK] Puerto 8000 (Django) en uso
)

netstat -an | find "LISTENING" | find ":5432" >nul
if errorlevel 1 (
    echo [ERROR] Puerto 5432 (PostgreSQL) no está en uso
) else (
    echo [OK] Puerto 5432 (PostgreSQL) en uso
)

netstat -an | find "LISTENING" | find ":6379" >nul
if errorlevel 1 (
    echo [ERROR] Puerto 6379 (Redis) no está en uso
) else (
    echo [OK] Puerto 6379 (Redis) en uso
)

netstat -an | find "LISTENING" | find ":5555" >nul
if errorlevel 1 (
    echo [WARNING] Puerto 5555 (Flower) no está en uso
) else (
    echo [OK] Puerto 5555 (Flower) en uso
)

echo.
echo ==========================================
echo   RESUMEN DEL ESTADO
echo ==========================================
echo Servicios funcionando: %SERVICES_OK%/%SERVICES_TOTAL%

if %SERVICES_OK% GEQ 3 (
    echo [ESTADO] Sistema funcionando correctamente
    echo.
    echo URLs disponibles:
    echo - Aplicación: http://localhost:8000
    echo - Flower:     http://localhost:5555
    color 0A
) else if %SERVICES_OK% GEQ 1 (
    echo [ESTADO] Sistema parcialmente funcional
    echo [ACCIÓN] Algunos servicios requieren atención
    color 0E
) else (
    echo [ESTADO] Sistema no funcional
    echo [ACCIÓN] Es necesario iniciar los servicios
    color 0C
)

echo.
echo ==========================================
echo   LOGS RECIENTES (Últimas 5 líneas)
echo ==========================================
docker logs actas_web --tail=5 2>nul

:end_check
echo.
echo [INFO] Verificación completada
echo [INFO] Para iniciar: iniciar_sistema_corregido.bat
echo [INFO] Para detener: detener_sistema.bat
echo.
pause
