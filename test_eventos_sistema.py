#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from apps.auditoria.views import api_ultimos_eventos, obtener_ultimos_eventos_sistema
    print("✅ Vistas importadas correctamente")
    
    # Probar la función
    eventos = obtener_ultimos_eventos_sistema(3)
    print(f"✅ Función obtener_ultimos_eventos_sistema ejecutada: {len(eventos)} eventos")
    
    for evento in eventos:
        print(f"   - {evento['tipo']}: {evento['titulo']}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()