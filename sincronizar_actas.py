#!/usr/bin/env python3

# Script para sincronizar todas las ActaGenerada con GestionActa
from apps.generador_actas.models import ActaGenerada
from gestion_actas.models import GestionActa
from django.utils import timezone

print("=== SINCRONIZACIÓN MASIVA DE ACTAS ===")

# Obtener todas las ActaGenerada
actas_generadas = ActaGenerada.objects.all()
print(f"Total ActaGeneradas: {actas_generadas.count()}")

sincronizadas = 0
creadas = 0
sin_contenido = 0

for acta_gen in actas_generadas:
    try:
        # Buscar GestionActa correspondiente
        gestion_acta = GestionActa.objects.get(acta_generada=acta_gen)
        
        # Obtener contenido de ActaGenerada
        contenido_nuevo = acta_gen.contenido_html or acta_gen.contenido_final or acta_gen.contenido_borrador or ''
        
        if not contenido_nuevo:
            print(f"⚠️ ActaGenerada {acta_gen.id} sin contenido")
            sin_contenido += 1
            continue
            
        # Si GestionActa no tiene contenido o es diferente
        if not gestion_acta.contenido_editado or len(gestion_acta.contenido_editado.strip()) == 0:
            # Actualizar contenido
            gestion_acta.contenido_editado = contenido_nuevo
            if not gestion_acta.contenido_original_backup:
                gestion_acta.contenido_original_backup = contenido_nuevo
            gestion_acta.fecha_ultima_edicion = timezone.now()
            
            # Actualizar cambios realizados
            cambios = gestion_acta.cambios_realizados or {}
            cambios['sincronizacion_masiva'] = timezone.now().isoformat()
            cambios['contenido_sincronizado'] = True
            gestion_acta.cambios_realizados = cambios
            
            gestion_acta.save()
            
            print(f"🔄 Sincronizada ActaGenerada {acta_gen.id} -> GestionActa {gestion_acta.id}")
            print(f"   Título: {acta_gen.titulo}")
            print(f"   Contenido: {len(contenido_nuevo)} caracteres")
            sincronizadas += 1
        else:
            print(f"✅ ActaGenerada {acta_gen.id} ya sincronizada")
            
    except GestionActa.DoesNotExist:
        print(f"📝 ActaGenerada {acta_gen.id} sin GestionActa - disparando save()")
        # Disparar save() para crear GestionActa automáticamente
        acta_gen.save()
        creadas += 1

print(f"\n=== RESUMEN ===")
print(f"✅ Sincronizadas: {sincronizadas}")
print(f"📝 Nuevas creadas: {creadas}")
print(f"⚠️ Sin contenido: {sin_contenido}")
print(f"🎉 Proceso completado")