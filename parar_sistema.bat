@echo off
REM Script para parar el Sistema de Actas Municipales de Pastaza

echo ================================================================
echo    Parando Sistema de Actas Municipales de Pastaza
echo ================================================================
echo.

echo 🛑 Parando todos los servicios...
docker-compose -f docker-compose.simple.yml down

echo.
echo ✅ Todos los servicios han sido detenidos.
echo.
echo 💡 Para eliminar también los volúmenes de datos, ejecuta:
echo    docker-compose -f docker-compose.simple.yml down -v
echo.
echo 🚀 Para reiniciar el sistema, ejecuta: iniciar_sistema.bat
echo.
pause
