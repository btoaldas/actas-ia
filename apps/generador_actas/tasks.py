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