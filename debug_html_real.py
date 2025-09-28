#!/usr/bin/env python
"""
DEBUG COMPLETO DEL HTML REAL - Extraer y analizar formulario
Vamos a ver qué realmente tiene el HTML generado
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
import re

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

def main():
    print("🔍 DEBUGGEANDO HTML REAL DEL FORMULARIO...")
    
    client = Client()
    User = get_user_model()
    
    # Login como superadmin
    login_success = client.login(username='superadmin', password='AdminPuyo2025!')
    print(f"✅ Login: {login_success}")
    
    # 1. EXTRAER HTML COMPLETO
    print("\n📄 1. EXTRAYENDO HTML COMPLETO...")
    response = client.get('/generador-actas/segmentos/crear/')
    print(f"Status GET: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ ERROR: No se pudo cargar la página. Status: {response.status_code}")
        return
    
    html_content = response.content.decode()
    
    # 2. BUSCAR FORMULARIO
    print("\n🔍 2. BUSCANDO ETIQUETAS <FORM>...")
    form_matches = re.findall(r'<form[^>]*>', html_content, re.IGNORECASE)
    print(f"Formas encontradas: {len(form_matches)}")
    for i, form in enumerate(form_matches, 1):
        print(f"  Form {i}: {form[:100]}...")
    
    # 3. BUSCAR CSRF TOKEN
    print("\n🔒 3. VERIFICANDO CSRF TOKEN...")
    csrf_matches = re.findall(r'name=["\']csrfmiddlewaretoken["\'][^>]*value=["\']([^"\']*)["\']', html_content)
    if csrf_matches:
        print(f"✅ CSRF token encontrado: {csrf_matches[0][:20]}...")
    else:
        print("❌ NO SE ENCONTRÓ CSRF TOKEN")
    
    # 4. BUSCAR CAMPOS ESPECÍFICOS
    print("\n📋 4. VERIFICANDO CAMPOS ESPECÍFICOS...")
    campos_criticos = [
        'codigo', 'nombre', 'tipo', 'categoria', 'descripcion',
        'contenido_estatico', 'prompt_ia', 'proveedor_ia',
        'formato_salida', 'orden_defecto', 'tiempo_limite_ia', 
        'reintentos_ia', 'activo', 'reutilizable'
    ]
    
    campos_encontrados = {}
    for campo in campos_criticos:
        # Buscar input, select, textarea con ese name
        patterns = [
            rf'<input[^>]*name=["\']({campo})["\'][^>]*>',
            rf'<select[^>]*name=["\']({campo})["\'][^>]*>',
            rf'<textarea[^>]*name=["\']({campo})["\'][^>]*>'
        ]
        
        found = False
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                found = True
                # Extraer el elemento completo
                full_element = re.search(rf'<(?:input|select|textarea)[^>]*name=["\']({campo})["\'][^>]*(?:/?>|>.*?</(?:select|textarea)>)', html_content, re.IGNORECASE | re.DOTALL)
                if full_element:
                    element_html = full_element.group(0)
                    campos_encontrados[campo] = element_html[:200] + "..." if len(element_html) > 200 else element_html
                break
        
        if found:
            print(f"✅ {campo}: ENCONTRADO")
        else:
            print(f"❌ {campo}: NO ENCONTRADO")
    
    # 5. EXTRAER SECCIONES ESPECÍFICAS
    print("\n🎯 5. BUSCANDO SECCIONES ESPECÍFICAS...")
    
    # Buscar la sección de configuración avanzada
    config_section = re.search(r'Configuración Avanzada.*?</div>\s*</div>', html_content, re.IGNORECASE | re.DOTALL)
    if config_section:
        print("✅ Sección 'Configuración Avanzada' encontrada")
        print(f"Tamaño de la sección: {len(config_section.group(0))} caracteres")
    else:
        print("❌ NO se encontró sección 'Configuración Avanzada'")
    
    # 6. VERIFICAR BOTÓN DE SUBMIT
    print("\n🎯 6. VERIFICANDO BOTÓN DE ENVÍO...")
    submit_buttons = re.findall(r'<(?:button|input)[^>]*type=["\']submit["\'][^>]*>', html_content, re.IGNORECASE)
    if submit_buttons:
        print(f"✅ Botones submit encontrados: {len(submit_buttons)}")
        for i, btn in enumerate(submit_buttons, 1):
            print(f"  Botón {i}: {btn}")
    else:
        print("❌ NO se encontró botón submit")
    
    # 7. BUSCAR ERRORES EN HTML
    print("\n🚨 7. BUSCANDO ERRORES EN HTML...")
    
    # Buscar errorlist de Django
    errorlists = re.findall(r'<ul class=["\']errorlist["\']>.*?</ul>', html_content, re.IGNORECASE | re.DOTALL)
    if errorlists:
        print(f"⚠️ Se encontraron {len(errorlists)} listas de errores:")
        for i, error in enumerate(errorlists, 1):
            print(f"  Error {i}: {error}")
    else:
        print("✅ No se encontraron listas de errores")
    
    # 8. VERIFICAR JAVASCRIPT
    print("\n📜 8. VERIFICANDO JAVASCRIPT...")
    script_tags = re.findall(r'<script[^>]*>.*?</script>', html_content, re.IGNORECASE | re.DOTALL)
    print(f"Scripts encontrados: {len(script_tags)}")
    
    # Buscar referencias a actualizarSugerencias
    if 'actualizarSugerencias' in html_content:
        print("❌ ENCONTRADA referencia a 'actualizarSugerencias' - ESTO CAUSARÁ ERROR")
        matches = re.findall(r'[^\n]*actualizarSugerencias[^\n]*', html_content)
        for match in matches:
            print(f"  -> {match.strip()}")
    else:
        print("✅ No se encontró referencia problemática a 'actualizarSugerencias'")
    
    # 9. MOSTRAR MUESTRA DEL HTML DE CAMPOS CRÍTICOS
    print("\n📝 9. MUESTRA DE HTML DE CAMPOS CRÍTICOS:")
    for campo, html in campos_encontrados.items():
        print(f"\n{campo}:")
        print(f"  {html}")
    
    # 10. VERIFICAR ACTION DEL FORMULARIO
    print("\n🎯 10. VERIFICANDO ACTION DEL FORMULARIO...")
    form_action = re.search(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', html_content, re.IGNORECASE)
    if form_action:
        print(f"✅ Action encontrado: {form_action.group(1)}")
    else:
        print("⚠️ No se encontró action específico (usará URL actual)")
    
    # 11. CONTAR ELEMENTOS DEL FORMULARIO
    print(f"\n📊 11. ESTADÍSTICAS DEL HTML:")
    print(f"  Tamaño total: {len(html_content):,} caracteres")
    print(f"  Elementos <input>: {len(re.findall(r'<input', html_content, re.IGNORECASE))}")
    print(f"  Elementos <select>: {len(re.findall(r'<select', html_content, re.IGNORECASE))}")
    print(f"  Elementos <textarea>: {len(re.findall(r'<textarea', html_content, re.IGNORECASE))}")
    print(f"  Elementos <button>: {len(re.findall(r'<button', html_content, re.IGNORECASE))}")
    
    print("\n✅ Debug HTML completo")

if __name__ == '__main__':
    main()