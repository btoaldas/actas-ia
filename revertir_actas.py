#!/usr/bin/env python3
"""
Script para revertir todas las actas procesadas al estado borrador
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

from apps.generador_actas.models import ActaGenerada
from django.utils import timezone

def revertir_actas_procesadas():
    """Revierte todas las actas procesadas al estado borrador"""
    print("🔄 INICIANDO REVERSIÓN DE ACTAS PROCESADAS")
    print("=" * 50)
    
    # Obtener actas procesadas
    actas_procesadas = ActaGenerada.objects.filter(
        estado__in=['revision', 'aprobado', 'publicado', 'error']
    ).order_by('-id')
    
    total_actas = actas_procesadas.count()
    print(f"📊 Actas encontradas para revertir: {total_actas}")
    
    if total_actas == 0:
        print("ℹ️ No hay actas para revertir")
        return
    
    print("\n📋 Lista de actas a revertir:")
    for acta in actas_procesadas:
        print(f"   ID {acta.id}: {acta.numero_acta} (Estado: {acta.estado})")
    
    # Confirmar acción
    respuesta = input(f"\n❓ ¿Confirmas revertir {total_actas} actas? (s/N): ").strip().lower()
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada")
        return
    
    print(f"\n🔄 Revirtiendo {total_actas} actas...")
    
    # Revertir cada acta
    revertidas = 0
    for acta in actas_procesadas:
        try:
            # Limpiar todos los campos del procesamiento
            acta.estado = 'borrador'
            acta.progreso = 0
            acta.segmentos_procesados = {}
            acta.historial_cambios = []
            acta.contenido_borrador = ''
            acta.contenido_final = ''
            acta.contenido_html = ''
            acta.mensajes_error = ''
            acta.metricas_procesamiento = {}
            acta.metadatos = {}
            acta.task_id_celery = ''
            acta.fecha_procesamiento = None
            
            acta.save()
            revertidas += 1
            print(f"   ✅ {acta.numero_acta} revertida")
            
        except Exception as e:
            print(f"   ❌ Error en {acta.numero_acta}: {str(e)}")
    
    print(f"\n🎉 PROCESO COMPLETADO")
    print(f"   ✅ Actas revertidas: {revertidas}")
    print(f"   ❌ Errores: {total_actas - revertidas}")
    print("\n💡 Ahora puedes reprocesar las actas con la nueva funcionalidad del prompt global")

if __name__ == "__main__":
    revertir_actas_procesadas()