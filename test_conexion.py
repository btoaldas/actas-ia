#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.config_system.models import PerfilUsuario

print("VERIFICANDO CONEXIÓN...")
print(f"Usuarios: {User.objects.count()}")
print(f"Perfiles: {PerfilUsuario.objects.count()}")

for user in User.objects.all()[:3]:
    print(f"- {user.username}")
    try:
        perfil = user.perfilusuario
        print(f"  Rol: {perfil.rol}")
    except:
        print(f"  Sin perfil")

print("CONEXIÓN OK")
