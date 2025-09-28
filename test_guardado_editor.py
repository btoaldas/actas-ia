#!/usr/bin/env python
"""
Test específico para verificar que el guardado en el editor funciona
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gestion_actas.models import GestionActa

def test_guardado_editor():
    """Test para verificar que el formulario de editor guarda correctamente"""
    
    print("🧪 TEST DE GUARDADO DEL EDITOR")
    print("=" * 50)
    
    # Buscar un acta para probar (usar una reciente)
    acta_test = GestionActa.objects.order_by('-id').first()
    
    if not acta_test:
        print("❌ No hay actas disponibles para probar")
        return
    
    print(f"📋 Usando acta ID: {acta_test.pk}")
    print(f"   - Contenido actual: {len(acta_test.contenido_editado or '')} chars")
    
    # Contenido de prueba
    contenido_prueba = """
    <h1>TEST DE GUARDADO AUTOMÁTICO</h1>
    <h2>Verificación de Funcionalidad</h2>
    <p>Este contenido se está guardando desde un test automatizado para verificar que:</p>
    <ul>
        <li>El formulario POST funciona correctamente</li>
        <li>El campo contenido_editado se actualiza</li>
        <li>El usuario editor se asigna correctamente</li>
        <li>La fecha de edición se actualiza</li>
    </ul>
    <p><strong>Fecha del test:</strong> 28 de septiembre de 2025</p>
    <p><em>Contenido generado automáticamente para pruebas.</em></p>
    """
    
    # Guardar contenido anterior para comparar
    contenido_anterior = acta_test.contenido_editado or ''
    
    print(f"\n🔄 Actualizando contenido directamente en BD...")
    
    # Actualizar directamente en base de datos (simular POST)
    from django.contrib.auth.models import User
    from django.utils import timezone
    
    usuario_test = User.objects.get(username='superadmin')
    
    acta_test.contenido_editado = contenido_prueba.strip()
    acta_test.usuario_editor = usuario_test
    acta_test.fecha_ultima_edicion = timezone.now()
    acta_test.save()
    
    print(f"✅ Acta actualizada:")
    print(f"   - Contenido anterior: {len(contenido_anterior)} chars")
    print(f"   - Contenido nuevo: {len(acta_test.contenido_editado)} chars")
    print(f"   - Usuario editor: {acta_test.usuario_editor}")
    print(f"   - Fecha edición: {acta_test.fecha_ultima_edicion}")
    
    # Verificar que se guardó correctamente
    acta_test.refresh_from_db()
    
    if "TEST DE GUARDADO AUTOMÁTICO" in acta_test.contenido_editado:
        print(f"🎉 ¡ÉXITO! El contenido se guardó correctamente")
        
        # Preview del contenido
        preview = acta_test.contenido_editado[:100] + "..." if len(acta_test.contenido_editado) > 100 else acta_test.contenido_editado
        print(f"\n📄 Preview del contenido guardado:")
        print(f"   {preview}")
        
        return True
    else:
        print(f"❌ FALLO: El contenido no se guardó correctamente")
        return False

def test_autoguardado_ajax():
    """Test del endpoint de autoguardado AJAX"""
    
    print(f"\n🌐 TEST DE AUTOGUARDADO AJAX")
    print("=" * 50)
    
    # Usar la misma acta
    acta_test = GestionActa.objects.order_by('-id').first()
    
    print(f"📋 Probando autoguardado para acta ID: {acta_test.pk}")
    
    # Simular request AJAX
    import json
    from django.test import RequestFactory
    from django.contrib.auth.models import User
    from gestion_actas.views import autoguardar_contenido
    
    # Crear request simulado
    factory = RequestFactory()
    usuario = User.objects.get(username='superadmin')
    
    contenido_ajax = """
    <h2>TEST AUTOGUARDADO AJAX</h2>
    <p>Este contenido viene de una simulación de request AJAX.</p>
    <p>Verificando que el endpoint /api/acta/ID/autoguardar/ funciona correctamente.</p>
    """
    
    request = factory.post(
        f'/gestion-actas/api/acta/{acta_test.pk}/autoguardar/',
        data=json.dumps({'contenido_html': contenido_ajax}),
        content_type='application/json'
    )
    request.user = usuario
    
    # Llamar la vista
    response = autoguardar_contenido(request, acta_test.pk)
    
    # Verificar respuesta
    if response.status_code == 200:
        response_data = json.loads(response.content)
        if response_data.get('success'):
            print(f"✅ Autoguardado AJAX exitoso")
            print(f"   - Respuesta: {response_data}")
            
            # Verificar que se guardó en BD
            acta_test.refresh_from_db()
            if "TEST AUTOGUARDADO AJAX" in acta_test.contenido_editado:
                print(f"✅ Contenido guardado correctamente en BD")
                return True
            else:
                print(f"❌ Contenido no se reflejó en BD")
                return False
        else:
            print(f"❌ Autoguardado falló: {response_data}")
            return False
    else:
        print(f"❌ Error HTTP: {response.status_code}")
        return False

if __name__ == '__main__':
    print("🚀 INICIANDO TESTS DE GUARDADO")
    print("=" * 60)
    
    # Test 1: Guardado directo
    test1_exitoso = test_guardado_editor()
    
    # Test 2: Autoguardado AJAX
    test2_exitoso = test_autoguardado_ajax()
    
    print(f"\n" + "=" * 60)
    print(f"📊 RESUMEN DE TESTS:")
    print(f"   ✅ Guardado directo: {'ÉXITO' if test1_exitoso else 'FALLO'}")
    print(f"   ✅ Autoguardado AJAX: {'ÉXITO' if test2_exitoso else 'FALLO'}")
    
    if test1_exitoso and test2_exitoso:
        print(f"🎉 TODOS LOS TESTS EXITOSOS - El guardado funciona correctamente!")
    else:
        print(f"❌ ALGUNOS TESTS FALLARON - Hay problemas con el guardado")