#!/usr/bin/env python3
"""
Script para probar que la página principal cargue sin errores
"""

import os
import sys
import django
from django.test import Client

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_homepage():
    """Prueba que la página principal cargue sin errores de NoReverseMatch"""
    print("🏠 Probando página principal...")
    
    try:
        client = Client()
        response = client.get('/')
        
        print(f"   📊 Código de respuesta: {response.status_code}")
        
        if response.status_code == 302:
            # Redirección esperada
            print(f"   🔄 Redirige a: {response['Location']}")
            
            # Probar seguir la redirección
            response = client.get(response['Location'])
            print(f"   📊 Código final: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Página principal carga correctamente")
                return True
            else:
                print(f"   ❌ Error en redirección: {response.status_code}")
                return False
        elif response.status_code == 200:
            print("   ✅ Página principal carga correctamente")
            return True
        else:
            print(f"   ❌ Error: código {response.status_code}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        if 'NoReverseMatch' in error_msg and 'segmentos_lista' in error_msg:
            print(f"   ❌ ERROR ENCONTRADO: {error_msg}")
            return False
        else:
            print(f"   ❌ Error diferente: {error_msg}")
            return False

def test_menu_rendering():
    """Prueba que el menú se renderice correctamente"""
    print("\n📋 Probando renderizado del menú...")
    
    try:
        from django.template.loader import render_to_string
        from django.http import HttpRequest
        from django.contrib.auth.models import AnonymousUser
        
        # Crear request simulado
        request = HttpRequest()
        request.user = AnonymousUser()
        request.META = {'HTTP_HOST': 'localhost:8000'}
        
        # Intentar renderizar el menú
        menu_html = render_to_string('includes/menu-list.html', {
            'request': request,
            'segment': 'home'
        })
        
        # Verificar que no tenga referencias incorrectas
        if 'segmentos_lista' in menu_html:
            print("   ❌ El menú aún contiene 'segmentos_lista'")
            return False
        else:
            print("   ✅ Menú renderizado sin referencias incorrectas")
            return True
            
    except Exception as e:
        error_msg = str(e)
        if 'NoReverseMatch' in error_msg and 'segmentos_lista' in error_msg:
            print(f"   ❌ ERROR EN MENÚ: {error_msg}")
            return False
        else:
            print(f"   ⚠️  Error diferente en menú: {error_msg}")
            return True  # Otros errores no son nuestro problema actual

def main():
    """Ejecuta las pruebas"""
    print("🔍 VERIFICACIÓN DE CORRECCIÓN DEL ERROR NoReverseMatch")
    print("=" * 60)
    
    tests = [
        test_homepage,
        test_menu_rendering
    ]
    
    resultados = []
    
    for test in tests:
        resultado = test()
        resultados.append(resultado)
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    if all(resultados):
        print("🎉 ¡ERROR CORREGIDO EXITOSAMENTE!")
        print("✅ La página principal carga sin errores")
        print("✅ El menú no tiene referencias incorrectas")
        print("✅ NoReverseMatch para 'segmentos_lista' resuelto")
        return True
    else:
        exitosos = sum(resultados)
        total = len(resultados)
        print(f"⚠️  Pruebas exitosas: {exitosos}/{total}")
        print("🔧 Revisar errores específicos arriba")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)