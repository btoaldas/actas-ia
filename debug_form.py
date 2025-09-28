#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    import django
    django.setup()
    
    from django.contrib.auth.models import User
    from django.test import Client
    from apps.generador_actas.models import ProveedorIA
    
    print("🔍 DEBUGGEANDO FORMULARIO DE SEGMENTOS...")
    
    c = Client()
    login_ok = c.login(username='superadmin', password='AdminPuyo2025!')
    print(f"✅ Login: {login_ok}")
    
    # Primero, obtenemos el formulario vacío
    print("\n📄 1. Obteniendo formulario...")
    response = c.get('/generador-actas/segmentos/crear/')
    print(f"Status GET: {response.status_code}")
    
    # Preparamos datos mínimos
    print("\n📝 2. Preparando datos de prueba...")
    proveedor = ProveedorIA.objects.first()
    
    data = {
        'codigo': 'DEBUG_DINAMICO',
        'nombre': 'Segmento Dinámico Debug', 
        'tipo': 'dinamico',
        'categoria': 'participantes',
        'descripcion': 'Test segmento dinámico',
        'prompt_ia': 'Extrae los participantes de la transcripción. Responde en JSON con nombres y cargos.',
        'proveedor_ia': proveedor.pk if proveedor else '',
        # CAMPOS OCULTOS QUE AGREGAMOS AL TEMPLATE
        'formato_salida': 'json',
        'orden_defecto': '5', 
        'tiempo_limite_ia': '120',
        'reintentos_ia': '3',
        'activo': 'on',
        'reutilizable': 'on'
    }
    
    print("Datos a enviar:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    # Intentamos crear
    print("\n💾 3. Intentando crear segmento...")
    response = c.post('/generador-actas/segmentos/crear/', data)
    print(f"Status POST: {response.status_code}")
    
    if response.status_code == 302:
        print("✅ ¡CREACIÓN EXITOSA!")
        print(f"Redirect a: {response.get('Location', 'Sin ubicación')}")
    else:
        print("❌ ERROR EN CREACIÓN")
        print("Analizando formulario...")
        
        if hasattr(response, 'context') and response.context:
            form = response.context.get('form')
            if form:
                print("\n🔴 ERRORES DEL FORMULARIO:")
                if hasattr(form, 'errors') and form.errors:
                    for field, errors in form.errors.items():
                        print(f"  Campo '{field}': {errors}")
                else:
                    print("  (No hay errores específicos de campos)")
                
                if hasattr(form, 'non_field_errors') and form.non_field_errors():
                    print(f"  Errores generales: {form.non_field_errors()}")
                
                # Mostrar campos requeridos
                print("\n📋 CAMPOS REQUERIDOS:")
                for field_name, field in form.fields.items():
                    if field.required:
                        value = form.data.get(field_name, 'NO ENVIADO')
                        print(f"  {field_name}: {value}")
        else:
            print("No se puede acceder al contexto del formulario")
    
    print("\n✅ Debug completo")