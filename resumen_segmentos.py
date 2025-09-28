#!/usr/bin/env python3
"""
Resumen completo de segmentos creados
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

from apps.generador_actas.models import SegmentoPlantilla

def generar_resumen():
    print("=" * 60)
    print("RESUMEN COMPLETO DE SEGMENTOS CREADOS")
    print("=" * 60)
    
    segmentos = SegmentoPlantilla.objects.all().order_by('categoria', 'tipo')
    total_estaticos = segmentos.filter(tipo='estatico').count()
    total_dinamicos = segmentos.filter(tipo='dinamico').count()
    
    print(f"ESTADISTICAS:")
    print(f"   Total segmentos: {segmentos.count()}")
    print(f"   Estaticos: {total_estaticos}")
    print(f"   Dinamicos: {total_dinamicos}")
    print()
    
    categorias = ['encabezado', 'participantes', 'agenda', 'decisiones', 'cierre']
    for categoria in categorias:
        print(f"CATEGORIA: {categoria.upper()}")
        segs_categoria = segmentos.filter(categoria=categoria)
        for seg in segs_categoria:
            print(f"   ID {seg.pk}: {seg.nombre}")
            print(f"      Codigo: {seg.codigo}")
            print(f"      Tipo: {seg.tipo}")
            if seg.tipo == 'estatico':
                print(f"      Contenido: {len(seg.contenido_estatico)} caracteres")
            else:
                print(f"      Prompt IA: {len(seg.prompt_ia)} caracteres")
            print(f"      Estado: {'Activo' if seg.activo else 'Inactivo'}")
            print()
        print()
    
    print("FUNCIONALIDADES DISPONIBLES:")
    print("   - Auto-completado en formularios")
    print("   - Segmentos estaticos con HTML municipal")
    print("   - Segmentos dinamicos con prompts IA")
    print("   - Variables de plantilla ({{variable}})")
    print("   - Formato AdminLTE compatible")
    print("   - Integracion con proveedores IA")
    print()
    
    print("EJEMPLOS DE USO:")
    print("   1. Crear formulario: usar auto-completado")
    print("   2. Generar acta: seleccionar segmentos apropiados") 
    print("   3. Personalizar: editar contenido o prompts")
    print("   4. Administrar: activar/desactivar segmentos")
    
    print("=" * 60)
    print("PROCESO COMPLETADO EXITOSAMENTE")
    print("=" * 60)

if __name__ == "__main__":
    generar_resumen()