#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import ConfiguracionIA, ConfiguracionWhisper, PerfilUsuario
from django.contrib.auth.models import User

print("=== VERIFICACIÓN DE BASE DE DATOS ===")
print(f"Usuarios: {User.objects.count()}")
print(f"Configuraciones IA: {ConfiguracionIA.objects.count()}")
print(f"Configuraciones Whisper: {ConfiguracionWhisper.objects.count()}")
print(f"Perfiles de Usuario: {PerfilUsuario.objects.count()}")

print("\n=== CONFIGURACIONES IA EXISTENTES ===")
for config in ConfiguracionIA.objects.all():
    print(f"- {config.nombre} ({config.proveedor}) - Activa: {config.activa}")

print("\n=== CONFIGURACIONES WHISPER EXISTENTES ===")
for config in ConfiguracionWhisper.objects.all():
    print(f"- {config.nombre} (modelo: {config.modelo_whisper}) - Activa: {config.activa}")

print("\n=== PERFILES DE USUARIO ===")
for perfil in PerfilUsuario.objects.all():
    print(f"- {perfil.usuario.username} ({perfil.rol}) - Departamento: {perfil.departamento}")
