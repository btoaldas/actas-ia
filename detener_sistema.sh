#!/bin/bash

# ========================================
#   SCRIPT DE DETENER - ACTAS MUNICIPALES
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
echo -e "${CYAN}   Detener Sistema - Municipio de Pastaza${NC}"  
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

echo -e "${BLUE}🛑 Deteniendo Sistema de Actas Municipales...${NC}"
echo

# Mostrar servicios activos antes de detener
echo -e "${BLUE}📊 Servicios activos actualmente:${NC}"
docker-compose ps

echo
echo -e "${BLUE}🛑 Deteniendo todos los servicios...${NC}"

# Detener todos los servicios
if docker-compose down; then
    echo -e "${GREEN}✅ Todos los servicios detenidos exitosamente${NC}"
else
    echo -e "${YELLOW}⚠️  Algunos servicios pueden haberse detenido con errores${NC}"
fi

echo
echo -e "${BLUE}🧹 Limpiando contenedores huérfanos...${NC}"
docker container prune -f &> /dev/null || true
echo -e "${GREEN}✅ Limpieza completada${NC}"

echo
echo -e "${BLUE}📊 Estado final del sistema:${NC}"
docker-compose ps

echo
echo -e "${GREEN}🎉 Sistema detenido correctamente${NC}"
echo
echo -e "${CYAN}🔧 Para reiniciar el sistema, ejecuta:${NC}"
echo "   ./iniciar_sistema.sh"
echo
echo -e "${CYAN}🔄 Para reiniciar rápidamente, ejecuta:${NC}"
echo "   ./reiniciar_sistema.sh"
echo
echo -e "${CYAN}🛠️  Para reparación completa, ejecuta:${NC}"
echo "   ./INSTALADOR_ACTAS_IA.sh"
echo

echo "Presiona Enter para salir..."
read