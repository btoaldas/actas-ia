#!/usr/bin/env python
"""
Script para probar el sistema SMTP configurado
Sistema de Actas Municipales - Municipio de Pastaza
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import ConfiguracionSMTP, ConfiguracionEmail, LogEnvioEmail
from apps.config_system.smtp_service import smtp_service
from django.contrib.auth.models import User


def mostrar_configuraciones():
    """Muestra las configuraciones SMTP disponibles"""
    print("📧 === CONFIGURACIONES SMTP DISPONIBLES ===")
    print()
    
    configs = ConfiguracionSMTP.objects.all().order_by('prioridad')
    
    if not configs.exists():
        print("❌ No hay configuraciones SMTP creadas")
        return False
    
    for config in configs:
        status = "🟢 ACTIVO" if config.activo else "🔴 INACTIVO"
        default = " ⭐ (Por defecto)" if config.por_defecto else ""
        
        print(f"{status}{default}")
        print(f"   Nombre: {config.nombre}")
        print(f"   Proveedor: {config.get_proveedor_display()}")
        print(f"   Servidor: {config.servidor_smtp}:{config.puerto}")
        print(f"   Usuario: {config.usuario_smtp}")
        print(f"   Email remitente: {config.email_remitente}")
        print(f"   Límite diario: {config.emails_enviados_hoy}/{config.limite_diario}")
        
        if config.ultimo_test:
            test_status = "✅ OK" if config.test_exitoso else "❌ ERROR"
            print(f"   Último test: {test_status} - {config.ultimo_test.strftime('%d/%m/%Y %H:%M')}")
            if config.mensaje_error:
                print(f"   Error: {config.mensaje_error}")
        else:
            print(f"   Estado: 🤷 Sin probar")
        
        print()
    
    return True


def probar_conexiones():
    """Prueba las conexiones SMTP"""
    print("🔍 === PROBANDO CONEXIONES SMTP ===")
    print()
    
    configs_activas = ConfiguracionSMTP.objects.filter(activo=True)
    
    if not configs_activas.exists():
        print("⚠️  No hay configuraciones SMTP activas para probar")
        return
    
    for config in configs_activas:
        print(f"Probando: {config.nombre} ({config.get_proveedor_display()})")
        
        # Usar el método del servicio para probar conexión
        exito, mensaje = smtp_service._probar_conexion_smtp(config)
        
        if exito:
            print(f"   ✅ {mensaje}")
        else:
            print(f"   ❌ {mensaje}")
        print()


def enviar_email_prueba():
    """Envía un email de prueba"""
    print("📨 === ENVIANDO EMAIL DE PRUEBA ===")
    print()
    
    # Buscar un usuario administrador
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user or not admin_user.email:
        print("⚠️  No se encontró un usuario administrador con email")
        email_destino = input("Ingresa un email para la prueba: ").strip()
        if not email_destino:
            print("❌ Email requerido para la prueba")
            return
    else:
        email_destino = admin_user.email
        print(f"📧 Enviando email de prueba a: {email_destino}")
    
    print("🚀 Iniciando envío...")
    
    contenido = """
    <h2>🧪 Prueba Completa del Sistema SMTP</h2>
    <p>Este email confirma que el sistema SMTP del Municipio de Pastaza está funcionando correctamente.</p>
    
    <div style="background-color: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h3>✅ Componentes Verificados:</h3>
        <ul>
            <li>🔗 Conexión al servidor SMTP establecida</li>
            <li>🔐 Autenticación con credenciales exitosa</li>
            <li>📤 Envío de mensaje completado</li>
            <li>🎨 Renderizado de template HTML correcto</li>
            <li>📋 Registro en logs del sistema</li>
            <li>🎯 Sistema de failover operativo</li>
        </ul>
    </div>
    
    <div style="background-color: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
        <h4>📊 Información del Sistema:</h4>
        <p><strong>Aplicación:</strong> {{nombre_aplicacion}}</p>
        <p><strong>Fecha de prueba:</strong> {{fecha_actual}}</p>
        <p><strong>Sistema operativo:</strong> Linux Docker</p>
        <p><strong>Versión:</strong> Sistema de Actas v2.0</p>
    </div>
    
    <div style="background-color: #ecfdf5; padding: 15px; border-radius: 8px; margin-top: 20px;">
        <h4>🎉 ¡Felicitaciones!</h4>
        <p>El sistema de envío de emails está configurado correctamente y listo para usar en:</p>
        <ul>
            <li>📅 Invitaciones a eventos municipales</li>
            <li>📋 Notificaciones de actas</li>
            <li>👥 Comunicaciones con funcionarios</li>
            <li>📢 Alertas del sistema</li>
        </ul>
    </div>
    """
    
    from django.utils import timezone
    variables = {
        'fecha_actual': timezone.now().strftime('%d/%m/%Y %H:%M:%S'),
        'nombre_aplicacion': 'Sistema de Actas Municipales - Pastaza'
    }
    
    # Enviar usando el servicio SMTP
    exito, mensaje = smtp_service.enviar_email(
        destinatario=email_destino,
        asunto="🧪 Prueba Sistema SMTP - Municipio de Pastaza",
        contenido=contenido,
        es_html=True,
        variables_template=variables,
        usuario_solicitante=admin_user
    )
    
    if exito:
        print(f"✅ Email enviado exitosamente: {mensaje}")
        print(f"📧 Revisa la bandeja de entrada de: {email_destino}")
    else:
        print(f"❌ Error enviando email: {mensaje}")
    
    print()


def mostrar_estadisticas():
    """Muestra estadísticas del sistema"""
    print("📊 === ESTADÍSTICAS DEL SISTEMA ===")
    print()
    
    stats = smtp_service.get_estadisticas_envio()
    
    print(f"📤 Emails enviados hoy: {stats['total_enviados_hoy']}")
    print(f"❌ Errores hoy: {stats['total_errores_hoy']}")
    print(f"📈 Emails enviados (7 días): {stats['total_enviados_7_dias']}")
    print(f"📊 Emails enviados (30 días): {stats['total_enviados_30_dias']}")
    print(f"🔧 Proveedores activos: {stats['proveedores_activos']}")
    
    if stats['proveedor_por_defecto']:
        print(f"⭐ Proveedor por defecto: {stats['proveedor_por_defecto'].nombre}")
    else:
        print("⚠️  No hay proveedor por defecto configurado")
    
    print()
    
    # Mostrar uso por proveedor
    print("📈 USO POR PROVEEDOR:")
    for proveedor in stats['emails_por_proveedor']:
        nombre = proveedor['nombre']
        enviados = proveedor['emails_enviados']
        enviados_hoy = proveedor['emails_enviados_hoy']
        limite = proveedor['limite_diario']
        porcentaje = (enviados_hoy / limite * 100) if limite > 0 else 0
        
        print(f"   {nombre}:")
        print(f"     Total enviados: {enviados}")
        print(f"     Hoy: {enviados_hoy}/{limite} ({porcentaje:.1f}%)")
    
    print()


def mostrar_logs_recientes():
    """Muestra los logs más recientes"""
    print("📋 === LOGS RECIENTES ===")
    print()
    
    logs = LogEnvioEmail.objects.order_by('-fecha_creacion')[:10]
    
    if not logs.exists():
        print("ℹ️  No hay logs de envío registrados")
        return
    
    for log in logs:
        estado_icon = {
            'enviado': '✅',
            'error': '❌',
            'pendiente': '⏳',
            'reintentando': '🔄'
        }.get(log.estado, '❓')
        
        proveedor = log.configuracion_smtp.nombre if log.configuracion_smtp else 'Sistema'
        
        print(f"{estado_icon} {log.destinatario}")
        print(f"   Asunto: {log.asunto[:50]}...")
        print(f"   Estado: {log.estado.upper()}")
        print(f"   Proveedor: {proveedor}")
        print(f"   Fecha: {log.fecha_creacion.strftime('%d/%m/%Y %H:%M:%S')}")
        
        if log.mensaje_error:
            print(f"   Error: {log.mensaje_error[:100]}...")
        
        print()


def menu_principal():
    """Menú principal del script"""
    while True:
        print("🚀 === SISTEMA SMTP MUNICIPIO DE PASTAZA ===")
        print("   Sistema de Actas Municipales")
        print("=" * 50)
        print()
        print("Opciones disponibles:")
        print("1. 📧 Ver configuraciones SMTP")
        print("2. 🔍 Probar conexiones SMTP")
        print("3. 📨 Enviar email de prueba")
        print("4. 📊 Ver estadísticas")
        print("5. 📋 Ver logs recientes")
        print("6. 🔄 Ejecutar todas las pruebas")
        print("0. ❌ Salir")
        print()
        
        try:
            opcion = input("Selecciona una opción (0-6): ").strip()
            print()
            
            if opcion == '0':
                print("👋 ¡Hasta pronto!")
                break
            elif opcion == '1':
                mostrar_configuraciones()
            elif opcion == '2':
                probar_conexiones()
            elif opcion == '3':
                enviar_email_prueba()
            elif opcion == '4':
                mostrar_estadisticas()
            elif opcion == '5':
                mostrar_logs_recientes()
            elif opcion == '6':
                print("🔄 === EJECUTANDO TODAS LAS PRUEBAS ===")
                print()
                if mostrar_configuraciones():
                    probar_conexiones()
                    enviar_email_prueba()
                    mostrar_estadisticas()
                    mostrar_logs_recientes()
            else:
                print("❌ Opción inválida")
            
            input("\n👆 Presiona Enter para continuar...")
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            input("\n👆 Presiona Enter para continuar...")


def main():
    """Función principal"""
    print("🚀 === INICIANDO PRUEBAS SMTP ===")
    print("   Sistema de Actas Municipales")
    print("   Municipio de Pastaza - Puyo, Ecuador")
    print("=" * 50)
    print()
    
    try:
        # Verificar configuración inicial
        config_count = ConfiguracionSMTP.objects.count()
        if config_count == 0:
            print("⚠️  No hay configuraciones SMTP. Ejecuta 'python configurar_smtp.py' primero.")
            return
        
        print(f"✅ Encontradas {config_count} configuracion(es) SMTP")
        print()
        
        # Ejecutar menú interactivo
        menu_principal()
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
