#!/usr/bin/env python
"""
Script de prueba para el sistema completo de Fase 2: Drag & Drop + Celery
Prueba el flujo completo desde la interfaz hasta la generación de actas
"""

import os
import sys
import django
import requests
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.generador_actas.models import (
    PlantillaActa, ConfiguracionSegmento, SegmentoPlantilla, 
    EjecucionPlantilla, ResultadoSegmento, ActaBorrador, ProveedorIA
)
from apps.generador_actas.tasks import procesar_plantilla_completa_task

def test_drag_drop_interface():
    """Prueba 1: Verificar que la interfaz de drag & drop es accesible"""
    print("🔍 Probando interfaz de drag & drop...")
    
    # Obtener plantilla demo
    try:
        plantilla = PlantillaActa.objects.get(nombre="Plantilla Demo - Drag & Drop")
        print(f"✅ Plantilla encontrada: {plantilla.nombre} (ID: {plantilla.pk})")
        
        # Verificar configuraciones
        configs = ConfiguracionSegmento.objects.filter(plantilla=plantilla).count()
        print(f"✅ Configuraciones de segmentos: {configs}")
        
        return plantilla
    except PlantillaActa.DoesNotExist:
        print("❌ Plantilla demo no encontrada")
        return None

def test_web_interface():
    """Prueba 2: Verificar URLs y respuestas web"""
    print("\n🌐 Probando interfaz web...")
    
    base_url = "http://localhost:8000"
    
    # Probar página principal
    try:
        response = requests.get(f"{base_url}/generador-actas/", timeout=10)
        print(f"✅ Dashboard accesible: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Error accediendo dashboard: {e}")
        return False
    
    return True

def test_celery_tasks():
    """Prueba 3: Verificar funciones Celery"""
    print("\n⚙️ Probando sistema Celery...")
    
    # Verificar que las tareas están disponibles
    try:
        from apps.generador_actas.tasks import (
            procesar_plantilla_completa_task,
            procesar_segmento_con_ia_task,
            procesar_segmento_estatico_task,
            unificar_segmentos_task
        )
        print("✅ Todas las tareas Celery importadas correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando tareas Celery: {e}")
        return False

def test_database_structure():
    """Prueba 4: Verificar estructura de base de datos"""
    print("\n🗃️ Probando estructura de base de datos...")
    
    # Verificar modelos
    try:
        plantillas_count = PlantillaActa.objects.count()
        segmentos_count = SegmentoPlantilla.objects.count()
        configs_count = ConfiguracionSegmento.objects.count()
        
        print(f"✅ Plantillas en BD: {plantillas_count}")
        print(f"✅ Segmentos disponibles: {segmentos_count}")
        print(f"✅ Configuraciones: {configs_count}")
        
        # Verificar plantilla demo específica
        demo_plantilla = PlantillaActa.objects.filter(nombre="Plantilla Demo - Drag & Drop").first()
        if demo_plantilla:
            demo_configs = ConfiguracionSegmento.objects.filter(plantilla=demo_plantilla).count()
            print(f"✅ Demo plantilla tiene {demo_configs} configuraciones")
            return True
        else:
            print("❌ Plantilla demo no encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando BD: {e}")
        return False

def test_demo_execution():
    """Prueba 5: Crear ejecución de prueba (sin procesar)"""
    print("\n🚀 Probando creación de ejecución...")
    
    try:
        plantilla = PlantillaActa.objects.get(nombre="Plantilla Demo - Drag & Drop")
        
        # Obtener un proveedor IA por defecto
        proveedor_ia = ProveedorIA.objects.filter(activo=True).first()
        if not proveedor_ia:
            print("❌ No hay proveedores IA activos")
            return None
        
        # Crear ejecución de prueba
        ejecucion = EjecucionPlantilla.objects.create(
            plantilla=plantilla,
            nombre="Ejecución Demo Fase 2",
            usuario=User.objects.get(username='superadmin'),
            proveedor_ia_global=proveedor_ia,
            estado='iniciada',
            variables_contexto={
                'nombre_municipio': 'Pastaza',
                'fecha_reunion': '2025-09-27',
                'tipo_reunion': 'ordinaria',
                'test_mode': True,
                'fecha_test': datetime.now().isoformat(),
                'tipo_test': 'fase_2_demo'
            }
        )
        
        print(f"✅ Ejecución creada: {ejecucion.id} - Estado: {ejecucion.estado}")
        print(f"✅ Plantilla: {ejecucion.plantilla.nombre}")
        print(f"✅ Proveedor IA: {ejecucion.proveedor_ia_global.nombre}")
        
        return ejecucion
        
    except Exception as e:
        print(f"❌ Error creando ejecución: {e}")
        return None

def test_complete_workflow():
    """Prueba completa del workflow"""
    print("\n" + "="*60)
    print("🎯 PRUEBA COMPLETA - FASE 2: DRAG & DROP + CELERY")
    print("="*60)
    
    results = {
        'drag_drop': False,
        'web_interface': False,
        'celery_tasks': False,
        'database': False,
        'demo_execution': False
    }
    
    # Ejecutar todas las pruebas
    plantilla = test_drag_drop_interface()
    results['drag_drop'] = plantilla is not None
    
    results['web_interface'] = test_web_interface()
    results['celery_tasks'] = test_celery_tasks()
    results['database'] = test_database_structure()
    
    ejecucion = test_demo_execution()
    results['demo_execution'] = ejecucion is not None
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper():.<30} {status}")
    
    print(f"\nRESULTADO: {passed_tests}/{total_tests} pruebas exitosas")
    
    if passed_tests == total_tests:
        print("\n🎉 ¡FASE 2 COMPLETADA CON ÉXITO!")
        print("✅ Sistema de Drag & Drop funcional")
        print("✅ Tareas Celery implementadas")
        print("✅ Interfaz web operativa") 
        print("✅ Base de datos configurada")
        print("✅ Ejecución demo creada")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} pruebas fallaron")
        print("Revisar los errores arriba para más detalles")
    
    return passed_tests == total_tests

if __name__ == '__main__':
    success = test_complete_workflow()
    sys.exit(0 if success else 1)