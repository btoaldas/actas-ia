@echo off
echo ===============================================
echo  Sistema SMTP - Municipio de Pastaza
echo  Prueba completa del sistema de emails
echo ===============================================
echo.

cd /d "%~dp0"

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    echo Instala Python o verifica que este en el PATH
    pause
    exit /b 1
)

echo Verificando Django...
python -c "import django; print('Django version:', django.get_version())" 2>nul
if errorlevel 1 (
    echo ERROR: Django no encontrado
    echo Instala las dependencias: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo Iniciando pruebas del sistema SMTP...
echo.

python probar_smtp.py

echo.
echo ===============================================
echo  Pruebas completadas
echo ===============================================
pause
