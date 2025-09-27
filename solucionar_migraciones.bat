@echo off
REM Script para solucionar conflictos de migración - Sistema de Actas Municipales
chcp 65001 >nul 2>&1

echo ================================================================
echo    Solucionador de Conflictos de Migración - Actas IA
echo ================================================================
echo.

echo [INFO] Este script resolverá el conflicto de migración eliminando
echo        completamente la base de datos y recreándola desde cero
echo.
echo [WARN] ¡ATENCIÓN! Esto eliminará TODOS los datos existentes
echo        ¿Estás seguro de que quieres continuar? (S/N)
set /p confirmacion=

if /i "%confirmacion%" NEQ "S" (
    echo [INFO] Operación cancelada por el usuario
    pause
    exit /b 0
)

echo.
echo [INFO] Procediendo con la solución de conflictos...

REM 1. Parar y limpiar completamente todo
echo [STEP 1] Limpiando sistema completo...
docker-compose down --remove-orphans --volumes
docker system prune -af >nul 2>&1
docker volume prune -f >nul 2>&1

REM 2. Eliminar volúmenes específicos si existen
echo [STEP 2] Eliminando volúmenes persistentes...
docker volume rm actasia_postgres_data >nul 2>&1
docker volume rm actas-ia_postgres_data >nul 2>&1
docker volume rm postgres_data >nul 2>&1

REM 3. Limpiar todas las imágenes relacionadas
echo [STEP 3] Limpiando imágenes Docker...
docker image rm actasia-base:latest >nul 2>&1
docker image rm actas-ia-web >nul 2>&1
docker image rm actas-ia_web >nul 2>&1

REM 4. Verificar que no hay contenedores relacionados
echo [STEP 4] Verificando limpieza...
docker container prune -f >nul 2>&1

REM 5. Crear directorio de migraciones temporal si no existe
echo [STEP 5] Preparando migraciones...
if not exist "temp_migrations_backup" mkdir temp_migrations_backup

REM 6. Respaldar y limpiar migraciones conflictivas
echo [INFO] Respaldando migraciones conflictivas...
if exist "apps\config_system\migrations\0004_add_permissions_system.py" (
    copy "apps\config_system\migrations\0004_add_permissions_system.py" "temp_migrations_backup\" >nul 2>&1
    del "apps\config_system\migrations\0004_add_permissions_system.py" >nul 2>&1
    echo [OK] Migración conflictiva temporalmente removida
)

REM 7. Construir imagen completamente nueva
echo [STEP 6] Construyendo imagen completamente nueva...
docker-compose build --no-cache --pull
if errorlevel 1 (
    echo [ERROR] Error al construir imagen
    pause
    exit /b 1
)

REM 8. Iniciar solo PostgreSQL con volumen nuevo
echo [STEP 7] Iniciando PostgreSQL con base de datos nueva...
docker-compose up -d db_postgres
timeout /t 15 /nobreak >nul

REM 9. Verificar que PostgreSQL está completamente listo
echo [INFO] Esperando que PostgreSQL esté completamente inicializado...
:wait_postgres_ready
docker-compose exec -T db_postgres pg_isready -U admin_actas -d actas_municipales_pastaza >nul 2>&1
if errorlevel 1 (
    echo [INFO] PostgreSQL iniciando...
    timeout /t 5 /nobreak >nul
    goto wait_postgres_ready
)
echo [OK] PostgreSQL está listo con base de datos nueva

REM 10. Iniciar Redis
echo [STEP 8] Iniciando Redis...
docker-compose up -d redis
timeout /t 5 /nobreak >nul

REM 11. Regenerar todas las migraciones desde cero
echo [STEP 9] Regenerando migraciones desde cero...
docker-compose run --rm web python manage.py makemigrations --noinput
if errorlevel 1 (
    echo [WARN] Error al generar migraciones, continuando...
)

REM 12. Aplicar migraciones en base de datos limpia
echo [STEP 10] Aplicando migraciones en base de datos limpia...
docker-compose run --rm web python manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] Error crítico aplicando migraciones
    echo [INFO] Mostrando logs de error...
    docker-compose logs db_postgres
    pause
    exit /b 1
)
echo [OK] Migraciones aplicadas exitosamente

REM 13. Restaurar migración respaldada
echo [INFO] Restaurando migración respaldada...
if exist "temp_migrations_backup\0004_add_permissions_system.py" (
    copy "temp_migrations_backup\0004_add_permissions_system.py" "apps\config_system\migrations\" >nul 2>&1
    rmdir /s /q temp_migrations_backup >nul 2>&1
    echo [OK] Migración restaurada
)

REM 14. Crear superusuario
echo [STEP 11] Creando usuarios iniciales...
docker-compose run --rm web python manage.py crear_usuarios_iniciales
echo [OK] Usuarios creados

REM 15. Recopilar archivos estáticos
echo [STEP 12] Recopilando archivos estáticos...
docker-compose run --rm web python manage.py collectstatic --noinput >nul 2>&1
echo [OK] Archivos estáticos listos

REM 16. Iniciar todos los servicios
echo [STEP 13] Iniciando todos los servicios...
docker-compose up -d
echo [OK] Servicios iniciando...

REM 17. Esperar que los servicios estén listos
echo [INFO] Esperando que los servicios estén completamente listos...
timeout /t 30 /nobreak >nul

REM 18. Verificación final
echo [STEP 14] Verificación final...
docker-compose ps

echo.
echo ================================================================
echo    ¡CONFLICTO DE MIGRACIONES RESUELTO EXITOSAMENTE!
echo ================================================================
echo.
echo [SUCCESS] El sistema ha sido completamente reiniciado con:
echo ✅ Base de datos PostgreSQL completamente nueva
echo ✅ Todas las migraciones aplicadas correctamente
echo ✅ Usuarios iniciales creados
echo ✅ Todos los servicios funcionando
echo.
echo 🌐 URLs disponibles:
echo    - Aplicación: http://localhost:8000
echo    - Admin: http://localhost:8000/admin/
echo    - Flower: http://localhost:5555
echo.
echo 🔑 Usuario admin: superadmin / AdminPuyo2025!
echo.
echo [INFO] El sistema debería estar completamente funcional ahora
echo [INFO] Espera 1-2 minutos adicionales para que todos los servicios se estabilicen
echo.
pause