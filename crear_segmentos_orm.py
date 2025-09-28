#!/usr/bin/env python3
"""
Script para crear segmentos directamente usando Django ORM (más confiable)
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

from apps.generador_actas.models import SegmentoPlantilla, ProveedorIA
from django.contrib.auth import get_user_model

User = get_user_model()

def limpiar_segmentos():
    """Eliminar todos los segmentos existentes"""
    count = SegmentoPlantilla.objects.count()
    SegmentoPlantilla.objects.all().delete()
    print(f"🗑️ Eliminados {count} segmentos existentes")

def crear_todos_los_segmentos():
    """Crear todos los segmentos usando Django ORM"""
    
    # Obtener usuario administrador y proveedor IA por defecto
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        proveedor_ia = ProveedorIA.objects.filter(activo=True).first()
    except:
        admin_user = None
        proveedor_ia = None
    
    # Definir todos los segmentos con los campos correctos
    segmentos = [
        # ===== SEGMENTOS ESTÁTICOS =====
        {
            'nombre': 'Encabezado de Acta Municipal',
            'codigo': 'ENCABEZADO_ESTATICO',
            'tipo': 'estatico',
            'categoria': 'encabezado',
            'descripcion': 'Encabezado oficial para actas municipales de Pastaza con logo y datos protocolar',
            'contenido_estatico': '''<div class="encabezado-acta">
    <div class="logo-municipio text-center mb-3">
        <img src="/static/img/logo-pastaza.png" alt="Municipio de Pastaza" class="img-fluid" style="max-height: 80px;">
    </div>
    <h2 class="text-center mb-4">GOBIERNO AUTÓNOMO DESCENTRALIZADO MUNICIPAL DE PASTAZA</h2>
    <h3 class="text-center mb-3">ACTA DE SESIÓN {{tipo_sesion|upper}}</h3>
    
    <div class="info-basica">
        <p><strong>Fecha:</strong> {{fecha}}</p>
        <p><strong>Hora de Inicio:</strong> {{hora_inicio}}</p>
        <p><strong>Lugar:</strong> {{lugar}}</p>
        <p><strong>Presidida por:</strong> {{alcalde}}</p>
        <p><strong>Secretario:</strong> {{secretario}}</p>
    </div>
</div>''',
            'formato_salida': 'html',
            'prompt_ia': '',
            'prompt_sistema': '',
            'activo': True,
            'reutilizable': True,
            'obligatorio': False,
            'orden_defecto': 1,
            'longitud_maxima': 5000,
            'tiempo_limite_ia': 30,
            'reintentos_ia': 3
        },
        {
            'nombre': 'Lista de Participantes Municipal',
            'codigo': 'PARTICIPANTES_ESTATICO', 
            'tipo': 'estatico',
            'categoria': 'participantes',
            'contenido': '''<div class="participantes-sesion">
    <h4>PARTICIPANTES DE LA SESIÓN</h4>
    
    <div class="autoridades mb-3">
        <h5>Autoridades Principales:</h5>
        <ul class="list-unstyled">
            <li><strong>Alcalde:</strong> {{alcalde}}</li>
            <li><strong>Secretario General:</strong> {{secretario}}</li>
        </ul>
    </div>
    
    <div class="concejales mb-3">
        <h5>Concejales Presentes:</h5>
        <ul>
            {% for concejal in concejales %}
            <li>{{concejal.nombre}} - {{concejal.cargo}}</li>
            {% endfor %}
        </ul>
    </div>
    
    <div class="invitados">
        <h5>Invitados y Funcionarios:</h5>
        <ul>
            {% for invitado in invitados %}
            <li>{{invitado.nombre}} - {{invitado.cargo}}</li>
            {% endfor %}
        </ul>
    </div>
    
    <p class="quorum"><strong>Quórum:</strong> {{quorum}} ({{porcentaje_quorum}}%)</p>
</div>''',
            'prompt_ia': '',
            'activo': True
        },
        {
            'nombre': 'Agenda de Sesión Municipal',
            'codigo': 'AGENDA_ESTATICA',
            'tipo': 'estatico', 
            'categoria': 'agenda',
            'contenido': '''<div class="agenda-sesion">
    <h4>ORDEN DEL DÍA</h4>
    
    <ol class="agenda-lista">
        <li><strong>Constatación del Quórum</strong></li>
        <li><strong>Aprobación del Orden del Día</strong></li>
        <li><strong>Lectura y Aprobación del Acta Anterior</strong></li>
        
        {% for punto in puntos_agenda %}
        <li>
            <strong>{{punto.titulo}}</strong>
            {% if punto.descripcion %}
            <p class="descripcion-punto">{{punto.descripcion}}</p>
            {% endif %}
        </li>
        {% endfor %}
        
        <li><strong>Varios</strong></li>
        <li><strong>Clausura de la Sesión</strong></li>
    </ol>
</div>''',
            'prompt_ia': '',
            'activo': True
        },
        {
            'nombre': 'Decisiones y Acuerdos Municipales',
            'codigo': 'DECISIONES_ESTATICAS',
            'tipo': 'estatico',
            'categoria': 'decisiones',
            'contenido': '''<div class="decisiones-acuerdos">
    <h4>DECISIONES Y ACUERDOS ADOPTADOS</h4>
    
    {% for decision in decisiones %}
    <div class="decision-item mb-4">
        <h5>{{decision.tipo|upper}} No. {{decision.numero}}</h5>
        <p><strong>Asunto:</strong> {{decision.asunto}}</p>
        <p><strong>Propuesto por:</strong> {{decision.proponente}}</p>
        
        <div class="contenido-decision">
            {{decision.contenido|safe}}
        </div>
        
        <div class="votacion mt-3">
            <p><strong>Votación:</strong></p>
            <ul class="list-inline">
                <li class="list-inline-item"><span class="badge badge-success">A favor: {{decision.votos_favor}}</span></li>
                <li class="list-inline-item"><span class="badge badge-danger">En contra: {{decision.votos_contra}}</span></li>
                <li class="list-inline-item"><span class="badge badge-warning">Abstenciones: {{decision.abstenciones}}</span></li>
            </ul>
            <p><strong>Resultado:</strong> <span class="badge badge-{{decision.estado|lower}}">{{decision.estado|upper}}</span></p>
        </div>
    </div>
    {% endfor %}
</div>''',
            'prompt_ia': '',
            'activo': True
        },
        {
            'nombre': 'Cierre y Firmas del Acta',
            'codigo': 'CIERRE_ESTATICO',
            'tipo': 'estatico',
            'categoria': 'cierre', 
            'contenido': '''<div class="cierre-acta">
    <h4>CLAUSURA DE LA SESIÓN</h4>
    
    <p>No habiendo más asuntos que tratar, el señor Alcalde clausura la sesión siendo las <strong>{{hora_clausura}}</strong> del día {{fecha}}.</p>
    
    <div class="firmas mt-5">
        <div class="row">
            <div class="col-md-6 text-center">
                <div class="firma-alcalde">
                    <div class="linea-firma mb-2"></div>
                    <p><strong>{{alcalde}}</strong><br>
                    ALCALDE DEL GAD MUNICIPAL DE PASTAZA</p>
                </div>
            </div>
            <div class="col-md-6 text-center">
                <div class="firma-secretario">
                    <div class="linea-firma mb-2"></div>
                    <p><strong>{{secretario}}</strong><br>
                    SECRETARIO GENERAL</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="validacion-acta mt-4">
        <p class="text-muted small">
            Acta elaborada y validada conforme a las disposiciones del Código Orgánico de Organización Territorial, 
            Autonomía y Descentralización (COOTAD) y el Reglamento Interno del GAD Municipal de Pastaza.
        </p>
    </div>
</div>

<style>
.linea-firma {
    border-bottom: 1px solid #000;
    width: 200px;
    margin: 0 auto;
    height: 50px;
}
</style>''',
            'prompt_ia': '',
            'activo': True
        },
        
        # ===== SEGMENTOS DINÁMICOS =====
        {
            'nombre': 'Encabezado Dinámico con IA',
            'codigo': 'ENCABEZADO_DINAMICO',
            'tipo': 'dinamico',
            'categoria': 'encabezado',
            'contenido': '{}',
            'prompt_ia': 'Genera un encabezado personalizado para acta municipal considerando: tipo de sesión ({{tipo_sesion}}), fecha ({{fecha}}), tema principal ({{tema_principal}}). Incluye logo municipal, datos oficiales del GAD Pastaza y formato protocolar ecuatoriano. Retorna HTML válido con clases Bootstrap.',
            'activo': True
        },
        {
            'nombre': 'Participantes Dinámico con IA',
            'codigo': 'PARTICIPANTES_DINAMICO',
            'tipo': 'dinamico', 
            'categoria': 'participantes',
            'contenido': '{}',
            'prompt_ia': 'Genera lista de participantes municipal inteligente basada en: asistentes detectados ({{participantes_audio}}), roles identificados ({{cargos_detectados}}), tipo de sesión ({{tipo_sesion}}). Calcula quórum automáticamente, identifica autoridades principales y clasifica invitados. Incluye validación de presencia y formato oficial.',
            'activo': True
        },
        {
            'nombre': 'Agenda Dinámica con IA', 
            'codigo': 'AGENDA_DINAMICA',
            'tipo': 'dinamico',
            'categoria': 'agenda',
            'contenido': '{}',
            'prompt_ia': 'Extrae y estructura agenda municipal de transcripción de audio considerando: puntos tratados ({{temas_detectados}}), orden de discusión ({{cronologia}}), normativa municipal (COOTAD). Identifica puntos principales, subpuntos, mociones y propuestas. Formato ordenado con numeración oficial y tiempos estimados.',
            'activo': True
        },
        {
            'nombre': 'Decisiones Dinámicas con IA',
            'codigo': 'DECISIONES_DINAMICAS', 
            'tipo': 'dinamico',
            'categoria': 'decisiones',
            'contenido': '{}',
            'prompt_ia': 'Identifica y estructura decisiones municipales de audio: acuerdos adoptados ({{decisiones_detectadas}}), votaciones realizadas ({{resultados_votacion}}), resoluciones aprobadas. Extrae número de resolución, asunto tratado, proponente, argumentos y resultado de votación. Clasifica por tipo: ordenanzas, resoluciones, acuerdos ministeriales.',
            'activo': True
        },
        {
            'nombre': 'Cierre Dinámico con IA',
            'codigo': 'CIERRE_DINAMICO', 
            'tipo': 'dinamico',
            'categoria': 'cierre',
            'contenido': '{}',
            'prompt_ia': 'Genera cierre de acta municipal personalizado con: hora de clausura ({{hora_fin}}), resumen de acuerdos principales ({{acuerdos_principales}}), próximas sesiones programadas ({{proximas_fechas}}). Incluye firmas digitales, validaciones legales y referencias normativas según COOTAD. Formato oficial con sello temporal.',
            'activo': True
        }
    ]
    
    print(f"🚀 Creando {len(segmentos)} segmentos...")
    
    exitosos = 0
    fallidos = 0
    
    for segmento in segmentos:
        try:
            # Crear usando ORM directamente
            obj, created = SegmentoPlantilla.objects.get_or_create(
                codigo=segmento['codigo'],
                defaults={
                    'nombre': segmento['nombre'],
                    'tipo': segmento['tipo'],
                    'categoria': segmento['categoria'],
                    'contenido': segmento['contenido'],
                    'prompt_ia': segmento['prompt_ia'],
                    'activo': segmento['activo']
                }
            )
            
            if created:
                print(f"✅ Creado: {segmento['codigo']} ({segmento['tipo']})")
                exitosos += 1
            else:
                print(f"⚠️ Ya existía: {segmento['codigo']}")
                exitosos += 1
            
        except Exception as e:
            print(f"❌ Error creando {segmento['codigo']}: {e}")
            fallidos += 1
    
    print(f"\n📊 RESUMEN FINAL:")
    print(f"   ✅ Exitosos: {exitosos}")
    print(f"   ❌ Fallidos: {fallidos}")
    print(f"   📝 Total: {len(segmentos)}")
    
    return exitosos, fallidos

if __name__ == "__main__":
    print("🧹 Iniciando limpieza y recreación completa de segmentos...")
    
    # Limpiar segmentos existentes
    limpiar_segmentos()
    
    # Crear todos los segmentos
    exitosos, fallidos = crear_todos_los_segmentos()
    
    print(f"\n🎉 PROCESO COMPLETADO")
    print(f"✅ {exitosos} segmentos creados exitosamente")
    print(f"❌ {fallidos} segmentos fallidos")
    
    # Mostrar listado final
    print(f"\n📋 LISTADO FINAL DE SEGMENTOS:")
    segmentos = SegmentoPlantilla.objects.all().order_by('categoria', 'tipo')
    for seg in segmentos:
        print(f"   ID {seg.pk}: {seg.nombre} ({seg.tipo} - {seg.categoria})")