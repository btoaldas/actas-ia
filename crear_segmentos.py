#!/usr/bin/env python
"""
CREAR SEGMENTOS PREDEFINIDOS PARA TODAS LAS CATEGORÍAS
Tanto estáticos como dinámicos, listos para usar
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

def main():
    print("🏗️ CREANDO SEGMENTOS PREDEFINIDOS PARA TODAS LAS CATEGORÍAS...")
    
    client = Client()
    User = get_user_model()
    
    # Login como superadmin
    login_success = client.login(username='superadmin', password='AdminPuyo2025!')
    print(f"✅ Login: {login_success}")
    
    # SEGMENTOS ESTÁTICOS
    print("\n📝 1. CREANDO SEGMENTOS ESTÁTICOS...")
    
    segmentos_estaticos = [
        {
            'codigo': 'ENCABEZADO_ESTATICO',
            'nombre': 'Encabezado de Acta Municipal',
            'categoria': 'encabezado',
            'descripcion': 'Sección de introducción del acta con datos generales de la sesión municipal',
            'contenido_estatico': '''<div class="encabezado-acta">
    <div class="logo-municipio text-center">
        <img src="/static/images/logo-pastaza.png" alt="GAD Municipal Pastaza" style="height: 80px;">
        <h2><strong>GOBIERNO AUTÓNOMO DESCENTRALIZADO MUNICIPAL DE PASTAZA</strong></h2>
        <h3>SESIÓN {{tipo_sesion|upper}}</h3>
    </div>
    
    <div class="datos-sesion">
        <table class="table table-borderless">
            <tr>
                <td><strong>FECHA:</strong></td>
                <td>{{fecha_sesion}}</td>
                <td><strong>HORA INICIO:</strong></td>
                <td>{{hora_inicio}}</td>
            </tr>
            <tr>
                <td><strong>LUGAR:</strong></td>
                <td colspan="3">{{ubicacion}}</td>
            </tr>
            <tr>
                <td><strong>PRESIDIDA POR:</strong></td>
                <td colspan="3">{{presidente_nombre}} - {{presidente_cargo}}</td>
            </tr>
            <tr>
                <td><strong>SECRETARÍA:</strong></td>
                <td colspan="3">{{secretario_nombre}}</td>
            </tr>
        </table>
    </div>
</div>''',
            'formato_salida': 'html',
            'orden_defecto': '1'
        },
        {
            'codigo': 'PARTICIPANTES_ESTATICO',
            'nombre': 'Lista de Participantes Municipal',
            'categoria': 'participantes',
            'descripcion': 'Lista completa de autoridades y funcionarios municipales presentes en la sesión',
            'contenido_estatico': '''<div class="participantes-acta">
    <h3>PARTICIPANTES DE LA SESIÓN</h3>
    
    <div class="autoridades-municipales">
        <h4>AUTORIDADES MUNICIPALES PRESENTES:</h4>
        <ul class="list-unstyled">
            <li><i class="fas fa-user-tie text-primary"></i> <strong>{{alcalde_nombre}}</strong> - Alcalde</li>
            <li><i class="fas fa-user text-info"></i> <strong>{{vicealcalde_nombre}}</strong> - Vicealcalde</li>
            <li><i class="fas fa-users text-success"></i> <strong>Concejales Presentes:</strong>
                <ul>
                    <li>{{concejal_1}} - Concejal Principal</li>
                    <li>{{concejal_2}} - Concejal Principal</li>
                    <li>{{concejal_3}} - Concejal Principal</li>
                    <li>{{concejal_4}} - Concejal Suplente</li>
                </ul>
            </li>
        </ul>
    </div>

    <div class="funcionarios-municipales">
        <h4>FUNCIONARIOS MUNICIPALES:</h4>
        <ul class="list-unstyled">
            <li><i class="fas fa-file-alt text-warning"></i> <strong>{{secretario_general}}</strong> - Secretario General</li>
            <li><i class="fas fa-gavel text-danger"></i> <strong>{{procurador_sindico}}</strong> - Procurador Síndico</li>
            <li><i class="fas fa-calculator text-info"></i> <strong>{{director_financiero}}</strong> - Director Financiero</li>
            <li><i class="fas fa-hard-hat text-success"></i> <strong>{{director_obras}}</strong> - Director de Obras Públicas</li>
        </ul>
    </div>
    
    <div class="invitados-especiales" style="margin-top: 15px;">
        <h4>INVITADOS ESPECIALES:</h4>
        <ul class="list-unstyled">
            <li><i class="fas fa-user-friends text-secondary"></i> {{invitado_1}}</li>
            <li><i class="fas fa-user-friends text-secondary"></i> {{invitado_2}}</li>
        </ul>
    </div>
</div>''',
            'formato_salida': 'html',
            'orden_defecto': '2'
        },
        {
            'codigo': 'AGENDA_ESTATICA',
            'nombre': 'Orden del Día Municipal',
            'categoria': 'agenda',
            'descripcion': 'Orden del día con los puntos a tratar en la sesión del concejo municipal',
            'contenido_estatico': '''<div class="agenda-acta">
    <h3>ORDEN DEL DÍA</h3>
    
    <div class="puntos-agenda">
        <ol class="agenda-numerada">
            <li class="punto-agenda">
                <strong>Verificación del Quórum</strong>
                <div class="detalle-punto">
                    <small class="text-muted">Constatación de asistencia de autoridades municipales</small>
                </div>
            </li>
            
            <li class="punto-agenda">
                <strong>Aprobación del Orden del Día</strong>
                <div class="detalle-punto">
                    <small class="text-muted">{{observaciones_agenda}}</small>
                </div>
            </li>
            
            <li class="punto-agenda">
                <strong>Aprobación del Acta Anterior</strong>
                <div class="detalle-punto">
                    <small class="text-muted">Acta de sesión {{fecha_sesion_anterior}}</small>
                </div>
            </li>
            
            <li class="punto-agenda">
                <strong>{{punto_4_titulo}}</strong>
                <div class="detalle-punto">
                    <small class="text-muted">{{punto_4_detalle}}</small>
                </div>
            </li>
            
            <li class="punto-agenda">
                <strong>{{punto_5_titulo}}</strong>
                <div class="detalle-punto">
                    <small class="text-muted">{{punto_5_detalle}}</small>
                </div>
            </li>
            
            <li class="punto-agenda">
                <strong>{{punto_6_titulo}}</strong>
                <div class="detalle-punto">
                    <small class="text-muted">{{punto_6_detalle}}</small>
                </div>
            </li>
            
            <li class="punto-agenda">
                <strong>Varios e Imprevistos</strong>
                <div class="detalle-punto">
                    <small class="text-muted">Puntos adicionales propuestos durante la sesión</small>
                </div>
            </li>
        </ol>
    </div>
</div>''',
            'formato_salida': 'html',
            'orden_defecto': '3'
        },
        {
            'codigo': 'DECISIONES_ESTATICAS',
            'nombre': 'Resoluciones y Acuerdos Municipales',
            'categoria': 'decisiones',
            'descripcion': 'Sección para documentar las resoluciones, acuerdos y decisiones tomadas por el concejo',
            'contenido_estatico': '''<div class="decisiones-acta">
    <h3>RESOLUCIONES Y ACUERDOS ADOPTADOS</h3>
    
    <div class="decision-item">
        <div class="card border-primary mb-3">
            <div class="card-header bg-primary text-white">
                <h5><i class="fas fa-gavel"></i> {{tipo_decision_1}} No. {{numero_decision_1}}</h5>
            </div>
            <div class="card-body">
                <p><strong class="text-primary">VISTO:</strong> {{antecedente_1}}</p>
                <p><strong class="text-info">CONSIDERANDO:</strong> {{consideracion_1}}</p>
                <p><strong class="text-success">RESUELVE:</strong> {{resolucion_1}}</p>
                
                <div class="votacion">
                    <h6 class="text-warning">RESULTADO DE VOTACIÓN:</h6>
                    <div class="row">
                        <div class="col-md-4">
                            <span class="badge badge-success">Votos a Favor: {{votos_favor_1}}</span>
                        </div>
                        <div class="col-md-4">
                            <span class="badge badge-danger">Votos en Contra: {{votos_contra_1}}</span>
                        </div>
                        <div class="col-md-4">
                            <span class="badge badge-warning">Abstenciones: {{abstenciones_1}}</span>
                        </div>
                    </div>
                    <p class="mt-2"><strong>Estado:</strong> <span class="badge badge-{{estado_1}}">{{resultado_1}}</span></p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="decision-item">
        <div class="card border-info mb-3">
            <div class="card-header bg-info text-white">
                <h5><i class="fas fa-balance-scale"></i> {{tipo_decision_2}} No. {{numero_decision_2}}</h5>
            </div>
            <div class="card-body">
                <p><strong class="text-primary">RESUELVE:</strong> {{resolucion_2}}</p>
                <p><strong>Estado:</strong> <span class="badge badge-{{estado_2}}">{{resultado_2}}</span></p>
            </div>
        </div>
    </div>
</div>''',
            'formato_salida': 'html',
            'orden_defecto': '4'
        },
        {
            'codigo': 'CIERRE_ESTATICO',
            'nombre': 'Cierre y Firmas del Acta',
            'categoria': 'cierre',
            'descripcion': 'Sección final del acta con información de cierre, próxima sesión y firmas oficiales',
            'contenido_estatico': '''<div class="cierre-acta">
    <div class="informacion-cierre">
        <h3>CIERRE DE LA SESIÓN</h3>
        
        <div class="datos-cierre">
            <table class="table table-borderless">
                <tr>
                    <td><strong>HORA DE FINALIZACIÓN:</strong></td>
                    <td>{{hora_cierre}}</td>
                </tr>
                <tr>
                    <td><strong>DURACIÓN TOTAL:</strong></td>
                    <td>{{duracion_sesion}}</td>
                </tr>
                <tr>
                    <td><strong>PRÓXIMA SESIÓN ORDINARIA:</strong></td>
                    <td>{{fecha_proxima_sesion}}</td>
                </tr>
            </table>
        </div>
        
        <div class="observaciones-finales">
            <h4>OBSERVACIONES FINALES:</h4>
            <p>{{observaciones_cierre}}</p>
        </div>
    </div>
    
    <div class="firmas-oficiales" style="margin-top: 40px;">
        <div class="row">
            <div class="col-md-6 text-center">
                <div style="margin-bottom: 60px; border-bottom: 1px solid #333; width: 80%; margin-left: auto; margin-right: auto;"></div>
                <p><strong>{{presidente_nombre}}</strong><br>
                {{presidente_cargo}}<br>
                GAD Municipal de Pastaza</p>
            </div>
            
            <div class="col-md-6 text-center">
                <div style="margin-bottom: 60px; border-bottom: 1px solid #333; width: 80%; margin-left: auto; margin-right: auto;"></div>
                <p><strong>{{secretario_nombre}}</strong><br>
                Secretario General<br>
                GAD Municipal de Pastaza</p>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-12 text-center">
                <small class="text-muted">
                    <i class="fas fa-calendar"></i> Acta elaborada el {{fecha_elaboracion}}<br>
                    <i class="fas fa-map-marker-alt"></i> Puyo - Pastaza - Ecuador
                </small>
            </div>
        </div>
    </div>
</div>''',
            'formato_salida': 'html',
            'orden_defecto': '5'
        }
    ]
    
    segmentos_creados = []
    
    for i, segmento in enumerate(segmentos_estaticos, 1):
        print(f"   📝 {i}/5: Creando {segmento['nombre']}...")
        
        data = {
            'codigo': segmento['codigo'],
            'nombre': segmento['nombre'],
            'tipo': 'estatico',
            'categoria': segmento['categoria'],
            'descripcion': segmento['descripcion'],
            'contenido_estatico': segmento['contenido_estatico'],
            'formato_salida': segmento['formato_salida'],
            'orden_defecto': segmento['orden_defecto'],
            'tiempo_limite_ia': '60',
            'reintentos_ia': '2',
            'activo': 'on',
            'reutilizable': 'on'
        }
        
        response = client.post('/generador-actas/segmentos/crear/', data)
        
        if response.status_code == 302:
            segmento_id = response.url.split('/')[-2]
            print(f"      ✅ Creado exitosamente (ID: {segmento_id})")
            segmentos_creados.append(f"{segmento['nombre']} (ID: {segmento_id})")
        else:
            print(f"      ❌ Error creando segmento: {response.status_code}")
    
    print(f"\n✅ SEGMENTOS ESTÁTICOS CREADOS: {len(segmentos_creados)}/5")
    
    return segmentos_creados

if __name__ == '__main__':
    main()