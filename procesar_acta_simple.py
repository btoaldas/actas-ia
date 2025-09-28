"""
Tarea Celery simple para procesar actas generadas
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=2)
def procesar_acta_simple_task(self, acta_id):
    """
    Tarea simple para procesar un acta - simulación con IA
    """
    try:
        from apps.generador_actas.models import ActaGenerada, ProveedorIA
        
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
        import time
        total_segmentos = 5
        
        for i in range(1, total_segmentos + 1):
            logger.info(f"📝 Procesando segmento {i}/{total_segmentos}")
            
            # Simular tiempo de procesamiento
            time.sleep(2)
            
            # Simular llamada a IA
            segmento_content = f"""
            ### Segmento {i} - {acta.numero_acta}
            **Fecha:** {acta.fecha_sesion}
            **Transcripción:** {acta.transcripcion.titulo if acta.transcripcion else 'N/A'}
            
            Contenido procesado con {acta.proveedor_ia.nombre} para el segmento {i}.
            Este es contenido simulado generado por IA para demostrar el flujo de procesamiento.
            """
            
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
**Transcripción Base:** {acta.transcripcion.titulo if acta.transcripcion else 'N/A'}
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
        acta.contenido_html = contenido_final.replace('\n', '<br>').replace('#', '<h1>').replace('**', '<strong>')
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