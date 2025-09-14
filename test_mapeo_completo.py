#!/usr/bin/env python3
"""
Test completo del mapeo corregido de speakers
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion, ProcesamientoAudio, EstadoTranscripcion
from apps.transcripcion.tasks import procesar_transcripcion_completa

def test_mapeo_completo():
    print("🧪 TEST COMPLETO DEL MAPEO CORREGIDO")
    print("=" * 60)
    
    # Buscar procesamiento de audio con participantes
    procesamiento = ProcesamientoAudio.objects.filter(
        participantes_detallados__isnull=False
    ).order_by('-id').first()
    
    if not procesamiento:
        print("❌ No hay procesamiento de audio con participantes")
        return
    
    print(f"🎵 Procesamiento de Audio ID: {procesamiento.id}")
    participantes = procesamiento.participantes_detallados or []
    print(f"👥 Participantes: {[p.get('nombres', 'Sin nombre') for p in participantes]}")
    
    # Crear nueva transcripción para probar
    transcripcion = Transcripcion.objects.create(
        procesamiento_audio=procesamiento,
        estado=EstadoTranscripcion.PENDIENTE
    )
    
    print(f"📝 Transcripción creada: ID {transcripcion.id}")
    
    try:
        # Ejecutar procesamiento completo
        print("🔄 Iniciando procesamiento...")
        resultado = procesar_transcripcion_completa.delay(transcripcion.id)
        
        print(f"✅ Tarea iniciada: {resultado.id}")
        print("📌 Para verificar resultado, revisar:")
        print(f"   - Transcripción ID: {transcripcion.id}")
        print(f"   - Estado en admin: http://localhost:8000/admin/transcripcion/transcripcion/{transcripcion.id}/")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Limpiar transcripción de prueba
        transcripcion.delete()

if __name__ == "__main__":
    test_mapeo_completo()