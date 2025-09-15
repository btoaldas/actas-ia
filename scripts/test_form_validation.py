import subprocess
import re
import json

# 1. Obtener el token CSRF y autenticarse
print("=== STEP 1: Obtener token CSRF ===")
try:
    login_response = subprocess.run([
        'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
        'http://localhost:8000/admin/login/'
    ], capture_output=True, text=True, cwd='c:/p/actas.ia')
    
    # Extraer CSRF token
    csrf_match = re.search(r"name='csrfmiddlewaretoken' value='([^']+)'", login_response.stdout)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"✅ CSRF Token obtenido: {csrf_token[:20]}...")
        
        # 2. Autenticarse como superadmin
        print("\n=== STEP 2: Autenticar como superadmin ===")
        auth_response = subprocess.run([
            'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
            '-X', 'POST',
            '-d', f'csrfmiddlewaretoken={csrf_token}',
            '-d', 'username=superadmin',
            '-d', 'password=AdminPuyo2025!',
            '-d', 'next=/admin/',
            'http://localhost:8000/admin/login/'
        ], capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        if "login" not in auth_response.stdout:
            print("✅ Autenticación exitosa")
            
            # 3. Probar el formulario de crear proveedor
            print("\n=== STEP 3: Obtener formulario de crear proveedor ===")
            form_response = subprocess.run([
                'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
                'http://localhost:8000/generador-actas/proveedores/crear/'
            ], capture_output=True, text=True, cwd='c:/p/actas.ia')
            
            if "Configuración del Proveedor" in form_response.stdout:
                print("✅ Formulario cargado correctamente")
                
                # Extraer CSRF del formulario
                form_csrf_match = re.search(r"name='csrfmiddlewaretoken' value='([^']+)'", form_response.stdout)
                if form_csrf_match:
                    form_csrf = form_csrf_match.group(1)
                    
                    # 4. Probar crear proveedor con checkbox marcado
                    print("\n=== STEP 4: Crear proveedor con .env (checkbox marcado) ===")
                    create_response = subprocess.run([
                        'curl', '-c', 'cookies.txt', '-b', 'cookies.txt',
                        '-X', 'POST',
                        '-d', f'csrfmiddlewaretoken={form_csrf}',
                        '-d', 'nombre=Test OpenAI ENV',
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
                    
                    if "Debe proporcionar una API Key" in create_response.stdout:
                        print("❌ ERROR: Formulario sigue pidiendo API Key aunque checkbox esté marcado")
                        print("Respuesta del servidor:")
                        print(create_response.stdout[-500:])  # Últimos 500 caracteres
                    elif "proveedores" in create_response.stdout.lower() or "lista" in create_response.stdout.lower():
                        print("✅ SUCCESS: Proveedor creado exitosamente")
                    else:
                        print("⚠️ UNKNOWN: Respuesta inesperada del servidor")
                        print("Status code se detecta por ausencia de errores HTML")
                        
                else:
                    print("❌ No se encontró CSRF token en formulario")
            else:
                print("❌ Error cargando formulario")
                print(form_response.stdout[-200:])
        else:
            print("❌ Error en autenticación")
    else:
        print("❌ No se pudo obtener CSRF token")
        
except Exception as e:
    print(f"❌ Error en prueba: {e}")

print("\n=== CLEANUP ===")
try:
    subprocess.run(['rm', 'cookies.txt'], cwd='c:/p/actas.ia')
    print("✅ Archivos temporales limpiados")
except:
    pass