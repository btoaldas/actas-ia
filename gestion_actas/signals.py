"""
Señales para el módulo gestion_actas
Maneja la creación automática de GestionActa cuando se crea una ActaGenerada
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from apps.generador_actas.models import ActaGenerada
from gestion_actas.models import GestionActa, EstadoGestionActa
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ActaGenerada)
def crear_gestion_acta_automatica(sender, instance, created, **kwargs):
    """
    Crear automáticamente una GestionActa cuando se crea una ActaGenerada
    o actualizar el contenido cuando se modifica
    """
    try:
        contenido_disponible = instance.contenido_html or instance.contenido_final or instance.contenido_borrador or ''
        
        # Obtener o crear GestionActa
        if created:
            # Creación nueva
            if not hasattr(instance, 'gestion'):
                estado_inicial = EstadoGestionActa.objects.get(codigo='en_edicion')
                
                gestion_acta = GestionActa.objects.create(
                    acta_generada=instance,
                    estado=estado_inicial,
                    contenido_editado=contenido_disponible,
                    contenido_original_backup=contenido_disponible,
                    usuario_editor=instance.usuario_creacion,
                    version=1,
                    cambios_realizados={
                        'creado_automaticamente': True,
                        'fecha_creacion_automatica': timezone.now().isoformat(),
                        'estado_acta_original': instance.estado,
                        'contenido_inicial_length': len(contenido_disponible)
                    },
                    observaciones=f'Creado automáticamente al generar acta. Estado original: {instance.estado}. Contenido: {len(contenido_disponible)} chars'
                )
                
                logger.info(
                    f'✅ Gestión creada automáticamente para ActaGenerada ID: {instance.pk} '
                    f'- "{instance.titulo}" (Gestión ID: {gestion_acta.pk}) '
                    f'- Contenido: {len(contenido_disponible)} chars'
                )
        else:
            # Actualización existente - sincronizar contenido  
            # TAMBIÉN revisar si es una GestionActa recién creada vacía que necesita contenido
            try:
                gestion_acta = GestionActa.objects.get(acta_generada=instance)
                contenido_nuevo = contenido_disponible
                
                # Condición mejorada: actualizar si hay contenido nuevo Y si GestionActa está vacío o es diferente
                necesita_actualizacion = (
                    contenido_nuevo and (
                        not gestion_acta.contenido_editado or  # GestionActa vacío
                        len(gestion_acta.contenido_editado.strip()) == 0 or  # Solo espacios
                        contenido_nuevo != gestion_acta.contenido_editado  # Contenido diferente
                    )
                )
                
                if necesita_actualizacion:
                    # Guardar backup si no existe
                    if not gestion_acta.contenido_original_backup:
                        gestion_acta.contenido_original_backup = gestion_acta.contenido_editado or contenido_nuevo
                    
                    gestion_acta.contenido_editado = contenido_nuevo
                    gestion_acta.fecha_ultima_edicion = timezone.now()
                    
                    # Actualizar cambios realizados
                    cambios = gestion_acta.cambios_realizados or {}
                    cambios['ultima_sincronizacion'] = timezone.now().isoformat()
                    cambios['contenido_actualizado_desde_generador'] = True
                    cambios['razon_actualizacion'] = 'contenido_vacio' if not gestion_acta.contenido_editado else 'contenido_diferente'
                    cambios['contenido_length'] = len(contenido_nuevo)
                    gestion_acta.cambios_realizados = cambios
                    
                    gestion_acta.save()
                    
                    logger.info(
                        f'🔄 Contenido sincronizado para GestionActa ID: {gestion_acta.pk} '
                        f'desde ActaGenerada ID: {instance.pk} - {len(contenido_nuevo)} chars'
                    )
                    
            except GestionActa.DoesNotExist:
                logger.warning(
                    f'⚠️ GestionActa no existe para ActaGenerada ID: {instance.pk} '
                    f'durante actualización. Se creará automáticamente.'
                )
                # Crear si no existe
                estado_inicial = EstadoGestionActa.objects.get(codigo='en_edicion')
                
                gestion_acta = GestionActa.objects.create(
                    acta_generada=instance,
                    estado=estado_inicial,
                    contenido_editado=instance.contenido_html or instance.contenido_final or instance.contenido_borrador or '',
                    contenido_original_backup=instance.contenido_html or instance.contenido_final or instance.contenido_borrador or '',
                    usuario_editor=instance.usuario_creacion,
                    version=1,
                    cambios_realizados={
                        'creado_en_actualizacion': True,
                        'fecha_creacion': timezone.now().isoformat(),
                        'estado_acta_original': instance.estado
                    },
                    observaciones=f'Creado durante actualización de ActaGenerada. Estado: {instance.estado}'
                )
                
                logger.info(
                    f'✅ Gestión creada durante actualización para ActaGenerada ID: {instance.pk}'
                )
            
    except EstadoGestionActa.DoesNotExist:
        logger.error(
            f'❌ Error: No se encontró el estado "en_edicion" para ActaGenerada ID: {instance.pk}'
        )
    except Exception as e:
        logger.error(
            f'❌ Error al crear gestión automática para ActaGenerada ID: {instance.pk} - {str(e)}'
        )