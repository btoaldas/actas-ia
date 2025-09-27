@echo off
setlocal EnableDelayedExpansion

:: ========================================
::   INSTALADOR ACTAS IA - MUNICIPIO PASTAZA
::   Sistema de Gestión de Actas Municipales
:: ========================================

title Instalador Actas IA - Municipio de Pastaza

:main
cls
echo.
echo ========================================
echo    ACTAS IA - MUNICIPIO DE PASTAZA
echo    Sistema de Gestion de Actas
echo ========================================
echo.
echo Seleccione una opcion:
echo.
echo [1] Instalacion completa (Primera vez)
echo [2] Iniciar sistema existente
echo [3] Reparar sistema
echo [4] Verificar estado
echo [5] Crear backup
echo [6] Restaurar backup
echo [7] Detener sistema
echo [8] Limpiar y reinstalar
echo [0] Salir
echo.
set /p "opcion=Ingrese su opcion (0-8): "

if "%opcion%"=="1" goto instalacion_completa
if "%opcion%"=="2" goto iniciar_sistema
if "%opcion%"=="3" goto reparar_sistema
if "%opcion%"=="4" goto verificar_estado
if "%opcion%"=="5" goto crear_backup
if "%opcion%"=="6" goto restaurar_backup
if "%opcion%"=="7" goto detener_sistema
if "%opcion%"=="8" goto limpiar_reinstalar
if "%opcion%"=="0" goto salir
goto main

:: ========================================
::   INSTALACION COMPLETA
:: ========================================
:instalacion_completa
cls
echo.
echo 🚀 INSTALACION COMPLETA - ACTAS IA
echo ========================================

echo.
echo 📋 Verificando requisitos...

:: Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker no esta instalado
    echo 📥 Instale Docker Desktop desde: https://www.docker.com/products/docker-desktop
    pause
    goto main
)
echo ✅ Docker esta instalado

:: Verificar Docker Compose  
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker Compose no esta instalado
    pause
    goto main
)
echo ✅ Docker Compose esta disponible

:: Verificar puertos
echo 🔍 Verificando puertos...
netstat -an | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Advertencia: Puerto 8000 en uso
    set /p "continuar=¿Continuar anyway? (s/n): "
    if /i not "!continuar!"=="s" goto main
)

netstat -an | findstr ":5432" >nul 2>&1
if not errorlevel 1 (
    echo ⚠️  Advertencia: Puerto 5432 en uso (PostgreSQL)
    set /p "continuar=¿Continuar anyway? (s/n): "
    if /i not "!continuar!"=="s" goto main
)

echo 🧹 Limpiando instalacion previa...
docker-compose down -v >nul 2>&1
docker system prune -f >nul 2>&1

echo 🏗️  Construyendo imagenes Docker...
docker-compose build --no-cache
if errorlevel 1 (
    echo ❌ Error en construccion de imagenes
    pause
    goto main
)

echo 📊 Iniciando servicios base...
docker-compose up -d db_postgres redis
if errorlevel 1 (
    echo ❌ Error iniciando servicios base
    pause
    goto main
)

echo ⏳ Esperando PostgreSQL...
timeout /t 10 >nul

echo 🗄️  Aplicando migraciones...
docker-compose run --rm web python manage.py migrate
if errorlevel 1 (
    echo ❌ Error en migraciones
    echo 🔧 Intentando reparacion automatica...
    call :reparar_migraciones
)

echo 👤 Creando usuarios iniciales...
docker-compose run --rm web python manage.py crear_usuarios_iniciales

echo 🚀 Iniciando todos los servicios...
docker-compose up -d

echo ⏳ Esperando servicios...
timeout /t 30 >nul

echo.
echo ✅ INSTALACION COMPLETADA
echo ========================================
echo 🌐 URL Sistema:     http://localhost:8000
echo 🔧 Panel Admin:     http://localhost:8000/admin/
echo 🌺 Monitor Celery:  http://localhost:5555
echo.
echo 👤 ACCESO PRINCIPAL:
echo    Usuario: superadmin
echo    Clave:   AdminPuyo2025!
echo ========================================
echo.

call :mostrar_servicios
pause
goto main

:: ========================================
::   INICIAR SISTEMA EXISTENTE
:: ========================================
:iniciar_sistema
cls
echo.
echo 🚀 INICIANDO SISTEMA ACTAS IA
echo ========================================

echo 🔍 Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no disponible
    pause
    goto main
)

echo 🗄️  Verificando servicios base...
docker-compose up -d db_postgres redis
timeout /t 5 >nul

echo 🌐 Iniciando aplicacion web...
docker-compose up -d web

echo ⚙️  Iniciando servicios Celery...
docker-compose up -d celery_worker celery_beat flower

echo 🔄 Iniciando Nginx...
docker-compose up -d nginx

echo ⏳ Esperando servicios...
timeout /t 20 >nul

call :verificar_servicios
if errorlevel 1 (
    echo ⚠️  Algunos servicios no iniciaron correctamente
    echo 🔧 ¿Ejecutar reparacion? (s/n)
    set /p "reparar="
    if /i "!reparar!"=="s" goto reparar_sistema
)

echo.
echo ✅ SISTEMA INICIADO CORRECTAMENTE
echo ========================================
call :mostrar_urls
pause
goto main

:: ========================================
::   REPARAR SISTEMA
:: ========================================
:reparar_sistema
cls
echo.
echo 🔧 REPARACION DEL SISTEMA
echo ========================================

echo 🛑 Deteniendo servicios...
docker-compose down

echo 🧹 Limpiando contenedores...
docker container prune -f >nul

echo 🗄️  Verificando base de datos...
docker-compose up -d db_postgres redis
timeout /t 10 >nul

call :reparar_migraciones

echo 🚀 Reiniciando sistema...
docker-compose up -d

echo ⏳ Esperando servicios...
timeout /t 30 >nul

call :verificar_servicios
echo.
echo ✅ REPARACION COMPLETADA
echo ========================================
pause
goto main

:: ========================================
::   FUNCIONES DE UTILIDAD
:: ========================================
:reparar_migraciones
echo 🔧 Reparando migraciones...

:: Limpiar base de datos
docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO admin_actas; GRANT ALL ON SCHEMA public TO public;" >nul 2>&1

:: Aplicar migraciones
docker-compose run --rm web python manage.py migrate
docker-compose run --rm web python manage.py crear_usuarios_iniciales

echo ✅ Migraciones reparadas
goto :eof

:verificar_servicios
echo 🔍 Verificando servicios...
set servicios_ok=1

docker exec actas_postgres pg_isready -U admin_actas >nul 2>&1
if errorlevel 1 (
    echo ❌ PostgreSQL no responde
    set servicios_ok=0
) else (
    echo ✅ PostgreSQL OK
)

docker exec actas_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo ❌ Redis no responde  
    set servicios_ok=0
) else (
    echo ✅ Redis OK
)

curl -s -o nul -w "%%{http_code}" http://localhost:8000 | findstr "200\|302" >nul 2>&1
if errorlevel 1 (
    echo ❌ Web no responde
    set servicios_ok=0
) else (
    echo ✅ Django Web OK
)

if %servicios_ok%==0 exit /b 1
exit /b 0

:mostrar_servicios
echo 📊 SERVICIOS ACTIVOS:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
goto :eof

:mostrar_urls
echo 🌐 URLs DISPONIBLES:
echo    Sistema:      http://localhost:8000
echo    Admin:        http://localhost:8000/admin/
echo    Portal:       http://localhost:8000/portal-ciudadano/
echo    Celery:       http://localhost:5555
echo    Nginx:        http://localhost:80
goto :eof

:verificar_estado
cls
echo.
echo 📊 ESTADO DEL SISTEMA
echo ========================================
call :verificar_servicios
call :mostrar_servicios
echo.
call :mostrar_urls
pause
goto main

:crear_backup
cls
echo.
echo 💾 CREAR BACKUP
echo ========================================
if not exist "backups" mkdir backups

for /f "tokens=1-6 delims=/: " %%a in ('echo %date% %time%') do (
    set fecha=%%c-%%b-%%a_%%d-%%e-%%f
)
set fecha=!fecha: =!

set backup_file=backups\backup_!fecha!.sql
echo 🗄️  Creando backup: !backup_file!

docker exec actas_postgres pg_dump -U admin_actas -d actas_municipales_pastaza > "!backup_file!"
if errorlevel 1 (
    echo ❌ Error creando backup
) else (
    echo ✅ Backup creado exitosamente
    echo 📁 Ubicacion: !backup_file!
)
pause
goto main

:restaurar_backup
cls
echo.
echo 📥 RESTAURAR BACKUP  
echo ========================================
echo Backups disponibles:
if exist "backups\*.sql" (
    dir /b backups\*.sql
) else (
    echo ❌ No hay backups disponibles
    pause
    goto main
)

echo.
set /p "backup_name=Nombre del backup (sin extension): "
if not exist "backups\!backup_name!.sql" (
    echo ❌ Backup no encontrado
    pause
    goto main
)

echo ⚠️  ADVERTENCIA: Esto eliminara todos los datos actuales
set /p "confirmar=¿Continuar? (escriba SI): "
if not "!confirmar!"=="SI" goto main

echo 🛑 Deteniendo servicios...
docker-compose down
docker-compose up -d db_postgres
timeout /t 5 >nul

echo 🧹 Limpiando base de datos...
docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >nul

echo 📥 Restaurando backup...
docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza < "backups\!backup_name!.sql"

echo 🚀 Iniciando sistema...
docker-compose up -d

echo ✅ Backup restaurado
timeout /t 10 >nul
pause
goto main

:detener_sistema
cls
echo.
echo 🛑 DETENIENDO SISTEMA
echo ========================================
docker-compose down
echo ✅ Sistema detenido
pause
goto main

:limpiar_reinstalar
cls
echo.
echo 🧹 LIMPIAR Y REINSTALAR
echo ========================================
echo ⚠️  ADVERTENCIA: Esto eliminara TODOS los datos
set /p "confirmar=¿Continuar? (escriba CONFIRMO): "
if not "!confirmar!"=="CONFIRMO" goto main

echo 🛑 Deteniendo y limpiando...
docker-compose down -v
docker system prune -af
docker volume prune -f

echo 🚀 Ejecutando instalacion completa...
goto instalacion_completa

:salir
cls
echo.
echo 👋 Gracias por usar Actas IA
echo    Municipio de Pastaza
echo ========================================
exit /b 0