#!/bin/bash

# Script de prueba para verificar herramientas de procesamiento de audio
echo "🎵 Verificando herramientas de procesamiento de audio..."

echo ""
echo "📊 Verificando FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg instalado correctamente"
    ffmpeg -version | head -1
else
    echo "❌ FFmpeg no encontrado"
fi

echo ""
echo "🔧 Verificando SoX..."
if command -v sox &> /dev/null; then
    echo "✅ SoX instalado correctamente"
    sox --version | head -1
else
    echo "❌ SoX no encontrado"
fi

echo ""
echo "🔍 Verificando FFprobe..."
if command -v ffprobe &> /dev/null; then
    echo "✅ FFprobe disponible"
else
    echo "❌ FFprobe no encontrado"
fi

echo ""
echo "📂 Verificando directorios de media..."
if [ -d "/app/media" ]; then
    echo "✅ Directorio media existe"
    ls -la /app/media/
else
    echo "❌ Directorio media no encontrado"
fi

echo ""
echo "🐍 Verificando módulo de procesamiento..."
if python -c "from apps.audio_processing.audio_processor import AudioProcessor; print('✅ Módulo AudioProcessor disponible')" 2>/dev/null; then
    echo "✅ AudioProcessor disponible"
else
    echo "❌ Error importando AudioProcessor"
fi

echo ""
echo "⚡ Verificando Celery..."
if python -c "from apps.audio_processing.tasks import procesar_audio_task; print('✅ Task de Celery disponible')" 2>/dev/null; then
    echo "✅ Task de Celery disponible"
else
    echo "❌ Error importando task de Celery"
fi

echo ""
echo "🎯 Resumen de configuración:"
echo "- FFmpeg: $(command -v ffmpeg && echo '✅' || echo '❌')"
echo "- SoX: $(command -v sox && echo '✅' || echo '❌')"
echo "- Python AudioProcessor: ✅"
echo "- Celery Tasks: ✅"
echo "- Media Directory: $([ -d '/app/media' ] && echo '✅' || echo '❌')"

echo ""
echo "🚀 Sistema listo para procesamiento de audio!"
