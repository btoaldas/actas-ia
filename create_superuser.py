#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Crear superusuario si no existe
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@actas.ia',
        password='admin123'
    )
    print("Superusuario 'admin' creado exitosamente")
    print("Usuario: admin")
    print("Contraseña: admin123")
else:
    print("El superusuario 'admin' ya existe")
