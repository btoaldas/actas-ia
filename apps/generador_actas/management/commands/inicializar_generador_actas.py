"""
Comando de gestión para inicializar datos del módulo Generador de Actas
Este comando crea proveedores IA, segmentos y plantillas por defecto
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.generador_actas.models import (
    ProveedorIA, SegmentoPlantilla, PlantillaActa, ConfiguracionSegmento
)


class Command(BaseCommand):
    help = 'Inicializa datos por defecto para el módulo Generador de Actas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de datos existentes',
        )
        parser.add_argument(
            '--proveedores-only',
            action='store_true',
            help='Solo crear proveedores IA',
        )
        parser.add_argument(
            '--segmentos-only',
            action='store_true',
            help='Solo crear segmentos de plantilla',
        )
        parser.add_argument(
            '--plantillas-only',
            action='store_true',
            help='Solo crear plantillas por defecto',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando configuración de datos por defecto...')
        )

        try:
            with transaction.atomic():
                if options['proveedores_only']:
                    self.crear_proveedores_ia(options['force'])
                elif options['segmentos_only']:
                    self.crear_segmentos_plantilla(options['force'])
                elif options['plantillas_only']:
                    self.crear_plantillas_por_defecto(options['force'])
                else:
                    # Crear todo en orden
                    self.crear_proveedores_ia(options['force'])
                    self.crear_segmentos_plantilla(options['force'])
                    self.crear_plantillas_por_defecto(options['force'])

            self.stdout.write(
                self.style.SUCCESS('✓ Configuración completada exitosamente')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la configuración: {str(e)}')
            )
            raise

    def crear_proveedores_ia(self, force=False):
        """Crear proveedores IA por defecto"""
        self.stdout.write('Configurando proveedores IA...')
        
        proveedores_data = [
            {
                'nombre': 'OpenAI GPT-4',
                'tipo': 'openai',
                'modelo': 'gpt-4',
                'temperatura': 0.7,
                'max_tokens': 2000,
                'timeout': 30,
                'configuracion_adicional': {
                    'top_p': 0.9,
                    'frequency_penalty': 0.0,
                    'presence_penalty': 0.0
                },
                'activo': True,
                'costo_por_1k_tokens': 0.03
            },
            {
                'nombre': 'OpenAI GPT-3.5 Turbo',
                'tipo': 'openai',
                'modelo': 'gpt-3.5-turbo',
                'temperatura': 0.7,
                'max_tokens': 1500,
                'timeout': 25,
                'configuracion_adicional': {
                    'top_p': 0.9,
                    'frequency_penalty': 0.0,
                    'presence_penalty': 0.0
                },
                'activo': True,
                'costo_por_1k_tokens': 0.002
            },
            {
                'nombre': 'DeepSeek Chat',
                'tipo': 'deepseek',
                'modelo': 'deepseek-chat',
                'temperatura': 0.7,
                'max_tokens': 2000,
                'timeout': 35,
                'configuracion_adicional': {
                    'top_p': 0.95,
                    'frequency_penalty': 0.0,
                    'presence_penalty': 0.0
                },
                'activo': False,  # Desactivado por defecto hasta configuración
                'costo_por_1k_tokens': 0.001
            },
            {
                'nombre': 'Claude 3 Sonnet',
                'tipo': 'anthropic',
                'modelo': 'claude-3-sonnet-20240229',
                'temperatura': 0.7,
                'max_tokens': 2000,
                'timeout': 40,
                'configuracion_adicional': {
                    'top_p': 0.9,
                    'top_k': 40
                },
                'activo': False,  # Desactivado por defecto
                'costo_por_1k_tokens': 0.015
            },
            {
                'nombre': 'Google Gemini Pro',
                'tipo': 'google',
                'modelo': 'gemini-pro',
                'temperatura': 0.7,
                'max_tokens': 2000,
                'timeout': 30,
                'configuracion_adicional': {
                    'top_p': 0.8,
                    'top_k': 40
                },
                'activo': False,  # Desactivado por defecto
                'costo_por_1k_tokens': 0.001
            },
            {
                'nombre': 'Ollama Local',
                'tipo': 'ollama',
                'modelo': 'llama2',
                'api_url': 'http://localhost:11434',
                'temperatura': 0.7,
                'max_tokens': 4000,
                'timeout': 60,  # Más tiempo para procesamiento local
                'configuracion_adicional': {
                    'top_p': 0.9,
                    'num_predict': 2000
                },
                'activo': False,  # Requiere configuración local
                'costo_por_1k_tokens': 0.0  # Sin costo en local
            }
        ]

        created_count = 0
        for proveedor_data in proveedores_data:
            # Necesitamos el usuario para crear el proveedor
            from django.contrib.auth.models import User
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR('No hay usuarios superusuarios. Crear uno primero.')
                )
                return
            
            proveedor_data['usuario_creacion'] = admin_user
            
            proveedor, created = ProveedorIA.objects.get_or_create(
                nombre=proveedor_data['nombre'],
                tipo=proveedor_data['tipo'],
                defaults=proveedor_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Creado: {proveedor.nombre}')
            elif force:
                for key, value in proveedor_data.items():
                    setattr(proveedor, key, value)
                proveedor.save()
                self.stdout.write(f'  ↺ Actualizado: {proveedor.nombre}')
            else:
                self.stdout.write(f'  - Ya existe: {proveedor.nombre}')
        
        self.stdout.write(f'Proveedores IA: {created_count} creados\n')

    def crear_segmentos_plantilla(self, force=False):
        """Crear segmentos de plantilla por defecto"""
        self.stdout.write('Configurando segmentos de plantilla...')
        
        segmentos_data = [
            {
                'codigo': 'ENC_MUNICIPAL',
                'nombre': 'Encabezado Municipal',
                'categoria': 'encabezado',
                'descripcion': 'Encabezado oficial con información municipal y de la sesión',
                'tipo': 'dinamico',
                'prompt_ia': '''
Genera un encabezado formal para un acta municipal con la siguiente información:
- Municipio: {municipio}
- Tipo de sesión: {tipo_reunion}
- Fecha: {fecha}
- Hora de inicio: {hora_inicio}
- Lugar: {lugar}
- Presidente/Alcalde: {presidente}

El encabezado debe seguir el formato oficial municipal ecuatoriano.
''',
                'parametros_entrada': ['municipio', 'tipo_reunion', 'fecha', 'hora_inicio', 'lugar', 'presidente'],
                'estructura_json': {
                    'longitud_minima': 100,
                    'longitud_maxima': 500,
                    'requiere_formato_fecha': True
                },
                'reutilizable': True,
                'obligatorio': True
            },
            {
                'codigo': 'LST_PARTICIPANTES',
                'nombre': 'Lista de Participantes',
                'categoria': 'asistentes',
                'descripcion': 'Listado formal de participantes con sus cargos',
                'tipo': 'dinamico',
                'prompt_ia': '''
Genera una lista formal de participantes para un acta municipal:

Participantes presentes:
{participantes_presentes}

Participantes ausentes (si aplica):
{participantes_ausentes}

Formato cada participante como: "Nombre Completo - Cargo/Función"
Mantén el orden jerárquico apropiado (Alcalde, Vicealcalde, Concejales, etc.)
''',
                'parametros_entrada': ['participantes_presentes'],
                'estructura_json': {
                    'formato_lista': True,
                    'requiere_cargos': True
                },
                'reutilizable': True,
                'obligatorio': True
            },
            {
                'codigo': 'ORD_DIA',
                'nombre': 'Orden del Día',
                'categoria': 'orden_dia',
                'descripcion': 'Agenda detallada de temas a tratar en la sesión',
                'tipo': 'dinamico',
                'prompt_ia': '''
Basándote en la transcripción y los temas identificados, genera un orden del día formal:

Temas tratados:
{temas_tratados}

Formato:
1. [Tema principal]
   - Subtemas o puntos específicos
   - Presentado por: [Responsable]

Mantén un orden lógico y formal apropiado para un acta municipal.
''',
                'parametros_entrada': ['temas_tratados'],
                'estructura_json': {
                    'formato_numerado': True,
                    'longitud_minima': 50
                },
                'reutilizable': True,
                'obligatorio': False
            },
            {
                'codigo': 'DES_SESION',
                'nombre': 'Desarrollo de la Sesión',
                'categoria': 'desarrollo',
                'descripcion': 'Resumen narrativo del desarrollo de la sesión',
                'tipo': 'dinamico',
                'prompt_ia': '''
Basándote en la siguiente transcripción, crea un resumen formal y profesional del desarrollo de la sesión:

Transcripción:
{transcripcion_completa}

Instrucciones:
- Escribe en tercera persona
- Mantén un tono formal y objetivo
- Destaca decisiones importantes y acuerdos
- Incluye intervenciones relevantes sin mencionar interrupciones menores
- Organiza cronológicamente los temas tratados
- Usa terminología apropiada para documentos municipales
''',
                'parametros_entrada': ['transcripcion_completa'],
                'estructura_json': {
                    'longitud_minima': 200,
                    'tono_formal': True,
                    'tercera_persona': True
                },
                'reutilizable': True,
                'obligatorio': True
            },
            {
                'codigo': 'ACU_RESOLUCIONES',
                'nombre': 'Acuerdos y Resoluciones',
                'categoria': 'resoluciones',
                'descripcion': 'Listado formal de acuerdos y resoluciones adoptadas',
                'tipo': 'dinamico',
                'prompt_ia': '''
Identifica y formaliza los acuerdos y resoluciones de la siguiente transcripción:

Transcripción:
{transcripcion_completa}

Formato para cada acuerdo:
ACUERDO Nº [número]: [Descripción del acuerdo]
APROBADO POR: [Resultado de votación]
RESPONSABLE: [Quien debe ejecutar]
PLAZO: [Si aplica]

Solo incluye decisiones formalmente adoptadas o consensuadas.
''',
                'parametros_entrada': ['transcripcion_completa'],
                'estructura_json': {
                    'formato_acuerdos': True,
                    'requiere_numeracion': True
                },
                'reutilizable': True,
                'obligatorio': False
            },
            {
                'codigo': 'COM_SEGUIMIENTO',
                'nombre': 'Compromisos y Seguimiento',
                'categoria': 'compromisos',
                'descripcion': 'Tareas y compromisos para seguimiento posterior',
                'tipo': 'dinamico',
                'prompt_ia': '''
Extrae de la transcripción los compromisos y tareas de seguimiento:

Transcripción:
{transcripcion_completa}

Formato:
- [Compromiso/Tarea]
  Responsable: [Persona/Área]
  Fecha límite: [Si se mencionó]
  Estado: Pendiente

Solo incluye compromisos específicos y verificables.
''',
                'parametros_entrada': ['transcripcion_completa'],
                'estructura_json': {
                    'incluye_responsables': True,
                    'formato_tareas': True
                },
                'reutilizable': True,
                'obligatorio': False
            },
            {
                'codigo': 'CIE_FIRMA',
                'nombre': 'Cierre y Firma',
                'categoria': 'cierre',
                'descripcion': 'Cierre formal del acta con firmas',
                'tipo': 'dinamico',
                'prompt_ia': '''
Genera el cierre formal del acta con:
- Hora de finalización: {hora_fin}
- Lugar: {lugar}
- Fecha: {fecha}

Incluye las líneas para firmas de:
- {presidente} (Presidente/Alcalde)
- {secretario} (Secretario/a)

Formato oficial municipal ecuatoriano.
''',
                'parametros_entrada': ['hora_fin', 'lugar', 'fecha', 'presidente', 'secretario'],
                'estructura_json': {
                    'incluye_firmas': True,
                    'formato_oficial': True
                },
                'reutilizable': True,
                'obligatorio': True
            }
        ]

        created_count = 0
        for segmento_data in segmentos_data:
            # Necesitamos el usuario para crear el segmento
            from django.contrib.auth.models import User
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR('No hay usuarios superusuarios. Crear uno primero.')
                )
                return
            
            segmento_data['usuario_creacion'] = admin_user
            
            segmento, created = SegmentoPlantilla.objects.get_or_create(
                codigo=segmento_data['codigo'],
                defaults=segmento_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Creado: {segmento.nombre}')
            elif force:
                for key, value in segmento_data.items():
                    setattr(segmento, key, value)
                segmento.save()
                self.stdout.write(f'  ↺ Actualizado: {segmento.nombre}')
            else:
                self.stdout.write(f'  - Ya existe: {segmento.nombre}')
        
        self.stdout.write(f'Segmentos de plantilla: {created_count} creados\n')

    def crear_plantillas_por_defecto(self, force=False):
        """Crear plantillas por defecto"""
        self.stdout.write('Configurando plantillas por defecto...')
        
        # Obtener proveedores y segmentos
        try:
            proveedor_principal = ProveedorIA.objects.filter(activo=True).first()
            if not proveedor_principal:
                self.stdout.write(
                    self.style.WARNING('No hay proveedores IA activos. Usando el primero disponible.')
                )
                proveedor_principal = ProveedorIA.objects.first()
        except ProveedorIA.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('No hay proveedores IA. Ejecuta primero la creación de proveedores.')
            )
            return

        plantillas_data = [
            {
                'codigo': 'ORD_MUNICIPAL',
                'nombre': 'Acta Sesión Ordinaria',
                'tipo_acta': 'ordinaria',
                'descripcion': 'Plantilla estándar para sesiones ordinarias del concejo municipal',
                'prompt_global': 'Unifica los segmentos generados en un acta formal y coherente, manteniendo el orden lógico y la terminología municipal apropiada.',
                'proveedor_ia_defecto': proveedor_principal,
                'configuracion_procesamiento': {
                    'temperature': 0.7,
                    'max_tokens': 2500,
                    'format': 'formal'
                },
                'orden_segmentos': [
                    'ENC_MUNICIPAL',
                    'LST_PARTICIPANTES', 
                    'ORD_DIA',
                    'DES_SESION',
                    'ACU_RESOLUCIONES',
                    'COM_SEGUIMIENTO',
                    'CIE_FIRMA'
                ],
                'activa': True,
                'version': '1.0'
            },
            {
                'codigo': 'EXT_MUNICIPAL',
                'nombre': 'Acta Sesión Extraordinaria',
                'tipo_acta': 'extraordinaria',
                'descripcion': 'Plantilla para sesiones extraordinarias con temas específicos',
                'prompt_global': 'Unifica los segmentos en un acta extraordinaria enfocada en el tema específico, manteniendo la formalidad requerida.',
                'proveedor_ia_defecto': proveedor_principal,
                'configuracion_procesamiento': {
                    'temperature': 0.6,  # Más conservador para temas urgentes
                    'max_tokens': 2000,
                    'format': 'formal'
                },
                'orden_segmentos': [
                    'ENC_MUNICIPAL',
                    'LST_PARTICIPANTES',
                    'DES_SESION',  # Directo al tema específico
                    'ACU_RESOLUCIONES',
                    'CIE_FIRMA'
                ],
                'activa': True,
                'version': '1.0'
            },
            {
                'codigo': 'COM_MUNICIPAL',
                'nombre': 'Acta Sesión de Comisión',
                'tipo_acta': 'comision',
                'descripcion': 'Plantilla para sesiones de comisiones específicas',
                'prompt_global': 'Genera un acta de comisión destacando las deliberaciones y recomendaciones específicas.',
                'proveedor_ia_defecto': proveedor_principal,
                'configuracion_procesamiento': {
                    'temperature': 0.7,
                    'max_tokens': 1800,
                    'format': 'formal'
                },
                'orden_segmentos': [
                    'ENC_MUNICIPAL',
                    'LST_PARTICIPANTES',
                    'ORD_DIA',
                    'DES_SESION',
                    'COM_SEGUIMIENTO',
                    'CIE_FIRMA'
                ],
                'activa': True,
                'version': '1.0'
            }
        ]

        created_count = 0
        for plantilla_data in plantillas_data:
            orden_segmentos = plantilla_data.pop('orden_segmentos')
            
            # Necesitamos el usuario para crear la plantilla
            from django.contrib.auth.models import User
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR('No hay usuarios superusuarios. Crear uno primero.')
                )
                return
            
            plantilla_data['usuario_creacion'] = admin_user
            
            plantilla, created = PlantillaActa.objects.get_or_create(
                codigo=plantilla_data['codigo'],
                defaults=plantilla_data
            )
            
            if created or force:
                if force and not created:
                    # Actualizar plantilla existente
                    for key, value in plantilla_data.items():
                        setattr(plantilla, key, value)
                    plantilla.save()
                    # Limpiar configuraciones anteriores
                    plantilla.segmentos.all().delete()
                
                # Crear configuraciones de segmentos
                for i, codigo_segmento in enumerate(orden_segmentos, 1):
                    try:
                        segmento = SegmentoPlantilla.objects.get(codigo=codigo_segmento)
                        ConfiguracionSegmento.objects.create(
                            plantilla=plantilla,
                            segmento=segmento,
                            orden=i,
                            obligatorio=True,
                            parametros_override={'prioridad': 'alta' if i <= 3 else 'media'}
                        )
                    except SegmentoPlantilla.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'Segmento con código "{codigo_segmento}" no encontrado')
                        )
                
                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Creada: {plantilla.nombre}')
                else:
                    self.stdout.write(f'  ↺ Actualizada: {plantilla.nombre}')
            else:
                self.stdout.write(f'  - Ya existe: {plantilla.nombre}')
        
        self.stdout.write(f'Plantillas: {created_count} creadas\n')