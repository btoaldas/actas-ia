#!/usr/bin/env python
"""
DEBUG DE IDS DE CAMPOS EN EL HTML
Verificar que los IDs coincidan con lo que espera el JavaScript
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
    print("🔍 DEBUGGEANDO IDs DE CAMPOS EN HTML...")
    
    client = Client()
    User = get_user_model()
    
    # Login como superadmin
    login_success = client.login(username='superadmin', password='AdminPuyo2025!')
    print(f"✅ Login: {login_success}")
    
    # Obtener HTML
    response = client.get('/generador-actas/segmentos/crear/')
    if response.status_code != 200:
        print(f"❌ Error obteniendo página: {response.status_code}")
        return
        
    html_content = response.content.decode()
    
    # IDs que espera el JavaScript
    ids_esperados = [
        'id_nombre', 'id_codigo', 'id_tipo', 'id_categoria',
        'id_descripcion', 'id_contenido_estatico', 'id_prompt_ia'
    ]
    
    print("\n📋 VERIFICANDO IDs DE CAMPOS:")
    ids_encontrados = {}
    
    for id_esperado in ids_esperados:
        # Buscar el ID en el HTML
        patron = rf'id="{id_esperado}"[^>]*>'
        match = re.search(patron, html_content)
        
        if match:
            print(f"✅ {id_esperado}: ENCONTRADO")
            # Extraer el elemento completo
            elemento = match.group(0)
            ids_encontrados[id_esperado] = elemento
        else:
            print(f"❌ {id_esperado}: NO ENCONTRADO")
    
    print("\n🔍 ELEMENTOS ENCONTRADOS:")
    for id_campo, elemento in ids_encontrados.items():
        print(f"{id_campo}:")
        print(f"  {elemento}")
    
    # Verificar si el JavaScript está presente
    print("\n📜 VERIFICANDO JAVASCRIPT:")
    js_functions = [
        'autoGenerarCodigo()',
        'autoRellenarEjemplos()',
        'addEventListener'
    ]
    
    for func in js_functions:
        if func in html_content:
            print(f"✅ {func}: PRESENTE")
        else:
            print(f"❌ {func}: NO ENCONTRADO")
    
    # Buscar errores comunes de JavaScript
    print("\n🚨 BUSCANDO ERRORES COMUNES:")
    
    # Verificar que document.getElementById esté presente
    if 'document.getElementById' in html_content:
        print("✅ document.getElementById: PRESENTE")
    else:
        print("❌ document.getElementById: NO ENCONTRADO")
    
    # Contar cuántos getElementById hay
    getbyid_count = html_content.count('document.getElementById')
    print(f"📊 Usos de getElementById: {getbyid_count}")
    
    # Verificar DOMContentLoaded
    if 'DOMContentLoaded' in html_content:
        print("✅ DOMContentLoaded: PRESENTE")
    else:
        print("❌ DOMContentLoaded: NO ENCONTRADO")
    
    # Mostrar parte del JavaScript para debug
    js_start = html_content.find('<script>')
    js_end = html_content.find('</script>', js_start) + 9
    
    if js_start != -1 and js_end != -1:
        js_content = html_content[js_start:js_end]
        print(f"\n📝 PRIMERAS LÍNEAS DEL JAVASCRIPT:")
        js_lines = js_content.split('\n')[:15]  # Primeras 15 líneas
        for i, line in enumerate(js_lines, 1):
            print(f"  {i:2d}: {line}")
        print("  ...")
    
    print("\n✅ Debug de IDs completo")

if __name__ == '__main__':
    main()