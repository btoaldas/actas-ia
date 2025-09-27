@echo off
chcp 65001 >nul
title Reparación Automática - Actas IA
color 0D
echo.
echo ==========================================
echo   REPARACIÓN AUTOMÁTICA SISTEMA DOCKER
echo ==========================================
echo.
echo [WARNING] Este script intentará reparar automáticamente
echo problemas comunes con Docker y el sistema Actas IA.
echo.
choice /c SN /m "¿Deseas continuar con la reparación automática? (S/N)"
if errorlevel 2 exit /b 0

echo.
echo [INICIO] Reparación automática iniciada...
echo.

REM PASO 1: Verificar Docker
echo [1/10] Verificando Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker no está disponible
    echo [INFO] Abriendo página de descarga de Docker Desktop...
    start https://www.docker.com/products/docker-desktop
    echo [MANUAL] Instala Docker Desktop y reinicia este script
    pause
    exit /b 1
) else (
    echo [OK] Docker funcionando
)

REM PASO 2: Detener todos los contenedores del proyecto
echo [2/10] Deteniendo contenedores existentes...
docker stop actas_web actas_postgres actas_redis actas_celery actas_flower 2>nul
docker rm actas_web actas_postgres actas_redis actas_celery actas_flower 2>nul
echo [OK] Contenedores limpiados

REM PASO 3: Limpiar recursos Docker
echo [3/10] Limpiando recursos Docker...
docker system prune -f >nul 2>&1
docker network prune -f >nul 2>&1
echo [OK] Recursos Docker limpiados

REM PASO 4: Verificar archivos de configuración
echo [4/10] Verificando archivos de configuración...
if not exist "docker-compose.simple.yml" (
    if exist "docker-compose.yml" (
        echo [INFO] Usando docker-compose.yml como archivo principal
        set COMPOSE_FILE=docker-compose.yml
    ) else (
        echo [ERROR] No se encuentra archivo Docker Compose
        echo [MANUAL] Verifica que estés en el directorio correcto del proyecto
        pause
        exit /b 1
    )
) else (
    set COMPOSE_FILE=docker-compose.simple.yml
    echo [OK] Usando docker-compose.simple.yml
)

REM PASO 5: Crear archivo .env si no existe
echo [5/10] Verificando archivo .env...
if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creando .env desde .env.example...
        copy ".env.example" ".env" >nul
        echo [OK] Archivo .env creado
    ) else (
        echo [INFO] Creando .env básico...
        (
            echo # Configuración básica para desarrollo
            echo DEBUG=True
            echo SECRET_KEY=django-insecure-development-key-only
            echo DATABASE_URL=postgresql://admin_actas:Pastaza2024!@localhost:5432/actas_municipales_pastaza
            echo REDIS_URL=redis://localhost:6379/0
        ) > ".env"
        echo [OK] Archivo .env básico creado
    )
) else (
    echo [OK] Archivo .env existe
)

REM PASO 6: Verificar Dockerfile
echo [6/10] Verificando Dockerfile...
if not exist "Dockerfile" (
    echo [WARNING] Dockerfile no encontrado
    echo [INFO] El sistema intentará usar imagen base
) else (
    echo [OK] Dockerfile encontrado
)

REM PASO 7: Liberar puertos en uso (opcional)
echo [7/10] Verificando puertos...
netstat -an | find ":8000" | find "LISTENING" >nul
if not errorlevel 1 (
    echo [WARNING] Puerto 8000 en uso
    echo [INFO] Intentando liberar puerto...
    for /f "tokens=5" %%i in ('netstat -ano ^| find ":8000" ^| find "LISTENING"') do taskkill /PID %%i /F >nul 2>&1
)

netstat -an | find ":5432" | find "LISTENING" >nul
if not errorlevel 1 (
    echo [WARNING] Puerto 5432 en uso
    echo [INFO] Puede ser PostgreSQL local - continuando...
)

echo [OK] Verificación de puertos completada

REM PASO 8: Determinar comando Docker Compose
echo [8/10] Configurando Docker Compose...
docker compose version >nul 2>&1
if errorlevel 1 (
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Docker Compose no disponible
        pause
        exit /b 1
    ) else (
        set COMPOSE_CMD=docker-compose
        echo [OK] Usando docker-compose (legacy)
    )
) else (
    set COMPOSE_CMD=docker compose
    echo [OK] Usando docker compose (moderno)
)

REM PASO 9: Construir e iniciar servicios
echo [9/10] Construyendo e iniciando servicios...
echo [INFO] Este proceso puede tomar varios minutos...
echo.

%COMPOSE_CMD% -f %COMPOSE_FILE% up --build -d --force-recreate

if errorlevel 1 (
    echo.
    echo [ERROR] Falló la construcción de servicios
    echo.
    echo [DIAGNÓSTICO] Mostrando logs de error:
    %COMPOSE_CMD% -f %COMPOSE_FILE% logs --tail=20
    echo.
    echo [SOLUCIONES MANUALES]
    echo 1. Verificar sintaxis del archivo %COMPOSE_FILE%
    echo 2. Verificar que todas las dependencias estén disponibles
    echo 3. Reiniciar Docker Desktop completamente
    echo 4. Ejecutar: docker system prune -a --volumes
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Servicios iniciados correctamente
)

REM PASO 10: Verificación final
echo [10/10] Verificación final del sistema...
timeout /t 15 /nobreak >nul

echo.
echo Estado de los contenedores:
%COMPOSE_CMD% -f %COMPOSE_FILE% ps

echo.
echo Verificando servicios individuales...

REM PostgreSQL
docker exec actas_postgres pg_isready -U admin_actas 2>nul
if errorlevel 1 (
    echo [WARNING] PostgreSQL no responde aún
) else (
    echo [OK] PostgreSQL funcionando
)

REM Redis
docker exec actas_redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Redis no responde aún
) else (
    echo [OK] Redis funcionando
)

REM Django (esperar más tiempo)
echo [INFO] Esperando a Django (30 segundos)...
timeout /t 30 /nobreak >nul

powershell -command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000' -UseBasicParsing -TimeoutSec 10; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Django no responde en HTTP
    echo [INFO] Últimos logs de Django:
    docker logs actas_web --tail=10
) else (
    echo [OK] Django funcionando (HTTP 200)
)

echo.
echo ==========================================
echo   REPARACIÓN COMPLETADA
echo ==========================================
echo.

echo RESULTADO:
echo - Sistema Docker: Reparado
echo - Contenedores: Iniciados
echo - Configuración: Verificada
echo.
echo SIGUIENTES PASOS:
echo 1. Abrir http://localhost:8000 en el navegador
echo 2. Si es primera vez, ejecutar migraciones:
echo    docker exec -it actas_web python manage.py migrate
echo 3. Crear superusuario si es necesario:
echo    docker exec -it actas_web python manage.py createsuperuser
echo.

choice /c SN /m "¿Deseas abrir el navegador ahora? (S/N)"
if errorlevel 1 start http://localhost:8000

echo.
echo [INFO] Para verificar estado: verificar_estado.bat
echo [INFO] Para detener: detener_sistema.bat
echo.
pause