#!/usr/bin/env python3
"""
Completar los segmentos faltantes - Crear las 12 categorías restantes
Cada categoría tendrá 1 estático (JSON) + 1 dinámico (Prompt→JSON)
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

def crear_segmentos_faltantes():
    """Crear los 12 segmentos faltantes para completar las 17 categorías"""
    
    # Obtener referencias
    admin_user = User.objects.filter(is_superuser=True).first()
    proveedor_ia = ProveedorIA.objects.filter(activo=True).first()
    
    print("🚀 Completando segmentos faltantes (12 categorías restantes)...")
    
    # Categorías ya creadas: encabezado, participantes, agenda, decisiones, cierre
    # Faltantes: titulo, fecha_hora, orden_dia, introduccion, desarrollo, transcripcion, 
    #           resumen, acuerdos, compromisos, seguimiento, firmas, anexos, legal, otros
    
    # TÍTULO
    titulo_estatico = {
        "tipo": "titulo_acta",
        "titulo": "ACTA DE SESIÓN",
        "atributos": {
            "negrita": True,
            "centrado": True,
            "tamano_fuente": "20px",
            "mayusculas": True
        },
        "numero_acta": "[NUMERO_ACTA]",
        "tipo_sesion": "[TIPO_SESION]",
        "formato_numero": {
            "prefijo": "ACTA N°",
            "formato": "000-GAD-MP-2025",
            "negrita": True
        },
        "subtitulo": {
            "texto": "Gobierno Autónomo Descentralizado Municipal de Pastaza",
            "formato": {"italica": True, "tamano_fuente": "14px"}
        }
    }
    
    # FECHA Y HORA  
    fecha_hora_estatico = {
        "tipo": "fecha_hora_sesion",
        "titulo": "DATOS TEMPORALES DE LA SESIÓN",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "12px"
        },
        "estructura": {
            "fecha_sesion": {
                "campo": "[FECHA_SESION]",
                "formato": "DD de MMMM de YYYY",
                "ejemplo": "27 de septiembre de 2025"
            },
            "hora_inicio": {
                "campo": "[HORA_INICIO]", 
                "formato": "HH:MM",
                "ejemplo": "09:00"
            },
            "hora_fin": {
                "campo": "[HORA_FIN]",
                "formato": "HH:MM", 
                "ejemplo": "11:30"
            },
            "duracion": {
                "calculada": True,
                "formato": "X horas Y minutos"
            }
        },
        "zona_horaria": "GMT-5 (Ecuador Continental)"
    }
    
    # ORDEN DEL DÍA
    orden_dia_estatico = {
        "tipo": "orden_del_dia",
        "titulo": "ORDEN DEL DÍA DETALLADO",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "14px"
        },
        "estructura_protocolar": [
            {
                "orden": 1,
                "punto": "Verificación del Quórum",
                "obligatorio": True,
                "responsable": "Secretario General"
            },
            {
                "orden": 2,
                "punto": "Lectura y Aprobación del Orden del Día",
                "obligatorio": True,
                "responsable": "Alcalde"
            },
            {
                "orden": 3,
                "punto": "Lectura y Aprobación del Acta Anterior",
                "obligatorio": True,
                "documento": "[ACTA_ANTERIOR]"
            }
        ],
        "puntos_especificos": [
            {
                "orden": "[ORDEN]",
                "titulo": "[TITULO_PUNTO]",
                "ponente": "[PONENTE]",
                "documentos_soporte": ["[DOC1]", "[DOC2]"],
                "tiempo_estimado": "[TIEMPO]"
            }
        ]
    }
    
    # INTRODUCCIÓN
    introduccion_estatico = {
        "tipo": "introduccion_sesion",
        "titulo": "INTRODUCCIÓN Y ANTECEDENTES",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "contexto_sesion": {
            "convocatoria": {
                "fecha_convocatoria": "[FECHA_CONVOCATORIA]",
                "medio": "Oficio circular",
                "base_legal": "Art. 58 COOTAD"
            },
            "objetivo_principal": "[OBJETIVO_SESION]",
            "antecedentes": [
                "[ANTECEDENTE_1]",
                "[ANTECEDENTE_2]"
            ]
        },
        "marco_normativo": {
            "constitucion": "Art. 238 Constitución del Ecuador",
            "cootad": "Título V del COOTAD",
            "reglamento_interno": "Reglamento Interno GAD Municipal Pastaza"
        }
    }
    
    # DESARROLLO
    desarrollo_estatico = {
        "tipo": "desarrollo_sesion",
        "titulo": "DESARROLLO DE LA SESIÓN",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "estructura_desarrollo": [
            {
                "fase": "Instalación",
                "descripcion": "Verificación de quórum e instalación formal",
                "responsable": "Alcalde",
                "tiempo": "[TIEMPO_INSTALACION]"
            },
            {
                "fase": "Tratamiento de Puntos",
                "puntos_tratados": [
                    {
                        "punto": "[NUMERO_PUNTO]",
                        "tema": "[TEMA_TRATADO]",
                        "ponente": "[PONENTE]",
                        "duracion": "[DURACION]",
                        "intervenciones": ["[INTERVENCION_1]"]
                    }
                ]
            },
            {
                "fase": "Deliberación",
                "descripcion": "Análisis y debate de propuestas",
                "participantes": ["[PARTICIPANTE_1]"]
            }
        ]
    }
    
    # TRANSCRIPCIÓN
    transcripcion_estatico = {
        "tipo": "transcripcion_textual",
        "titulo": "TRANSCRIPCIÓN TEXTUAL DE INTERVENCIONES",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "12px"
        },
        "formato_transcripcion": {
            "estructura_intervencion": {
                "speaker": "[NOMBRE_PARTICIPANTE]",
                "cargo": "[CARGO_PARTICIPANTE]",
                "timestamp": "[HH:MM:SS]",
                "contenido": "[TEXTO_TRANSCRIPCION]"
            },
            "notaciones": {
                "pausa": "[PAUSA]",
                "inaudible": "[INAUDIBLE]",
                "aplausos": "[APLAUSOS]",
                "interrupcion": "[INTERRUPCIÓN]"
            }
        },
        "calidad_audio": {
            "nivel": "[CALIDAD]",
            "observaciones": "[OBSERVACIONES_AUDIO]"
        }
    }
    
    # RESUMEN EJECUTIVO
    resumen_estatico = {
        "tipo": "resumen_ejecutivo",
        "titulo": "RESUMEN EJECUTIVO DE LA SESIÓN",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "puntos_clave": [
            {
                "categoria": "Decisiones Importantes",
                "items": ["[DECISION_1]", "[DECISION_2]"]
            },
            {
                "categoria": "Proyectos Aprobados", 
                "items": ["[PROYECTO_1]", "[PROYECTO_2]"]
            },
            {
                "categoria": "Asignaciones Presupuestarias",
                "items": ["[ASIGNACION_1]", "[ASIGNACION_2]"]
            }
        ],
        "impacto_ciudadano": {
            "beneficiarios": "[NUMERO_BENEFICIARIOS]",
            "sectores": ["[SECTOR_1]", "[SECTOR_2]"],
            "inversion_total": "[MONTO_INVERSION]"
        }
    }
    
    # Continúo con el resto...
    segmentos_faltantes = [
        # TÍTULO
        ('TITULO_ESTATICO', 'Título de Acta Municipal Estático', 'titulo', 'estatico',
         json.dumps(titulo_estatico, ensure_ascii=False, indent=2),
         ''),
        
        ('TITULO_DINAMICO', 'Título de Acta Municipal Dinámico', 'titulo', 'dinamico', '{}',
         '''Extrae información para generar el título oficial del acta municipal.

INFORMACIÓN A EXTRAER:
- Tipo de sesión (ordinaria/extraordinaria/emergencia)
- Número correlativo del acta
- Fecha de la sesión
- Denominación oficial del GAD

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "numero_acta": "001-GAD-MP-2025",
  "tipo_sesion": "ORDINARIA", 
  "fecha_sesion": "27 de septiembre de 2025",
  "denominacion": "GOBIERNO AUTÓNOMO DESCENTRALIZADO MUNICIPAL DE PASTAZA"
}'''),

        # FECHA Y HORA
        ('FECHA_HORA_ESTATICO', 'Fecha y Hora Municipal Estático', 'fecha_hora', 'estatico',
         json.dumps(fecha_hora_estatico, ensure_ascii=False, indent=2),
         ''),
         
        ('FECHA_HORA_DINAMICO', 'Fecha y Hora Municipal Dinámico', 'fecha_hora', 'dinamico', '{}',
         '''Extrae información temporal completa de la sesión municipal.

INFORMACIÓN A EXTRAER:
- Fecha exacta de la sesión
- Hora de inicio de la sesión
- Hora de finalización
- Duración total calculada
- Zona horaria

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "fecha_sesion": "27 de septiembre de 2025",
  "hora_inicio": "09:00",
  "hora_fin": "11:30", 
  "duracion": "2 horas 30 minutos",
  "zona_horaria": "GMT-5"
}'''),

        # ORDEN DEL DÍA
        ('ORDEN_DIA_ESTATICO', 'Orden del Día Municipal Estático', 'orden_dia', 'estatico',
         json.dumps(orden_dia_estatico, ensure_ascii=False, indent=2),
         ''),
         
        ('ORDEN_DIA_DINAMICO', 'Orden del Día Municipal Dinámico', 'orden_dia', 'dinamico', '{}',
         '''Extrae el orden del día completo de la transcripción municipal.

INFORMACIÓN A EXTRAER:
- Puntos protocolares obligatorios
- Puntos específicos tratados en orden
- Responsables de cada punto
- Documentos de soporte mencionados
- Tiempos estimados o reales

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "puntos_protocolares": [
    {"orden": 1, "punto": "Verificación del Quórum", "responsable": "Secretario"}
  ],
  "puntos_especificos": [
    {"orden": 4, "titulo": "Título extraído", "ponente": "Nombre ponente", "documentos": ["Doc1"]}
  ]
}'''),

        # INTRODUCCIÓN
        ('INTRODUCCION_ESTATICO', 'Introducción Municipal Estática', 'introduccion', 'estatico',
         json.dumps(introduccion_estatico, ensure_ascii=False, indent=2),
         ''),
         
        ('INTRODUCCION_DINAMICO', 'Introducción Municipal Dinámica', 'introduccion', 'dinamico', '{}',
         '''Extrae información introductoria y antecedentes de la sesión municipal.

INFORMACIÓN A EXTRAER:
- Objetivo principal de la sesión
- Antecedentes relevantes mencionados
- Convocatoria y base legal
- Contexto normativo aplicable

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "objetivo_principal": "Objetivo extraído de la transcripción",
  "antecedentes": ["Antecedente 1", "Antecedente 2"],
  "base_legal": "Normativa mencionada",
  "convocatoria": "Medio y fecha de convocatoria"
}'''),

        # DESARROLLO
        ('DESARROLLO_ESTATICO', 'Desarrollo de Sesión Municipal Estático', 'desarrollo', 'estatico',
         json.dumps(desarrollo_estatico, ensure_ascii=False, indent=2),
         ''),
         
        ('DESARROLLO_DINAMICO', 'Desarrollo de Sesión Municipal Dinámico', 'desarrollo', 'dinamico', '{}',
         '''Extrae el desarrollo cronológico completo de la sesión municipal.

INFORMACIÓN A EXTRAER:
- Fases de la sesión (instalación, tratamiento, deliberación)
- Puntos tratados con duración
- Intervenciones principales
- Participantes en cada fase

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "fases": [
    {"nombre": "Instalación", "duracion": "15 minutos", "descripcion": "Descripción extraída"}
  ],
  "puntos_tratados": [
    {"punto": 4, "tema": "Tema extraído", "duracion": "30 minutos", "ponente": "Nombre"}
  ]
}'''),

        # TRANSCRIPCIÓN
        ('TRANSCRIPCION_ESTATICO', 'Transcripción Municipal Estática', 'transcripcion', 'estatico',
         json.dumps(transcripcion_estatico, ensure_ascii=False, indent=2),
         ''),
         
        ('TRANSCRIPCION_DINAMICO', 'Transcripción Municipal Dinámica', 'transcripcion', 'dinamico', '{}',
         '''Estructura la transcripción textual completa con identificación de participantes.

INFORMACIÓN A EXTRAER:
- Intervenciones por participante con timestamps
- Identificación de roles/cargos
- Notaciones especiales (pausas, interrupciones)
- Calidad del audio y observaciones

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "intervenciones": [
    {"speaker": "Nombre completo", "cargo": "Cargo", "timestamp": "09:15:30", "texto": "Contenido transcrito"}
  ],
  "calidad_audio": "Alta/Media/Baja",
  "observaciones": "Observaciones técnicas"
}'''),

        # RESUMEN EJECUTIVO
        ('RESUMEN_ESTATICO', 'Resumen Ejecutivo Municipal Estático', 'resumen', 'estatico',
         json.dumps(resumen_estatico, ensure_ascii=False, indent=2),
         ''),
         
        ('RESUMEN_DINAMICO', 'Resumen Ejecutivo Municipal Dinámico', 'resumen', 'dinamico', '{}',
         '''Genera un resumen ejecutivo con los puntos más relevantes de la sesión.

INFORMACIÓN A EXTRAER:
- Decisiones más importantes adoptadas
- Proyectos aprobados o rechazados
- Asignaciones presupuestarias
- Impacto ciudadano estimado
- Beneficiarios identificados

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "decisiones_importantes": ["Decisión 1", "Decisión 2"],
  "proyectos_aprobados": ["Proyecto 1", "Proyecto 2"], 
  "inversion_total": "USD $XXX,XXX.XX",
  "beneficiarios_estimados": "X familias/ciudadanos",
  "sectores_impactados": ["Sector 1", "Sector 2"]
}''')
    ]
    
    # Crear los primeros 8 segmentos
    contador = 0
    for codigo, nombre, categoria, tipo, contenido, prompt in segmentos_faltantes:
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
                orden_defecto=contador + 10,
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
            contador += 1
        except Exception as e:
            print(f"❌ Error creando {codigo}: {e}")
    
    print(f"\n🎉 PARTE 1 COMPLETADA: {contador} segmentos creados")
    return contador

if __name__ == "__main__":
    total_creados = crear_segmentos_faltantes()
    print(f"\n📊 Segmentos creados en esta ejecución: {total_creados}")
    
    # Mostrar estado actual
    total_actual = SegmentoPlantilla.objects.count()
    print(f"📈 Total segmentos en sistema: {total_actual}")
    print(f"🎯 Objetivo: 34 segmentos (17 estáticos + 17 dinámicos)")
    print(f"📋 Faltan: {34 - total_actual} segmentos")