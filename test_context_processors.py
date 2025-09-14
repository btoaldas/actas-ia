#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from apps.auditoria.context_processors import eventos_sistema_context, estadisticas_resumen_context

# Crear un request mock con usuario autenticado
factory = RequestFactory()
request = factory.get('/')

# Obtener o crear un usuario
try:
    user = User.objects.get(username='superadmin')
except User.DoesNotExist:
    user = User.objects.create_user('testuser', 'test@test.com', 'testpass')

request.user = user

print("=== Probando Context Processors ===")

# Probar eventos del sistema
print("\n1. Eventos del sistema:")
try:
    context_eventos = eventos_sistema_context(request)
    eventos = context_eventos.get('ultimos_eventos_sistema', [])
    print(f"   ✅ {len(eventos)} eventos encontrados")
    for i, evento in enumerate(eventos[:3]):
        print(f"   {i+1}. {evento['tipo']}: {evento['titulo']}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n2. Estadísticas del sistema:")
try:
    context_stats = estadisticas_resumen_context(request)
    stats = context_stats.get('stats_sistema', {})
    print(f"   ✅ Estadísticas obtenidas:")
    for key, value in stats.items():
        print(f"      {key}: {value}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n=== Fin de pruebas ===")