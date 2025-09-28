#!/usr/bin/env python3
"""
Script para crear segmentos municipales ecuatorianos correctamente estructurados
- Estáticos: JSON estructurado con atributos de formato
- Dinámicos: Prompts especializados que responden JSON puro
"""

import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

from apps.generador_actas.models import SegmentoPlantilla, ProveedorIA
from django.contrib.auth import get_user_model

User = get_user_model()

def crear_segmentos_municipales():
    """Crear segmentos con estructura municipal ecuatoriana real"""
    
    # Obtener referencias
    admin_user = User.objects.filter(is_superuser=True).first()
    proveedor_ia = ProveedorIA.objects.filter(activo=True).first()
    
    print("🏛️ Creando segmentos municipales ecuatorianos...")
    
    # ===== SEGMENTOS ESTÁTICOS (JSON Estructurado) =====
    
    # 1. ENCABEZADO ESTÁTICO
    encabezado_estatico = {
        "tipo": "cabecera",
        "titulo": "GOBIERNO AUTÓNOMO DESCENTRALIZADO MUNICIPAL DEL CANTÓN PASTAZA",
        "atributos": {
            "negrita": True,
            "centrado": True,
            "tamano_fuente": "18px"
        },
        "subtitulo": "ACTA DE SESIÓN ORDINARIA/EXTRAORDINARIA",
        "subtitulo_atributos": {
            "negrita": True,
            "centrado": True,
            "tamano_fuente": "16px",
            "mayusculas": True
        },
        "datos_sesion": {
            "numero_acta": "001-2025",
            "fecha": "27 de septiembre de 2025",
            "hora_inicio": "09:00",
            "lugar": "Sala de Sesiones del GAD Municipal de Pastaza",
            "canton": "Pastaza",
            "provincia": "Pastaza"
        },
        "autoridades": {
            "presidente_sesion": "Alcalde del GAD Municipal de Pastaza",
            "secretario": "Secretario General del GAD Municipal"
        },
        "base_legal": "Art. 58 del Código Orgánico de Organización Territorial, Autonomía y Descentralización (COOTAD)"
    }
    
    # 2. PARTICIPANTES ESTÁTICO
    participantes_estatico = {
        "tipo": "lista_participantes",
        "titulo": "PARTICIPANTES DE LA SESIÓN",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "14px"
        },
        "estructura": {
            "autoridades_principales": [
                {
                    "cargo": "Alcalde",
                    "nombre": "[NOMBRE_ALCALDE]",
                    "presente": True,
                    "formato": {"negrita": True}
                },
                {
                    "cargo": "Secretario General", 
                    "nombre": "[NOMBRE_SECRETARIO]",
                    "presente": True,
                    "formato": {"negrita": True}
                }
            ],
            "concejales": [
                {
                    "cargo": "Concejal Principal",
                    "nombre": "[NOMBRE_CONCEJAL_1]",
                    "presente": True
                },
                {
                    "cargo": "Concejal Principal", 
                    "nombre": "[NOMBRE_CONCEJAL_2]",
                    "presente": True
                },
                {
                    "cargo": "Concejal Suplente",
                    "nombre": "[NOMBRE_CONCEJAL_3]",
                    "presente": False,
                    "justificacion": "Licencia médica"
                }
            ],
            "invitados": [
                {
                    "cargo": "Director de Obras Públicas",
                    "nombre": "[NOMBRE_DIRECTOR]", 
                    "presente": True,
                    "motivo": "Presentación proyecto vial"
                }
            ]
        },
        "quorum": {
            "minimo_requerido": 3,
            "presentes": 4,
            "porcentaje": "80%",
            "status": "CONSTITUIDO",
            "formato_status": {"negrita": True, "color": "verde"}
        }
    }
    
    # 3. AGENDA ESTÁTICA
    agenda_estatica = {
        "tipo": "orden_dia",
        "titulo": "ORDEN DEL DÍA",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "14px"
        },
        "estructura": [
            {
                "punto": 1,
                "titulo": "Constatación del Quórum",
                "tipo": "protocolar",
                "obligatorio": True,
                "formato": {"italica": False}
            },
            {
                "punto": 2, 
                "titulo": "Aprobación del Orden del Día",
                "tipo": "protocolar",
                "obligatorio": True
            },
            {
                "punto": 3,
                "titulo": "Lectura y Aprobación del Acta Anterior",
                "tipo": "protocolar", 
                "obligatorio": True,
                "referencia": "Acta N° 000-2025"
            },
            {
                "punto": 4,
                "titulo": "Aprobación de Ordenanza Municipal sobre Gestión de Residuos Sólidos",
                "tipo": "normativo",
                "ponente": "Comisión de Ambiente",
                "documentos_soporte": ["Proyecto de Ordenanza", "Estudio Técnico"],
                "urgencia": "alta"
            },
            {
                "punto": 5,
                "titulo": "Autorización para Contratación de Obra: Mejoramiento Vial Sector La Merced",
                "tipo": "administrativo",
                "monto": "USD $125,000.00",
                "modalidad": "Lista Corta",
                "plazo": "90 días"
            },
            {
                "punto": 6,
                "titulo": "Varios",
                "tipo": "protocolar",
                "obligatorio": True
            },
            {
                "punto": 7,
                "titulo": "Clausura",
                "tipo": "protocolar", 
                "obligatorio": True
            }
        ]
    }
    
    # 4. DECISIONES ESTÁTICAS
    decisiones_estaticas = {
        "tipo": "resoluciones_acuerdos",
        "titulo": "DECISIONES Y ACUERDOS ADOPTADOS",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "14px"
        },
        "estructura": [
            {
                "tipo_decision": "RESOLUCIÓN",
                "numero": "001-GAD-MP-2025",
                "asunto": "Aprobación Ordenanza Municipal de Gestión de Residuos Sólidos",
                "ponente": "Comisión de Ambiente y Salubridad",
                "considerandos": [
                    "Que es competencia del GAD Municipal la gestión de residuos sólidos",
                    "Que se requiere actualizar la normativa vigente",
                    "Que se cumplió el proceso de socialización ciudadana"
                ],
                "resuelve": "Aprobar en segundo y definitivo debate la Ordenanza Municipal",
                "votacion": {
                    "a_favor": 4,
                    "en_contra": 0, 
                    "abstenciones": 0,
                    "ausentes": 1,
                    "resultado": "APROBADA",
                    "formato_resultado": {"negrita": True, "color": "verde"}
                },
                "vigencia": "Inmediata tras publicación"
            },
            {
                "tipo_decision": "ACUERDO",
                "numero": "002-GAD-MP-2025", 
                "asunto": "Autorización Contratación Mejoramiento Vial La Merced",
                "monto": "USD $125,000.00",
                "modalidad": "Lista Corta",
                "plazo_ejecucion": "90 días calendario",
                "partida_presupuestaria": "730801-Obras de Infraestructura",
                "votacion": {
                    "a_favor": 3,
                    "en_contra": 1,
                    "abstenciones": 0, 
                    "resultado": "APROBADA",
                    "observacion": "Concejal X vota en contra por consideraciones técnicas"
                }
            }
        ]
    }
    
    # 5. CIERRE ESTÁTICO
    cierre_estatico = {
        "tipo": "clausura_acta",
        "titulo": "CLAUSURA DE LA SESIÓN",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "14px"
        },
        "contenido": {
            "texto_clausura": "No habiendo más asuntos que tratar, el señor Alcalde clausura la sesión",
            "hora_clausura": "11:30",
            "fecha": "27 de septiembre de 2025"
        },
        "firmas": {
            "alcalde": {
                "nombre": "[NOMBRE_ALCALDE]",
                "cargo": "ALCALDE DEL GAD MUNICIPAL DE PASTAZA",
                "formato": {"negrita": True, "centrado": True}
            },
            "secretario": {
                "nombre": "[NOMBRE_SECRETARIO]", 
                "cargo": "SECRETARIO GENERAL",
                "formato": {"negrita": True, "centrado": True}
            }
        },
        "validacion": {
            "texto": "Acta elaborada conforme al Art. 58 del COOTAD y Reglamento Interno del GAD Municipal de Pastaza",
            "formato": {"italica": True, "tamano_fuente": "10px"}
        },
        "sello_institucional": {
            "requerido": True,
            "posicion": "centro_inferior"
        }
    }
    
    segmentos_a_crear = [
        # ESTÁTICOS
        ('ENCABEZADO_ESTATICO', 'Encabezado Municipal Estático', 'encabezado', 'estatico', 
         json.dumps(encabezado_estatico, ensure_ascii=False, indent=2), ''),
         
        ('PARTICIPANTES_ESTATICO', 'Lista Participantes Municipal Estática', 'participantes', 'estatico',
         json.dumps(participantes_estatico, ensure_ascii=False, indent=2), ''),
         
        ('AGENDA_ESTATICA', 'Agenda Municipal Estática', 'agenda', 'estatico',
         json.dumps(agenda_estatica, ensure_ascii=False, indent=2), ''),
         
        ('DECISIONES_ESTATICAS', 'Decisiones Municipales Estáticas', 'decisiones', 'estatico', 
         json.dumps(decisiones_estaticas, ensure_ascii=False, indent=2), ''),
         
        ('CIERRE_ESTATICO', 'Cierre Municipal Estático', 'cierre', 'estatico',
         json.dumps(cierre_estatico, ensure_ascii=False, indent=2), ''),
        
        # DINÁMICOS
        ('ENCABEZADO_DINAMICO', 'Encabezado Municipal Dinámico', 'encabezado', 'dinamico', '{}',
         '''Extrae la información de encabezado de la transcripción de sesión municipal recibida en formato JSON.

INFORMACIÓN A EXTRAER:
- Tipo de sesión (ordinaria/extraordinaria/emergencia)
- Número de acta secuencial
- Fecha completa de la sesión
- Hora exacta de inicio
- Lugar específico donde se realiza
- Nombre completo del Alcalde que preside
- Nombre completo del Secretario

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "tipo_sesion": "ORDINARIA",
  "numero_acta": "001-2025",
  "fecha": "27 de septiembre de 2025",
  "hora_inicio": "09:00",
  "lugar": "Sala de Sesiones del GAD Municipal de Pastaza",
  "alcalde": "Nombre Completo del Alcalde",
  "secretario": "Nombre Completo del Secretario",
  "canton": "Pastaza",
  "provincia": "Pastaza"
}'''),

        ('PARTICIPANTES_DINAMICO', 'Participantes Municipal Dinámico', 'participantes', 'dinamico', '{}',
         '''Extrae la información de participantes de la transcripción de sesión municipal recibida identificando roles y asistencia.

INFORMACIÓN A EXTRAER:
- Alcalde presente con nombre completo
- Secretario presente con nombre completo  
- Lista completa de concejales con nombres y asistencia
- Invitados especiales con cargos y nombres
- Cálculo automático del quórum legal
- Justificaciones de ausencias si las menciona

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "alcalde": {"nombre": "Nombre Completo", "presente": true},
  "secretario": {"nombre": "Nombre Completo", "presente": true},
  "concejales": [
    {"nombre": "Nombre Concejal 1", "cargo": "Concejal Principal", "presente": true},
    {"nombre": "Nombre Concejal 2", "cargo": "Concejal Suplente", "presente": false, "justificacion": "Motivo"}
  ],
  "invitados": [
    {"nombre": "Nombre Invitado", "cargo": "Cargo Específico", "motivo": "Razón de participación"}
  ],
  "quorum": {
    "requerido": 3,
    "presentes": 4, 
    "porcentaje": "80%",
    "constituido": true
  }
}'''),

        ('AGENDA_DINAMICA', 'Agenda Municipal Dinámica', 'agenda', 'dinamico', '{}',
         '''Extrae y estructura el orden del día de la transcripción de sesión municipal identificando todos los puntos tratados.

INFORMACIÓN A EXTRAER:
- Puntos protocolares obligatorios (quórum, orden del día, acta anterior)
- Proyectos de ordenanza con detalles específicos
- Autorizaciones de contratación con montos y modalidades
- Asuntos administrativos y técnicos
- Ponentes o responsables de cada punto
- Documentos de soporte mencionados

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "puntos": [
    {
      "numero": 1,
      "titulo": "Constatación del Quórum",
      "tipo": "protocolar",
      "obligatorio": true
    },
    {
      "numero": 4,
      "titulo": "Título específico extraído del audio",
      "tipo": "normativo",
      "ponente": "Nombre del ponente",
      "monto": "USD $125,000.00",
      "documentos": ["Documento 1", "Documento 2"]
    }
  ]
}'''),

        ('DECISIONES_DINAMICAS', 'Decisiones Municipales Dinámicas', 'decisiones', 'dinamico', '{}', 
         '''Extrae las decisiones, acuerdos y resoluciones adoptadas en la sesión municipal con resultados de votación.

INFORMACIÓN A EXTRAER:
- Tipo de decisión (resolución/acuerdo/ordenanza)
- Número oficial asignado
- Asunto específico tratado
- Resultados exactos de votación (a favor/contra/abstenciones)
- Montos económicos si aplica
- Modalidades de contratación
- Plazos establecidos
- Observaciones o justificaciones de votos

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "decisiones": [
    {
      "tipo": "RESOLUCIÓN",
      "numero": "001-GAD-MP-2025",
      "asunto": "Asunto específico extraído",
      "votacion": {
        "a_favor": 4,
        "en_contra": 0,
        "abstenciones": 1,
        "resultado": "APROBADA"
      },
      "monto": "USD $125,000.00",
      "plazo": "90 días",
      "observaciones": "Observación específica si existe"
    }
  ]
}'''),

        ('CIERRE_DINAMICO', 'Cierre Municipal Dinámico', 'cierre', 'dinamico', '{}',
         '''Extrae la información de cierre de la sesión municipal desde la transcripción recibida en formato JSON.

INFORMACIÓN A EXTRAER:
- Hora exacta de finalización de la sesión
- Fecha de próxima sesión si se menciona
- Nombres completos de las personas que firman el acta
- Cargos oficiales de los firmantes
- Menciones de convocatorias futuras

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "hora_cierre": "11:30",
  "fecha": "27 de septiembre de 2025",
  "proxima_sesion": "15 de octubre de 2025",
  "firmantes": [
    {"nombre": "Nombre Completo del Alcalde", "cargo": "ALCALDE DEL GAD MUNICIPAL DE PASTAZA"},
    {"nombre": "Nombre Completo del Secretario", "cargo": "SECRETARIO GENERAL"}
  ],
  "observaciones": "Observación adicional si existe"
}''')
    ]
    
    total_creados = 0
    
    for codigo, nombre, categoria, tipo, contenido, prompt in segmentos_a_crear:
        try:
            segmento = SegmentoPlantilla.objects.create(
                codigo=codigo,
                nombre=nombre,
                descripcion=f"Segmento {tipo} municipal ecuatoriano para {categoria}",
                categoria=categoria,
                tipo=tipo,
                contenido_estatico=contenido,
                formato_salida='json',
                prompt_ia=prompt,
                prompt_sistema='Eres un especialista en actas municipales ecuatorianas que sigue estrictamente el COOTAD y reglamentos internos de GADs.',
                proveedor_ia=proveedor_ia,
                estructura_json={},
                validaciones_salida={},
                formato_validacion='json',
                parametros_entrada={},
                variables_personalizadas={},
                contexto_requerido={},
                orden_defecto=total_creados + 1,
                reutilizable=True,
                obligatorio=False,
                activo=True,
                longitud_maxima=15000,
                tiempo_limite_ia=120,
                reintentos_ia=3,
                total_usos=0,
                total_errores=0,
                tiempo_promedio_procesamiento=0.0,
                tasa_exito=0.0,
                usuario_creacion=admin_user
            )
            print(f"✅ Creado: {codigo} ({tipo})")
            total_creados += 1
        except Exception as e:
            print(f"❌ Error creando {codigo}: {e}")
    
    print(f"\n🎉 PROCESO COMPLETADO: {total_creados} segmentos creados")
    
    # Mostrar resumen
    print(f"\n📋 SEGMENTOS MUNICIPALES ECUATORIANOS:")
    for seg in SegmentoPlantilla.objects.all().order_by('categoria', 'tipo'):
        formato = "JSON" if seg.tipo == 'estatico' else "Prompt→JSON"
        print(f"   {seg.codigo}: {formato}")

if __name__ == "__main__":
    crear_segmentos_municipales()