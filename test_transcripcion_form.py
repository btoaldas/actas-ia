#!/usr/bin/env python
"""
Script simple para probar el formulario de transcripción via POST
"""
import requests
import json

def test_transcripcion_form():
    """Prueba el formulario de transcripción"""
    
    # URL del formulario 
    url = "http://localhost:8000/transcripcion/configurar/6/"
    
    # Datos del formulario (simulando lo que enviaría el botón)
    form_data = {
        'configuracion_id': '1',  # ID de configuración (o 'custom' para personalizada)
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
    
    try:
        # Primero obtener la página para el token CSRF
        session = requests.Session()
        response = session.get(url)
        
        if response.status_code == 200:
            print("✅ Página de configuración cargada correctamente")
            
            # Extraer token CSRF con regex simple
            import re
            csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', response.text)
            if csrf_match:
                csrf_token = csrf_match.group(1)
                form_data['csrfmiddlewaretoken'] = csrf_token
                print(f"✅ Token CSRF obtenido: {csrf_token[:10]}...")
            else:
                print("⚠️ No se encontró token CSRF")
            
            # Enviar POST
            post_response = session.post(url, data=form_data)
            
            print(f"📝 Respuesta POST: Status {post_response.status_code}")
            print(f"📝 URL final: {post_response.url}")
            
            if post_response.status_code == 302:
                print("✅ Redirección exitosa - El formulario funcionó")
                print(f"   Redirigido a: {post_response.headers.get('Location')}")
            elif post_response.status_code == 200:
                print("⚠️ Página recargada - Revisar si hay errores en el formulario")
                if 'error' in post_response.text.lower():
                    print("❌ Se detectaron errores en la respuesta")
            else:
                print(f"❌ Error inesperado: {post_response.status_code}")
                
        else:
            print(f"❌ Error al cargar página: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en la prueba: {str(e)}")

if __name__ == "__main__":
    print("🧪 PROBANDO FORMULARIO DE TRANSCRIPCIÓN")
    print("=" * 50)
    test_transcripcion_form()
