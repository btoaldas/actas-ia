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
    
    c = Client()
    c.login(username='superadmin', password='AdminPuyo2025!')
    
    # Obtener un proveedor de IA si existe
    from apps.generador_actas.models import ProveedorIA
    proveedor = ProveedorIA.objects.first()
    
    data = {
        'codigo': 'TEST_DINAMICO_FORM', 
        'nombre': 'Test Segmento Dinámico', 
        'tipo': 'dinamico', 
        'categoria': 'participantes', 
        'descripcion': 'Test segmento dinámico con IA', 
        'prompt_ia': 'Analiza la transcripción y extrae los participantes de la reunión. Responde en formato JSON con los nombres y cargos.',
        'proveedor_ia': proveedor.id if proveedor else '',
        # CAMPOS REQUERIDOS FALTANTES
        'formato_salida': 'json',
        'orden_defecto': '5',
        'tiempo_limite_ia': '120',
        'reintentos_ia': '3',
        'activo': True,
        'reutilizable': True,
        'obligatorio': False
    }
    
    print("Enviando datos al formulario...")
    response = c.post('/generador-actas/segmentos/crear/', data)
    print(f'Status: {response.status_code}')
    
    if response.status_code == 302:
        print('✅ SEGMENTO CREADO EXITOSAMENTE!')
        print(f'Redirect Location: {response.get("Location", "No location")}')
    else:
        print('❌ Error en el formulario')
        if hasattr(response, 'context') and response.context:
            form = response.context.get('form')
            if form and hasattr(form, 'errors'):
                print('Errores del formulario:')
                for field, errors in form.errors.items():
                    print(f'  {field}: {errors}')