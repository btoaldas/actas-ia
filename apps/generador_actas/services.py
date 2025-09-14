"""
Servicios de negocio para generación de actas con IA
Contiene la lógica principal y utilidades del módulo
"""
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.transcripcion.models import Transcripcion
from .models import (
    ActaGenerada, ProveedorIA, PlantillaActa, 
    SegmentoPlantilla, ConfiguracionSegmento
)
from .ia_providers import get_ia_provider

logger = logging.getLogger(__name__)


class GeneradorActasService:
    """
    Servicio principal para gestión de actas generadas con IA
    """
    
    @staticmethod
    def crear_acta_desde_transcripcion(
        transcripcion: Transcripcion,
        plantilla: PlantillaActa,
        proveedor_ia: ProveedorIA,
        usuario: User,
        **kwargs
    ) -> ActaGenerada:
        """
        Crea una nueva acta desde una transcripción validada
        
        Args:
            transcripcion: Transcripción base
            plantilla: Plantilla a utilizar
            proveedor_ia: Proveedor IA para procesamiento
            usuario: Usuario que crea el acta
            **kwargs: Parámetros adicionales del acta
            
        Returns:
            Instancia de ActaGenerada creada
        """
        try:
            # Validar transcripción
            if not transcripcion.conversacion_json:
                raise ValidationError("La transcripción no tiene datos de conversación")
            
            if not transcripcion.conversacion_json.get('conversacion'):
                raise ValidationError("La transcripción no contiene segmentos de conversación")
            
            # Validar plantilla
            if not plantilla.activa:
                raise ValidationError("La plantilla seleccionada no está activa")
            
            # Validar proveedor IA
            if not proveedor_ia.activo:
                raise ValidationError("El proveedor IA seleccionado no está activo")
            
            # Probar conexión con el proveedor
            try:
                ia_provider = get_ia_provider(proveedor_ia)
                if not ia_provider.validar_configuracion():
                    raise ValidationError(f"La configuración del proveedor {proveedor_ia.nombre} no es válida")
            except Exception as e:
                raise ValidationError(f"Error conectando con {proveedor_ia.nombre}: {str(e)}")
            
            # Extraer información de la transcripción
            audio = transcripcion.procesamiento_audio
            
            # Determinar fecha de sesión
            fecha_sesion = kwargs.get('fecha_sesion')
            if not fecha_sesion:
                if hasattr(audio, 'fecha_procesamiento') and audio.fecha_procesamiento:
                    fecha_sesion = audio.fecha_procesamiento.date()
                else:
                    fecha_sesion = date.today()
            
            # Generar número de acta automático
            numero_acta = kwargs.get('numero_acta') or GeneradorActasService.generar_numero_acta(
                plantilla.tipo_acta,
                fecha_sesion
            )
            
            # Generar título automático
            titulo = kwargs.get('titulo') or GeneradorActasService.generar_titulo_acta(
                transcripcion,
                plantilla.tipo_acta
            )
            
            with transaction.atomic():
                # Crear el acta
                acta = ActaGenerada.objects.create(
                    numero_acta=numero_acta,
                    titulo=titulo,
                    plantilla=plantilla,
                    transcripcion=transcripcion,
                    proveedor_ia=proveedor_ia,
                    estado='borrador',
                    usuario_creacion=usuario
                )
                
                # Agregar al historial
                acta.agregar_historial(
                    'acta_creada',
                    usuario,
                    {
                        'plantilla': plantilla.nombre,
                        'proveedor_ia': proveedor_ia.nombre,
                        'transcripcion_id': transcripcion.id
                    }
                )
                
                logger.info(f"Acta {numero_acta} creada exitosamente para transcripción {transcripcion.id}")
                
                return acta
                
        except Exception as e:
            logger.error(f"Error creando acta: {str(e)}")
            raise ValidationError(f"No se pudo crear el acta: {str(e)}")
    
    @staticmethod
    def generar_numero_acta(tipo_acta: str, fecha: date) -> str:
        """
        Genera un número de acta único y secuencial
        
        Args:
            tipo_acta: Tipo de acta (municipio, sesion, etc.)
            fecha: Fecha de la sesión
            
        Returns:
            Número de acta generado
        """
        try:
            # Buscar el último número para este tipo y año
            año = fecha.year
            mes = fecha.month
            
            # Filtrar actas del mismo tipo y período
            actas_existentes = ActaGenerada.objects.filter(
                plantilla__tipo_acta=tipo_acta,
                fecha_sesion__year=año,
                fecha_sesion__month=mes
            ).order_by('-numero_acta')
            
            if actas_existentes.exists():
                ultimo_numero = actas_existentes.first().numero_acta
                # Extraer secuencial del formato: TIPO-YYYY-MM-NNN
                partes = ultimo_numero.split('-')
                if len(partes) >= 4:
                    try:
                        secuencial = int(partes[-1]) + 1
                    except ValueError:
                        secuencial = 1
                else:
                    secuencial = 1
            else:
                secuencial = 1
            
            # Formatear número de acta
            tipo_codigo = {
                'municipio': 'MUN',
                'sesion': 'SES',
                'extraordinaria': 'EXT',
                'comision': 'COM',
                'ordinaria': 'ORD'
            }.get(tipo_acta, 'GEN')
            
            numero = f"{tipo_codigo}-{año}-{mes:02d}-{secuencial:03d}"
            
            return numero
            
        except Exception as e:
            logger.error(f"Error generando número de acta: {str(e)}")
            # Fallback a formato simple
            timestamp = int(datetime.now().timestamp())
            return f"ACTA-{timestamp}"
    
    @staticmethod
    def generar_titulo_acta(transcripcion: Transcripcion, tipo_acta: str) -> str:
        """
        Genera un título descriptivo para el acta
        
        Args:
            transcripcion: Transcripción base
            tipo_acta: Tipo de acta
            
        Returns:
            Título generado
        """
        try:
            audio = transcripcion.procesamiento_audio
            
            # Extraer información relevante
            tipo_reunion = audio.tipo_reunion.nombre if audio.tipo_reunion else 'Reunión'
            fecha = audio.fecha_procesamiento.strftime('%d/%m/%Y') if audio.fecha_procesamiento else ''
            
            # Buscar información adicional en metadatos
            metadatos = audio.metadatos_procesamiento or {}
            ubicacion = audio.ubicacion or metadatos.get('ubicacion', '')
            
            # Construir título base
            titulo_base = f"Acta de {tipo_reunion}"
            
            if fecha:
                titulo_base += f" del {fecha}"
            
            if ubicacion:
                titulo_base += f" - {ubicacion}"
            
            # Agregar información del tipo de acta
            tipo_descripciones = {
                'municipio': 'Sesión Municipal',
                'sesion': 'Sesión Ordinaria',
                'extraordinaria': 'Sesión Extraordinaria',
                'comision': 'Sesión de Comisión',
                'ordinaria': 'Sesión Ordinaria'
            }
            
            if tipo_acta in tipo_descripciones:
                titulo_base = titulo_base.replace('Reunión', tipo_descripciones[tipo_acta])
            
            return titulo_base
            
        except Exception as e:
            logger.error(f"Error generando título de acta: {str(e)}")
            return f"Acta {tipo_acta} - {datetime.now().strftime('%d/%m/%Y')}"
    
    @staticmethod
    def procesar_acta_asincrono(acta: ActaGenerada) -> str:
        """
        Inicia el procesamiento asíncrono de un acta
        
        Args:
            acta: Acta a procesar
            
        Returns:
            ID de la tarea Celery
        """
        try:
            # Validar que el acta puede ser procesada
            if not acta.puede_procesar:
                raise ValidationError(f"El acta está en estado {acta.estado} y no puede ser procesada")
            
            # Importar task aquí para evitar imports circulares
            from .tasks import procesar_acta_completa
            
            # Ejecutar tarea asíncrona
            task = procesar_acta_completa.delay(acta.id)
            
            # Actualizar acta con información de la tarea
            acta.task_id_celery = task.id
            acta.estado = 'en_cola'
            acta.save()
            
            logger.info(f"Iniciado procesamiento asíncrono para acta {acta.numero_acta} (task: {task.id})")
            
            return task.id
            
        except Exception as e:
            logger.error(f"Error iniciando procesamiento asíncrono: {str(e)}")
            raise ValidationError(f"No se pudo iniciar el procesamiento: {str(e)}")
    
    @staticmethod
    def obtener_estado_procesamiento(acta: ActaGenerada) -> Dict[str, Any]:
        """
        Obtiene el estado actual del procesamiento de un acta
        
        Args:
            acta: Acta a consultar
            
        Returns:
            Diccionario con información del estado
        """
        try:
            estado_info = {
                'acta_id': acta.id,
                'numero_acta': acta.numero_acta,
                'estado': acta.estado,
                'progreso': acta.progreso,
                'task_id': acta.task_id_celery,
                'puede_procesar': acta.puede_procesar,
                'fecha_procesamiento': acta.fecha_procesamiento,
                'mensajes_error': acta.mensajes_error
            }
            
            # Información adicional basada en el estado
            if acta.estado == 'procesando_segmentos':
                segmentos_total = acta.plantilla.configuracionsegmento_set.count()
                segmentos_procesados = len(acta.segmentos_procesados) if acta.segmentos_procesados else 0
                estado_info['segmentos'] = {
                    'total': segmentos_total,
                    'procesados': segmentos_procesados,
                    'pendientes': segmentos_total - segmentos_procesados
                }
            
            if acta.estado in ['revision', 'aprobado', 'publicado']:
                estado_info['metricas'] = acta.metricas_procesamiento
                
            # Estado de la tarea Celery si existe
            if acta.task_id_celery:
                try:
                    from celery.result import AsyncResult
                    task_result = AsyncResult(acta.task_id_celery)
                    estado_info['celery'] = {
                        'estado': task_result.state,
                        'exitoso': task_result.successful(),
                        'info': task_result.info if hasattr(task_result, 'info') else None
                    }
                except:
                    pass
            
            return estado_info
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def validar_transcripcion_para_acta(transcripcion: Transcripcion) -> Tuple[bool, List[str]]:
        """
        Valida si una transcripción es apta para generar actas
        
        Args:
            transcripcion: Transcripción a validar
            
        Returns:
            Tupla (es_valida, lista_errores)
        """
        errores = []
        
        try:
            # Validar que existe conversación
            if not transcripcion.conversacion_json:
                errores.append("La transcripción no tiene datos de conversación")
            else:
                conversacion = transcripcion.conversacion_json.get('conversacion', [])
                if not conversacion:
                    errores.append("La transcripción no contiene segmentos de conversación")
                elif len(conversacion) < 3:
                    errores.append("La transcripción es muy corta (menos de 3 segmentos)")
            
            # Validar audio asociado
            if not hasattr(transcripcion, 'procesamiento_audio'):
                errores.append("La transcripción no tiene audio asociado")
            else:
                audio = transcripcion.procesamiento_audio
                if not audio.duracion_segundos or audio.duracion_segundos < 60:
                    errores.append("El audio es muy corto (menos de 1 minuto)")
            
            # Validar calidad de la transcripción
            if transcripcion.conversacion_json:
                metadata = transcripcion.conversacion_json.get('metadata', {})
                confianza = metadata.get('confianza_promedio', 0)
                if confianza > 0 and confianza < 0.5:
                    errores.append("La calidad de la transcripción es baja (confianza < 50%)")
            
            return len(errores) == 0, errores
            
        except Exception as e:
            logger.error(f"Error validando transcripción: {str(e)}")
            return False, [f"Error en validación: {str(e)}"]
    
    @staticmethod
    def obtener_plantillas_compatibles(transcripcion: Transcripcion) -> List[PlantillaActa]:
        """
        Obtiene plantillas compatibles con una transcripción
        
        Args:
            transcripcion: Transcripción a evaluar
            
        Returns:
            Lista de plantillas compatibles
        """
        try:
            audio = transcripcion.procesamiento_audio
            tipo_reunion = audio.tipo_reunion.nombre if audio.tipo_reunion else None
            
            # Filtrar plantillas activas
            plantillas = PlantillaActa.objects.filter(activa=True)
            
            # Filtrar por tipo de reunión si está disponible
            if tipo_reunion:
                # Buscar plantillas que mencionen el tipo de reunión
                plantillas_compatibles = []
                for plantilla in plantillas:
                    if (tipo_reunion.lower() in plantilla.descripcion.lower() or
                        tipo_reunion.lower() in plantilla.nombre.lower() or
                        plantilla.tipo_acta == 'municipio'):  # Tipo genérico
                        plantillas_compatibles.append(plantilla)
                
                if plantillas_compatibles:
                    return plantillas_compatibles
            
            # Si no hay filtros específicos, devolver todas las activas
            return list(plantillas)
            
        except Exception as e:
            logger.error(f"Error obteniendo plantillas compatibles: {str(e)}")
            return list(PlantillaActa.objects.filter(activa=True))
    
    @staticmethod
    def formatear_duracion(segundos: int) -> str:
        """
        Formatea duración en segundos a formato legible
        
        Args:
            segundos: Duración en segundos
            
        Returns:
            Duración formateada (ej: "1h 30m 45s")
        """
        if not segundos:
            return "0s"
        
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        segundos_resto = segundos % 60
        
        partes = []
        if horas > 0:
            partes.append(f"{horas}h")
        if minutos > 0:
            partes.append(f"{minutos}m")
        if segundos_resto > 0:
            partes.append(f"{segundos_resto}s")
        
        return " ".join(partes)
    
    @staticmethod
    def exportar_acta(acta: ActaGenerada, formato: str = 'txt') -> bytes:
        """
        Exporta un acta en diferentes formatos
        
        Args:
            acta: Acta a exportar
            formato: Formato de exportación ('txt', 'pdf', 'docx')
            
        Returns:
            Contenido del archivo como bytes
        """
        try:
            contenido = acta.contenido_final or acta.contenido_borrador
            if not contenido:
                raise ValidationError("El acta no tiene contenido para exportar")
            
            if formato == 'txt':
                # Agregar metadatos
                header = f"""ACTA: {acta.numero_acta}
TÍTULO: {acta.titulo}
FECHA SESIÓN: {acta.fecha_sesion.strftime('%d/%m/%Y') if acta.fecha_sesion else 'No especificada'}
PLANTILLA: {acta.plantilla.nombre}
ESTADO: {acta.get_estado_display()}
GENERADO: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}

{'='*80}

{contenido}
"""
                return header.encode('utf-8')
            
            elif formato == 'pdf':
                # Aquí se podría integrar con reportlab o weasyprint
                # Por ahora devolver texto plano
                return contenido.encode('utf-8')
            
            elif formato == 'docx':
                # Aquí se podría integrar con python-docx
                # Por ahora devolver texto plano
                return contenido.encode('utf-8')
            
            else:
                raise ValidationError(f"Formato {formato} no soportado")
                
        except Exception as e:
            logger.error(f"Error exportando acta: {str(e)}")
            raise ValidationError(f"No se pudo exportar el acta: {str(e)}")


class PlantillasService:
    """
    Servicio para gestión de plantillas y segmentos
    """
    
    @staticmethod
    def crear_plantilla_desde_template(
        nombre: str,
        tipo_acta: str,
        segmentos_config: List[Dict],
        usuario: User
    ) -> PlantillaActa:
        """
        Crea una plantilla con sus segmentos configurados
        
        Args:
            nombre: Nombre de la plantilla
            tipo_acta: Tipo de acta
            segmentos_config: Lista de configuraciones de segmentos
            usuario: Usuario que crea la plantilla
            
        Returns:
            Plantilla creada
        """
        try:
            with transaction.atomic():
                # Crear plantilla
                plantilla = PlantillaActa.objects.create(
                    nombre=nombre,
                    tipo_acta=tipo_acta,
                    activa=True,
                    usuario_creacion=usuario
                )
                
                # Crear configuraciones de segmentos
                for i, config in enumerate(segmentos_config):
                    segmento = config['segmento']
                    
                    ConfiguracionSegmento.objects.create(
                        plantilla=plantilla,
                        segmento=segmento,
                        orden=i + 1,
                        activo=True,
                        prompt_override=config.get('prompt_override'),
                        parametros_override=config.get('parametros_override')
                    )
                
                logger.info(f"Plantilla {nombre} creada con {len(segmentos_config)} segmentos")
                
                return plantilla
                
        except Exception as e:
            logger.error(f"Error creando plantilla: {str(e)}")
            raise ValidationError(f"No se pudo crear la plantilla: {str(e)}")
    
    @staticmethod
    def duplicar_plantilla(plantilla_origen: PlantillaActa, nuevo_nombre: str, usuario: User) -> PlantillaActa:
        """
        Duplica una plantilla existente con todas sus configuraciones
        
        Args:
            plantilla_origen: Plantilla a duplicar
            nuevo_nombre: Nombre para la nueva plantilla
            usuario: Usuario que duplica
            
        Returns:
            Nueva plantilla duplicada
        """
        try:
            with transaction.atomic():
                # Crear nueva plantilla
                nueva_plantilla = PlantillaActa.objects.create(
                    nombre=nuevo_nombre,
                    descripcion=f"Copia de: {plantilla_origen.descripcion}",
                    tipo_acta=plantilla_origen.tipo_acta,
                    prompt_global=plantilla_origen.prompt_global,
                    activa=False,  # Crear inactiva por defecto
                    usuario_creacion=usuario
                )
                
                # Duplicar configuraciones de segmentos
                configuraciones_origen = plantilla_origen.configuracionsegmento_set.all().order_by('orden')
                
                for config_origen in configuraciones_origen:
                    ConfiguracionSegmento.objects.create(
                        plantilla=nueva_plantilla,
                        segmento=config_origen.segmento,
                        orden=config_origen.orden,
                        activo=config_origen.activo,
                        prompt_override=config_origen.prompt_override,
                        parametros_override=config_origen.parametros_override
                    )
                
                logger.info(f"Plantilla {nuevo_nombre} duplicada desde {plantilla_origen.nombre}")
                
                return nueva_plantilla
                
        except Exception as e:
            logger.error(f"Error duplicando plantilla: {str(e)}")
            raise ValidationError(f"No se pudo duplicar la plantilla: {str(e)}")


class EstadisticasService:
    """
    Servicio para generación de estadísticas y reportes
    """
    
    @staticmethod
    def obtener_resumen_dashboard() -> Dict[str, Any]:
        """
        Obtiene resumen para el dashboard principal
        
        Returns:
            Diccionario con estadísticas del dashboard
        """
        try:
            from django.db.models import Count, Q
            
            # Estadísticas básicas
            total_actas = ActaGenerada.objects.count()
            actas_procesando = ActaGenerada.objects.filter(
                estado__in=['en_cola', 'procesando', 'procesando_segmentos', 'unificando']
            ).count()
            actas_revision = ActaGenerada.objects.filter(estado='revision').count()
            actas_publicadas = ActaGenerada.objects.filter(estado='publicado').count()
            
            # Estadísticas por proveedor
            proveedores_stats = (
                ActaGenerada.objects
                .values('proveedor_ia__nombre')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
            
            # Actividad reciente (últimos 7 días)
            from datetime import timedelta
            fecha_limite = timezone.now() - timedelta(days=7)
            
            actividad_reciente = ActaGenerada.objects.filter(
                fecha_creacion__gte=fecha_limite
            ).count()
            
            # Plantillas más utilizadas
            plantillas_populares = (
                ActaGenerada.objects
                .values('plantilla__nombre')
                .annotate(count=Count('id'))
                .order_by('-count')[:5]
            )
            
            return {
                'totales': {
                    'actas': total_actas,
                    'procesando': actas_procesando,
                    'revision': actas_revision,
                    'publicadas': actas_publicadas
                },
                'proveedores': list(proveedores_stats),
                'actividad_reciente': actividad_reciente,
                'plantillas_populares': list(plantillas_populares)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen dashboard: {str(e)}")
            return {'error': str(e)}