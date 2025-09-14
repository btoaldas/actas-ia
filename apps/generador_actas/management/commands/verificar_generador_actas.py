"""
Comando de gestión para verificar el estado del módulo Generador de Actas
"""

from django.core.management.base import BaseCommand
from django.db import connection
from apps.generador_actas.models import (
    ProveedorIA, SegmentoPlantilla, PlantillaActa, 
    ConfiguracionSegmento, ActaGenerada
)
from apps.generador_actas.ia_providers import get_ia_provider


class Command(BaseCommand):
    help = 'Verifica el estado y configuración del módulo Generador de Actas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Mostrar información detallada',
        )
        parser.add_argument(
            '--test-ia',
            action='store_true',
            help='Probar conectividad con proveedores IA',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== ESTADO DEL MÓDULO GENERADOR DE ACTAS ===\n')
        )

        # Verificar base de datos
        self.verificar_base_datos()
        
        # Verificar modelos
        self.verificar_modelos(options['detailed'])
        
        # Verificar proveedores IA
        if options['test_ia']:
            self.probar_proveedores_ia()

        self.stdout.write(
            self.style.SUCCESS('\n=== VERIFICACIÓN COMPLETADA ===')
        )

    def verificar_base_datos(self):
        """Verificar conectividad y tablas de base de datos"""
        self.stdout.write('📊 VERIFICACIÓN DE BASE DE DATOS')
        
        try:
            with connection.cursor() as cursor:
                # Verificar que las tablas existen
                tablas_esperadas = [
                    'generador_actas_proveedoria',
                    'generador_actas_segmentoplantilla',
                    'generador_actas_plantillaacta',
                    'generador_actas_configuracionsegmento',
                    'generador_actas_actagenerada'
                ]
                
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name LIKE 'generador_actas_%'
                """)
                tablas_existentes = [row[0] for row in cursor.fetchall()]
                
                for tabla in tablas_esperadas:
                    if tabla in tablas_existentes:
                        self.stdout.write(f'  ✓ Tabla {tabla} existe')
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'  ✗ Tabla {tabla} NO existe')
                        )
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Error de base de datos: {str(e)}')
            )
        
        self.stdout.write('')

    def verificar_modelos(self, detailed=False):
        """Verificar estado de los modelos"""
        self.stdout.write('📋 VERIFICACIÓN DE MODELOS')
        
        # Proveedores IA
        proveedores_total = ProveedorIA.objects.count()
        proveedores_activos = ProveedorIA.objects.filter(activo=True).count()
        self.stdout.write(f'  📡 Proveedores IA: {proveedores_total} total, {proveedores_activos} activos')
        
        if detailed and proveedores_total > 0:
            for proveedor in ProveedorIA.objects.all():
                estado = "🟢" if proveedor.activo else "🔴"
                self.stdout.write(f'    {estado} {proveedor.nombre} ({proveedor.tipo})')
        
        # Segmentos
        segmentos_total = SegmentoPlantilla.objects.count()
        segmentos_reutilizables = SegmentoPlantilla.objects.filter(reutilizable=True).count()
        self.stdout.write(f'  📝 Segmentos: {segmentos_total} total, {segmentos_reutilizables} reutilizables')
        
        if detailed and segmentos_total > 0:
            categorias = SegmentoPlantilla.objects.values_list('categoria', flat=True).distinct()
            for categoria in categorias:
                count = SegmentoPlantilla.objects.filter(categoria=categoria).count()
                self.stdout.write(f'    📂 {categoria}: {count} segmentos')
        
        # Plantillas
        plantillas_total = PlantillaActa.objects.count()
        plantillas_activas = PlantillaActa.objects.filter(activa=True).count()
        self.stdout.write(f'  📄 Plantillas: {plantillas_total} total, {plantillas_activas} activas')
        
        if detailed and plantillas_total > 0:
            for plantilla in PlantillaActa.objects.all():
                segmentos_count = plantilla.segmentos.count()
                estado = "🟢" if plantilla.activa else "🔴"
                self.stdout.write(f'    {estado} {plantilla.nombre} ({segmentos_count} segmentos)')
        
        # Configuraciones
        configuraciones_total = ConfiguracionSegmento.objects.count()
        self.stdout.write(f'  ⚙️  Configuraciones: {configuraciones_total} total')
        
        # Actas generadas
        actas_total = ActaGenerada.objects.count()
        if actas_total > 0:
            actas_por_estado = {}
            for estado in ['borrador', 'pendiente', 'procesando', 'procesando_segmentos', 'unificando', 'revision', 'aprobado', 'publicado', 'rechazado', 'error']:
                count = ActaGenerada.objects.filter(estado=estado).count()
                if count > 0:
                    actas_por_estado[estado] = count
            
            self.stdout.write(f'  📊 Actas generadas: {actas_total} total')
            for estado, count in actas_por_estado.items():
                emoji = {'borrador': '📝', 'pendiente': '⏳', 'procesando': '⚡', 'revision': '👁', 'aprobado': '✅', 'publicado': '🌐', 'error': '❌'}
                self.stdout.write(f'    {emoji.get(estado, "•")} {estado}: {count}')
        else:
            self.stdout.write('  📊 Actas generadas: 0 (ninguna generada aún)')
        
        self.stdout.write('')

    def probar_proveedores_ia(self):
        """Probar conectividad con proveedores IA activos"""
        self.stdout.write('🤖 PRUEBA DE PROVEEDORES IA')
        
        proveedores_activos = ProveedorIA.objects.filter(activo=True)
        
        if not proveedores_activos.exists():
            self.stdout.write('  ⚠️  No hay proveedores IA activos para probar')
            return
        
        for proveedor in proveedores_activos:
            self.stdout.write(f'  🔍 Probando {proveedor.nombre}...')
            
            try:
                # Crear instancia del proveedor
                instancia_proveedor = get_ia_provider(proveedor)
                
                # Validar configuración
                if instancia_proveedor.validar_configuracion():
                    self.stdout.write(f'    ✅ Configuración válida')
                    
                    # Probar generación de contenido (solo validación rápida)
                    try:
                        # No hacer llamada real para evitar costos, solo verificar que el método existe
                        if hasattr(instancia_proveedor, 'generar_contenido'):
                            self.stdout.write(f'    ✅ Método de generación disponible')
                        else:
                            self.stdout.write(f'    ❌ Método de generación no disponible')
                    except Exception as e:
                        self.stdout.write(f'    ⚠️  Error en prueba de generación: {str(e)}')
                else:
                    self.stdout.write(f'    ❌ Configuración inválida')
                    
            except Exception as e:
                self.stdout.write(f'    ❌ Error al crear proveedor: {str(e)}')
        
        self.stdout.write('')

    def verificar_dependencias(self):
        """Verificar dependencias del módulo"""
        self.stdout.write('📦 VERIFICACIÓN DE DEPENDENCIAS')
        
        dependencias = [
            ('celery', 'Procesamiento asíncrono'),
            ('requests', 'Llamadas HTTP a APIs'),
            ('openai', 'Proveedor OpenAI (opcional)'),
            ('anthropic', 'Proveedor Claude (opcional)'),
            ('google-generativeai', 'Proveedor Gemini (opcional)')
        ]
        
        for dependencia, descripcion in dependencias:
            try:
                __import__(dependencia)
                self.stdout.write(f'  ✅ {dependencia}: Disponible ({descripcion})')
            except ImportError:
                self.stdout.write(f'  ⚠️  {dependencia}: No disponible ({descripcion})')
        
        self.stdout.write('')