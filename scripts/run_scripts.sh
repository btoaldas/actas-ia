#!/bin/bash

# ============================================================================
# Script de Ejecución de Scripts SQL - Sistema de Actas Municipales
# Fecha: 2025-09-06
# Descripción: Script para ejecutar fácilmente los scripts SQL
# ============================================================================

# Configuración de conexión
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="actas_municipales_pastaza"
DB_USER="admin_actas"
DB_CONTAINER="actas_postgres"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}📋 Script de Gestión de Base de Datos - Sistema de Actas Municipales${NC}"
    echo ""
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  init         - Ejecutar migración inicial"
    echo "  data         - Cargar datos iniciales"
    echo "  test-data    - Cargar datos de prueba"
    echo "  migrate      - Ejecutar mejoras de esquema"
    echo "  backup       - Crear backup de la base de datos"
    echo "  cleanup      - Ejecutar limpieza y optimización"
    echo "  status       - Verificar estado de la base de datos"
    echo "  connect      - Conectar directamente a la base de datos"
    echo "  help         - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 init"
    echo "  $0 data"
    echo "  $0 backup"
    echo ""
}

# Función para verificar si Docker está corriendo
check_docker() {
    if ! docker ps | grep -q $DB_CONTAINER; then
        echo -e "${RED}❌ Error: El contenedor $DB_CONTAINER no está corriendo${NC}"
        echo "Ejecuta: docker-compose up -d"
        exit 1
    fi
}

# Función para ejecutar script SQL
execute_sql() {
    local script_file=$1
    local description=$2
    
    echo -e "${YELLOW}🚀 Ejecutando: $description${NC}"
    
    if [ ! -f "$script_file" ]; then
        echo -e "${RED}❌ Error: Archivo $script_file no encontrado${NC}"
        return 1
    fi
    
    if docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < "$script_file"; then
        echo -e "${GREEN}✅ Completado: $description${NC}"
        return 0
    else
        echo -e "${RED}❌ Error ejecutando: $description${NC}"
        return 1
    fi
}

# Función para crear backup
create_backup() {
    local backup_dir="backups"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="backup_actas_${timestamp}.sql"
    
    mkdir -p $backup_dir
    
    echo -e "${YELLOW}💾 Creando backup de la base de datos...${NC}"
    
    if docker exec $DB_CONTAINER pg_dump -U $DB_USER $DB_NAME > "$backup_dir/$backup_file"; then
        echo -e "${GREEN}✅ Backup creado: $backup_dir/$backup_file${NC}"
        
        # Comprimir el backup
        gzip "$backup_dir/$backup_file"
        echo -e "${GREEN}📦 Backup comprimido: $backup_dir/${backup_file}.gz${NC}"
    else
        echo -e "${RED}❌ Error creando backup${NC}"
    fi
}

# Función para mostrar estado
show_status() {
    echo -e "${BLUE}📊 Estado de la Base de Datos${NC}"
    echo ""
    
    # Verificar conexión
    if docker exec $DB_CONTAINER pg_isready -U $DB_USER -d $DB_NAME > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Conexión: OK${NC}"
    else
        echo -e "${RED}❌ Conexión: ERROR${NC}"
        return 1
    fi
    
    # Mostrar estadísticas básicas
    docker exec $DB_CONTAINER psql -U $DB_USER -d $DB_NAME -c "
    SELECT 
        'Usuarios registrados' as estadistica,
        COUNT(*) as cantidad
    FROM auth_user
    UNION ALL
    SELECT 
        'Sesiones municipales' as estadistica,
        COUNT(*) as cantidad
    FROM pages_sesion_municipal
    UNION ALL
    SELECT 
        'Documentos almacenados' as estadistica,
        COUNT(*) as cantidad
    FROM file_manager_documento
    UNION ALL
    SELECT 
        'Tamaño de la BD (MB)' as estadistica,
        ROUND(pg_database_size('$DB_NAME')/1024/1024, 2) as cantidad;
    "
}

# Función para conectar a la base de datos
connect_db() {
    echo -e "${BLUE}🔌 Conectando a la base de datos...${NC}"
    echo "Para salir, escribe: \\q"
    docker exec -it $DB_CONTAINER psql -U $DB_USER -d $DB_NAME
}

# Verificar que Docker esté corriendo
check_docker

# Procesar argumentos
case $1 in
    "init")
        execute_sql "scripts/migrations/2025-09-06_inicial.sql" "Migración inicial"
        ;;
    "data")
        execute_sql "scripts/data/initial_data.sql" "Datos iniciales"
        ;;
    "test-data")
        execute_sql "scripts/data/test_data.sql" "Datos de prueba"
        ;;
    "migrate")
        execute_sql "scripts/migrations/2025-09-06_mejoras_esquema.sql" "Mejoras de esquema"
        ;;
    "backup")
        create_backup
        ;;
    "cleanup")
        execute_sql "scripts/maintenance/cleanup_optimization.sql" "Limpieza y optimización"
        ;;
    "status")
        show_status
        ;;
    "connect")
        connect_db
        ;;
    "help"|"")
        show_help
        ;;
    *)
        echo -e "${RED}❌ Opción no válida: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
