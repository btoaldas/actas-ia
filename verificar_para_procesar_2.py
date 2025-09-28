#!/usr/bin/env python
"""
Verificar estado actual del acta problemática "Para Procesar 2"
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

# Buscar acta 'Para Procesar 2' que tenía el problema original
acta = ActaGenerada.objects.filter(titulo__icontains='Para Procesar 2').first()
if acta:
    print(f'✅ ActaGenerada encontrada:')
    print(f'   - ID: {acta.id}')
    print(f'   - Título: {acta.titulo}')
    print(f'   - Estado: {acta.estado}')
    print(f'   - Contenido HTML: {len(acta.contenido_html or "")} chars')
    print(f'   - Contenido Final: {len(acta.contenido_final or "")} chars')
    
    # Verificar GestionActa asociada
    try:
        gestion = GestionActa.objects.get(acta_generada=acta)
        print(f'\n✅ GestionActa asociada:')
        print(f'   - ID: {gestion.id}')
        print(f'   - Estado: {gestion.estado}')
        print(f'   - Contenido editado: {len(gestion.contenido_editado or "")} chars')
        
        # Verificar sincronización
        contenido_acta = acta.contenido_html or ""
        contenido_gestion = gestion.contenido_editado or ""
        
        if contenido_acta and contenido_gestion == contenido_acta:
            print(f'   ✅ SINCRONIZADO correctamente - Ambos tienen {len(contenido_acta)} chars')
        elif not contenido_acta and not contenido_gestion:
            print(f'   ⚠️ Ambos vacíos - esperando procesamiento')
        elif contenido_acta and not contenido_gestion:
            print(f'   ❌ DESINCRONIZADO - ActaGenerada: {len(contenido_acta)} chars, GestionActa: 0 chars')
        elif contenido_acta and len(contenido_gestion) != len(contenido_acta):
            print(f'   ❌ DESINCRONIZADO - ActaGenerada: {len(contenido_acta)} chars, GestionActa: {len(contenido_gestion)} chars')
        else:
            print(f'   ✅ SINCRONIZADO - {len(contenido_gestion)} chars')
            
    except GestionActa.DoesNotExist:
        print('❌ No tiene GestionActa asociada')
else:
    print('❌ No se encontró el acta "Para Procesar 2"')

print('\n' + '='*50)

# Listar todas las actas recientes para verificar estado general
print('\n📊 Estado de actas recientes:')
actas_recientes = ActaGenerada.objects.order_by('-id')[:5]

for acta in actas_recientes:
    try:
        gestion = GestionActa.objects.get(acta_generada=acta)
        contenido_acta = len(acta.contenido_html or "")
        contenido_gestion = len(gestion.contenido_editado or "")
        estado_sync = "✅" if contenido_acta == contenido_gestion or (contenido_acta > 0 and contenido_gestion > 0) else "❌"
        
        print(f'   {estado_sync} ID {acta.id}: "{acta.titulo[:30]}..." | ActaGen: {contenido_acta} chars | GestionActa: {contenido_gestion} chars')
    except GestionActa.DoesNotExist:
        print(f'   ❌ ID {acta.id}: "{acta.titulo[:30]}..." | Sin GestionActa')