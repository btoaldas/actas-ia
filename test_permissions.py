#!/usr/bin/env python
"""
Script para probar las funcionalidades del sistema de permisos
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import PermisoCustom, PerfilUsuario, UsuarioPerfil
from django.contrib.auth.models import User

def test_sistema_permisos():
    print("🎉 === SISTEMA DE PERMISOS OPERATIVO ===\n")
    
    try:
        # 1. Verificar permisos
        print("📋 PERMISOS DISPONIBLES:")
        permisos = PermisoCustom.objects.all()
        if permisos.exists():
            for p in permisos:
                estado = "✅ ACTIVO" if p.activo else "❌ INACTIVO"
                print(f"  • {p.codigo}: {p.nombre} [{estado}]")
                print(f"    └─ Categoría: {p.categoria} | Nivel: {p.nivel_acceso}")
                if p.urls_permitidas:
                    print(f"    └─ URLs: {p.urls_permitidas}")
        else:
            print("  ❌ No hay permisos registrados")
    
    print()
    
    # 2. Verificar perfiles
    print("👥 PERFILES DISPONIBLES:")
    perfiles = PerfilUsuario.objects.all()
    if perfiles.exists():
        for perfil in perfiles:
            estado = "✅ ACTIVO" if perfil.activo else "❌ INACTIVO"
            print(f"  • {perfil.nombre}: {perfil.descripcion} [{estado}]")
            print(f"    └─ Jerarquía: {perfil.nivel_jerarquia} | Color: {perfil.color}")
            
            # Mostrar permisos del perfil
            permisos_perfil = perfil.permisos.all()
            if permisos_perfil:
                print(f"    └─ Permisos asignados ({permisos_perfil.count()}):")
                for permiso in permisos_perfil:
                    print(f"       - {permiso.codigo}")
            else:
                print("    └─ Sin permisos asignados")
    else:
        print("  ❌ No hay perfiles registrados")
    
    print()
    
    # 3. Verificar asignaciones de usuarios
    print("🔗 ASIGNACIONES DE USUARIOS:")
    asignaciones = UsuarioPerfil.objects.filter(activo=True)
    if asignaciones.exists():
        for asig in asignaciones:
            principal = "⭐ PRINCIPAL" if asig.es_principal else "   Secundario"
            print(f"  • Usuario: {asig.usuario.username} → Perfil: {asig.perfil.nombre} [{principal}]")
            print(f"    └─ Asignado: {asig.fecha_asignacion.strftime('%d/%m/%Y %H:%M')}")
            if asig.fecha_expiracion:
                print(f"    └─ Expira: {asig.fecha_expiracion.strftime('%d/%m/%Y %H:%M')}")
    else:
        print("  ❌ No hay asignaciones activas")
    
    print()
    
    # 4. Verificar usuario administrador
    print("🛡️ VERIFICACIÓN USUARIO ADMIN:")
    try:
        admin = User.objects.get(username='admin')
        print(f"  ✅ Usuario encontrado: {admin.username}")
        print(f"    └─ Email: {admin.email}")
        print(f"    └─ Superusuario: {'Sí' if admin.is_superuser else 'No'}")
        print(f"    └─ Activo: {'Sí' if admin.is_active else 'No'}")
        
        # Perfiles del admin
        perfiles_admin = UsuarioPerfil.objects.filter(usuario=admin, activo=True)
        if perfiles_admin.exists():
            print(f"    └─ Perfiles asignados ({perfiles_admin.count()}):")
            for up in perfiles_admin:
                print(f"       • {up.perfil.nombre}")
                for permiso in up.perfil.permisos.all():
                    print(f"         ├─ {permiso.codigo}")
        else:
            print("    └─ ❌ Sin perfiles asignados")
            
    except User.DoesNotExist:
        print("  ❌ Usuario 'admin' no encontrado")
    
    print()
    print("✅ === PRUEBA COMPLETADA ===")
    
    # 5. URLs para probar
    print("\n🌐 URLS PARA PROBAR EN EL NAVEGADOR:")
    print("  Dashboard:        http://localhost:8000/config-system/permisos/dashboard/")
    print("  Lista Permisos:   http://localhost:8000/config-system/permisos/")
    print("  Lista Perfiles:   http://localhost:8000/config-system/perfiles/")
    print("  Asignaciones:     http://localhost:8000/config-system/usuarios-perfiles/")
    print("  Admin Django:     http://localhost:8000/admin/")

if __name__ == '__main__':
    test_sistema_permisos()
