from django.core.management.base import BaseCommand
from apps.pages.models import IndicadorTransparencia, MetricaTransparencia, EstadisticaMunicipal, ProyectoMunicipal
from datetime import datetime, timedelta
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Poblar datos de ejemplo para el Portal de Transparencia'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Iniciando población de datos de transparencia...')
        
        # Crear indicadores de transparencia
        self.crear_indicadores()
        
        # Crear métricas históricas
        self.crear_metricas()
        
        # Crear estadísticas municipales
        self.crear_estadisticas()
        
        # Crear proyectos municipales
        self.crear_proyectos()
        
        self.stdout.write(self.style.SUCCESS('✅ Población de datos completada exitosamente!'))

    def crear_indicadores(self):
        self.stdout.write('📊 Creando indicadores de transparencia...')
        
        indicadores = [
            {
                'nombre': 'Cumplimiento de Plazos',
                'descripcion': 'Porcentaje de actas publicadas dentro del plazo legal',
                'categoria': 'cumplimiento',
                'tipo': 'porcentaje',
                'icono': 'fas fa-clock',
                'color': '#28a745',
                'orden': 1
            },
            {
                'nombre': 'Tiempo Promedio Publicación',
                'descripcion': 'Tiempo promedio desde sesión hasta publicación',
                'categoria': 'tiempo_respuesta',
                'tipo': 'tiempo',
                'icono': 'fas fa-stopwatch',
                'color': '#007bff',
                'orden': 2
            },
            {
                'nombre': 'Participación Ciudadana',
                'descripcion': 'Número de visualizaciones de actas por mes',
                'categoria': 'participacion',
                'tipo': 'numero',
                'icono': 'fas fa-users',
                'color': '#ffc107',
                'orden': 3
            },
            {
                'nombre': 'Calidad de Información',
                'descripcion': 'Puntuación de completitud de documentos',
                'categoria': 'calidad',
                'tipo': 'puntuacion',
                'icono': 'fas fa-star',
                'color': '#e83e8c',
                'orden': 4
            },
            {
                'nombre': 'Accesibilidad Digital',
                'descripcion': 'Porcentaje de documentos en formato accesible',
                'categoria': 'accesibilidad',
                'tipo': 'porcentaje',
                'icono': 'fas fa-universal-access',
                'color': '#6f42c1',
                'orden': 5
            },
            {
                'nombre': 'Transparencia Presupuestal',
                'descripcion': 'Porcentaje de ejecución presupuestal publicada',
                'categoria': 'publicacion',
                'tipo': 'porcentaje',
                'icono': 'fas fa-dollar-sign',
                'color': '#20c997',
                'orden': 6
            },
        ]
        
        for indicador_data in indicadores:
            indicador, created = IndicadorTransparencia.objects.get_or_create(
                nombre=indicador_data['nombre'],
                defaults=indicador_data
            )
            if created:
                self.stdout.write(f'✓ Creado indicador: {indicador.nombre}')

    def crear_metricas(self):
        self.stdout.write('📈 Creando métricas históricas...')
        
        indicadores = IndicadorTransparencia.objects.all()
        fecha_inicio = datetime.now().date() - timedelta(days=365)
        
        for indicador in indicadores:
            # Generar datos para los últimos 12 meses
            for i in range(12):
                fecha = fecha_inicio + timedelta(days=i * 30)
                mes = fecha.month
                año = fecha.year
                
                # Generar valores según el tipo de indicador
                if indicador.tipo == 'porcentaje':
                    valor = round(random.uniform(85, 98), 2)
                elif indicador.tipo == 'tiempo':
                    valor = round(random.uniform(1, 5), 1)
                elif indicador.tipo == 'puntuacion':
                    valor = round(random.uniform(7, 10), 1)
                else:  # numero
                    valor = random.randint(50, 200)
                
                metrica, created = MetricaTransparencia.objects.get_or_create(
                    indicador=indicador,
                    fecha=fecha,
                    defaults={
                        'valor': Decimal(str(valor)),
                        'mes': mes,
                        'año': año,
                        'observaciones': f'Valor generado automáticamente para {fecha.strftime("%B %Y")}'
                    }
                )
                
                if created and i == 0:  # Solo mostrar el primer mensaje por indicador
                    self.stdout.write(f'✓ Métricas creadas para: {indicador.nombre}')

    def crear_estadisticas(self):
        self.stdout.write('📊 Creando estadísticas municipales...')
        
        estadisticas = [
            {
                'nombre': 'Población Total',
                'categoria': 'poblacion',
                'valor': 45680,
                'unidad': 'habitantes',
                'fuente': 'DANE - Proyecciones de población',
                'descripcion': 'Población total proyectada para el municipio',
                'icono': 'fas fa-users',
                'color': '#007bff'
            },
            {
                'nombre': 'Presupuesto Municipal',
                'categoria': 'economia',
                'valor': 15500000000,
                'unidad': 'COP',
                'fuente': 'Secretaría de Hacienda',
                'descripcion': 'Presupuesto total aprobado para la vigencia',
                'icono': 'fas fa-dollar-sign',
                'color': '#28a745'
            },
            {
                'nombre': 'Cobertura Acueducto',
                'categoria': 'servicios',
                'valor': 94.5,
                'unidad': '%',
                'fuente': 'Empresa de Servicios Públicos',
                'descripcion': 'Porcentaje de hogares con acceso al servicio',
                'icono': 'fas fa-tint',
                'color': '#17a2b8'
            },
            {
                'nombre': 'Vías Pavimentadas',
                'categoria': 'infraestructura',
                'valor': 78.2,
                'unidad': 'km',
                'fuente': 'Secretaría de Infraestructura',
                'descripcion': 'Kilómetros de vías urbanas pavimentadas',
                'icono': 'fas fa-road',
                'color': '#6c757d'
            },
            {
                'nombre': 'Cobertura Educativa',
                'categoria': 'social',
                'valor': 96.8,
                'unidad': '%',
                'fuente': 'Secretaría de Educación',
                'descripcion': 'Porcentaje de niños en edad escolar matriculados',
                'icono': 'fas fa-graduation-cap',
                'color': '#e83e8c'
            },
            {
                'nombre': 'Áreas Verdes',
                'categoria': 'medio_ambiente',
                'valor': 12.5,
                'unidad': 'm²/hab',
                'fuente': 'Secretaría de Medio Ambiente',
                'descripcion': 'Metros cuadrados de área verde por habitante',
                'icono': 'fas fa-leaf',
                'color': '#20c997'
            },
            {
                'nombre': 'Eficiencia Administrativa',
                'categoria': 'gobierno',
                'valor': 87.3,
                'unidad': '%',
                'fuente': 'Oficina de Control Interno',
                'descripcion': 'Índice de eficiencia en procesos administrativos',
                'icono': 'fas fa-building',
                'color': '#fd7e14'
            },
            {
                'nombre': 'Inversión Social',
                'categoria': 'economia',
                'valor': 3200000000,
                'unidad': 'COP',
                'fuente': 'Secretaría de Planeación',
                'descripcion': 'Recursos destinados a programas sociales',
                'icono': 'fas fa-hand-holding-heart',
                'color': '#dc3545'
            },
        ]
        
        fecha_actual = datetime.now().date()
        
        for stat_data in estadisticas:
            stat_data['fecha'] = fecha_actual
            estadistica, created = EstadisticaMunicipal.objects.get_or_create(
                nombre=stat_data['nombre'],
                fecha=fecha_actual,
                defaults=stat_data
            )
            if created:
                self.stdout.write(f'✓ Creada estadística: {estadistica.nombre}')

    def crear_proyectos(self):
        self.stdout.write('🏗️ Creando proyectos municipales...')
        
        proyectos = [
            {
                'nombre': 'Construcción Centro de Salud San Pedro',
                'descripcion': 'Construcción de un moderno centro de salud para atender a la población del sector rural',
                'categoria': 'infraestructura',
                'estado': 'en_ejecucion',
                'presupuesto_total': 2500000000,
                'presupuesto_ejecutado': 1750000000,
                'fecha_inicio': datetime.now().date() - timedelta(days=180),
                'fecha_fin_estimada': datetime.now().date() + timedelta(days=120),
                'porcentaje_avance': 70.0,
                'responsable': 'Secretaría de Salud',
                'contratista': 'Constructora ABC S.A.S.',
                'ubicacion': 'Vereda San Pedro',
                'beneficiarios_estimados': 3500
            },
            {
                'nombre': 'Programa de Alimentación Escolar',
                'descripcion': 'Fortalecimiento del programa de alimentación escolar con enfoque nutricional',
                'categoria': 'social',
                'estado': 'en_ejecucion',
                'presupuesto_total': 800000000,
                'presupuesto_ejecutado': 400000000,
                'fecha_inicio': datetime.now().date() - timedelta(days=90),
                'fecha_fin_estimada': datetime.now().date() + timedelta(days=275),
                'porcentaje_avance': 50.0,
                'responsable': 'Secretaría de Educación',
                'contratista': '',
                'ubicacion': 'Todas las instituciones educativas',
                'beneficiarios_estimados': 5200
            },
            {
                'nombre': 'Pavimentación Barrio La Esperanza',
                'descripcion': 'Pavimentación de vías principales del barrio La Esperanza',
                'categoria': 'infraestructura',
                'estado': 'finalizado',
                'presupuesto_total': 1200000000,
                'presupuesto_ejecutado': 1200000000,
                'fecha_inicio': datetime.now().date() - timedelta(days=300),
                'fecha_fin_estimada': datetime.now().date() - timedelta(days=30),
                'fecha_fin_real': datetime.now().date() - timedelta(days=30),
                'porcentaje_avance': 100.0,
                'responsable': 'Secretaría de Infraestructura',
                'contratista': 'Pavimentos del Norte Ltda.',
                'ubicacion': 'Barrio La Esperanza',
                'beneficiarios_estimados': 1200
            },
            {
                'nombre': 'Parque Ecológico Municipal',
                'descripcion': 'Creación de un parque ecológico con senderos, zonas recreativas y área de conservación',
                'categoria': 'medio_ambiente',
                'estado': 'aprobado',
                'presupuesto_total': 1800000000,
                'presupuesto_ejecutado': 0,
                'fecha_inicio': datetime.now().date() + timedelta(days=30),
                'fecha_fin_estimada': datetime.now().date() + timedelta(days=365),
                'porcentaje_avance': 0.0,
                'responsable': 'Secretaría de Medio Ambiente',
                'contratista': '',
                'ubicacion': 'Zona Norte del Municipio',
                'beneficiarios_estimados': 45000
            },
            {
                'nombre': 'Programa Emprendimiento Juvenil',
                'descripcion': 'Capacitación y financiación para jóvenes emprendedores del municipio',
                'categoria': 'economia',
                'estado': 'en_ejecucion',
                'presupuesto_total': 500000000,
                'presupuesto_ejecutado': 150000000,
                'fecha_inicio': datetime.now().date() - timedelta(days=60),
                'fecha_fin_estimada': datetime.now().date() + timedelta(days=305),
                'porcentaje_avance': 30.0,
                'responsable': 'Secretaría de Desarrollo Económico',
                'contratista': '',
                'ubicacion': 'Casa de la Cultura',
                'beneficiarios_estimados': 200
            },
            {
                'nombre': 'Centro Cultural y Recreativo',
                'descripcion': 'Adecuación de espacios para actividades culturales y recreativas',
                'categoria': 'cultura',
                'estado': 'planificacion',
                'presupuesto_total': 900000000,
                'presupuesto_ejecutado': 0,
                'fecha_inicio': datetime.now().date() + timedelta(days=90),
                'fecha_fin_estimada': datetime.now().date() + timedelta(days=455),
                'porcentaje_avance': 0.0,
                'responsable': 'Secretaría de Cultura',
                'contratista': '',
                'ubicacion': 'Centro del Municipio',
                'beneficiarios_estimados': 8000
            },
        ]
        
        for proyecto_data in proyectos:
            proyecto, created = ProyectoMunicipal.objects.get_or_create(
                nombre=proyecto_data['nombre'],
                defaults=proyecto_data
            )
            if created:
                self.stdout.write(f'✓ Creado proyecto: {proyecto.nombre}')
