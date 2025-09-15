import subprocess
import re

def test_form_with_env_config():
    """Probar el formulario con configuración del .env"""
    
    print("=== TESTING FORM WITH .ENV CONFIGURATION ===")
    
    try:
        # 1. Obtener CSRF token
        login_response = subprocess.run([
            'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
            'http://localhost:8000/admin/login/'
        ], capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        csrf_match = re.search(r"name='csrfmiddlewaretoken' value='([^']+)'", login_response.stdout)
        if not csrf_match:
            print("❌ No se pudo obtener CSRF token")
            return
            
        csrf_token = csrf_match.group(1)
        print(f"✅ CSRF Token: {csrf_token[:20]}...")
        
        # 2. Login
        auth_response = subprocess.run([
            'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
            '-X', 'POST',
            '-d', f'csrfmiddlewaretoken={csrf_token}',
            '-d', 'username=superadmin',
            '-d', 'password=AdminPuyo2025!',
            '-d', 'next=/admin/',
            'http://localhost:8000/admin/login/'
        ], capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        print("✅ Login realizado")
        
        # 3. Obtener formulario de crear proveedor
        form_response = subprocess.run([
            'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
            'http://localhost:8000/generador-actas/proveedores/crear/'
        ], capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        if "Configuración del Proveedor" not in form_response.stdout:
            print("❌ Error cargando formulario")
            return
            
        print("✅ Formulario cargado")
        
        # Extraer CSRF del formulario
        form_csrf_match = re.search(r"name='csrfmiddlewaretoken' value='([^']+)'", form_response.stdout)
        if not form_csrf_match:
            print("❌ No se encontró CSRF en formulario")
            return
            
        form_csrf = form_csrf_match.group(1)
        
        # 4. Probar OPENAI con .env
        print("\n=== TESTING OPENAI WITH .ENV ===")
        openai_response = subprocess.run([
            'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
            '-X', 'POST',
            '-d', f'csrfmiddlewaretoken={form_csrf}',
            '-d', 'nombre=OpenAI ENV Test',
            '-d', 'tipo=openai',
            '-d', 'usar_env_api_key=on',  # Checkbox marcado
            '-d', 'api_key=',  # Campo vacío
            '-d', 'api_url=https://api.openai.com/v1/chat/completions',
            '-d', 'modelo=gpt-4o-mini',
            '-d', 'temperatura=0.7',
            '-d', 'max_tokens=2000',
            '-d', 'costo_por_1k_tokens=0.001',
            '-d', 'activo=on',
            'http://localhost:8000/generador-actas/proveedores/crear/'
        ], capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        if "No se encontró OPENAI_API_KEY" in openai_response.stdout:
            print("❌ OPENAI: Sigue sin encontrar la configuración del .env")
        elif "Debe proporcionar una API Key" in openai_response.stdout:
            print("❌ OPENAI: Formulario sigue pidiendo API Key")
        elif any(keyword in openai_response.stdout.lower() for keyword in ['lista', 'proveedores', 'success']):
            print("✅ OPENAI: Creado exitosamente con .env")
        else:
            print("⚠️ OPENAI: Respuesta inesperada")
            print("Últimos 300 caracteres:", openai_response.stdout[-300:])
        
        # 5. Probar DEEPSEEK con .env
        print("\n=== TESTING DEEPSEEK WITH .ENV ===")
        deepseek_response = subprocess.run([
            'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
            '-X', 'POST',
            '-d', f'csrfmiddlewaretoken={form_csrf}',
            '-d', 'nombre=DeepSeek ENV Test',
            '-d', 'tipo=deepseek',
            '-d', 'usar_env_api_key=on',  # Checkbox marcado
            '-d', 'api_key=',  # Campo vacío
            '-d', 'api_url=https://api.deepseek.com/v1/chat/completions',
            '-d', 'modelo=deepseek-chat',
            '-d', 'temperatura=0.7',
            '-d', 'max_tokens=2000',
            '-d', 'costo_por_1k_tokens=0.001',
            '-d', 'activo=on',
            'http://localhost:8000/generador-actas/proveedores/crear/'
        ], capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        if "No se encontró DEEPSEEK_API_KEY" in deepseek_response.stdout:
            print("❌ DEEPSEEK: Sigue sin encontrar la configuración del .env")
        elif "Debe proporcionar una API Key" in deepseek_response.stdout:
            print("❌ DEEPSEEK: Formulario sigue pidiendo API Key")
        elif any(keyword in deepseek_response.stdout.lower() for keyword in ['lista', 'proveedores', 'success']):
            print("✅ DEEPSEEK: Creado exitosamente con .env")
        else:
            print("⚠️ DEEPSEEK: Respuesta inesperada")
            print("Últimos 300 caracteres:", deepseek_response.stdout[-300:])
            
        # 6. Verificar configuraciones en Django
        print("\n=== VERIFICANDO CONFIGURACIONES EN DJANGO ===")
        config_check = subprocess.run([
            'docker', 'exec', 'actas_web', 'python', 'manage.py', 'shell', '-c',
            'from django.conf import settings; print(f"OPENAI_API_KEY: {settings.OPENAI_API_KEY[:10] if settings.OPENAI_API_KEY else \"VACÍO\"}..."); print(f"DEEPSEEK_API_KEY: {settings.DEEPSEEK_API_KEY[:10] if settings.DEEPSEEK_API_KEY else \"VACÍO\"}...")'
        ], capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        print("Configuraciones Django:")
        print(config_check.stdout)
        if config_check.stderr:
            print("Errores:", config_check.stderr)
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
    
    finally:
        # Cleanup
        try:
            subprocess.run(['rm', 'cookies.txt'], cwd='c:/p/actas.ia')
        except:
            pass

if __name__ == "__main__":
    test_form_with_env_config()