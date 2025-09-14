#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def mostrar_eventos_actuales():
    """Mostrar los eventos actuales del sistema sin crear nuevos"""
    print("� Mostrando eventos actuales del sistema...")
    
    from apps.auditoria.views import obtener_ultimos_eventos_sistema
    from apps.auditoria.context_processors import estadisticas_resumen_context
    from django.test import RequestFactory
    from django.contrib.auth.models import User
    
    # Crear un request mock
    factory = RequestFactory()
    request = factory.get('/')
    try:
        user = User.objects.get(username='superadmin')
        request.user = user
    except User.DoesNotExist:
        print("❌ Usuario superadmin no encontrado")
        return
    
    # Obtener eventos
    eventos = obtener_ultimos_eventos_sistema(10)
    print(f"\n✅ Se encontraron {len(eventos)} eventos:")
    
    for i, evento in enumerate(eventos, 1):
        print(f"   {i}. [{evento['tipo'].upper()}] {evento['titulo']}")
        print(f"      {evento['descripcion']}")
        print(f"      {evento['tiempo_hace']}")
        print()
    
    # Obtener estadísticas
    context_stats = estadisticas_resumen_context(request)
    stats = context_stats.get('stats_sistema', {})
    print("📈 Estadísticas del sistema:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n🌐 Enlaces para verificar:")
    print("   - Portal Ciudadano: http://localhost:8000/portal-ciudadano/")
    print("   - Eventos en Tiempo Real: http://localhost:8000/auditoria/eventos/")
    print("   - Dashboard de Auditoría: http://localhost:8000/auditoria/")

if __name__ == "__main__":
    mostrar_eventos_actuales()