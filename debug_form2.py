#!/usr/bin/env python
"""
Debug del formulario de segmentos - VERSION NUEVA
Probando tanto creación como edición con todos los campos visibles
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

def main():
    print("🔍 DEBUGGEANDO FORMULARIO COMPLETO...")
    
    client = Client()
    User = get_user_model()
    
    # Login como superadmin
    login_success = client.login(username='superadmin', password='AdminPuyo2025!')
    print(f"✅ Login: {login_success}")
    
    # 1. TEST CREACIÓN CON CÓDIGO ÚNICO
    print("\n📄 1. Test de CREACIÓN...")
    response = client.get('/generador-actas/segmentos/crear/')
    print(f"Status GET: {response.status_code}")
    
    # Datos de prueba para CREAR
    data_crear = {
        'codigo': 'TEST_NUEVO_2024',
        'nombre': 'Segmento Nuevo Test',
        'tipo': 'estatico',
        'categoria': 'encabezado',
        'descripcion': 'Test segmento estático nuevo',
        'contenido_estatico': 'Este es contenido estático de prueba',
        'formato_salida': 'html',
        'orden_defecto': '15',
        'tiempo_limite_ia': '90',
        'reintentos_ia': '2',
        'activo': 'on',
        'reutilizable': 'on'
    }
    
    print("Datos a enviar:")
    for k, v in data_crear.items():
        print(f"  {k}: {v}")
    
    response_crear = client.post('/generador-actas/segmentos/crear/', data_crear)
    print(f"Status POST CREAR: {response_crear.status_code}")
    
    if response_crear.status_code == 302:
        print("✅ ¡CREACIÓN EXITOSA!")
        print(f"Redirect a: {response_crear.url}")
        
        # Extraer ID del redirect
        try:
            segment_id = response_crear.url.split('/')[-2]
            print(f"ID del segmento: {segment_id}")
            
            # 2. TEST EDICIÓN
            print(f"\n✏️ 2. Test de EDICIÓN (ID: {segment_id})...")
            response_edit = client.get(f'/generador-actas/segmentos/{segment_id}/editar/')
            print(f"Status GET EDITAR: {response_edit.status_code}")
            
            # Datos para editar
            data_editar = {
                'codigo': 'TEST_NUEVO_2024',
                'nombre': 'Segmento Editado Test',
                'tipo': 'dinamico',  # Cambiar a dinámico
                'categoria': 'participantes',
                'descripcion': 'Test segmento editado con IA',
                'prompt_ia': 'Identifica los participantes de la reunión. Responde en JSON.',
                'proveedor_ia': '1',
                'formato_salida': 'json',
                'orden_defecto': '20',
                'tiempo_limite_ia': '150',
                'reintentos_ia': '3',
                'activo': 'on',
                'reutilizable': 'on'
            }
            
            response_editar = client.post(f'/generador-actas/segmentos/{segment_id}/editar/', data_editar)
            print(f"Status POST EDITAR: {response_editar.status_code}")
            
            if response_editar.status_code == 302:
                print("✅ ¡EDICIÓN EXITOSA!")
                print(f"Redirect a: {response_editar.url}")
            else:
                print("❌ ERROR EN EDICIÓN")
                
        except Exception as e:
            print(f"Error procesando ID: {e}")
            
    else:
        print("❌ ERROR EN CREACIÓN")
        print(f"Contenido: {response_crear.content.decode()[:500]}...")
    
    # 3. VERIFICAR QUE LOS CAMPOS ESTÁN EN EL FORMULARIO
    print("\n🔍 3. Verificando campos del formulario...")
    response = client.get('/generador-actas/segmentos/crear/')
    content = response.content.decode()
    
    campos_a_verificar = [
        'formato_salida',
        'orden_defecto', 
        'tiempo_limite_ia',
        'reintentos_ia',
        'activo',
        'reutilizable'
    ]
    
    for campo in campos_a_verificar:
        if f'name="{campo}"' in content:
            print(f"✅ Campo '{campo}' encontrado en formulario")
        else:
            print(f"❌ Campo '{campo}' NO encontrado")
    
    print("\n✅ Debug completo")

if __name__ == '__main__':
    main()