#!/usr/bin/env python3
"""
Script mejorado para crear TODOS los segmentos (estáticos y dinámicos)
Con validación JSON y manejo de errores robusto
"""

import os
import sys
import django
import requests
import json
import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

from django.contrib.auth import get_user_model
from apps.generador_actas.models import SegmentoPlantilla

User = get_user_model()

def limpiar_segmentos():
    """Eliminar todos los segmentos existentes"""
    count = SegmentoPlantilla.objects.count()
    SegmentoPlantilla.objects.all().delete()
    print(f"🗑️ Eliminados {count} segmentos existentes")

def obtener_csrf_token():
    """Obtener token CSRF"""
    session = requests.Session()
    response = session.get('http://localhost:8000/admin/login/')
    csrf_token = session.cookies.get('csrftoken')
    return csrf_token, session

def login_admin(csrf_token, session):
    """Login como superadmin"""
    login_data = {
        'username': 'superadmin',
        'password': 'AdminPuyo2025!',
        'csrfmiddlewaretoken': csrf_token,
        'next': '/admin/'
    }
    
    response = session.post(
        'http://localhost:8000/admin/login/',
        data=login_data,
        allow_redirects=False
    )
    
    return session

def crear_segmento_http(nombre, codigo, tipo, categoria, contenido, prompt_ia, session, csrf_token):
    """Crear segmento vía HTTP con validación"""
    
    # Preparar datos con validación JSON
    data = {
        'nombre': nombre,
        'codigo': codigo,
        'tipo': tipo,
        'categoria': categoria,
        'contenido': contenido,
        'prompt_ia': prompt_ia,
        'activo': True,
        'csrfmiddlewaretoken': csrf_token
    }
    
    # Validar contenido JSON si es dinámico
    if tipo == 'dinamico' and contenido:
        try:
            json.loads(contenido)
        except json.JSONDecodeError as e:
            print(f"❌ Error JSON en {codigo}: {e}")
            return False
    
    # Crear segmento
    response = session.post(
        'http://localhost:8000/generador-actas/segmentos/crear/',
        data=data,
        allow_redirects=False
    )
    
    if response.status_code == 302:
        print(f"✅ Creado: {codigo} ({tipo})")
        return True
    else:
        print(f"❌ Error creando {codigo}: Status {response.status_code}")
        if response.status_code == 200:
            print("   Posible error de validación en el formulario")
        return False

def crear_todos_los_segmentos():
    """Crear todos los segmentos estáticos y dinámicos"""
    
    print("🔑 Obteniendo credenciales...")
    csrf_token, session = obtener_csrf_token()
    session = login_admin(csrf_token, session)
    
    # Definir todos los segmentos
    segmentos = [
        # ===== SEGMENTOS ESTÁTICOS =====
        {
            'nombre': 'Encabezado de Acta Municipal',
            'codigo': 'ENCABEZADO_ESTATICO',
            'tipo': 'estatico',
            'categoria': 'encabezado',
            'contenido': '''
<div class="encabezado-acta">
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
</div>
            '''.strip(),
            'prompt_ia': ''
        },
        {
            'nombre': 'Lista de Participantes Municipal',
            'codigo': 'PARTICIPANTES_ESTATICO', 
            'tipo': 'estatico',
            'categoria': 'participantes',
            'contenido': '''
<div class="participantes-sesion">
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
</div>
            '''.strip(),
            'prompt_ia': ''
        },
        {
            'nombre': 'Agenda de Sesión Municipal',
            'codigo': 'AGENDA_ESTATICA',
            'tipo': 'estatico', 
            'categoria': 'agenda',
            'contenido': '''
<div class="agenda-sesion">
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
</div>
            '''.strip(),
            'prompt_ia': ''
        },
        {
            'nombre': 'Decisiones y Acuerdos Municipales',
            'codigo': 'DECISIONES_ESTATICAS',
            'tipo': 'estatico',
            'categoria': 'decisiones',
            'contenido': '''
<div class="decisiones-acuerdos">
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
</div>
            '''.strip(),
            'prompt_ia': ''
        },
        {
            'nombre': 'Cierre y Firmas del Acta',
            'codigo': 'CIERRE_ESTATICO',
            'tipo': 'estatico',
            'categoria': 'cierre', 
            'contenido': '''
<div class="cierre-acta">
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
</style>
            '''.strip(),
            'prompt_ia': ''
        },
        
        # ===== SEGMENTOS DINÁMICOS =====
        {
            'nombre': 'Encabezado Dinámico con IA',
            'codigo': 'ENCABEZADO_DINAMICO',
            'tipo': 'dinamico',
            'categoria': 'encabezado',
            'contenido': '{}',
            'prompt_ia': 'Genera un encabezado personalizado para acta municipal considerando: tipo de sesión ({{tipo_sesion}}), fecha ({{fecha}}), tema principal ({{tema_principal}}). Incluye logo municipal, datos oficiales del GAD Pastaza y formato protocolar ecuatoriano. Retorna HTML válido con clases Bootstrap.'
        },
        {
            'nombre': 'Participantes Dinámico con IA',
            'codigo': 'PARTICIPANTES_DINAMICO',
            'tipo': 'dinamico', 
            'categoria': 'participantes',
            'contenido': '{}',
            'prompt_ia': 'Genera lista de participantes municipal inteligente basada en: asistentes detectados ({{participantes_audio}}), roles identificados ({{cargos_detectados}}), tipo de sesión ({{tipo_sesion}}). Calcula quórum automáticamente, identifica autoridades principales y clasifica invitados. Incluye validación de presencia y formato oficial.'
        },
        {
            'nombre': 'Agenda Dinámica con IA', 
            'codigo': 'AGENDA_DINAMICA',
            'tipo': 'dinamico',
            'categoria': 'agenda',
            'contenido': '{}',
            'prompt_ia': 'Extrae y estructura agenda municipal de transcripción de audio considerando: puntos tratados ({{temas_detectados}}), orden de discusión ({{cronologia}}), normativa municipal (COOTAD). Identifica puntos principales, subpuntos, mociones y propuestas. Formato ordenado con numeración oficial y tiempos estimados.'
        },
        {
            'nombre': 'Decisiones Dinámicas con IA',
            'codigo': 'DECISIONES_DINAMICAS', 
            'tipo': 'dinamico',
            'categoria': 'decisiones',
            'contenido': '{}',
            'prompt_ia': 'Identifica y estructura decisiones municipales de audio: acuerdos adoptados ({{decisiones_detectadas}}), votaciones realizadas ({{resultados_votacion}}), resoluciones aprobadas. Extrae número de resolución, asunto tratado, proponente, argumentos y resultado de votación. Clasifica por tipo: ordenanzas, resoluciones, acuerdos ministeriales.'
        },
        {
            'nombre': 'Cierre Dinámico con IA',
            'codigo': 'CIERRE_DINAMICO', 
            'tipo': 'dinamico',
            'categoria': 'cierre',
            'contenido': '{}',
            'prompt_ia': 'Genera cierre de acta municipal personalizado con: hora de clausura ({{hora_fin}}), resumen de acuerdos principales ({{acuerdos_principales}}), próximas sesiones programadas ({{proximas_fechas}}). Incluye firmas digitales, validaciones legales y referencias normativas según COOTAD. Formato oficial con sello temporal.'
        }
    ]
    
    print(f"🚀 Creando {len(segmentos)} segmentos...")
    
    exitosos = 0
    fallidos = 0
    
    for segmento in segmentos:
        try:
            success = crear_segmento_http(
                segmento['nombre'],
                segmento['codigo'], 
                segmento['tipo'],
                segmento['categoria'],
                segmento['contenido'],
                segmento['prompt_ia'],
                session,
                csrf_token
            )
            
            if success:
                exitosos += 1
            else:
                fallidos += 1
            
            time.sleep(0.5)  # Pausa entre creaciones
            
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