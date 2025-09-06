#!/bin/bash

# Script de inicio para el Sistema de Actas Municipales de Pastaza
# Este script automatiza el levantamiento completo del entorno

echo "🏛️ ========================================="
echo "   Sistema de Actas Municipales de Pastaza"
echo "   Municipio de Pastaza - Puyo, Ecuador"
echo "========================================="
echo ""

# Función para verificar si Docker está ejecutándose
verificar_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Error: Docker no está ejecutándose o no está accesible."
        echo "   Por favor, inicia Docker Desktop e intenta nuevamente."
        exit 1
    fi
    echo "✅ Docker está ejecutándose correctamente"
}

# Función para limpiar contenedores anteriores
limpiar_contenedores() {
    echo "🧹 Limpiando contenedores anteriores..."
    docker-compose -f docker-compose.simple.yml down > /dev/null 2>&1
    echo "✅ Contenedores anteriores limpiados"
}

# Función para construir las imágenes
construir_imagenes() {
    echo "🔨 Construyendo imágenes Docker..."
    if docker-compose -f docker-compose.simple.yml build; then
        echo "✅ Imágenes construidas exitosamente"
    else
        echo "❌ Error al construir las imágenes"
        exit 1
    fi
}

# Función para levantar servicios de base de datos
levantar_bd() {
    echo "🗄️ Levantando PostgreSQL y Redis..."
    if docker-compose -f docker-compose.simple.yml up -d db_postgres redis; then
        echo "✅ PostgreSQL y Redis levantados exitosamente"
        echo "⏳ Esperando que PostgreSQL esté listo..."
        sleep 10
    else
        echo "❌ Error al levantar PostgreSQL y Redis"
        exit 1
    fi
}

# Función para aplicar migraciones
aplicar_migraciones() {
    echo "📊 Aplicando migraciones de base de datos..."
    if docker-compose -f docker-compose.simple.yml run --rm web python manage.py migrate; then
        echo "✅ Migraciones aplicadas exitosamente"
    else
        echo "❌ Error al aplicar migraciones"
        exit 1
    fi
}

# Función para crear usuarios iniciales
crear_usuarios() {
    echo "👥 Creando usuarios iniciales..."
    if docker-compose -f docker-compose.simple.yml run --rm web python manage.py crear_usuarios_iniciales; then
        echo "✅ Usuarios iniciales creados exitosamente"
    else
        echo "⚠️ Los usuarios ya existen o hubo un error menor"
    fi
}

# Función para levantar el servicio web
levantar_web() {
    echo "🌐 Levantando servidor web Django..."
    if docker-compose -f docker-compose.simple.yml up -d web; then
        echo "✅ Servidor web levantado exitosamente"
    else
        echo "❌ Error al levantar el servidor web"
        exit 1
    fi
}

# Función para mostrar información final
mostrar_info() {
    echo ""
    echo "🎉 ¡Sistema levantado exitosamente!"
    echo ""
    echo "🌐 URLS DE ACCESO:"
    echo "   - Aplicación principal: http://localhost:8000"
    echo "   - Panel de administración: http://localhost:8000/admin/"
    echo ""
    echo "🔑 USUARIOS DE PRUEBA:"
    echo "   - Super Admin: superadmin / AdminPuyo2025!"
    echo "   - Alcalde: alcalde.pastaza / AlcaldePuyo2025!"
    echo "   - Secretario: secretario.concejo / SecretarioPuyo2025!"
    echo ""
    echo "📊 BASE DE DATOS POSTGRESQL:"
    echo "   - Host: localhost:5432"
    echo "   - Base de datos: actas_municipales_pastaza"
    echo "   - Usuario: admin_actas"
    echo "   - Contraseña: actas_pastaza_2025"
    echo ""
    echo "🛠️ COMANDOS ÚTILES:"
    echo "   - Ver logs: docker-compose -f docker-compose.simple.yml logs"
    echo "   - Parar sistema: docker-compose -f docker-compose.simple.yml down"
    echo "   - Acceder al contenedor: docker-compose -f docker-compose.simple.yml exec web bash"
    echo ""
    echo "📧 Soporte: tecnico@puyo.gob.ec"
    echo "🏛️ Municipio de Pastaza - Sistema de Actas Municipales"
}

# Ejecutar funciones principales
main() {
    verificar_docker
    limpiar_contenedores
    construir_imagenes
    levantar_bd
    aplicar_migraciones
    crear_usuarios
    levantar_web
    mostrar_info
}

# Manejar interrupciones
trap 'echo ""; echo "⚠️ Proceso interrumpido por el usuario"; exit 1' INT TERM

# Ejecutar script principal
main
