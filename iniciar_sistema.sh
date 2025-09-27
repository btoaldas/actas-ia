#!/bin/bash

# ========================================
#   SCRIPT DE INICIO - ACTAS MUNICIPALES
#   Municipio de Pastaza - Puyo, Ecuador
#   Versión Linux/MacOS Mejorada
# ========================================

set -e  # Salir si cualquier comando falla

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}   Sistema de Actas Municipales de Pastaza${NC}"
echo -e "${CYAN}   Municipio de Pastaza - Puyo, Ecuador${NC}"  
echo -e "${CYAN}================================================================${NC}"
echo

# Función para aplicar schema de logs
aplicar_schema_logs() {
    echo -e "${BLUE}🗄️  Aplicando schema de logs y auditoría...${NC}"

    if [ ! -f "scripts/migrations/2025-09-06_sistema_logs_auditoria.sql" ]; then
        echo -e "${YELLOW}⚠️  Archivo de migración no encontrado${NC}"
        return 1
    fi

    if cat scripts/migrations/2025-09-06_sistema_logs_auditoria.sql | docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza &> /dev/null; then
        echo -e "${GREEN}✅ Schema de logs aplicado correctamente${NC}"
        return 0
    else
        echo -e "${RED}❌ Error aplicando logs - algunas vistas pueden fallar${NC}"
        return 1
    fi
}

# Verificar que Docker esté ejecutándose
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está instalado${NC}"
    echo "   Por favor, instala Docker e intenta nuevamente."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Error: Docker no está ejecutándose o no es accesible${NC}"
    echo "   Por favor, inicia Docker e intenta nuevamente."
    exit 1
fi

echo -e "${GREEN}✅ Docker está ejecutándose correctamente${NC}"

# Limpiar contenedores anteriores
echo -e "${BLUE}🧹 Limpiando contenedores anteriores...${NC}"
docker-compose down &> /dev/null || true
echo -e "${GREEN}✅ Contenedores anteriores limpiados${NC}"

# Construir imágenes
echo -e "${BLUE}🔨 Construyendo imágenes Docker...${NC}"
if ! docker-compose build; then
    echo -e "${RED}❌ Error al construir las imágenes${NC}"
    echo "Presiona Enter para salir..."
    read
    exit 1
fi
echo -e "${GREEN}✅ Imágenes construidas exitosamente${NC}"

# Iniciar servicios base primero
echo -e "${BLUE}📊 Iniciando servicios base (PostgreSQL y Redis)...${NC}"
if ! docker-compose up -d db_postgres redis; then
    echo -e "${RED}❌ Error al iniciar servicios base${NC}"
    echo "Presiona Enter para salir..."
    read
    exit 1
fi
echo -e "${GREEN}✅ Servicios base iniciados${NC}"

# Esperar a que PostgreSQL esté listo
echo -e "${BLUE}⏳ Esperando a PostgreSQL (15 segundos)...${NC}"
sleep 15

# Verificar que PostgreSQL esté respondiendo
if ! docker exec actas_postgres pg_isready -U admin_actas &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL aún no está listo, esperando 10 segundos más...${NC}"
    sleep 10
fi

# Aplicar migraciones de Django
echo -e "${BLUE}🗄️  Aplicando migraciones de Django...${NC}"
if docker-compose run --rm web python manage.py migrate; then
    echo -e "${GREEN}✅ Migraciones aplicadas exitosamente${NC}"
else
    echo -e "${YELLOW}⚠️  Error en migraciones, continuando...${NC}"
fi

# Procesar usuarios iniciales
echo -e "${BLUE}👤 Procesando usuarios iniciales...${NC}"
if docker-compose run --rm web python manage.py crear_usuarios_iniciales; then
    echo -e "${GREEN}✅ Usuarios procesados${NC}"
else
    echo -e "${YELLOW}⚠️  Error en usuarios, continuando...${NC}"
fi

# Levantar todos los servicios
echo -e "${BLUE}🌐 Levantando todos los servicios (Web, Celery Worker, Beat, Flower)...${NC}"
if ! docker-compose up -d; then
    echo -e "${RED}❌ Error al levantar los servicios${NC}"
    echo "Presiona Enter para salir..."
    read
    exit 1
fi
echo -e "${GREEN}✅ Todos los servicios levantados exitosamente${NC}"

# 🆕 Verificación crítica del schema de logs
echo -e "${BLUE}🔍 Verificando schema de logs (crítico para vistas)...${NC}"
sleep 5

if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dn" 2>/dev/null | grep -q logs; then
    echo -e "${GREEN}✅ Schema de logs verificado correctamente${NC}"
else
    echo -e "${YELLOW}⚠️  Schema 'logs' no encontrado - Aplicando automáticamente...${NC}"
    if [ -f "scripts/migrations/2025-09-06_sistema_logs_auditoria.sql" ]; then
        if aplicar_schema_logs; then
            echo -e "${GREEN}✅ Schema de logs aplicado correctamente${NC}"
        else
            echo -e "${RED}❌ Error aplicando logs - algunas vistas pueden fallar${NC}"
        fi
    else
        echo -e "${RED}❌ Archivo de migración no encontrado - contactar soporte${NC}"
    fi
fi

echo
echo -e "${GREEN}🎉 ¡Sistema completo levantado exitosamente!${NC}"
echo
echo -e "${CYAN}🌐 URLS DE ACCESO:${NC}"
echo "   - Aplicación principal: http://localhost:8000"
echo "   - Panel de administración: http://localhost:8000/admin/"
echo "   - Login con OAuth: http://localhost:8000/accounts/login/"
echo "   - Monitor Celery (Flower): http://localhost:5555"
echo
echo -e "${CYAN}🔑 USUARIOS DE PRUEBA:${NC}"
echo "   - Super Admin: superadmin / AdminPuyo2025!"
echo "   - Alcalde: alcalde.pastaza / AlcaldePuyo2025!"
echo "   - Secretario: secretario.concejo / SecretarioPuyo2025!"
echo
echo -e "${CYAN}📊 BASE DE DATOS POSTGRESQL:${NC}"
echo "   - Host: localhost:5432"
echo "   - Base de datos: actas_municipales_pastaza"  
echo "   - Usuario: admin_actas"
echo "   - Contraseña: actas_pastaza_2025"
echo
echo -e "${CYAN}📝 DIRECTORIOS IMPORTANTES:${NC}"
echo "   - Media files: ./media/"
echo "   - Static files: ./static/"
echo "   - Logs: ./logs/"
echo "   - Backups: ./backups/"
echo
echo -e "${CYAN}🔧 COMANDOS ÚTILES:${NC}"
echo "   - Detener sistema: ./detener_sistema.sh"
echo "   - Reiniciar sistema: ./reiniciar_sistema.sh"
echo "   - Ver logs: docker-compose logs -f"
echo "   - Estado servicios: docker-compose ps"
echo
echo -e "${GREEN}Sistema listo para usar. ¡Buen trabajo!${NC}"
echo
echo "Presiona Enter para salir..."
read
