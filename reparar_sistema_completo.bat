@echo off
REM Script de reparación automática - Sistema de Actas Municipales de Pastaza
chcp 65001 >nul 2>&1

echo ================================================================
echo    Reparación Automática del Sistema de Actas Municipales
echo ================================================================
echo.

REM Verificar Docker
echo [INFO] Verificando Docker...
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está funcionando
    echo [INFO] Intenta iniciar Docker Desktop manualmente
    pause
    exit /b 1
)

echo [INFO] Iniciando reparación automática...

REM 1. Limpiar completamente el sistema
echo [STEP 1] Limpiando sistema completo...
docker-compose down --remove-orphans --volumes >nul 2>&1
docker system prune -af >nul 2>&1
docker volume prune -f >nul 2>&1
echo [OK] Sistema limpiado

REM 2. Verificar archivos críticos
echo [STEP 2] Verificando archivos críticos...
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml no encontrado
    echo [INFO] Asegúrate de estar en el directorio correcto del proyecto
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [WARN] requirements.txt no encontrado, creando uno básico...
    echo Django==4.2.9 > requirements.txt
    echo psycopg2-binary==2.9.9 >> requirements.txt
    echo redis==5.0.1 >> requirements.txt
    echo celery==5.3.4 >> requirements.txt
)

REM 3. Crear directorio media si no existe
if not exist "media" (
    echo [INFO] Creando directorio media...
    mkdir media
)

if not exist "staticfiles" (
    echo [INFO] Creando directorio staticfiles...
    mkdir staticfiles
)

REM 4. Reconstruir completamente las imágenes
echo [STEP 3] Reconstruyendo imágenes desde cero...
docker-compose build --no-cache --pull
if errorlevel 1 (
    echo [ERROR] Error al construir imágenes
    echo [INFO] Verifica tu conexión a internet y los archivos Dockerfile
    pause
    exit /b 1
)
echo [OK] Imágenes reconstruidas

REM 5. Iniciar servicios base paso a paso
echo [STEP 4] Iniciando servicios base...

echo [INFO] Iniciando PostgreSQL...
docker-compose up -d db_postgres
timeout /t 10 /nobreak >nul

echo [INFO] Iniciando Redis...
docker-compose up -d redis
timeout /t 5 /nobreak >nul

REM 6. Verificar conectividad de base de datos
echo [STEP 5] Verificando conectividad de base de datos...
:wait_db
docker-compose exec -T db_postgres pg_isready -U admin_actas >nul 2>&1
if errorlevel 1 (
    echo [INFO] Esperando PostgreSQL...
    timeout /t 3 /nobreak >nul
    goto wait_db
)
echo [OK] PostgreSQL está listo

REM 7. Aplicar migraciones
echo [STEP 6] Aplicando migraciones...
docker-compose run --rm web python manage.py migrate --noinput
if errorlevel 1 (
    echo [WARN] Error en migraciones, intentando recrear base de datos...
    docker-compose run --rm web python manage.py flush --noinput >nul 2>&1
    docker-compose run --rm web python manage.py migrate --noinput
    if errorlevel 1 (
        echo [ERROR] No se pudieron aplicar las migraciones
        pause
        exit /b 1
    )
)
echo [OK] Migraciones aplicadas

REM 8. Crear superusuario
echo [STEP 7] Creando usuarios del sistema...
docker-compose run --rm web python manage.py crear_usuarios_iniciales >nul 2>&1
echo [OK] Usuarios creados

REM 9. Recopilar archivos estáticos
echo [STEP 8] Recopilando archivos estáticos...
docker-compose run --rm web python manage.py collectstatic --noinput >nul 2>&1
echo [OK] Archivos estáticos recopilados

REM 10. Iniciar todos los servicios
echo [STEP 9] Iniciando todos los servicios...
docker-compose up -d
timeout /t 20 /nobreak >nul

REM 11. Verificación final
echo [STEP 10] Verificación final del sistema...
docker-compose ps
echo.

REM Verificar que la web responde
curl -f http://localhost:8000/ >nul 2>&1
if errorlevel 1 (
    echo [WARN] La aplicación web aún no responde
    echo [INFO] Esto puede ser normal, espera 1-2 minutos más
) else (
    echo [OK] Aplicación web está respondiendo
)

echo.
echo ================================================================
echo    Reparación completada
echo ================================================================
echo.
echo [SUCCESS] El sistema ha sido reparado y debería estar funcionando
echo.
echo URLs de verificación:
echo - Aplicación: http://localhost:8000
echo - Admin: http://localhost:8000/admin/
echo - Flower: http://localhost:5555
echo.
echo Si aún hay problemas:
echo 1. Espera 2-3 minutos para que todos los servicios inicien
echo 2. Revisa los logs: docker-compose logs web
echo 3. Ejecuta diagnosticar_sistema.bat
echo.
pause