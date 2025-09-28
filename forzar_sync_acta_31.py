#!/usr/bin/env python
"""
Forzar sincronización del acta problemática "Para Procesar 3"
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.generador_actas.models import ActaGenerada
from gestion_actas.models import GestionActa

print("🔧 FORZANDO SINCRONIZACIÓN DE ACTA DESINCRONIZADA")
print("=" * 60)

# Buscar acta ID 31 que está desincronizada
try:
    acta = ActaGenerada.objects.get(id=31)
    print(f'📋 ActaGenerada ID 31: "{acta.titulo}"')
    print(f'   - Contenido HTML: {len(acta.contenido_html or "")} chars')
    print(f'   - Estado: {acta.estado}')
    
    # Verificar GestionActa actual
    try:
        gestion = GestionActa.objects.get(acta_generada=acta)
        print(f'📋 GestionActa asociada ID {gestion.id}:')
        print(f'   - Contenido editado ANTES: {len(gestion.contenido_editado or "")} chars')
    except GestionActa.DoesNotExist:
        print('❌ No tiene GestionActa (esto es raro)')
        exit(1)
    
    print(f'\n🚀 Forzando save() para disparar señal de UPDATE...')
    
    # FORZAR SAVE - Esto debe disparar la señal post_save con created=False
    acta.save()
    
    print(f'✅ save() ejecutado')
    
    # Verificar resultado
    gestion.refresh_from_db()
    print(f'\n📊 Resultado después de save():')
    print(f'   - ActaGenerada: {len(acta.contenido_html or "")} chars')
    print(f'   - GestionActa: {len(gestion.contenido_editado or "")} chars')
    
    if gestion.contenido_editado == acta.contenido_html:
        print(f'🎉 ¡ÉXITO! Sincronización automática funcionó correctamente')
        print(f'   - Ambos sistemas tienen {len(acta.contenido_html)} chars')
    else:
        print(f'❌ FALLO: Aún desincronizado')
        print(f'   - ActaGenerada: {len(acta.contenido_html or "")} chars')
        print(f'   - GestionActa: {len(gestion.contenido_editado or "")} chars')
        
except ActaGenerada.DoesNotExist:
    print('❌ No se encontró ActaGenerada ID 31')
except Exception as e:
    print(f'❌ Error: {str(e)}')