#!/bin/bash

# ========================================
#   SCRIPT DE VERIFICAR ESTADO - ACTAS MUNICIPALES
#   Municipio de Pastaza - Puyo, Ecuador
#   Versión Linux/MacOS
# ========================================

# Colores para mejor visualización
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

clear

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}   Sistema de Actas Municipales de Pastaza${NC}"
echo -e "${CYAN}   Verificar Estado - Municipio de Pastaza${NC}"  
echo -e "${CYAN}================================================================${NC}"
echo

# Función para verificar conectividad HTTP
verificar_http() {
    local url=$1
    local nombre=$2
    
    if curl -s --connect-timeout 5 --max-time 10 "$url" &> /dev/null; then
        echo -e "${GREEN}✅ $nombre accesible${NC}"
        return 0
    else
        echo -e "${RED}❌ $nombre no accesible${NC}"
        return 1
    fi
}

# 1. VERIFICAR DOCKER
echo -e "${BLUE}🐳 VERIFICACIÓN DE DOCKER${NC}"
echo "================================"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker no está ejecutándose${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker está funcionando correctamente${NC}"
docker version --format "   Versión: {{.Server.Version}}"
echo

# 2. VERIFICAR CONTENEDORES
echo -e "${BLUE}📦 ESTADO DE CONTENEDORES${NC}"
echo "================================"
docker-compose ps
echo

# Verificar individualmente cada contenedor crítico
containers=("actas_postgres:PostgreSQL" "actas_redis:Redis" "actas_web:Django Web" "actas_celery_worker:Celery Worker" "actas_nginx:Nginx Proxy")

echo -e "${BLUE}🔍 Verificación detallada de servicios:${NC}"
for container_info in "${containers[@]}"; do
    IFS=':' read -r container_name service_name <<< "$container_info"
    
    if docker ps --format "table {{.Names}}" | grep -q "$container_name"; then
        # Verificar si está saludable
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
        status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "unknown")
        
        if [ "$status" = "running" ]; then
            if [ "$health" = "healthy" ] || [ "$health" = "unknown" ]; then
                echo -e "${GREEN}✅ $service_name funcionando${NC}"
            else
                echo -e "${YELLOW}⚠️  $service_name funcionando pero con problemas de salud${NC}"
            fi
        else
            echo -e "${RED}❌ $service_name no está ejecutándose${NC}"
        fi
    else
        echo -e "${RED}❌ $service_name no encontrado${NC}"
    fi
done
echo

# 3. VERIFICAR SERVICIOS ESPECÍFICOS
echo -e "${BLUE}🔧 VERIFICACIÓN DE SERVICIOS ESPECÍFICOS${NC}"
echo "================================"

# PostgreSQL
if docker exec actas_postgres pg_isready -U admin_actas &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL respondiendo${NC}"
    db_version=$(docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -t -c "SELECT version();" 2>/dev/null | head -n1 | xargs)
    echo "   Versión: ${db_version:0:50}..."
else
    echo -e "${RED}❌ PostgreSQL no responde${NC}"
fi

# Redis
if docker exec actas_redis redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis respondiendo${NC}"
    redis_info=$(docker exec actas_redis redis-cli info server | grep "redis_version" | cut -d: -f2 | tr -d '\r')
    echo "   Versión: Redis $redis_info"
else
    echo -e "${RED}❌ Redis no responde${NC}"
fi

# Django Web
if docker exec actas_web python manage.py check &> /dev/null; then
    echo -e "${GREEN}✅ Django Web funcionando${NC}"
    django_version=$(docker exec actas_web python -c "import django; print(f'Django {django.VERSION[0]}.{django.VERSION[1]}.{django.VERSION[2]}')" 2>/dev/null)
    echo "   Versión: $django_version"
else
    echo -e "${RED}❌ Django Web con problemas${NC}"
fi

# Celery Worker  
if docker exec actas_celery_worker celery -A config inspect ping &> /dev/null; then
    echo -e "${GREEN}✅ Celery Worker funcionando${NC}"
    active_tasks=$(docker exec actas_celery_worker celery -A config inspect active 2>/dev/null | grep -c "uuid" || echo "0")
    echo "   Tareas activas: $active_tasks"
else
    echo -e "${YELLOW}⚠️  Celery Worker no responde completamente${NC}"
fi
echo

# 4. VERIFICAR SCHEMA DE LOGS (CRÍTICO)
echo -e "${BLUE}🗄️  VERIFICACIÓN DE SCHEMA DE LOGS${NC}"
echo "================================"

if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dn" 2>/dev/null | grep -q logs; then
    echo -e "${GREEN}✅ Schema 'logs' presente${NC}"
    
    # Verificar tablas específicas
    tables=("sistema_logs" "celery_logs" "navegacion_usuarios" "api_logs")
    for table in "${tables[@]}"; do
        if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dt logs.$table" 2>/dev/null | grep -q "$table"; then
            count=$(docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -t -c "SELECT COUNT(*) FROM logs.$table;" 2>/dev/null | xargs)
            echo -e "${GREEN}   ✅ logs.$table (${count} registros)${NC}"
        else
            echo -e "${RED}   ❌ logs.$table faltante${NC}"
        fi
    done
    
    # Verificar schema auditoria
    if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dn" 2>/dev/null | grep -q auditoria; then
        echo -e "${GREEN}✅ Schema 'auditoria' presente${NC}"
    else
        echo -e "${YELLOW}⚠️  Schema 'auditoria' faltante${NC}"
    fi
else
    echo -e "${RED}❌ Schema 'logs' faltante - CRÍTICO${NC}"
    echo -e "${CYAN}💡 Para reparar: ./INSTALADOR_ACTAS_IA.sh → Opción 9${NC}"
fi
echo

# 5. VERIFICAR CONECTIVIDAD HTTP
echo -e "${BLUE}🌐 VERIFICACIÓN DE CONECTIVIDAD WEB${NC}"
echo "================================"

verificar_http "http://localhost:8000" "Aplicación principal"
verificar_http "http://localhost:8000/admin/" "Panel de administración"
verificar_http "http://localhost:5555" "Monitor Celery (Flower)"
verificar_http "http://localhost:8000/auditoria/" "Dashboard de auditoría"

echo

# 6. VERIFICAR VOLÚMENES Y DATOS
echo -e "${BLUE}💾 VERIFICACIÓN DE VOLÚMENES${NC}"
echo "================================"

# Verificar volúmenes Docker
postgres_volume=$(docker volume ls | grep postgres | awk '{print $2}' | head -n1)
if [ -n "$postgres_volume" ]; then
    echo -e "${GREEN}✅ Volumen PostgreSQL: $postgres_volume${NC}"
else
    echo -e "${YELLOW}⚠️  Volumen PostgreSQL no encontrado${NC}"
fi

# Verificar directorios importantes
dirs=("./media" "./static" "./logs" "./backups")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        echo -e "${GREEN}✅ Directorio $dir ($size)${NC}"
    else
        echo -e "${YELLOW}⚠️  Directorio $dir no existe${NC}"
    fi
done
echo

# 7. ESTADÍSTICAS DE RENDIMIENTO
echo -e "${BLUE}📊 ESTADÍSTICAS DE RENDIMIENTO${NC}"
echo "================================"

# Uso de CPU y memoria de contenedores
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" actas_web actas_postgres actas_celery_worker actas_redis 2>/dev/null || echo "No se pudieron obtener estadísticas"

echo

# 8. VERIFICAR LOGS RECIENTES
echo -e "${BLUE}📋 LOGS RECIENTES (ÚLTIMAS 5 LÍNEAS)${NC}"
echo "================================"

echo -e "${CYAN}Django Web:${NC}"
docker logs --tail=5 actas_web 2>/dev/null | head -5 || echo "No hay logs disponibles"

echo -e "${CYAN}PostgreSQL:${NC}"
docker logs --tail=5 actas_postgres 2>/dev/null | head -5 || echo "No hay logs disponibles"

echo -e "${CYAN}Celery Worker:${NC}"  
docker logs --tail=5 actas_celery_worker 2>/dev/null | head -5 || echo "No hay logs disponibles"

echo

# 9. RESUMEN FINAL
echo -e "${PURPLE}================================================================${NC}"
echo -e "${PURPLE}                        RESUMEN FINAL                          ${NC}"
echo -e "${PURPLE}================================================================${NC}"

# Contar servicios funcionando
running_containers=$(docker ps --filter "name=actas_" --format "{{.Names}}" | wc -l)
expected_containers=7

if [ "$running_containers" -eq "$expected_containers" ]; then
    echo -e "${GREEN}🎉 SISTEMA COMPLETAMENTE FUNCIONAL${NC}"
    echo -e "${GREEN}   $running_containers/$expected_containers contenedores ejecutándose${NC}"
elif [ "$running_containers" -gt 4 ]; then
    echo -e "${YELLOW}⚠️  SISTEMA MAYORMENTE FUNCIONAL${NC}"
    echo -e "${YELLOW}   $running_containers/$expected_containers contenedores ejecutándose${NC}"
else
    echo -e "${RED}❌ SISTEMA CON PROBLEMAS CRÍTICOS${NC}"
    echo -e "${RED}   Solo $running_containers/$expected_containers contenedores ejecutándose${NC}"
fi

echo
echo -e "${CYAN}🔧 ACCIONES RECOMENDADAS:${NC}"
if docker exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\\dn" 2>/dev/null | grep -q logs; then
    echo -e "${GREEN}   ✅ Schema de logs OK${NC}"
else
    echo -e "${RED}   🚨 Aplicar schema de logs: ./INSTALADOR_ACTAS_IA.sh → Opción 9${NC}"
fi

if [ "$running_containers" -lt "$expected_containers" ]; then
    echo -e "${YELLOW}   🔄 Reiniciar sistema: ./reiniciar_sistema.sh${NC}"
    echo -e "${YELLOW}   🛠️  Reparación completa: ./INSTALADOR_ACTAS_IA.sh → Opción 3${NC}"
fi

echo
echo -e "${CYAN}📞 URLs de acceso:${NC}"
echo "   - http://localhost:8000 (Aplicación)"
echo "   - http://localhost:8000/admin/ (Administración)"
echo "   - http://localhost:5555 (Monitor Celery)"

echo
echo "Presiona Enter para salir..."
read