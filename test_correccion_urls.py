#!/usr/bin/env python3
"""
Script para verificar que el error de NoReverseMatch esté corregido
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_urls_resolution():
    """Verifica que todas las URLs de segmentos se puedan resolver"""
    print("🔗 Probando resolución de URLs...")
    
    try:
        from django.urls import reverse
        
        urls_test = [
            ('generador_actas:segmentos_dashboard', 'Dashboard de Segmentos'),
            ('generador_actas:lista_segmentos', 'Lista de Segmentos'),
            ('generador_actas:crear_segmento', 'Crear Segmento'),
            ('generador_actas:asistente_variables', 'Asistente de Variables')
        ]
        
        resultados = []
        
        for url_name, descripcion in urls_test:
            try:
                url_path = reverse(url_name)
                print(f"   ✅ {descripcion}: {url_name} → {url_path}")
                resultados.append(True)
            except Exception as e:
                print(f"   ❌ {descripcion}: {url_name} → Error: {e}")
                resultados.append(False)
        
        return all(resultados)
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def test_template_render():
    """Verifica que los templates se puedan renderizar sin error de URLs"""
    print("\n🎨 Probando renderizado de templates...")
    
    try:
        from django.template import Template, Context
        from django.template.loader import get_template
        
        # Test template que usa URLs de segmentos
        template_content = """
        {% load url %}
        <a href="{% url 'generador_actas:segmentos_dashboard' %}">Dashboard</a>
        <a href="{% url 'generador_actas:lista_segmentos' %}">Lista</a>
        <a href="{% url 'generador_actas:crear_segmento' %}">Crear</a>
        <a href="{% url 'generador_actas:asistente_variables' %}">Asistente</a>
        """
        
        template = Template(template_content)
        context = Context({})
        rendered = template.render(context)
        
        # Verificar que contiene las URLs esperadas
        if '/segmentos/' in rendered and '/lista/' in rendered:
            print("   ✅ Template renderizado correctamente con URLs")
            return True
        else:
            print("   ❌ Template renderizado pero URLs incorrectas")
            return False
            
    except Exception as e:
        print(f"   ❌ Error renderizando template: {e}")
        return False

def test_menu_template():
    """Verifica específicamente el menu-list.html"""
    print("\n📋 Probando template de menú...")
    
    try:
        from django.template.loader import get_template
        from django.template import Context
        from django.http import HttpRequest
        from django.contrib.auth.models import AnonymousUser
        
        # Simular request
        request = HttpRequest()
        request.user = AnonymousUser()
        request.META = {}
        
        # Cargar template
        template = get_template('includes/menu-list.html')
        context = {
            'request': request,
            'segment': 'generador-actas'
        }
        
        rendered = template.render(context)
        
        # Verificar que no tenga referencias incorrectas
        if 'segmentos_lista' in rendered:
            print("   ❌ Aún hay referencias a 'segmentos_lista'")
            return False
        elif 'segmentos_dashboard' in rendered or 'lista_segmentos' in rendered:
            print("   ✅ Menú usa URLs correctas")
            return True
        else:
            print("   ⚠️  No se encontraron URLs de segmentos en el menú")
            return True
            
    except Exception as e:
        print(f"   ❌ Error con template de menú: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones"""
    print("🔍 VERIFICACIÓN DE CORRECCIÓN DE URLs")
    print("=" * 50)
    
    tests = [
        test_urls_resolution,
        test_template_render,
        test_menu_template
    ]
    
    resultados = []
    
    for test in tests:
        resultado = test()
        resultados.append(resultado)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    print("=" * 50)
    
    exitosos = sum(resultados)
    total = len(resultados)
    
    print(f"✅ Pruebas exitosas: {exitosos}/{total}")
    
    if all(resultados):
        print("\n🎉 ¡ERROR CORREGIDO EXITOSAMENTE!")
        print("✅ Todas las URLs de segmentos funcionan correctamente")
        print("✅ Los templates se renderizan sin errores")
        print("✅ El menú de navegación está corregido")
        return True
    else:
        print(f"\n⚠️  Aún hay {total - exitosos} problemas por resolver")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)