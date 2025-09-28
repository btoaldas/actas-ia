#!/usr/bin/env python3

# Script para probar la sincronización automática con nueva acta
from apps.generador_actas.models import ActaGenerada, PlantillaActa, ProveedorIA
from apps.transcripcion.models import Transcripcion
from django.contrib.auth.models import User
from django.utils import timezone
from gestion_actas.models import GestionActa
import time

print("=== PRUEBA DE SINCRONIZACIÓN AUTOMÁTICA ===")

# Obtener datos necesarios
user = User.objects.get(username='superadmin')
transcripcion = Transcripcion.objects.first()
plantilla = PlantillaActa.objects.first()
proveedor = ProveedorIA.objects.filter(activo=True).first()

print("Datos obtenidos correctamente")

# Crear ActaGenerada con contenido HTML inmediatamente
contenido_test = '''
<html>
<head><meta charset="UTF-8"></head>
<body>
<h1 style="text-align: center; font-weight: bold;">ACTA DE PRUEBA AUTOMÁTICA</h1>
<h2 style="text-align: center;">ACTA-TEST-AUTO-2025</h2>
<hr>
<h3 style="font-weight: bold;">CONTENIDO DE PRUEBA</h3>
<p>Esta es una prueba para verificar la sincronización automática entre el generador de actas y el sistema de gestión.</p>
<table border="1" style="width: 100%; border-collapse: collapse;">
<tr><th style="padding: 8px;">Dato</th><th style="padding: 8px;">Valor</th></tr>
<tr><td style="padding: 8px;">Estado</td><td style="padding: 8px;">Prueba Automática</td></tr>
<tr><td style="padding: 8px;">Sincronización</td><td style="padding: 8px;">Debe Funcionar</td></tr>
</table>
<h3 style="font-weight: bold;">VERIFICACIÓN</h3>
<p>Este contenido debe aparecer automáticamente en el sistema de gestión de actas sin intervención manual.</p>
</body>
</html>
'''.strip()

print(f"Contenido preparado: {len(contenido_test)} caracteres")

# Crear ActaGenerada
acta = ActaGenerada.objects.create(
    numero_acta='ACTA-TEST-AUTO-2025',
    titulo='Prueba Sincronización Automática',
    transcripcion=transcripcion,
    plantilla=plantilla,
    proveedor_ia=proveedor,
    fecha_sesion=timezone.now(),
    usuario_creacion=user,
    contenido_html=contenido_test,
    estado='finalizada'
)

print(f"✅ ActaGenerada creada: ID {acta.pk}")
print(f"   Título: {acta.titulo}")
print(f"   Contenido HTML: {len(acta.contenido_html)} chars")

# Esperar un momento para que se ejecute la señal
time.sleep(2)

# Verificar si se creó GestionActa automáticamente
try:
    gestion = GestionActa.objects.get(acta_generada=acta)
    print(f"✅ GestionActa creada automáticamente: ID {gestion.pk}")
    print(f"   Contenido: {len(gestion.contenido_editado) if gestion.contenido_editado else 0} chars")
    
    if gestion.contenido_editado and len(gestion.contenido_editado) > 0:
        print("🎉 ¡SINCRONIZACIÓN AUTOMÁTICA EXITOSA!")
        print(f"   Primeros 100 chars: {gestion.contenido_editado[:100]}")
        
        # Verificar coincidencia exacta
        if gestion.contenido_editado == acta.contenido_html:
            print("✅ Contenido coincide exactamente")
        else:
            print(f"⚠️ Contenido diferente - ActaGen: {len(acta.contenido_html)} vs Gestión: {len(gestion.contenido_editado)}")
    else:
        print("❌ SINCRONIZACIÓN FALLÓ - GestionActa sin contenido")
        
except GestionActa.DoesNotExist:
    print("❌ SINCRONIZACIÓN FALLÓ - No se creó GestionActa")

print("\n=== RESUMEN DE PRUEBA ===")
print("Verificar manualmente:")
print(f"- Ver acta: http://localhost:8000/gestion-actas/acta/{gestion.pk}/")
print(f"- Editar acta: http://localhost:8000/gestion-actas/acta/{gestion.pk}/editar/")