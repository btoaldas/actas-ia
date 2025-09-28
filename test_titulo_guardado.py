#!/usr/bin/env python3
"""
Test específico para verificar que el título del acta se guarda correctamente
"""
import requests
import json
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    return session

def obtener_csrf_token(session, url):
    """Obtener CSRF token de una página"""
    response = session.get(url)
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', response.text)
    if csrf_match:
        return csrf_match.group(1)
    return None

def login_admin(session):
    """Login como superadmin"""
    print("🔐 [LOGIN] Iniciando sesión como superadmin...")
    
    # Obtener CSRF token
    login_url = "http://localhost:8000/admin/login/"
    csrf_token = obtener_csrf_token(session, login_url)
    
    if not csrf_token:
        print("❌ [ERROR] No se pudo obtener CSRF token")
        return False
    
    # Hacer login
    login_data = {
        'username': 'superadmin',
        'password': 'AdminPuyo2025!',
        'csrfmiddlewaretoken': csrf_token,
        'next': '/admin/'
    }
    
    response = session.post(login_url, data=login_data)
    
    if response.status_code == 200 and '/admin/' in response.url:
        print("✅ [LOGIN] Sesión iniciada exitosamente")
        return True
    else:
        print(f"❌ [LOGIN] Error en login: {response.status_code}")
        return False

def obtener_acta_para_prueba(session):
    """Obtener una acta de prueba desde la gestión"""
    print("🔍 [BÚSQUEDA] Buscando acta para prueba...")
    
    try:
        listado_url = "http://localhost:8000/gestion-actas/"
        response = session.get(listado_url)
        
        if response.status_code != 200:
            print(f"❌ [ERROR] No se pudo acceder al listado: {response.status_code}")
            return None
        
        # Buscar enlaces a editor en el HTML
        editor_links = re.findall(r'href="(/gestion-actas/editor/(\d+)/)"', response.text)
        
        if not editor_links:
            print("❌ [ERROR] No se encontraron actas en el listado")
            return None
        
        # Tomar la primera acta
        acta_url, acta_id = editor_links[0]
        print(f"✅ [BÚSQUEDA] Encontrada acta ID {acta_id}")
        return {"id": acta_id, "url": acta_url}
        
    except Exception as e:
        print(f"❌ [ERROR] Error al buscar acta: {e}")
        return None

def probar_guardado_titulo(session, acta_info):
    """Probar el guardado del título específicamente"""
    print(f"📝 [TEST] Probando guardado de título para acta {acta_info['id']}...")
    
    editor_url = f"http://localhost:8000{acta_info['url']}"
    
    # Obtener el formulario del editor
    response = session.get(editor_url)
    if response.status_code != 200:
        print(f"❌ [ERROR] No se pudo acceder al editor: {response.status_code}")
        return False
    
    # Obtener CSRF token
    csrf_token = obtener_csrf_token(session, editor_url)
    if not csrf_token:
        print("❌ [ERROR] No se pudo obtener CSRF token del editor")
        return False
    
    # Obtener título actual
    titulo_match = re.search(r'name="titulo" value="([^"]*)"', response.text)
    titulo_actual = titulo_match.group(1) if titulo_match else "Sin título"
    print(f"📖 [INFO] Título actual: '{titulo_actual}'")
    
    # Crear nuevo título único
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    nuevo_titulo = f"TITULO MODIFICADO {timestamp}"
    
    print(f"🎯 [TEST] Cambiando título a: '{nuevo_titulo}'")
    
    # Preparar datos del formulario
    form_data = {
        'csrfmiddlewaretoken': csrf_token,
        'titulo': nuevo_titulo,
        'contenido_html': '<p>Contenido de prueba para test de título</p>',
        'observaciones': f'Test de título realizado a las {timestamp}'
    }
    
    # Enviar formulario
    post_response = session.post(editor_url, data=form_data)
    
    print(f"📤 [POST] Status: {post_response.status_code}")
    print(f"📤 [POST] URL final: {post_response.url}")
    
    if post_response.status_code == 200:
        # Verificar si hay mensaje de éxito
        if "¡Acta guardada exitosamente!" in post_response.text:
            print("✅ [SUCCESS] Mensaje de éxito encontrado")
            
            # Recargar página para verificar que el título se guardó
            verificacion_response = session.get(editor_url)
            
            if nuevo_titulo in verificacion_response.text:
                print("🎯 [VERIFICACIÓN] ¡Título guardado correctamente!")
                print(f"✅ [RESULTADO] ÉXITO: El título '{nuevo_titulo}' se guardó")
                return True
            else:
                print("❌ [VERIFICACIÓN] El título NO se guardó")
                
                # Buscar qué título aparece ahora
                nuevo_titulo_match = re.search(r'name="titulo" value="([^"]*)"', verificacion_response.text)
                titulo_encontrado = nuevo_titulo_match.group(1) if nuevo_titulo_match else "Sin título"
                print(f"📖 [INFO] Título encontrado después del guardado: '{titulo_encontrado}'")
                return False
        else:
            print("❌ [ERROR] No se encontró mensaje de éxito")
            print("🔍 [DEBUG] Verificando errores en la respuesta...")
            if "error" in post_response.text.lower():
                print("⚠️ [WARNING] Se detectaron errores en la respuesta")
            return False
    else:
        print(f"❌ [ERROR] Error HTTP: {post_response.status_code}")
        return False

def main():
    print("🧪 [TEST] Iniciando test de guardado de título")
    print("=" * 60)
    
    session = create_session()
    
    # Login
    if not login_admin(session):
        return False
    
    # Buscar acta
    acta_info = obtener_acta_para_prueba(session)
    if not acta_info:
        return False
    
    # Probar guardado
    resultado = probar_guardado_titulo(session, acta_info)
    
    print("=" * 60)
    if resultado:
        print("🎉 [RESULTADO FINAL] ¡TEST EXITOSO! El título se guarda correctamente")
    else:
        print("💥 [RESULTADO FINAL] TEST FALLIDO: El título NO se guarda")
    
    return resultado

if __name__ == "__main__":
    main()