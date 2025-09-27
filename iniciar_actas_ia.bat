@echo off
:: ========================================
::   ACTAS IA - INICIO RAPIDO
::   Municipio de Pastaza
:: ========================================

title Actas IA - Inicio Rapido

echo.
echo ========================================
echo    ACTAS IA - MUNICIPIO DE PASTAZA
echo    Inicio Rapido del Sistema
echo ========================================
echo.

:: Verificar Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no esta disponible
    echo 📥 Instale Docker Desktop y ejecute INSTALADOR_ACTAS_IA.bat
    pause
    exit /b 1
)

echo 🔍 Verificando Docker...
echo ✅ Docker disponible

echo.
echo 🚀 Iniciando servicios de Actas IA...
echo.

:: Iniciar servicios base
echo 📊 Iniciando PostgreSQL y Redis...
docker-compose up -d db_postgres redis

:: Esperar que los servicios base estén listos
echo ⏳ Esperando servicios base (10 segundos)...
timeout /t 10 >nul

:: Iniciar aplicación web
echo 🌐 Iniciando Django Web...
docker-compose up -d web

:: Iniciar Celery
echo ⚙️  Iniciando Celery Worker y Beat...
docker-compose up -d celery_worker celery_beat

:: Iniciar Flower
echo 🌺 Iniciando Flower Monitor...
docker-compose up -d flower

:: Iniciar Nginx
echo 🔄 Iniciando Nginx...
docker-compose up -d nginx

:: Verificar estado
echo.
echo ⏳ Esperando que todos los servicios estén listos (20 segundos)...
timeout /t 20 >nul

echo.
echo 📊 Estado de los servicios:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

:: Verificar conectividad
echo.
echo 🔍 Verificando conectividad...

curl -s -o nul -w "HTTP %%{http_code}" http://localhost:8000
if errorlevel 1 (
    echo ❌ Aplicación web no responde
    echo 🔧 Ejecute INSTALADOR_ACTAS_IA.bat opción [3] Reparar sistema
) else (
    echo ✅ Aplicación web funcionando
)

echo.
echo ========================================
echo ✅ SISTEMA ACTAS IA INICIADO
echo ========================================
echo.
echo 🌐 URLs DISPONIBLES:
echo    👤 Sistema Principal: http://localhost:8000
echo    🔧 Panel Admin:       http://localhost:8000/admin/
echo    🏛️  Portal Ciudadano:  http://localhost:8000/portal-ciudadano/
echo    🌺 Monitor Celery:    http://localhost:5555
echo    🔄 Nginx (Prod):      http://localhost:80
echo.
echo 🔑 ACCESO PRINCIPAL:
echo    Usuario: superadmin
echo    Clave:   AdminPuyo2025!
echo.
echo 📋 OTROS USUARIOS:
echo    Alcalde:     alcalde.pastaza / AlcaldePuyo2025!
echo    Secretario:  secretario.concejo / SecretarioPuyo2025!
echo.
echo ========================================
echo 💡 COMANDOS ÚTILES:
echo    - Para detener: docker-compose down
echo    - Para logs:    docker-compose logs -f web
echo    - Para backup:  INSTALADOR_ACTAS_IA.bat opción [5]
echo    - Para reparar: INSTALADOR_ACTAS_IA.bat opción [3]
echo ========================================
echo.

pause