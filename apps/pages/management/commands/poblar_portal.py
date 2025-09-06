from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.pages.models import TipoSesion, EstadoActa, ActaMunicipal
from datetime import datetime, timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de demostración para el Portal Ciudadano'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Iniciando población de datos del Portal Ciudadano...\n')
        
        self.crear_tipos_sesion()
        self.crear_estados_acta()
        self.crear_actas_demo()
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ ¡Proceso completado exitosamente!')
        )
        self.stdout.write(f'📊 Estadísticas:')
        self.stdout.write(f'   - Tipos de sesión: {TipoSesion.objects.count()}')
        self.stdout.write(f'   - Estados de acta: {EstadoActa.objects.count()}')
        self.stdout.write(f'   - Actas municipales: {ActaMunicipal.objects.count()}')
        self.stdout.write(f'\n🌐 Accede al Portal Ciudadano en: http://localhost:8000/portal-ciudadano/')

    def crear_tipos_sesion(self):
        """Crear tipos de sesión"""
        self.stdout.write('📋 Creando tipos de sesión...')
        
        tipos = [
            {
                'nombre': 'ordinaria',
                'descripcion': 'Sesiones regulares del consejo municipal',
                'color': '#007bff',
                'icono': 'fas fa-calendar-check'
            },
            {
                'nombre': 'extraordinaria', 
                'descripcion': 'Sesiones especiales convocadas por urgencia',
                'color': '#ffc107',
                'icono': 'fas fa-exclamation-triangle'
            },
            {
                'nombre': 'solemne',
                'descripcion': 'Sesiones ceremoniales y protocolarias',
                'color': '#6f42c1',
                'icono': 'fas fa-crown'
            },
            {
                'nombre': 'publica',
                'descripcion': 'Audiencias públicas con participación ciudadana',
                'color': '#28a745',
                'icono': 'fas fa-users'
            },
            {
                'nombre': 'comision',
                'descripcion': 'Reuniones de comisiones especializadas',
                'color': '#17a2b8',
                'icono': 'fas fa-user-friends'
            }
        ]
        
        for tipo_data in tipos:
            tipo, created = TipoSesion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(f"✓ Creado tipo de sesión: {tipo.get_nombre_display()}")

    def crear_estados_acta(self):
        """Crear estados de actas"""
        self.stdout.write('\n📊 Creando estados de actas...')
        
        estados = [
            {'nombre': 'borrador', 'descripcion': 'Acta en preparación', 'color': '#6c757d', 'orden': 1},
            {'nombre': 'transcripcion', 'descripcion': 'En proceso de transcripción', 'color': '#fd7e14', 'orden': 2},
            {'nombre': 'revision', 'descripcion': 'En revisión por secretaría', 'color': '#ffc107', 'orden': 3},
            {'nombre': 'aprobada', 'descripcion': 'Aprobada por el consejo', 'color': '#20c997', 'orden': 4},
            {'nombre': 'publicada', 'descripcion': 'Publicada oficialmente', 'color': '#28a745', 'orden': 5},
            {'nombre': 'archivada', 'descripcion': 'Archivada en repositorio', 'color': '#6f42c1', 'orden': 6},
        ]
        
        for estado_data in estados:
            estado, created = EstadoActa.objects.get_or_create(
                nombre=estado_data['nombre'],
                defaults=estado_data
            )
            if created:
                self.stdout.write(f"✓ Creado estado: {estado.get_nombre_display()}")

    def crear_actas_demo(self):
        """Crear actas de demostración"""
        self.stdout.write('\n📄 Creando actas de demostración...')
        
        # Crear usuario secretario si no existe
        secretario, created = User.objects.get_or_create(
            username='secretario_municipal',
            defaults={
                'first_name': 'María',
                'last_name': 'González',
                'email': 'secretario@municipio.gob.ec',
                'is_staff': True
            }
        )
        
        if created:
            secretario.set_password('demo123')
            secretario.save()
            self.stdout.write(f"✓ Creado usuario secretario: {secretario.get_full_name()}")
        
        # Datos de ejemplo para actas
        actas_data = [
            {
                'titulo': 'Aprobación del Presupuesto Municipal 2025',
                'resumen': 'Sesión ordinaria para la aprobación del presupuesto participativo del municipio para el año fiscal 2025, incluyendo inversiones en infraestructura, servicios básicos y programas sociales.',
                'presidente': 'Dr. Carlos Mendoza - Alcalde',
                'tipo': 'ordinaria',
                'acceso': 'publico',
                'transcripcion_ia': True,
                'precision_ia': 97.5
            },
            {
                'titulo': 'Declaratoria de Emergencia por Deslizamientos',
                'resumen': 'Sesión extraordinaria convocada por la emergencia causada por los deslizamientos en el sector La Esperanza, para tomar medidas urgentes de atención a las familias afectadas.',
                'presidente': 'Dr. Carlos Mendoza - Alcalde',
                'tipo': 'extraordinaria',
                'acceso': 'publico',
                'transcripcion_ia': True,
                'precision_ia': 95.2
            },
            {
                'titulo': 'Audiencia Pública - Reforma al Plan de Ordenamiento Territorial',
                'resumen': 'Audiencia pública para socializar las propuestas de reforma al Plan de Ordenamiento Territorial (POT) 2025-2035 y recibir observaciones de la ciudadanía.',
                'presidente': 'Ing. Ana Rodríguez - Presidenta del Concejo',
                'tipo': 'publica',
                'acceso': 'publico',
                'transcripcion_ia': False,
            },
            {
                'titulo': 'Sesión Solemne - 150 Años de Fundación del Cantón',
                'resumen': 'Sesión solemne conmemorativa de los 150 años de fundación del cantón, con reconocimientos a personalidades destacadas y presentación de proyectos emblemáticos.',
                'presidente': 'Dr. Carlos Mendoza - Alcalde',
                'tipo': 'solemne',
                'acceso': 'publico',
                'transcripcion_ia': True,
                'precision_ia': 98.1
            },
            {
                'titulo': 'Comisión de Obras Públicas - Proyecto Vial Urbano',
                'resumen': 'Reunión de la comisión de obras públicas para evaluar las propuestas técnicas del proyecto de mejoramiento vial del casco urbano.',
                'presidente': 'Ing. Ana Rodríguez - Presidenta de Comisión',
                'tipo': 'comision',
                'acceso': 'restringido',
                'transcripcion_ia': True,
                'precision_ia': 94.8
            },
            {
                'titulo': 'Aprobación de Ordenanza de Gestión de Residuos Sólidos',
                'resumen': 'Sesión para el segundo debate y aprobación definitiva de la ordenanza municipal para la gestión integral de residuos sólidos y reciclaje.',
                'presidente': 'Dr. Carlos Mendoza - Alcalde',
                'tipo': 'ordinaria',
                'acceso': 'publico',
                'transcripcion_ia': True,
                'precision_ia': 96.3
            }
        ]
        
        # Crear las actas
        base_date = timezone.now() - timedelta(days=90)
        
        for i, acta_data in enumerate(actas_data):
            # Calcular fecha de sesión (últimos 3 meses)
            fecha_sesion = base_date + timedelta(days=i*15 + random.randint(0, 10))
            
            # Obtener tipo y estado
            tipo_sesion = TipoSesion.objects.get(nombre=acta_data['tipo'])
            
            # Asignar estado basado en la fecha
            if fecha_sesion < timezone.now() - timedelta(days=30):
                estado = EstadoActa.objects.get(nombre='publicada')
            elif fecha_sesion < timezone.now() - timedelta(days=15):
                estado = EstadoActa.objects.get(nombre='aprobada')
            else:
                estado = EstadoActa.objects.get(nombre='revision')
            
            # Crear el acta
            acta, created = ActaMunicipal.objects.get_or_create(
                numero_acta=f"ACT-{2025:04d}-{i+1:03d}",
                defaults={
                    'titulo': acta_data['titulo'],
                    'numero_sesion': f"{i+1:03d}/2025",
                    'tipo_sesion': tipo_sesion,
                    'estado': estado,
                    'fecha_sesion': fecha_sesion,
                    'fecha_publicacion': fecha_sesion + timedelta(days=5) if estado.nombre == 'publicada' else None,
                    'resumen': acta_data['resumen'],
                    'contenido': f"ACTA DE LA SESIÓN {acta_data['tipo'].upper()}\n\n" + 
                               f"Fecha: {fecha_sesion.strftime('%d de %B de %Y')}\n" +
                               f"Hora: {fecha_sesion.strftime('%H:%M')}\n\n" +
                               acta_data['resumen'] + "\n\n" +
                               "El contenido completo del acta incluye todos los debates, intervenciones y decisiones tomadas durante la sesión.",
                    'acceso': acta_data.get('acceso', 'publico'),
                    'secretario': secretario,
                    'presidente': acta_data['presidente'],
                    'transcripcion_ia': acta_data.get('transcripcion_ia', False),
                    'precision_ia': acta_data.get('precision_ia', None),
                    'palabras_clave': f"municipal, {acta_data['tipo']}, 2025, {tipo_sesion.get_nombre_display().lower()}",
                    'prioridad': 'alta' if acta_data['tipo'] == 'extraordinaria' else 'normal',
                    'activo': True
                }
            )
            
            if created:
                self.stdout.write(f"✓ Creada acta: {acta.numero_acta} - {acta.titulo[:50]}...")
