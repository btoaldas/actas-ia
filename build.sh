#!/usr/bin/env bash
# Script de build para el Sistema de Actas Municipales de Pastaza
# Optimizado para deployment en Render

set -o errexit  # Salir en caso de error

echo "🏛️ Iniciando build para Sistema de Actas Municipales de Pastaza..."

# Instalar y ejecutar WebPack para frontend
echo "📦 Instalando dependencias de frontend..."
if [ -f "package.json" ]; then
    if command -v pnpm &> /dev/null; then
        pnpm i
        pnpm run webpack:build
    elif command -v npm &> /dev/null; then
        npm install
        npm run webpack:build
    else
        echo "⚠️ No se encontró pnpm ni npm, saltando build de frontend"
    fi
else
    echo "⚠️ No se encontró package.json, saltando build de frontend"
fi

# Actualizar pip
echo "🔧 Actualizando pip..."
python -m pip install --upgrade pip

# Instalar dependencias Python
echo "📋 Instalando dependencias Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "requirements.basic.txt" ]; then
    pip install -r requirements.basic.txt
else
    echo "❌ No se encontró archivo de requirements"
    exit 1
fi

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --no-input

# Crear y aplicar migraciones
echo "🗄️ Aplicando migraciones de base de datos..."
python manage.py makemigrations
python manage.py migrate

# Crear usuarios iniciales si no existen
echo "👥 Creando usuarios iniciales del municipio..."
python manage.py crear_usuarios_iniciales || echo "⚠️ Los usuarios ya existen o hubo un error menor"

# Verificar que Django funciona
echo "✅ Verificando configuración de Django..."
python manage.py check

echo "🎉 Build completado exitosamente para el Municipio de Pastaza!"
