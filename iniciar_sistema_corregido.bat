@echo off
chcp 65001 >nul
title Sistema Actas IA - Municipio de Pastaza
color 0A
echo.
echo ==========================================
echo   SISTEMA ACTAS IA - MUNICIPIO PASTAZA
echo ==========================================
echo   Estado: Iniciando sistema Docker...
echo ==========================================
echo.

REM Verificar si Docker está corriendo
echo [1/8] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está disponible o no está corriendo.
    echo.
    echo SOLUCIONES:
    echo - Asegúrate de que Docker Desktop esté ejecutándose
    echo - Reinicia Docker Desktop si está colgado
    echo - Verifica que Docker esté en tu PATH
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('docker --version') do set DOCKER_VERSION=%%i
echo [OK] %DOCKER_VERSION%
echo.

REM Verificar Docker Compose
echo [2/8] Verificando Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Intentando con docker-compose...
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose no está disponible.
        echo Instala Docker Compose o actualiza Docker Desktop.
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker-compose
    echo [OK] Usando docker-compose (versión legacy)
) else (
    set COMPOSE_CMD=docker compose
    for /f "tokens=*" %%i in ('docker compose version') do echo [OK] %%i
)
echo.

REM Verificar archivos de configuración
echo [3/8] Verificando archivos de configuración...
if not exist "docker-compose.simple.yml" (
    echo [ERROR] No se encuentra docker-compose.simple.yml
    echo.
    echo Archivos Docker Compose disponibles:
    if exist "docker-compose.yml" echo - docker-compose.yml (encontrado)
    if exist "docker-compose.prod.yml" echo - docker-compose.prod.yml (encontrado)
    if exist "docker-compose.dev.yml" echo - docker-compose.dev.yml (encontrado)
    echo.
    if exist "docker-compose.yml" (
        echo [INFO] Usando docker-compose.yml como alternativa...
        set COMPOSE_FILE=docker-compose.yml
    ) else (
        echo [ERROR] No se encuentra ningún archivo Docker Compose válido.
        pause
        exit /b 1
    )
) else (
    set COMPOSE_FILE=docker-compose.simple.yml
    echo [OK] docker-compose.simple.yml encontrado
)
echo.

REM Verificar archivo .env
echo [4/8] Verificando configuración de ambiente...
if not exist ".env" (
    echo [WARNING] Archivo .env no encontrado.
    if exist ".env.example" (
        echo [INFO] Copiando .env.example a .env...
        copy .env.example .env >nul
        echo [OK] Archivo .env creado desde ejemplo
    ) else (
        echo [WARNING] Continuando sin configuración de ambiente específica...
    )
) else (
    echo [OK] Archivo .env encontrado
)
echo.

REM Detener contenedores existentes
echo [5/8] Deteniendo contenedores existentes...
%COMPOSE_CMD% -f %COMPOSE_FILE% down --remove-orphans --volumes >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Algunos contenedores ya estaban detenidos
) else (
    echo [OK] Contenedores detenidos correctamente
)
echo.

REM Limpiar imágenes huérfanas opcionales
echo [6/8] Limpiando recursos Docker (opcional)...
docker system prune -f >nul 2>&1
echo [OK] Limpieza de recursos completada
echo.

REM Construir y levantar servicios
echo [7/8] Construyendo e iniciando servicios...
echo [INFO] Este proceso puede tomar varios minutos en la primera ejecución...
echo.
%COMPOSE_CMD% -f %COMPOSE_FILE% up --build -d
if errorlevel 1 (
    echo.
    echo [ERROR] Falló al iniciar los servicios Docker.
    echo.
    echo DIAGNÓSTICO:
    echo Mostrando logs de error...
    %COMPOSE_CMD% -f %COMPOSE_FILE% logs --tail=20
    echo.
    echo SOLUCIONES COMUNES:
    echo - Verifica que los puertos 8000, 5432, 6379, 5555 estén libres
    echo - Asegúrate de tener suficiente espacio en disco
    echo - Reinicia Docker Desktop completamente
    echo - Ejecuta: docker system prune -a --volumes
    echo.
    pause
    exit /b 1
)
echo [OK] Servicios iniciados en modo daemon
echo.

REM Verificar estado de los servicios
echo [8/8] Verificando estado de los servicios...
timeout /t 10 /nobreak >nul
echo.

%COMPOSE_CMD% -f %COMPOSE_FILE% ps

echo.
echo ==========================================
echo   VERIFICACIÓN DE SERVICIOS
echo ==========================================

REM Verificar cada servicio individualmente
echo Comprobando conectividad de servicios...
echo.

REM Verificar PostgreSQL
echo [DB] PostgreSQL:
docker exec actas_postgres pg_isready -U admin_actas -d actas_municipales_pastaza >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PostgreSQL no está listo
) else (
    echo [OK] PostgreSQL funcionando correctamente
)

REM Verificar Redis  
echo [CACHE] Redis:
docker exec actas_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis no está respondiendo
) else (
    echo [OK] Redis funcionando correctamente
)

REM Verificar Django
echo [WEB] Django:
timeout /t 5 /nobreak >nul
for /f %%i in ('powershell -command "(Invoke-WebRequest -Uri http://localhost:8000 -UseBasicParsing).StatusCode" 2^>nul') do set HTTP_STATUS=%%i
if "%HTTP_STATUS%"=="200" (
    echo [OK] Django funcionando correctamente
) else (
    echo [WARNING] Django aún se está inicializando o hay un problema
    echo [INFO] Mostrando logs de Django...
    docker logs actas_web --tail=10
)

echo.
echo ==========================================
echo   SISTEMA INICIADO
echo ==========================================
echo.
echo URLs del sistema:
echo - Aplicación web:     http://localhost:8000
echo - Monitor de tareas:  http://localhost:5555 (Flower)
echo - Base de datos:      localhost:5432
echo - Cache Redis:        localhost:6379
echo.
echo SIGUIENTES PASOS:
echo 1. Abrir navegador en: http://localhost:8000
echo 2. Ejecutar migraciones si es primera vez:
echo    docker exec -it actas_web python manage.py migrate
echo 3. Crear usuario admin si es necesario:
echo    docker exec -it actas_web python manage.py createsuperuser
echo.
echo [INFO] Presiona cualquier tecla para abrir el navegador...
pause >nul
start http://localhost:8000

echo.
echo [INFO] Para detener el sistema ejecuta: detener_sistema.bat
echo [INFO] Para ver logs: docker logs actas_web -f
echo.