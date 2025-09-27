@echo off
chcp 65001 >nul
title Diagnóstico Sistema Docker - Actas IA
color 0E
echo.
echo ==========================================
echo   DIAGNÓSTICO COMPLETO - ACTAS IA
echo ==========================================
echo.

echo [PASO 1] Verificando Docker...
docker --version
if errorlevel 1 (
    echo [ERROR] Docker no está disponible
    echo.
    echo SOLUCIONES:
    echo 1. Instalar Docker Desktop desde: https://www.docker.com/products/docker-desktop
    echo 2. Asegurarse que Docker Desktop esté corriendo
    echo 3. Reiniciar el equipo si es necesario
    echo.
    pause
    exit /b 1
)

echo.
echo [PASO 2] Verificando Docker Compose...
docker compose version 2>nul
if errorlevel 1 (
    docker-compose --version 2>nul
    if errorlevel 1 (
        echo [ERROR] Docker Compose no está disponible
    ) else (
        echo [INFO] Usando docker-compose (legacy)
    )
) else (
    echo [OK] docker compose disponible
)

echo.
echo [PASO 3] Verificando archivos de configuración...
echo Directorio actual: %CD%
echo.
echo Archivos Docker disponibles:
if exist "docker-compose.yml" (
    echo [ENCONTRADO] docker-compose.yml
) else (
    echo [FALTA] docker-compose.yml
)

if exist "docker-compose.simple.yml" (
    echo [ENCONTRADO] docker-compose.simple.yml
) else (
    echo [FALTA] docker-compose.simple.yml
)

if exist "docker-compose.dev.yml" (
    echo [ENCONTRADO] docker-compose.dev.yml
) else (
    echo [FALTA] docker-compose.dev.yml
)

if exist "docker-compose.prod.yml" (
    echo [ENCONTRADO] docker-compose.prod.yml
) else (
    echo [FALTA] docker-compose.prod.yml
)

echo.
echo [PASO 4] Verificando archivos de configuración...
if exist ".env" (
    echo [ENCONTRADO] .env
) else (
    echo [FALTA] .env
    if exist ".env.example" (
        echo [ENCONTRADO] .env.example (se puede usar como plantilla)
    )
)

if exist "Dockerfile" (
    echo [ENCONTRADO] Dockerfile
) else (
    echo [FALTA] Dockerfile
)

echo.
echo [PASO 5] Verificando puertos en uso...
echo.
echo Puerto 8000 (Django):
netstat -an | find ":8000" | find "LISTENING"
if errorlevel 1 (
    echo [LIBRE] Puerto 8000 disponible
) else (
    echo [OCUPADO] Puerto 8000 en uso
)

echo.
echo Puerto 5432 (PostgreSQL):
netstat -an | find ":5432" | find "LISTENING"
if errorlevel 1 (
    echo [LIBRE] Puerto 5432 disponible
) else (
    echo [OCUPADO] Puerto 5432 en uso
)

echo.
echo Puerto 6379 (Redis):
netstat -an | find ":6379" | find "LISTENING"
if errorlevel 1 (
    echo [LIBRE] Puerto 6379 disponible
) else (
    echo [OCUPADO] Puerto 6379 en uso
)

echo.
echo [PASO 6] Verificando contenedores existentes...
echo.
echo Contenedores del proyecto (todos los estados):
docker ps -a --filter "name=actas"
if errorlevel 1 (
    echo [INFO] No hay contenedores previos del proyecto
)

echo.
echo [PASO 7] Verificando imágenes Docker...
echo.
echo Imágenes relacionadas con el proyecto:
docker images | findstr actas
if errorlevel 1 (
    echo [INFO] No hay imágenes previas del proyecto
)

echo.
echo [PASO 8] Verificando espacio en disco...
for /f "tokens=3" %%i in ('dir /-c %SystemDrive%\ ^| find "bytes free"') do set DISK_FREE=%%i
echo Espacio libre en disco: %DISK_FREE% bytes

echo.
echo [PASO 9] Verificando memoria disponible...
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list | find "="

echo.
echo ==========================================
echo   RESUMEN DEL DIAGNÓSTICO
echo ==========================================

echo.
echo PRÓXIMOS PASOS RECOMENDADOS:
echo.

if not exist "docker-compose.simple.yml" (
    if exist "docker-compose.yml" (
        echo 1. Usar docker-compose.yml como archivo principal
        echo    Comando: docker compose -f docker-compose.yml up --build -d
    ) else (
        echo 1. [CRÍTICO] Falta archivo docker-compose - Verificar instalación del proyecto
    )
) else (
    echo 1. Usar docker-compose.simple.yml (archivo encontrado)
    echo    Comando: docker compose -f docker-compose.simple.yml up --build -d
)

if not exist ".env" (
    echo 2. Crear archivo .env desde .env.example
    if exist ".env.example" (
        echo    Comando: copy .env.example .env
    )
)

echo 3. Limpiar contenedores antiguos si existen:
echo    docker system prune -f

echo 4. Iniciar servicios:
echo    docker compose up --build -d

echo.
echo ==========================================
echo   COMANDOS DE EMERGENCIA
echo ==========================================
echo.
echo Si nada funciona, ejecutar en orden:
echo 1. docker system prune -a --volumes
echo 2. Reiniciar Docker Desktop
echo 3. Ejecutar: docker compose up --build --force-recreate -d
echo.

echo [INFO] Diagnóstico completado
pause