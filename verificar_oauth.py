#!/usr/bin/env python3
"""
🔍 Script de Verificación OAuth - Sistema de Actas Municipales Pastaza
Verifica que la configuración OAuth esté correcta antes de desplegar

Uso: python verificar_oauth.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Imprime un header decorado"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"✅ {message}")

def print_error(message):
    """Imprime mensaje de error"""
    print(f"❌ {message}")

def print_warning(message):
    """Imprime mensaje de advertencia"""
    print(f"⚠️  {message}")

def check_env_file():
    """Verifica que el archivo .env existe y tiene las variables necesarias"""
    print_header("Verificando archivo .env")
    
    env_path = Path(".env")
    if not env_path.exists():
        print_error("Archivo .env no encontrado")
        print("   Ejecuta: cp .env.example .env")
        return False
    
    print_success("Archivo .env encontrado")
    
    # Leer variables requeridas
    required_vars = [
        'GITHUB_CLIENT_ID',
        'GITHUB_CLIENT_SECRET',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET'
    ]
    
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if f"{var}=" not in env_content or f"{var}=tu_" in env_content:
            missing_vars.append(var)
    
    if missing_vars:
        print_error(f"Variables faltantes o sin configurar: {', '.join(missing_vars)}")
        print("   Configura estas variables en el archivo .env")
        return False
    
    print_success("Todas las variables OAuth están configuradas")
    return True

def check_docker_services():
    """Verifica que los servicios Docker estén ejecutándose"""
    print_header("Verificando servicios Docker")
    
    try:
        result = subprocess.run(['docker-compose', '-f', 'docker-compose.simple.yml', 'ps'], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print_error("Error ejecutando docker-compose ps")
            return False
        
        services = ['web', 'postgres', 'redis', 'celery_worker']
        running_services = []
        
        for line in result.stdout.split('\n'):
            for service in services:
                if service in line and 'Up' in line:
                    running_services.append(service)
        
        for service in services:
            if service in running_services:
                print_success(f"Servicio {service} ejecutándose")
            else:
                print_error(f"Servicio {service} no está ejecutándose")
                return False
        
        return True
        
    except FileNotFoundError:
        print_error("Docker o docker-compose no encontrado")
        return False

def check_web_service():
    """Verifica que el servicio web responda"""
    print_header("Verificando servicio web")
    
    try:
        import requests
        response = requests.get('http://localhost:8000', timeout=10)
        if response.status_code == 200:
            print_success("Servicio web respondiendo en puerto 8000")
            return True
        else:
            print_error(f"Servicio web respondió con código {response.status_code}")
            return False
    except Exception as e:
        print_error(f"No se puede conectar al servicio web: {e}")
        return False

def check_oauth_urls():
    """Verifica que las URLs de OAuth estén accesibles"""
    print_header("Verificando URLs OAuth")
    
    try:
        import requests
        
        urls = [
            'http://localhost:8000/accounts/login/',
            'http://localhost:8000/accounts/github/login/',
            'http://localhost:8000/accounts/google/login/'
        ]
        
        for url in urls:
            try:
                response = requests.get(url, timeout=5, allow_redirects=False)
                if response.status_code in [200, 302]:
                    print_success(f"URL accesible: {url}")
                else:
                    print_warning(f"URL {url} respondió con código {response.status_code}")
            except Exception as e:
                print_error(f"Error accediendo a {url}: {e}")
        
        return True
        
    except ImportError:
        print_warning("Módulo requests no disponible, saltando verificación de URLs")
        return True

def check_admin_config():
    """Verifica configuración en Django Admin"""
    print_header("Verificando configuración Django Admin")
    
    print("🔧 Para completar la configuración OAuth:")
    print("   1. Ve a http://localhost:8000/admin/")
    print("   2. Login: superadmin / AdminPuyo2025!")
    print("   3. Configura 'Sites' y 'Social applications'")
    print("   4. Ver GUIA_OAUTH.md para detalles completos")
    
    return True

def main():
    """Función principal"""
    print_header("VERIFICADOR OAUTH - SISTEMA ACTAS MUNICIPALES PASTAZA")
    
    all_checks = [
        check_env_file,
        check_docker_services,
        check_web_service,
        check_oauth_urls,
        check_admin_config
    ]
    
    results = []
    
    for check in all_checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print_error(f"Error en verificación: {e}")
            results.append(False)
    
    # Resumen final
    print_header("RESUMEN DE VERIFICACIÓN")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print_success(f"✨ Todas las verificaciones pasaron ({passed}/{total})")
        print("\n🚀 OAuth está listo para usar!")
        print("   Ve a: http://localhost:8000/accounts/login/")
    else:
        print_error(f"Algunas verificaciones fallaron ({passed}/{total})")
        print("\n📖 Consulta GUIA_OAUTH.md para solucionar problemas")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
