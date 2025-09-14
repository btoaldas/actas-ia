#!/usr/bin/env python
"""
Script para probar la renderización del navbar con las nuevas actas
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.template.loader import render_to_string
from django.contrib.auth.models import User
from apps.auditoria.context_processors import ultimas_actas_publicadas_context

class MockRequest:
    def __init__(self, user):
        self.user = user

def main():
    print("🧪 Probando renderización del navbar con actas...")
    
    # Obtener usuario
    try:
        user = User.objects.get(username='superadmin')
    except User.DoesNotExist:
        user = User.objects.filter(is_superuser=True).first()
    
    if not user:
        print("❌ No se encontró usuario")
        return
    
    request = MockRequest(user)
    
    # Obtener datos del context processor
    context_data = ultimas_actas_publicadas_context(request)
    actas = context_data.get('ultimas_actas_publicadas', [])
    
    print(f"✅ Context processor cargado: {len(actas)} actas")
    
    # Simular el template rendering
    template_context = {
        'ultimas_actas_publicadas': actas,
        'request': request
    }
    
    # Mostrar cómo se vería en el navbar
    print("\n📱 Vista previa del navbar:")
    print(f"Badge count: {len(actas)}")
    print(f"Header: {len(actas)} Acta{'s' if len(actas) != 1 else ''} Reciente{'s' if len(actas) != 1 else ''}")
    
    if actas:
        print("\n📄 Items del dropdown:")
        for i, acta in enumerate(actas, 1):
            print(f"  {i}. [{acta['numero_acta']}] {acta['titulo'][:40]}...")
            print(f"     🏛️  {acta['tipo_sesion']}")
            print(f"     👤 {acta['secretario_nombre']}")
            print(f"     ⏰ {acta['tiempo_hace']}")
            print(f"     🔗 {acta['url']}")
            print()
    
    print("✅ El navbar debería mostrar estas actas en lugar de las notificaciones vacías")
    print("🔗 Al hacer clic en cualquier acta, llevará directamente a su URL de detalle")
    print("🌐 El botón 'Ver Todas las Actas Públicas' lleva al portal ciudadano")

if __name__ == '__main__':
    main()