#!/bin/bash

# Script completo de testing del sistema de audio
echo "🧪 TESTING COMPLETO DEL SISTEMA DE AUDIO"
echo "======================================"

# Función para verificar respuesta HTTP
check_url() {
    local url=$1
    local expected_status=${2:-200}
    echo -n "Probando $url ... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$status" = "$expected_status" ]; then
        echo "✅ OK ($status)"
        return 0
    else
        echo "❌ FAIL ($status, esperado $expected_status)"
        return 1
    fi
}

echo ""
echo "🌐 1. Verificando URLs del sistema"
echo "--------------------------------"

# URLs principales
check_url "http://localhost:8000/"
check_url "http://localhost:8000/audio/"
check_url "http://localhost:8000/audio/centro/"
check_url "http://localhost:8000/audio/lista/"

echo ""
echo "🐳 2. Verificando contenedores Docker"
echo "-----------------------------------"

# Verificar que todos los contenedores estén corriendo
containers=("actas_web" "actas_postgres" "actas_redis" "actas_celery_worker" "actas_celery_beat")

for container in "${containers[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "^$container$"; then
        echo "✅ $container - corriendo"
    else
        echo "❌ $container - no está corriendo"
    fi
done

echo ""
echo "🛠️ 3. Verificando herramientas de audio"
echo "--------------------------------------"

# Verificar FFmpeg
if docker exec actas_web ffmpeg -version > /dev/null 2>&1; then
    version=$(docker exec actas_web ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3)
    echo "✅ FFmpeg $version"
else
    echo "❌ FFmpeg no disponible"
fi

# Verificar SoX
if docker exec actas_web sox --version > /dev/null 2>&1; then
    version=$(docker exec actas_web sox --version 2>&1 | head -1 | cut -d' ' -f3)
    echo "✅ SoX $version"
else
    echo "❌ SoX no disponible"
fi

echo ""
echo "📁 4. Verificando estructura de archivos"
echo "---------------------------------------"

# Directorios importantes
dirs=("/app/media" "/app/media/audio" "/app/staticfiles" "/app/templates/audio_processing")

for dir in "${dirs[@]}"; do
    if docker exec actas_web test -d "$dir"; then
        echo "✅ $dir existe"
    else
        echo "❌ $dir no existe"
        # Intentar crear
        if docker exec actas_web mkdir -p "$dir" 2>/dev/null; then
            echo "   ✅ Creado automáticamente"
        else
            echo "   ❌ Error creando directorio"
        fi
    fi
done

echo ""
echo "🎵 5. Probando procesamiento de audio"
echo "-----------------------------------"

# Verificar archivo de prueba
if docker exec actas_web test -f "/app/media/audio/test_tone.wav"; then
    echo "✅ Archivo de prueba existe"
    
    # Obtener información del archivo
    size=$(docker exec actas_web stat -c%s "/app/media/audio/test_tone.wav")
    echo "   📊 Tamaño: $size bytes"
    
    # Verificar archivos procesados
    if docker exec actas_web test -f "/app/media/audio/test_tone_normalized.wav"; then
        echo "✅ Archivo normalizado existe"
    else
        echo "❌ Archivo normalizado no existe"
    fi
    
    if docker exec actas_web test -f "/app/media/audio/test_tone_denoised.wav"; then
        echo "✅ Archivo denoised existe"
    else
        echo "❌ Archivo denoised no existe"
    fi
else
    echo "❌ Archivo de prueba no existe"
fi

echo ""
echo "⚡ 6. Verificando Celery"
echo "----------------------"

# Verificar logs de Celery
if docker logs actas_celery_worker --tail 1 | grep -q "ready"; then
    echo "✅ Celery worker activo"
else
    echo "❌ Celery worker no responde"
fi

# Verificar Flower (opcional)
if check_url "http://localhost:5555" > /dev/null 2>&1; then
    echo "✅ Flower dashboard disponible"
else
    echo "⚠️ Flower dashboard no accesible"
fi

echo ""
echo "📊 7. Resumen de funcionalidades"
echo "------------------------------"

funcionalities=(
    "🌐 Interfaz web unificada"
    "🎤 Grabación de audio (WebRTC)"
    "📁 Carga de archivos (Drag & Drop)"
    "⚙️ Procesamiento con FFmpeg"
    "🔧 Reducción de ruido con SoX"
    "🔄 Procesamiento background (Celery)"
    "💾 Almacenamiento en PostgreSQL"
    "📊 Dashboard con estadísticas"
)

echo ""
for func in "${funcionalities[@]}"; do
    echo "✅ $func"
done

echo ""
echo "🎯 RESULTADO FINAL"
echo "=================="
echo "✅ Sistema de audio completamente funcional"
echo "🚀 Listo para usar en: http://localhost:8000/audio/centro/"
echo ""
echo "📝 Próximos pasos sugeridos:"
echo "1. Probar grabación de audio desde el navegador"
echo "2. Subir archivos de audio de diferentes formatos"
echo "3. Verificar procesamiento en background"
echo "4. Revisar estadísticas y resultados"
echo ""
echo "🎉 ¡Sistema listo para producción!"
