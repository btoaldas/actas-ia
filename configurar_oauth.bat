@echo off
:: 🔐 Configurador OAuth - Sistema de Actas Municipales Pastaza
:: Este script ayuda a configurar OAuth paso a paso

echo.
echo ==============================================================
echo 🔐 CONFIGURADOR OAUTH - SISTEMA ACTAS MUNICIPALES PASTAZA
echo ==============================================================
echo.

:: Verificar si existe .env
if not exist ".env" (
    echo ⚠️  Archivo .env no encontrado
    echo.
    echo 📋 Copiando .env.example a .env...
    copy ".env.example" ".env" >nul
    if %errorlevel% equ 0 (
        echo ✅ Archivo .env creado exitosamente
    ) else (
        echo ❌ Error creando archivo .env
        pause
        exit /b 1
    )
) else (
    echo ✅ Archivo .env encontrado
)

echo.
echo ==============================================================
echo 🔧 CONFIGURACIÓN OAUTH
echo ==============================================================
echo.

echo Para configurar OAuth necesitas:
echo.
echo 📖 GitHub OAuth:
echo    1. Ve a: https://github.com/settings/developers
echo    2. Crea nueva OAuth App
echo    3. Callback URL: http://localhost:8000/accounts/github/login/callback/
echo.
echo 📖 Google OAuth:
echo    1. Ve a: https://console.cloud.google.com
echo    2. Crea proyecto y habilita Google+ API
echo    3. Callback URL: http://localhost:8000/accounts/google/login/callback/
echo.

set /p continuar="¿Quieres continuar con la configuración? (s/n): "
if /i not "%continuar%"=="s" (
    echo Configuración cancelada
    pause
    exit /b 0
)

echo.
echo ==============================================================
echo 🔑 CONFIGURAR GITHUB OAUTH
echo ==============================================================
echo.

set /p github_id="Ingresa tu GitHub Client ID: "
set /p github_secret="Ingresa tu GitHub Client Secret: "

echo.
echo ==============================================================
echo 🔑 CONFIGURAR GOOGLE OAUTH
echo ==============================================================
echo.

set /p google_id="Ingresa tu Google Client ID: "
set /p google_secret="Ingresa tu Google Client Secret: "

echo.
echo 📝 Actualizando archivo .env...

:: Crear script temporal de PowerShell para reemplazar variables
echo $content = Get-Content '.env' > temp_update.ps1
echo $content = $content -replace 'GITHUB_CLIENT_ID=.*', 'GITHUB_CLIENT_ID=%github_id%' >> temp_update.ps1
echo $content = $content -replace 'GITHUB_CLIENT_SECRET=.*', 'GITHUB_CLIENT_SECRET=%github_secret%' >> temp_update.ps1
echo $content = $content -replace 'GOOGLE_CLIENT_ID=.*', 'GOOGLE_CLIENT_ID=%google_id%' >> temp_update.ps1
echo $content = $content -replace 'GOOGLE_CLIENT_SECRET=.*', 'GOOGLE_CLIENT_SECRET=%google_secret%' >> temp_update.ps1
echo $content ^| Set-Content '.env' >> temp_update.ps1

:: Ejecutar script PowerShell
powershell -ExecutionPolicy Bypass -File temp_update.ps1
del temp_update.ps1

if %errorlevel% equ 0 (
    echo ✅ Archivo .env actualizado exitosamente
) else (
    echo ❌ Error actualizando archivo .env
    pause
    exit /b 1
)

echo.
echo ==============================================================
echo 🚀 INICIAR SISTEMA
echo ==============================================================
echo.

set /p iniciar="¿Quieres iniciar el sistema ahora? (s/n): "
if /i not "%iniciar%"=="s" (
    echo.
    echo 📖 Para iniciar el sistema manualmente:
    echo    iniciar_sistema.bat
    echo.
    echo 📖 Para verificar OAuth:
    echo    python verificar_oauth.py
    echo.
    pause
    exit /b 0
)

echo.
echo 🔄 Iniciando sistema...
call iniciar_sistema.bat

echo.
echo ==============================================================
echo ✨ CONFIGURACIÓN COMPLETADA
echo ==============================================================
echo.

echo 🎉 OAuth configurado exitosamente!
echo.
echo 📋 Próximos pasos:
echo    1. Ve a: http://localhost:8000/admin/
echo    2. Login: superadmin / AdminPuyo2025!
echo    3. Configura 'Sites' y 'Social applications'
echo    4. Prueba OAuth en: http://localhost:8000/accounts/login/
echo.
echo 📖 Para más detalles: GUIA_OAUTH.md
echo 🔍 Para verificar: python verificar_oauth.py
echo.

pause
