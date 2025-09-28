#!/usr/bin/env python3
"""
Script simplificado para crear segmentos usando Django ORM
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

def crear_segmentos():
    """Crear todos los segmentos"""
    
    # Limpiar existentes
    count = SegmentoPlantilla.objects.count()
    SegmentoPlantilla.objects.all().delete()
    print(f"🗑️ Eliminados {count} segmentos existentes")
    
    # Obtener referencias necesarias
    admin_user = User.objects.filter(is_superuser=True).first()
    proveedor_ia = ProveedorIA.objects.filter(activo=True).first()
    
    # Crear segmentos estáticos
    estaticos = [
        ('ENCABEZADO_ESTATICO', 'Encabezado de Acta Municipal', 'encabezado', 
         '<div class="encabezado-acta"><h2 class="text-center">GOBIERNO AUTÓNOMO DESCENTRALIZADO MUNICIPAL DE PASTAZA</h2><h3 class="text-center">ACTA DE SESIÓN {{tipo_sesion|upper}}</h3><p><strong>Fecha:</strong> {{fecha}}</p><p><strong>Lugar:</strong> {{lugar}}</p></div>'),
        
        ('PARTICIPANTES_ESTATICO', 'Lista de Participantes Municipal', 'participantes',
         '<div class="participantes-sesion"><h4>PARTICIPANTES</h4><ul>{% for p in participantes %}<li>{{p.nombre}} - {{p.cargo}}</li>{% endfor %}</ul><p><strong>Quórum:</strong> {{quorum}}</p></div>'),
        
        ('AGENDA_ESTATICA', 'Agenda de Sesión Municipal', 'agenda',
         '<div class="agenda-sesion"><h4>ORDEN DEL DÍA</h4><ol>{% for punto in agenda %}<li><strong>{{punto.titulo}}</strong></li>{% endfor %}</ol></div>'),
        
        ('DECISIONES_ESTATICAS', 'Decisiones y Acuerdos Municipales', 'decisiones',
         '<div class="decisiones-acuerdos"><h4>DECISIONES ADOPTADAS</h4>{% for d in decisiones %}<div><h5>{{d.tipo}} No. {{d.numero}}</h5><p><strong>Asunto:</strong> {{d.asunto}}</p><p><strong>Resultado:</strong> {{d.resultado}}</p></div>{% endfor %}</div>'),
        
        ('CIERRE_ESTATICO', 'Cierre y Firmas del Acta', 'cierre',
         '<div class="cierre-acta"><h4>CLAUSURA</h4><p>Se clausura la sesión a las <strong>{{hora_clausura}}</strong></p><div class="firmas"><p><strong>{{alcalde}}</strong><br>ALCALDE</p><p><strong>{{secretario}}</strong><br>SECRETARIO</p></div></div>')
    ]
    
    # Crear segmentos dinámicos
    dinamicos = [
        ('ENCABEZADO_DINAMICO', 'Encabezado Dinámico con IA', 'encabezado',
         'Genera encabezado personalizado para acta municipal con tipo de sesión {{tipo_sesion}}, fecha {{fecha}} y tema {{tema_principal}}'),
        
        ('PARTICIPANTES_DINAMICO', 'Participantes Dinámico con IA', 'participantes',
         'Extrae y organiza lista de participantes de audio {{participantes_audio}} con roles {{cargos_detectados}} y calcula quórum automáticamente'),
        
        ('AGENDA_DINAMICA', 'Agenda Dinámica con IA', 'agenda',
         'Estructura agenda municipal de temas detectados {{temas_detectados}} en orden cronológico {{cronologia}} según normativa COOTAD'),
        
        ('DECISIONES_DINAMICAS', 'Decisiones Dinámicas con IA', 'decisiones',
         'Identifica decisiones municipales {{decisiones_detectadas}} con votaciones {{resultados_votacion}} y clasifica por tipo normativo'),
        
        ('CIERRE_DINAMICO', 'Cierre Dinámico con IA', 'cierre',
         'Genera cierre personalizado con hora {{hora_fin}}, resumen {{acuerdos_principales}} y próximas sesiones {{proximas_fechas}}')
    ]
    
    total_creados = 0
    
    # Crear estáticos
    for codigo, nombre, categoria, contenido in estaticos:
        try:
            segmento = SegmentoPlantilla.objects.create(
                codigo=codigo,
                nombre=nombre,
                descripcion=f"Segmento estático para {categoria}",
                categoria=categoria,
                tipo='estatico',
                contenido_estatico=contenido,
                formato_salida='html',
                prompt_ia='',
                prompt_sistema='',
                proveedor_ia=proveedor_ia,
                estructura_json={},
                validaciones_salida={},
                formato_validacion='html',
                parametros_entrada={},
                variables_personalizadas={},
                contexto_requerido={},
                orden_defecto=total_creados + 1,
                reutilizable=True,
                obligatorio=False,
                activo=True,
                longitud_maxima=5000,
                tiempo_limite_ia=30,
                reintentos_ia=3,
                total_usos=0,
                total_errores=0,
                tiempo_promedio_procesamiento=0.0,
                tasa_exito=0.0,
                usuario_creacion=admin_user
            )
            print(f"✅ Creado estático: {codigo}")
            total_creados += 1
        except Exception as e:
            print(f"❌ Error creando {codigo}: {e}")
    
    # Crear dinámicos
    for codigo, nombre, categoria, prompt in dinamicos:
        try:
            segmento = SegmentoPlantilla.objects.create(
                codigo=codigo,
                nombre=nombre,
                descripcion=f"Segmento dinámico para {categoria}",
                categoria=categoria,
                tipo='dinamico',
                contenido_estatico='',
                formato_salida='html',
                prompt_ia=prompt,
                prompt_sistema='Eres un asistente especializado en redacción de actas municipales ecuatorianas siguiendo normativa COOTAD.',
                proveedor_ia=proveedor_ia,
                estructura_json={},
                validaciones_salida={},
                formato_validacion='html',
                parametros_entrada={},
                variables_personalizadas={},
                contexto_requerido={},
                orden_defecto=total_creados + 1,
                reutilizable=True,
                obligatorio=False,
                activo=True,
                longitud_maxima=10000,
                tiempo_limite_ia=60,
                reintentos_ia=3,
                total_usos=0,
                total_errores=0,
                tiempo_promedio_procesamiento=0.0,
                tasa_exito=0.0,
                usuario_creacion=admin_user
            )
            print(f"✅ Creado dinámico: {codigo}")
            total_creados += 1
        except Exception as e:
            print(f"❌ Error creando {codigo}: {e}")
    
    print(f"\n🎉 CREADOS {total_creados} segmentos en total")
    
    # Mostrar resultado final
    print(f"\n📋 SEGMENTOS FINALES:")
    for seg in SegmentoPlantilla.objects.all().order_by('categoria', 'tipo'):
        print(f"   ID {seg.pk}: {seg.nombre} ({seg.tipo} - {seg.categoria})")

if __name__ == "__main__":
    crear_segmentos()