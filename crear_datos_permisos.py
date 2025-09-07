"""
Script para crear datos de ejemplo del sistema de permisos
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.config_system.models import PermisoCustom, PerfilUsuario, UsuarioPerfil, LogPermisos

def crear_permisos_ejemplo():
    """Crear permisos de ejemplo"""
    permisos_data = [
        {
            'codigo': 'actas.crear',
            'nombre': 'Crear Actas',
            'descripcion': 'Permite crear nuevas actas municipales',
            'categoria': 'actas',
            'nivel_acceso': 'escribir',
            'urls_permitidas': '/actas/crear/, /actas/new/',
            'mostrar_en_menu': True,
            'icono_menu': 'fas fa-plus-circle',
            'orden_menu': 10
        },
        {
            'codigo': 'actas.editar',
            'nombre': 'Editar Actas',
            'descripcion': 'Permite editar actas existentes',
            'categoria': 'actas',
            'nivel_acceso': 'escribir',
            'urls_permitidas': '/actas/editar/, /actas/edit/',
            'mostrar_en_menu': True,
            'icono_menu': 'fas fa-edit',
            'orden_menu': 20
        },
        {
            'codigo': 'actas.eliminar',
            'nombre': 'Eliminar Actas',
            'descripcion': 'Permite eliminar actas',
            'categoria': 'actas',
            'nivel_acceso': 'eliminar',
            'urls_permitidas': '/actas/eliminar/, /actas/delete/',
            'mostrar_en_menu': False,
            'icono_menu': 'fas fa-trash',
            'orden_menu': 30
        },
        {
            'codigo': 'users.gestionar',
            'nombre': 'Gestionar Usuarios',
            'descripcion': 'Permite gestionar usuarios del sistema',
            'categoria': 'users',
            'nivel_acceso': 'admin',
            'urls_permitidas': '/config-system/usuarios/, /admin/auth/user/',
            'mostrar_en_menu': True,
            'icono_menu': 'fas fa-users',
            'orden_menu': 100
        },
        {
            'codigo': 'config.smtp',
            'nombre': 'Configurar SMTP',
            'descripcion': 'Permite configurar servidores SMTP',
            'categoria': 'config',
            'nivel_acceso': 'admin',
            'urls_permitidas': '/config-system/smtp/',
            'mostrar_en_menu': True,
            'icono_menu': 'fas fa-envelope',
            'orden_menu': 200
        },
        {
            'codigo': 'reports.ver',
            'nombre': 'Ver Reportes',
            'descripcion': 'Permite ver reportes del sistema',
            'categoria': 'reports',
            'nivel_acceso': 'leer',
            'urls_permitidas': '/reportes/, /analytics/',
            'mostrar_en_menu': True,
            'icono_menu': 'fas fa-chart-bar',
            'orden_menu': 300
        }
    ]
    
    permisos_creados = []
    for data in permisos_data:
        permiso, created = PermisoCustom.objects.get_or_create(
            codigo=data['codigo'],
            defaults=data
        )
        if created:
            print(f"✅ Permiso creado: {permiso.nombre}")
        else:
            print(f"ℹ️  Permiso ya existe: {permiso.nombre}")
        permisos_creados.append(permiso)
    
    return permisos_creados

def crear_perfiles_ejemplo(permisos):
    """Crear perfiles de ejemplo"""
    perfiles_data = [
        {
            'nombre': 'Administrador Municipal',
            'descripcion': 'Perfil con acceso completo para administradores municipales',
            'color': '#dc3545',
            'es_publico': True,
            'nivel_jerarquia': 2,
            'dashboard_personalizado': True,
            'pagina_inicio': '/config-system/',
            'permisos_codigos': ['actas.crear', 'actas.editar', 'actas.eliminar', 'users.gestionar', 'config.smtp', 'reports.ver']
        },
        {
            'nombre': 'Secretario Municipal',
            'descripcion': 'Perfil para secretarios que gestionan actas',
            'color': '#007bff',
            'es_publico': True,
            'nivel_jerarquia': 1,
            'dashboard_personalizado': False,
            'pagina_inicio': '/actas/',
            'permisos_codigos': ['actas.crear', 'actas.editar', 'reports.ver']
        },
        {
            'nombre': 'Usuario Consulta',
            'descripcion': 'Perfil de solo lectura para consultar información',
            'color': '#28a745',
            'es_publico': True,
            'nivel_jerarquia': 0,
            'dashboard_personalizado': False,
            'pagina_inicio': '/actas/',
            'permisos_codigos': ['reports.ver']
        }
    ]
    
    perfiles_creados = []
    for data in perfiles_data:
        permisos_codigos = data.pop('permisos_codigos')
        perfil, created = PerfilUsuario.objects.get_or_create(
            nombre=data['nombre'],
            defaults=data
        )
        
        if created:
            print(f"✅ Perfil creado: {perfil.nombre}")
            
            # Asignar permisos
            permisos_perfil = PermisoCustom.objects.filter(codigo__in=permisos_codigos)
            perfil.permisos.set(permisos_perfil)
            print(f"   📋 Asignados {permisos_perfil.count()} permisos")
        else:
            print(f"ℹ️  Perfil ya existe: {perfil.nombre}")
        
        perfiles_creados.append(perfil)
    
    return perfiles_creados

def asignar_perfiles_usuarios(perfiles):
    """Asignar perfiles a usuarios existentes"""
    try:
        # Buscar usuario superadmin
        superusers = User.objects.filter(is_superuser=True)
        if superusers.exists():
            user = superusers.first()
            perfil_admin = PerfilUsuario.objects.filter(nombre='Administrador Municipal').first()
            
            if perfil_admin:
                asignacion, created = UsuarioPerfil.objects.get_or_create(
                    usuario=user,
                    perfil=perfil_admin,
                    defaults={
                        'es_principal': True,
                        'asignado_por': user,
                        'notas': 'Asignación automática inicial'
                    }
                )
                
                if created:
                    print(f"✅ Perfil '{perfil_admin.nombre}' asignado a {user.username}")
                else:
                    print(f"ℹ️  {user.username} ya tiene el perfil '{perfil_admin.nombre}'")
    except Exception as e:
        print(f"❌ Error asignando perfiles: {e}")

def main():
    print("🚀 Iniciando creación de datos de ejemplo del sistema de permisos...\n")
    
    # Verificar que las tablas existen
    try:
        print("🔍 Verificando tablas...")
        PermisoCustom.objects.count()
        PerfilUsuario.objects.count()
        UsuarioPerfil.objects.count()
        print("✅ Tablas verificadas\n")
    except Exception as e:
        print(f"❌ Error: Las tablas no existen. Ejecutar migraciones primero: {e}")
        return
    
    # Crear permisos
    print("📝 Creando permisos...")
    permisos = crear_permisos_ejemplo()
    print(f"✅ Total permisos: {len(permisos)}\n")
    
    # Crear perfiles
    print("👥 Creando perfiles...")
    perfiles = crear_perfiles_ejemplo(permisos)
    print(f"✅ Total perfiles: {len(perfiles)}\n")
    
    # Asignar perfiles a usuarios
    print("🔗 Asignando perfiles a usuarios...")
    asignar_perfiles_usuarios(perfiles)
    print()
    
    print("🎉 ¡Datos de ejemplo creados exitosamente!")
    print("\n📊 Resumen:")
    print(f"   • Permisos: {PermisoCustom.objects.count()}")
    print(f"   • Perfiles: {PerfilUsuario.objects.count()}")
    print(f"   • Asignaciones: {UsuarioPerfil.objects.count()}")

if __name__ == "__main__":
    main()
