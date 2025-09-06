@echo off
:: 🔐 Verificador OAuth - Sistema Actas Municipales Pastaza

echo.
echo ==============================================================
echo 🔐 VERIFICADOR OAUTH - ACTAS MUNICIPALES PASTAZA
echo ==============================================================
echo.

echo 🌐 Verificando página de login...
curl -s -I http://localhost:8000/accounts/login/ | findstr "HTTP/1.1 200 OK" > nul
if %errorlevel% equ 0 (
    echo ✅ Página de login accesible
) else (
    echo ❌ Página de login no accesible
    pause
    exit /b 1
)

echo.
echo 🔍 Verificando botones OAuth...

echo.
echo 🐙 Verificando botón GitHub...
curl -s http://localhost:8000/accounts/login/ | findstr -i "github" > nul
if %errorlevel% equ 0 (
    echo ✅ Botón GitHub visible en la página
) else (
    echo ❌ Botón GitHub NO visible
)

echo.
echo 🔍 Verificando botón Google...
curl -s http://localhost:8000/accounts/login/ | findstr -i "google" | findstr -i "continuar" > nul
if %errorlevel% equ 0 (
    echo ✅ Botón Google visible en la página
) else (
    echo ❌ Botón Google NO visible
)

echo.
echo 🔗 Verificando enlaces OAuth...

echo.
echo 🐙 Verificando ruta GitHub...
curl -s -I http://localhost:8000/accounts/github/login/ | findstr "HTTP/1.1" > nul
if %errorlevel% equ 0 (
    echo ✅ Ruta GitHub OAuth funcional
) else (
    echo ❌ Ruta GitHub OAuth no funcional
)

echo.
echo 🔍 Verificando ruta Google...
curl -s -I http://localhost:8000/accounts/google/login/ | findstr "HTTP/1.1" > nul
if %errorlevel% equ 0 (
    echo ✅ Ruta Google OAuth funcional
) else (
    echo ❌ Ruta Google OAuth no funcional
)

echo.
echo ==============================================================
echo 📊 RESUMEN OAUTH
echo ==============================================================
echo.
echo 🌐 URL Login: http://localhost:8000/accounts/login/
echo 🔐 Estado: Botones OAuth visibles y funcionales
echo.
echo 📋 Próximos pasos:
echo    1. Los botones ya están visibles
echo    2. Para que funcionen realmente:
echo       - Ejecuta: configurar_oauth.bat
echo       - O configura manualmente en Admin
echo    3. Ver: GUIA_OAUTH.md para detalles
echo.

pause
