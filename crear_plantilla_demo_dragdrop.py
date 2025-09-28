#!/usr/bin/env python
"""
Script para crear plantilla de prueba con segmentos para testing del sistema drag & drop
"""
import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.generador_actas.models import PlantillaActa, SegmentoPlantilla, ConfiguracionSegmento, ProveedorIA


def crear_plantilla_demo():
    """Crea una plantilla de demostración con varios segmentos"""
    
    # Obtener usuario admin
    try:
        admin_user = User.objects.get(username='superadmin')
    except User.DoesNotExist:
        print("❌ Usuario superadmin no encontrado")
        return False
    
    print("🔄 Creando plantilla demo para testing drag & drop...")
    
    # Crear proveedor IA demo si no existe
    proveedor, created = ProveedorIA.objects.get_or_create(
        nombre="Proveedor Demo",
        defaults={
            'tipo': 'openai',
            'modelo': 'gpt-3.5-turbo',
            'activo': True,
            'usuario_creacion': admin_user
        }
    )
    if created:
        print(f"✅ Proveedor IA creado: {proveedor.nombre}")
    else:
        print(f"ℹ️  Proveedor IA ya existe: {proveedor.nombre}")
    
    # Crear segmentos base
    segmentos_data = [
        {
            'codigo': 'ENCABEZADO_ACTA',
            'nombre': 'Encabezado del Acta',
            'descripcion': 'Información básica del acta: fecha, lugar, tipo de reunión',
            'categoria': 'encabezado',
            'tipo': 'estatico',
            'contenido_estatico': '''ACTA DE SESIÓN {{tipo_sesion|upper}}
Fecha: {{fecha_sesion}}
Lugar: {{lugar_sesion}}
Hora de inicio: {{hora_inicio}}''',
            'orden_defecto': 1
        },
        {
            'codigo': 'PARTICIPANTES',
            'nombre': 'Lista de Participantes',
            'descripcion': 'Registro de asistentes y autoridades presentes',
            'categoria': 'participantes',
            'tipo': 'hibrido',
            'contenido_estatico': 'ASISTENTES:\n{{participantes_lista}}',
            'prompt_ia': 'Organiza la lista de participantes por jerarquía y rol institucional.',
            'proveedor_ia': proveedor,
            'orden_defecto': 2
        },
        {
            'codigo': 'ORDEN_DIA',
            'nombre': 'Orden del Día',
            'descripcion': 'Puntos a tratar en la sesión',
            'categoria': 'orden_dia',
            'tipo': 'estatico',
            'contenido_estatico': '''ORDEN DEL DÍA:
{{puntos_orden_dia}}''',
            'orden_defecto': 3
        },
        {
            'codigo': 'DESARROLLO_SESION',
            'nombre': 'Desarrollo de la Sesión',
            'descripcion': 'Contenido principal procesado con IA',
            'categoria': 'desarrollo',
            'tipo': 'dinamico',
            'prompt_ia': '''Analiza la transcripción y genera un resumen estructurado del desarrollo de la sesión.
Incluye:
1. Principales temas tratados
2. Intervenciones relevantes
3. Debates y discusiones importantes
4. Propuestas presentadas

Formato: párrafos claros y concisos, manteniendo el orden cronológico.''',
            'proveedor_ia': proveedor,
            'orden_defecto': 4
        },
        {
            'codigo': 'ACUERDOS_RESOLUCIONES',
            'nombre': 'Acuerdos y Resoluciones',
            'descripcion': 'Decisiones tomadas y resoluciones aprobadas',
            'categoria': 'acuerdos',
            'tipo': 'dinamico',
            'prompt_ia': '''Extrae todos los acuerdos, resoluciones y decisiones tomadas en la sesión.
Para cada acuerdo incluye:
- Número o identificación
- Descripción completa
- Resultado de la votación (si aplica)
- Responsables de ejecución

Formato: lista numerada con detalles específicos.''',
            'proveedor_ia': proveedor,
            'orden_defecto': 5
        },
        {
            'codigo': 'COMPROMISOS_TAREAS',
            'nombre': 'Compromisos y Tareas',
            'descripcion': 'Compromisos adquiridos y tareas asignadas',
            'categoria': 'compromisos',
            'tipo': 'dinamico',
            'prompt_ia': '''Identifica todos los compromisos adquiridos y tareas asignadas.
Para cada compromiso especifica:
- Responsable(s)
- Descripción de la tarea
- Plazo de cumplimiento
- Seguimiento requerido

Formato: tabla organizada por responsable.''',
            'proveedor_ia': proveedor,
            'orden_defecto': 6
        },
        {
            'codigo': 'CIERRE_ACTA',
            'nombre': 'Cierre del Acta',
            'descripcion': 'Información de cierre y firmas',
            'categoria': 'cierre',
            'tipo': 'estatico',
            'contenido_estatico': '''CIERRE:
La sesión se levanta a las {{hora_fin}}.

Para constancia firman:

_______________________
{{presidente_nombre}}
{{presidente_cargo}}

_______________________  
{{secretario_nombre}}
{{secretario_cargo}}''',
            'orden_defecto': 7
        }
    ]
    
    # Crear segmentos
    segmentos_creados = []
    for segmento_data in segmentos_data:
        segmento, created = SegmentoPlantilla.objects.get_or_create(
            codigo=segmento_data['codigo'],
            defaults={
                **segmento_data,
                'usuario_creacion': admin_user
            }
        )
        segmentos_creados.append(segmento)
        if created:
            print(f"✅ Segmento creado: {segmento.nombre}")
        else:
            print(f"ℹ️  Segmento ya existe: {segmento.nombre}")
    
    # Crear plantilla
    plantilla, created = PlantillaActa.objects.get_or_create(
        codigo="PLANTILLA_DEMO_DRAGDROP",
        defaults={
            'nombre': 'Plantilla Demo - Drag & Drop',
            'descripcion': 'Plantilla de demostración para probar el sistema de drag & drop de segmentos',
            'tipo_acta': 'ordinaria',
            'prompt_global': 'Unifica todos los segmentos en un acta coherente y bien estructurada.',
            'proveedor_ia_defecto': proveedor,
            'usuario_creacion': admin_user
        }
    )
    
    if created:
        print(f"✅ Plantilla creada: {plantilla.nombre}")
        
        # Crear configuraciones de segmentos
        for i, segmento in enumerate(segmentos_creados, 1):
            config, created = ConfiguracionSegmento.objects.get_or_create(
                plantilla=plantilla,
                segmento=segmento,
                defaults={
                    'orden': i,
                    'obligatorio': segmento.codigo in ['ENCABEZADO_ACTA', 'CIERRE_ACTA']
                }
            )
            if created:
                print(f"  ✅ Configuración creada: {segmento.nombre} (orden: {i})")
    else:
        print(f"ℹ️  Plantilla ya existe: {plantilla.nombre}")
    
    print(f"\n🎉 Plantilla demo creada exitosamente!")
    print(f"📋 ID de plantilla: {plantilla.pk}")
    print(f"🔧 URL para configurar: http://localhost:8000/generador-actas/plantillas/nuevo/{plantilla.pk}/configurar/")
    print(f"👀 URL vista previa: http://localhost:8000/generador-actas/plantillas/nuevo/{plantilla.pk}/preview/")
    
    return True


if __name__ == "__main__":
    crear_plantilla_demo()