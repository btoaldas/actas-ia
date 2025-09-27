@echo off
REM Script de parada para Windows - Sistema de Actas Municipales de Pastaza
chcp 65001 >nul 2>&1

echo ================================================================
echo    Deteniendo Sistema de Actas Municipales de Pastaza
echo ================================================================
echo.

REM Verificar que Docker esté corriendo
docker version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está ejecutándose
    echo [INFO] El sistema ya podría estar detenido
    pause
    exit /b 0
)

echo [INFO] Deteniendo todos los servicios...
docker-compose down --remove-orphans

echo [INFO] Eliminando volúmenes no utilizados...
docker volume prune -f >nul 2>&1

echo [INFO] Limpiando imágenes no utilizadas...
docker image prune -f >nul 2>&1

echo [INFO] Estado final de contenedores:
docker ps -a --filter "name=actas"

echo.
echo [SUCCESS] Sistema detenido completamente
echo.
echo Para reiniciar el sistema, ejecuta: iniciar_sistema.bat
echo.
pause