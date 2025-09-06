"""
Script para poblar la base de datos con datos de demostración para el portal ciudadano
"""

from django.contrib.auth.models import User
from apps.pages.models import TipoSesion, EstadoActa, ActaMunicipal
from datetime import datetime, timedelta
from django.utils import timezone
import random

def crear_tipos_sesion():
    """Crear tipos de sesión"""
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
            print(f"✓ Creado tipo de sesión: {tipo.get_nombre_display()}")

def crear_estados_acta():
    """Crear estados de actas"""
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
            print(f"✓ Creado estado: {estado.get_nombre_display()}")

def crear_actas_demo():
    """Crear actas de demostración"""
    
    # Obtener datos necesarios
    tipos = list(TipoSesion.objects.all())
    estados = list(EstadoActa.objects.all())
    
    # Crear usuario secretario si no existe
    secretario, created = User.objects.get_or_create(
        username='secretario_municipal',
        defaults={
            'first_name': 'María',
            'last_name': 'Gonzalez',
            'email': 'secretario@municipio.gob.ec',
            'is_staff': True
        }
    )
    
    if created:
        secretario.set_password('demo123')
        secretario.save()
        print(f"✓ Creado usuario secretario: {secretario.get_full_name()}")
    
    # Datos de ejemplo para actas
    actas_data = [
        {
            'titulo': 'Aprobación del Presupuesto Municipal 2025',
            'resumen': 'Sesión ordinaria para la aprobación del presupuesto participativo del municipio para el año fiscal 2025, incluyendo inversiones en infraestructura, servicios básicos y programas sociales.',
            'presidente': 'Dr. Carlos Mendoza - Alcalde',
            'tipo': 'ordinaria',
            'acceso': 'publico',
            'orden_del_dia': '1. Verificación del quórum\n2. Lectura del orden del día\n3. Presentación del presupuesto 2025\n4. Debate y discusión\n5. Votación\n6. Varios',
            'acuerdos': 'ACUERDO 001-2025: Aprobar el presupuesto municipal por $2.5 millones para el ejercicio fiscal 2025.\nACUERDO 002-2025: Autorizar al alcalde para gestionar créditos hasta $500,000.',
            'asistentes': 'Dr. Carlos Mendoza (Alcalde), Ing. Ana Rodríguez (Concejal), Lic. Pedro Ramírez (Concejal), Dra. Luisa Vega (Concejal), Eco. Mario Silva (Concejal)',
            'transcripcion_ia': True,
            'precision_ia': 97.5
        },
        {
            'titulo': 'Declaratoria de Emergencia por Deslizamientos',
            'resumen': 'Sesión extraordinaria convocada por la emergencia causada por los deslizamientos en el sector La Esperanza, para tomar medidas urgentes de atención a las familias afectadas.',
            'presidente': 'Dr. Carlos Mendoza - Alcalde',
            'tipo': 'extraordinaria',
            'acceso': 'publico',
            'orden_del_dia': '1. Informe de la situación de emergencia\n2. Evaluación de daños\n3. Plan de contingencia\n4. Declaratoria de emergencia\n5. Asignación de recursos',
            'acuerdos': 'ACUERDO 003-2025: Declarar estado de emergencia en el sector La Esperanza.\nACUERDO 004-2025: Asignar $50,000 para atención inmediata de familias damnificadas.',
            'ausentes': 'Lic. Pedro Ramírez (Concejal) - Justificado por viaje de trabajo',
            'transcripcion_ia': True,
            'precision_ia': 95.2
        },
        {
            'titulo': 'Audiencia Pública - Reforma al Plan de Ordenamiento Territorial',
            'resumen': 'Audiencia pública para socializar las propuestas de reforma al Plan de Ordenamiento Territorial (POT) 2025-2035 y recibir observaciones de la ciudadanía.',
            'presidente': 'Ing. Ana Rodríguez - Presidenta del Concejo',
            'tipo': 'publica',
            'acceso': 'publico',
            'orden_del_dia': '1. Presentación de las reformas al POT\n2. Intervenciones ciudadanas\n3. Observaciones y sugerencias\n4. Compromisos municipales',
            'asistentes': 'Funcionarios municipales, 45 ciudadanos, representantes de organizaciones sociales',
            'transcripcion_ia': False,
        },
        {
            'titulo': 'Sesión Solemne - 150 Años de Fundación del Cantón',
            'resumen': 'Sesión solemne conmemorativa de los 150 años de fundación del cantón, con reconocimientos a personalidades destacadas y presentación de proyectos emblemáticos.',
            'presidente': 'Dr. Carlos Mendoza - Alcalde',
            'tipo': 'solemne',
            'acceso': 'publico',
            'orden_del_dia': '1. Acto protocolario\n2. Historia del cantón\n3. Reconocimientos\n4. Presentación de proyectos del sesquicentenario',
            'acuerdos': 'ACUERDO 005-2025: Declarar el 2025 como "Año del Sesquicentenario".\nACUERDO 006-2025: Crear la comisión organizadora de festividades.',
            'transcripcion_ia': True,
            'precision_ia': 98.1
        },
        {
            'titulo': 'Comisión de Obras Públicas - Proyecto Vial Urbano',
            'resumen': 'Reunión de la comisión de obras públicas para evaluar las propuestas técnicas del proyecto de mejoramiento vial del casco urbano.',
            'presidente': 'Ing. Ana Rodríguez - Presidenta de Comisión',
            'tipo': 'comision',
            'acceso': 'restringido',
            'orden_del_dia': '1. Revisión de propuestas técnicas\n2. Evaluación económica\n3. Cronograma de ejecución\n4. Recomendaciones al pleno',
            'observaciones': 'Sesión técnica con participación de ingenieros consultores',
            'transcripcion_ia': True,
            'precision_ia': 94.8
        },
        {
            'titulo': 'Aprobación de Ordenanza de Gestión de Residuos Sólidos',
            'resumen': 'Sesión para el segundo debate y aprobación definitiva de la ordenanza municipal para la gestión integral de residuos sólidos y reciclaje.',
            'presidente': 'Dr. Carlos Mendoza - Alcalde',
            'tipo': 'ordinaria',
            'acceso': 'publico',
            'acuerdos': 'ORDENANZA 001-2025: Aprobar la ordenanza de gestión de residuos sólidos.\nACUERDO 007-2025: Implementar programa de reciclaje municipal.',
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
                'orden_del_dia': acta_data.get('orden_del_dia', ''),
                'acuerdos': acta_data.get('acuerdos', ''),
                'acceso': acta_data.get('acceso', 'publico'),
                'secretario': secretario,
                'presidente': acta_data['presidente'],
                'asistentes': acta_data.get('asistentes', ''),
                'ausentes': acta_data.get('ausentes', ''),
                'transcripcion_ia': acta_data.get('transcripcion_ia', False),
                'precision_ia': acta_data.get('precision_ia', None),
                'palabras_clave': f"municipal, {acta_data['tipo']}, 2025, {tipo_sesion.get_nombre_display().lower()}",
                'observaciones': acta_data.get('observaciones', ''),
                'prioridad': 'alta' if acta_data['tipo'] == 'extraordinaria' else 'normal',
                'activo': True
            }
        )
        
        if created:
            print(f"✓ Creada acta: {acta.numero_acta} - {acta.titulo[:50]}...")

def run():
    """Función principal para ejecutar el script"""
    print("🚀 Iniciando población de datos del Portal Ciudadano...\n")
    
    print("📋 Creando tipos de sesión...")
    crear_tipos_sesion()
    
    print("\n📊 Creando estados de actas...")
    crear_estados_acta()
    
    print("\n📄 Creando actas de demostración...")
    crear_actas_demo()
    
    print(f"\n✅ ¡Proceso completado exitosamente!")
    print(f"📊 Estadísticas:")
    print(f"   - Tipos de sesión: {TipoSesion.objects.count()}")
    print(f"   - Estados de acta: {EstadoActa.objects.count()}")
    print(f"   - Actas municipales: {ActaMunicipal.objects.count()}")
    print(f"\n🌐 Accede al Portal Ciudadano en: http://localhost:8000/portal-ciudadano/")

if __name__ == '__main__':
    run()
