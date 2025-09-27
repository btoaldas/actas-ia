@echo off
REM Script de inicio mejorado para Windows - Sistema de Actas Municipales de Pastaza
chcp 65001 >nul 2>&1

echo ================================================================
echo    Sistema de Actas Municipales de Pastaza
echo    Municipio de Pastaza - Puyo, Ecuador  
echo ================================================================
echo.

REM Verificar que Docker Desktop esté ejecutándose
echo [INFO] Verificando Docker...
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está ejecutándose o no está accesible.
    echo [INFO] Por favor, inicia Docker Desktop e intenta nuevamente.
    pause
    exit /b 1
)
echo [OK] Docker está ejecutándose correctamente

REM Verificar archivo docker-compose.yml
if not exist "docker-compose.yml" (
    echo [ERROR] No se encuentra docker-compose.yml en el directorio actual
    echo [INFO] Directorio actual: %CD%
    pause
    exit /b 1
)

REM Limpiar contenedores anteriores
echo [INFO] Limpiando contenedores anteriores...
docker-compose down --remove-orphans >nul 2>&1
docker system prune -f >nul 2>&1
echo [OK] Contenedores anteriores limpiados

REM Construir imágenes
echo [INFO] Construyendo imágenes Docker...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Error al construir las imágenes
    echo [INFO] Revisando logs de construcción...
    docker-compose build
    pause
    exit /b 1
)
echo [OK] Imágenes construidas exitosamente

REM Levantar PostgreSQL y Redis primero
echo [INFO] Levantando PostgreSQL y Redis...
docker-compose up -d db_postgres redis
if errorlevel 1 (
    echo [ERROR] Error al levantar PostgreSQL y Redis
    pause
    exit /b 1
)
echo [OK] PostgreSQL y Redis iniciados

REM Esperar a que PostgreSQL esté completamente listo
echo [INFO] Esperando que PostgreSQL esté completamente listo...
:wait_postgres
timeout /t 3 /nobreak >nul
docker-compose exec -T db_postgres pg_isready -U admin_actas -d actas_municipales_pastaza >nul 2>&1
if errorlevel 1 (
    echo [INFO] PostgreSQL aún no está listo, esperando...
    goto wait_postgres
)
echo [OK] PostgreSQL está listo para conexiones

REM Verificar si Redis está listo
echo [INFO] Verificando Redis...
docker-compose exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Redis no responde
    pause
    exit /b 1
)
echo [OK] Redis está funcionando

REM Aplicar migraciones
echo [INFO] Aplicando migraciones de base de datos...
docker-compose run --rm web python manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] Error al aplicar migraciones
    echo [INFO] Intentando diagnóstico de la base de datos...
    docker-compose logs db_postgres
    pause
    exit /b 1
)
echo [OK] Migraciones aplicadas exitosamente

REM Crear usuarios iniciales
echo [INFO] Creando usuarios iniciales...
docker-compose run --rm web python manage.py crear_usuarios_iniciales
if errorlevel 1 (
    echo [WARN] Error al crear usuarios (puede ser que ya existan)
)
echo [OK] Usuarios procesados

REM Recopilar archivos estáticos
echo [INFO] Recopilando archivos estáticos...
docker-compose run --rm web python manage.py collectstatic --noinput >nul 2>&1
echo [OK] Archivos estáticos recopilados

REM Levantar todos los servicios
echo [INFO] Levantando servicios principales (Web, Celery Worker, Beat, Flower)...
docker-compose up -d web celery_worker celery_beat flower
if errorlevel 1 (
    echo [ERROR] Error al levantar los servicios principales
    echo [INFO] Mostrando logs de errores...
    docker-compose logs web
    pause
    exit /b 1
)

REM Esperar que los servicios estén listos
echo [INFO] Esperando que los servicios web estén listos...
timeout /t 15 /nobreak >nul

REM Verificar que la aplicación web responde
echo [INFO] Verificando que la aplicación web responde...
:wait_web
timeout /t 2 /nobreak >nul
curl -f http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo [INFO] Aplicación web aún no responde, esperando...
    timeout /t 5 /nobreak >nul
    goto wait_web_check
)
echo [OK] Aplicación web está respondiendo
goto success

:wait_web_check
REM Verificar si el contenedor está corriendo
docker-compose ps web | findstr "Up" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] El contenedor web no está funcionando
    echo [INFO] Logs del contenedor web:
    docker-compose logs web
    pause
    exit /b 1
)
goto wait_web

:success
echo.
echo [SUCCESS] ¡Sistema completo levantado exitosamente!
echo.
echo 🌐 URLS DE ACCESO:
echo    - Aplicación principal: http://localhost:8000
echo    - Panel de administración: http://localhost:8000/admin/
echo    - Login con OAuth: http://localhost:8000/accounts/login/
echo    - Monitor Celery (Flower): http://localhost:5555
echo.
echo 🔑 USUARIOS DE PRUEBA:
echo    - Super Admin: superadmin / AdminPuyo2025!
echo    - Alcalde: alcalde.pastaza / AlcaldePuyo2025!
echo    - Secretario: secretario.concejo / SecretarioPuyo2025!
echo.
echo 📊 BASE DE DATOS POSTGRESQL:
echo    - Host: localhost:5432
echo    - Base de datos: actas_municipales_pastaza
echo    - Usuario: admin_actas / actas_pastaza_2025
echo.
echo ⚙️ SERVICIOS CELERY:
echo    - Worker: Procesamiento de tareas en segundo plano
echo    - Beat: Tareas programadas (limpieza, backups)
echo    - Flower: Monitor web en http://localhost:5555
echo.
echo 🛠️ COMANDOS ÚTILES:
echo    - Ver logs: docker-compose logs [servicio]
echo    - Parar sistema: parar_sistema.bat
echo    - Estado servicios: docker-compose ps
echo    - Reiniciar servicio: docker-compose restart [servicio]
echo.

REM Mostrar estado actual de servicios
echo [INFO] Estado actual de servicios:
docker-compose ps

echo.
echo [INFO] El sistema está listo para usar
echo [INFO] Abriendo el sistema en el navegador...
start http://localhost:8000

echo.
echo Presiona cualquier tecla para salir...
pause >nul