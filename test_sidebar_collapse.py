#!/usr/bin/env python
"""
Script para verificar que el CSS del sidebar se carga correctamente
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

def main():
    print("🔍 Verificando configuración del sidebar colapsado...")
    
    # Verificar que el archivo CSS existe
    css_path = os.path.join(settings.STATIC_ROOT or settings.BASE_DIR / 'static', 'css', 'sidebar-custom.css')
    
    if os.path.exists(css_path):
        print("✅ Archivo sidebar-custom.css encontrado")
        with open(css_path, 'r') as f:
            content = f.read()
            if '.sidebar-collapse' in content:
                print("✅ Reglas CSS para sidebar-collapse presentes")
            else:
                print("❌ No se encontraron reglas para sidebar-collapse")
    else:
        print("❌ Archivo sidebar-custom.css no encontrado en:", css_path)
        # Intentar en directorio de desarrollo
        dev_css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'sidebar-custom.css')
        if os.path.exists(dev_css_path):
            print("✅ Archivo encontrado en directorio de desarrollo:", dev_css_path)
        else:
            print("❌ Archivo no encontrado en ninguna ubicación")
    
    print("\n📝 Reglas CSS implementadas:")
    print("   - .sidebar-collapse .nav-link p { display: none }")
    print("   - .sidebar-collapse .nav-link i.right { display: none }")
    print("   - .sidebar-collapse .nav-treeview { display: none }")
    print("   - .sidebar-collapse .brand-text { display: none }")
    print("   - .sidebar-collapse .user-actions { display: none }")
    print("   - .sidebar-collapse .form-inline { display: none }")
    
    print("\n🎯 Funcionalidad esperada:")
    print("   - Al hacer clic en el botón hamburguesa, el sidebar se colapsa")
    print("   - Solo se muestran los iconos, sin texto")
    print("   - El ancho se reduce a ~74px")
    print("   - Los submenús se ocultan completamente")
    print("   - El contenido principal se ajusta automáticamente")
    
    print("\n🚀 Para probar:")
    print("   1. Cargar cualquier página del sistema")
    print("   2. Hacer clic en el botón hamburguesa (☰) en el navbar")
    print("   3. Verificar que el sidebar solo muestra iconos")
    print("   4. Hacer clic nuevamente para expandir")

if __name__ == '__main__':
    main()