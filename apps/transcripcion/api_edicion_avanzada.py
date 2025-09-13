"""
APIs avanzadas para edición completa de transcripciones
Permite al usuario editar todos los aspectos de la transcripción:
- Segmentos de conversación (texto, tiempos, hablantes)
- Hablantes (nombres, mapeo, colores)
- Estadísticas y metadatos
- Estructura JSON completa
"""

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import logging

from .models import Transcripcion, HistorialEdicion, ConfiguracionHablante
from .logging_helper import log_transcripcion_edicion, log_transcripcion_error

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET"])
def api_obtener_estructura_completa(request, transcripcion_id):
    """
    Obtiene la estructura JSON completa de la transcripción
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        # Obtener estructura completa
        estructura = transcripcion.conversacion_json or {}
        
        # Asegurar que tiene la estructura esperada
        if not isinstance(estructura, dict):
            estructura = {"cabecera": {}, "conversacion": [], "texto_estructurado": "", "metadata": {}}
        
        # Validar campos requeridos
        if 'cabecera' not in estructura:
            estructura['cabecera'] = {}
        if 'conversacion' not in estructura:
            estructura['conversacion'] = []
        if 'texto_estructurado' not in estructura:
            estructura['texto_estructurado'] = ""
        if 'metadata' not in estructura:
            estructura['metadata'] = {}
            
        return JsonResponse({
            'exito': True,
            'estructura': estructura,
            'puede_editar': transcripcion.esta_completado,
            'estado': transcripcion.estado,
            'total_segmentos': len(estructura.get('conversacion', [])),
            'hablantes_disponibles': list(estructura.get('cabecera', {}).get('mapeo_hablantes', {}).values())
        })
        
    except Exception as e:
        logger.error(f"Error en api_obtener_estructura_completa: {str(e)}")
        return JsonResponse({
            'exito': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_editar_segmento_avanzado(request, transcripcion_id):
    """
    Edita un segmento específico con validación completa
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if not transcripcion.esta_completado:
            return JsonResponse({
                'exito': False,
                'error': 'Solo se pueden editar transcripciones completadas'
            }, status=400)
        
        data = json.loads(request.body)
        indice_segmento = data.get('indice')
        nuevo_texto = data.get('texto', '').strip()
        nuevo_hablante = data.get('hablante', '').strip()
        nuevo_inicio = float(data.get('inicio', 0))
        nuevo_fin = float(data.get('fin', 0))
        
        # Validaciones
        if indice_segmento is None:
            return JsonResponse({'exito': False, 'error': 'Índice de segmento requerido'}, status=400)
        
        if nuevo_inicio >= nuevo_fin:
            return JsonResponse({'exito': False, 'error': 'El tiempo de inicio debe ser menor al tiempo de fin'}, status=400)
            
        if not nuevo_texto:
            return JsonResponse({'exito': False, 'error': 'El texto no puede estar vacío'}, status=400)
            
        if not nuevo_hablante:
            return JsonResponse({'exito': False, 'error': 'El hablante no puede estar vacío'}, status=400)
        
        # Obtener estructura actual
        estructura = transcripcion.conversacion_json or {}
        if 'conversacion' not in estructura:
            estructura['conversacion'] = []
            
        conversacion = estructura['conversacion']
        
        # Validar índice
        if indice_segmento < 0 or indice_segmento >= len(conversacion):
            return JsonResponse({'exito': False, 'error': 'Índice de segmento inválido'}, status=400)
        
        # Guardar estado anterior para historial
        segmento_anterior = conversacion[indice_segmento].copy()
        
        # Actualizar segmento
        conversacion[indice_segmento].update({
            'texto': nuevo_texto,
            'hablante': nuevo_hablante,
            'inicio': nuevo_inicio,
            'fin': nuevo_fin,
            'duracion': round(nuevo_fin - nuevo_inicio, 2),
            'editado': True,
            'fecha_edicion': timezone.now().isoformat()
        })
        
        # Regenerar texto estructurado
        estructura['texto_estructurado'] = _generar_texto_estructurado(conversacion)
        
        # Actualizar metadata
        if 'metadata' not in estructura:
            estructura['metadata'] = {}
        estructura['metadata'].update({
            'fecha_ultima_edicion': timezone.now().isoformat(),
            'usuario_ultima_edicion': request.user.username,
            'total_segmentos': len(conversacion),
            'segmentos_editados': len([s for s in conversacion if s.get('editado', False)])
        })
        
        # Guardar cambios
        transcripcion.conversacion_json = estructura
        transcripcion.save()
        
        # Registrar en historial
        HistorialEdicion.objects.create(
            transcripcion=transcripcion,
            usuario=request.user,
            tipo_edicion='edicion_segmento',
            descripcion=f'Editó segmento {indice_segmento}: "{segmento_anterior.get("texto", "")[:50]}..." → "{nuevo_texto[:50]}..."',
            datos_anteriores={'segmento': segmento_anterior, 'indice': indice_segmento},
            datos_nuevos={'segmento': conversacion[indice_segmento], 'indice': indice_segmento}
        )
        
        log_transcripcion_edicion(
            transcripcion, 
            request.user, 
            'editar_segmento_avanzado',
            {'indice': indice_segmento, 'hablante': nuevo_hablante}
        )
        
        return JsonResponse({
            'exito': True,
            'segmento_actualizado': conversacion[indice_segmento],
            'texto_estructurado': estructura['texto_estructurado'],
            'metadata': estructura['metadata']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'exito': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en api_editar_segmento_avanzado: {str(e)}")
        log_transcripcion_error(transcripcion, 'api_error', str(e), {'api': 'editar_segmento_avanzado'})
        return JsonResponse({'exito': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_agregar_segmento_avanzado(request, transcripcion_id):
    """
    Agrega un nuevo segmento a la conversación
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if not transcripcion.esta_completado:
            return JsonResponse({
                'exito': False,
                'error': 'Solo se pueden editar transcripciones completadas'
            }, status=400)
        
        data = json.loads(request.body)
        texto = data.get('texto', '').strip()
        hablante = data.get('hablante', '').strip()
        inicio = float(data.get('inicio', 0))
        fin = float(data.get('fin', 0))
        posicion = data.get('posicion', None)  # None = al final
        
        # Validaciones
        if inicio >= fin:
            return JsonResponse({'exito': False, 'error': 'El tiempo de inicio debe ser menor al tiempo de fin'}, status=400)
            
        if not texto:
            return JsonResponse({'exito': False, 'error': 'El texto no puede estar vacío'}, status=400)
            
        if not hablante:
            return JsonResponse({'exito': False, 'error': 'El hablante no puede estar vacío'}, status=400)
        
        # Obtener estructura actual
        estructura = transcripcion.conversacion_json or {}
        if 'conversacion' not in estructura:
            estructura['conversacion'] = []
            
        conversacion = estructura['conversacion']
        
        # Crear nuevo segmento
        nuevo_segmento = {
            'inicio': inicio,
            'fin': fin,
            'duracion': round(fin - inicio, 2),
            'hablante': hablante,
            'hablante_id': f"MANUAL_{hablante.upper()}",
            'texto': texto,
            'editado': True,
            'fecha_creacion': timezone.now().isoformat()
        }
        
        # Insertar en la posición correcta
        if posicion is None or posicion >= len(conversacion):
            conversacion.append(nuevo_segmento)
            posicion_final = len(conversacion) - 1
        else:
            conversacion.insert(posicion, nuevo_segmento)
            posicion_final = posicion
        
        # Regenerar texto estructurado
        estructura['texto_estructurado'] = _generar_texto_estructurado(conversacion)
        
        # Actualizar metadata
        if 'metadata' not in estructura:
            estructura['metadata'] = {}
        estructura['metadata'].update({
            'fecha_ultima_edicion': timezone.now().isoformat(),
            'usuario_ultima_edicion': request.user.username,
            'total_segmentos': len(conversacion),
            'segmentos_editados': len([s for s in conversacion if s.get('editado', False)])
        })
        
        # Guardar cambios
        transcripcion.conversacion_json = estructura
        transcripcion.save()
        
        # Registrar en historial
        HistorialEdicion.objects.create(
            transcripcion=transcripcion,
            usuario=request.user,
            tipo_edicion='agregar_segmento',
            descripcion=f'Agregó nuevo segmento en posición {posicion_final}: "{texto[:50]}..."',
            datos_anteriores={'total_segmentos': len(conversacion) - 1},
            datos_nuevos={'segmento': nuevo_segmento, 'posicion': posicion_final, 'total_segmentos': len(conversacion)}
        )
        
        log_transcripcion_edicion(
            transcripcion, 
            request.user, 
            'agregar_segmento',
            {'posicion': posicion_final, 'hablante': hablante}
        )
        
        return JsonResponse({
            'exito': True,
            'segmento_creado': nuevo_segmento,
            'posicion': posicion_final,
            'total_segmentos': len(conversacion),
            'texto_estructurado': estructura['texto_estructurado'],
            'metadata': estructura['metadata']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'exito': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en api_agregar_segmento_avanzado: {str(e)}")
        log_transcripcion_error(transcripcion, 'api_error', str(e), {'api': 'agregar_segmento_avanzado'})
        return JsonResponse({'exito': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_eliminar_segmento_avanzado(request, transcripcion_id):
    """
    Elimina un segmento específico de la conversación
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if not transcripcion.esta_completado:
            return JsonResponse({
                'exito': False,
                'error': 'Solo se pueden editar transcripciones completadas'
            }, status=400)
        
        data = json.loads(request.body)
        indice_segmento = data.get('indice')
        
        # Validaciones
        if indice_segmento is None:
            return JsonResponse({'exito': False, 'error': 'Índice de segmento requerido'}, status=400)
        
        # Obtener estructura actual
        estructura = transcripcion.conversacion_json or {}
        if 'conversacion' not in estructura:
            estructura['conversacion'] = []
            
        conversacion = estructura['conversacion']
        
        # Validar índice
        if indice_segmento < 0 or indice_segmento >= len(conversacion):
            return JsonResponse({'exito': False, 'error': 'Índice de segmento inválido'}, status=400)
        
        # Guardar segmento para historial antes de eliminar
        segmento_eliminado = conversacion[indice_segmento].copy()
        
        # Eliminar segmento
        del conversacion[indice_segmento]
        
        # Regenerar texto estructurado
        estructura['texto_estructurado'] = _generar_texto_estructurado(conversacion)
        
        # Actualizar metadata
        if 'metadata' not in estructura:
            estructura['metadata'] = {}
        estructura['metadata'].update({
            'fecha_ultima_edicion': timezone.now().isoformat(),
            'usuario_ultima_edicion': request.user.username,
            'total_segmentos': len(conversacion),
            'segmentos_editados': len([s for s in conversacion if s.get('editado', False)])
        })
        
        # Guardar cambios
        transcripcion.conversacion_json = estructura
        transcripcion.save()
        
        # Registrar en historial
        HistorialEdicion.objects.create(
            transcripcion=transcripcion,
            usuario=request.user,
            tipo_edicion='eliminar_segmento',
            descripcion=f'Eliminó segmento {indice_segmento}: "{segmento_eliminado.get("texto", "")[:50]}..."',
            datos_anteriores={'segmento': segmento_eliminado, 'indice': indice_segmento, 'total_segmentos': len(conversacion) + 1},
            datos_nuevos={'total_segmentos': len(conversacion)}
        )
        
        log_transcripcion_edicion(
            transcripcion, 
            request.user, 
            'eliminar_segmento',
            {'indice': indice_segmento}
        )
        
        return JsonResponse({
            'exito': True,
            'segmento_eliminado': segmento_eliminado,
            'total_segmentos': len(conversacion),
            'texto_estructurado': estructura['texto_estructurado'],
            'metadata': estructura['metadata']
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'exito': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en api_eliminar_segmento_avanzado: {str(e)}")
        log_transcripcion_error(transcripcion, 'api_error', str(e), {'api': 'eliminar_segmento_avanzado'})
        return JsonResponse({'exito': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_gestionar_hablantes_avanzado(request, transcripcion_id):
    """
    Gestiona los hablantes: agregar, editar, eliminar, renombrar
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if not transcripcion.esta_completado:
            return JsonResponse({
                'exito': False,
                'error': 'Solo se pueden editar transcripciones completadas'
            }, status=400)
        
        data = json.loads(request.body)
        accion = data.get('accion')  # 'agregar', 'editar', 'eliminar', 'renombrar'
        
        # Obtener estructura actual
        estructura = transcripcion.conversacion_json or {}
        if 'cabecera' not in estructura:
            estructura['cabecera'] = {}
        if 'mapeo_hablantes' not in estructura['cabecera']:
            estructura['cabecera']['mapeo_hablantes'] = {}
        if 'conversacion' not in estructura:
            estructura['conversacion'] = []
            
        mapeo_hablantes = estructura['cabecera']['mapeo_hablantes']
        conversacion = estructura['conversacion']
        
        if accion == 'agregar':
            nuevo_nombre = data.get('nombre', '').strip()
            nuevo_id = data.get('id', f"SPEAKER_{len(mapeo_hablantes):02d}")
            
            if not nuevo_nombre:
                return JsonResponse({'exito': False, 'error': 'El nombre del hablante no puede estar vacío'}, status=400)
            
            if nuevo_nombre in mapeo_hablantes.values():
                return JsonResponse({'exito': False, 'error': 'Ya existe un hablante con ese nombre'}, status=400)
            
            mapeo_hablantes[nuevo_id] = nuevo_nombre
            
            descripcion = f'Agregó hablante: {nuevo_nombre} ({nuevo_id})'
            
        elif accion == 'editar':
            hablante_id = data.get('id')
            nuevo_nombre = data.get('nuevo_nombre', '').strip()
            
            if not hablante_id or hablante_id not in mapeo_hablantes:
                return JsonResponse({'exito': False, 'error': 'Hablante no encontrado'}, status=400)
            
            if not nuevo_nombre:
                return JsonResponse({'exito': False, 'error': 'El nuevo nombre no puede estar vacío'}, status=400)
            
            nombre_anterior = mapeo_hablantes[hablante_id]
            mapeo_hablantes[hablante_id] = nuevo_nombre
            
            # Actualizar conversación
            for segmento in conversacion:
                if segmento.get('hablante') == nombre_anterior:
                    segmento['hablante'] = nuevo_nombre
                    segmento['editado'] = True
            
            descripcion = f'Renombró hablante: {nombre_anterior} → {nuevo_nombre}'
            
        elif accion == 'eliminar':
            hablante_id = data.get('id')
            
            if not hablante_id or hablante_id not in mapeo_hablantes:
                return JsonResponse({'exito': False, 'error': 'Hablante no encontrado'}, status=400)
            
            # Verificar si el hablante está en uso
            nombre_hablante = mapeo_hablantes[hablante_id]
            segmentos_con_hablante = [s for s in conversacion if s.get('hablante') == nombre_hablante]
            
            if segmentos_con_hablante:
                return JsonResponse({
                    'exito': False, 
                    'error': f'No se puede eliminar el hablante {nombre_hablante} porque está siendo usado en {len(segmentos_con_hablante)} segmento(s)'
                }, status=400)
            
            del mapeo_hablantes[hablante_id]
            descripcion = f'Eliminó hablante: {nombre_hablante} ({hablante_id})'
            
        else:
            return JsonResponse({'exito': False, 'error': 'Acción no válida'}, status=400)
        
        # Regenerar texto estructurado si cambió la conversación
        estructura['texto_estructurado'] = _generar_texto_estructurado(conversacion)
        
        # Actualizar metadata
        if 'metadata' not in estructura:
            estructura['metadata'] = {}
        estructura['metadata'].update({
            'fecha_ultima_edicion': timezone.now().isoformat(),
            'usuario_ultima_edicion': request.user.username,
            'total_hablantes': len(mapeo_hablantes),
            'hablantes_disponibles': list(mapeo_hablantes.values())
        })
        
        # Guardar cambios
        transcripcion.conversacion_json = estructura
        transcripcion.save()
        
        # Registrar en historial
        HistorialEdicion.objects.create(
            transcripcion=transcripcion,
            usuario=request.user,
            tipo_edicion=f'hablantes_{accion}',
            descripcion=descripcion,
            datos_anteriores={'mapeo_anterior': dict(mapeo_hablantes) if accion != 'agregar' else {}},
            datos_nuevos={'mapeo_nuevo': dict(mapeo_hablantes)}
        )
        
        log_transcripcion_edicion(
            transcripcion, 
            request.user, 
            f'hablantes_{accion}',
            {'accion': accion}
        )
        
        return JsonResponse({
            'exito': True,
            'mapeo_hablantes': mapeo_hablantes,
            'hablantes_disponibles': list(mapeo_hablantes.values()),
            'total_hablantes': len(mapeo_hablantes),
            'texto_estructurado': estructura['texto_estructurado'],
            'metadata': estructura['metadata'],
            'descripcion': descripcion
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'exito': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en api_gestionar_hablantes_avanzado: {str(e)}")
        log_transcripcion_error(transcripcion, 'api_error', str(e), {'api': 'gestionar_hablantes_avanzado'})
        return JsonResponse({'exito': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_guardar_estructura_completa(request, transcripcion_id):
    """
    Guarda la estructura JSON completa editada manualmente
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if not transcripcion.esta_completado:
            return JsonResponse({
                'exito': False,
                'error': 'Solo se pueden editar transcripciones completadas'
            }, status=400)
        
        data = json.loads(request.body)
        nueva_estructura = data.get('estructura')
        
        if not nueva_estructura or not isinstance(nueva_estructura, dict):
            return JsonResponse({'exito': False, 'error': 'Estructura JSON inválida'}, status=400)
        
        # Validar estructura mínima requerida
        campos_requeridos = ['cabecera', 'conversacion', 'texto_estructurado', 'metadata']
        for campo in campos_requeridos:
            if campo not in nueva_estructura:
                return JsonResponse({'exito': False, 'error': f'Campo requerido faltante: {campo}'}, status=400)
        
        # Validar conversación
        conversacion = nueva_estructura.get('conversacion', [])
        if not isinstance(conversacion, list):
            return JsonResponse({'exito': False, 'error': 'La conversación debe ser una lista'}, status=400)
        
        # Validar cada segmento
        for i, segmento in enumerate(conversacion):
            campos_segmento = ['inicio', 'fin', 'hablante', 'texto']
            for campo in campos_segmento:
                if campo not in segmento:
                    return JsonResponse({'exito': False, 'error': f'Segmento {i}: campo requerido faltante: {campo}'}, status=400)
            
            if segmento['inicio'] >= segmento['fin']:
                return JsonResponse({'exito': False, 'error': f'Segmento {i}: tiempo inicio debe ser menor que tiempo fin'}, status=400)
        
        # Guardar estado anterior para historial
        estructura_anterior = transcripcion.conversacion_json or {}
        
        # Actualizar metadata
        nueva_estructura['metadata'].update({
            'fecha_ultima_edicion': timezone.now().isoformat(),
            'usuario_ultima_edicion': request.user.username,
            'total_segmentos': len(conversacion),
            'edicion_manual': True
        })
        
        # Guardar cambios
        transcripcion.conversacion_json = nueva_estructura
        transcripcion.save()
        
        # Registrar en historial
        HistorialEdicion.objects.create(
            transcripcion=transcripcion,
            usuario=request.user,
            tipo_edicion='edicion_completa',
            descripcion='Editó la estructura JSON completa manualmente',
            datos_anteriores={'estructura': estructura_anterior},
            datos_nuevos={'estructura': nueva_estructura}
        )
        
        log_transcripcion_edicion(
            transcripcion, 
            request.user, 
            'edicion_completa',
            {'segmentos': len(conversacion)}
        )
        
        return JsonResponse({
            'exito': True,
            'estructura_guardada': nueva_estructura,
            'total_segmentos': len(conversacion),
            'mensaje': 'Estructura JSON guardada exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'exito': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f"Error en api_guardar_estructura_completa: {str(e)}")
        log_transcripcion_error(transcripcion, 'api_error', str(e), {'api': 'guardar_estructura_completa'})
        return JsonResponse({'exito': False, 'error': str(e)}, status=500)


def _generar_texto_estructurado(conversacion):
    """
    Genera el texto estructurado en formato MM:SS,Hablante,Texto
    """
    lineas = []
    for segmento in conversacion:
        inicio = segmento.get('inicio', 0)
        minutos = int(inicio // 60)
        segundos = int(inicio % 60)
        tiempo_formateado = f"{minutos:02d}:{segundos:02d}"
        
        hablante = segmento.get('hablante', 'Desconocido')
        texto = segmento.get('texto', '').replace('\n', ' ').replace('\r', ' ')
        
        lineas.append(f"{tiempo_formateado},{hablante},{texto}")
    
    return '\n'.join(lineas)