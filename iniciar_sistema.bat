@echo off
REM Script de inicio para Windows - Sistema de Actas Municipales de Pastaza

echo ================================================================
echo    Sistema de Actas Municipales de Pastaza
echo    Municipio de Pastaza - Puyo, Ecuador  
echo ================================================================
echo.

REM Verificar que Docker Desktop esté ejecutándose
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker no está ejecutándose o no está accesible.
    echo    Por favor, inicia Docker Desktop e intenta nuevamente.
    pause
    exit /b 1
)
echo ✅ Docker está ejecutándose correctamente

REM Limpiar contenedores anteriores
echo 🧹 Limpiando contenedores anteriores...
docker-compose down >nul 2>&1
echo ✅ Contenedores anteriores limpiados

REM Construir imágenes
echo 🔨 Construyendo imágenes Docker...
docker-compose build
if errorlevel 1 (
    echo ❌ Error al construir las imágenes
    pause
    exit /b 1
)
echo ✅ Imágenes construidas exitosamente

REM Levantar PostgreSQL y Redis primero
echo 🗄️ Levantando PostgreSQL y Redis...
docker-compose up -d db_postgres redis
if errorlevel 1 (
    echo ❌ Error al levantar PostgreSQL y Redis
    pause
    exit /b 1
)
echo ✅ PostgreSQL y Redis levantados exitosamente
echo ⏳ Esperando que PostgreSQL esté listo...
timeout /t 10 /nobreak >nul

REM Aplicar migraciones
echo 📊 Aplicando migraciones de base de datos...
docker-compose run --rm web python manage.py migrate
if errorlevel 1 (
    echo ❌ Error al aplicar migraciones
    pause
    exit /b 1
)
echo ✅ Migraciones aplicadas exitosamente

REM Crear usuarios iniciales
echo 👥 Creando usuarios iniciales...
docker-compose run --rm web python manage.py crear_usuarios_iniciales
echo ✅ Usuarios procesados

REM Levantar todos los servicios
echo 🌐 Levantando todos los servicios (Web, Celery Worker, Beat, Flower)...
docker-compose up -d
if errorlevel 1 (
    echo ❌ Error al levantar los servicios
    pause
    exit /b 1
)
echo ✅ Todos los servicios levantados exitosamente

REM 🆕 Verificación crítica del schema de logs
echo 🔍 Verificando schema de logs (crítico para vistas)...
timeout /t 5 >nul
docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\dn" | findstr logs >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Schema 'logs' no encontrado - Aplicando automáticamente...
    if exist "scripts\migrations\2025-09-06_sistema_logs_auditoria.sql" (
        powershell -Command "Get-Content scripts/migrations/2025-09-06_sistema_logs_auditoria.sql | docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza" >nul 2>&1
        if errorlevel 1 (
            echo ❌ Error aplicando logs - algunas vistas pueden fallar
        ) else (
            echo ✅ Schema de logs aplicado correctamente
        )
    ) else (
        echo ❌ Archivo de migración no encontrado - contactar soporte
    )
) else (
    echo ✅ Schema de logs verificado correctamente
)

echo.
echo 🎉 ¡Sistema completo levantado exitosamente!
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
echo    - Usuario: admin_actas
echo    - Contraseña: actas_pastaza_2025
echo.
echo � SERVICIOS CELERY:
echo    - Worker: Procesamiento de tareas en segundo plano
echo    - Beat: Tareas programadas (limpieza, backups)
echo    - Flower: Monitor web en http://localhost:5555
echo.
echo �🛠️ COMANDOS ÚTILES:
echo    - Ver logs: docker-compose logs
echo    - Parar sistema: parar_sistema.bat
echo    - Ver estado: docker-compose ps
echo.
echo 📧 Soporte: tecnico@puyo.gob.ec
echo 🏛️ Municipio de Pastaza - Sistema de Actas Municipales
echo.

REM Mostrar estado de servicios
echo 📋 Estado de servicios:
docker-compose ps

echo.
echo Abriendo el sistema en el navegador...
start http://localhost:8000

pause
