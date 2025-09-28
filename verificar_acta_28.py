#!/usr/bin/env python3

# Script para verificar la sincronización del acta 28
from gestion_actas.models import GestionActa
from apps.generador_actas.models import ActaGenerada

print("=== VERIFICACIÓN ACTA 28 ===")

# Verificar ActaGenerada
try:
    acta_gen = ActaGenerada.objects.get(id=28)
    print(f"ActaGenerada {acta_gen.id}: {acta_gen.titulo}")
    print(f"Estado: {acta_gen.estado}")
    print(f"Contenido HTML length: {len(acta_gen.contenido_html) if acta_gen.contenido_html else 0}")
except ActaGenerada.DoesNotExist:
    print("No existe ActaGenerada con ID 28")
    exit()

# Verificar GestionActa correspondiente
try:
    gestion = GestionActa.objects.get(acta_generada=acta_gen)
    print(f"\nGestionActa encontrada - ID: {gestion.id}")
    print(f"Título: {gestion.titulo}")
    print(f"Contenido editado length: {len(gestion.contenido_editado) if gestion.contenido_editado else 0}")
    
    if gestion.contenido_editado:
        print("\nPrimeros 200 chars del contenido:")
        print(gestion.contenido_editado[:200])
    else:
        print("\n⚠️ No hay contenido en GestionActa")
        
except GestionActa.DoesNotExist:
    print("\n❌ No existe GestionActa para esta ActaGenerada")

# Verificar todos los GestionActa
print(f"\nTotal GestionActas: {GestionActa.objects.count()}")
print("Últimas 5 GestionActas:")
for g in GestionActa.objects.order_by('-id')[:5]:
    acta_id = g.acta_generada.id if g.acta_generada else 'None'
    print(f"  ID {g.id}: {g.titulo} (ActaGenerada: {acta_id})")