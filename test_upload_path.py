#!/usr/bin/env python
"""
Script para verificar la estructura de subida de archivos
"""
import os
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.pages.models import evento_documento_upload_path, EventoMunicipal

def test_upload_path():
    """Prueba la función de generación de rutas de subida"""
    print("=== PRUEBA DE RUTAS DE SUBIDA ===")
    
    # Crear un evento de prueba (sin guardarlo)
    fecha_prueba = datetime(2025, 9, 6, 14, 30)
    evento_mock = type('MockEvento', (), {
        'fecha_inicio': fecha_prueba,
        'tipo': 'sesion_ordinaria'
    })()
    
    # Crear una instancia mock de documento
    documento_mock = type('MockDocumento', (), {
        'evento': evento_mock
    })()
    
    # Probar la función de ruta
    ruta = evento_documento_upload_path(documento_mock, 'acta_reunion.pdf')
    print(f"✓ Ruta generada: {ruta}")
    
    # Verificar estructura esperada
    expected_parts = ['eventos', '2025', '09', 'sesion_ordinaria']
    ruta_parts = ruta.split('/')
    
    for expected in expected_parts:
        if expected in ruta_parts:
            print(f"✓ Contiene '{expected}': SÍ")
        else:
            print(f"✗ Contiene '{expected}': NO")
    
    print(f"✓ Estructura jerárquica: media/{ruta}")
    print("\n=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    test_upload_path()
