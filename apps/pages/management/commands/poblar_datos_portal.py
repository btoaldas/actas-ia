from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.pages.models import ActaMunicipal, TipoSesion, EstadoActa, VisualizacionActa, DescargaActa
from datetime import datetime, timedelta
import random
from faker import Faker

class Command(BaseCommand):
    help = 'Poblar la base de datos con datos de prueba para el Portal Ciudadano'

    def add_arguments(self, parser):
        parser.add_argument(
            '--actas',
            type=int,
            default=50,
            help='Número de actas a crear'
        )
        parser.add_argument(
            '--visualizaciones',
            type=int,
            default=200,
            help='Número de visualizaciones a crear'
        )
        parser.add_argument(
            '--descargas',
            type=int,
            default=80,
            help='Número de descargas a crear'
        )

    def handle(self, *args, **options):
        fake = Faker('es_ES')
        
        self.stdout.write('Iniciando poblado de datos...')
        
        # Crear tipos de sesión si no existen
        tipos_sesion, created = TipoSesion.objects.get_or_create(
            nombre='ordinaria',
            defaults={'descripcion': 'Sesión Ordinaria', 'activo': True}
        )
        if created:
            self.stdout.write(f'Creado tipo de sesión: {tipos_sesion.nombre}')
        
        tipo_extraordinaria, created = TipoSesion.objects.get_or_create(
            nombre='extraordinaria',
            defaults={'descripcion': 'Sesión Extraordinaria', 'activo': True}
        )
        if created:
            self.stdout.write(f'Creado tipo de sesión: {tipo_extraordinaria.nombre}')
        
        tipo_comision, created = TipoSesion.objects.get_or_create(
            nombre='comision',
            defaults={'descripcion': 'Sesión de Comisión', 'activo': True}
        )
        if created:
            self.stdout.write(f'Creado tipo de sesión: {tipo_comision.nombre}')
        
        # Crear estados si no existen
        estado_borrador, created = EstadoActa.objects.get_or_create(
            nombre='borrador',
            defaults={'descripcion': 'En Borrador', 'activo': True}
        )
        if created:
            self.stdout.write(f'Creado estado: {estado_borrador.nombre}')
        
        estado_revision, created = EstadoActa.objects.get_or_create(
            nombre='revision',
            defaults={'descripcion': 'En Revisión', 'activo': True}
        )
        if created:
            self.stdout.write(f'Creado estado: {estado_revision.nombre}')
        
        estado_publicada, created = EstadoActa.objects.get_or_create(
            nombre='publicada',
            defaults={'descripcion': 'Publicada', 'activo': True}
        )
        if created:
            self.stdout.write(f'Creado estado: {estado_publicada.nombre}')
        
        # Crear actas municipales
        num_actas = options['actas']
        actas_creadas = 0
        
        tipos_lista = [tipos_sesion, tipo_extraordinaria, tipo_comision]
        estados_lista = [estado_borrador, estado_revision, estado_publicada]
        acceso_opciones = ['publico', 'restringido', 'privado']
        
        for i in range(num_actas):
            fecha_sesion = fake.date_between(start_date='-2y', end_date='today')
            fecha_creacion = fecha_sesion + timedelta(days=random.randint(1, 7))
            
            acta = ActaMunicipal.objects.create(
                numero_acta=f'ACT-{fecha_sesion.year}-{str(i+1).zfill(3)}',
                titulo=f'Sesión {random.choice(["Ordinaria", "Extraordinaria", "de Comisión"])} - {fake.catch_phrase()}',
                tipo_sesion=random.choice(tipos_lista),
                estado=random.choice(estados_lista),
                fecha_sesion=fecha_sesion,
                fecha_creacion=fecha_creacion,
                resumen=fake.text(max_nb_chars=300),
                contenido=fake.text(max_nb_chars=2000),
                presidente=fake.name(),
                secretario=fake.name(),
                participantes=fake.text(max_nb_chars=200),
                acceso=random.choice(acceso_opciones),
                palabras_clave=', '.join(fake.words(nb=random.randint(3, 8))),
                precision_ia=random.uniform(85.0, 98.5) if random.choice([True, False]) else None,
                transcripcion_ia=fake.text(max_nb_chars=1500) if random.choice([True, False]) else None,
                activo=True
            )
            actas_creadas += 1
            
            if actas_creadas % 10 == 0:
                self.stdout.write(f'Creadas {actas_creadas} actas...')
        
        self.stdout.write(f'✓ Creadas {actas_creadas} actas municipales')
        
        # Crear visualizaciones
        num_visualizaciones = options['visualizaciones']
        actas_existentes = list(ActaMunicipal.objects.filter(activo=True))
        usuarios = list(User.objects.all())
        
        visualizaciones_creadas = 0
        for i in range(num_visualizaciones):
            acta = random.choice(actas_existentes)
            usuario = random.choice(usuarios) if random.choice([True, False]) else None
            fecha_vis = fake.date_time_between(start_date='-6m', end_date='now')
            
            VisualizacionActa.objects.create(
                acta=acta,
                usuario=usuario,
                ip_address=fake.ipv4(),
                user_agent=fake.user_agent(),
                fecha=fecha_vis
            )
            visualizaciones_creadas += 1
            
            if visualizaciones_creadas % 50 == 0:
                self.stdout.write(f'Creadas {visualizaciones_creadas} visualizaciones...')
        
        self.stdout.write(f'✓ Creadas {visualizaciones_creadas} visualizaciones')
        
        # Crear descargas
        num_descargas = options['descargas']
        descargas_creadas = 0
        
        for i in range(num_descargas):
            acta = random.choice(actas_existentes)
            usuario = random.choice(usuarios) if random.choice([True, False]) else None
            fecha_desc = fake.date_time_between(start_date='-6m', end_date='now')
            
            DescargaActa.objects.create(
                acta=acta,
                usuario=usuario,
                ip_address=fake.ipv4(),
                fecha=fecha_desc
            )
            descargas_creadas += 1
            
            if descargas_creadas % 20 == 0:
                self.stdout.write(f'Creadas {descargas_creadas} descargas...')
        
        self.stdout.write(f'✓ Creadas {descargas_creadas} descargas')
        
        # Estadísticas finales
        total_actas = ActaMunicipal.objects.filter(activo=True).count()
        total_visualizaciones = VisualizacionActa.objects.count()
        total_descargas = DescargaActa.objects.count()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('DATOS CREADOS EXITOSAMENTE'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'📋 Actas municipales: {total_actas}')
        self.stdout.write(f'👁️  Visualizaciones: {total_visualizaciones}')
        self.stdout.write(f'⬇️  Descargas: {total_descargas}')
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('Ya puedes ver las métricas reales en el Portal Ciudadano!')
