#!/usr/bin/env python
"""
Test específico para simular POST del navegador desde el editor
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from gestion_actas.models import GestionActa
import re

def test_post_formulario_editor():
    """Simular exactamente lo que hace el navegador al enviar el formulario"""
    
    print("🌐 TEST POST DEL FORMULARIO DE EDITOR")
    print("=" * 50)
    
    # Configurar cliente de prueba
    client = Client()
    
    # Hacer login
    user = User.objects.get(username='superadmin')
    client.force_login(user)
    
    # Obtener acta para probar
    acta = GestionActa.objects.order_by('-id').first()
    print(f"📋 Probando acta ID: {acta.pk}")
    print(f"   - Contenido antes: {len(acta.contenido_editado or '')} chars")
    
    # Obtener la página del editor para conseguir el CSRF token
    response = client.get(f'/gestion-actas/acta/{acta.pk}/editar/')
    
    if response.status_code != 200:
        print(f"❌ Error obteniendo editor: HTTP {response.status_code}")
        return False
    
    # Extraer CSRF token
    content = response.content.decode('utf-8')
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
    if not csrf_match:
        print("❌ No se pudo obtener CSRF token")
        return False
    
    csrf_token = csrf_match.group(1)
    print(f"✅ CSRF token obtenido: {csrf_token[:20]}...")
    
    # Contenido de prueba HTML
    contenido_test = """
    <h1>TEST POST FORMULARIO NAVEGADOR</h1>
    <h2>Simulación Completa del Navegador</h2>
    <p>Este contenido se está enviando via POST HTTP exactamente como lo haría el navegador cuando el usuario hace clic en <strong>"Guardar Cambios"</strong>.</p>
    
    <h3>Información de la Prueba:</h3>
    <ul>
        <li>✅ CSRF Token incluido</li>
        <li>✅ Usuario autenticado (superadmin)</li>
        <li>✅ Contenido HTML con formato</li>
        <li>✅ Simulación completa de POST</li>
    </ul>
    
    <blockquote>
        <p><em>"Esta es una prueba automatizada para verificar que el guardado desde el editor funciona correctamente."</em></p>
        <footer>— Test automatizado, 28 de septiembre de 2025</footer>
    </blockquote>
    
    <h3>Estado:</h3>
    <p class="text-success"><strong>✅ READY TO SAVE</strong></p>
    """
    
    # Simular POST del formulario (exactamente como el navegador)
    post_data = {
        'csrfmiddlewaretoken': csrf_token,
        'titulo': acta.acta_generada.titulo if acta.acta_generada else f"Acta Manual #{acta.pk}",
        'contenido_html': contenido_test.strip(),
        'observaciones': 'Test automatizado de POST desde navegador simulado'
    }
    
    print(f"🚀 Enviando POST con {len(contenido_test)} chars de contenido...")
    
    # Realizar POST
    response = client.post(
        f'/gestion-actas/acta/{acta.pk}/editar/', 
        data=post_data,
        follow=True  # Seguir redirects
    )
    
    print(f"📊 Respuesta HTTP: {response.status_code}")
    
    if response.status_code == 200:
        # Verificar si hubo redirect (éxito)
        if response.redirect_chain:
            print(f"✅ Redirect detectado: {response.redirect_chain}")
            print("✅ Esto indica que el POST fue exitoso")
        
        # Verificar mensajes de éxito
        messages = list(response.context['messages']) if response.context and 'messages' in response.context else []
        for message in messages:
            print(f"💬 Mensaje: {message}")
        
        # Verificar en base de datos
        acta.refresh_from_db()
        contenido_guardado = acta.contenido_editado or ''
        
        print(f"📊 Verificación en BD:")
        print(f"   - Contenido después: {len(contenido_guardado)} chars")
        
        if "TEST POST FORMULARIO NAVEGADOR" in contenido_guardado:
            print(f"🎉 ¡ÉXITO! El contenido se guardó correctamente via POST")
            
            # Preview del contenido guardado
            preview = contenido_guardado[:150] + "..." if len(contenido_guardado) > 150 else contenido_guardado
            print(f"\n📄 Preview del contenido guardado:")
            print(f"   {preview}")
            
            return True
        else:
            print(f"❌ FALLO: El contenido no se guardó en BD")
            print(f"   Contenido actual: {contenido_guardado[:100]}...")
            return False
    else:
        print(f"❌ Error HTTP: {response.status_code}")
        if response.content:
            print(f"   Contenido de error: {response.content.decode('utf-8')[:500]}...")
        return False

if __name__ == '__main__':
    print("🚀 INICIANDO TEST POST DEL FORMULARIO")
    print("=" * 60)
    
    try:
        exito = test_post_formulario_editor()
        
        print(f"\n" + "=" * 60)
        if exito:
            print(f"🎉 TEST EXITOSO - El formulario POST funciona correctamente!")
            print(f"   ✅ El problema NO está en el backend")
            print(f"   ✅ El guardado funciona perfectamente") 
            print(f"   💡 El problema debe estar en el frontend/JavaScript")
        else:
            print(f"❌ TEST FALLIDO - Hay problemas con el POST")
            print(f"   🔍 Revisar la vista, validaciones o modelo")
    
    except Exception as e:
        print(f"❌ ERROR EN TEST: {str(e)}")
        import traceback
        traceback.print_exc()