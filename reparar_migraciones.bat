@echo off
echo ========================================
echo   REPARAR MIGRACIONES - ACTAS IA
echo ========================================

echo 🧹 Limpiando migraciones conflictivas...
docker-compose down > nul 2>&1

echo 📊 Verificando estado PostgreSQL...
docker-compose up -d db_postgres redis
timeout /t 5 > nul

echo 🗄️ Limpiando base de datos...
docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO admin_actas;
GRANT ALL ON SCHEMA public TO public;
"

echo 🔄 Regenerando migraciones desde cero...
docker run --rm -v "%CD%":/app -w /app python:3.11-slim bash -c "
pip install django==4.2.9 psycopg2-binary > /dev/null 2>&1
cd /app
find apps/*/migrations/ -name '*.py' ! -name '__init__.py' -delete 2>/dev/null || true
python manage.py makemigrations config_system
python manage.py makemigrations audio_processing
python manage.py makemigrations transcripcion  
python manage.py makemigrations generador_actas
python manage.py makemigrations auditoria
python manage.py makemigrations pages
python manage.py makemigrations users
python manage.py makemigrations tasks
python manage.py makemigrations
"

echo ✅ Migraciones regeneradas. Iniciando sistema...
docker-compose up -d

echo ⏳ Esperando servicios...
timeout /t 30 > nul

echo 🎯 Sistema listo!
docker ps

pause