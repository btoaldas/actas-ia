#!/usr/bin/env python
"""Script para verificar la página de detalle"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def main():
    # Crear cliente de test
    client = Client()

    # Obtener usuario superadmin
    user = User.objects.get(username='superadmin')
    client.force_login(user)

    # Hacer request a la página
    response = client.get('/transcripcion/detalle/29/')
    print(f'Status: {response.status_code}')

    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'json-viewer' in content:
            print('✅ Nuevos estilos JSON encontrados')
        else:
            print('❌ Nuevos estilos JSON NO encontrados')
            
        if 'colorizeJSON' in content:
            print('✅ Función colorizeJSON encontrada')
        else:
            print('❌ Función colorizeJSON NO encontrada')
            
        # Verificar JSON formateados en contexto
        if 'transcripcion_json_formatted' in content:
            print('✅ JSON formateado en contexto encontrado')
        else:
            print('❌ JSON formateado en contexto NO encontrado')
            
        # Verificar que los divs de JSON existen
        if 'id="transcripcion-json"' in content:
            print('✅ Div transcripcion-json encontrado')
        if 'id="diarizacion-json"' in content:
            print('✅ Div diarizacion-json encontrado')
        if 'id="conversacion-json"' in content:
            print('✅ Div conversacion-json encontrado')
            
        # Verificar que los estilos CSS están presentes
        if '.json-key' in content:
            print('✅ Estilos CSS para colorear JSON encontrados')
        else:
            print('❌ Estilos CSS para colorear JSON NO encontrados')
    else:
        print(f'Error: {response.status_code}')

if __name__ == '__main__':
    main()