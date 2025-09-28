#!/usr/bin/env python
"""
DEBUG DE ERRORES ESPECÍFICOS DEL FORMULARIO
Vamos a capturar EXACTAMENTE qué errores están impidiendo guardar
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

def extraer_errores_del_html(html_content):
    """Extraer todos los errores del HTML"""
    errores = {}
    
    # Buscar errorlist de Django
    errorlists = re.findall(r'<ul class=["\']errorlist["\']>(.*?)</ul>', html_content, re.IGNORECASE | re.DOTALL)
    if errorlists:
        print(f"🚨 ERRORES ENCONTRADOS:")
        for i, error in enumerate(errorlists, 1):
            print(f"  Error {i}: {error}")
    
    # Buscar mensajes de error específicos por campo
    error_patterns = [
        r'<div class=["\'][^"\']*text-danger[^"\']*["\'][^>]*>(.*?)</div>',
        r'<span class=["\'][^"\']*error[^"\']*["\'][^>]*>(.*?)</span>',
        r'<div class=["\'][^"\']*invalid-feedback[^"\']*["\'][^>]*>(.*?)</div>'
    ]
    
    for pattern in error_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if matches:
            for match in matches:
                clean_error = re.sub(r'<[^>]+>', '', match).strip()
                if clean_error:
                    print(f"  📍 Error: {clean_error}")

def main():
    print("🔍 DEBUGGEANDO ERRORES ESPECÍFICOS DEL FORMULARIO...")
    
    client = Client()
    User = get_user_model()
    
    # Login como superadmin
    login_success = client.login(username='superadmin', password='AdminPuyo2025!')
    print(f"✅ Login: {login_success}")
    
    # Datos de prueba con código único
    data = {
        'codigo': 'TEST_ERRORES_2024',
        'nombre': 'Segmento Test Errores',
        'tipo': 'estatico',
        'categoria': 'encabezado',
        'descripcion': 'Test para capturar errores',
        'contenido_estatico': 'Contenido de prueba',
        'formato_salida': 'html',
        'orden_defecto': '15',
        'tiempo_limite_ia': '90',
        'reintentos_ia': '2',
        'activo': 'on',
        'reutilizable': 'on'
    }
    
    print("\n💾 ENVIANDO FORMULARIO...")
    print("Datos a enviar:")
    for k, v in data.items():
        print(f"  {k}: {v}")
    
    response = client.post('/generador-actas/segmentos/crear/', data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ ¡ÉXITO! Redirigiendo a:", response.url)
    else:
        print("❌ ERROR EN FORMULARIO")
        html_content = response.content.decode()
        
        # Extraer errores específicos
        extraer_errores_del_html(html_content)
        
        # Buscar si el formulario se está renderizando correctamente
        if 'csrf_token' in html_content:
            print("✅ CSRF token presente en respuesta")
        else:
            print("❌ NO hay CSRF token en respuesta")
        
        # Buscar elementos form
        forms = re.findall(r'<form[^>]*>', html_content, re.IGNORECASE)
        print(f"Forms encontrados en respuesta: {len(forms)}")
        
        # Mostrar primeros 1000 caracteres para debug
        print(f"\n📝 PRIMEROS 1000 CARACTERES DE LA RESPUESTA:")
        print(html_content[:1000])
        print("...")
        
        # Buscar parte crítica donde deberían estar los errores
        if 'Crear Segmento' in html_content or 'crear segmento' in html_content.lower():
            print("✅ La página del formulario se está cargando")
            
            # Buscar específicamente errorlists cerca del título
            formulario_section = re.search(r'Crear Segmento.*?</form>', html_content, re.IGNORECASE | re.DOTALL)
            if formulario_section:
                print("✅ Sección del formulario encontrada")
                form_html = formulario_section.group(0)
                
                # Buscar errores en esta sección específica
                if 'errorlist' in form_html:
                    print("🚨 HAY ERRORES EN EL FORMULARIO:")
                    errorlists = re.findall(r'<ul class=["\']errorlist["\']>(.*?)</ul>', form_html, re.IGNORECASE | re.DOTALL)
                    for error in errorlists:
                        clean_error = re.sub(r'<[^>]+>', '', error).strip()
                        print(f"  -> {clean_error}")
                else:
                    print("🤔 NO hay errorlists en el formulario - problema más profundo")
            else:
                print("❌ NO se encontró la sección del formulario")
        else:
            print("❌ La página NO parece ser el formulario de crear segmento")

if __name__ == '__main__':
    main()