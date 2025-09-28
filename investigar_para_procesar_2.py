#!/usr/bin/env python3

# Script para investigar el acta "Para Procesar 2"
from apps.generador_actas.models import ActaGenerada
from gestion_actas.models import GestionActa

print("=== INVESTIGACIÓN ACTA 'PARA PROCESAR 2' ===")

# Buscar actas con "Para Procesar 2"
actas = ActaGenerada.objects.filter(titulo__contains='Para Procesar').order_by('-id')
print(f"Actas con 'Para Procesar': {actas.count()}")

for acta in actas[:5]:
    print(f"\n--- ActaGenerada ID {acta.id} ---")
    print(f"Título: {acta.titulo}")
    print(f"Estado: {acta.estado}")
    print(f"Fecha creación: {acta.fecha_creacion}")
    print(f"Contenido HTML: {len(acta.contenido_html) if acta.contenido_html else 0} chars")
    
    if acta.contenido_html:
        print(f"Primeros 100 chars: {acta.contenido_html[:100]}")
    
    # Verificar si existe GestionActa correspondiente
    try:
        gestion = GestionActa.objects.get(acta_generada=acta)
        print(f"✅ GestionActa ID {gestion.id} encontrada")
        print(f"   Contenido editado: {len(gestion.contenido_editado) if gestion.contenido_editado else 0} chars")
        
        if gestion.contenido_editado:
            print(f"   Primeros 100 chars: {gestion.contenido_editado[:100]}")
        else:
            print("   ❌ SIN CONTENIDO EN GESTION")
            
    except GestionActa.DoesNotExist:
        print(f"❌ NO EXISTE GestionActa para esta ActaGenerada")

# Verificar las últimas GestionActa creadas
print(f"\n=== ÚLTIMAS 5 GESTIONACTA ===")
gestiones = GestionActa.objects.order_by('-id')[:5]
for g in gestiones:
    acta_id = g.acta_generada.id if g.acta_generada else 'None'
    print(f"GestionActa ID {g.id}: {g.titulo} (ActaGenerada: {acta_id}) - Contenido: {len(g.contenido_editado) if g.contenido_editado else 0} chars")