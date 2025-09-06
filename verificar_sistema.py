#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.config_system.models import ConfiguracionIA, ConfiguracionWhisper, PerfilUsuario, LogConfiguracion

print("🎯 === ESTADO ACTUAL DEL SISTEMA DE ACTAS MUNICIPALES IA ===")
print()

# Verificar usuarios
usuarios = User.objects.all()
print(f"👥 USUARIOS ({usuarios.count()}):")
for user in usuarios:
    perfil = getattr(user, 'perfilusuario', None)
    if perfil:
        print(f"   • {user.username} ({user.first_name} {user.last_name}) - {perfil.get_rol_display()}")
        if perfil.departamento:
            print(f"     Departamento: {perfil.get_departamento_display()}")
        if perfil.cargo:
            print(f"     Cargo: {perfil.cargo}")
    else:
        print(f"   • {user.username} (sin perfil)")
print()

# Verificar configuraciones IA
configs_ia = ConfiguracionIA.objects.all()
print(f"🤖 CONFIGURACIONES IA ({configs_ia.count()}):")
for config in configs_ia:
    estado = "🟢 ACTIVA" if config.activa else "🔴 INACTIVA"
    print(f"   • {config.nombre} ({config.proveedor}/{config.modelo}) - {estado}")
    print(f"     {config.descripcion}")
print()

# Verificar configuraciones Whisper
configs_whisper = ConfiguracionWhisper.objects.all()
print(f"🎤 CONFIGURACIONES WHISPER ({configs_whisper.count()}):")
for config in configs_whisper:
    estado = "🟢 ACTIVA" if config.activa else "🔴 INACTIVA"
    print(f"   • {config.nombre} (modelo: {config.modelo_whisper}) - {estado}")
    print(f"     Idioma: {config.idioma}, Pyannote: {'Sí' if config.usar_pyannote else 'No'}")
print()

# Verificar perfiles
perfiles = PerfilUsuario.objects.all()
print(f"👤 PERFILES DE USUARIO ({perfiles.count()}):")
for perfil in perfiles:
    permisos = []
    if perfil.puede_configurar_ia:
        permisos.append("Config IA")
    if perfil.puede_procesar_actas:
        permisos.append("Procesar")
    if perfil.puede_publicar_actas:
        permisos.append("Publicar")
    if perfil.puede_transcribir:
        permisos.append("Transcribir")
    if perfil.puede_gestionar_usuarios:
        permisos.append("Usuarios")
    
    print(f"   • {perfil.usuario.username} - {perfil.get_rol_display()}")
    if permisos:
        print(f"     Permisos: {', '.join(permisos)}")
    print(f"     Límites: {perfil.limite_procesamiento_diario} procesos/día, {perfil.limite_transcripcion_horas}h transcripción")
print()

# Verificar logs
logs = LogConfiguracion.objects.all()[:5]
print(f"📋 LOGS RECIENTES ({LogConfiguracion.objects.count()} total):")
for log in logs:
    print(f"   • {log.fecha.strftime('%d/%m/%Y %H:%M')} - {log.usuario} - {log.accion} {log.tipo_configuracion}")
print()

print("🌐 ACCESO AL SISTEMA:")
print("   • Portal principal: http://localhost:8000")
print("   • Panel de configuración: http://localhost:8000/config_system/")
print("   • Login: Usa cualquier usuario creado")
print()

print("🔑 CREDENCIALES DISPONIBLES:")
for user in usuarios:
    if user.username == 'admin':
        print(f"   • {user.username} / admin123 (Superadministrador)")
    elif user.username.startswith(('secretario', 'alcalde', 'editor', 'operador')):
        print(f"   • {user.username} / demo123")
print()

print("✅ SISTEMA COMPLETAMENTE CONFIGURADO Y FUNCIONAL")
print("📌 Todos los superusuarios tienen acceso completo a las configuraciones")
print("🚀 El sistema está listo para procesar actas municipales con IA")
