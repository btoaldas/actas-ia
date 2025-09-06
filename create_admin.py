import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Verificar si existe
if User.objects.filter(username='admin').exists():
    print("El usuario admin ya existe")
else:
    # Crear superusuario
    user = User.objects.create_user(
        username='admin',
        email='admin@actas.ia',
        password='admin123',
        is_staff=True,
        is_superuser=True
    )
    print("Superusuario creado:")
    print(f"Usuario: {user.username}")
    print("Contraseña: admin123")
    print(f"Es superuser: {user.is_superuser}")
