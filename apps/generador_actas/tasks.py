"""
Tareas Celery para operaciones asíncronas del módulo Generador de Actas
Incluye backup, exportación, procesamiento de segmentos, etc.
"""
import os
import json
import subprocess
import zipfile
import tempfile
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from celery import shared_task
from django.conf import settings
from django.core.management import call_command
from django.core.files.base import ContentFile
from django.utils import timezone
from django.template.loader import render_to_string
from django.db import transaction

from .models import (
    OperacionSistema, ProveedorIA, PlantillaActa, ConfiguracionSistema,
    SegmentoPlantilla, ActaGenerada
)
from .services import GeneradorActasService, PlantillasService


@shared_task(bind=True, max_retries=2)
def procesar_segmento_dinamico(self, segmento_id, contexto, opciones=None):
    """
    Procesa un segmento dinámico usando IA de manera asíncrona
    """
    if opciones is None:
        opciones = {}
    
    try:
        # Obtener el segmento
        segmento = SegmentoPlantilla.objects.get(id=segmento_id)
        
        if not segmento.es_dinamico:
            return {
                'exito': False,
                'error': 'El segmento no es dinámico',
                'segmento_id': segmento_id
            }
        
        if not segmento.esta_configurado:
            return {
                'exito': False,
                'error': 'El segmento no está correctamente configurado',
                'segmento_id': segmento_id
            }
        
        tiempo_inicio = time.time()
        
        # Generar prompt completo
        prompt_completo = segmento.generar_prompt_completo(contexto)
        
        # Procesar con el proveedor IA
        proveedor = segmento.proveedor_ia
        config = proveedor.obtener_configuracion_completa()
        
        # Simular llamada a IA (reemplazar con llamada real según proveedor)
        resultado = _simular_llamada_ia(prompt_completo, config, segmento)
        
        tiempo_fin = time.time()
        tiempo_procesamiento = tiempo_fin - tiempo_inicio
        
        # Validar resultado
        errores_validacion = segmento.validar_resultado(resultado)
        
        if errores_validacion:
            segmento.actualizar_metricas_uso(
                tiempo_procesamiento=tiempo_procesamiento,
                exito=False,
                error=f"Errores de validación: {'; '.join(errores_validacion)}"
            )
            return {
                'exito': False,
                'error': f"Errores de validación: {'; '.join(errores_validacion)}",
                'resultado_parcial': resultado,
                'tiempo_procesamiento': tiempo_procesamiento,
                'segmento_id': segmento_id
            }
        
        # Actualizar métricas
        segmento.actualizar_metricas_uso(
            tiempo_procesamiento=tiempo_procesamiento,
            exito=True
        )
        
        return {
            'exito': True,
            'resultado': resultado,
            'tiempo_procesamiento': tiempo_procesamiento,
            'segmento_id': segmento_id,
            'prompt_usado': prompt_completo[:500] + "..." if len(prompt_completo) > 500 else prompt_completo
        }
    
    except SegmentoPlantilla.DoesNotExist:
        return {
            'exito': False,
            'error': f'Segmento con ID {segmento_id} no encontrado',
            'segmento_id': segmento_id
        }
    except Exception as e:
        # Actualizar métricas de error si el segmento existe
        try:
            segmento = SegmentoPlantilla.objects.get(id=segmento_id)
            segmento.actualizar_metricas_uso(exito=False, error=str(e))
        except:
            pass
        
        return {
            'exito': False,
            'error': str(e),
            'segmento_id': segmento_id
        }


def _simular_llamada_ia(prompt, config, segmento):
    """
    Simulación de llamada a IA - reemplazar con integración real
    """
    # Simular tiempo de procesamiento
    time.sleep(1)
    
    # Simular respuesta basada en el tipo de segmento
    if 'participantes' in segmento.categoria.lower():
        return """
        **PARTICIPANTES**
        
        1. Dr. Juan Pérez González - Alcalde
        2. Ing. María García López - Secretaria Municipal  
        3. Lic. Carlos Ruiz Mendoza - Director de Planificación
        4. Eco. Ana Martínez Silva - Directora Financiera
        
        **QUÓRUM:** Se verifica la asistencia del 80% de los miembros convocados.
        """
    
    elif 'resumen' in segmento.categoria.lower():
        return """
        En la presente sesión se trataron los siguientes temas principales:
        
        1. **Aprobación del Presupuesto Municipal 2025**: Se presentó y aprobó por unanimidad el presupuesto para el próximo período fiscal.
        
        2. **Proyecto de Mejoramiento Vial**: Se discutió la propuesta para el mejoramiento de las vías del sector norte de la ciudad.
        
        3. **Convenio Interinstitucional**: Se autorizó la suscripción de convenio con la Universidad Local para proyectos de investigación.
        
        Las decisiones adoptadas reflejan el compromiso con el desarrollo sostenible del municipio.
        """
    
    elif 'titulo' in segmento.categoria.lower() or 'encabezado' in segmento.categoria.lower():
        return f"""
        ACTA DE SESIÓN ORDINARIA N° 001-2025
        GOBIERNO AUTÓNOMO DESCENTRALIZADO MUNICIPAL DE PASTAZA
        """
    
    else:
        return f"""
        Contenido generado para segmento: {segmento.nombre}
        
        Este es un resultado de ejemplo del procesamiento con IA.
        El contenido real dependería de la configuración específica del prompt
        y los datos de contexto proporcionados.
        
        Categoría: {segmento.get_categoria_display()}
        Tipo: {segmento.get_tipo_display()}
        """


@shared_task(bind=True)
def probar_segmento_masivo(self, segmento_ids, contexto_prueba):
    """
    Prueba múltiples segmentos de manera asíncrona
    """
    resultados = []
    
    for segmento_id in segmento_ids:
        try:
            resultado = procesar_segmento_dinamico.apply_async(
                args=[segmento_id, contexto_prueba, {'es_prueba': True}]
            ).get(timeout=60)
            
            resultados.append({
                'segmento_id': segmento_id,
                'resultado': resultado
            })
        except Exception as e:
            resultados.append({
                'segmento_id': segmento_id,
                'resultado': {
                    'exito': False,
                    'error': str(e)
                }
            })
    
    return {
        'total_procesados': len(segmento_ids),
        'resultados': resultados
    }


@shared_task(bind=True, max_retries=2)
def crear_backup_sistema(self, operacion_id, incluir_media=True, incluir_logs=False):
    """
    Crea un backup completo del sistema incluyendo BD y archivos
    """
    try:
        operacion = OperacionSistema.objects.get(id=operacion_id)
        operacion.estado = 'running'
        operacion.task_id = self.request.id
        operacion.save()
        
        operacion.agregar_log('info', 'Iniciando backup del sistema')
        operacion.actualizar_progreso(10, 'Preparando directorio de backup')
        
        # Crear directorio temporal
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'backup_actas_{timestamp}'
        temp_dir = Path(tempfile.mkdtemp())
        backup_dir = temp_dir / backup_name
        backup_dir.mkdir()
        
        # 1. Backup de base de datos
        operacion.actualizar_progreso(20, 'Creando backup de base de datos')
        db_backup_path = backup_dir / f'database_{timestamp}.sql'
        
        # Comando para PostgreSQL
        db_settings = settings.DATABASES['default']
        pg_dump_cmd = [
            'pg_dump',
            '-h', db_settings['HOST'],
            '-p', str(db_settings['PORT']),
            '-U', db_settings['USER'],
            '-d', db_settings['NAME'],
            '-f', str(db_backup_path),
            '--verbose'
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        result = subprocess.run(pg_dump_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Error en pg_dump: {result.stderr}")
        
        operacion.agregar_log('info', f'Backup de BD creado: {db_backup_path}')
        
        # 2. Backup de archivos media
        if incluir_media:
            operacion.actualizar_progreso(40, 'Copiando archivos media')
            media_backup_dir = backup_dir / 'media'
            if os.path.exists(settings.MEDIA_ROOT):
                shutil.copytree(settings.MEDIA_ROOT, media_backup_dir)
                operacion.agregar_log('info', f'Archivos media copiados: {media_backup_dir}')
        
        # 3. Backup de configuraciones
        operacion.actualizar_progreso(60, 'Exportando configuraciones del sistema')
        config_backup = backup_dir / 'configuraciones.json'
        
        configuraciones = {}
        for config in ConfiguracionSistema.objects.all():
            configuraciones[config.clave] = {
                'nombre': config.nombre,
                'valor': config.valor,
                'valor_por_defecto': config.valor_por_defecto,
                'tipo_dato': config.tipo_dato,
                'descripcion': config.descripcion,
                'fecha_modificacion': config.fecha_modificacion.isoformat()
            }
        
        with open(config_backup, 'w', encoding='utf-8') as f:
            json.dump(configuraciones, f, indent=2, ensure_ascii=False)
        
        # 6. Crear archivo ZIP
        operacion.actualizar_progreso(90, 'Comprimiendo backup')
        zip_path = temp_dir / f'{backup_name}.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(backup_dir)
                    zipf.write(file_path, arcname)
        
        # 7. Guardar archivo en modelo
        with open(zip_path, 'rb') as f:
            file_content = ContentFile(f.read(), name=f'{backup_name}.zip')
            operacion.archivo_resultado.save(f'{backup_name}.zip', file_content)
        
        # Limpiar archivos temporales
        shutil.rmtree(temp_dir)
        
        # Resultado final
        resultado = {
            'archivo_backup': operacion.archivo_resultado.name,
            'tamaño_mb': round(operacion.archivo_resultado.size / (1024*1024), 2),
            'incluye_media': incluir_media,
            'incluye_logs': incluir_logs
        }
        
        operacion.marcar_completado(resultado)
        operacion.actualizar_progreso(100, 'Backup completado exitosamente')
        operacion.agregar_log('info', f'Backup creado exitosamente: {backup_name}.zip')
        
        return resultado
        
    except Exception as e:
        operacion.marcar_fallido(str(e))
        operacion.agregar_log('error', f'Error creando backup: {str(e)}')
        raise


@shared_task(bind=True, max_retries=1)
def exportar_configuraciones(self, operacion_id, formato='json', incluir_sensibles=False):
    """
    Exporta todas las configuraciones del sistema
    """
    try:
        operacion = OperacionSistema.objects.get(id=operacion_id)
        operacion.estado = 'running'
        operacion.task_id = self.request.id
        operacion.save()
        
        operacion.agregar_log('info', f'Iniciando exportación en formato {formato}')
        operacion.actualizar_progreso(20, 'Recopilando configuraciones')
        
        # Recopilar todas las configuraciones
        configuraciones = {}
        
        # 1. Configuraciones del sistema
        for config in ConfiguracionSistema.objects.all():
            if not incluir_sensibles and 'password' in config.clave.lower():
                continue
                
            configuraciones[config.clave] = {
                'nombre': config.nombre,
                'descripcion': config.descripcion,
                'valor': config.valor,
                'valor_por_defecto': config.valor_por_defecto,
                'tipo_dato': config.tipo_dato,
                'es_requerido': config.es_requerido,
                'es_publico': config.es_publico,
                'version': config.version,
                'fecha_modificacion': config.fecha_modificacion.isoformat()
            }
        
        operacion.actualizar_progreso(40, 'Recopilando proveedores IA')
        
        # 2. Proveedores IA
        proveedores = {}
        for proveedor in ProveedorIA.objects.all():
            proveedor_data = {
                'nombre': proveedor.nombre,
                'tipo': proveedor.tipo,
                'modelo': proveedor.modelo,
                'temperatura': float(proveedor.temperatura),
                'max_tokens': proveedor.max_tokens,
                'timeout': proveedor.timeout,
                'configuracion_adicional': proveedor.configuracion_adicional,
                'activo': proveedor.activo,
                'costo_por_1k_tokens': float(proveedor.costo_por_1k_tokens)
            }
            
            # Solo incluir API key si se especifica
            if incluir_sensibles:
                proveedor_data['api_key'] = proveedor.api_key
                proveedor_data['api_url'] = proveedor.api_url
            
            proveedores[proveedor.nombre] = proveedor_data
        
        operacion.actualizar_progreso(60, 'Recopilando plantillas')
        
        # 3. Plantillas con sus segmentos
        plantillas = {}
        for plantilla in PlantillaActa.objects.select_related().prefetch_related('configuracionsegmento_set'):
            segmentos_config = {}
            for config_seg in plantilla.configuracionsegmento_set.all():
                segmentos_config[config_seg.segmento.nombre] = {
                    'orden': config_seg.orden,
                    'activo': config_seg.activo,
                    'configuracion_personalizada': config_seg.configuracion_personalizada
                }
            
            plantillas[plantilla.nombre] = {
                'descripcion': plantilla.descripcion,
                'tipo_reunion': plantilla.tipo_reunion,
                'formato_salida': plantilla.formato_salida,
                'configuracion_global': plantilla.configuracion_global,
                'activo': plantilla.activo,
                'segmentos': segmentos_config
            }
        
        operacion.actualizar_progreso(80, 'Generando archivo de exportación')
        
        # Estructura final
        export_data = {
            'metadatos': {
                'fecha_exportacion': timezone.now().isoformat(),
                'version_sistema': '1.0.0',
                'incluye_datos_sensibles': incluir_sensibles,
                'formato': formato
            },
            'configuraciones_sistema': configuraciones,
            'proveedores_ia': proveedores,
            'plantillas': plantillas
        }
        
        # Generar archivo según formato
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if formato == 'json':
            filename = f'configuraciones_actas_{timestamp}.json'
            content = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
            content_type = 'application/json'
        
        elif formato == 'yaml':
            import yaml
            filename = f'configuraciones_actas_{timestamp}.yaml'
            content = yaml.dump(export_data, default_flow_style=False, allow_unicode=True)
            content_type = 'application/x-yaml'
        
        else:
            raise ValueError(f"Formato no soportado: {formato}")
        
        # Guardar archivo
        file_content = ContentFile(content.encode('utf-8'), name=filename)
        operacion.archivo_resultado.save(filename, file_content)
        
        resultado = {
            'archivo': filename,
            'formato': formato,
            'tamaño_kb': round(len(content.encode('utf-8')) / 1024, 2),
            'elementos_exportados': {
                'configuraciones': len(configuraciones),
                'proveedores_ia': len(proveedores),
                'plantillas': len(plantillas)
            },
            'incluye_sensibles': incluir_sensibles
        }
        
        operacion.marcar_completado(resultado)
        operacion.actualizar_progreso(100, 'Exportación completada')
        operacion.agregar_log('info', f'Configuraciones exportadas: {filename}')
        
        return resultado
        
    except Exception as e:
        operacion.marcar_fallido(str(e))
        operacion.agregar_log('error', f'Error exportando configuraciones: {str(e)}')
        raise


@shared_task(bind=True, max_retries=1)
def reiniciar_servicios_sistema(self, operacion_id, servicios=None):
    """
    Reinicia servicios del sistema de forma segura
    """
    try:
        operacion = OperacionSistema.objects.get(id=operacion_id)
        operacion.estado = 'running'
        operacion.task_id = self.request.id
        operacion.save()
        
        if servicios is None:
            servicios = ['celery', 'redis']
        
        operacion.agregar_log('info', f'Iniciando reinicio de servicios: {servicios}')
        total_servicios = len(servicios)
        servicios_reiniciados = []
        errores = []
        
        for i, servicio in enumerate(servicios):
            try:
                progreso = int(20 + (i / total_servicios) * 60)
                operacion.actualizar_progreso(progreso, f'Reiniciando {servicio}')
                
                if servicio == 'celery':
                    # Reiniciar worker de Celery
                    result = subprocess.run([
                        'docker', 'restart', 'actas_celery_worker'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        servicios_reiniciados.append(servicio)
                        operacion.agregar_log('info', f'Servicio {servicio} reiniciado exitosamente')
                    else:
                        errores.append(f'{servicio}: {result.stderr}')
                
                elif servicio == 'redis':
                    # Reiniciar Redis
                    result = subprocess.run([
                        'docker', 'restart', 'actas_redis'
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        servicios_reiniciados.append(servicio)
                        operacion.agregar_log('info', f'Servicio {servicio} reiniciado exitosamente')
                    else:
                        errores.append(f'{servicio}: {result.stderr}')
                
                elif servicio == 'web':
                    # Reiniciar aplicación web (requiere cuidado especial)
                    operacion.agregar_log('warning', 'Reinicio de servicio web no implementado por seguridad')
                    errores.append('web: Reinicio no permitido por seguridad')
                
            except subprocess.TimeoutExpired:
                errores.append(f'{servicio}: Timeout al reiniciar')
            except Exception as e:
                errores.append(f'{servicio}: {str(e)}')
        
        operacion.actualizar_progreso(90, 'Verificando estado de servicios')
        
        # Verificar estado final
        estado_servicios = {}
        for servicio in servicios:
            try:
                if servicio in ['celery', 'redis']:
                    container_name = f'actas_{servicio}_worker' if servicio == 'celery' else f'actas_{servicio}'
                    result = subprocess.run([
                        'docker', 'ps', '--filter', f'name={container_name}', '--format', 'table {{.Status}}'
                    ], capture_output=True, text=True)
                    
                    if 'Up' in result.stdout:
                        estado_servicios[servicio] = 'activo'
                    else:
                        estado_servicios[servicio] = 'inactivo'
                        
            except Exception as e:
                estado_servicios[servicio] = f'error: {str(e)}'
        
        resultado = {
            'servicios_solicitados': servicios,
            'servicios_reiniciados': servicios_reiniciados,
            'errores': errores,
            'estado_final': estado_servicios,
            'exito_parcial': len(servicios_reiniciados) > 0,
            'exito_total': len(errores) == 0
        }
        
        if errores:
            operacion.estado = 'completed'  # Completado con errores
            operacion.mensaje_estado = f'Reiniciado con errores: {len(errores)} servicios fallaron'
        else:
            operacion.marcar_completado(resultado)
        
        operacion.actualizar_progreso(100, 'Reinicio de servicios completado')
        operacion.agregar_log('info', f'Servicios reiniciados: {servicios_reiniciados}')
        
        if errores:
            for error in errores:
                operacion.agregar_log('error', f'Error: {error}')
        
        return resultado
        
    except Exception as e:
        operacion.marcar_fallido(str(e))
        operacion.agregar_log('error', f'Error reiniciando servicios: {str(e)}')
        raise
@shared_task(bind=True, max_retries=1)
def probar_proveedores_ia(self, operacion_id, proveedor_ids=None):
    """
    Prueba la conectividad y funcionalidad de proveedores IA
    """
    try:
        operacion = OperacionSistema.objects.get(id=operacion_id)
        operacion.estado = 'running'
        operacion.task_id = self.request.id
        operacion.save()
        
        # Obtener proveedores a probar
        if proveedor_ids:
            proveedores = ProveedorIA.objects.filter(id__in=proveedor_ids, activo=True)
        else:
            proveedores = ProveedorIA.objects.filter(activo=True)
        
        operacion.agregar_log('info', f'Iniciando prueba de {proveedores.count()} proveedores IA')
        
        resultados = {}
        total_proveedores = proveedores.count()
        
        # Prompt de prueba estándar
        prompt_prueba = "Responde brevemente: ¿Cuál es la capital de Ecuador?"
        respuesta_esperada_keywords = ['quito', 'ecuador']
        
        for i, proveedor in enumerate(proveedores):
            try:
                progreso = int(20 + (i / total_proveedores) * 70)
                operacion.actualizar_progreso(progreso, f'Probando {proveedor.nombre}')
                
                tiempo_inicio = timezone.now()
                
                # Simulación de prueba (implementar clientes reales después)
                resultado_prueba = {
                    'exito': True,
                    'respuesta': 'Quito es la capital de Ecuador.',
                    'error': None
                }
                
                tiempo_fin = timezone.now()
                tiempo_respuesta = (tiempo_fin - tiempo_inicio).total_seconds()
                
                # Validar respuesta
                if resultado_prueba['exito'] and resultado_prueba['respuesta']:
                    respuesta_lower = resultado_prueba['respuesta'].lower()
                    respuesta_valida = any(keyword in respuesta_lower for keyword in respuesta_esperada_keywords)
                else:
                    respuesta_valida = False
                
                resultados[proveedor.nombre] = {
                    'id': proveedor.id,
                    'tipo': proveedor.tipo,
                    'modelo': proveedor.modelo,
                    'exito_conexion': resultado_prueba['exito'],
                    'respuesta_valida': respuesta_valida,
                    'tiempo_respuesta_segundos': tiempo_respuesta,
                    'respuesta': resultado_prueba['respuesta'][:200] if resultado_prueba['respuesta'] else None,
                    'error': resultado_prueba.get('error', None),
                    'timestamp': tiempo_inicio.isoformat()
                }
                
                if resultado_prueba['exito']:
                    operacion.agregar_log('info', f'{proveedor.nombre}: Conexión exitosa ({tiempo_respuesta:.2f}s)')
                else:
                    operacion.agregar_log('warning', f'{proveedor.nombre}: Error - {resultado_prueba.get("error", "Error desconocido")}')
                
            except Exception as e:
                resultados[proveedor.nombre] = {
                    'id': proveedor.id,
                    'tipo': proveedor.tipo,
                    'modelo': proveedor.modelo,
                    'exito_conexion': False,
                    'respuesta_valida': False,
                    'tiempo_respuesta_segundos': None,
                    'respuesta': None,
                    'error': str(e),
                    'timestamp': timezone.now().isoformat()
                }
                operacion.agregar_log('error', f'{proveedor.nombre}: Excepción - {str(e)}')
        
        # Estadísticas finales
        total_probados = len(resultados)
        exitosos = sum(1 for r in resultados.values() if r['exito_conexion'])
        respuestas_validas = sum(1 for r in resultados.values() if r['respuesta_valida'])
        
        resultado_final = {
            'total_proveedores_probados': total_probados,
            'conexiones_exitosas': exitosos,
            'respuestas_validas': respuestas_validas,
            'tasa_exito_conexion': round((exitosos / total_probados) * 100, 2) if total_probados > 0 else 0,
            'tasa_respuestas_validas': round((respuestas_validas / total_probados) * 100, 2) if total_probados > 0 else 0,
            'resultados_detallados': resultados,
            'prompt_prueba': prompt_prueba
        }
        
        operacion.marcar_completado(resultado_final)
        operacion.actualizar_progreso(100, f'Pruebas completadas: {exitosos}/{total_probados} exitosos')
        operacion.agregar_log('info', f'Pruebas finalizadas: {exitosos}/{total_probados} conexiones exitosas')
        
        return resultado_final
        
    except Exception as e:
        operacion.marcar_fallido(str(e))
        operacion.agregar_log('error', f'Error probando proveedores IA: {str(e)}')
        raise


@shared_task(bind=True, max_retries=2)
def procesar_prueba_ia_task(self, proveedor_id: int, prompt_prueba: str, incluir_contexto: bool = False, task_uuid: str = None):
    """
    Tarea Celery para procesar pruebas de IA en segundo plano con logging detallado
    
    Args:
        proveedor_id: ID del proveedor de IA a probar
        prompt_prueba: Texto del prompt a enviar
        incluir_contexto: Si incluir contexto adicional
        task_uuid: UUID único para tracking del progreso
    
    Returns:
        dict: Resultado de la prueba con métricas y respuesta
    """
    import time
    import logging
    from django.core.cache import cache
    
    logger = logging.getLogger(__name__)
    
    if not task_uuid:
        task_uuid = self.request.id
    
    # Actualizar progreso inicial
    cache_key = f"ia_test_progress_{task_uuid}"
    
    def actualizar_progreso(paso: str, detalle: str, porcentaje: int = 0):
        """Helper para actualizar el progreso en cache"""
        progreso = {
            'paso': paso,
            'detalle': detalle,
            'porcentaje': porcentaje,
            'timestamp': timezone.now().isoformat(),
            'task_id': task_uuid
        }
        cache.set(cache_key, progreso, timeout=300)  # 5 minutos
        logger.info(f"[{task_uuid}] {paso}: {detalle}")
        return progreso
    
    try:
        actualizar_progreso("INICIANDO", "Preparando prueba de IA...", 10)
        
        # Obtener proveedor
        actualizar_progreso("VALIDANDO", "Obteniendo información del proveedor...", 20)
        try:
            proveedor = ProveedorIA.objects.get(id=proveedor_id, activo=True)
        except ProveedorIA.DoesNotExist:
            error_msg = f"Proveedor con ID {proveedor_id} no encontrado o inactivo"
            actualizar_progreso("ERROR", error_msg, 100)
            return {
                'success': False,
                'error': error_msg,
                'proveedor_id': proveedor_id,
                'task_id': task_uuid
            }
        
        actualizar_progreso("CONFIGURANDO", f"Configurando conexión con {proveedor.nombre}...", 30)
        
        # Obtener el handler del proveedor
        from .ia_providers import get_ia_provider
        handler = get_ia_provider(proveedor)
        
        if not handler:
            error_msg = f"Handler no encontrado para el tipo: {proveedor.tipo}"
            actualizar_progreso("ERROR", error_msg, 100)
            return {
                'success': False,
                'error': error_msg,
                'proveedor': {
                    'id': proveedor.id,
                    'nombre': proveedor.nombre,
                    'tipo': proveedor.tipo
                },
                'task_id': task_uuid
            }
        
        # Preparar prompt con contexto si se solicita
        prompt_final = prompt_prueba
        if incluir_contexto:
            actualizar_progreso("PREPARANDO", "Agregando contexto adicional al prompt...", 40)
            contexto_adicional = {
                'fecha_prueba': timezone.now().isoformat(),
                'proveedor_probado': proveedor.nombre,
                'tipo_prueba': 'automatizada',
                'contexto_municipal': 'Municipio de Pastaza, Ecuador'
            }
            prompt_final = f"""Contexto de prueba: {json.dumps(contexto_adicional, indent=2)}

Prompt de prueba: {prompt_prueba}

Por favor responde considerando este contexto municipal."""
        
        actualizar_progreso("CONECTANDO", f"Estableciendo conexión con {proveedor.tipo}...", 50)
        
        # Logging detallado de parámetros
        parametros_envio = {
            'proveedor_id': proveedor.id,
            'proveedor_nombre': proveedor.nombre,
            'proveedor_tipo': proveedor.tipo,
            'modelo': proveedor.modelo,
            'url_api': proveedor.api_url or 'Default',
            'prompt_length': len(prompt_final),
            'incluir_contexto': incluir_contexto,
            'timestamp_envio': timezone.now().isoformat()
        }
        
        logger.info(f"[{task_uuid}] PARÁMETROS DE ENVÍO: {json.dumps(parametros_envio, indent=2)}")
        actualizar_progreso("ENVIANDO", f"Enviando prompt ({len(prompt_final)} caracteres)...", 70)
        
        # Medir tiempo de inicio
        tiempo_inicio = time.time()
        
        # Realizar la prueba real de conexión
        resultado_prueba = handler.test_conexion()
        
        # Si la conexión es exitosa Y tenemos un prompt personalizado, ejecutarlo
        prueba_prompt_resultado = {}
        if resultado_prueba.get('exito', False) and prompt_final.strip():
            actualizar_progreso("ENVIANDO_PROMPT", f"Enviando prompt personalizado a {proveedor.tipo}...", 85)
            try:
                # Ejecutar el prompt personalizado directamente
                if hasattr(handler, 'generar_respuesta'):
                    respuesta_ia = handler.generar_respuesta(prompt_final)
                    prueba_prompt_resultado = {
                        'exito': True,
                        'respuesta': respuesta_ia.get('contenido', respuesta_ia.get('response', str(respuesta_ia))),
                        'tokens': respuesta_ia.get('tokens_usados'),
                        'modelo_usado': respuesta_ia.get('modelo_usado', proveedor.modelo),
                        'tiempo_respuesta': respuesta_ia.get('tiempo_respuesta')
                    }
                else:
                    # Fallback para proveedores sin método generar_respuesta
                    prueba_prompt_resultado = {
                        'exito': False,
                        'error': f'Proveedor {proveedor.tipo} no soporta ejecución de prompts personalizados'
                    }
            except Exception as e:
                prueba_prompt_resultado = {
                    'exito': False,
                    'error': f'Error ejecutando prompt personalizado: {str(e)}'
                }
        elif prompt_final.strip():
            prueba_prompt_resultado = {
                'exito': False,
                'error': 'Conexión falló, no se pudo ejecutar el prompt'
            }
        
        # Medir tiempo final
        tiempo_total = round(time.time() - tiempo_inicio, 2)
        
        actualizar_progreso("PROCESANDO", "Procesando respuesta de la IA...", 90)
        
        # Preparar resultado completo
        resultado_completo = {
            'success': True,
            'proveedor': {
                'id': proveedor.id,
                'nombre': proveedor.nombre,
                'tipo': proveedor.tipo,
                'modelo': proveedor.modelo,
                'api_url': proveedor.api_url
            },
            'parametros_envio': parametros_envio,
            'tiempo_respuesta': tiempo_total,
            'timestamp_completado': timezone.now().isoformat(),
            'task_id': task_uuid,
            'incluir_contexto': incluir_contexto,
            'prompt_enviado': prompt_final,
            'prueba_prompt': prueba_prompt_resultado,  # Usar el resultado real del prompt
            'mensaje': resultado_prueba.get('mensaje', 'Prueba completada'),
            'metricas': {
                'tiempo_respuesta_segundos': tiempo_total,
                'caracteres_prompt': len(prompt_final),
                'exito_conexion': resultado_prueba.get('exito', False),
                'tokens_estimados': prueba_prompt_resultado.get('tokens'),
                'modelo_usado': prueba_prompt_resultado.get('modelo_usado', proveedor.modelo),
                'prompt_ejecutado': bool(prompt_final.strip() and prueba_prompt_resultado.get('exito'))
            }
        }
        
        # Logging detallado del resultado
        logger.info(f"[{task_uuid}] RESULTADO COMPLETO: {json.dumps(resultado_completo, indent=2, default=str)}")
        
        actualizar_progreso("COMPLETADO", f"Prueba exitosa en {tiempo_total}s", 100)
        
        return resultado_completo
        
    except Exception as e:
        error_msg = f"Error durante la prueba: {str(e)}"
        logger.error(f"[{task_uuid}] ERROR: {error_msg}", exc_info=True)
        
        actualizar_progreso("ERROR", error_msg, 100)
        
        return {
            'success': False,
            'error': error_msg,
            'proveedor_id': proveedor_id,
            'task_id': task_uuid,
            'timestamp_error': timezone.now().isoformat()
        }


def obtener_progreso_tarea(task_uuid: str):
    """
    Obtener el progreso actual de una tarea
    
    Args:
        task_uuid: UUID de la tarea
    
    Returns:
        dict: Información del progreso o None si no existe
    """
    from django.core.cache import cache
    cache_key = f"ia_test_progress_{task_uuid}"
    return cache.get(cache_key)


@shared_task(bind=True)
def procesar_generacion_acta_task(self, proveedor_id: int, contenido_reunion: str, configuracion: dict = None):
    """
    Tarea Celery para generar actas usando IA (para uso futuro)
    
    Args:
        proveedor_id: ID del proveedor de IA
        contenido_reunion: Transcripción o contenido de la reunión
        configuracion: Configuración específica para la generación
    
    Returns:
        dict: Acta generada y métricas
    """
    # TODO: Implementar para módulos futuros de generación de actas
    pass


@shared_task(bind=True)
def procesar_resumen_acta_task(self, proveedor_id: int, acta_contenido: str, tipo_resumen: str = "ejecutivo"):
    """
    Tarea Celery para generar resúmenes de actas (para uso futuro)
    
    Args:
        proveedor_id: ID del proveedor de IA
        acta_contenido: Contenido completo del acta
        tipo_resumen: Tipo de resumen a generar
    
    Returns:
        dict: Resumen generado y métricas
    """
    # TODO: Implementar para módulos futuros de resúmenes
    pass


# ==================== TAREAS DE SEGMENTOS ====================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def procesar_segmento_dinamico(self, segmento_id: int, datos_contexto: dict, 
                              configuracion: dict = None) -> dict:
    """
    Procesa un segmento dinámico usando IA de forma asíncrona
    
    Args:
        segmento_id: ID del segmento a procesar
        datos_contexto: Datos de contexto para el procesamiento
        configuracion: Configuración adicional para el procesamiento
        
    Returns:
        Dict con el resultado del procesamiento
    """
    import time
    import logging
    from apps.generador_actas.services import GeneradorActasService
    
    logger = logging.getLogger(__name__)
    tiempo_inicio = time.time()
    
    try:
        # Obtener el segmento
        segmento = SegmentoPlantilla.objects.select_related('proveedor_ia').get(
            id=segmento_id
        )
        
        if not segmento.activo:
            raise Exception(f"El segmento {segmento.nombre} está inactivo")
        
        if not segmento.es_dinamico:
            raise Exception(f"El segmento {segmento.nombre} no es dinámico")
        
        if not segmento.proveedor_ia:
            raise Exception(f"El segmento {segmento.nombre} no tiene proveedor IA configurado")
        
        logger.info(f"Iniciando procesamiento de segmento {segmento.nombre} (ID: {segmento_id})")
        
        # Generar JSON completo con variables
        json_completo = segmento.generar_json_completo(datos_contexto)
        
        # Configurar parámetros del proveedor
        proveedor = segmento.proveedor_ia
        if not proveedor.activo:
            raise Exception(f"El proveedor IA {proveedor.nombre} está inactivo")
        
        # Preparar el prompt
        prompt_final = segmento.prompt_ia
        if segmento.variables_personalizadas:
            # Aplicar variables personalizadas al prompt
            for variable, valor in segmento.variables_personalizadas.items():
                if isinstance(valor, dict) and 'valor' in valor:
                    prompt_final = prompt_final.replace(f"{{{{{variable}}}}}", str(valor['valor']))
                else:
                    prompt_final = prompt_final.replace(f"{{{{{variable}}}}}", str(valor))
        
        # Aplicar variables de contexto
        for variable, valor in datos_contexto.items():
            prompt_final = prompt_final.replace(f"{{{{{variable}}}}}", str(valor))
        
        # Configurar parámetros de la llamada IA
        parametros_ia = {
            'prompt': prompt_final,
            'max_tokens': configuracion.get('max_tokens', 1500) if configuracion else 1500,
            'temperature': configuracion.get('temperature', 0.7) if configuracion else 0.7,
        }
        
        # Procesar con el proveedor IA (simulado por ahora)
        resultado_ia = _simular_procesamiento_ia(proveedor, parametros_ia, segmento)
        
        # Procesar el resultado
        contenido_generado = resultado_ia.get('contenido', '')
        tokens_usados = resultado_ia.get('tokens_usados', 0)
        costo_aproximado = resultado_ia.get('costo', 0)
        
        tiempo_procesamiento = time.time() - tiempo_inicio
        
        # Actualizar métricas del segmento
        with transaction.atomic():
            segmento.actualizar_metricas_uso(
                tiempo_procesamiento=tiempo_procesamiento,
                resultado_prueba=json.dumps({
                    'success': True,
                    'tokens_usados': tokens_usados,
                    'costo': costo_aproximado,
                    'timestamp': timezone.now().isoformat()
                }, default=str)
            )
        
        resultado = {
            'success': True,
            'segmento_id': segmento_id,
            'segmento_nombre': segmento.nombre,
            'contenido': contenido_generado,
            'tiempo_procesamiento': tiempo_procesamiento,
            'tokens_usados': tokens_usados,
            'costo_aproximado': costo_aproximado,
            'proveedor_usado': proveedor.nombre,
            'json_usado': json_completo,
            'task_id': self.request.id,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(f"Segmento {segmento.nombre} procesado exitosamente en {tiempo_procesamiento:.2f}s")
        return resultado
        
    except SegmentoPlantilla.DoesNotExist:
        error_msg = f"Segmento con ID {segmento_id} no encontrado"
        logger.error(error_msg)
        return {
            'success': False,
            'error': error_msg,
            'error_type': 'segmento_not_found',
            'task_id': self.request.id
        }
        
    except Exception as exc:
        error_msg = f"Error procesando segmento {segmento_id}: {str(exc)}"
        logger.error(error_msg)
        
        # Intentar retry si no hemos agotado los intentos
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando procesamiento de segmento {segmento_id} (intento {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        
        # Actualizar métricas con el error
        try:
            segmento = SegmentoPlantilla.objects.get(id=segmento_id)
            segmento.actualizar_metricas_uso(
                tiempo_procesamiento=time.time() - tiempo_inicio,
                resultado_prueba=json.dumps({
                    'success': False,
                    'error': error_msg,
                    'retries': self.request.retries,
                    'timestamp': timezone.now().isoformat()
                }, default=str)
            )
        except:
            pass
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': 'processing_error',
            'retries': self.request.retries,
            'task_id': self.request.id
        }


def _simular_procesamiento_ia(proveedor: ProveedorIA, parametros: dict, 
                             segmento: SegmentoPlantilla) -> dict:
    """
    Simula el procesamiento con IA mientras se implementa la integración real
    """
    import time
    import random
    
    # Simular tiempo de procesamiento
    time.sleep(random.uniform(2, 5))
    
    contenido_simulado = f"""
[CONTENIDO GENERADO POR IA PARA: {segmento.nombre}]

Proveedor: {proveedor.nombre} ({proveedor.tipo})
Prompt procesado: {parametros['prompt'][:150]}...

Este es contenido generado para el segmento '{segmento.nombre}' 
usando el proveedor {proveedor.nombre}.

Variables de contexto aplicadas correctamente.
Estructura JSON respetada.
Parámetros de configuración utilizados.

[Contenido real sería generado por {proveedor.tipo.upper()}]
"""
    
    tokens_simulados = random.randint(100, 800)
    costo_simulado = tokens_simulados * 0.002 / 1000  # Precio simulado
    
    return {
        'contenido': contenido_simulado,
        'tokens_usados': tokens_simulados,
        'costo': costo_simulado
    }


@shared_task(bind=True)
def batch_procesar_segmentos(self, configuracion_batch: dict) -> dict:
    """
    Procesa múltiples segmentos en lote
    
    Args:
        configuracion_batch: Configuración del lote con segmentos y datos
        
    Returns:
        Dict con resultados del lote
    """
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    tiempo_inicio = time.time()
    segmentos_config = configuracion_batch.get('segmentos', [])
    datos_globales = configuracion_batch.get('datos_contexto', {})
    
    resultados = []
    errores = []
    
    logger.info(f"Iniciando procesamiento en lote de {len(segmentos_config)} segmentos")
    
    for i, config_segmento in enumerate(segmentos_config):
        try:
            segmento_id = config_segmento['segmento_id']
            datos_contexto = {**datos_globales, **config_segmento.get('datos_contexto', {})}
            configuracion = config_segmento.get('configuracion', {})
            
            # Procesar segmento individual
            resultado = procesar_segmento_dinamico.apply_async(
                args=[segmento_id, datos_contexto, configuracion]
            ).get(timeout=300)  # 5 minutos de timeout
            
            resultados.append({
                'segmento_id': segmento_id,
                'resultado': resultado,
                'orden': i
            })
            
        except Exception as e:
            error_info = {
                'segmento_id': config_segmento.get('segmento_id', 'unknown'),
                'error': str(e),
                'orden': i
            }
            errores.append(error_info)
            logger.error(f"Error en segmento {error_info['segmento_id']}: {str(e)}")
    
    tiempo_total = time.time() - tiempo_inicio
    
    resultado_batch = {
        'success': len(errores) == 0,
        'total_segmentos': len(segmentos_config),
        'exitosos': len(resultados),
        'fallidos': len(errores),
        'tiempo_total': tiempo_total,
        'resultados': resultados,
        'errores': errores,
        'task_id': self.request.id,
        'timestamp': timezone.now().isoformat()
    }
    
    logger.info(f"Lote completado: {len(resultados)} exitosos, {len(errores)} fallidos en {tiempo_total:.2f}s")
    return resultado_batch


@shared_task
def limpiar_metricas_antiguas_segmentos():
    """
    Tarea de mantenimiento para limpiar métricas antiguas de segmentos
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        fecha_limite = timezone.now() - timedelta(days=90)  # 90 días atrás
        
        segmentos_actualizados = 0
        for segmento in SegmentoPlantilla.objects.filter(ultima_prueba__lt=fecha_limite):
            # Resetear métricas muy antiguas
            segmento.total_usos = 0
            segmento.tiempo_promedio_procesamiento = None
            segmento.ultimo_resultado_prueba = None
            segmento.save(update_fields=[
                'total_usos', 'tiempo_promedio_procesamiento', 'ultimo_resultado_prueba'
            ])
            segmentos_actualizados += 1
        
        logger.info(f"Limpieza de métricas completada: {segmentos_actualizados} segmentos actualizados")
        
        return {
            'success': True,
            'segmentos_actualizados': segmentos_actualizados,
            'fecha_limite': fecha_limite.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de métricas: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def generar_reporte_uso_segmentos():
    """
    Genera reporte de uso de segmentos para análisis
    """
    import logging
    from django.db.models import Count, Avg, Sum
    
    logger = logging.getLogger(__name__)
    
    try:
        # Estadísticas generales
        stats = SegmentoPlantilla.objects.aggregate(
            total_segmentos=Count('id'),
            segmentos_activos=Count('id', filter={'activo': True}),
            total_usos=Sum('total_usos'),
            tiempo_promedio_global=Avg('tiempo_promedio_procesamiento')
        )
        
        # Top 10 segmentos más usados
        top_segmentos = list(SegmentoPlantilla.objects.order_by('-total_usos')[:10].values(
            'id', 'nombre', 'total_usos', 'tiempo_promedio_procesamiento'
        ))
        
        # Distribución por tipo
        distribucion_tipo = list(SegmentoPlantilla.objects.values('tipo').annotate(
            cantidad=Count('id'),
            usos_totales=Sum('total_usos')
        ))
        
        # Distribución por categoría
        distribucion_categoria = list(SegmentoPlantilla.objects.values('categoria').annotate(
            cantidad=Count('id'),
            usos_totales=Sum('total_usos')
        ))
        
        reporte = {
            'timestamp': timezone.now().isoformat(),
            'estadisticas_generales': stats,
            'top_segmentos': top_segmentos,
            'distribucion_tipo': distribucion_tipo,
            'distribucion_categoria': distribucion_categoria,
            'periodo_analisis': '90_dias'
        }
        
        logger.info("Reporte de uso de segmentos generado exitosamente")
        return reporte
        
    except Exception as e:
        logger.error(f"Error generando reporte: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# ================== TAREAS FASE 2: PROCESAMIENTO DE PLANTILLAS POR SEGMENTOS ==================

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def procesar_plantilla_completa_task(self, ejecucion_id: str, contexto_datos: dict = None):
    """
    Tarea principal para procesar una plantilla completa por segmentos
    Coordina el procesamiento asíncrono de todos los segmentos configurados
    """
    from .models import EjecucionPlantilla, ResultadoSegmento, ActaBorrador, ConfiguracionSegmento
    from celery import group, chain, chord
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Obtener ejecución
        ejecucion = EjecucionPlantilla.objects.select_related('plantilla').get(id=ejecucion_id)
        
        # Actualizar estado inicial
        ejecucion.estado = 'procesando'
        ejecucion.tiempo_inicio = timezone.now()  # Este campo sí existe
        ejecucion.progreso_actual = 0
        ejecucion.progreso_total = 0
        ejecucion.task_id = str(self.request.id)
        ejecucion.save()
        
        logger.info(f"🔄 Iniciando procesamiento de plantilla {ejecucion.plantilla.nombre} (ID: {ejecucion_id})")
        
        # Obtener configuraciones de segmentos ordenados
        configuraciones = ConfiguracionSegmento.objects.filter(
            plantilla=ejecucion.plantilla
        ).select_related('segmento', 'segmento__proveedor_ia').order_by('orden')
        
        if not configuraciones.exists():
            raise ValueError("La plantilla no tiene segmentos configurados")
        
        # Preparar contexto base
        if contexto_datos is None:
            contexto_datos = {
                'transcripcion_id': ejecucion.transcripcion.id if ejecucion.transcripcion else None,
                'variables_contexto': ejecucion.variables_contexto,
                'configuracion_overrides': ejecucion.configuracion_overrides
            }
        
        # Crear resultados para cada segmento
        total_segmentos = configuraciones.count()
        segmento_tasks = []
        
        for i, config in enumerate(configuraciones, 1):
            # Crear ResultadoSegmento
            resultado = ResultadoSegmento.objects.create(
                ejecucion=ejecucion,
                segmento=config.segmento,  # Usar el segmento de la configuración
                orden_procesamiento=i,
                estado='pendiente',
                prompt_usado=""  # Se llenará durante el procesamiento
            )
            
            # Contexto específico del segmento
            contexto_segmento = {
                **contexto_datos,
                'orden_segmento': i,
                'total_segmentos': total_segmentos,
                'configuracion_id': config.id
            }
            
            # Crear tarea según tipo de segmento
            if config.segmento.es_dinamico:
                task = procesar_segmento_con_ia_task.s(resultado.id, contexto_segmento)
            else:
                task = procesar_segmento_estatico_task.s(resultado.id, contexto_segmento)
            
            segmento_tasks.append(task)
        
        # Ejecutar tareas (usar procesamiento secuencial por defecto)
        if len(segmento_tasks) > 1:
            # Procesamiento paralelo con callback
            job = chord(segmento_tasks)(unificar_segmentos_task.s(ejecucion_id))
        else:
            # Procesamiento secuencial
            job = chain(*segmento_tasks, unificar_segmentos_task.s(ejecucion_id))
        
        # Actualizar progreso
        ejecucion.progreso_actual = 0
        ejecucion.progreso_total = len(segmento_tasks)
        ejecucion.save()
        
        logger.info(f"✅ {len(segmento_tasks)} tareas de segmentos creadas para plantilla {ejecucion_id}")
        
        return {
            'ejecucion_id': ejecucion_id,
            'total_segmentos': total_segmentos,
            'procesamiento_paralelo': ejecucion.procesamiento_paralelo,
            'job_id': str(job.id) if hasattr(job, 'id') else None
        }
        
    except Exception as exc:
        logger.error(f"❌ Error procesando plantilla {ejecucion_id}: {exc}")
        
        # Actualizar estado de error
        try:
            ejecucion = EjecucionPlantilla.objects.get(id=ejecucion_id)
            ejecucion.estado = 'error'
            ejecucion.error_details = str(exc)
            ejecucion.fecha_fin = timezone.now()
            ejecucion.save()
        except:
            pass
        
        # Retry si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        raise


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def procesar_segmento_con_ia_task(self, resultado_id: str, contexto: dict):
    """
    Procesa un segmento dinámico usando IA
    """
    from .models import ResultadoSegmento
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    
    try:
        resultado = ResultadoSegmento.objects.select_related(
            'configuracion_segmento__segmento',
            'configuracion_segmento__segmento__proveedor_ia',
            'ejecucion__transcripcion'
        ).get(id=resultado_id)
        
        # Actualizar estado
        resultado.estado = 'procesando'
        resultado.fecha_inicio = timezone.now()
        resultado.save()
        
        config = resultado.configuracion_segmento
        segmento = config.segmento
        
        logger.info(f"🤖 Procesando segmento dinámico: {segmento.nombre}")
        
        # Obtener proveedor IA
        proveedor = segmento.proveedor_ia or resultado.ejecucion.plantilla.proveedor_ia_defecto
        if not proveedor:
            raise ValueError(f"No hay proveedor IA configurado para {segmento.nombre}")
        
        # Preparar prompt
        prompt_efectivo = config.prompt_personalizado or segmento.prompt_ia
        if not prompt_efectivo:
            raise ValueError(f"No hay prompt configurado para {segmento.nombre}")
        
        # Preparar contexto de procesamiento
        contexto_procesamiento = _preparar_contexto_segmento_ia(resultado, contexto)
        
        # Procesar con IA
        inicio_ia = time.time()
        
        try:
            contenido_generado = GeneradorActasService.procesar_segmento_con_ia(
                prompt=prompt_efectivo,
                contexto=contexto_procesamiento,
                proveedor=proveedor,
                configuracion_extra=config.parametros_override
            )
        except Exception as e:
            logger.error(f"❌ Error en procesamiento IA para {segmento.nombre}: {e}")
            raise
        
        tiempo_procesamiento = time.time() - inicio_ia
        
        # Guardar resultado
        resultado.contenido_generado = contenido_generado
        resultado.estado = 'completado'
        resultado.fecha_fin = timezone.now()
        resultado.tiempo_procesamiento = tiempo_procesamiento
        resultado.metadata_procesamiento = {
            'proveedor_usado': proveedor.nombre,
            'modelo_usado': proveedor.modelo,
            'tiempo_procesamiento': tiempo_procesamiento,
            'prompt_usado': prompt_efectivo[:500] + '...' if len(prompt_efectivo) > 500 else prompt_efectivo,
            'longitud_resultado': len(contenido_generado)
        }
        resultado.save()
        
        # Actualizar progreso global
        _actualizar_progreso_ejecucion_segmentos(resultado.ejecucion)
        
        logger.info(f"✅ Segmento dinámico completado: {segmento.nombre} ({tiempo_procesamiento:.2f}s)")
        
        return {
            'resultado_id': resultado_id,
            'segmento_nombre': segmento.nombre,
            'tiempo_procesamiento': tiempo_procesamiento,
            'estado': 'completado'
        }
        
    except Exception as exc:
        logger.error(f"❌ Error procesando segmento dinámico {resultado_id}: {exc}")
        
        # Actualizar estado de error
        try:
            resultado = ResultadoSegmento.objects.get(id=resultado_id)
            resultado.estado = 'error'
            resultado.error_details = str(exc)
            resultado.fecha_fin = timezone.now()
            resultado.save()
        except:
            pass
        
        # Retry si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (2 ** self.request.retries), exc=exc)
        raise


@shared_task(bind=True, max_retries=1)
def procesar_segmento_estatico_task(self, resultado_id: str, contexto: dict):
    """
    Procesa un segmento estático (reemplaza variables sin IA)
    """
    from .models import ResultadoSegmento
    import logging
    import time
    
    logger = logging.getLogger(__name__)
    
    try:
        resultado = ResultadoSegmento.objects.select_related(
            'configuracion_segmento__segmento'
        ).get(id=resultado_id)
        
        # Actualizar estado
        resultado.estado = 'procesando'
        resultado.fecha_inicio = timezone.now()
        resultado.save()
        
        config = resultado.configuracion_segmento
        segmento = config.segmento
        
        logger.info(f"📋 Procesando segmento estático: {segmento.nombre}")
        
        # Obtener contenido base
        contenido_base = segmento.contenido_estatico
        if not contenido_base:
            raise ValueError(f"No hay contenido estático para {segmento.nombre}")
        
        # Preparar contexto
        contexto_procesamiento = _preparar_contexto_segmento_ia(resultado, contexto)
        
        # Procesar template
        inicio_procesamiento = time.time()
        contenido_generado = _procesar_template_estatico(contenido_base, contexto_procesamiento)
        tiempo_procesamiento = time.time() - inicio_procesamiento
        
        # Guardar resultado
        resultado.contenido_generado = contenido_generado
        resultado.estado = 'completado'
        resultado.fecha_fin = timezone.now()
        resultado.tiempo_procesamiento = tiempo_procesamiento
        resultado.metadata_procesamiento = {
            'tipo_procesamiento': 'estatico',
            'tiempo_procesamiento': tiempo_procesamiento,
            'longitud_original': len(contenido_base),
            'longitud_final': len(contenido_generado)
        }
        resultado.save()
        
        # Actualizar progreso global
        _actualizar_progreso_ejecucion_segmentos(resultado.ejecucion)
        
        logger.info(f"✅ Segmento estático completado: {segmento.nombre}")
        
        return {
            'resultado_id': resultado_id,
            'segmento_nombre': segmento.nombre,
            'tiempo_procesamiento': tiempo_procesamiento,
            'estado': 'completado'
        }
        
    except Exception as exc:
        logger.error(f"❌ Error procesando segmento estático {resultado_id}: {exc}")
        
        # Actualizar estado de error
        try:
            resultado = ResultadoSegmento.objects.get(id=resultado_id)
            resultado.estado = 'error'
            resultado.error_details = str(exc)
            resultado.fecha_fin = timezone.now()
            resultado.save()
        except:
            pass
        
        # Retry si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=15, exc=exc)
        raise


@shared_task(bind=True, max_retries=2)
def unificar_segmentos_task(self, resultados_anteriores, ejecucion_id: str):
    """
    Unifica todos los segmentos procesados en un acta final
    """
    from .models import EjecucionPlantilla, ResultadoSegmento, ActaBorrador
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        ejecucion = EjecucionPlantilla.objects.select_related('plantilla').get(id=ejecucion_id)
        
        logger.info(f"🔄 Unificando segmentos para plantilla {ejecucion.plantilla.nombre}")
        
        # Obtener todos los resultados
        resultados = ResultadoSegmento.objects.filter(
            ejecucion=ejecucion
        ).select_related('configuracion_segmento__segmento').order_by('orden_procesamiento')
        
        # Verificar completitud
        segmentos_error = resultados.filter(estado='error')
        if segmentos_error.exists():
            error_names = list(segmentos_error.values_list('configuracion_segmento__segmento__nombre', flat=True))
            error_msg = f"Segmentos con error: {error_names}"
            
            ejecucion.estado = 'error'
            ejecucion.error_details = error_msg
            ejecucion.fecha_fin = timezone.now()
            ejecucion.save()
            
            raise ValueError(error_msg)
        
        # Actualizar estado
        ejecucion.estado = 'unificando'
        ejecucion.progreso = 85
        ejecucion.save()
        
        # Unificar contenido
        contenido_partes = []
        for resultado in resultados.filter(estado='completado'):
            if resultado.contenido_generado:
                segmento = resultado.configuracion_segmento.segmento
                
                # Añadir separador si no es el primero
                if contenido_partes:
                    contenido_partes.append("\n\n---\n\n")
                
                # Añadir título de sección
                if segmento.categoria != 'otros':
                    titulo_seccion = f"## {segmento.nombre}\n\n"
                    contenido_partes.append(titulo_seccion)
                
                # Añadir contenido
                contenido_partes.append(resultado.contenido_generado)
        
        contenido_unificado = "".join(contenido_partes)

        # Aplicar prompt global de plantilla si está disponible
        from collections import UserDict
        from .ia_providers import get_ia_provider

        prompt_global = ejecucion.prompt_unificacion_override or (ejecucion.plantilla.prompt_global or '')
        prompt_global = prompt_global.strip()
        contenido_final = contenido_unificado
        prompt_final_renderizado = None

        prompt_metadata = None

        if prompt_global:
            logger.info("🤖 Ejecutando prompt global de plantilla durante unificación")

            class _PromptFormatter(UserDict):
                def __missing__(self, key):
                    return '{' + key + '}'

            participantes = ejecucion.variables_contexto.get('participantes', []) if ejecucion.variables_contexto else []
            participantes_texto = ", ".join([
                str(p.get('nombre', p)) if isinstance(p, dict) else str(p)
                for p in participantes if p
            ])

            prompt_contexto = {
                'segmentos': contenido_unificado,
                'contenido_unificado': contenido_unificado,
                'transcripcion': ejecucion.variables_contexto.get('transcripcion_texto', '') if ejecucion.variables_contexto else '',
                'fecha': ejecucion.variables_contexto.get('fecha_sesion', ''),
                'participantes': participantes_texto,
                'titulo_acta': ejecucion.nombre,
                'numero_acta': ejecucion.variables_contexto.get('numero_acta', ''),
                'tipo_acta': ejecucion.plantilla.get_tipo_acta_display(),
            }

            prompt_final_renderizado = prompt_global.format_map(_PromptFormatter(prompt_contexto))
            prompt_metadata = {
                'prompt_original': prompt_global,
                'prompt_renderizado': prompt_final_renderizado,
                'timestamp': timezone.now().isoformat()
            }

            proveedor_final = ejecucion.proveedor_ia_global or ejecucion.plantilla.proveedor_ia_defecto
            if proveedor_final:
                try:
                    proveedor_instance = get_ia_provider(proveedor_final)
                    respuesta_final = proveedor_instance.generar_respuesta(
                        prompt=prompt_final_renderizado,
                        contexto={
                            'plantilla': ejecucion.plantilla.nombre,
                            'ejecucion': ejecucion.id,
                            'segmentos_total': resultados.count(),
                            'borrador_unificado': contenido_unificado
                        }
                    )
                    contenido_generado_final = respuesta_final.get('contenido') or respuesta_final.get('respuesta')
                    if contenido_generado_final and len(contenido_generado_final.strip()) > 100:
                        contenido_final = contenido_generado_final.strip()
                        logger.info("✅ Prompt global aplicado correctamente para ejecución")
                        resultados_parciales = ejecucion.resultados_parciales or {}
                        prompt_metadata.update({
                            'tokens_usados': respuesta_final.get('tokens_usados'),
                            'modelo_usado': respuesta_final.get('modelo_usado'),
                            'tiempo_respuesta': respuesta_final.get('tiempo_respuesta')
                        })
                        resultados_parciales['prompt_final'] = prompt_metadata
                        ejecucion.resultados_parciales = resultados_parciales
                        ejecucion.resultado_unificacion = contenido_final
                    else:
                        logger.warning("⚠️ Respuesta final de prompt global inválida, usando contenido unificado")
                        prompt_metadata['error'] = 'Respuesta final insuficiente'
                except Exception as exc_final:
                    logger.error(f"❌ Error aplicando prompt global en unificación: {exc_final}")
                    prompt_metadata['error'] = str(exc_final)
            else:
                logger.warning("⚠️ No hay proveedor IA configurado para aplicar prompt global en unificación")
                prompt_metadata['error'] = 'Proveedor IA no configurado'

        if prompt_metadata:
            resultados_parciales = ejecucion.resultados_parciales or {}
            resultados_parciales.setdefault('prompt_final', prompt_metadata)
            ejecucion.resultados_parciales = resultados_parciales

        # Crear acta borrador
        acta_borrador = ActaBorrador.objects.create(
            ejecucion=ejecucion,
            contenido_markdown=contenido_final,
            contenido_html=contenido_final.replace('\n', '<br>') if contenido_final else '',
            estado='borrador',
            version=1,
            metadata_generacion={
                'total_segmentos': resultados.count(),
                'segmentos_completados': resultados.filter(estado='completado').count(),
                'tiempo_total_procesamiento': sum(r.tiempo_procesamiento or 0 for r in resultados),
                'fecha_generacion': timezone.now().isoformat(),
                'plantilla_utilizada': ejecucion.plantilla.nombre
            }
        )
        
        # Finalizar ejecución
        ejecucion.estado = 'completado'
        ejecucion.progreso = 100
        ejecucion.fecha_fin = timezone.now()
        ejecucion.acta_generada = acta_borrador
        ejecucion.save()
        
        logger.info(f"✅ Unificación completada. Acta borrador: {acta_borrador.id}")
        
        return {
            'ejecucion_id': ejecucion_id,
            'acta_borrador_id': str(acta_borrador.id),
            'total_segmentos': resultados.count(),
            'estado': 'completado'
        }
        
    except Exception as exc:
        logger.error(f"❌ Error unificando segmentos {ejecucion_id}: {exc}")
        
        # Actualizar estado de error
        try:
            ejecucion = EjecucionPlantilla.objects.get(id=ejecucion_id)
            ejecucion.estado = 'error'
            ejecucion.error_details = str(exc)
            ejecucion.fecha_fin = timezone.now()
            ejecucion.save()
        except:
            pass
        
        # Retry si es posible
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        raise


# ================== FUNCIONES AUXILIARES PARA TAREAS FASE 2 ==================

def _preparar_contexto_segmento_ia(resultado, contexto: dict) -> dict:
    """Prepara contexto específico para procesamiento de segmentos"""
    from .models import ResultadoSegmento
    
    ejecucion = resultado.ejecucion
    
    contexto_procesamiento = {
        **contexto,
        'ejecucion_id': str(ejecucion.id),
        'plantilla_nombre': ejecucion.plantilla.nombre,
        'segmento_nombre': resultado.configuracion_segmento.segmento.nombre,
        'orden_segmento': resultado.orden_procesamiento
    }
    
    # Datos de transcripción
    if ejecucion.transcripcion:
        transcripcion = ejecucion.transcripcion
        participantes_transcripcion = getattr(transcripcion, 'participantes_detallados', None) or []
        if not participantes_transcripcion and hasattr(transcripcion, 'procesamiento_audio'):
            participantes_transcripcion = getattr(transcripcion.procesamiento_audio, 'participantes_detallados', []) or []

        contexto_procesamiento.update({
            'transcripcion_texto': transcripcion.texto_final,
            'transcripcion_metadata': transcripcion.metadata_procesamiento or {},
            'participantes': participantes_transcripcion,
            'duracion_audio': transcripcion.duracion_estimada,
            'fecha_transcripcion': transcripcion.fecha_creacion.isoformat()
        })
    
    # Parámetros globales
    if ejecucion.parametros_globales:
        contexto_procesamiento.update(ejecucion.parametros_globales)
    
    return contexto_procesamiento


def _procesar_template_estatico(contenido: str, contexto: dict) -> str:
    """Procesa template estático reemplazando variables"""
    from django.template import Template, Context
    
    try:
        template = Template(contenido)
        context = Context(contexto)
        return template.render(context)
    except Exception as e:
        # Fallback: reemplazo manual básico
        resultado = contenido
        for key, value in contexto.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in resultado:
                resultado = resultado.replace(placeholder, str(value))
        return resultado


def _actualizar_progreso_ejecucion_segmentos(ejecucion):
    """Actualiza progreso basado en segmentos completados"""
    from .models import ResultadoSegmento
    
    total = ResultadoSegmento.objects.filter(ejecucion=ejecucion).count()
    completados = ResultadoSegmento.objects.filter(
        ejecucion=ejecucion, estado='completado'
    ).count()
    
    if total > 0:
        progreso_segmentos = (completados / total) * 70  # 70% del progreso total
        nuevo_progreso = min(10 + progreso_segmentos, 80)  # Entre 10% y 80%
        
        if ejecucion.progreso < nuevo_progreso:
            ejecucion.progreso = nuevo_progreso
            ejecucion.save(update_fields=['progreso'])


# ================== TAREAS DE MONITOREO Y LIMPIEZA FASE 2 ==================

@shared_task
def limpiar_ejecuciones_antiguas_task():
    """Limpia ejecuciones antiguas para liberar espacio"""
    from .models import EjecucionPlantilla
    import logging
    
    logger = logging.getLogger(__name__)
    dias_limite = 30  # Configurable
    fecha_limite = timezone.now() - timedelta(days=dias_limite)
    
    # Limpiar ejecuciones completadas antiguas
    ejecuciones_antiguas = EjecucionPlantilla.objects.filter(
        estado__in=['completado', 'error'],
        fecha_fin__lt=fecha_limite
    )
    
    count = ejecuciones_antiguas.count()
    ejecuciones_antiguas.delete()
    
    logger.info(f"🧹 Limpiadas {count} ejecuciones antiguas")
    return {'ejecuciones_eliminadas': count}


@shared_task
def monitorear_ejecuciones_colgadas_task():
    """Identifica ejecuciones que llevan demasiado tiempo procesando"""
    from .models import EjecucionPlantilla
    import logging
    
    logger = logging.getLogger(__name__)
    limite_horas = 2  # Configurable
    fecha_limite = timezone.now() - timedelta(hours=limite_horas)
    
    ejecuciones_colgadas = EjecucionPlantilla.objects.filter(
        estado__in=['procesando', 'pendiente'],
        fecha_inicio__lt=fecha_limite
    )
    
    count = 0
    for ejecucion in ejecuciones_colgadas:
        ejecucion.estado = 'error'
        ejecucion.error_details = 'Timeout: Procesamiento excedió el tiempo límite'
        ejecucion.fecha_fin = timezone.now()
        ejecucion.save()
        count += 1
    
    logger.info(f"⚠️ Marcadas como timeout: {count} ejecuciones")
    return {'ejecuciones_timeout': count}


# ======================================================================
# TAREA SIMPLE PARA PROCESAMIENTO DE ACTAS
# ======================================================================

@shared_task(bind=True, max_retries=2)
def procesar_acta_simple_task(self, acta_id):
    """
    Tarea simple para procesar un acta - simulación con IA
    """
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        from .models import ActaGenerada
        
        # Obtener acta
        acta = ActaGenerada.objects.get(id=acta_id)
        
        logger.info(f"🔄 Iniciando procesamiento simple de acta {acta.numero_acta}")
        
        # Actualizar estado
        acta.estado = 'procesando'
        acta.progreso = 10
        acta.fecha_procesamiento = timezone.now()
        acta.task_id_celery = str(self.request.id)
        acta.save()
        
        # Simular procesamiento de segmentos
        total_segmentos = 5
        
        for i in range(1, total_segmentos + 1):
            logger.info(f"📝 Procesando segmento {i}/{total_segmentos}")
            
            # Simular tiempo de procesamiento
            time.sleep(2)
            
            # Actualizar progreso
            progreso = int((i / total_segmentos) * 80) + 10  # 10-90%
            acta.progreso = progreso
            
            # Agregar al historial
            historial_entry = {
                'timestamp': timezone.now().isoformat(),
                'evento': f'segmento_{i}_procesado',
                'descripcion': f'Segmento {i} procesado exitosamente',
                'progreso': progreso
            }
            acta.historial_cambios.append(historial_entry)
            acta.save()
        
        # Unificar contenido final
        logger.info("🔗 Unificando contenido final")
        acta.estado = 'unificando'
        acta.progreso = 90
        acta.save()
        
        time.sleep(3)  # Simular unificación
        
        # Generar contenido final simulado
        contenido_final = f"""
# ACTA DE REUNIÓN MUNICIPAL
## {acta.numero_acta}

**Fecha de Sesión:** {acta.fecha_sesion.strftime('%d/%m/%Y') if acta.fecha_sesion else 'N/A'}
**Lugar:** Sala de Sesiones - Municipio de Pastaza
**Transcripción Base:** {str(acta.transcripcion) if acta.transcripcion else 'N/A'}
**Procesado con:** {acta.proveedor_ia.nombre}

---

## 1. APERTURA DE SESIÓN
Se procede a la apertura de la sesión ordinaria/extraordinaria del Concejo Municipal.

## 2. VERIFICACIÓN DEL QUÓRUM
Se verifica la asistencia de los concejales y se constata el quórum reglamentario.

## 3. ORDEN DEL DÍA
- Punto 1: Revisión de actas anteriores
- Punto 2: Informes de comisiones
- Punto 3: Asuntos varios
- Punto 4: Clausura

## 4. DESARROLLO DE LA SESIÓN
[Contenido procesado con IA basado en la transcripción]

## 5. ACUERDOS ADOPTADOS
- Acuerdo 1: [Detalle del acuerdo]
- Acuerdo 2: [Detalle del acuerdo]

## 6. CLAUSURA
Se da por terminada la sesión a las [hora] del día [fecha].

---
**Documento generado automáticamente el {timezone.now().strftime('%d/%m/%Y a las %H:%M')}**
**Sistema de Actas Municipales - Pastaza**
"""
        
        # Guardar resultado final
        acta.contenido_final = contenido_final
        acta.contenido_html = contenido_final.replace('\n', '<br>')
        acta.estado = 'revision'
        acta.progreso = 100
        acta.fecha_revision = timezone.now()
        
        # Agregar entrada final al historial
        historial_final = {
            'timestamp': timezone.now().isoformat(),
            'evento': 'procesamiento_completado',
            'descripcion': 'Procesamiento completado exitosamente',
            'progreso': 100,
            'task_id': str(self.request.id)
        }
        acta.historial_cambios.append(historial_final)
        acta.save()
        
        logger.info(f"✅ Procesamiento de acta {acta.numero_acta} completado exitosamente")
        
        return {
            'success': True,
            'acta_id': acta_id,
            'numero_acta': acta.numero_acta,
            'estado_final': acta.estado,
            'progreso': acta.progreso,
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"❌ Error procesando acta {acta_id}: {exc}")
        
        # Intentar actualizar el acta con el error
        try:
            acta = ActaGenerada.objects.get(id=acta_id)
            acta.estado = 'error'
            acta.mensajes_error = str(exc)
            acta.save()
        except:
            pass
            
        # Reintentar si hay reintentos disponibles
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Reintentando procesamiento de acta {acta_id} (intento {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=exc)
        else:
            logger.error(f"❌ Máximo de reintentos alcanzado para acta {acta_id}")
            raise


@shared_task(bind=True, max_retries=2)
def procesar_acta_completa_real(self, acta_id):
    """
    Procesamiento REAL de un acta usando la transcripción y segmentos configurados
    """
    from .models import ActaGenerada, ConfiguracionSegmento
    from .ia_providers import get_ia_provider
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Obtener acta con relaciones necesarias
        acta = ActaGenerada.objects.select_related(
            'plantilla', 'proveedor_ia', 'transcripcion'
        ).get(id=acta_id)
        
        logger.info(f"🔄 Iniciando procesamiento REAL de acta {acta.numero_acta}")
        
        # Actualizar estado inicial
        acta.estado = 'procesando'
        acta.progreso = 0
        acta.fecha_procesamiento = timezone.now()
        acta.segmentos_procesados = {}
        acta.mensajes_error = ""
        
        # Registrar inicio en historial
        if not acta.historial_cambios:
            acta.historial_cambios = []
        acta.historial_cambios.append({
            'evento': 'procesamiento_iniciado',
            'descripcion': 'Procesamiento real iniciado',
            'progreso': 0,
            'timestamp': timezone.now().isoformat(),
        })
        acta.save()
        
        # Verificar que tiene transcripción
        if not acta.transcripcion or not acta.transcripcion.conversacion_json:
            raise ValueError("El acta no tiene una transcripción válida")
        
        # Obtener segmentos de conversación
        conversacion = acta.transcripcion.conversacion_json.get('conversacion', [])
        if not conversacion:
            raise ValueError("La transcripción no tiene segmentos de conversación")
        
        logger.info(f"📝 Transcripción con {len(conversacion)} segmentos de conversación")
        
        # Obtener configuraciones de segmentos
        configuraciones = ConfiguracionSegmento.objects.filter(
            plantilla=acta.plantilla
        ).select_related('segmento').order_by('orden')
        
        if not configuraciones.exists():
            raise ValueError("La plantilla no tiene segmentos configurados")
        
        total_segmentos = configuraciones.count()
        logger.info(f"📋 Plantilla con {total_segmentos} segmentos configurados")
        
        # Procesar cada segmento
        contenido_completo = []
        
        for i, config in enumerate(configuraciones):
            segmento = config.segmento
            progreso_actual = int((i / total_segmentos) * 90)  # 90% para segmentos, 10% para unificación
            
            logger.info(f"📝 Procesando segmento {i+1}/{total_segmentos}: {segmento.nombre}")
            
            # Actualizar progreso
            acta.progreso = progreso_actual
            acta.historial_cambios.append({
                'evento': f'segmento_{i+1}_iniciado',
                'descripcion': f'Iniciando procesamiento de {segmento.nombre}',
                'progreso': progreso_actual,
                'timestamp': timezone.now().isoformat(),
            })
            acta.save()
            
            # Preparar contexto para el segmento
            contexto_segmento = {
                'transcripcion_completa': conversacion,
                'numero_acta': acta.numero_acta,
                'fecha_sesion': acta.fecha_sesion.isoformat() if acta.fecha_sesion else None,
                'titulo_acta': acta.titulo,
            }
            
            if segmento.tipo == 'dinamico':
                # Segmento dinámico: usar IA
                try:
                    # Obtener proveedor IA
                    proveedor = acta.proveedor_ia
                    ia_provider = get_ia_provider(proveedor)
                    
                    # Preparar prompt
                    prompt_base = config.prompt_personalizado or segmento.prompt_ia
                    
                    # Convertir conversación a texto para el prompt
                    texto_conversacion = "\n".join([
                        f"[{seg['hablante']}] ({seg['inicio']:.1f}s): {seg['texto']}"
                        for seg in conversacion
                    ])
                    
                    prompt_final = f"""
{prompt_base}

TRANSCRIPCIÓN DE LA REUNIÓN:
{texto_conversacion}

INSTRUCCIONES:
- Genera el contenido para la sección "{segmento.nombre}"
- Usa ÚNICAMENTE la información de la transcripción
- Mantén un formato profesional y claro
- Si no hay información relevante, indica "No se discutieron temas relacionados con {segmento.nombre}"
"""
                    
                    logger.info(f"🤖 Enviando prompt a IA para {segmento.nombre}")
                    
                    # Llamar a IA
                    resultado_ia = ia_provider.generar_respuesta(
                        prompt=prompt_final,
                        contexto=contexto_segmento
                    )
                    
                    contenido_segmento = resultado_ia.get('contenido', f'Error procesando {segmento.nombre}')
                    
                    # Guardar información detallada del procesamiento
                    info_segmento = {
                        'orden': i + 1,
                        'segmento_id': segmento.id,
                        'nombre': segmento.nombre,
                        'tipo': segmento.tipo,
                        'contenido': contenido_segmento,
                        'prompt_usado': prompt_final,
                        'proveedor': proveedor.nombre,
                        'timestamp': timezone.now().isoformat(),
                        'tokens_usados': resultado_ia.get('tokens_usados', 0),
                        'costo_estimado': resultado_ia.get('costo_estimado', 0),
                    }
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando segmento dinámico {segmento.nombre}: {str(e)}")
                    contenido_segmento = f"[ERROR] No se pudo procesar {segmento.nombre}: {str(e)}"
                    info_segmento = {
                        'orden': i + 1,
                        'segmento_id': segmento.id,
                        'nombre': segmento.nombre,
                        'tipo': segmento.tipo,
                        'contenido': contenido_segmento,
                        'error': str(e),
                        'timestamp': timezone.now().isoformat(),
                    }
            else:
                # Segmento estático: usar contenido predefinido
                contenido_segmento = segmento.contenido_estatico or f"[{segmento.nombre}]\n(Contenido estático no definido)"
                info_segmento = {
                    'orden': i + 1,
                    'segmento_id': segmento.id,
                    'nombre': segmento.nombre,
                    'tipo': segmento.tipo,
                    'contenido': contenido_segmento,
                    'timestamp': timezone.now().isoformat(),
                }
            
            # Guardar segmento procesado
            acta.segmentos_procesados[f'segmento_{i+1}'] = info_segmento
            contenido_completo.append(f"\n=== {segmento.nombre.upper()} ===\n{contenido_segmento}\n")
            
            # Actualizar progreso completado del segmento
            progreso_segmento = int(((i + 1) / total_segmentos) * 90)
            acta.progreso = progreso_segmento
            acta.historial_cambios.append({
                'evento': f'segmento_{i+1}_completado',
                'descripcion': f'Segmento {segmento.nombre} procesado exitosamente',
                'progreso': progreso_segmento,
                'timestamp': timezone.now().isoformat(),
            })
            acta.save()
            
            logger.info(f"✅ Segmento {segmento.nombre} completado")
        
        # Unificar contenido final
        logger.info(f"🔗 Unificando contenido final")
        acta.progreso = 95
        acta.historial_cambios.append({
            'evento': 'unificacion_iniciada',
            'descripcion': 'Unificando todos los segmentos',
            'progreso': 95,
            'timestamp': timezone.now().isoformat(),
        })
        acta.save()
        
        # Crear contenido unificado básico
        contenido_borrador = "\n\n".join(contenido_completo)
        contenido_unificado = contenido_borrador

        # Intentar mejorar con IA si hay múltiples segmentos
        if total_segmentos > 1:
            try:
                logger.info(f"🤖 Aplicando prompt de unificación general con IA")
                prompt_unificacion = f"""
Eres un asistente especializado en redacción de actas municipales.

Tu tarea es revisar y unificar el siguiente contenido de acta municipal, asegurando:
1. Coherencia y fluidez en el texto
2. Formato apropiado para un documento oficial
3. Eliminación de redundancias
4. Estructura lógica y profesional

Contenido a unificar:
{contenido_borrador}

Genera una versión unificada manteniendo toda la información importante pero mejorando la redacción y estructura.
"""

                respuesta_ia_unificacion = ia_provider.generar_respuesta(prompt_unificacion)
                
                # Extraer contenido de la respuesta de manera robusta
                if isinstance(respuesta_ia_unificacion, dict):
                    respuesta_texto = respuesta_ia_unificacion.get('contenido') or respuesta_ia_unificacion.get('respuesta') or respuesta_ia_unificacion.get('text') or ''
                else:
                    respuesta_texto = str(respuesta_ia_unificacion) if respuesta_ia_unificacion else ''
                
                # Limpiar y validar el contenido
                respuesta_texto = respuesta_texto.strip() if respuesta_texto else ''
                if respuesta_texto and len(respuesta_texto) > 100:
                    contenido_unificado = respuesta_texto
                    logger.info(f"✅ Contenido mejorado con IA: {len(contenido_unificado)} caracteres")

                    acta.historial_cambios.append({
                        'evento': 'unificacion_ia_aplicada',
                        'descripcion': f'Contenido mejorado con IA: {len(contenido_unificado)} caracteres',
                        'progreso': 97,
                        'timestamp': timezone.now().isoformat(),
                    })
                else:
                    logger.warning("⚠️ IA no generó respuesta válida, usando unificación básica")
                    contenido_unificado = contenido_borrador
            except Exception as e:
                logger.error(f"❌ Error en unificación con IA: {str(e)}")
                contenido_unificado = contenido_borrador

        # Guardar borrador previo al prompt global
        acta.contenido_borrador = contenido_unificado

        # Aplicar prompt global de la plantilla para versión final
        prompt_global_plantilla = (acta.plantilla.prompt_global or '').strip()
        contenido_final = contenido_unificado
        prompt_final_renderizado = None
        metricas_finales = acta.metricas_procesamiento or {}

        procesamiento_final_metadata = {}

        if prompt_global_plantilla:
            logger.info("🤖 Ejecutando prompt global de plantilla para versión final del acta")

            from collections import UserDict

            class _PromptFormatter(UserDict):
                def __missing__(self, key):
                    return '{' + key + '}'

            participantes = []
            if acta.transcripcion:
                participantes = getattr(acta.transcripcion, 'participantes_detallados', None) or []
                if not participantes and hasattr(acta.transcripcion, 'procesamiento_audio'):
                    participantes = getattr(acta.transcripcion.procesamiento_audio, 'participantes_detallados', []) or []

            participantes_normalizados = []
            for participante in participantes or []:
                if not participante:
                    continue

                if isinstance(participante, dict):
                    nombre = participante.get('nombre') or participante.get('alias') or participante.get('rol') or participante.get('cargo')
                    if nombre:
                        participantes_normalizados.append(str(nombre))
                    else:
                        participantes_normalizados.append('Participante sin nombre')
                else:
                    participantes_normalizados.append(str(participante))

            participantes_texto = ", ".join(participantes_normalizados)

            if hasattr(acta.transcripcion, 'conversacion_json') and isinstance(acta.transcripcion.conversacion_json, dict):
                transcripcion_texto = "\n".join([
                    f"[{seg.get('hablante')}] {seg.get('texto')}"
                    for seg in acta.transcripcion.conversacion_json.get('conversacion', [])
                ])
            else:
                transcripcion_texto = getattr(acta.transcripcion, 'texto_completo', '') if acta.transcripcion else ''

            prompt_contexto = {
                'segmentos': contenido_unificado,
                'contenido_unificado': contenido_unificado,
                'borrador': contenido_unificado,
                'transcripcion': transcripcion_texto,
                'fecha': acta.fecha_sesion.strftime('%d/%m/%Y') if acta.fecha_sesion else '',
                'participantes': participantes_texto,
                'titulo_acta': acta.titulo,
                'numero_acta': acta.numero_acta,
                'tipo_acta': acta.plantilla.get_tipo_acta_display(),
            }

            prompt_final_renderizado = prompt_global_plantilla.format_map(_PromptFormatter(prompt_contexto))
            procesamiento_final_metadata = {
                'prompt_original': prompt_global_plantilla,
                'prompt_renderizado': prompt_final_renderizado,
                'timestamp': timezone.now().isoformat()
            }

            try:
                ia_provider_global = get_ia_provider(acta.proveedor_ia)
                respuesta_final = ia_provider_global.generar_respuesta(
                    prompt=prompt_final_renderizado,
                    contexto={
                        'numero_acta': acta.numero_acta,
                        'titulo_acta': acta.titulo,
                        'proveedor': acta.proveedor_ia.nombre,
                        'plantilla': acta.plantilla.nombre,
                        'segmentos_resumidos': [
                            {
                                'nombre': seg.get('nombre'),
                                'orden': seg.get('orden'),
                                'longitud': len(seg.get('contenido', '') or '')
                            }
                            for seg in acta.segmentos_procesados.values()
                        ] if acta.segmentos_procesados else [],
                        'borrador_unificado': contenido_unificado
                    }
                )

                contenido_generado_final = respuesta_final.get('contenido') or respuesta_final.get('respuesta')
                if contenido_generado_final and len(contenido_generado_final.strip()) > 100:
                    contenido_final = contenido_generado_final.strip()
                    procesamiento_final_metadata.update({
                        'tokens_usados': respuesta_final.get('tokens_usados'),
                        'modelo_usado': respuesta_final.get('modelo_usado'),
                        'tiempo_respuesta': respuesta_final.get('tiempo_respuesta')
                    })
                    metricas_finales['prompt_final'] = {
                        'tokens_usados': respuesta_final.get('tokens_usados'),
                        'modelo_usado': respuesta_final.get('modelo_usado'),
                        'tiempo_respuesta': respuesta_final.get('tiempo_respuesta'),
                        'timestamp': timezone.now().isoformat()
                    }
                    logger.info("✅ Prompt global aplicado correctamente")
                else:
                    logger.warning("⚠️ Respuesta final inválida, se mantiene contenido unificado")
                    procesamiento_final_metadata['error'] = 'Respuesta final insuficiente'
            except Exception as e:
                logger.error(f"❌ Error aplicando prompt global: {str(e)}")
                procesamiento_final_metadata['error'] = str(e)

        # Guardar contenido final y métrica
        acta.contenido_final = contenido_final
        acta.contenido_html = contenido_final.replace('\n', '<br>') if contenido_final else ''
        acta.metricas_procesamiento = metricas_finales
        if procesamiento_final_metadata:
            metadatos_acta = acta.metadatos or {}
            metadatos_acta['procesamiento_final'] = procesamiento_final_metadata
            acta.metadatos = metadatos_acta
            acta.historial_cambios.append({
                'evento': 'prompt_global_ejecutado',
                'descripcion': 'Se aplicó el prompt global de la plantilla para generar la versión final del acta',
                'progreso': 99,
                'timestamp': timezone.now().isoformat(),
            })
        
        # Finalizar
        acta.estado = 'revision'
        acta.progreso = 100
        acta.fecha_completado = timezone.now()
        acta.historial_cambios.append({
            'evento': 'procesamiento_completado',
            'descripcion': f'Acta procesada exitosamente con {total_segmentos} segmentos. Contenido final: {len(contenido_unificado)} caracteres.',
            'progreso': 100,
            'timestamp': timezone.now().isoformat(),
        })
        acta.save()
        
        logger.info(f"✅ Acta {acta.numero_acta} procesada exitosamente")
        
        return {
            'success': True,
            'acta_id': acta.id,
            'numero_acta': acta.numero_acta,
            'estado_final': acta.estado,
            'progreso': 100,
            'segmentos_procesados': len(acta.segmentos_procesados),
            'task_id': str(self.request.id)
        }
        
    except Exception as exc:
        logger.error(f"❌ Error procesando acta {acta_id}: {str(exc)}")
        
        try:
            acta = ActaGenerada.objects.get(id=acta_id)
            acta.estado = 'error'
            acta.mensajes_error = str(exc)
            acta.historial_cambios.append({
                'evento': 'error_procesamiento',
                'descripcion': f'Error: {str(exc)}',
                'progreso': acta.progreso,
                'timestamp': timezone.now().isoformat(),
            })
            acta.save()
        except:
            pass
            
        # Reintentar si hay reintentos disponibles
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Reintentando procesamiento de acta {acta_id} (intento {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=exc)
        else:
            logger.error(f"❌ Máximo de reintentos alcanzado para acta {acta_id}")
            raise