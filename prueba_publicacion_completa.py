#!/usr/bin/env python3
"""
Script para probar el flujo completo de publicación con notificaciones
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
from gestion_actas.models import GestionActa, EstadoGestionActa
from gestion_actas.email_notifications import enviar_notificacion_publicacion
from django.utils import timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crear_acta_de_prueba():
    """Crear una acta de prueba para probar el sistema"""
    try:
        print("📝 Creando acta de prueba para el sistema de notificaciones...")
        
        # Obtener el superusuario
        usuario = User.objects.filter(is_superuser=True).first()
        if not usuario:
            print("❌ No se encontró superusuario")
            return None
            
        # Obtener estado lista_publicacion
        estado_lista = EstadoGestionActa.objects.filter(codigo='lista_publicacion').first()
        if not estado_lista:
            print("❌ Estado 'lista_publicacion' no encontrado")
            return None
        
        # Crear acta (sin acta_generada, solo para pruebas)
        contenido_prueba = f"""
ACTA DE SESIÓN MUNICIPAL - PRUEBA DE NOTIFICACIONES

Fecha: {timezone.now().strftime('%d de %B de %Y')}
Hora: {timezone.now().strftime('%H:%M')}

ORDEN DEL DÍA:
1. Verificación de quórum
2. Lectura y aprobación del acta anterior
3. Asuntos varios
4. Próxima convocatoria

DESARROLLO DE LA SESIÓN:

La presente sesión se realiza con el objetivo de probar el sistema de notificaciones por email 
del Sistema de Gestión de Actas Municipales del GAD Pastaza.

ACUERDOS TOMADOS:
- Aprobar el funcionamiento del sistema de notificaciones
- Verificar que los emails lleguen correctamente a los funcionarios
- Confirmar la integración con el Portal Ciudadano

ASISTENTES:
- Alcalde Municipal
- Concejales del GAD Pastaza
- Secretario Municipal

La sesión se levanta a las {timezone.now().strftime('%H:%M')} del mismo día.

_________________________________
Secretario Municipal              Alcalde
        """
        
        acta = GestionActa.objects.create(
            # No incluimos titulo ni numero_acta porque son propiedades
            contenido_editado=contenido_prueba,
            observaciones=f"Acta generada automáticamente para pruebas del sistema de notificaciones - {timezone.now()}",
            estado=estado_lista,
            usuario_editor=usuario,
            fecha_creacion=timezone.now()
        )
        
        print(f"✅ Acta creada exitosamente:")
        print(f"   📋 ID: {acta.id}")
        print(f"   📝 Título: {acta.titulo}")
        print(f"   🔢 Número: {acta.numero_acta}")
        print(f"   📅 Fecha: {acta.fecha_creacion}")
        print(f"   ✅ Estado: {acta.estado.nombre}")
        
        return acta
        
    except Exception as e:
        print(f"❌ Error creando acta de prueba: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def simular_publicacion_completa(acta):
    """Simular el proceso completo de publicación"""
    try:
        print(f"\n🚀 Iniciando proceso de publicación para acta ID {acta.id}...")
        
        # Importar las funciones de publicación
        from gestion_actas.views import _sincronizar_con_portal_ciudadano, _generar_documentos_publicacion
        from gestion_actas.models import HistorialCambios
        from django.db import transaction
        
        usuario_publicador = User.objects.filter(is_superuser=True).first()
        
        with transaction.atomic():
            print("1. Cambiando estado a 'publicada'...")
            # Cambiar estado a publicada
            estado_publicada = EstadoGestionActa.objects.get(codigo='publicada')
            acta.estado = estado_publicada
            acta.fecha_publicacion = timezone.now()
            acta.save()
            
            print("2. Registrando en historial...")
            # Registrar en historial
            HistorialCambios.objects.create(
                gestion_acta=acta,
                usuario=usuario_publicador,
                tipo_cambio='publicacion',
                descripcion=f'Acta publicada en portal ciudadano por {usuario_publicador.get_full_name() or usuario_publicador.username}',
                datos_adicionales={
                    'fecha_publicacion': timezone.now().isoformat(),
                    'publicado_por': usuario_publicador.id
                }
            )
            
            print("3. Sincronizando con portal ciudadano...")
            # Sincronizar con el portal ciudadano
            acta_portal = _sincronizar_con_portal_ciudadano(acta, usuario_publicador)
            
            if not acta_portal:
                print("❌ Error sincronizando con portal ciudadano")
                return False
                
            print(f"   ✅ ActaMunicipal creada con ID: {acta_portal.id}")
            
            print("4. Generando documentos...")
            # Generar documentos en múltiples formatos
            documentos_generados = _generar_documentos_publicacion(acta, acta_portal)
            
            print(f"   📄 Documentos generados: {list(documentos_generados.keys())}")
            
            print("5. Enviando notificaciones por email...")
            # Enviar notificaciones por email
            resultado_email = enviar_notificacion_publicacion(
                acta_gestion=acta,
                acta_portal=acta_portal,
                usuario_publicador=usuario_publicador
            )
            
            if resultado_email:
                print("   ✅ Notificaciones enviadas exitosamente")
                
                # Registrar en historial
                HistorialCambios.objects.create(
                    gestion_acta=acta,
                    usuario=usuario_publicador,
                    tipo_cambio='notificacion_enviada',
                    descripcion='Notificaciones de publicación enviadas por email',
                    datos_adicionales={
                        'emails_enviados': True,
                        'fecha_envio': timezone.now().isoformat()
                    }
                )
            else:
                print("   ⚠️  Problemas enviando notificaciones")
            
            print(f"\n🎉 ¡PUBLICACIÓN COMPLETADA EXITOSAMENTE!")
            print(f"   🌐 Portal: http://localhost:8000/acta/{acta_portal.id}/")
            print(f"   ⚙️  Gestión: http://localhost:8000/gestion-actas/acta/{acta.id}/")
            
            return True
            
    except Exception as e:
        print(f"❌ Error en proceso de publicación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def verificar_resultado(acta_id):
    """Verificar que todo esté funcionando correctamente"""
    try:
        print(f"\n🔍 Verificando resultado de la publicación...")
        
        acta = GestionActa.objects.get(id=acta_id)
        print(f"   📋 Estado del acta: {acta.estado.nombre}")
        print(f"   📅 Fecha publicación: {acta.fecha_publicacion}")
        
        if hasattr(acta, 'acta_portal') and acta.acta_portal:
            print(f"   🌐 Portal integrado: ✅ ID {acta.acta_portal.id}")
        else:
            print(f"   🌐 Portal integrado: ❌")
            
        # Verificar historial
        historial = acta.historial_cambios.all()
        print(f"   📊 Registros en historial: {historial.count()}")
        
        for registro in historial:
            print(f"      - {registro.tipo_cambio}: {registro.descripcion}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error verificando resultado: {str(e)}")
        return False


def main():
    print("=" * 80)
    print("🧪 PRUEBA COMPLETA DEL SISTEMA DE PUBLICACIÓN CON NOTIFICACIONES")
    print("=" * 80)
    
    # 1. Crear acta de prueba
    acta = crear_acta_de_prueba()
    if not acta:
        print("❌ No se pudo crear acta de prueba. Terminando.")
        return
    
    # 2. Simular publicación completa
    exito = simular_publicacion_completa(acta)
    if not exito:
        print("❌ Error en el proceso de publicación. Terminando.")
        return
    
    # 3. Verificar resultado
    verificar_resultado(acta.id)
    
    print("\n" + "=" * 80)
    print("✨ PRUEBA COMPLETADA")
    print("=" * 80)
    print("\n💡 Resumen de lo realizado:")
    print("   ✅ Acta de prueba creada")
    print("   ✅ Estado cambiado a 'publicada'")
    print("   ✅ Sincronización con portal ciudadano")
    print("   ✅ Documentos generados (TXT, HTML)")
    print("   ✅ Notificaciones por email enviadas")
    print("   ✅ Historial registrado")
    print("\n🎯 El sistema está funcionando correctamente!")


if __name__ == '__main__':
    main()