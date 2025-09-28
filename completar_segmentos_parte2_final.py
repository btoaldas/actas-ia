#!/usr/bin/env python3
"""
Completar los últimos 10 segmentos faltantes - Parte 2 FINAL
Categorías restantes: acuerdos, compromisos, seguimiento, firmas, anexos, legal, otros
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

def completar_segmentos_finales():
    """Crear los últimos 10 segmentos para completar las 17 categorías"""
    
    # Obtener referencias
    admin_user = User.objects.filter(is_superuser=True).first()
    proveedor_ia = ProveedorIA.objects.filter(activo=True).first()
    
    print("🎯 Creando los últimos 10 segmentos faltantes...")
    
    # ACUERDOS
    acuerdos_estatico = {
        "tipo": "acuerdos_resoluciones",
        "titulo": "ACUERDOS Y RESOLUCIONES ESPECÍFICAS",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "estructura_acuerdos": [
            {
                "tipo": "ACUERDO MUNICIPAL",
                "numero": "[NUMERO_ACUERDO]",
                "fecha": "[FECHA_ACUERDO]",
                "asunto": "[ASUNTO_ACUERDO]",
                "considerandos": ["[CONSIDERANDO_1]", "[CONSIDERANDO_2]"],
                "resuelve": "[RESOLUCION]",
                "vigencia": "[FECHA_VIGENCIA]",
                "publicacion": "Registro Oficial Municipal"
            }
        ],
        "clasificacion": {
            "administrativos": ["[ACUERDO_ADM_1]"],
            "financieros": ["[ACUERDO_FIN_1]"],
            "normativos": ["[ACUERDO_NOR_1]"],
            "operativos": ["[ACUERDO_OPE_1]"]
        }
    }
    
    # COMPROMISOS
    compromisos_estatico = {
        "tipo": "compromisos_tareas",
        "titulo": "COMPROMISOS Y TAREAS ASIGNADAS",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "compromisos": [
            {
                "id": "[ID_COMPROMISO]",
                "descripcion": "[DESCRIPCION_COMPROMISO]",
                "responsable": "[FUNCIONARIO_RESPONSABLE]",
                "area": "[DEPARTAMENTO]",
                "plazo": "[FECHA_LIMITE]",
                "prioridad": "[ALTA/MEDIA/BAJA]",
                "recursos_asignados": "[RECURSOS]",
                "indicador_cumplimiento": "[INDICADOR]"
            }
        ],
        "seguimiento": {
            "frecuencia": "Quincenal",
            "responsable_seguimiento": "Secretario General",
            "formato_reporte": "Informe de avance"
        }
    }
    
    # SEGUIMIENTO
    seguimiento_estatico = {
        "tipo": "seguimiento_acuerdos",
        "titulo": "SEGUIMIENTO DE ACUERDOS ANTERIORES",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "acuerdos_seguimiento": [
            {
                "acuerdo_referencia": "[NUMERO_ACUERDO_ANTERIOR]",
                "fecha_original": "[FECHA_ACUERDO]",
                "responsable": "[FUNCIONARIO]",
                "estado": "[CUMPLIDO/PENDIENTE/EN_PROCESO]",
                "porcentaje_avance": "[PORCENTAJE]%",
                "observaciones": "[OBSERVACIONES_AVANCE]",
                "nueva_fecha_limite": "[NUEVA_FECHA]"
            }
        ],
        "estadisticas": {
            "total_seguimientos": "[NUMERO]",
            "cumplidos": "[NUMERO]",
            "pendientes": "[NUMERO]",
            "tasa_cumplimiento": "[PORCENTAJE]%"
        }
    }
    
    # FIRMAS
    firmas_estatico = {
        "tipo": "firmas_validaciones",
        "titulo": "FIRMAS Y VALIDACIONES OFICIALES",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "firmas_requeridas": [
            {
                "cargo": "Alcalde",
                "nombre_completo": "[NOMBRE_ALCALDE]",
                "cedula": "[CEDULA_ALCALDE]",
                "firma_digital": "[HASH_FIRMA]",
                "timestamp": "[FECHA_HORA_FIRMA]",
                "ubicacion": "Pastaza, Ecuador"
            },
            {
                "cargo": "Secretario General",
                "nombre_completo": "[NOMBRE_SECRETARIO]",
                "cedula": "[CEDULA_SECRETARIO]", 
                "firma_digital": "[HASH_FIRMA]",
                "timestamp": "[FECHA_HORA_FIRMA]",
                "ubicacion": "Pastaza, Ecuador"
            }
        ],
        "sellos_institucionales": {
            "sello_municipal": "Requerido",
            "codigo_verificacion": "[CODIGO_QR]",
            "hash_documento": "[SHA256]"
        }
    }
    
    # ANEXOS
    anexos_estatico = {
        "tipo": "anexos_documentos",
        "titulo": "ANEXOS Y DOCUMENTOS DE SOPORTE",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "documentos_anexos": [
            {
                "tipo": "Proyecto de Ordenanza",
                "nombre": "[NOMBRE_DOCUMENTO]",
                "numero_paginas": "[NUM_PAGINAS]",
                "fecha_elaboracion": "[FECHA_DOC]",
                "autor": "[AUTOR_DOCUMENTO]",
                "version": "[VERSION]",
                "archivo_digital": "[RUTA_ARCHIVO]"
            }
        ],
        "clasificacion": {
            "tecnicos": ["[DOC_TEC_1]", "[DOC_TEC_2]"],
            "legales": ["[DOC_LEG_1]", "[DOC_LEG_2]"],
            "financieros": ["[DOC_FIN_1]", "[DOC_FIN_2]"],
            "administrativos": ["[DOC_ADM_1]", "[DOC_ADM_2]"]
        }
    }
    
    # MARCO LEGAL
    legal_estatico = {
        "tipo": "marco_legal",
        "titulo": "MARCO LEGAL Y NORMATIVO APLICABLE",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "normativa_aplicable": {
            "constitucion": {
                "articulos": ["Art. 238", "Art. 264", "Art. 267"],
                "descripcion": "Autonomía y competencias municipales"
            },
            "cootad": {
                "articulos": ["Art. 57", "Art. 58", "Art. 59"],
                "descripcion": "Funcionamiento de gobiernos locales"
            },
            "reglamento_interno": {
                "capitulos": ["Cap. III", "Cap. IV"],
                "descripcion": "Procedimientos internos GAD Pastaza"
            }
        },
        "jurisprudencia": {
            "sentencias_cc": ["[SENTENCIA_1]"],
            "dictamenes_pg": ["[DICTAMEN_1]"],
            "resoluciones_cge": ["[RESOLUCION_1]"]
        }
    }
    
    # OTROS
    otros_estatico = {
        "tipo": "informacion_adicional",
        "titulo": "INFORMACIÓN ADICIONAL Y VARIOS",
        "atributos": {
            "negrita": True,
            "tamano_fuente": "13px"
        },
        "informacion_complementaria": {
            "observaciones_generales": ["[OBSERVACION_1]", "[OBSERVACION_2]"],
            "incidentes_sesion": ["[INCIDENTE_1]"],
            "invitados_especiales": [
                {
                    "nombre": "[NOMBRE_INVITADO]",
                    "cargo": "[CARGO_INVITADO]",
                    "institucion": "[INSTITUCION]",
                    "motivo_participacion": "[MOTIVO]"
                }
            ]
        },
        "aspectos_tecnicos": {
            "sistema_grabacion": "Digital HD",
            "calidad_audio": "[CALIDAD]",
            "duracion_grabacion": "[DURACION]",
            "formato_archivo": "MP4/WAV"
        },
        "proxima_sesion": {
            "fecha_tentativa": "[FECHA_PROXIMA]",
            "agenda_preliminar": ["[PUNTO_1]", "[PUNTO_2]"]
        }
    }
    
    segmentos_finales = [
        # ACUERDOS
        ('ACUERDOS_ESTATICO', 'Acuerdos Municipales Estático', 'acuerdos', 'estatico',
         json.dumps(acuerdos_estatico, ensure_ascii=False, indent=2), ''),
         
        ('ACUERDOS_DINAMICO', 'Acuerdos Municipales Dinámico', 'acuerdos', 'dinamico', '{}',
         '''Extrae todos los acuerdos y resoluciones específicas adoptadas en la sesión.

INFORMACIÓN A EXTRAER:
- Acuerdos municipales con numeración oficial
- Asuntos específicos de cada acuerdo
- Considerandos mencionados
- Fechas de vigencia establecidas
- Clasificación por tipo (administrativo/financiero/normativo)

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "acuerdos": [
    {
      "numero": "001-GAD-MP-2025",
      "asunto": "Asunto específico extraído",
      "considerandos": ["Considerando 1", "Considerando 2"],
      "vigencia": "Inmediata",
      "clasificacion": "administrativo"
    }
  ]
}'''),

        # COMPROMISOS
        ('COMPROMISOS_ESTATICO', 'Compromisos Municipales Estático', 'compromisos', 'estatico',
         json.dumps(compromisos_estatico, ensure_ascii=False, indent=2), ''),
         
        ('COMPROMISOS_DINAMICO', 'Compromisos Municipales Dinámico', 'compromisos', 'dinamico', '{}',
         '''Identifica compromisos y tareas asignadas durante la sesión municipal.

INFORMACIÓN A EXTRAER:
- Tareas específicas asignadas
- Funcionarios responsables identificados
- Plazos establecidos para cumplimiento
- Recursos asignados mencionados
- Indicadores de seguimiento definidos

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "compromisos": [
    {
      "descripcion": "Tarea específica extraída",
      "responsable": "Nombre del funcionario",
      "plazo": "30 días",
      "prioridad": "Alta",
      "area": "Departamento responsable"
    }
  ]
}'''),

        # SEGUIMIENTO
        ('SEGUIMIENTO_ESTATICO', 'Seguimiento Municipal Estático', 'seguimiento', 'estatico',
         json.dumps(seguimiento_estatico, ensure_ascii=False, indent=2), ''),
         
        ('SEGUIMIENTO_DINAMICO', 'Seguimiento Municipal Dinámico', 'seguimiento', 'dinamico', '{}',
         '''Extrae información sobre seguimiento de acuerdos y compromisos anteriores.

INFORMACIÓN A EXTRAER:
- Referencias a acuerdos anteriores mencionados
- Estados de cumplimiento reportados
- Porcentajes de avance informados
- Nuevos plazos establecidos
- Observaciones sobre el progreso

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "seguimientos": [
    {
      "acuerdo_referencia": "Número de acuerdo anterior",
      "estado": "EN_PROCESO",
      "porcentaje_avance": "75%",
      "observaciones": "Observaciones extraídas"
    }
  ]
}'''),

        # FIRMAS
        ('FIRMAS_ESTATICO', 'Firmas Municipales Estático', 'firmas', 'estatico',
         json.dumps(firmas_estatico, ensure_ascii=False, indent=2), ''),
         
        ('FIRMAS_DINAMICO', 'Firmas Municipales Dinámico', 'firmas', 'dinamico', '{}',
         '''Identifica las autoridades que firman el acta y datos de validación.

INFORMACIÓN A EXTRAER:
- Nombres completos de firmantes
- Cargos oficiales de las autoridades
- Hora y fecha de las firmas
- Menciones sobre sellos institucionales
- Códigos de verificación si se mencionan

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "firmantes": [
    {
      "nombre": "Nombre completo extraído",
      "cargo": "Cargo oficial",
      "fecha_firma": "27 de septiembre de 2025",
      "hora_firma": "11:30"
    }
  ],
  "validaciones": "Información de sellos o códigos mencionados"
}'''),

        # ANEXOS
        ('ANEXOS_ESTATICO', 'Anexos Municipales Estático', 'anexos', 'estatico',
         json.dumps(anexos_estatico, ensure_ascii=False, indent=2), ''),
         
        ('ANEXOS_DINAMICO', 'Anexos Municipales Dinámico', 'anexos', 'dinamico', '{}',
         '''Identifica documentos anexos y de soporte mencionados en la sesión.

INFORMACIÓN A EXTRAER:
- Documentos técnicos referenciados
- Proyectos de ordenanza mencionados
- Informes presentados
- Estudios de soporte citados
- Versiones de documentos especificadas

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "documentos": [
    {
      "nombre": "Nombre del documento extraído",
      "tipo": "Proyecto de Ordenanza",
      "autor": "Autor mencionado",
      "version": "v1.0",
      "fecha": "Fecha del documento"
    }
  ]
}'''),

        # LEGAL
        ('LEGAL_ESTATICO', 'Marco Legal Municipal Estático', 'legal', 'estatico',
         json.dumps(legal_estatico, ensure_ascii=False, indent=2), ''),
         
        ('LEGAL_DINAMICO', 'Marco Legal Municipal Dinámico', 'legal', 'dinamico', '{}',
         '''Extrae referencias legales y normativas mencionadas durante la sesión.

INFORMACIÓN A EXTRAER:
- Artículos de la Constitución citados
- Referencias al COOTAD mencionadas
- Reglamentos internos aplicados
- Jurisprudencia citada
- Dictámenes legales referenciados

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "constitucion": ["Art. 238", "Art. 264"],
  "cootad": ["Art. 57", "Art. 58"],
  "reglamento_interno": ["Cap. III"],
  "jurisprudencia": ["Sentencia o dictamen mencionado"],
  "otras_normas": ["Normativa adicional citada"]
}'''),

        # OTROS
        ('OTROS_ESTATICO', 'Información Adicional Municipal Estática', 'otros', 'estatico',
         json.dumps(otros_estatico, ensure_ascii=False, indent=2), ''),
         
        ('OTROS_DINAMICO', 'Información Adicional Municipal Dinámica', 'otros', 'dinamico', '{}',
         '''Captura información adicional y varios no clasificados en otras categorías.

INFORMACIÓN A EXTRAER:
- Observaciones generales importantes
- Incidentes durante la sesión
- Invitados especiales mencionados
- Aspectos técnicos de grabación
- Información sobre próximas sesiones

FORMATO DE RESPUESTA:
Responde únicamente en formato JSON válido específicamente de la siguiente manera sin contexto sin abertura en texto plano directamente y sin explicación final sin nada específicamente así:
{
  "observaciones": ["Observación 1", "Observación 2"],
  "incidentes": ["Incidente reportado"],
  "invitados_especiales": [{"nombre": "Nombre", "institucion": "Institución"}],
  "proxima_sesion": "Fecha tentativa mencionada",
  "aspectos_tecnicos": "Información técnica relevante"
}''')
    ]
    
    contador = 0
    for codigo, nombre, categoria, tipo, contenido, prompt in segmentos_finales:
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
                orden_defecto=contador + 25,
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
    
    print(f"\n🎉 PARTE 2 FINAL COMPLETADA: {contador} segmentos creados")
    return contador

if __name__ == "__main__":
    total_creados = completar_segmentos_finales()
    print(f"\n📊 Segmentos creados en esta ejecución: {total_creados}")
    
    # Mostrar estado FINAL
    total_final = SegmentoPlantilla.objects.count()
    print(f"📈 Total segmentos en sistema: {total_final}")
    print(f"🎯 Objetivo alcanzado: {total_final}/34 segmentos")
    
    if total_final == 34:
        print("🏆 ¡OBJETIVO COMPLETADO! 17 estáticos + 17 dinámicos")
    else:
        print(f"📋 Faltan: {34 - total_final} segmentos")
    
    # Mostrar resumen por categoría
    print(f"\n📋 RESUMEN POR CATEGORÍAS:")
    categorias = ['encabezado', 'titulo', 'fecha_hora', 'participantes', 'orden_dia', 
                  'introduccion', 'desarrollo', 'transcripcion', 'resumen', 'acuerdos', 
                  'compromisos', 'seguimiento', 'cierre', 'firmas', 'anexos', 'legal', 'otros']
    
    for cat in categorias:
        estatico = SegmentoPlantilla.objects.filter(categoria=cat, tipo='estatico').count()
        dinamico = SegmentoPlantilla.objects.filter(categoria=cat, tipo='dinamico').count()
        total_cat = estatico + dinamico
        print(f"   {cat}: {estatico}E + {dinamico}D = {total_cat}")