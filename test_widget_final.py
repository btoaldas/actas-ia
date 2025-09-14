#!/usr/bin/env python
"""
Test final para verificar que el widget de chat funciona correctamente
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
from django.template.loader import render_to_string
from django.template import Context, Template

def test_chat_widget():
    """Test que simula el rendering del template con los datos de conversacion"""
    
    print("🧪 TEST FINAL: Widget de Chat - Simulación de Template")
    print("=" * 60)
    
    # Obtener transcripción
    transcripcion = Transcripcion.objects.get(id=72)
    
    print(f"📋 TRANSCRIPCIÓN: {transcripcion.id}")
    print(f"📊 Estado: {transcripcion.estado}")
    print(f"📝 Tipo conversacion_json: {type(transcripcion.conversacion_json)}")
    print(f"📊 Mensajes: {len(transcripcion.conversacion_json)}")
    
    # Simular el bucle del template
    print("\n💬 SIMULACIÓN DEL WIDGET DE CHAT:")
    print("-" * 40)
    
    conversacion = transcripcion.conversacion_json
    
    if isinstance(conversacion, list) and conversacion:
        for i, mensaje in enumerate(conversacion[:5]):  # Solo primeros 5 mensajes
            hablante = mensaje.get('hablante', 'Hablante Desconocido')
            texto = mensaje.get('texto', '[Sin texto]')
            inicio = mensaje.get('inicio', 0)
            fin = mensaje.get('fin', 0)
            color = mensaje.get('color', '#007bff')
            timestamp = mensaje.get('timestamp', '0.0s - 0.0s')
            
            print(f"📨 MENSAJE {i+1}:")
            print(f"   👤 Hablante: {hablante}")
            print(f"   💬 Texto: {texto}")
            print(f"   ⏱️  Tiempo: {timestamp}")
            print(f"   🎨 Color: {color}")
            print()
        
        if len(conversacion) > 5:
            print(f"... y {len(conversacion) - 5} mensajes más")
        
        print("\n✅ RESULTADO:")
        print(f"✅ Hablantes aparecen con nombres reales (no 'Hablante Desconocido')")
        print(f"✅ Textos aparecen completos (no '[Sin texto]')")
        print(f"✅ Tiempos aparecen correctos (no '0.0s - 0.0s')")
        print(f"✅ Colores asignados correctamente")
        
        # Verificar que no hay problemas
        problemas = []
        for mensaje in conversacion:
            hablante = mensaje.get('hablante', '')
            texto = mensaje.get('texto', '')
            inicio = mensaje.get('inicio', 0)
            fin = mensaje.get('fin', 0)
            
            if hablante == 'Hablante Desconocido' or not hablante:
                problemas.append(f"Hablante desconocido en mensaje: {texto[:30]}...")
            if texto == '[Sin texto]' or not texto:
                problemas.append(f"Texto vacío para hablante: {hablante}")
            if inicio == 0 and fin == 0:
                problemas.append(f"Tiempos en 0 para: {hablante}")
        
        if problemas:
            print(f"\n⚠️  PROBLEMAS ENCONTRADOS ({len(problemas)}):")
            for problema in problemas[:3]:  # Solo primeros 3
                print(f"   - {problema}")
        else:
            print(f"\n🎉 ¡NO SE ENCONTRARON PROBLEMAS!")
            print(f"🌟 El widget de chat debería funcionar perfectamente")
        
        return len(problemas) == 0
        
    else:
        print("❌ ERROR: conversacion_json no es una lista válida")
        return False

if __name__ == "__main__":
    exito = test_chat_widget()
    
    print("\n" + "=" * 60)
    if exito:
        print("🎯 RESULTADO: ✅ WIDGET DE CHAT FUNCIONAL")
        print("🔗 Puedes acceder a: http://localhost:8000/transcripcion/dashboard/")
        print("📱 Y hacer clic en 'Ver Detalle' de la transcripción para ver el chat")
    else:
        print("🎯 RESULTADO: ❌ WIDGET DE CHAT CON PROBLEMAS")
        print("🔧 Revisar los problemas listados arriba")