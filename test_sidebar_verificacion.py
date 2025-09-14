#!/usr/bin/env python
"""
Información para verificar el sidebar colapsado en el navegador
"""

def main():
    print("🔧 GUÍA PARA VERIFICAR EL SIDEBAR COLAPSADO")
    print("=" * 60)
    
    print("\n📋 CÓMO PROBAR:")
    print("1. Abre el navegador y ve a: http://localhost:8000/")
    print("2. Abre las herramientas de desarrollador (F12)")
    print("3. Haz clic en el botón hamburguesa (☰) en el navbar superior")
    print("4. Observa los cambios en el sidebar")
    
    print("\n🎯 QUÉ DEBERÍAS VER:")
    print("✅ El sidebar se reduce a ~74px de ancho")
    print("✅ Solo se muestran los iconos de los menús")
    print("✅ Todo el texto desaparece")
    print("✅ Los submenús se ocultan")
    print("✅ El logo 'Actas IA' desaparece")
    print("✅ Los botones de usuario desaparecen")
    print("✅ La búsqueda desaparece")
    
    print("\n🔍 CLASES CSS A VERIFICAR:")
    print("En las herramientas de desarrollador, busca:")
    print("- <body> debe tener la clase 'sidebar-collapse'")
    print("- .main-sidebar debe tener width: 4.6rem")
    print("- .nav-link p debe tener display: none")
    print("- .brand-text debe tener display: none")
    
    print("\n🛠️ SI NO FUNCIONA:")
    print("1. Verifica que la clase 'sidebar-collapse' se agregue al <body>")
    print("2. Asegúrate que AdminLTE JavaScript esté cargado")
    print("3. Revisa la consola del navegador por errores JS")
    print("4. Confirma que sidebar-custom.css se carga después de adminlte.css")
    
    print("\n💡 PERSONALIZACIÓN ADICIONAL:")
    print("Si quieres cambiar el ancho colapsado, modifica en sidebar-custom.css:")
    print("   .sidebar-collapse .main-sidebar { width: TU_ANCHO !important; }")
    print("   .sidebar-collapse .content-wrapper { margin-left: TU_ANCHO !important; }")
    
    print("\n🚀 SISTEMA LISTO PARA USAR")

if __name__ == '__main__':
    main()