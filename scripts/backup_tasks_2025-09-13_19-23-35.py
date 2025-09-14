"""
Tareas Celery para operaciones asíncronas del módulo Generador de Actas
Incluye backup, exportación, reinicio de servicios, etc.
"""
import os
import json
import subprocess
import zipfile
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db import transaction

from .models import (
    OperacionSistema, ProveedorIA, PlantillaActa, ConfiguracionSistema,
    SegmentoPlantilla, ActaGenerada
)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def procesar_acta_completa(self, acta_id: int):
    """
    Flujo completo de procesamiento de acta con IA
    
    Args:
        acta_id: ID del acta a procesar
        
    Returns:
        Diccionario con resultado del procesamiento
    """
    try:
        # Obtener acta y validar estado
        acta = ActaGenerada.objects.select_related(
            'transcripcion', 'plantilla', 'proveedor_ia'
        ).get(id=acta_id)
        
        if not acta.puede_procesar:
            return {
                'success': False,
                'message': f'El acta está en estado {acta.estado} y no puede ser procesada'
            }
        
        # Actualizar estado inicial
        acta.estado = 'procesando'
        acta.task_id_celery = self.request.id
        acta.fecha_procesamiento = timezone.now()
        acta.progreso = 10
        acta.save()
        
        logger.info(f"Iniciando procesamiento del acta {acta.numero_acta}")
        
        # 1. Preparar contexto de la transcripción
        contexto = preparar_contexto_acta(acta)
        if not contexto:
            raise Exception("No se pudo preparar el contexto de la transcripción")
        
        acta.progreso = 20
        acta.save()
        
        # 2. Obtener segmentos ordenados de la plantilla
        segmentos_config = acta.plantilla.configuracionsegmento_set.all().order_by('orden')
        total_segmentos = segmentos_config.count()
        
        if total_segmentos == 0:
            raise Exception("La plantilla no tiene segmentos configurados")
        
        logger.info(f"Procesando {total_segmentos} segmentos para acta {acta.numero_acta}")
        
        # 3. Separar segmentos estáticos y dinámicos
        segmentos_estaticos = []
        segmentos_dinamicos = []
        
        for config in segmentos_config:
            if config.segmento.es_dinamico:
                segmentos_dinamicos.append(config)
            else:
                segmentos_estaticos.append(config)
        
        acta.estado = 'procesando_segmentos'
        acta.progreso = 30
        acta.save()
        
        # 4. Procesar segmentos estáticos
        resultados_estaticos = []
        for config in segmentos_estaticos:
            resultado = procesar_segmento_estatico(config, contexto)
            resultados_estaticos.append(resultado)
        
        # 5. Procesar segmentos dinámicos en paralelo
        resultados_dinamicos = []
        if segmentos_dinamicos:
            # Crear tareas paralelas para segmentos dinámicos
            tareas_paralelas = group([
                procesar_segmento_individual.s(
                    config.id,
                    contexto,
                    acta.proveedor_ia.id
                ) for config in segmentos_dinamicos
            ])
            
            # Ejecutar en paralelo
            resultado_grupo = tareas_paralelas.apply_async()
            resultados_dinamicos = resultado_grupo.get()
        
        acta.progreso = 70
        acta.save()
        
        # 6. Combinar todos los resultados
        todos_resultados = resultados_estaticos + resultados_dinamicos
        todos_resultados.sort(key=lambda x: x['orden'])
        
        # Guardar resultados de segmentos
        segmentos_dict = {}
        for resultado in todos_resultados:
            segmentos_dict[f"segmento_{resultado['segmento_id']}"] = resultado
        
        acta.segmentos_procesados = segmentos_dict
        acta.estado = 'unificando'
        acta.progreso = 80
        acta.save()
        
        # 7. Unificar todos los segmentos
        contenido_unificado = unificar_segmentos(todos_resultados)
        acta.contenido_borrador = contenido_unificado
        acta.save()
        
        # 8. Generar versión final con prompt global
        if acta.plantilla.prompt_global.strip():
            contenido_final = generar_version_final(
                acta.id,
                contenido_unificado,
                contexto
            )
            acta.contenido_final = contenido_final
        else:
            acta.contenido_final = contenido_unificado
        
        # 9. Actualizar estado final
        acta.estado = 'revision'
        acta.progreso = 100
        acta.metricas_procesamiento = {
            'tiempo_procesamiento': (timezone.now() - acta.fecha_procesamiento).total_seconds(),
            'segmentos_procesados': len(todos_resultados),
            'segmentos_dinamicos': len(segmentos_dinamicos),
            'segmentos_estaticos': len(segmentos_estaticos)
        }
        acta.save()
        
        # Agregar al historial
        acta.agregar_historial(
            'procesamiento_completado',
            acta.usuario_creacion,
            {'segmentos': len(todos_resultados)}
        )
        
        logger.info(f"Procesamiento completado para acta {acta.numero_acta}")
        
        return {
            'success': True,
            'acta_id': acta.id,
            'numero_acta': acta.numero_acta,
            'mensaje': 'Acta procesada exitosamente'
        }
        
    except Exception as e:
        logger.error(f"Error procesando acta {acta_id}: {str(e)}")
        
        # Actualizar estado de error
        try:
            acta = ActaGenerada.objects.get(id=acta_id)
            acta.estado = 'error'
            acta.mensajes_error = str(e)
            acta.save()
            
            acta.agregar_historial(
                'error_procesamiento',
                acta.usuario_creacion,
                {'error': str(e)}
            )
        except:
            pass
        
        # Reintentar si aún quedan intentos
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando procesamiento de acta {acta_id} (intento {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        
        return {
            'success': False,
            'acta_id': acta_id,
            'mensaje': f'Error en procesamiento: {str(e)}'
        }


@shared_task(bind=True, max_retries=2)
def procesar_segmento_individual(self, config_id: int, contexto: Dict, proveedor_id: int):
    """
    Procesa un segmento individual con IA
    
    Args:
        config_id: ID de la configuración del segmento
        contexto: Contexto de la reunión
        proveedor_id: ID del proveedor IA
        
    Returns:
        Diccionario con el resultado del procesamiento
    """
    try:
        config = ConfiguracionSegmento.objects.select_related(
            'segmento', 'plantilla'
        ).get(id=config_id)
        
        proveedor = ProveedorIA.objects.get(id=proveedor_id)
        
        logger.info(f"Procesando segmento {config.segmento.nombre} con {proveedor.nombre}")
        
        # Obtener el prompt efectivo
        prompt = config.prompt_efectivo
        if not prompt:
            raise Exception(f"Segmento {config.segmento.nombre} no tiene prompt configurado")
        
        # Preparar contexto específico del segmento
        contexto_segmento = {
            **contexto,
            'parametros_segmento': config.parametros_override or config.segmento.parametros_entrada,
            'categoria_segmento': config.segmento.categoria,
            'tipo_segmento': config.segmento.tipo
        }
        
        # Procesar con IA
        ia_provider = get_ia_provider(proveedor)
        contenido = ia_provider.procesar_prompt(prompt, contexto_segmento)
        
        return {
            'segmento_id': config.segmento.id,
            'nombre': config.segmento.nombre,
            'categoria': config.segmento.categoria,
            'orden': config.orden,
            'tipo': 'dinamico',
            'contenido': contenido,
            'prompt_usado': prompt[:200] + '...' if len(prompt) > 200 else prompt,
            'proveedor': proveedor.nombre,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error procesando segmento {config_id}: {str(e)}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
        
        # Si no se puede reintentar, devolver error
        try:
            config = ConfiguracionSegmento.objects.get(id=config_id)
            return {
                'segmento_id': config.segmento.id,
                'nombre': config.segmento.nombre,
                'categoria': config.segmento.categoria,
                'orden': config.orden,
                'tipo': 'dinamico',
                'contenido': f"ERROR: No se pudo procesar este segmento. {str(e)}",
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }
        except:
            raise e


def procesar_segmento_estatico(config: ConfiguracionSegmento, contexto: Dict) -> Dict:
    """
    Procesa un segmento estático (sin IA)
    
    Args:
        config: Configuración del segmento
        contexto: Contexto de la reunión
        
    Returns:
        Diccionario con el resultado del procesamiento
    """
    try:
        # Los segmentos estáticos pueden usar plantillas simples
        contenido = config.segmento.componentes.get('template', '')
        
        # Reemplazar variables básicas del contexto
        if contenido and contexto:
            variables = {
                'fecha_reunion': contexto.get('fecha_reunion', ''),
                'tipo_reunion': contexto.get('tipo_reunion', ''),
                'ubicacion': contexto.get('ubicacion', ''),
                'duracion': contexto.get('duracion', ''),
            }
            
            for var, valor in variables.items():
                contenido = contenido.replace(f'{{{{{var}}}}}', str(valor))
        
        if not contenido:
            contenido = f"[{config.segmento.nombre}]"
        
        return {
            'segmento_id': config.segmento.id,
            'nombre': config.segmento.nombre,
            'categoria': config.segmento.categoria,
            'orden': config.orden,
            'tipo': 'estatico',
            'contenido': contenido,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error procesando segmento estático {config.segmento.nombre}: {str(e)}")
        return {
            'segmento_id': config.segmento.id,
            'nombre': config.segmento.nombre,
            'categoria': config.segmento.categoria,
            'orden': config.orden,
            'tipo': 'estatico',
            'contenido': f"ERROR: {str(e)}",
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }


def unificar_segmentos(resultados_segmentos: List[Dict]) -> str:
    """
    Unifica todos los segmentos procesados en un documento coherente
    
    Args:
        resultados_segmentos: Lista de resultados de segmentos procesados
        
    Returns:
        Documento unificado como string
    """
    try:
        # Ordenar segmentos por posición
        segmentos_ordenados = sorted(resultados_segmentos, key=lambda x: x['orden'])
        
        documento_partes = []
        
        for segmento in segmentos_ordenados:
            # Agregar título del segmento si es necesario
            if segmento['categoria'] in ['titulo', 'encabezado']:
                documento_partes.append(segmento['contenido'])
            else:
                # Agregar separación entre segmentos
                if documento_partes:
                    documento_partes.append('\n')
                
                documento_partes.append(segmento['contenido'])
        
        return '\n'.join(documento_partes)
        
    except Exception as e:
        logger.error(f"Error unificando segmentos: {str(e)}")
        # Fallback: concatenar todo el contenido
        return '\n\n'.join([s.get('contenido', '') for s in resultados_segmentos])


def generar_version_final(acta_id: int, contenido_borrador: str, contexto: Dict) -> str:
    """
    Genera la versión final del acta aplicando el prompt global
    
    Args:
        acta_id: ID del acta
        contenido_borrador: Borrador unificado
        contexto: Contexto de la reunión
        
    Returns:
        Versión final del acta
    """
    try:
        acta = ActaGenerada.objects.select_related('plantilla', 'proveedor_ia').get(id=acta_id)
        
        if not acta.plantilla.prompt_global.strip():
            return contenido_borrador
        
        ia_provider = get_ia_provider(acta.proveedor_ia)
        
        contexto_final = {
            **contexto,
            'borrador_acta': contenido_borrador,
            'tipo_acta': acta.plantilla.tipo_acta,
            'numero_acta': acta.numero_acta,
            'titulo_acta': acta.titulo,
            'metadata_procesamiento': {
                'fecha_procesamiento': timezone.now().isoformat(),
                'plantilla_usada': acta.plantilla.nombre,
                'proveedor_ia': acta.proveedor_ia.nombre
            }
        }
        
        acta_final = ia_provider.procesar_prompt(
            acta.plantilla.prompt_global,
            contexto_final
        )
        
        return acta_final
        
    except Exception as e:
        logger.error(f"Error generando versión final para acta {acta_id}: {str(e)}")
        return contenido_borrador  # Fallback al borrador


def preparar_contexto_acta(acta: ActaGenerada) -> Dict[str, Any]:
    """
    Prepara el contexto completo para procesamiento del acta
    
    Args:
        acta: Instancia del acta a procesar
        
    Returns:
        Diccionario con contexto completo
    """
    try:
        transcripcion = acta.transcripcion
        audio = transcripcion.procesamiento_audio
        
        # Validar que la transcripción tenga datos
        if not transcripcion.conversacion_json:
            raise Exception("La transcripción no tiene datos de conversación")
        
        conversacion = transcripcion.conversacion_json.get('conversacion', [])
        if not conversacion:
            raise Exception("La transcripción no tiene segmentos de conversación")
        
        # Preparar mapeo de hablantes
        mapeo_hablantes = transcripcion.conversacion_json.get('cabecera', {}).get('mapeo_hablantes', {})
        
        # Preparar participantes
        participantes = []
        if audio.participantes_detallados:
            participantes = audio.participantes_detallados
        elif mapeo_hablantes:
            participantes = [{'nombre': nombre, 'rol': 'Participante', 'hablante_id': hid} 
                           for hid, nombre in mapeo_hablantes.items()]
        
        contexto = {
            # Datos de la transcripción
            'conversacion': conversacion,
            'hablantes': mapeo_hablantes,
            'resumen_conversacion': transcripcion.conversacion_json.get('metadata', {}).get('resumen', ''),
            
            # Datos del audio
            'metadata_audio': audio.metadatos_procesamiento,
            'duracion_segundos': audio.duracion_segundos,
            'duracion_formateada': GeneradorActasService.formatear_duracion(audio.duracion_segundos),
            
            # Datos de la reunión
            'tipo_reunion': audio.tipo_reunion.nombre if audio.tipo_reunion else 'Reunión General',
            'participantes': participantes,
            'ubicacion': audio.ubicacion or 'No especificada',
            'fecha_reunion': acta.fecha_sesion.strftime('%d de %B de %Y') if acta.fecha_sesion else '',
            'hora_reunion': acta.fecha_sesion.strftime('%H:%M') if acta.fecha_sesion else '',
            
            # Metadatos del acta
            'numero_acta': acta.numero_acta,
            'titulo_acta': acta.titulo,
            'tipo_acta': acta.plantilla.get_tipo_acta_display(),
            
            # Información adicional
            'fecha_procesamiento': timezone.now().strftime('%d de %B de %Y'),
            'usuario_creacion': acta.usuario_creacion.get_full_name() or acta.usuario_creacion.username
        }
        
        return contexto
        
    except Exception as e:
        logger.error(f"Error preparando contexto para acta {acta.numero_acta}: {str(e)}")
        raise Exception(f"No se pudo preparar el contexto: {str(e)}")


@shared_task
def limpiar_actas_error():
    """
    Tarea periódica para limpiar actas con errores antiguas
    """
    try:
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=7)
        
        actas_error = ActaGenerada.objects.filter(
            estado='error',
            fecha_actualizacion__lt=fecha_limite
        )
        
        count = actas_error.count()
        if count > 0:
            logger.info(f"Eliminando {count} actas con error de más de 7 días")
            actas_error.delete()
        
        return f"Eliminadas {count} actas con error"
        
    except Exception as e:
        logger.error(f"Error limpiando actas: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generar_estadisticas_procesamiento():
    """
    Genera estadísticas de procesamiento de actas
    """
    try:
        from django.db.models import Count, Avg
        
        stats = {}
        
        # Estadísticas por estado
        stats['por_estado'] = dict(
            ActaGenerada.objects.values('estado').annotate(
                count=Count('id')
            ).values_list('estado', 'count')
        )
        
        # Estadísticas por proveedor IA
        stats['por_proveedor'] = dict(
            ActaGenerada.objects.select_related('proveedor_ia').values(
                'proveedor_ia__nombre'
            ).annotate(
                count=Count('id')
            ).values_list('proveedor_ia__nombre', 'count')
        )
        
        # Promedio de tiempo de procesamiento
        actas_completadas = ActaGenerada.objects.filter(
            estado__in=['revision', 'aprobado', 'publicado'],
            metricas_procesamiento__isnull=False
        )
        
        if actas_completadas.exists():
            tiempos = [
                acta.metricas_procesamiento.get('tiempo_procesamiento', 0)
                for acta in actas_completadas
                if acta.metricas_procesamiento.get('tiempo_procesamiento')
            ]
            
            if tiempos:
                stats['tiempo_promedio'] = sum(tiempos) / len(tiempos)
                stats['tiempo_min'] = min(tiempos)
                stats['tiempo_max'] = max(tiempos)
        
        logger.info(f"Estadísticas generadas: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error generando estadísticas: {str(e)}")
        return {'error': str(e)}