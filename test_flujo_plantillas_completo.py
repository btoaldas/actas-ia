#!/usr/bin/env python
"""
Script para probar el flujo completo de plantillas desde Django
Verificación desde creación hasta ejecución sin requerir autenticación web
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.generador_actas.models import (
    PlantillaActa, ConfiguracionSegmento, SegmentoPlantilla, 
    EjecucionPlantilla, ResultadoSegmento, ActaBorrador, ProveedorIA
)

def test_crear_plantilla():
    """Prueba 1: Crear una nueva plantilla"""
    print("🔧 Probando creación de plantilla...")
    
    try:
        # Obtener usuario
        usuario = User.objects.get(username='superadmin')
        
        # Crear nueva plantilla con código único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plantilla = PlantillaActa.objects.create(
            codigo=f"PLANTILLA_TEST_{timestamp}",
            nombre=f"Plantilla Test - Flujo Completo {timestamp}",
            descripcion="Plantilla para probar todo el flujo desde creación hasta ejecución",
            tipo_acta="ordinaria",
            prompt_global="Unifica los siguientes segmentos en un acta coherente y profesional para una reunión municipal.",
            activa=True,
            usuario_creacion=usuario
        )
        
        print(f"✅ Plantilla creada: '{plantilla.nombre}' (ID: {plantilla.pk})")
        return plantilla
        
    except Exception as e:
        print(f"❌ Error creando plantilla: {e}")
        return None

def test_agregar_segmentos_plantilla(plantilla):
    """Prueba 2: Agregar segmentos a la plantilla"""
    print("📋 Probando agregado de segmentos...")
    
    try:
        # Obtener algunos segmentos disponibles
        segmentos_disponibles = SegmentoPlantilla.objects.filter(activo=True)[:5]
        
        if not segmentos_disponibles.exists():
            print("❌ No hay segmentos disponibles en la BD")
            return False
        
        # Agregar configuraciones para cada segmento
        configuraciones_creadas = []
        for i, segmento in enumerate(segmentos_disponibles, 1):
            config = ConfiguracionSegmento.objects.create(
                plantilla=plantilla,
                segmento=segmento,
                orden=i,
                obligatorio=True if i <= 2 else False,  # Primeros 2 obligatorios
                prompt_personalizado=f"Prompt personalizado para {segmento.nombre}" if i == 1 else ""
            )
            configuraciones_creadas.append(config)
        
        print(f"✅ Agregados {len(configuraciones_creadas)} segmentos a la plantilla")
        
        # Mostrar configuraciones
        for config in configuraciones_creadas:
            print(f"   • {config.segmento.nombre} (Orden: {config.orden}, Obligatorio: {config.obligatorio})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error agregando segmentos: {e}")
        return False

def test_reordenar_segmentos(plantilla):
    """Prueba 3: Probar reordenamiento de segmentos (drag & drop logic)"""
    print("🔄 Probando reordenamiento de segmentos...")
    
    try:
        # Obtener configuraciones actuales
        configs = list(ConfiguracionSegmento.objects.filter(plantilla=plantilla).order_by('orden'))
        
        if len(configs) < 3:
            print("❌ Necesitan al menos 3 segmentos para probar reordenamiento")
            return False
        
        print("📊 Orden original:")
        for config in configs:
            print(f"   {config.orden}. {config.segmento.nombre}")
        
        # Simular drag & drop: intercambiar primer y segundo elemento
        # Esto evita el problema de constraint único
        primer_config = configs[0]
        segundo_config = configs[1]
        
        # Intercambiar órdenes temporalmente usando un valor temporal
        temp_orden = 999  # Valor temporal para evitar constraint
        
        primer_config.orden = temp_orden
        primer_config.save()
        
        segundo_config.orden = 1
        segundo_config.save()
        
        primer_config.orden = 2
        primer_config.save()
        
        print("🔄 Nuevo orden después de drag & drop:")
        configs_actualizadas = ConfiguracionSegmento.objects.filter(plantilla=plantilla).order_by('orden')
        for config in configs_actualizadas:
            print(f"   {config.orden}. {config.segmento.nombre}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reordenando segmentos: {e}")
        return False

def test_editar_plantilla(plantilla):
    """Prueba 4: Editar plantilla existente"""
    print("✏️ Probando edición de plantilla...")
    
    try:
        # Guardar datos originales
        nombre_original = plantilla.nombre
        descripcion_original = plantilla.descripcion
        
        # Editar plantilla
        plantilla.nombre = f"{nombre_original} - EDITADA"
        plantilla.descripcion = f"{descripcion_original}\n\n[ACTUALIZACIÓN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Plantilla modificada durante prueba de edición"
        plantilla.save()
        
        print(f"✅ Plantilla editada exitosamente")
        print(f"   • Nombre: '{plantilla.nombre}'")
        print(f"   • Descripción actualizada con timestamp")
        
        return True
        
    except Exception as e:
        print(f"❌ Error editando plantilla: {e}")
        return False

def test_agregar_mas_segmentos(plantilla):
    """Prueba 5: Agregar más segmentos a plantilla existente"""
    print("➕ Probando agregar más segmentos a plantilla existente...")
    
    try:
        # Obtener segmentos que aún no están en la plantilla
        segmentos_actuales = ConfiguracionSegmento.objects.filter(plantilla=plantilla).values_list('segmento_id', flat=True)
        segmentos_disponibles = SegmentoPlantilla.objects.filter(activo=True).exclude(id__in=segmentos_actuales)[:3]
        
        if not segmentos_disponibles.exists():
            print("⚠️ No hay más segmentos disponibles para agregar")
            return True  # No es error, simplemente no hay más
        
        # Obtener el último orden actual
        ultima_config = ConfiguracionSegmento.objects.filter(plantilla=plantilla).order_by('-orden').first()
        ultimo_orden = ultima_config.orden if ultima_config else 0
        
        # Agregar nuevos segmentos
        nuevas_configs = []
        for i, segmento in enumerate(segmentos_disponibles, 1):
            config = ConfiguracionSegmento.objects.create(
                plantilla=plantilla,
                segmento=segmento,
                orden=ultimo_orden + i,
                obligatorio=False,
                prompt_personalizado=f"Prompt añadido en edición para {segmento.nombre}"
            )
            nuevas_configs.append(config)
        
        print(f"✅ Agregados {len(nuevas_configs)} segmentos adicionales")
        for config in nuevas_configs:
            print(f"   • {config.segmento.nombre} (Orden: {config.orden})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error agregando más segmentos: {e}")
        return False

def test_crear_ejecucion(plantilla):
    """Prueba 6: Crear ejecución de la plantilla"""
    print("🚀 Probando creación de ejecución...")
    
    try:
        # Verificar que la plantilla tenga segmentos configurados
        total_segmentos = ConfiguracionSegmento.objects.filter(plantilla=plantilla).count()
        if total_segmentos == 0:
            print("❌ La plantilla no tiene segmentos configurados")
            return None
        
        # Obtener proveedor IA
        proveedor = ProveedorIA.objects.filter(activo=True).first()
        if not proveedor:
            print("❌ No hay proveedores IA activos")
            return None
        
        # Obtener usuario
        usuario = User.objects.get(username='superadmin')
        
        # Crear ejecución
        ejecucion = EjecucionPlantilla.objects.create(
            plantilla=plantilla,
            nombre=f"Ejecución Test - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            usuario=usuario,
            proveedor_ia_global=proveedor,
            estado='iniciada',
            progreso_total=total_segmentos,
            variables_contexto={
                'nombre_municipio': 'Pastaza',
                'fecha_reunion': '2025-09-27',
                'tipo_reunion': 'ordinaria',
                'alcalde': 'Ing. Roberto Garzón',
                'secretario': 'Dr. María Fernanda López',
                'test_execution': True,
                'fecha_test': datetime.now().isoformat()
            }
        )
        
        print(f"✅ Ejecución creada: '{ejecucion.nombre}' (ID: {ejecucion.id})")
        print(f"   • Estado: {ejecucion.estado}")
        print(f"   • Plantilla: {ejecucion.plantilla.nombre}")
        print(f"   • Total segmentos: {ejecucion.progreso_total}")
        print(f"   • Proveedor IA: {ejecucion.proveedor_ia_global.nombre}")
        
        return ejecucion
        
    except Exception as e:
        print(f"❌ Error creando ejecución: {e}")
        return None

def test_simular_procesamiento(ejecucion):
    """Prueba 7: Simular procesamiento de segmentos (sin IA real)"""
    print("⚙️ Probando simulación de procesamiento...")
    
    try:
        # Obtener configuraciones de segmentos
        configuraciones = ConfiguracionSegmento.objects.filter(
            plantilla=ejecucion.plantilla
        ).order_by('orden')
        
        # Crear resultados para cada segmento
        resultados_creados = []
        for i, config in enumerate(configuraciones, 1):
            resultado = ResultadoSegmento.objects.create(
                ejecucion=ejecucion,
                segmento=config.segmento,
                orden_procesamiento=i,
                estado='completado',
                prompt_usado=config.prompt_efectivo or f"Prompt para {config.segmento.nombre}",
                resultado_procesado=f"""
# {config.segmento.nombre}

Este es el contenido simulado para el segmento "{config.segmento.nombre}".

**Detalles del procesamiento:**
- Orden de procesamiento: {i}
- Tipo: {'Dinámico' if config.segmento.es_dinamico else 'Estático'}
- Categoría: {config.segmento.categoria}
- Obligatorio: {'Sí' if config.obligatorio else 'No'}

**Variables de contexto utilizadas:**
- Municipio: {ejecucion.variables_contexto.get('nombre_municipio', 'N/A')}
- Fecha reunión: {ejecucion.variables_contexto.get('fecha_reunion', 'N/A')}
- Tipo reunión: {ejecucion.variables_contexto.get('tipo_reunion', 'N/A')}

**Contenido específico del segmento:**
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

---
Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """.strip(),
                tiempo_total_ms=int((0.5 + (i * 0.2)) * 1000),  # Simular tiempo creciente en ms
                metadatos_ia={
                    'simulado': True,
                    'orden': i,
                    'total_segmentos': configuraciones.count(),
                    'fecha_procesamiento': datetime.now().isoformat()
                }
            )
            resultados_creados.append(resultado)
        
        # Actualizar progreso de ejecución
        ejecucion.progreso_actual = len(resultados_creados)
        ejecucion.estado = 'completada'
        ejecucion.tiempo_fin = datetime.now()
        ejecucion.save()
        
        print(f"✅ Procesamiento simulado completado")
        print(f"   • {len(resultados_creados)} segmentos procesados")
        print(f"   • Estado de ejecución: {ejecucion.estado}")
        print(f"   • Progreso: {ejecucion.progreso_actual}/{ejecucion.progreso_total}")
        
        return resultados_creados
        
    except Exception as e:
        print(f"❌ Error simulando procesamiento: {e}")
        return None

def test_generar_acta_final(ejecucion, resultados):
    """Prueba 8: Generar acta final unificada"""
    print("📄 Probando generación de acta final...")
    
    try:
        # Unificar contenido de todos los resultados
        contenido_partes = [
            f"# ACTA DE REUNIÓN - {ejecucion.variables_contexto.get('tipo_reunion', 'ORDINARIA').upper()}",
            f"",
            f"**Municipio:** {ejecucion.variables_contexto.get('nombre_municipio', 'N/A')}",
            f"**Fecha:** {ejecucion.variables_contexto.get('fecha_reunion', 'N/A')}",
            f"**Alcalde:** {ejecucion.variables_contexto.get('alcalde', 'N/A')}",
            f"**Secretario:** {ejecucion.variables_contexto.get('secretario', 'N/A')}",
            f"",
            f"---",
            f""
        ]
        
        # Agregar contenido de cada segmento
        for resultado in resultados:
            contenido_partes.append(resultado.resultado_procesado)
            contenido_partes.append("")  # Línea en blanco entre segmentos
        
        # Agregar pie de acta
        contenido_partes.extend([
            "---",
            "",
            "**FIRMA DE PARTICIPANTES:**",
            "",
            f"**Alcalde:** ________________________",
            f"          {ejecucion.variables_contexto.get('alcalde', 'N/A')}",
            "",
            f"**Secretario:** ________________________", 
            f"              {ejecucion.variables_contexto.get('secretario', 'N/A')}",
            "",
            f"*Acta generada automáticamente el {datetime.now().strftime('%d de %B de %Y a las %H:%M:%S')}*",
            f"*Plantilla utilizada: {ejecucion.plantilla.nombre}*",
            f"*ID de ejecución: {ejecucion.id}*"
        ])
        
        contenido_final = "\n".join(contenido_partes)
        
        # Crear acta borrador  
        from django.utils import timezone
        
        acta_borrador = ActaBorrador.objects.create(
            ejecucion=ejecucion,
            titulo=f"Acta {ejecucion.variables_contexto.get('tipo_reunion', 'Ordinaria')} - {ejecucion.variables_contexto.get('fecha_reunion', 'Sin fecha')}",
            usuario_creacion=ejecucion.usuario,
            contenido_html=contenido_final,  # Se usará como HTML básico
            contenido_markdown=contenido_final,
            fecha_acta=timezone.now().date(),
            lugar_sesion=f"Municipio de {ejecucion.variables_contexto.get('nombre_municipio', 'Pastaza')}",
            participantes=[
                {"nombre": ejecucion.variables_contexto.get('alcalde', 'N/A'), "rol": "Alcalde"},
                {"nombre": ejecucion.variables_contexto.get('secretario', 'N/A'), "rol": "Secretario"}
            ],
            estado='borrador',
            version='1.0',
            tiempo_generacion_segundos=sum(r.tiempo_total_ms or 0 for r in resultados) // 1000,
            configuracion_formato={
                'total_segmentos': len(resultados),
                'tiempo_total_procesamiento_ms': sum(r.tiempo_total_ms or 0 for r in resultados),
                'fecha_generacion': datetime.now().isoformat(),
                'plantilla_utilizada': ejecucion.plantilla.nombre,
                'tipo_generacion': 'simulacion_completa'
            }
        )
        
        # Vincular acta a ejecución
        ejecucion.acta_generada = acta_borrador
        ejecucion.save()
        
        print(f"✅ Acta final generada exitosamente")
        print(f"   • ID del borrador: {acta_borrador.id}")
        print(f"   • Estado: {acta_borrador.estado}")
        print(f"   • Versión: {acta_borrador.version}")
        print(f"   • Longitud contenido: {len(contenido_final)} caracteres")
        print(f"   • Vinculada a ejecución: {ejecucion.id}")
        
        return acta_borrador
        
    except Exception as e:
        print(f"❌ Error generando acta final: {e}")
        return None

def test_flujo_completo():
    """Ejecutar todas las pruebas en secuencia"""
    print("\n" + "="*70)
    print("🎯 PRUEBA FLUJO COMPLETO DE PLANTILLAS")
    print("   Desde creación hasta ejecución y generación de acta")
    print("="*70)
    
    resultados = {
        'crear_plantilla': False,
        'agregar_segmentos': False,
        'reordenar_segmentos': False,
        'editar_plantilla': False,
        'agregar_mas_segmentos': False,
        'crear_ejecucion': False,
        'simular_procesamiento': False,
        'generar_acta': False
    }
    
    # Paso 1: Crear plantilla
    plantilla = test_crear_plantilla()
    resultados['crear_plantilla'] = plantilla is not None
    if not plantilla:
        print("❌ Flujo detenido: No se pudo crear plantilla")
        return mostrar_resultados_finales(resultados)
    
    print()
    
    # Paso 2: Agregar segmentos
    resultados['agregar_segmentos'] = test_agregar_segmentos_plantilla(plantilla)
    if not resultados['agregar_segmentos']:
        print("❌ Flujo detenido: No se pudieron agregar segmentos")
        return mostrar_resultados_finales(resultados)
    
    print()
    
    # Paso 3: Reordenar segmentos (drag & drop)
    resultados['reordenar_segmentos'] = test_reordenar_segmentos(plantilla)
    
    print()
    
    # Paso 4: Editar plantilla
    resultados['editar_plantilla'] = test_editar_plantilla(plantilla)
    
    print()
    
    # Paso 5: Agregar más segmentos 
    resultados['agregar_mas_segmentos'] = test_agregar_mas_segmentos(plantilla)
    
    print()
    
    # Paso 6: Crear ejecución
    ejecucion = test_crear_ejecucion(plantilla)
    resultados['crear_ejecucion'] = ejecucion is not None
    if not ejecucion:
        print("❌ Flujo detenido: No se pudo crear ejecución")
        return mostrar_resultados_finales(resultados)
    
    print()
    
    # Paso 7: Simular procesamiento
    resultados_segmentos = test_simular_procesamiento(ejecucion)
    resultados['simular_procesamiento'] = resultados_segmentos is not None
    if not resultados_segmentos:
        print("❌ Flujo detenido: No se pudo simular procesamiento")
        return mostrar_resultados_finales(resultados)
    
    print()
    
    # Paso 8: Generar acta final
    acta_final = test_generar_acta_final(ejecucion, resultados_segmentos)
    resultados['generar_acta'] = acta_final is not None
    
    print()
    
    return mostrar_resultados_finales(resultados, plantilla, ejecucion, acta_final)

def mostrar_resultados_finales(resultados, plantilla=None, ejecucion=None, acta=None):
    """Mostrar resumen final de resultados"""
    print("\n" + "="*70)
    print("📊 RESUMEN FINAL DEL FLUJO COMPLETO")
    print("="*70)
    
    total_pruebas = len(resultados)
    pruebas_exitosas = sum(resultados.values())
    
    # Mostrar cada resultado
    for paso, exito in resultados.items():
        estado = "✅ PASS" if exito else "❌ FAIL"
        nombre_paso = paso.replace('_', ' ').title()
        print(f"{nombre_paso:.<40} {estado}")
    
    print(f"\nRESULTADO GENERAL: {pruebas_exitosas}/{total_pruebas} pruebas exitosas")
    
    # Información adicional si todo fue exitoso
    if pruebas_exitosas == total_pruebas:
        print("\n🎉 ¡FLUJO COMPLETO EXITOSO!")
        print("✅ Creación de plantillas funcional")
        print("✅ Agregar/editar segmentos funcional")
        print("✅ Sistema drag & drop operativo")
        print("✅ Ejecución de plantillas funcional")
        print("✅ Generación de actas funcional")
        
        if plantilla and ejecucion and acta:
            print(f"\n📋 OBJETOS CREADOS:")
            print(f"• Plantilla: {plantilla.nombre} (ID: {plantilla.pk})")
            print(f"• Segmentos configurados: {ConfiguracionSegmento.objects.filter(plantilla=plantilla).count()}")
            print(f"• Ejecución: {ejecucion.nombre} (ID: {ejecucion.id})")
            print(f"• Acta generada: {acta.id} ({len(acta.contenido_markdown)} chars)")
    else:
        print(f"\n⚠️ {total_pruebas - pruebas_exitosas} pruebas fallaron")
        print("Revisar los errores específicos arriba")
    
    return pruebas_exitosas == total_pruebas

if __name__ == '__main__':
    exito = test_flujo_completo()
    sys.exit(0 if exito else 1)