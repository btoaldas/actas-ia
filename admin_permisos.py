#!/usr/bin/env python
"""
ADMINISTRADOR DE PERFILES Y PERMISOS - SISTEMA ACTAS MUNICIPALES IA
================================================================

Este script permite gestionar de manera completa los perfiles y permisos del sistema.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.config_system.models import PerfilUsuario, PermisosDetallados

def mostrar_menu():
    print("🔐 === ADMINISTRADOR DE PERFILES Y PERMISOS ===")
    print()
    print("1. 👥 Ver todos los usuarios y sus perfiles")
    print("2. 🔑 Ver permisos detallados por usuario")
    print("3. 📊 Resumen por roles")
    print("4. ✅ Crear usuario con perfil")
    print("5. 🔄 Actualizar permisos de un usuario")
    print("6. 🎯 Aplicar permisos por rol")
    print("7. 📋 Exportar configuración de permisos")
    print("0. ❌ Salir")
    print()

def ver_usuarios_perfiles():
    print("👥 === USUARIOS Y PERFILES ===")
    print()
    usuarios = User.objects.all().order_by('username')
    
    for user in usuarios:
        print(f"👤 {user.username} ({user.first_name} {user.last_name})")
        print(f"   📧 Email: {user.email}")
        print(f"   🔒 Staff: {'Sí' if user.is_staff else 'No'} | Superuser: {'Sí' if user.is_superuser else 'No'}")
        
        try:
            perfil = user.perfilusuario
            print(f"   📋 Rol: {perfil.get_rol_display()}")
            if perfil.departamento:
                print(f"   🏢 Departamento: {perfil.get_departamento_display()}")
            if perfil.cargo:
                print(f"   💼 Cargo: {perfil.cargo}")
            print(f"   📱 Teléfono: {perfil.telefono or 'No registrado'}")
            print(f"   🔢 Extensión: {perfil.extension or 'No registrada'}")
            print(f"   ✅ Activo: {'Sí' if perfil.activo else 'No'}")
            print(f"   📅 Último acceso: {perfil.ultimo_acceso or 'Nunca'}")
        except PerfilUsuario.DoesNotExist:
            print(f"   ❌ SIN PERFIL ASIGNADO")
        
        print()

def ver_permisos_detallados():
    print("🔑 === PERMISOS DETALLADOS POR USUARIO ===")
    print()
    
    username = input("Ingrese el username a consultar (o 'todos' para ver todos): ").strip()
    
    if username.lower() == 'todos':
        usuarios = User.objects.all()
    else:
        usuarios = User.objects.filter(username=username)
        if not usuarios.exists():
            print(f"❌ Usuario '{username}' no encontrado")
            return
    
    for user in usuarios:
        print(f"👤 === PERMISOS DE {user.username.upper()} ===")
        try:
            perfil = user.perfilusuario
            permisos = perfil.permisos_detallados
            
            print(f"📋 Rol: {perfil.get_rol_display()}")
            print()
            
            print("🗂️ PERMISOS DE MENÚS:")
            menus = [
                ('ver_menu_dashboard', 'Dashboard'),
                ('ver_menu_transcribir', 'Transcribir'),
                ('ver_menu_procesar_actas', 'Procesar Actas'),
                ('ver_menu_revisar_actas', 'Revisar Actas'),
                ('ver_menu_publicar_actas', 'Publicar Actas'),
                ('ver_menu_gestionar_sesiones', 'Gestionar Sesiones'),
                ('ver_menu_configurar_ia', 'Configurar IA'),
                ('ver_menu_configurar_whisper', 'Configurar Whisper'),
                ('ver_menu_gestionar_usuarios', 'Gestionar Usuarios'),
                ('ver_menu_reportes', 'Reportes'),
                ('ver_menu_auditoria', 'Auditoría'),
                ('ver_menu_transparencia', 'Portal Transparencia'),
            ]
            
            for campo, nombre in menus:
                estado = '✅' if getattr(permisos, campo) else '❌'
                print(f"   {estado} {nombre}")
            
            print()
            print("⚙️ PERMISOS DE FUNCIONALIDADES:")
            funcionalidades = [
                ('subir_audio_transcripcion', 'Subir audio'),
                ('iniciar_transcripcion', 'Iniciar transcripción'),
                ('procesar_con_ia', 'Procesar con IA'),
                ('configurar_modelos_ia', 'Configurar modelos IA'),
                ('crear_acta_nueva', 'Crear acta nueva'),
                ('editar_acta_borrador', 'Editar acta borrador'),
                ('revisar_actas', 'Revisar actas'),
                ('aprobar_actas', 'Aprobar actas'),
                ('publicar_actas', 'Publicar actas'),
                ('gestionar_perfiles_usuarios', 'Gestionar usuarios'),
                ('ver_reportes_uso', 'Ver reportes'),
                ('gestionar_respaldos', 'Gestionar respaldos'),
            ]
            
            for campo, nombre in funcionalidades:
                estado = '✅' if getattr(permisos, campo) else '❌'
                print(f"   {estado} {nombre}")
            
        except PerfilUsuario.DoesNotExist:
            print(f"❌ Usuario sin perfil")
        except PermisosDetallados.DoesNotExist:
            print(f"❌ Usuario sin permisos detallados")
        
        print("=" * 50)
        print()

def resumen_por_roles():
    print("📊 === RESUMEN POR ROLES ===")
    print()
    
    for rol_code, rol_name in PerfilUsuario.ROLES:
        count = PerfilUsuario.objects.filter(rol=rol_code).count()
        if count > 0:
            print(f"📋 {rol_name}: {count} usuario(s)")
            
            # Mostrar usuarios de este rol
            usuarios_rol = PerfilUsuario.objects.filter(rol=rol_code)
            for perfil in usuarios_rol:
                print(f"   👤 {perfil.usuario.username} ({perfil.usuario.first_name} {perfil.usuario.last_name})")
                if perfil.departamento:
                    print(f"      🏢 {perfil.get_departamento_display()}")
                if perfil.cargo:
                    print(f"      💼 {perfil.cargo}")
            
            # Mostrar permisos típicos de este rol
            if usuarios_rol.exists():
                primer_perfil = usuarios_rol.first()
                if hasattr(primer_perfil, 'permisos_detallados'):
                    permisos = primer_perfil.permisos_detallados
                    print(f"   🔑 Permisos clave:")
                    print(f"      • Ver menú transcribir: {'✅' if permisos.ver_menu_transcribir else '❌'}")
                    print(f"      • Ver menú config IA: {'✅' if permisos.ver_menu_configurar_ia else '❌'}")
                    print(f"      • Gestionar usuarios: {'✅' if permisos.gestionar_perfiles_usuarios else '❌'}")
                    print(f"      • Procesar con IA: {'✅' if permisos.procesar_con_ia else '❌'}")
                    print(f"      • Aprobar actas: {'✅' if permisos.aprobar_actas else '❌'}")
            print()

def crear_usuario_con_perfil():
    print("✅ === CREAR USUARIO CON PERFIL ===")
    print()
    
    username = input("Username: ").strip()
    if User.objects.filter(username=username).exists():
        print(f"❌ El usuario '{username}' ya existe")
        return
    
    email = input("Email: ").strip()
    first_name = input("Nombre: ").strip()
    last_name = input("Apellido: ").strip()
    password = input("Contraseña (mínimo 6 caracteres): ").strip()
    
    if len(password) < 6:
        print("❌ La contraseña debe tener al menos 6 caracteres")
        return
    
    print("\nRoles disponibles:")
    for i, (rol_code, rol_name) in enumerate(PerfilUsuario.ROLES, 1):
        print(f"{i}. {rol_name}")
    
    try:
        rol_idx = int(input("Seleccione rol (número): ").strip()) - 1
        rol_code = PerfilUsuario.ROLES[rol_idx][0]
    except (ValueError, IndexError):
        print("❌ Rol inválido")
        return
    
    print("\nDepartamentos disponibles:")
    for i, (dept_code, dept_name) in enumerate(PerfilUsuario.DEPARTAMENTOS, 1):
        print(f"{i}. {dept_name}")
    
    try:
        dept_idx = int(input("Seleccione departamento (número): ").strip()) - 1
        dept_code = PerfilUsuario.DEPARTAMENTOS[dept_idx][0]
    except (ValueError, IndexError):
        print("❌ Departamento inválido")
        return
    
    cargo = input("Cargo: ").strip()
    telefono = input("Teléfono (opcional): ").strip()
    extension = input("Extensión (opcional): ").strip()
    
    # Crear usuario
    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=password
    )
    
    # Crear perfil
    perfil = PerfilUsuario.objects.create(
        usuario=user,
        rol=rol_code,
        departamento=dept_code,
        cargo=cargo,
        telefono=telefono or None,
        extension=extension or None,
        activo=True
    )
    
    # Aplicar permisos
    permisos = PermisosDetallados.aplicar_permisos_por_rol(perfil)
    
    print(f"✅ Usuario '{username}' creado exitosamente")
    print(f"📋 Rol: {perfil.get_rol_display()}")
    print(f"🏢 Departamento: {perfil.get_departamento_display()}")
    print(f"🔑 Permisos aplicados según el rol")

def actualizar_permisos_usuario():
    print("🔄 === ACTUALIZAR PERMISOS DE USUARIO ===")
    print()
    
    username = input("Username del usuario: ").strip()
    try:
        user = User.objects.get(username=username)
        perfil = user.perfilusuario
    except User.DoesNotExist:
        print(f"❌ Usuario '{username}' no encontrado")
        return
    except PerfilUsuario.DoesNotExist:
        print(f"❌ Usuario '{username}' no tiene perfil")
        return
    
    print(f"👤 Usuario: {user.first_name} {user.last_name}")
    print(f"📋 Rol actual: {perfil.get_rol_display()}")
    print()
    print("¿Desea:")
    print("1. Reaplicar permisos según el rol actual")
    print("2. Cambiar rol y aplicar nuevos permisos")
    print("0. Cancelar")
    
    opcion = input("Seleccione opción: ").strip()
    
    if opcion == '1':
        PermisosDetallados.aplicar_permisos_por_rol(perfil)
        print(f"✅ Permisos reaplicados para el rol {perfil.get_rol_display()}")
    
    elif opcion == '2':
        print("\nRoles disponibles:")
        for i, (rol_code, rol_name) in enumerate(PerfilUsuario.ROLES, 1):
            print(f"{i}. {rol_name}")
        
        try:
            rol_idx = int(input("Seleccione nuevo rol: ").strip()) - 1
            nuevo_rol = PerfilUsuario.ROLES[rol_idx][0]
            
            perfil.rol = nuevo_rol
            perfil.save()
            
            PermisosDetallados.aplicar_permisos_por_rol(perfil)
            
            print(f"✅ Rol cambiado a {perfil.get_rol_display()}")
            print(f"✅ Permisos actualizados")
            
        except (ValueError, IndexError):
            print("❌ Rol inválido")

def aplicar_permisos_por_rol():
    print("🎯 === APLICAR PERMISOS POR ROL ===")
    print()
    
    print("Roles disponibles:")
    for i, (rol_code, rol_name) in enumerate(PerfilUsuario.ROLES, 1):
        count = PerfilUsuario.objects.filter(rol=rol_code).count()
        print(f"{i}. {rol_name} ({count} usuarios)")
    
    print("0. Todos los roles")
    
    opcion = input("Seleccione rol: ").strip()
    
    if opcion == '0':
        perfiles = PerfilUsuario.objects.all()
        print("Aplicando permisos a todos los usuarios...")
    else:
        try:
            rol_idx = int(opcion) - 1
            rol_code = PerfilUsuario.ROLES[rol_idx][0]
            perfiles = PerfilUsuario.objects.filter(rol=rol_code)
            print(f"Aplicando permisos a usuarios con rol {PerfilUsuario.ROLES[rol_idx][1]}...")
        except (ValueError, IndexError):
            print("❌ Opción inválida")
            return
    
    count = 0
    for perfil in perfiles:
        PermisosDetallados.aplicar_permisos_por_rol(perfil)
        count += 1
        print(f"✅ {perfil.usuario.username}")
    
    print(f"\n🎯 Permisos aplicados a {count} usuarios")

def exportar_configuracion():
    print("📋 === EXPORTAR CONFIGURACIÓN DE PERMISOS ===")
    print()
    
    filename = "configuracion_permisos.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("CONFIGURACIÓN DE PERFILES Y PERMISOS - SISTEMA ACTAS MUNICIPALES IA\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"Fecha de exportación: {django.utils.timezone.now()}\n\n")
        
        f.write("USUARIOS Y PERFILES:\n")
        f.write("-" * 20 + "\n")
        
        for user in User.objects.all().order_by('username'):
            f.write(f"\nUsuario: {user.username} ({user.first_name} {user.last_name})\n")
            f.write(f"Email: {user.email}\n")
            
            try:
                perfil = user.perfilusuario
                f.write(f"Rol: {perfil.get_rol_display()}\n")
                f.write(f"Departamento: {perfil.get_departamento_display() or 'No asignado'}\n")
                f.write(f"Cargo: {perfil.cargo or 'No asignado'}\n")
                f.write(f"Activo: {'Sí' if perfil.activo else 'No'}\n")
                
                if hasattr(perfil, 'permisos_detallados'):
                    permisos = perfil.permisos_detallados
                    f.write("\nPermisos de menús:\n")
                    
                    menus = [
                        ('ver_menu_transcribir', 'Transcribir'),
                        ('ver_menu_configurar_ia', 'Configurar IA'),
                        ('ver_menu_gestionar_usuarios', 'Gestionar Usuarios'),
                        ('ver_menu_reportes', 'Reportes'),
                    ]
                    
                    for campo, nombre in menus:
                        estado = 'SÍ' if getattr(permisos, campo) else 'NO'
                        f.write(f"  - {nombre}: {estado}\n")
                
            except PerfilUsuario.DoesNotExist:
                f.write("Sin perfil asignado\n")
        
        f.write("\n\nRESUMEN POR ROLES:\n")
        f.write("-" * 18 + "\n")
        
        for rol_code, rol_name in PerfilUsuario.ROLES:
            count = PerfilUsuario.objects.filter(rol=rol_code).count()
            if count > 0:
                f.write(f"\n{rol_name}: {count} usuario(s)\n")
    
    print(f"✅ Configuración exportada a: {filename}")

def main():
    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()
        
        if opcion == '1':
            ver_usuarios_perfiles()
        elif opcion == '2':
            ver_permisos_detallados()
        elif opcion == '3':
            resumen_por_roles()
        elif opcion == '4':
            crear_usuario_con_perfil()
        elif opcion == '5':
            actualizar_permisos_usuario()
        elif opcion == '6':
            aplicar_permisos_por_rol()
        elif opcion == '7':
            exportar_configuracion()
        elif opcion == '0':
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")
        
        input("\nPresione Enter para continuar...")
        print("\n" + "=" * 60 + "\n")

if __name__ == '__main__':
    main()
