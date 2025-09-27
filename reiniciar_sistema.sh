#!/bin/bash

# ========================================
#   SCRIPT DE REINICIAR - ACTAS MUNICIPALES
#   Municipio de Pastaza - Puyo, Ecuador
#   Versión Linux/MacOS
# ========================================

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}   Sistema de Actas Municipales de Pastaza${NC}"
echo -e "${CYAN}   Reiniciar Sistema - Municipio de Pastaza${NC}"  
echo -e "${CYAN}================================================================${NC}"
echo

# Verificar que Docker esté disponible
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está instalado${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está ejecutándose${NC}"
    exit 1
fi

echo -e "${BLUE}🔄 Reiniciando Sistema de Actas Municipales...${NC}"
echo

# Función para aplicar schema de logs
aplicar_schema_logs() {
    if [ -f "scripts/migrations/2025-09-06_sistema_logs_auditoria.sql" ]; then
        if cat scripts/migrations/2025-09-06_sistema_logs_auditoria.sql | docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza &> /dev/null; then
            echo -e "${GREEN}✅ Schema de logs aplicado correctamente${NC}"
            return 0
        fi
    fi
    return 1
}

# Paso 1: Detener servicios
echo -e "${BLUE}🛑 Deteniendo servicios actuales...${NC}"
docker-compose down
echo -e "${GREEN}✅ Servicios detenidos${NC}"

# Paso 2: Limpiar contenedores huérfanos
echo -e "${BLUE}🧹 Limpiando contenedores huérfanos...${NC}"
docker container prune -f &> /dev/null || true
echo -e "${GREEN}✅ Contenedores limpiados${NC}"

# Paso 3: Reconstruir imágenes si es necesario
echo -e "${BLUE}🔨 Verificando y construyendo imágenes...${NC}"
if docker-compose build; then
    echo -e "${GREEN}✅ Imágenes construidas/verificadas${NC}"
else
    echo -e "${RED}❌ Error construyendo imágenes${NC}"
    exit 1
fi

# Paso 4: Iniciar servicios base
echo -e "${BLUE}📊 Iniciando servicios base (PostgreSQL y Redis)...${NC}"
if docker-compose up -d db_postgres redis; then
    echo -e "${GREEN}✅ Servicios base iniciados${NC}"
else
    echo -e "${RED}❌ Error iniciando servicios base${NC}"
    exit 1
fi

# Paso 5: Esperar PostgreSQL
echo -e "${BLUE}⏳ Esperando PostgreSQL (15 segundos)...${NC}"
sleep 15

if ! docker exec actas_postgres pg_isready -U admin_actas &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL aún no está listo, esperando 10 segundos más...${NC}"
    sleep 10
fi

# Paso 6: Verificar y aplicar migraciones si es necesario
echo -e "${BLUE}🗄️  Verificando migraciones...${NC}"
if docker-compose run --rm web python manage.py showmigrations --plan | grep -q "\\[ \\]"; then
    echo -e "${BLUE}📊 Aplicando migraciones pendientes...${NC}"
    if docker-compose run --rm web python manage.py migrate; then
        echo -e "${GREEN}✅ Migraciones aplicadas${NC}"
    else
        echo -e "${YELLOW}⚠️  Error en migraciones, continuando...${NC}"
    fi
else
    echo -e "${GREEN}✅ No hay migraciones pendientes${NC}"
fi

# Paso 7: Verificar usuarios
echo -e "${BLUE}👤 Verificando usuarios iniciales...${NC}"
docker-compose run --rm web python manage.py crear_usuarios_iniciales &> /dev/null || true
echo -e "${GREEN}✅ Usuarios verificados${NC}"

# Paso 8: Levantar todos los servicios
echo -e "${BLUE}🚀 Iniciando todos los servicios...${NC}"
if docker-compose up -d; then
    echo -e "${GREEN}✅ Todos los servicios iniciados${NC}"
else
    echo -e "${RED}❌ Error iniciando servicios${NC}"
    exit 1
fi

# Paso 9: Esperar estabilización
echo -e "${BLUE}⏳ Esperando estabilización del sistema (20 segundos)...${NC}"
sleep 20

# Paso 10: Verificación crítica del schema de logs
echo -e "${BLUE}🔍 Verificando schema de logs (crítico para vistas)...${NC}"
if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dn" 2>/dev/null | grep -q logs; then
    echo -e "${GREEN}✅ Schema de logs verificado${NC}"
else
    echo -e "${YELLOW}⚠️  Schema de logs faltante - Aplicando...${NC}"
    if aplicar_schema_logs; then
        echo -e "${GREEN}✅ Schema de logs aplicado${NC}"
    else
        echo -e "${YELLOW}⚠️  No se pudo aplicar schema de logs automáticamente${NC}"
        echo -e "${CYAN}💡 Ejecuta: ./INSTALADOR_ACTAS_IA.sh → Opción 9${NC}"
    fi
fi

# Paso 11: Verificación final
echo -e "${BLUE}🔍 Verificando servicios finales...${NC}"
echo

# Verificar PostgreSQL
if docker exec actas_postgres pg_isready -U admin_actas &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL funcionando${NC}"
else
    echo -e "${RED}❌ PostgreSQL no responde${NC}"
fi

# Verificar Redis
if docker exec actas_redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis funcionando${NC}"
else
    echo -e "${RED}❌ Redis no responde${NC}"
fi

# Verificar Web
if docker exec actas_web python manage.py check --deploy &> /dev/null; then
    echo -e "${GREEN}✅ Django Web funcionando${NC}"
else
    echo -e "${YELLOW}⚠️  Django Web con advertencias menores${NC}"
fi

# Verificar Celery Worker
if docker exec actas_celery_worker celery -A config inspect ping &> /dev/null; then
    echo -e "${GREEN}✅ Celery Worker funcionando${NC}"
else
    echo -e "${YELLOW}⚠️  Celery Worker no responde completamente${NC}"
fi

echo
echo -e "${BLUE}📊 Estado actual de contenedores:${NC}"
docker-compose ps

echo
echo -e "${GREEN}🎉 ¡Sistema reiniciado exitosamente!${NC}"
echo
echo -e "${CYAN}🌐 URLS DE ACCESO:${NC}"
echo "   - Aplicación principal: http://localhost:8000"
echo "   - Panel de administración: http://localhost:8000/admin/"
echo "   - Monitor Celery (Flower): http://localhost:5555"
echo
echo -e "${CYAN}🔑 CREDENCIALES:${NC}"
echo "   - Super Admin: superadmin / AdminPuyo2025!"
echo "   - Alcalde: alcalde.pastaza / AlcaldePuyo2025!"
echo
echo -e "${CYAN}🔧 Si hay problemas, ejecuta:${NC}"
echo "   - Reparación completa: ./INSTALADOR_ACTAS_IA.sh → Opción 3"
echo "   - Solo schema logs: ./INSTALADOR_ACTAS_IA.sh → Opción 9"
echo

echo "Presiona Enter para salir..."
read