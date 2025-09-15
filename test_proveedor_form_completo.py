#!/usr/bin/env python
"""
Test completo del formulario de proveedores IA
Verifica que todas las funcionalidades estén funcionando correctamente.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.generador_actas.models import ProveedorIA
from apps.generador_actas.forms import ProveedorIAForm
import json

def test_form_creation():
    """Test de creación del formulario"""
    print("🧪 Probando creación del formulario...")
    
    form_data = {
        'nombre': 'Test Provider API URL',
        'tipo': 'openai',
        'modelo': 'gpt-4',
        'api_url': 'https://api.openai.com/v1/chat/completions',
        'api_key': 'sk-test123456789',
        'prompt_sistema_global': 'Eres un asistente especializado en actas municipales',
        'temperatura': 0.7,
        'max_tokens': 2000,
        'timeout': 60,
        'costo_por_1k_tokens': 0.002,
        'activo': True
    }
    
    form = ProveedorIAForm(data=form_data)
    
    if form.is_valid():
        print("✅ Formulario válido")
        proveedor = form.save()
        print(f"✅ Proveedor creado: {proveedor.nombre}")
        print(f"   - API URL: {proveedor.api_url}")
        print(f"   - Prompt Sistema: {proveedor.prompt_sistema_global[:50]}...")
        print(f"   - Configuración adicional: {proveedor.configuracion_adicional}")
        return proveedor
    else:
        print("❌ Formulario inválido:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return None

def test_form_edit():
    """Test de edición del formulario"""
    print("\n🧪 Probando edición del formulario...")
    
    # Buscar un proveedor existente o crear uno
    proveedor = ProveedorIA.objects.filter(nombre__icontains='Test').first()
    if not proveedor:
        print("   Creando proveedor para prueba...")
        proveedor = test_form_creation()
    
    if not proveedor:
        print("❌ No se pudo crear proveedor para prueba")
        return False
    
    # Editar el proveedor
    form_data = {
        'nombre': proveedor.nombre + ' EDITADO',
        'tipo': proveedor.tipo,
        'modelo': 'gpt-4o',  # Cambiar modelo
        'api_url': 'https://api.openai.com/v1/chat/completions',
        'api_key': proveedor.api_key,  # Mantener API key
        'prompt_sistema_global': 'PROMPT EDITADO: ' + (proveedor.prompt_sistema_global or ''),
        'temperatura': 0.5,  # Cambiar temperatura
        'max_tokens': 3000,  # Cambiar max tokens
        'timeout': proveedor.timeout,
        'costo_por_1k_tokens': proveedor.costo_por_1k_tokens,
        'activo': True
    }
    
    form = ProveedorIAForm(data=form_data, instance=proveedor)
    
    if form.is_valid():
        print("✅ Formulario de edición válido")
        proveedor_editado = form.save()
        print(f"✅ Proveedor editado: {proveedor_editado.nombre}")
        print(f"   - Modelo: {proveedor_editado.modelo}")
        print(f"   - Temperatura: {proveedor_editado.temperatura}")
        print(f"   - Prompt Sistema: {proveedor_editado.prompt_sistema_global[:50]}...")
        return True
    else:
        print("❌ Formulario de edición inválido:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return False

def test_api_configuration():
    """Test de API de configuración por defecto"""
    print("\n🧪 Probando API de configuración por defecto...")
    
    from apps.generador_actas.models import ProveedorIA
    
    configuraciones = ProveedorIA.obtener_configuraciones_por_defecto()
    
    print("✅ Configuraciones disponibles:")
    for tipo, config in configuraciones.items():
        print(f"   {tipo}: {config}")
    
    # Test específico para OpenAI
    config_openai = configuraciones.get('openai', {})
    if config_openai:
        print(f"✅ Configuración OpenAI: {config_openai}")
        return True
    else:
        print("❌ No se encontró configuración OpenAI")
        return False

def test_form_fields():
    """Test de campos del formulario"""
    print("\n🧪 Probando campos del formulario...")
    
    form = ProveedorIAForm()
    
    required_fields = [
        'nombre', 'tipo', 'modelo', 'temperatura', 
        'max_tokens', 'costo_por_1k_tokens'
    ]
    
    optional_fields = [
        'api_key', 'api_url', 'prompt_sistema_global', 
        'timeout', 'activo'
    ]
    
    print("✅ Campos requeridos:")
    for field in required_fields:
        if field in form.fields:
            print(f"   ✓ {field}")
        else:
            print(f"   ❌ {field} (faltante)")
    
    print("✅ Campos opcionales:")
    for field in optional_fields:
        if field in form.fields:
            print(f"   ✓ {field}")
        else:
            print(f"   ❌ {field} (faltante)")
    
    return True

def test_navigation_button():
    """Test del botón de navegación a pruebas"""
    print("\n🧪 Probando navegación a pruebas...")
    
    from django.urls import reverse
    
    try:
        url_test = reverse('generador_actas:test_proveedor_ia')
        print(f"✅ URL de pruebas disponible: {url_test}")
        return True
    except Exception as e:
        print(f"❌ Error en URL de pruebas: {e}")
        return False

def main():
    """Función principal de pruebas"""
    print("🧪 INICIANDO PRUEBAS COMPLETAS DEL FORMULARIO DE PROVEEDORES IA")
    print("=" * 70)
    
    tests = [
        ("Campos del formulario", test_form_fields),
        ("API de configuración", test_api_configuration),
        ("Creación de proveedor", test_form_creation),
        ("Edición de proveedor", test_form_edit),
        ("Navegación a pruebas", test_navigation_button),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE PRUEBAS:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{len(results)} pruebas pasaron")
    
    if passed == len(results):
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
    else:
        print("⚠️  Algunas pruebas fallaron, revisar implementación")

if __name__ == '__main__':
    main()