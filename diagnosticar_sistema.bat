@echo off
REM Script de diagnóstico - Sistema de Actas Municipales de Pastaza
chcp 65001 >nul 2>&1

echo ================================================================
echo    Diagnóstico del Sistema de Actas Municipales de Pastaza
echo ================================================================
echo.

echo [INFO] Verificando entorno...
echo - Sistema Operativo: %OS%
echo - Fecha y hora: %date% %time%
echo - Directorio actual: %CD%
echo.

REM Verificar Docker
echo [INFO] Verificando Docker Desktop...
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está ejecutándose o no está instalado
    echo [SOLUCION] Instala Docker Desktop y asegúrate de que esté ejecutándose
    goto end_check
) else (
    echo [OK] Docker está funcionando
    docker version
    echo.
)

REM Verificar docker-compose
echo [INFO] Verificando docker-compose...
docker-compose version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] docker-compose no está disponible
    goto end_check
) else (
    echo [OK] docker-compose está disponible
    docker-compose version
    echo.
)

REM Verificar archivos necesarios
echo [INFO] Verificando archivos del proyecto...
if exist "docker-compose.yml" (
    echo [OK] docker-compose.yml encontrado
) else (
    echo [ERROR] docker-compose.yml NO encontrado
)

if exist "Dockerfile" (
    echo [OK] Dockerfile encontrado
) else (
    echo [ERROR] Dockerfile NO encontrado
)

if exist "manage.py" (
    echo [OK] manage.py encontrado
) else (
    echo [ERROR] manage.py NO encontrado
)

if exist "requirements.txt" (
    echo [OK] requirements.txt encontrado
) else (
    echo [ERROR] requirements.txt NO encontrado
)
echo.

REM Verificar puertos
echo [INFO] Verificando puertos utilizados...
netstat -an | findstr ":8000" >nul 2>&1
if errorlevel 1 (
    echo [OK] Puerto 8000 está libre
) else (
    echo [WARN] Puerto 8000 está siendo utilizado
)

netstat -an | findstr ":5432" >nul 2>&1
if errorlevel 1 (
    echo [OK] Puerto 5432 está libre
) else (
    echo [WARN] Puerto 5432 está siendo utilizado
)

netstat -an | findstr ":6379" >nul 2>&1
if errorlevel 1 (
    echo [OK] Puerto 6379 está libre
) else (
    echo [WARN] Puerto 6379 está siendo utilizado
)
echo.

REM Estado de contenedores
echo [INFO] Estado de contenedores del proyecto...
docker-compose ps
echo.

REM Verificar logs si hay contenedores corriendo
docker-compose ps | findstr "Up" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Últimos logs del contenedor web:
    docker-compose logs --tail=10 web
    echo.
    echo [INFO] Últimos logs de PostgreSQL:
    docker-compose logs --tail=5 db_postgres
    echo.
)

REM Información del sistema Docker
echo [INFO] Información del sistema Docker...
docker system df
echo.

:end_check
echo ================================================================
echo    Diagnóstico completado
echo ================================================================
echo.
echo Si hay problemas, revisa:
echo 1. Docker Desktop está corriendo
echo 2. Los puertos 8000, 5432, 6379 están libres
echo 3. Todos los archivos del proyecto están presentes
echo 4. No hay errores en los logs mostrados arriba
echo.
pause