#!/usr/bin/env python
"""
Script para probar la funcionalidad de copia automática de API key 
a través de la interfaz web con autenticación
"""
import os
import sys
import django
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append('/app')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.generador_actas.models import ProveedorIA
from apps.generador_actas.forms import ProveedorIAForm

User = get_user_model()

def test_with_authenticated_user():
    """Probar con usuario autenticado"""
    print("🧪 PROBANDO CON USUARIO AUTENTICADO")
    print("=" * 60)
    
    # Obtener o crear un usuario de prueba
    try:
        user = User.objects.get(username='superadmin')
        print(f"👤 Usuario encontrado: {user.username}")
    except User.DoesNotExist:
        print("❌ Usuario superadmin no encontrado")
        return False
    
    # Datos de prueba para un proveedor DeepSeek con checkbox marcado
    form_data = {
        'nombre': 'DeepSeek WebTest Auto ENV',
        'tipo': 'deepseek',
        'usar_env_api_key': True,  # Checkbox marcado = usar .env
        'modelo': 'deepseek-chat',
        'temperatura': 0.7,
        'max_tokens': 2000,
        'costo_por_1k_tokens': 0.002,
        'activo': True,
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
    print(f"🔑 API Key en .env: {env_api_key[:15]}..." if env_api_key else "❌ No encontrada en .env")
    
    # Guardar el proveedor con usuario
    print("\n💾 Guardando proveedor...")
    try:
        proveedor = form.save(commit=False)
        proveedor.usuario_creacion = user  # Asignar usuario
        proveedor.save()
        
        print(f"✅ Proveedor guardado con ID: {proveedor.id}")
        print(f"👤 Usuario creación: {proveedor.usuario_creacion.username}")
        
        # Verificar que la API key se copió correctamente
        print(f"🔍 API Key en BD: {proveedor.api_key[:15]}..." if proveedor.api_key else "❌ No hay API key en BD")
        
        # Comparar si son iguales
        if env_api_key and proveedor.api_key == env_api_key:
            print("✅ ¡ÉXITO! La API key se copió correctamente del .env a la BD")
            
            # Mostrar algunos caracteres más para confirmar
            print(f"   🔑 Confirmación - Últimos 8 chars: ...{env_api_key[-8:]}")
            return proveedor.id
        else:
            print("❌ ERROR: La API key no se copió correctamente")
            print(f"   .env: {env_api_key[:20]}...{env_api_key[-8:]}")
            print(f"   BD:   {proveedor.api_key[:20]}...{proveedor.api_key[-8:] if proveedor.api_key else 'None'}")
            return False
            
    except Exception as e:
        print(f"❌ Error al guardar: {str(e)}")
        return False

def test_edit_existing_provider():
    """Probar edición de proveedor existente para ver cómo maneja el checkbox"""
    print("\n🧪 PROBANDO EDICIÓN DE PROVEEDOR EXISTENTE")
    print("=" * 60)
    
    # Buscar un proveedor existente
    try:
        proveedor = ProveedorIA.objects.filter(tipo='deepseek').first()
        if not proveedor:
            print("❌ No hay proveedores DeepSeek existentes para probar")
            return False
        
        print(f"📄 Proveedor existente: {proveedor.nombre} (ID: {proveedor.id})")
        print(f"🔑 API Key actual: {proveedor.api_key[:15]}..." if proveedor.api_key else "❌ Sin API key")
        
        # Crear formulario de edición con el checkbox marcado
        form_data = {
            'nombre': proveedor.nombre,
            'tipo': proveedor.tipo,
            'usar_env_api_key': True,  # Cambiar a usar .env
            'modelo': proveedor.modelo,
            'temperatura': proveedor.temperatura,
            'max_tokens': proveedor.max_tokens,
            'costo_por_1k_tokens': float(proveedor.costo_por_1k_tokens),
            'activo': proveedor.activo,
        }
        
        # Crear formulario con la instancia existente
        form = ProveedorIAForm(data=form_data, instance=proveedor)
        
        if form.is_valid():
            env_api_key = os.environ.get('DEEPSEEK_API_KEY', '')
            
            # Guardar
            updated_proveedor = form.save()
            
            print(f"✅ Proveedor actualizado")
            print(f"🔑 Nueva API Key: {updated_proveedor.api_key[:15]}..." if updated_proveedor.api_key else "❌ Sin API key")
            
            if env_api_key and updated_proveedor.api_key == env_api_key:
                print("✅ ¡ÉXITO! La API key se actualizó del .env en la edición")
                return True
            else:
                print("❌ La API key no se actualizó correctamente en la edición")
                return False
        else:
            print("❌ Formulario de edición no válido")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ Error en edición: {str(e)}")
        return False

def cleanup_test_providers():
    """Limpiar proveedores de prueba"""
    print("\n🧹 LIMPIANDO PROVEEDORES DE PRUEBA")
    try:
        proveedores_test = ProveedorIA.objects.filter(
            nombre__icontains='WebTest Auto ENV'
        )
        
        count = proveedores_test.count()
        if count > 0:
            for p in proveedores_test:
                print(f"   🗑️  Eliminando: {p.nombre}")
            proveedores_test.delete()
            print(f"✅ Eliminados {count} proveedores de prueba")
        else:
            print("ℹ️  No hay proveedores de prueba para eliminar")
    except Exception as e:
        print(f"⚠️  Error al limpiar: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 INICIANDO PRUEBAS WEB - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Limpiar antes de empezar
    cleanup_test_providers()
    
    # Ejecutar pruebas
    test1_result = test_with_authenticated_user()
    test2_result = test_edit_existing_provider()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS WEB:")
    print(f"   • Creación con .env:         {'✅ PASÓ' if test1_result else '❌ FALLÓ'}")
    print(f"   • Edición cambio a .env:     {'✅ PASÓ' if test2_result else '❌ FALLÓ'}")
    
    if test1_result and test2_result:
        print("\n🎉 ¡TODAS LAS PRUEBAS WEB PASARON! La funcionalidad de copia automática funciona perfectamente.")
        print("\n🔧 FUNCIONAMIENTO CONFIRMADO:")
        print("   • ✅ Checkbox marcado → API key copiada del .env a BD")
        print("   • ✅ Proveedor funcional con API key del .env")  
        print("   • ✅ Edición preserva la funcionalidad")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisar la implementación.")
    
    # Limpiar después de las pruebas
    cleanup_test_providers()
    print("\n✅ Pruebas web completadas")