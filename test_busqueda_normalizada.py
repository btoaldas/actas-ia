#!/usr/bin/env python
"""
Script de prueba para verificar la funcionalidad de búsqueda normalizada
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from helpers.util import normalizar_busqueda

def test_normalizacion():
    """Pruebas de normalización de texto"""
    print("🧪 Pruebas de normalización de búsqueda:")
    print("=" * 50)
    
    # Casos de prueba
    casos = [
        ("Sesión", "sesion"),
        ("SESIÓN", "sesion"),
        ("administración", "administracion"),
        ("Educación", "educacion"),
        ("INFORMACIÓN", "informacion"),
        ("Participación", "participacion"),
        ("reunión", "reunion"),
        ("decisión", "decision"),
        ("comisión", "comision"),
        ("situación", "situacion"),
        ("Niño", "nino"),
        ("año", "ano"),
        ("Años", "anos"),
        ("Señor", "senor"),
        ("niños", "ninos"),
    ]
    
    todos_exitosos = True
    
    for original, esperado in casos:
        resultado = normalizar_busqueda(original)
        exito = resultado == esperado
        emoji = "✅" if exito else "❌"
        
        print(f"{emoji} '{original}' → '{resultado}' (esperado: '{esperado}')")
        
        if not exito:
            todos_exitosos = False
    
    print("=" * 50)
    
    if todos_exitosos:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n📝 Ejemplos de búsquedas que ahora funcionarán:")
        print("   - 'sesion' encontrará 'Sesión'")
        print("   - 'SESION' encontrará 'Sesión'") 
        print("   - 'administracion' encontrará 'Administración'")
        print("   - 'educacion' encontrará 'Educación'")
        print("   - 'informacion' encontrará 'Información'")
    else:
        print("❌ Algunas pruebas fallaron")
    
    return todos_exitosos

if __name__ == "__main__":
    test_normalizacion()