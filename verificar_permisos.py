#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.config_system.models import PerfilUsuario, PermisosDetallados

print("🔍 === VERIFICACIÓN DE PERFILES Y PERMISOS ===")
print()

# Verificar todos los usuarios y sus permisos
usuarios = User.objects.all().order_by('username')

for user in usuarios:
    try:
        perfil = user.perfilusuario
        print(f"👤 {user.username} ({user.first_name} {user.last_name})")
        print(f"   📋 Rol: {perfil.get_rol_display()}")
        if perfil.departamento:
            print(f"   🏢 Departamento: {perfil.get_departamento_display()}")
        if perfil.cargo:
            print(f"   💼 Cargo: {perfil.cargo}")
        
        # Verificar permisos detallados
        if hasattr(perfil, 'permisos_detallados'):
            permisos = perfil.permisos_detallados
            print(f"   🔑 PERMISOS DE MENÚS:")
            print(f"      • Ver menú transcribir: {'✅' if permisos.ver_menu_transcribir else '❌'}")
            print(f"      • Ver menú config IA: {'✅' if permisos.ver_menu_configurar_ia else '❌'}")
            print(f"      • Ver menú gestionar usuarios: {'✅' if permisos.ver_menu_gestionar_usuarios else '❌'}")
            print(f"      • Ver menú reportes: {'✅' if permisos.ver_menu_reportes else '❌'}")
            
            print(f"   ⚙️ PERMISOS DE FUNCIONALIDADES:")
            print(f"      • Procesar con IA: {'✅' if permisos.procesar_con_ia else '❌'}")
            print(f"      • Aprobar actas: {'✅' if permisos.aprobar_actas else '❌'}")
            print(f"      • Gestionar usuarios: {'✅' if permisos.gestionar_perfiles_usuarios else '❌'}")
            print(f"      • Configurar modelos IA: {'✅' if permisos.configurar_modelos_ia else '❌'}")
        else:
            print(f"   ❌ Sin permisos detallados configurados")
        
        print()
        
    except PerfilUsuario.DoesNotExist:
        print(f"👤 {user.username} - ❌ SIN PERFIL")
        print()

print(f"📊 RESUMEN:")
print(f"   Usuarios totales: {User.objects.count()}")
print(f"   Perfiles creados: {PerfilUsuario.objects.count()}")
print(f"   Permisos configurados: {PermisosDetallados.objects.count()}")
