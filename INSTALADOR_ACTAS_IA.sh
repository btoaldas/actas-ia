#!/bin/bash

# ========================================
#   INSTALADOR ACTAS IA - MUNICIPIO PASTAZA
#   Sistema de Gestión de Actas Municipales
#   Versión Linux/MacOS
# ========================================

set -e  # Salir si cualquier comando falla

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para mostrar títulos
show_title() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}   ACTAS IA - MUNICIPIO DE PASTAZA${NC}"
    echo -e "${CYAN}   Sistema de Gestión de Actas${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

# Función para mostrar el menú principal
show_menu() {
    clear
    show_title
    echo -e "${BLUE}Seleccione una opción:${NC}"
    echo
    echo -e "${GREEN}[1]${NC} Instalación completa (Primera vez)"
    echo -e "${GREEN}[2]${NC} Iniciar sistema existente"
    echo -e "${GREEN}[3]${NC} Reparar sistema"
    echo -e "${GREEN}[4]${NC} Verificar estado"
    echo -e "${GREEN}[5]${NC} Crear backup"
    echo -e "${GREEN}[6]${NC} Restaurar backup"
    echo -e "${GREEN}[7]${NC} Detener sistema"
    echo -e "${GREEN}[8]${NC} Limpiar y reinstalar"
    echo -e "${GREEN}[9]${NC} 🆕 Aplicar solo schema de logs (reparación rápida)"
    echo -e "${RED}[0]${NC} Salir"
    echo
}

# Función para verificar Docker
verificar_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Error: Docker no está instalado${NC}"
        echo "   Por favor, instala Docker e intenta nuevamente."
        return 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Error: Docker no está ejecutándose o no es accesible${NC}"
        echo "   Por favor, inicia Docker e intenta nuevamente."
        return 1
    fi

    echo -e "${GREEN}✅ Docker está ejecutándose correctamente${NC}"
    return 0
}

# Función para aplicar schema de logs
aplicar_schema_logs() {
    echo -e "${BLUE}🗄️  Verificando y aplicando schema de logs...${NC}"

    # Verificar si el archivo de migración existe
    if [ ! -f "scripts/migrations/2025-09-06_sistema_logs_auditoria.sql" ]; then
        echo -e "${YELLOW}⚠️  Archivo de migración de logs no encontrado${NC}"
        echo "    scripts/migrations/2025-09-06_sistema_logs_auditoria.sql"
        return 1
    fi

    # Aplicar schema usando cat y pipe
    if cat scripts/migrations/2025-09-06_sistema_logs_auditoria.sql | docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza &> /dev/null; then
        echo -e "${GREEN}✅ Schema de logs aplicado exitosamente${NC}"
        echo -e "${CYAN}    - Schema 'logs' creado con 8 tablas${NC}"
        echo -e "${CYAN}    - Schema 'auditoria' creado${NC}"
        echo -e "${CYAN}    - 37 índices optimizados${NC}"
        echo -e "${CYAN}    - 4 funciones de logging${NC}"
        echo -e "${CYAN}    - 3 vistas de reportes${NC}"
        return 0
    else
        echo -e "${RED}❌ Error aplicando schema de logs${NC}"
        echo -e "${YELLOW}💡 El sistema funcionará pero algunas vistas pueden fallar${NC}"
        echo "    Ejecuta manualmente: cat scripts/migrations/2025-09-06_sistema_logs_auditoria.sql | docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza"
        return 1
    fi
}

# Función para reparar migraciones
reparar_migraciones() {
    echo -e "${BLUE}🔧 Reparando migraciones...${NC}"

    # Limpiar base de datos
    docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO admin_actas; GRANT ALL ON SCHEMA public TO public;" &> /dev/null || true

    # Aplicar migraciones Django
    if docker-compose run --rm web python manage.py migrate; then
        echo -e "${GREEN}✅ Migraciones Django aplicadas${NC}"
    else
        echo -e "${RED}❌ Error en migraciones Django${NC}"
        return 1
    fi

    # Crear usuarios iniciales
    if docker-compose run --rm web python manage.py crear_usuarios_iniciales; then
        echo -e "${GREEN}✅ Usuarios iniciales creados${NC}"
    else
        echo -e "${RED}❌ Error creando usuarios iniciales${NC}"
        return 1
    fi

    # 🆕 APLICAR SCHEMA DE LOGS CRÍTICO (previene errores de vistas)
    echo -e "${BLUE}🗄️  Aplicando schema de logs y auditoría...${NC}"
    aplicar_schema_logs || echo -e "${YELLOW}⚠️  Error aplicando logs - continuando...${NC}"

    echo -e "${GREEN}✅ Migraciones reparadas${NC}"
}

# Función para verificar servicios
verificar_servicios() {
    echo -e "${BLUE}🔍 Verificando servicios...${NC}"
    local servicios_ok=1

    # Verificar PostgreSQL
    if docker exec actas_postgres pg_isready -U admin_actas &> /dev/null; then
        echo -e "${GREEN}✅ PostgreSQL OK${NC}"
    else
        echo -e "${RED}❌ PostgreSQL no responde${NC}"
        servicios_ok=0
    fi

    # Verificar Redis
    if docker exec actas_redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis OK${NC}"
    else
        echo -e "${RED}❌ Redis no responde${NC}"
        servicios_ok=0
    fi

    # Verificar Web
    if docker exec actas_web python manage.py check &> /dev/null; then
        echo -e "${GREEN}✅ Django Web OK${NC}"
    else
        echo -e "${RED}❌ Django Web no responde${NC}"
        servicios_ok=0
    fi

    # Verificar Celery Worker
    if docker exec actas_celery_worker celery -A config inspect ping &> /dev/null; then
        echo -e "${GREEN}✅ Celery Worker OK${NC}"
    else
        echo -e "${RED}❌ Celery Worker no responde${NC}"
        servicios_ok=0
    fi

    if [ $servicios_ok -eq 1 ]; then
        echo -e "${GREEN}🎉 Todos los servicios están funcionando correctamente${NC}"
    else
        echo -e "${YELLOW}⚠️  Algunos servicios tienen problemas${NC}"
    fi

    return $servicios_ok
}

# 1. INSTALACIÓN COMPLETA
instalacion_completa() {
    clear
    show_title
    echo -e "${GREEN}🚀 INSTALACIÓN COMPLETA - ACTAS IA${NC}"
    echo "========================================"
    echo

    verificar_docker || return 1

    echo -e "${BLUE}🛑 Limpiando instalaciones anteriores...${NC}"
    docker-compose down -v &> /dev/null || true
    docker system prune -f &> /dev/null || true

    echo -e "${BLUE}🔨 Construyendo imágenes Docker...${NC}"
    if ! docker-compose build; then
        echo -e "${RED}❌ Error construyendo imágenes${NC}"
        read -p "Presiona Enter para continuar..."
        return 1
    fi

    echo -e "${BLUE}📊 Iniciando servicios base...${NC}"
    if ! docker-compose up -d db_postgres redis; then
        echo -e "${RED}❌ Error iniciando servicios base${NC}"
        read -p "Presiona Enter para continuar..."
        return 1
    fi

    echo -e "${BLUE}⏳ Esperando PostgreSQL...${NC}"
    sleep 10

    echo -e "${BLUE}🗄️  Aplicando migraciones...${NC}"
    if ! docker-compose run --rm web python manage.py migrate; then
        echo -e "${RED}❌ Error en migraciones${NC}"
        echo -e "${BLUE}🔧 Intentando reparación automática...${NC}"
        reparar_migraciones
    fi

    echo -e "${BLUE}👤 Creando usuarios iniciales...${NC}"
    docker-compose run --rm web python manage.py crear_usuarios_iniciales

    echo -e "${BLUE}🗄️  Aplicando schema de logs y auditoría (CRÍTICO)...${NC}"
    aplicar_schema_logs

    echo -e "${BLUE}🚀 Iniciando todos los servicios...${NC}"
    docker-compose up -d

    echo -e "${BLUE}⏳ Esperando servicios...${NC}"
    sleep 30

    verificar_servicios

    echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA${NC}"
    echo "========================================"
    echo
    echo -e "${CYAN}🌐 URLS DE ACCESO:${NC}"
    echo "   - Aplicación principal: http://localhost:8000"
    echo "   - Panel de administración: http://localhost:8000/admin/"
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

    read -p "Presiona Enter para continuar..."
}

# 2. INICIAR SISTEMA EXISTENTE
iniciar_sistema() {
    clear
    show_title
    echo -e "${GREEN}🚀 INICIAR SISTEMA EXISTENTE${NC}"
    echo "========================================"
    echo

    verificar_docker || return 1

    echo -e "${BLUE}🔨 Construyendo imágenes actualizadas...${NC}"
    docker-compose build

    echo -e "${BLUE}🚀 Iniciando servicios...${NC}"
    docker-compose up -d

    echo -e "${BLUE}⏳ Esperando servicios...${NC}"
    sleep 20

    # 🆕 Verificación crítica del schema de logs
    echo -e "${BLUE}🔍 Verificando schema de logs (crítico para vistas)...${NC}"
    sleep 5

    if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dn" | grep -q logs; then
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

    verificar_servicios

    echo -e "${GREEN}🎉 ¡Sistema iniciado exitosamente!${NC}"
    echo "========================================"
    echo
    echo -e "${CYAN}🌐 URLS DE ACCESO:${NC}"
    echo "   - Aplicación: http://localhost:8000"
    echo "   - Admin: http://localhost:8000/admin/"
    echo "   - Flower: http://localhost:5555"
    echo

    read -p "Presiona Enter para continuar..."
}

# 3. REPARAR SISTEMA
reparar_sistema() {
    clear
    show_title
    echo -e "${YELLOW}🔧 REPARACIÓN DEL SISTEMA${NC}"
    echo "========================================"
    echo

    echo -e "${BLUE}🛑 Deteniendo servicios...${NC}"
    docker-compose down

    echo -e "${BLUE}🧹 Limpiando contenedores...${NC}"
    docker container prune -f &> /dev/null

    echo -e "${BLUE}🗄️  Verificando base de datos...${NC}"
    docker-compose up -d db_postgres redis
    sleep 10

    reparar_migraciones

    echo -e "${BLUE}🚀 Reiniciando sistema...${NC}"
    docker-compose up -d

    echo -e "${BLUE}⏳ Esperando servicios...${NC}"
    sleep 30

    verificar_servicios

    echo -e "${GREEN}✅ REPARACIÓN COMPLETADA${NC}"
    echo "========================================"
    read -p "Presiona Enter para continuar..."
}

# 4. VERIFICAR ESTADO
verificar_estado() {
    clear
    show_title
    echo -e "${BLUE}🔍 VERIFICACIÓN DEL ESTADO${NC}"
    echo "========================================"
    echo

    verificar_docker || return 1

    echo -e "${BLUE}📊 Estado de contenedores:${NC}"
    docker-compose ps

    echo
    verificar_servicios

    # Verificar schema de logs
    echo
    echo -e "${BLUE}🗄️  Verificando schema de logs:${NC}"
    if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dn" | grep -q logs; then
        echo -e "${GREEN}✅ Schema de logs presente${NC}"
    else
        echo -e "${RED}❌ Schema de logs faltante${NC}"
        echo -e "${YELLOW}💡 Ejecuta Opción 9 para aplicar rápidamente${NC}"
    fi

    read -p "Presiona Enter para continuar..."
}

# 5. CREAR BACKUP
crear_backup() {
    clear
    show_title
    echo -e "${BLUE}💾 CREAR BACKUP${NC}"
    echo "========================================"
    echo

    local timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    local backup_dir="backups"
    
    mkdir -p "$backup_dir"

    echo -e "${BLUE}📦 Creando backup completo...${NC}"
    
    # Backup de PostgreSQL
    if docker exec actas_postgres pg_dump -U admin_actas -d actas_municipales_pastaza > "$backup_dir/backup_completo_${timestamp}.sql"; then
        echo -e "${GREEN}✅ Backup de PostgreSQL creado${NC}"
    else
        echo -e "${RED}❌ Error creando backup de PostgreSQL${NC}"
    fi

    # Backup de archivos de configuración
    tar -czf "$backup_dir/config_backup_${timestamp}.tar.gz" docker-compose.yml .env* scripts/ &> /dev/null || true

    echo -e "${GREEN}✅ BACKUP COMPLETADO${NC}"
    echo "   Archivos en: ./$backup_dir/"
    echo "   - backup_completo_${timestamp}.sql"
    echo "   - config_backup_${timestamp}.tar.gz"
    
    read -p "Presiona Enter para continuar..."
}

# 6. RESTAURAR BACKUP
restaurar_backup() {
    clear
    show_title
    echo -e "${YELLOW}🔄 RESTAURAR BACKUP${NC}"
    echo "========================================"
    echo

    if [ ! -d "backups" ] || [ -z "$(ls -A backups/*.sql 2>/dev/null)" ]; then
        echo -e "${RED}❌ No hay backups disponibles${NC}"
        read -p "Presiona Enter para continuar..."
        return 1
    fi

    echo -e "${BLUE}📂 Backups disponibles:${NC}"
    ls -la backups/*.sql

    echo
    read -p "Nombre del archivo de backup (sin ruta): " backup_file

    if [ ! -f "backups/$backup_file" ]; then
        echo -e "${RED}❌ Archivo no encontrado${NC}"
        read -p "Presiona Enter para continuar..."
        return 1
    fi

    echo -e "${RED}⚠️  ADVERTENCIA: Esto eliminará todos los datos actuales${NC}"
    read -p "¿Continuar? (escriba CONFIRMO): " confirmar

    if [ "$confirmar" != "CONFIRMO" ]; then
        echo -e "${YELLOW}Operación cancelada${NC}"
        read -p "Presiona Enter para continuar..."
        return 0
    fi

    echo -e "${BLUE}🗄️  Restaurando backup...${NC}"
    
    docker-compose up -d db_postgres
    sleep 10

    if cat "backups/$backup_file" | docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza; then
        echo -e "${GREEN}✅ Backup restaurado exitosamente${NC}"
        
        echo -e "${BLUE}🚀 Reiniciando servicios...${NC}"
        docker-compose up -d
        sleep 20
        
        verificar_servicios
    else
        echo -e "${RED}❌ Error restaurando backup${NC}"
    fi

    read -p "Presiona Enter para continuar..."
}

# 7. DETENER SISTEMA
detener_sistema() {
    clear
    show_title
    echo -e "${YELLOW}🛑 DETENER SISTEMA${NC}"
    echo "========================================"
    echo

    echo -e "${BLUE}Deteniendo todos los servicios...${NC}"
    docker-compose down

    echo -e "${GREEN}✅ Sistema detenido correctamente${NC}"
    read -p "Presiona Enter para continuar..."
}

# 8. LIMPIAR Y REINSTALAR
limpiar_reinstalar() {
    clear
    show_title
    echo -e "${RED}🧹 LIMPIAR Y REINSTALAR${NC}"
    echo "========================================"
    echo

    echo -e "${RED}⚠️  ADVERTENCIA: Esto eliminará TODOS los datos${NC}"
    read -p "¿Continuar? (escriba CONFIRMO): " confirmar

    if [ "$confirmar" != "CONFIRMO" ]; then
        echo -e "${YELLOW}Operación cancelada${NC}"
        read -p "Presiona Enter para continuar..."
        return 0
    fi

    echo -e "${BLUE}🛑 Deteniendo y limpiando...${NC}"
    docker-compose down -v
    docker system prune -af &> /dev/null || true
    docker volume prune -f &> /dev/null || true

    echo -e "${BLUE}🚀 Ejecutando instalación completa...${NC}"
    instalacion_completa
}

# 9. APLICAR SOLO SCHEMA DE LOGS
aplicar_solo_logs() {
    clear
    show_title
    echo -e "${BLUE}🗄️  APLICAR SCHEMA DE LOGS Y AUDITORÍA${NC}"
    echo "========================================"
    echo
    echo "Esta opción aplica SOLO el schema de logs sin afectar otros datos."
    echo "Útil para reparar errores de vistas sin reinstalar todo."
    echo

    read -p "¿Aplicar schema de logs? (s/N): " confirmar
    if [[ ! "$confirmar" =~ ^[sS]$ ]]; then
        return 0
    fi

    echo -e "${BLUE}🔍 Verificando servicios...${NC}"
    if ! docker exec actas_postgres pg_isready -U admin_actas &> /dev/null; then
        echo -e "${RED}❌ PostgreSQL no está disponible${NC}"
        echo -e "${YELLOW}💡 Asegúrate de que el sistema esté iniciado (Opción 2)${NC}"
        read -p "Presiona Enter para continuar..."
        return 1
    fi

    echo -e "${BLUE}🗄️  Aplicando schema de logs...${NC}"
    aplicar_schema_logs

    echo -e "${GREEN}✅ SCHEMA DE LOGS APLICADO${NC}"
    echo "========================================"
    echo
    echo "Las vistas de auditoría ahora deberían funcionar correctamente."
    echo

    read -p "Presiona Enter para continuar..."
}

# Función principal del menú
main_menu() {
    while true; do
        show_menu
        read -p "Ingrese su opción (0-9): " opcion

        case $opcion in
            1) instalacion_completa ;;
            2) iniciar_sistema ;;
            3) reparar_sistema ;;
            4) verificar_estado ;;
            5) crear_backup ;;
            6) restaurar_backup ;;
            7) detener_sistema ;;
            8) limpiar_reinstalar ;;
            9) aplicar_solo_logs ;;
            0) 
                clear
                echo
                echo -e "${CYAN}👋 Gracias por usar Actas IA${NC}"
                echo -e "${CYAN}   Municipio de Pastaza${NC}"
                echo "========================================"
                exit 0
                ;;
            *)
                echo -e "${RED}Opción inválida. Por favor, selecciona una opción del 0-9.${NC}"
                sleep 2
                ;;
        esac
    done
}

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: No se encontró docker-compose.yml${NC}"
    echo "   Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Iniciar el menú principal
main_menu