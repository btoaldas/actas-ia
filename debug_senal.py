#!/usr/bin/env python3

# Script para debuggear la señal de sincronización
from apps.generador_actas.models import ActaGenerada
from gestion_actas.models import GestionActa
from django.utils import timezone
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

print("=== DEBUG SEÑAL DE SINCRONIZACIÓN ===")

# Obtener el acta problema
acta = ActaGenerada.objects.get(id=29)  # "Para Procesar 2"
print(f"ActaGenerada ID {acta.id}: {acta.titulo}")
print(f"contenido_html length: {len(acta.contenido_html) if acta.contenido_html else 0}")
print(f"contenido_final length: {len(acta.contenido_final) if acta.contenido_final else 0}")
print(f"contenido_borrador length: {len(acta.contenido_borrador) if acta.contenido_borrador else 0}")

# Simular la lógica de la señal manualmente
contenido_a_usar = acta.contenido_html or acta.contenido_final or acta.contenido_borrador or ''
print(f"\n--- LÓGICA DE SEÑAL ---")
print(f"Contenido a usar: {len(contenido_a_usar)} chars")
if contenido_a_usar:
    print(f"Primeros 100 chars: {contenido_a_usar[:100]}")
else:
    print("❌ NO HAY CONTENIDO PARA TRANSFERIR")

# Verificar GestionActa actual
try:
    gestion = GestionActa.objects.get(acta_generada=acta)
    print(f"\n--- GESTIONACTA ACTUAL ---")
    print(f"ID: {gestion.pk}")
    print(f"Contenido actual: {len(gestion.contenido_editado) if gestion.contenido_editado else 0} chars")
    print(f"Backup actual: {len(gestion.contenido_original_backup) if gestion.contenido_original_backup else 0} chars")
    
    # Simular actualización manual
    if contenido_a_usar and len(contenido_a_usar) > 0:
        print(f"\n--- SIMULANDO ACTUALIZACIÓN MANUAL ---")
        gestion.contenido_editado = contenido_a_usar
        if not gestion.contenido_original_backup:
            gestion.contenido_original_backup = contenido_a_usar
        gestion.fecha_ultima_edicion = timezone.now()
        
        cambios = gestion.cambios_realizados or {}
        cambios['debug_manual_fix'] = timezone.now().isoformat()
        cambios['contenido_corregido_manualmente'] = True
        gestion.cambios_realizados = cambios
        
        gestion.save()
        
        print(f"✅ ACTUALIZACIÓN MANUAL COMPLETADA")
        print(f"   Nuevo contenido: {len(gestion.contenido_editado)} chars")
    else:
        print("❌ NO SE PUEDE ACTUALIZAR - SIN CONTENIDO")

except GestionActa.DoesNotExist:
    print("❌ NO EXISTE GESTIONACTA")

# Verificar el resultado
print(f"\n--- VERIFICACIÓN FINAL ---")
gestion_final = GestionActa.objects.get(acta_generada=acta)
print(f"Contenido final: {len(gestion_final.contenido_editado) if gestion_final.contenido_editado else 0} chars")