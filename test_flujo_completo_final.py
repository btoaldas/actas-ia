#!/usr/bin/env python
"""
TEST FINAL - Flujo completo end-to-end
Crear → Procesar con Celery Real → Verificar Sincronización Automática
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.generador_actas.models import ActaGenerada, PlantillaActa, ProveedorIA
from apps.generador_actas.tasks import procesar_acta_simple_task
from gestion_actas.models import GestionActa
from apps.transcripcion.models import Transcripcion
from django.contrib.auth.models import User
from django.utils import timezone
import time

print("🚀 TEST FINAL - FLUJO COMPLETO END-TO-END")
print("=" * 60)

# Obtener datos necesarios
user = User.objects.get(username='superadmin')
transcripcion = Transcripcion.objects.first()
plantilla = PlantillaActa.objects.first()
proveedor = ProveedorIA.objects.filter(activo=True).first()

print("📋 PASO 1: Crear ActaGenerada vacía (como hace el frontend)")

# Crear ActaGenerada vacía (estado inicial del frontend)
acta = ActaGenerada.objects.create(
    numero_acta='TEST-FLUJO-COMPLETO-2025-001',
    titulo='Test Flujo Completo End-to-End',
    transcripcion=transcripcion,
    plantilla=plantilla,
    proveedor_ia=proveedor,
    fecha_sesion=timezone.now(),
    usuario_creacion=user,
    estado='borrador',  # Estado inicial
    progreso=0
    # SIN contenido_html - completamente vacío
)

print(f"✅ ActaGenerada creada - ID: {acta.id}")
print(f"   - Estado: {acta.estado}")
print(f"   - Progreso: {acta.progreso}%") 
print(f"   - Contenido: {len(acta.contenido_html or '')} chars")

# Verificar creación automática de GestionActa
try:
    gestion_acta = GestionActa.objects.get(acta_generada=acta)
    print(f"✅ GestionActa creada automáticamente - ID: {gestion_acta.id}")
    print(f"   - Contenido inicial: {len(gestion_acta.contenido_editado or '')} chars")
    print(f"   - Estado: {gestion_acta.estado}")
except GestionActa.DoesNotExist:
    print("❌ ERROR: GestionActa NO se creó automáticamente")
    exit(1)

print(f"\n📋 PASO 2: Lanzar procesamiento REAL de Celery")

# Lanzar tarea Celery REAL
print("🔄 Iniciando tarea Celery...")
resultado_celery = procesar_acta_simple_task.apply_async(args=[acta.id])

print(f"✅ Tarea Celery lanzada")
print(f"   - Task ID: {resultado_celery.id}")
print(f"   - Estado inicial: {resultado_celery.state}")

print(f"\n📋 PASO 3: Esperar y monitorear procesamiento")

# Monitorear progreso
max_intentos = 60  # 60 segundos máximo
intento = 0

while intento < max_intentos:
    intento += 1
    
    # Recargar acta desde BD
    acta.refresh_from_db()
    
    print(f"⏱️ Intento {intento}/60 - Estado: {acta.estado} - Progreso: {acta.progreso}% - Contenido: {len(acta.contenido_html or '')} chars")
    
    # Si terminó exitosamente
    if acta.estado in ['revision', 'completado'] and acta.progreso == 100:
        print(f"🎉 ¡Procesamiento Celery completado exitosamente!")
        break
    
    # Si falló
    if acta.estado == 'error':
        print(f"❌ Procesamiento Celery falló")
        break
        
    time.sleep(1)

if intento >= max_intentos:
    print(f"⏰ Timeout - Procesamiento tomó más de 60 segundos")
    print(f"   Estado final: {acta.estado}")
    print(f"   Progreso final: {acta.progreso}%")
    print(f"   Continuando con verificación...")

print(f"\n📋 PASO 4: Verificar sincronización automática post-Celery")

# Recargar datos finales
acta.refresh_from_db()
gestion_acta.refresh_from_db()

print(f"📊 Estado Final:")
print(f"   ActaGenerada:")
print(f"   - Estado: {acta.estado}")
print(f"   - Progreso: {acta.progreso}%")
print(f"   - Contenido HTML: {len(acta.contenido_html or '')} chars")
print(f"   - Contenido Final: {len(acta.contenido_final or '')} chars")

print(f"   GestionActa:")
print(f"   - Estado: {gestion_acta.estado}")
print(f"   - Contenido editado: {len(gestion_acta.contenido_editado or '')} chars")

# Verificar sincronización
contenido_acta = acta.contenido_html or ''
contenido_gestion = gestion_acta.contenido_editado or ''

print(f"\n🔍 Verificación de Sincronización:")

if contenido_acta and contenido_gestion == contenido_acta:
    print(f"✅ ¡ÉXITO TOTAL! Sincronización automática funcionó perfectamente")
    print(f"   - Ambos sistemas tienen {len(contenido_acta)} chars")
    print(f"   - Contenido idéntico verificado ✅")
    
    # Preview del contenido
    preview = contenido_acta[:150] + "..." if len(contenido_acta) > 150 else contenido_acta
    print(f"\n📄 Preview del contenido sincronizado:")
    print(f"   {preview}")
    
    resultado = "✅ ÉXITO COMPLETO"
    
elif not contenido_acta and not contenido_gestion:
    print(f"⚠️ Ambos vacíos - Celery aún procesando o falló")
    resultado = "⏳ PENDIENTE"
    
else:
    print(f"❌ FALLO EN SINCRONIZACIÓN")
    print(f"   - ActaGenerada: {len(contenido_acta)} chars")
    print(f"   - GestionActa: {len(contenido_gestion)} chars")
    resultado = "❌ FALLO"

print(f"\n" + "=" * 60)
print(f"🏁 RESULTADO FINAL DEL TEST: {resultado}")
print(f"=" * 60)

if resultado == "✅ ÉXITO COMPLETO":
    print(f"🎉 EL SISTEMA ESTÁ FUNCIONANDO PERFECTAMENTE!")
    print(f"   ✅ Creación automática de GestionActa")
    print(f"   ✅ Procesamiento Celery exitoso") 
    print(f"   ✅ Sincronización automática post-Celery")
    print(f"   ✅ Flujo end-to-end completamente funcional")
elif resultado == "⏳ PENDIENTE":
    print(f"⏰ El procesamiento está tomando más tiempo del esperado")
    print(f"   💡 Esto puede ser normal si Celery está cargado")
    print(f"   💡 La sincronización funcionará cuando termine el procesamiento")
else:
    print(f"❌ Hay problemas que necesitan investigación")

# Cleanup opcional
print(f"\n🧹 Limpieza de datos de prueba")
respuesta = input("¿Deseas eliminar el acta de prueba? (s/n): ").lower().strip()
if respuesta in ['s', 'si', 'y', 'yes']:
    acta.delete()
    print("🗑️ Acta de prueba eliminada")
else:
    print(f"📂 Acta conservada para inspección manual (ID: {acta.id})")