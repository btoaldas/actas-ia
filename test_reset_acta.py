#!/usr/bin/env python
"""
Script de prueba para la funcionalidad de reset de actas
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User, AnonymousUser
from apps.pages.views import reset_acta_publicada
from apps.pages.models import ActaMunicipal
from django.contrib.messages.storage.fallback import FallbackStorage

def test_reset_acta():
    # Obtener usuario administrador
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ No se encontró usuario administrador")
        return
        
    print(f"✅ Usuario administrador encontrado: {admin_user.username}")
    
    # Obtener acta de prueba
    acta = ActaMunicipal.objects.filter(pk=6).first()
    if not acta:
        print("❌ No se encontró acta con ID 6")
        return
        
    print(f"✅ Acta encontrada: {acta.numero_acta}")
    print(f"   - Estado antes: activo={acta.activo}, archivo_pdf={bool(acta.archivo_pdf)}")
    
    # Crear factory de request
    factory = RequestFactory()
    
    # Crear request POST simulado
    request = factory.post(f'/acta/{acta.pk}/reset/', {
        'csrfmiddlewaretoken': 'test-token'
    })
    
    # Asignar usuario autenticado
    request.user = admin_user
    
    # Configurar almacenamiento de mensajes
    setattr(request, 'session', {})
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    try:
        # Ejecutar la vista
        print("🔄 Ejecutando reset...")
        response = reset_acta_publicada(request, acta.pk)
        
        # Verificar respuesta
        if response.status_code == 302:  # Redirect esperado
            print("✅ Reset ejecutado correctamente (redirect)")
        else:
            print(f"⚠️ Respuesta inesperada: {response.status_code}")
            
        # Verificar estado del acta después
        acta.refresh_from_db()
        print(f"   - Estado después: activo={acta.activo}, archivo_pdf={bool(acta.archivo_pdf)}")
        
        # Verificar si hay acta en gestor de actas
        try:
            from gestion_actas.models import GestionActa
            acta_gestion = GestionActa.objects.filter(acta_portal=acta).first()
            if acta_gestion:
                print(f"   - Estado gestor: {acta_gestion.estado.nombre}")
            else:
                print("   - No se encontró en gestor de actas")
        except Exception as e:
            print(f"   - Error verificando gestor: {str(e)}")
            
        # Mostrar mensajes
        for message in messages:
            print(f"📝 Mensaje: {message}")
            
    except Exception as e:
        print(f"❌ Error ejecutando reset: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_reset_acta()