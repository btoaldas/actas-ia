#!/usr/bin/env python
"""
Script para verificar el estado del sistema y crear usuario de prueba
"""
import subprocess
import time

def verificar_estado_sistema():
    print("🔍 VERIFICANDO ESTADO DEL SISTEMA")
    print("=" * 50)
    
    # 1. Verificar contenedores
    print("📦 Verificando contenedores...")
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=actas", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10
        )
        print(result.stdout)
    except Exception as e:
        print(f"❌ Error verificando contenedores: {e}")
    
    # 2. Verificar conectividad web
    print("\n🌐 Verificando conectividad web...")
    try:
        import requests
        response = requests.get("http://localhost:8000", timeout=5)
        print(f"✅ Servidor responde: {response.status_code}")
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
    
    # 3. Crear usuario simple usando Django
    print("\n👤 Creando usuario de prueba...")
    try:
        cmd = [
            "docker", "exec", "actas_web", "python", "manage.py", "shell", "-c",
            """
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

# Crear usuario simple
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'password': make_password('admin123'),
        'is_superuser': True,
        'is_staff': True,
        'email': 'admin@test.com',
        'first_name': 'Admin',
        'last_name': 'Test'
    }
)

print(f'Usuario admin: {"creado" if created else "ya existe"}')
print(f'Es superuser: {user.is_superuser}')
print(f'Es staff: {user.is_staff}')
print('Credenciales: admin / admin123')
            """
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Comando de usuario ejecutado:")
            print(result.stdout)
        else:
            print("❌ Error creando usuario:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
    
    print("\n📋 INSTRUCCIONES PARA PROBAR EL BOTÓN:")
    print("-" * 50)
    print("1. Abrir http://localhost:8000 en el navegador")
    print("2. Ir a login: http://localhost:8000/accounts/login/")
    print("3. Usar credenciales: admin / admin123")
    print("4. Ir a: http://localhost:8000/transcripcion/configurar/6/")
    print("5. Probar el botón 'Transcribir y Diarización'")
    print("\n🔧 SI EL BOTÓN NO FUNCIONA:")
    print("- Verificar consola del navegador (F12) para errores JavaScript")
    print("- Verificar que el formulario tenga todos los campos requeridos")
    print("- Verificar logs del servidor: docker logs actas_web --tail 50")

if __name__ == "__main__":
    verificar_estado_sistema()
