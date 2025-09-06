#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.config_system.models import ConfiguracionIA, ConfiguracionWhisper, PerfilUsuario

print("=== POBLANDO BASE DE DATOS ===")

# 1. Crear superusuario
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@puyo.gob.ec',
        'first_name': 'Admin',
        'last_name': 'Sistema',
        'is_staff': True,
        'is_superuser': True,
    }
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    print("✓ Usuario admin creado")

# 2. Crear configuración IA
ia_config, created = ConfiguracionIA.objects.get_or_create(
    nombre='OpenAI GPT-4 Demo',
    defaults={
        'proveedor': 'openai',
        'modelo': 'gpt-4',
        'api_key': 'sk-demo-key',
        'descripcion': 'Configuración demo para actas municipales',
        'activa': True,
        'prompt_sistema': 'Eres un asistente para actas municipales.',
    }
)
if created:
    print("✓ Configuración IA creada")

# 3. Crear configuración Whisper
whisper_config, created = ConfiguracionWhisper.objects.get_or_create(
    nombre='Whisper Español Demo',
    defaults={
        'modelo_whisper': 'large-v3',
        'idioma': 'es',
        'descripcion': 'Configuración demo para transcripción',
        'activa': True,
        'usar_pyannote': True,
    }
)
if created:
    print("✓ Configuración Whisper creada")

# 4. Crear perfil admin
perfil, created = PerfilUsuario.objects.get_or_create(
    usuario=admin_user,
    defaults={
        'rol': 'superadmin',
        'departamento': 'sistemas',
        'cargo': 'Administrador del Sistema',
    }
)
if created:
    print("✓ Perfil admin creado")

print(f"\nUsuarios: {User.objects.count()}")
print(f"Configuraciones IA: {ConfiguracionIA.objects.count()}")
print(f"Configuraciones Whisper: {ConfiguracionWhisper.objects.count()}")
print(f"Perfiles: {PerfilUsuario.objects.count()}")
print("\n✅ COMPLETADO")
