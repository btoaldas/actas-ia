#!/usr/bin/env python
"""
Prueba específica para los enlaces de autenticación en sidebar colapsado
"""

def main():
    print("🎯 PRUEBA ESPECÍFICA - Enlaces de Autenticación")
    print("=" * 55)
    
    print("\n📋 CAMBIOS REALIZADOS:")
    print("✅ Agregada clase 'sidebar-text' a los textos de los botones")
    print("✅ CSS creado para ocultar .sidebar-text cuando .sidebar-collapse está activo")
    
    print("\n🔍 ELEMENTOS MODIFICADOS:")
    print("- 'Cerrar Sesión' → <span class='sidebar-text'>Cerrar Sesión</span>")
    print("- 'Cambiar Contraseña' → <span class='sidebar-text'>Cambiar Contraseña</span>")
    print("- 'Iniciar Sesión' → <span class='sidebar-text'>Iniciar Sesión</span>")
    print("- 'Registrarse' → <span class='sidebar-text'>Registrarse</span>")
    
    print("\n🎯 RESULTADO ESPERADO:")
    print("Cuando el sidebar esté colapsado:")
    print("  ✅ Los iconos de los botones permanecen visibles")
    print("  ✅ Los textos de los botones desaparecen")
    print("  ✅ Los botones se centran automáticamente")
    
    print("\n🧪 PARA PROBAR:")
    print("1. Ve a: http://localhost:8000/")
    print("2. Haz clic en el botón hamburguesa (☰)")
    print("3. Observa los botones de autenticación en el sidebar")
    print("4. Deberías ver solo los iconos (sin texto)")
    
    print("\n💻 CSS APLICADO:")
    print(".sidebar-collapse .sidebar-text {")
    print("    display: none !important;")
    print("}")
    print("")
    print(".sidebar-collapse .user-actions .btn {")
    print("    text-align: center !important;")
    print("    justify-content: center !important;")
    print("}")
    
    print("\n🚀 SIMPLE Y ESPECÍFICO - LISTO PARA USAR")

if __name__ == '__main__':
    main()