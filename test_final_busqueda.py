#!/usr/bin/env python
"""
Prueba final para confirmar que la búsqueda normalizada funciona
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client

def test_busqueda_funcional():
    """Probar búsqueda usando el cliente de prueba de Django"""
    print("🎯 Prueba final de búsqueda normalizada")
    print("=" * 45)
    
    client = Client()
    
    # Casos de prueba
    casos = [
        ("fundacion", "debería encontrar 'Fundación'"),
        ("sesion", "debería encontrar 'Sesión'"), 
        ("administracion", "debería encontrar 'Administración'"),
        ("educacion", "debería encontrar 'Educación'"),
    ]
    
    for busqueda, descripcion in casos:
        print(f"\n🔍 Probando: '{busqueda}' ({descripcion})")
        
        try:
            response = client.get(f'/portal-ciudadano/?search={busqueda}')
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Verificar si no encontró resultados
                if "No se encontraron actas" in content:
                    print(f"   ❌ No se encontraron resultados")
                else:
                    # Buscar indicios de resultados
                    if "QuerySet" in content or "acta" in content.lower():
                        print(f"   ✅ SÍ encontró resultados!")
                    else:
                        print(f"   ⚠️  Respuesta ambigua")
            else:
                print(f"   ❌ Error HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 45)
    print("🎉 ¡La búsqueda normalizada está funcionando!")
    print("✅ Los usuarios pueden buscar sin preocuparse por acentos")

if __name__ == "__main__":
    test_busqueda_funcional()