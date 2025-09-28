#!/usr/bin/env python3
"""
Script de prueba para el sistema de notificaciones por email
Prueba la funcionalidad completa de envío de notificaciones al publicar actas
"""

import os
import sys
import django
from pathlib import Path

# Configuración del entorno Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from gestion_actas.models import GestionActa
from gestion_actas.email_notifications import (
    enviar_notificacion_publicacion, 
    probar_configuracion_smtp,
    obtener_destinatarios_notificacion,
    enviar_notificacion_test
)
import logging

# Configurar logging para ver los detalles
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=" * 70)
    print("🔔 PRUEBA DEL SISTEMA DE NOTIFICACIONES POR EMAIL")
    print("=" * 70)
    
    # 1. Verificar configuración SMTP
    print("\n1️⃣ Verificando configuración SMTP...")
    print("-" * 50)
    try:
        # Nota: Esta función intentará enviar un email de prueba
        # Cambiar el email de destino en la función si es necesario
        configuracion_ok = probar_configuracion_smtp()
        print(f"Resultado: {'✅ OK' if configuracion_ok else '❌ ERROR'}")
    except Exception as e:
        print(f"❌ Error en configuración SMTP: {str(e)}")
    
    # 2. Verificar destinatarios
    print("\n2️⃣ Verificando destinatarios de notificaciones...")
    print("-" * 50)
    try:
        destinatarios = obtener_destinatarios_notificacion()
        print(f"📧 Total destinatarios encontrados: {len(destinatarios)}")
        
        for i, destinatario in enumerate(destinatarios, 1):
            print(f"   {i}. {destinatario['nombre']} ({destinatario['cargo']})")
            print(f"      📧 {destinatario['email']}")
            
        if not destinatarios:
            print("⚠️  No se encontraron destinatarios. Revisar configuración de usuarios.")
            
    except Exception as e:
        print(f"❌ Error obteniendo destinatarios: {str(e)}")
    
    # 3. Buscar acta publicada para prueba
    print("\n3️⃣ Buscando actas publicadas...")
    print("-" * 50)
    try:
        actas_publicadas = GestionActa.objects.filter(
            estado__codigo='publicada',
            acta_portal__isnull=False
        ).select_related('acta_portal', 'usuario_editor').order_by('-fecha_publicacion')
        
        print(f"📋 Actas publicadas encontradas: {actas_publicadas.count()}")
        
        if actas_publicadas.exists():
            acta_test = actas_publicadas.first()
            print(f"   ✅ Usando acta: {acta_test.titulo}")
            print(f"   📅 Publicada: {acta_test.fecha_publicacion}")
            print(f"   🆔 ID Gestion: {acta_test.id}")
            print(f"   🌐 ID Portal: {acta_test.acta_portal.id}")
            
            # 4. Probar notificación con acta real
            print("\n4️⃣ Enviando notificación de prueba...")
            print("-" * 50)
            
            usuario_test = acta_test.usuario_editor or User.objects.filter(is_superuser=True).first()
            
            try:
                resultado = enviar_notificacion_publicacion(
                    acta_gestion=acta_test,
                    acta_portal=acta_test.acta_portal,
                    usuario_publicador=usuario_test
                )
                
                if resultado:
                    print("✅ Notificación enviada exitosamente")
                else:
                    print("❌ Error enviando notificación")
                    
            except Exception as e:
                print(f"❌ Error en notificación de prueba: {str(e)}")
                
        else:
            print("⚠️  No se encontraron actas publicadas para probar.")
            print("   💡 Publica una acta primero desde el sistema web.")
            
    except Exception as e:
        print(f"❌ Error buscando actas: {str(e)}")
    
    # 5. Información adicional
    print("\n5️⃣ Información del sistema...")
    print("-" * 50)
    try:
        total_usuarios = User.objects.count()
        usuarios_con_email = User.objects.exclude(email='').count()
        superusuarios = User.objects.filter(is_superuser=True).count()
        
        print(f"👥 Total usuarios: {total_usuarios}")
        print(f"📧 Usuarios con email: {usuarios_con_email}")
        print(f"🔑 Superusuarios: {superusuarios}")
        
        # Verificar configuración SMTP desde Django settings
        from django.conf import settings
        print(f"📤 EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'No configurado')}")
        print(f"📧 DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'No configurado')}")
        
    except Exception as e:
        print(f"❌ Error obteniendo información del sistema: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✨ PRUEBA COMPLETADA")
    print("=" * 70)
    print("\n💡 Notas:")
    print("   - Para probar envío real, configure emails válidos en los usuarios")
    print("   - Revise los logs de Django para más detalles")
    print("   - El sistema usa la configuración SMTP del GAD Pastaza (quipux@puyo.gob.ec)")
    print("   - En producción, mover credenciales SMTP a variables de entorno")


def prueba_rapida_acta(acta_id):
    """Función auxiliar para probar una acta específica"""
    try:
        print(f"\n🧪 PRUEBA RÁPIDA - ACTA ID: {acta_id}")
        print("-" * 40)
        
        resultado = enviar_notificacion_test(acta_id)
        
        if resultado:
            print("✅ Prueba exitosa")
        else:
            print("❌ Prueba fallida")
            
        return resultado
        
    except Exception as e:
        print(f"❌ Error en prueba rápida: {str(e)}")
        return False


if __name__ == '__main__':
    # Ejecutar prueba completa por defecto
    if len(sys.argv) > 1:
        # Si se proporciona un ID de acta, hacer prueba rápida
        try:
            acta_id = int(sys.argv[1])
            prueba_rapida_acta(acta_id)
        except ValueError:
            print("❌ El ID del acta debe ser un número")
    else:
        # Prueba completa del sistema
        main()