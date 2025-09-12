#!/usr/bin/env python
"""
Script para probar el login y acceso al formulario de transcripción
"""
import requests
import re

def test_login_and_form():
    session = requests.Session()
    
    # 1. Obtener página de login
    print("🔐 OBTENIENDO PÁGINA DE LOGIN...")
    login_page = session.get("http://localhost:8000/accounts/login/")
    
    if login_page.status_code != 200:
        print(f"❌ Error al cargar login: {login_page.status_code}")
        return
    
    # 2. Extraer token CSRF
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', login_page.text)
    if not csrf_match:
        print("❌ No se encontró token CSRF")
        return
    
    csrf_token = csrf_match.group(1)
    print(f"✅ Token CSRF obtenido: {csrf_token[:10]}...")
    
    # 3. Intentar login con diferentes credenciales
    credentials = [
        ("superadmin", "AdminPuyo2025!"),
        ("admin", "AdminPuyo2025!"),
        ("testuser", "test123"),
        ("admin", "admin")
    ]
    
    for username, password in credentials:
        print(f"\n🔑 PROBANDO LOGIN: {username} / {password}")
        
        login_data = {
            'csrfmiddlewaretoken': csrf_token,
            'username': username,
            'password': password
        }
        
        response = session.post("http://localhost:8000/accounts/login/", data=login_data)
        
        if response.status_code == 302:
            print(f"✅ LOGIN EXITOSO con {username}")
            print(f"   Redirigido a: {response.headers.get('Location', 'N/A')}")
            
            # 4. Ahora probar acceso al formulario de transcripción
            print("\n📝 PROBANDO ACCESO AL FORMULARIO...")
            form_response = session.get("http://localhost:8000/transcripcion/configurar/6/")
            
            if form_response.status_code == 200:
                print("✅ Acceso al formulario exitoso")
                
                # 5. Extraer nuevo token CSRF del formulario
                form_csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', form_response.text)
                if form_csrf_match:
                    form_csrf = form_csrf_match.group(1)
                    print(f"✅ Token CSRF del formulario: {form_csrf[:10]}...")
                    
                    # 6. Simular envío del formulario
                    print("\n🚀 SIMULANDO ENVÍO DEL FORMULARIO...")
                    form_data = {
                        'csrfmiddlewaretoken': form_csrf,
                        'configuracion_id': '1',
                        'modelo_whisper': 'tiny',
                        'idioma_principal': 'es',
                        'temperatura': '0.0',
                        'usar_vad': 'on',
                        'vad_filtro': 'silero',
                        'min_hablantes': '1',
                        'max_hablantes': '4',
                        'umbral_clustering': '0.7',
                        'chunk_duracion': '30',
                        'usar_gpu': 'off',
                        'filtro_ruido': 'on',
                        'normalizar_audio': 'on'
                    }
                    
                    form_submit = session.post("http://localhost:8000/transcripcion/configurar/6/", data=form_data)
                    
                    print(f"📊 Respuesta del formulario: {form_submit.status_code}")
                    if form_submit.status_code == 302:
                        print(f"✅ FORMULARIO PROCESADO - Redirigido a: {form_submit.headers.get('Location')}")
                        return True
                    elif form_submit.status_code == 200:
                        if 'error' in form_submit.text.lower():
                            print("⚠️ Formulario devuelto con errores")
                        else:
                            print("⚠️ Formulario mostrado nuevamente (verificar validación)")
                else:
                    print("❌ No se encontró token CSRF en el formulario")
            elif form_response.status_code == 302:
                print(f"❌ Redirigido desde formulario: {form_response.headers.get('Location')}")
            else:
                print(f"❌ Error al acceder al formulario: {form_response.status_code}")
            
            return False
            
        elif response.status_code == 200:
            if 'Por favor, introduzca un nombre de usuario y clave correctos' in response.text:
                print(f"❌ Credenciales incorrectas para {username}")
            else:
                print(f"⚠️ Login devolvió 200 - verificar respuesta")
        else:
            print(f"❌ Error inesperado: {response.status_code}")
    
    print("\n❌ No se pudo autenticar con ninguna credencial")
    return False

if __name__ == "__main__":
    print("🧪 PRUEBA COMPLETA DE LOGIN Y FORMULARIO")
    print("=" * 60)
    success = test_login_and_form()
    if success:
        print("\n🎉 ¡PRUEBA EXITOSA!")
    else:
        print("\n💥 PRUEBA FALLIDA")
