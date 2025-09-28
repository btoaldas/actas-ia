#!/usr/bin/env python
"""
Test para verificar sincronización automática después del procesamiento de Celery
Simula el comportamiento típico: crear ActaGenerada → procesamiento Celery → actualización contenido
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.generador_actas.models import ActaGenerada, PlantillaActa, ProveedorIA
from gestion_actas.models import GestionActa
from apps.transcripcion.models import Transcripcion
from django.contrib.auth.models import User
from django.utils import timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_flujo_completo():
    """
    Simula el flujo completo:
    1. Crear ActaGenerada (como hace el frontend)
    2. Simular actualización por Celery con contenido_html
    3. Verificar que GestionActa se sincroniza automáticamente
    """
    
    # Obtener datos necesarios
    user = User.objects.get(username='superadmin')
    transcripcion = Transcripcion.objects.first()
    plantilla = PlantillaActa.objects.first()
    proveedor = ProveedorIA.objects.filter(activo=True).first()
    
    print("=== PASO 1: Crear ActaGenerada (simular frontend) ===")
    
    # Crear ActaGenerada SIN contenido (como hace el frontend inicialmente)
    acta = ActaGenerada.objects.create(
        numero_acta='TEST-CELERY-2025-001',
        titulo='Test Sincronización Post-Celery',
        transcripcion=transcripcion,
        plantilla=plantilla,
        proveedor_ia=proveedor,
        fecha_sesion=timezone.now(),
        usuario_creacion=user,
        estado='procesando',  # Estado inicial
        # SIN contenido_html/contenido_final - VACÍO inicialmente
    )
    
    print(f"✅ ActaGenerada creada - ID: {acta.id}")
    print(f"   - Título: {acta.titulo}")
    print(f"   - Estado: {acta.estado}")
    print(f"   - Contenido HTML: {len(acta.contenido_html or '')} chars")
    print(f"   - Contenido Final: {len(acta.contenido_final or '')} chars")
    
    # Verificar que se creó GestionActa (vacía inicialmente)
    try:
        gestion_acta = GestionActa.objects.get(acta_generada=acta)
        print(f"✅ GestionActa creada automáticamente - ID: {gestion_acta.id}")
        print(f"   - Contenido editado: {len(gestion_acta.contenido_editado or '')} chars")
        print(f"   - Estado: {gestion_acta.estado}")
    except GestionActa.DoesNotExist:
        print("❌ ERROR: GestionActa NO se creó automáticamente")
        return False
    
    print("\n=== PASO 2: Simular procesamiento Celery ===")
    
    # Simular que Celery terminó y actualiza el contenido
    contenido_procesado = """
    <h2>ACTA DE PRUEBA - PROCESAMIENTO CELERY</h2>
    <p>Este contenido fue generado por Celery después del procesamiento.</p>
    <h3>Asistentes:</h3>
    <ul>
        <li>Juan Pérez - Alcalde</li>
        <li>María González - Secretaria</li>
        <li>Carlos López - Concejal</li>
    </ul>
    <h3>Temas Tratados:</h3>
    <p>1. Aprobación del presupuesto municipal</p>
    <p>2. Proyectos de infraestructura</p>
    <p>3. Asuntos varios</p>
    <h3>Conclusiones:</h3>
    <p>Se aprobaron todas las propuestas por unanimidad.</p>
    """
    
    # ACTUALIZAR ActaGenerada (simular lo que hace Celery)
    acta.contenido_html = contenido_procesado
    acta.contenido_final = contenido_procesado.replace('<br>', '\n')
    acta.estado = 'revision'  # Celery cambia estado a revisión
    acta.progreso = 100
    acta.save()  # ESTO DEBE DISPARAR LA SEÑAL DE UPDATE
    
    print(f"✅ ActaGenerada actualizada por 'Celery'")
    print(f"   - Nuevo contenido HTML: {len(acta.contenido_html)} chars")
    print(f"   - Nuevo estado: {acta.estado}")
    
    print("\n=== PASO 3: Verificar sincronización automática ===")
    
    # Recargar GestionActa desde BD
    gestion_acta.refresh_from_db()
    
    contenido_sincronizado = gestion_acta.contenido_editado or ''
    
    print(f"📊 Resultados de sincronización:")
    print(f"   - ActaGenerada contenido: {len(acta.contenido_html)} chars")
    print(f"   - GestionActa contenido: {len(contenido_sincronizado)} chars")
    print(f"   - ¿Contenido coincide?: {'✅ SÍ' if contenido_sincronizado == acta.contenido_html else '❌ NO'}")
    
    if contenido_sincronizado == acta.contenido_html:
        print("🎉 ÉXITO: Sincronización post-Celery funcionando correctamente!")
        
        # Mostrar preview del contenido
        print(f"\n📄 Preview del contenido sincronizado:")
        preview = contenido_sincronizado[:200] + "..." if len(contenido_sincronizado) > 200 else contenido_sincronizado
        print(f"   {preview}")
        
        return True
    else:
        print("❌ FALLO: La sincronización NO funcionó")
        
        # Debug información
        print(f"\n🔍 Debug:")
        print(f"   - Cambios realizados: {gestion_acta.cambios_realizados}")
        print(f"   - Última edición: {gestion_acta.fecha_ultima_edicion}")
        print(f"   - Observaciones: {gestion_acta.observaciones}")
        
        return False

def cleanup_test_data():
    """Limpiar datos de prueba"""
    print("\n=== LIMPIEZA ===")
    
    actas_test = ActaGenerada.objects.filter(numero_acta__startswith='TEST-CELERY-')
    if actas_test.exists():
        count = actas_test.count()
        actas_test.delete()
        print(f"🧹 Eliminadas {count} ActaGenerada de prueba")
    else:
        print("🧹 No hay datos de prueba que limpiar")

if __name__ == '__main__':
    print("🚀 INICIANDO TEST DE SINCRONIZACIÓN CELERY")
    print("=" * 60)
    
    try:
        # Ejecutar test
        exito = test_flujo_completo()
        
        if exito:
            print("\n" + "=" * 60)
            print("✅ TEST COMPLETADO EXITOSAMENTE")
            print("La sincronización post-Celery está funcionando correctamente!")
        else:
            print("\n" + "=" * 60)
            print("❌ TEST FALLÓ")
            print("La sincronización necesita ajustes.")
            
    except Exception as e:
        print(f"\n❌ ERROR DURANTE EL TEST: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Preguntar si limpiar datos
        respuesta = input("\n¿Deseas limpiar los datos de prueba? (s/n): ").lower().strip()
        if respuesta in ['s', 'si', 'y', 'yes']:
            cleanup_test_data()
        else:
            print("🗂️ Datos de prueba conservados para inspección manual")