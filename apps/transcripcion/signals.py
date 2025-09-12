from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Transcripcion, ConfiguracionHablante
from .logging_helper import log_transcripcion_accion
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transcripcion)
def transcripcion_post_save(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar una transcripción
    """
    try:
        if created:
            log_transcripcion_accion(
                instance,
                'creacion',
                {
                    'usuario_creacion': instance.usuario_creacion.username if instance.usuario_creacion else 'Sistema',
                    'configuracion_id': instance.configuracion_utilizada.id if instance.configuracion_utilizada else None
                }
            )
        else:
            # Detectar cambios importantes de estado
            if hasattr(instance, '_state_changed'):
                log_transcripcion_accion(
                    instance,
                    'cambio_estado',
                    {
                        'estado_anterior': instance._state_changed.get('estado_anterior'),
                        'estado_nuevo': instance.estado,
                        'progreso': instance.progreso_porcentaje
                    }
                )
    
    except Exception as e:
        logger.error(f"Error en signal post_save de Transcripcion: {str(e)}")


@receiver(pre_delete, sender=Transcripcion)
def transcripcion_pre_delete(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de eliminar una transcripción
    """
    try:
        log_transcripcion_accion(
            instance,
            'eliminacion',
            {
                'estado_al_eliminar': instance.estado,
                'editado_manualmente': instance.editado_manualmente,
                'numero_segmentos': instance.numero_segmentos,
                'numero_hablantes': instance.numero_hablantes
            }
        )
    except Exception as e:
        logger.error(f"Error en signal pre_delete de Transcripcion: {str(e)}")


@receiver(post_save, sender=ConfiguracionHablante)
def configuracion_hablante_post_save(sender, instance, created, **kwargs):
    """
    Signal para actualizar estadísticas cuando se configura un hablante
    """
    try:
        if created or instance.confirmado_por_usuario:
            # Recalcular estadísticas del hablante
            transcripcion = instance.transcripcion
            conversacion = transcripcion.conversacion_json
            
            tiempo_total = 0
            intervenciones = 0
            palabras_total = 0
            
            for segmento in conversacion:
                if segmento.get('hablante') == instance.speaker_id:
                    tiempo_total += segmento.get('duracion', 0)
                    intervenciones += 1
                    palabras_total += len(segmento.get('texto', '').split())
            
            # Actualizar estadísticas
            instance.tiempo_total_hablando = tiempo_total
            instance.numero_intervenciones = intervenciones
            instance.palabras_promedio_por_intervencion = (
                palabras_total / intervenciones if intervenciones > 0 else 0
            )
            
            # Evitar recursión
            ConfiguracionHablante.objects.filter(id=instance.id).update(
                tiempo_total_hablando=instance.tiempo_total_hablando,
                numero_intervenciones=instance.numero_intervenciones,
                palabras_promedio_por_intervencion=instance.palabras_promedio_por_intervencion
            )
            
            log_transcripcion_accion(
                transcripcion,
                'configuracion_hablante',
                {
                    'speaker_id': instance.speaker_id,
                    'nombre_real': instance.nombre_real,
                    'accion': 'creacion' if created else 'actualizacion',
                    'estadisticas': {
                        'tiempo_total': tiempo_total,
                        'intervenciones': intervenciones,
                        'palabras_promedio': instance.palabras_promedio_por_intervencion
                    }
                }
            )
    
    except Exception as e:
        logger.error(f"Error en signal post_save de ConfiguracionHablante: {str(e)}")
