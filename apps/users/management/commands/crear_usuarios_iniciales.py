"""
Comando personalizado para crear usuarios iniciales del sistema de actas municipales
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction


class Command(BaseCommand):
    help = 'Crear usuarios iniciales para el Sistema de Actas Municipales de Pastaza'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la recreación de usuarios existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🏛️  Creando usuarios iniciales para el Municipio de Pastaza...')
        )

        try:
            with transaction.atomic():
                # Crear grupos de usuarios
                self._crear_grupos()
                
                # Crear usuarios del sistema
                self._crear_usuarios(force=options['force'])
                
            self.stdout.write(
                self.style.SUCCESS('✅ Usuarios iniciales creados exitosamente')
            )
            
            # Mostrar información de acceso
            self._mostrar_informacion_acceso()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear usuarios: {str(e)}')
            )

    def _crear_grupos(self):
        """Crear grupos de permisos del sistema"""
        grupos = [
            ('Administradores Municipales', 'Acceso completo al sistema'),
            ('Secretarios de Concejo', 'Gestión de actas y reuniones'),
            ('Concejales', 'Revisión y aprobación de actas'),
            ('Ciudadanos', 'Consulta pública de actas'),
            ('Operadores Técnicos', 'Procesamiento de audio y transcripciones'),
        ]
        
        for nombre_grupo, descripcion in grupos:
            grupo, created = Group.objects.get_or_create(name=nombre_grupo)
            if created:
                self.stdout.write(f'  📋 Grupo creado: {nombre_grupo}')

    def _crear_usuarios(self, force=False):
        """Crear usuarios del sistema"""
        usuarios = [
            {
                'username': 'superadmin',
                'email': 'admin@puyo.gob.ec',
                'first_name': 'Super',
                'last_name': 'Administrador',
                'password': 'AdminPuyo2025!',
                'is_superuser': True,
                'is_staff': True,
                'grupos': ['Administradores Municipales']
            },
            {
                'username': 'alcalde.pastaza',
                'email': 'alcalde@puyo.gob.ec',
                'first_name': 'Alcalde',
                'last_name': 'de Pastaza',
                'password': 'AlcaldePuyo2025!',
                'is_staff': True,
                'grupos': ['Administradores Municipales']
            },
            {
                'username': 'secretario.concejo',
                'email': 'secretario@puyo.gob.ec',
                'first_name': 'Secretario',
                'last_name': 'del Concejo',
                'password': 'SecretarioPuyo2025!',
                'is_staff': True,
                'grupos': ['Secretarios de Concejo']
            },
            {
                'username': 'concejal1',
                'email': 'concejal1@puyo.gob.ec',
                'first_name': 'Primer',
                'last_name': 'Concejal',
                'password': 'ConcejalPuyo2025!',
                'is_staff': True,
                'grupos': ['Concejales']
            },
            {
                'username': 'concejal2',
                'email': 'concejal2@puyo.gob.ec',
                'first_name': 'Segundo',
                'last_name': 'Concejal',
                'password': 'ConcejalPuyo2025!',
                'is_staff': True,
                'grupos': ['Concejales']
            },
            {
                'username': 'operador.tecnico',
                'email': 'tecnico@puyo.gob.ec',
                'first_name': 'Operador',
                'last_name': 'Técnico',
                'password': 'TecnicoPuyo2025!',
                'is_staff': True,
                'grupos': ['Operadores Técnicos']
            },
            {
                'username': 'ciudadano.demo',
                'email': 'ciudadano@ejemplo.com',
                'first_name': 'Ciudadano',
                'last_name': 'de Ejemplo',
                'password': 'CiudadanoPuyo2025!',
                'is_staff': False,
                'grupos': ['Ciudadanos']
            }
        ]

        for user_data in usuarios:
            username = user_data['username']
            
            # Verificar si el usuario existe
            if User.objects.filter(username=username).exists():
                if force:
                    User.objects.filter(username=username).delete()
                    self.stdout.write(f'  🔄 Usuario eliminado para recrear: {username}')
                else:
                    self.stdout.write(f'  ⚠️  Usuario ya existe: {username}')
                    continue

            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            
            # Asignar permisos especiales
            if user_data.get('is_superuser'):
                user.is_superuser = True
            if user_data.get('is_staff'):
                user.is_staff = True
            
            user.save()

            # Asignar grupos
            for nombre_grupo in user_data.get('grupos', []):
                try:
                    grupo = Group.objects.get(name=nombre_grupo)
                    user.groups.add(grupo)
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Grupo no encontrado: {nombre_grupo}')
                    )

            self.stdout.write(f'  👤 Usuario creado: {username} ({user_data["email"]})')

    def _mostrar_informacion_acceso(self):
        """Mostrar información de acceso para los usuarios"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('🔑 INFORMACIÓN DE ACCESO AL SISTEMA'))
        self.stdout.write('='*60)
        
        usuarios_info = [
            ('superadmin', 'AdminPuyo2025!', 'Super Administrador'),
            ('alcalde.pastaza', 'AlcaldePuyo2025!', 'Alcalde'),
            ('secretario.concejo', 'SecretarioPuyo2025!', 'Secretario del Concejo'),
            ('concejal1', 'ConcejalPuyo2025!', 'Primer Concejal'),
            ('concejal2', 'ConcejalPuyo2025!', 'Segundo Concejal'),
            ('operador.tecnico', 'TecnicoPuyo2025!', 'Operador Técnico'),
            ('ciudadano.demo', 'CiudadanoPuyo2025!', 'Ciudadano Demo'),
        ]
        
        for username, password, rol in usuarios_info:
            self.stdout.write(f'👤 {rol}:')
            self.stdout.write(f'   Usuario: {username}')
            self.stdout.write(f'   Clave:   {password}')
            self.stdout.write('')
        
        self.stdout.write(self.style.WARNING('⚠️  IMPORTANTE: Cambiar las contraseñas en producción'))
        self.stdout.write('')
        self.stdout.write('🌐 URL de acceso: http://localhost:8000')
        self.stdout.write('🔧 Panel admin: http://localhost:8000/admin/')
        self.stdout.write('')
        self.stdout.write('📊 BASE DE DATOS:')
        self.stdout.write('   Host: localhost')
        self.stdout.write('   Puerto: 5432')
        self.stdout.write('   BD: actas_municipales_pastaza')
        self.stdout.write('   Usuario: admin_actas')
        self.stdout.write('   Clave: actas_pastaza_2025')
        self.stdout.write('')
        self.stdout.write('🔄 Usuario adicional para BD:')
        self.stdout.write('   Usuario: desarrollador_actas')
        self.stdout.write('   Clave: dev_actas_2025')
        self.stdout.write('='*60)
