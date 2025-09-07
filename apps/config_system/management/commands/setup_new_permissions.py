"""
COMANDO DE MIGRACIÓN MANUAL PARA EL NUEVO SISTEMA DE PERMISOS

Este comando crea las tablas del nuevo sistema de permisos de forma segura,
evitando conflictos con el sistema existente.
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Crea las tablas del nuevo sistema de permisos de forma manual y segura'

    def add_arguments(self, parser):
        parser.add_argument(
            '--drop-existing',
            action='store_true',
            help='Elimina las tablas existentes del nuevo sistema antes de crearlas',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando migración manual del nuevo sistema de permisos...')
        )

        with connection.cursor() as cursor:
            if options['drop_existing']:
                self.drop_existing_tables(cursor)
            
            self.create_system_permission_table(cursor)
            self.create_user_profile_table(cursor)
            self.create_user_profile_assignment_table(cursor)
            self.create_profile_permissions_m2m_table(cursor)
            
        self.stdout.write(
            self.style.SUCCESS('✅ ¡Migración completada exitosamente!')
        )
        
        # Crear algunos datos de ejemplo
        self.create_sample_data()

    def drop_existing_tables(self, cursor):
        """Elimina tablas existentes del nuevo sistema"""
        self.stdout.write('⚠️  Eliminando tablas existentes...')
        
        tables_to_drop = [
            'config_system_userprofile_permissions',
            'config_system_userprofileassignment',
            'config_system_userprofile',
            'config_system_systempermission',
        ]
        
        for table in tables_to_drop:
            try:
                cursor.execute(f'DROP TABLE IF EXISTS {table} CASCADE;')
                self.stdout.write(f'   - Eliminada tabla: {table}')
            except Exception as e:
                self.stdout.write(f'   - Error eliminando {table}: {e}')

    def create_system_permission_table(self, cursor):
        """Crea la tabla SystemPermission"""
        self.stdout.write('📋 Creando tabla SystemPermission...')
        
        sql = """
        CREATE TABLE IF NOT EXISTS config_system_systempermission (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            code VARCHAR(255) UNIQUE NOT NULL,
            permission_type VARCHAR(20) NOT NULL CHECK (permission_type IN ('menu', 'view', 'widget', 'module')),
            url_pattern VARCHAR(500),
            view_name VARCHAR(255),
            app_name VARCHAR(100),
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            auto_generated BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_systempermission_type ON config_system_systempermission(permission_type);
        CREATE INDEX IF NOT EXISTS idx_systempermission_app ON config_system_systempermission(app_name);
        CREATE INDEX IF NOT EXISTS idx_systempermission_active ON config_system_systempermission(is_active);
        """
        
        cursor.execute(sql)
        self.stdout.write('   ✅ Tabla SystemPermission creada')

    def create_user_profile_table(self, cursor):
        """Crea la tabla UserProfile"""
        self.stdout.write('👥 Creando tabla UserProfile...')
        
        sql = """
        CREATE TABLE IF NOT EXISTS config_system_userprofile (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            description TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_userprofile_active ON config_system_userprofile(is_active);
        """
        
        cursor.execute(sql)
        self.stdout.write('   ✅ Tabla UserProfile creada')

    def create_user_profile_assignment_table(self, cursor):
        """Crea la tabla UserProfileAssignment"""
        self.stdout.write('🔗 Creando tabla UserProfileAssignment...')
        
        sql = """
        CREATE TABLE IF NOT EXISTS config_system_userprofileassignment (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE,
            profile_id INTEGER NOT NULL REFERENCES config_system_userprofile(id) ON DELETE CASCADE,
            assigned_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
            assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(user_id, profile_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_assignment_user ON config_system_userprofileassignment(user_id);
        CREATE INDEX IF NOT EXISTS idx_assignment_profile ON config_system_userprofileassignment(profile_id);
        """
        
        cursor.execute(sql)
        self.stdout.write('   ✅ Tabla UserProfileAssignment creada')

    def create_profile_permissions_m2m_table(self, cursor):
        """Crea la tabla de relación muchos a muchos UserProfile-SystemPermission"""
        self.stdout.write('🔄 Creando tabla de relación Profile-Permissions...')
        
        sql = """
        CREATE TABLE IF NOT EXISTS config_system_userprofile_permissions (
            id SERIAL PRIMARY KEY,
            userprofile_id INTEGER NOT NULL REFERENCES config_system_userprofile(id) ON DELETE CASCADE,
            systempermission_id INTEGER NOT NULL REFERENCES config_system_systempermission(id) ON DELETE CASCADE,
            UNIQUE(userprofile_id, systempermission_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_profile_permissions_profile ON config_system_userprofile_permissions(userprofile_id);
        CREATE INDEX IF NOT EXISTS idx_profile_permissions_permission ON config_system_userprofile_permissions(systempermission_id);
        """
        
        cursor.execute(sql)
        self.stdout.write('   ✅ Tabla de relación Profile-Permissions creada')

    def create_sample_data(self):
        """Crea datos de ejemplo"""
        self.stdout.write('🌱 Creando datos de ejemplo...')
        
        with connection.cursor() as cursor:
            # Crear permisos básicos
            basic_permissions = [
                ('menu.dashboard', 'Dashboard Principal', 'menu', '/dashboard-v3/', None, None, 'Acceso al dashboard principal'),
                ('menu.actas', 'Menú Actas', 'menu', '/actas/', None, None, 'Acceso al menú de actas'),
                ('menu.transparencia', 'Menú Transparencia', 'menu', '/transparencia/', None, None, 'Acceso al menú de transparencia'),
                ('menu.config_system', 'Configuración Sistema', 'menu', '/config-system/', None, None, 'Acceso a configuración del sistema'),
                ('view.actas_list', 'Listar Actas', 'view', 'actas:list', 'actas_list', 'actas', 'Visualizar lista de actas'),
                ('view.actas_detail', 'Ver Detalle Acta', 'view', 'actas:detail', 'actas_detail', 'actas', 'Ver detalles de una acta'),
                ('view.actas_create', 'Crear Acta', 'view', 'actas:create', 'actas_create', 'actas', 'Crear nuevas actas'),
                ('view.actas_edit', 'Editar Acta', 'view', 'actas:edit', 'actas_edit', 'actas', 'Editar actas existentes'),
                ('module.actas', 'Módulo Actas', 'module', None, None, 'actas', 'Acceso completo al módulo de actas'),
                ('module.config_system', 'Módulo Configuración', 'module', None, None, 'config_system', 'Acceso al módulo de configuración'),
            ]
            
            for code, name, ptype, url, view_name, app_name, description in basic_permissions:
                try:
                    cursor.execute("""
                        INSERT INTO config_system_systempermission 
                        (code, name, permission_type, url_pattern, view_name, app_name, description, auto_generated)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (code) DO NOTHING
                    """, [code, name, ptype, url, view_name, app_name, description, True])
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Error creando permiso {code}: {e}')
            
            # Crear perfiles básicos
            basic_profiles = [
                ('Administrador', 'Acceso completo al sistema'),
                ('Editor', 'Acceso de edición a contenidos'),
                ('Visualizador', 'Solo lectura del sistema'),
                ('Secretario Municipal', 'Acceso específico para secretario'),
            ]
            
            for name, description in basic_profiles:
                try:
                    cursor.execute("""
                        INSERT INTO config_system_userprofile (name, description)
                        VALUES (%s, %s)
                        ON CONFLICT (name) DO NOTHING
                    """, [name, description])
                except Exception as e:
                    self.stdout.write(f'   ⚠️  Error creando perfil {name}: {e}')
            
            self.stdout.write('   ✅ Datos de ejemplo creados')

        self.stdout.write(
            self.style.SUCCESS('🎉 ¡Sistema de permisos inicializado correctamente!')
        )
