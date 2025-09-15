#!/usr/bin/env python
"""
Script para probar la funcionalidad de copia automática de API key del .env
"""
import os
import sys
import django
import json
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append('/app')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.generador_actas.models import ProveedorIA
from apps.generador_actas.forms import ProveedorIAForm

def test_api_key_copy():
    """Probar la copia automática de API key del .env"""
    print("🧪 PROBANDO FUNCIONALIDAD DE COPIA AUTOMÁTICA DE API KEY")
    print("=" * 60)
    
    # Datos de prueba para un proveedor DeepSeek con checkbox marcado
    form_data = {
        'nombre': 'DeepSeek Test Auto ENV',
        'tipo': 'deepseek',
        'usar_env_api_key': True,  # Checkbox marcado = usar .env
        'modelo': 'deepseek-chat',
        'temperatura': 0.7,
        'max_tokens': 2000,
        'costo_por_1k_tokens': 0.002,  # Campo requerido
        'activo': True,
        # NO incluimos api_key porque debe copiarse automáticamente
    }
    
    print(f"📋 Datos del formulario:")
    for key, value in form_data.items():
        print(f"   {key}: {value}")
    
    # Crear formulario
    form = ProveedorIAForm(data=form_data)
    
    # Verificar que el formulario es válido
    print(f"\n✅ Formulario válido: {form.is_valid()}")
    if not form.is_valid():
        print("❌ Errores del formulario:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return False
    
    # Verificar valor de API key del .env ANTES del save
    env_api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    print(f"🔑 API Key en .env: {env_api_key[:10]}..." if env_api_key else "❌ No encontrada en .env")
    
    # Guardar el proveedor (aquí debe ocurrir la copia automática)
    print("\n💾 Guardando proveedor...")
    try:
        proveedor = form.save()
        print(f"✅ Proveedor guardado con ID: {proveedor.id}")
        
        # Verificar que la API key se copió correctamente
        print(f"🔍 API Key en BD: {proveedor.api_key[:10]}..." if proveedor.api_key else "❌ No hay API key en BD")
        
        # Comparar si son iguales
        if env_api_key and proveedor.api_key == env_api_key:
            print("✅ ¡ÉXITO! La API key se copió correctamente del .env a la BD")
            return True
        else:
            print("❌ ERROR: La API key no se copió correctamente")
            print(f"   .env: {env_api_key[:20]}...")
            print(f"   BD:   {proveedor.api_key[:20]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error al guardar: {str(e)}")
        return False

def test_custom_api_key():
    """Probar con API key personalizada (checkbox desmarcado)"""
    print("\n🧪 PROBANDO API KEY PERSONALIZADA")
    print("=" * 60)
    
    custom_api_key = "sk-test-custom-key-12345"
    
    form_data = {
        'nombre': 'DeepSeek Test Custom Key',
        'tipo': 'deepseek',
        'usar_env_api_key': False,  # Checkbox desmarcado = API personalizada
        'api_key': custom_api_key,
        'modelo': 'deepseek-chat',
        'temperatura': 0.7,
        'max_tokens': 2000,
        'costo_por_1k_tokens': 0.002,  # Campo requerido
        'activo': True,
    }
    
    print(f"📋 Datos del formulario:")
    for key, value in form_data.items():
        if key == 'api_key':
            print(f"   {key}: {value[:10]}...")
        else:
            print(f"   {key}: {value}")
    
    form = ProveedorIAForm(data=form_data)
    
    print(f"\n✅ Formulario válido: {form.is_valid()}")
    if not form.is_valid():
        print("❌ Errores del formulario:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return False
    
    try:
        proveedor = form.save()
        print(f"✅ Proveedor guardado con ID: {proveedor.id}")
        
        # Verificar que la API key personalizada se guardó
        if proveedor.api_key == custom_api_key:
            print("✅ ¡ÉXITO! La API key personalizada se guardó correctamente")
            return True
        else:
            print("❌ ERROR: La API key personalizada no se guardó correctamente")
            print(f"   Esperado: {custom_api_key[:20]}...")
            print(f"   BD:       {proveedor.api_key[:20]}...")
            return False
            
    except Exception as e:
        print(f"❌ Error al guardar: {str(e)}")
        return False

def cleanup_test_providers():
    """Limpiar proveedores de prueba"""
    print("\n🧹 LIMPIANDO PROVEEDORES DE PRUEBA")
    try:
        proveedores_test = ProveedorIA.objects.filter(
            nombre__icontains='Test Auto ENV'
        ).union(
            ProveedorIA.objects.filter(nombre__icontains='Test Custom Key')
        )
        
        count = proveedores_test.count()
        if count > 0:
            proveedores_test.delete()
            print(f"✅ Eliminados {count} proveedores de prueba")
        else:
            print("ℹ️  No hay proveedores de prueba para eliminar")
    except Exception as e:
        print(f"⚠️  Error al limpiar: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 INICIANDO PRUEBAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Limpiar antes de empezar
    cleanup_test_providers()
    
    # Ejecutar pruebas
    test1_ok = test_api_key_copy()
    test2_ok = test_custom_api_key()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS:")
    print(f"   • Copia automática del .env: {'✅ PASÓ' if test1_ok else '❌ FALLÓ'}")
    print(f"   • API key personalizada:     {'✅ PASÓ' if test2_ok else '❌ FALLÓ'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! La funcionalidad está trabajando correctamente.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar la implementación.")
    
    # Limpiar después de las pruebas
    cleanup_test_providers()
    print("\n✅ Pruebas completadas")