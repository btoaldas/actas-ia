@echo off
:: 🔍 Verificador Rápido de Estado - Sistema Actas Municipales Pastaza

echo.
echo ==============================================================
echo 🔍 VERIFICADOR RAPIDO DE ESTADO - ACTAS MUNICIPALES PASTAZA
echo ==============================================================
echo.

echo 📋 Verificando servicios Docker...
docker-compose -f docker-compose.simple.yml ps

echo.
echo 🌐 Verificando conectividad web...
curl -s -I http://localhost:8000 | findstr "HTTP/1.1 200 OK" > nul
if %errorlevel% equ 0 (
    echo ✅ Servidor web funcionando en http://localhost:8000
) else (
    echo ❌ Servidor web no responde
)

echo.
echo 🔐 Verificando página OAuth...
curl -s -I http://localhost:8000/accounts/login/ | findstr "HTTP/1.1 200 OK" > nul
if %errorlevel% equ 0 (
    echo ✅ Página OAuth accesible en http://localhost:8000/accounts/login/
) else (
    echo ❌ Página OAuth no accesible
)

echo.
echo 🛠️ Verificando admin panel...
curl -s -I http://localhost:8000/admin/ | findstr "HTTP/1.1" > nul
if %errorlevel% equ 0 (
    echo ✅ Panel admin accesible en http://localhost:8000/admin/
) else (
    echo ❌ Panel admin no accesible
)

echo.
echo 🌸 Verificando monitor Celery...
curl -s -I http://localhost:5555 | findstr "HTTP/1.1" > nul
if %errorlevel% equ 0 (
    echo ✅ Monitor Celery (Flower) funcionando en http://localhost:5555
) else (
    echo ❌ Monitor Celery no accesible
)

echo.
echo ==============================================================
echo 📊 RESUMEN DEL SISTEMA
echo ==============================================================
echo.
echo 🌐 URLs principales:
echo    • Dashboard: http://localhost:8000
echo    • Login OAuth: http://localhost:8000/accounts/login/
echo    • Admin Panel: http://localhost:8000/admin/
echo    • Monitor Celery: http://localhost:5555
echo.
echo 🔑 Credenciales:
echo    • Superadmin: superadmin / AdminPuyo2025!
echo    • Admin Municipal: admin_pastaza / AdminPuyo2025!
echo.
echo ⚙️ Servicios Celery:
echo    • Worker: Procesamiento asíncrono activo
echo    • Beat: Tareas programadas activas  
echo    • Flower: Monitor web en puerto 5555
echo.
echo 📖 Documentación:
echo    • Guía OAuth: GUIA_OAUTH.md
echo    • Configuración: .env.example
echo.

pause
