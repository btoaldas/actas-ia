#!/usr/bin/env python
"""
Script para crear perfiles y asignar permisos detallados a todos los usuarios
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.config_system.models import PerfilUsuario, PermisosDetallados

def main():
    print("🔐 === CONFIGURANDO PERFILES Y PERMISOS DETALLADOS ===")
    print()
    
    # 1. Obtener todos los usuarios
    usuarios = User.objects.all()
    print(f"👥 Usuarios encontrados: {usuarios.count()}")
    print()
    
    # 2. Crear perfiles para usuarios que no lo tienen
    usuarios_sin_perfil = []
    for user in usuarios:
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults={
                'rol': 'superadmin' if user.is_superuser else 'viewer',
                'departamento': 'sistemas' if user.is_superuser else 'secretaria',
                'cargo': 'Administrador del Sistema' if user.is_superuser else 'Usuario',
                'activo': True
            }
        )
        if created:
            usuarios_sin_perfil.append(user.username)
            print(f"✅ Perfil creado para: {user.username} (rol: {perfil.rol})")
        else:
            print(f"✓ Perfil existente: {user.username} (rol: {perfil.rol})")
    
    if usuarios_sin_perfil:
        print(f"\n📝 Se crearon perfiles para: {', '.join(usuarios_sin_perfil)}")
    
    print()
    
    # 3. Crear permisos detallados para todos los perfiles
    perfiles = PerfilUsuario.objects.all()
    print(f"🔑 Aplicando permisos detallados a {perfiles.count()} perfiles...")
    print()
    
    for perfil in perfiles:
        permisos = PermisosDetallados.aplicar_permisos_por_rol(perfil)
        print(f"✅ Permisos aplicados para: {perfil.usuario.username} ({perfil.get_rol_display()})")
        
        # Mostrar algunos permisos clave según el rol
        if perfil.rol == 'superadmin':
            print(f"   • Acceso completo a todas las funcionalidades")
        elif perfil.rol == 'admin':
            print(f"   • Ver menú transcribir: {permisos.ver_menu_transcribir}")
            print(f"   • Ver menú config IA: {permisos.ver_menu_configurar_ia}")
            print(f"   • Gestionar usuarios: {permisos.gestionar_perfiles_usuarios}")
        elif perfil.rol == 'secretario':
            print(f"   • Ver menú transcribir: {permisos.ver_menu_transcribir}")
            print(f"   • Ver menú config IA: {permisos.ver_menu_configurar_ia}")
            print(f"   • Gestionar sesiones: {permisos.gestionar_asistentes}")
        elif perfil.rol == 'alcalde':
            print(f"   • Ver menú transcribir: {permisos.ver_menu_transcribir}")
            print(f"   • Ver menú config IA: {permisos.ver_menu_configurar_ia}")
            print(f"   • Aprobar actas: {permisos.aprobar_actas}")
        elif perfil.rol == 'concejal':
            print(f"   • Ver menú transcribir: {permisos.ver_menu_transcribir}")
            print(f"   • Ver menú config IA: {permisos.ver_menu_configurar_ia}")
            print(f"   • Revisar actas: {permisos.revisar_actas}")
        elif perfil.rol == 'editor':
            print(f"   • Ver menú transcribir: {permisos.ver_menu_transcribir}")
            print(f"   • Ver menú config IA: {permisos.ver_menu_configurar_ia}")
            print(f"   • Procesar con IA: {permisos.procesar_con_ia}")
        elif perfil.rol == 'viewer':
            print(f"   • Ver menú transcribir: {permisos.ver_menu_transcribir}")
            print(f"   • Ver menú config IA: {permisos.ver_menu_configurar_ia}")
            print(f"   • Solo lectura: acceso limitado")
        print()
    
    print("🔄 === CREANDO USUARIOS DEMO ADICIONALES ===")
    print()
    
    # 4. Crear usuarios demo adicionales si no existen
    usuarios_demo = [
        {
            'username': 'secretario.municipal',
            'email': 'secretario@puyo.gob.ec',
            'first_name': 'María',
            'last_name': 'García',
            'perfil': {
                'rol': 'secretario',
                'departamento': 'secretaria',
                'cargo': 'Secretaria General',
                'telefono': '601-2345678',
                'extension': '101'
            }
        },
        {
            'username': 'alcalde.municipal',
            'email': 'alcalde@puyo.gob.ec',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'perfil': {
                'rol': 'alcalde',
                'departamento': 'alcaldia',
                'cargo': 'Alcalde Municipal',
                'telefono': '601-2345679',
                'extension': '100'
            }
        },
        {
            'username': 'concejal.primero',
            'email': 'concejal1@puyo.gob.ec',
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'perfil': {
                'rol': 'concejal',
                'departamento': 'concejo',
                'cargo': 'Concejal Principal',
                'telefono': '601-2345680',
                'extension': '201'
            }
        },
        {
            'username': 'editor.actas',
            'email': 'editor@puyo.gob.ec',
            'first_name': 'Luis',
            'last_name': 'Hernández',
            'perfil': {
                'rol': 'editor',
                'departamento': 'secretaria',
                'cargo': 'Editor de Actas',
                'telefono': '601-2345681',
                'extension': '102'
            }
        },
        {
            'username': 'admin.sistema',
            'email': 'admin.sistema@puyo.gob.ec',
            'first_name': 'José',
            'last_name': 'Pérez',
            'perfil': {
                'rol': 'admin',
                'departamento': 'sistemas',
                'cargo': 'Administrador de Sistemas',
                'telefono': '601-2345682',
                'extension': '300'
            }
        },
        {
            'username': 'viewer.ciudadano',
            'email': 'viewer@puyo.gob.ec',
            'first_name': 'Patricia',
            'last_name': 'López',
            'perfil': {
                'rol': 'viewer',
                'departamento': 'secretaria',
                'cargo': 'Consultor Externo',
                'telefono': '601-2345683',
                'extension': '400'
            }
        }
    ]
    
    for user_data in usuarios_demo:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_active': True
            }
        )
        if created:
            user.set_password('demo123')
            user.save()
            print(f"✅ Usuario demo creado: {user.username}")
        else:
            print(f"✓ Usuario demo existente: {user.username}")
        
        # Crear o actualizar perfil
        perfil, perfil_created = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults=user_data['perfil']
        )
        if perfil_created:
            print(f"   ✅ Perfil creado: {perfil.get_rol_display()}")
        else:
            # Actualizar perfil existente
            for key, value in user_data['perfil'].items():
                setattr(perfil, key, value)
            perfil.save()
            print(f"   ✓ Perfil actualizado: {perfil.get_rol_display()}")
        
        # Aplicar permisos detallados
        permisos = PermisosDetallados.aplicar_permisos_por_rol(perfil)
        print(f"   🔑 Permisos aplicados según rol: {perfil.rol}")
        print()
    
    print("📊 === RESUMEN FINAL ===")
    print(f"👥 Total usuarios: {User.objects.count()}")
    print(f"👤 Total perfiles: {PerfilUsuario.objects.count()}")
    print(f"🔑 Total permisos configurados: {PermisosDetallados.objects.count()}")
    print()
    
    print("🔍 === DISTRIBUCIÓN POR ROLES ===")
    for rol_code, rol_name in PerfilUsuario.ROLES:
        count = PerfilUsuario.objects.filter(rol=rol_code).count()
        if count > 0:
            print(f"   • {rol_name}: {count} usuario(s)")
    print()
    
    print("🔐 === EJEMPLOS DE PERMISOS POR ROL ===")
    for rol_code, rol_name in PerfilUsuario.ROLES:
        perfiles_rol = PerfilUsuario.objects.filter(rol=rol_code).first()
        if perfiles_rol and hasattr(perfiles_rol, 'permisos_detallados'):
            permisos = perfiles_rol.permisos_detallados
            print(f"   📋 {rol_name}:")
            print(f"      • Ver menú transcribir: {'✅' if permisos.ver_menu_transcribir else '❌'}")
            print(f"      • Ver menú config IA: {'✅' if permisos.ver_menu_configurar_ia else '❌'}")
            print(f"      • Gestionar usuarios: {'✅' if permisos.gestionar_perfiles_usuarios else '❌'}")
            print(f"      • Procesar con IA: {'✅' if permisos.procesar_con_ia else '❌'}")
            print(f"      • Aprobar actas: {'✅' if permisos.aprobar_actas else '❌'}")
            print()
    
    print("🌐 === CREDENCIALES DE ACCESO ===")
    print("   🔑 Superadmin: admin / admin123")
    print("   👨‍💼 Admin Sistema: admin.sistema / demo123")
    print("   📝 Secretario: secretario.municipal / demo123")
    print("   🏛️ Alcalde: alcalde.municipal / demo123")
    print("   🏛️ Concejal: concejal.primero / demo123")
    print("   ✏️ Editor: editor.actas / demo123")
    print("   👁️ Viewer: viewer.ciudadano / demo123")
    print()
    
    print("✅ SISTEMA DE PERFILES Y PERMISOS COMPLETAMENTE CONFIGURADO")
    print("🚀 Acceso: http://localhost:8000")
    print("⚙️ Panel config: http://localhost:8000/config_system/ (solo superadmins)")

if __name__ == '__main__':
    main()
