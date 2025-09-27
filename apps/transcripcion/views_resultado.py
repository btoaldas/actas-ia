@login_required
def vista_resultado_transcripcion(request, transcripcion_id):
    """
    Vista que muestra el resultado completo de una transcripción
    con timeline, texto formateado, hablantes y estadísticas
    """
    try:
        transcripcion = get_object_or_404(
            Transcripcion.objects.select_related(
                'procesamiento_audio', 
                'configuracion', 
                'usuario_creacion'
            ),
            id=transcripcion_id
        )
        
        # Verificar que está completada
        if transcripcion.estado != EstadoTranscripcion.COMPLETADO:
            messages.warning(request, 'La transcripción aún no está completada.')
            return redirect('transcripcion:audios_listos')
        
        # Procesar datos para la vista
        resultado_final = transcripcion.resultado_final or {}
        segmentos = resultado_final.get('segmentos_combinados', [])
        hablantes = transcripcion.hablantes_detectados or {}
        
        # Estadísticas básicas
        estadisticas = {
            'duracion_total': transcripcion.duracion_total,
            'num_palabras': len(transcripcion.texto_completo.split()) if transcripcion.texto_completo else 0,
            'num_segmentos': len(segmentos),
            'num_hablantes': transcripcion.num_hablantes,
            'duracion_procesamiento': None
        }
        
        if transcripcion.tiempo_inicio_proceso and transcripcion.tiempo_fin_proceso:
            duracion = transcripcion.tiempo_fin_proceso - transcripcion.tiempo_inicio_proceso
            estadisticas['duracion_procesamiento'] = duracion.total_seconds()
        
        # Preparar timeline para visualización
        timeline_data = []
        for i, segmento in enumerate(segmentos):
            timeline_data.append({
                'id': i,
                'inicio': segmento.get('inicio', 0),
                'fin': segmento.get('fin', 0),
                'duracion': segmento.get('duracion', 0),
                'hablante': segmento.get('hablante', 'Desconocido'),
                'hablante_nombre': hablantes.get(segmento.get('hablante'), segmento.get('hablante')),
                'texto': segmento.get('texto', ''),
                'confianza': segmento.get('confianza', 0.0)
            })
        
        # Estadísticas por hablante
        estadisticas_hablantes = {}
        for hablante_id, hablante_nombre in hablantes.items():
            segmentos_hablante = [s for s in segmentos if s.get('hablante') == hablante_id]
            tiempo_total = sum(s.get('duracion', 0) for s in segmentos_hablante)
            palabras_hablante = sum(len(s.get('texto', '').split()) for s in segmentos_hablante)
            
            estadisticas_hablantes[hablante_id] = {
                'nombre': hablante_nombre,
                'tiempo_total': tiempo_total,
                'porcentaje_tiempo': (tiempo_total / estadisticas['duracion_total'] * 100) if estadisticas['duracion_total'] > 0 else 0,
                'num_segmentos': len(segmentos_hablante),
                'num_palabras': palabras_hablante,
                'promedio_palabras_segmento': palabras_hablante / len(segmentos_hablante) if segmentos_hablante else 0
            }
        
        context = {
            'transcripcion': transcripcion,
            'timeline_data': timeline_data,
            'estadisticas': estadisticas,
            'estadisticas_hablantes': estadisticas_hablantes,
            'hablantes': hablantes,
            'configuracion_usada': transcripcion.configuracion,
            'datos_whisper': transcripcion.datos_whisper or {},
            'datos_pyannote': transcripcion.datos_pyannote or {},
            'puede_editar': True,
            'archivo_audio_disponible': bool(
                transcripcion.procesamiento_audio.archivo_audio or 
                transcripcion.procesamiento_audio.archivo_mejorado
            )
        }
        
        return render(request, 'transcripcion/vista_resultado.html', context)
        
    except Exception as e:
        logger.error(f"Error en vista_resultado_transcripcion: {str(e)}")
        messages.error(request, f"Error al cargar resultado: {str(e)}")
        return redirect('transcripcion:audios_listos')


@login_required  
def lista_transcripciones_completas(request):
    """
    Vista que lista todas las transcripciones completadas
    para gestión, edición y revisión
    """
    try:
        # Obtener transcripciones completadas
        transcripciones = Transcripcion.objects.filter(
            estado=EstadoTranscripcion.COMPLETADO
        ).select_related(
            'procesamiento_audio',
            'configuracion',
            'usuario_creacion'
        ).order_by('-fecha_completado')
        
        # Filtros
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        hablantes_filtro = request.GET.get('hablantes')
        busqueda = request.GET.get('q')
        tipo_reunion = request.GET.get('tipo_reunion')
        
        if fecha_desde:
            transcripciones = transcripciones.filter(fecha_completado__date__gte=fecha_desde)
        
        if fecha_hasta:
            transcripciones = transcripciones.filter(fecha_completado__date__lte=fecha_hasta)
        
        if hablantes_filtro:
            transcripciones = transcripciones.filter(num_hablantes=int(hablantes_filtro))
        
        if busqueda:
            transcripciones = transcripciones.filter(
                Q(texto_completo__icontains=busqueda) |
                Q(procesamiento_audio__titulo__icontains=busqueda) |
                Q(procesamiento_audio__descripcion__icontains=busqueda)
            )
        
        if tipo_reunion:
            transcripciones = transcripciones.filter(
                procesamiento_audio__tipo_reunion_id=tipo_reunion
            )
        
        # Paginación
        paginator = Paginator(transcripciones, 12)
        page_number = request.GET.get('page')
        transcripciones_page = paginator.get_page(page_number)
        
        # Estadísticas generales
        estadisticas = {
            'total_transcripciones': transcripciones.count(),
            'total_horas': sum(t.duracion_total or 0 for t in transcripciones) / 3600,
            'promedio_hablantes': transcripciones.aggregate(
                promedio=models.Avg('num_hablantes')
            )['promedio'] or 0,
            'transcripciones_mes': transcripciones.filter(
                fecha_completado__month=timezone.now().month,
                fecha_completado__year=timezone.now().year
            ).count()
        }
        
        # Tipos de reunión para filtro
        from apps.audio_processing.models import TipoReunion
        tipos_reunion = TipoReunion.objects.all()
        
        context = {
            'transcripciones': transcripciones_page,
            'estadisticas': estadisticas,
            'tipos_reunion': tipos_reunion,
            'filtros': {
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
                'hablantes': hablantes_filtro,
                'busqueda': busqueda,
                'tipo_reunion': tipo_reunion,
            }
        }
        
        return render(request, 'transcripcion/lista_completas.html', context)
        
    except Exception as e:
        logger.error(f"Error en lista_transcripciones_completas: {str(e)}")
        messages.error(request, f"Error al cargar transcripciones: {str(e)}")
        return render(request, 'transcripcion/lista_completas.html', {'transcripciones': []})


@login_required
@require_http_methods(["GET"])
def exportar_transcripcion(request, transcripcion_id, formato):
    """
    Exporta una transcripción en diferentes formatos (TXT, JSON, SRT, etc.)
    """
    try:
        transcripcion = get_object_or_404(Transcripcion, id=transcripcion_id)
        
        if transcripcion.estado != EstadoTranscripcion.COMPLETADO:
            messages.error(request, 'Solo se pueden exportar transcripciones completadas')
            return redirect('transcripcion:vista_resultado', transcripcion_id=transcripcion_id)
        
        audio_titulo = transcripcion.procesamiento_audio.titulo or f"transcripcion_{transcripcion_id}"
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        
        if formato == 'txt':
            # Exportar como texto plano
            filename = f"{audio_titulo}_{timestamp}.txt"
            response = HttpResponse(content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Formatear texto con hablantes y timestamps
            contenido = f"TRANSCRIPCIÓN: {audio_titulo}\n"
            contenido += f"Fecha de procesamiento: {transcripcion.fecha_completado.strftime('%d/%m/%Y %H:%M:%S')}\n"
            contenido += f"Duración: {transcripcion.duracion_total:.2f} segundos\n"
            contenido += f"Número de hablantes: {transcripcion.num_hablantes}\n"
            contenido += f"Configuración: {transcripcion.configuracion.nombre if transcripcion.configuracion else 'Personalizada'}\n"
            contenido += "\n" + "="*80 + "\n\n"
            
            # Agregar transcripción formateada
            if transcripcion.texto_completo:
                contenido += transcripcion.texto_completo
            else:
                # Formatear desde segmentos
                resultado_final = transcripcion.resultado_final or {}
                segmentos = resultado_final.get('segmentos_combinados', [])
                hablantes = transcripcion.hablantes_detectados or {}
                
                for segmento in segmentos:
                    timestamp_inicio = f"{segmento.get('inicio', 0):.2f}s"
                    hablante = hablantes.get(segmento.get('hablante'), segmento.get('hablante', 'Desconocido'))
                    texto = segmento.get('texto', '')
                    contenido += f"[{timestamp_inicio}] {hablante}: {texto}\n"
            
            response.write(contenido.encode('utf-8'))
            return response
        
        elif formato == 'json':
            # Exportar como JSON completo
            filename = f"{audio_titulo}_{timestamp}.json"
            response = HttpResponse(content_type='application/json; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            data_export = {
                'metadatos': {
                    'titulo': audio_titulo,
                    'fecha_procesamiento': transcripcion.fecha_completado.isoformat(),
                    'duracion_total': transcripcion.duracion_total,
                    'num_hablantes': transcripcion.num_hablantes,
                    'configuracion_usada': transcripcion.configuracion.nombre if transcripcion.configuracion else 'Personalizada',
                    'modelo_whisper': transcripcion.datos_whisper.get('modelo_usado') if transcripcion.datos_whisper else 'desconocido',
                    'usuario_procesamiento': transcripcion.usuario_creacion.username,
                    'version_transcripcion': getattr(transcripcion, 'version_actual', 1)
                },
                'hablantes': transcripcion.hablantes_detectados or {},
                'segmentos': transcripcion.resultado_final.get('segmentos_combinados', []) if transcripcion.resultado_final else [],
                'texto_completo': transcripcion.texto_completo,
                'estadisticas': transcripcion.estadisticas_procesamiento or {},
                'datos_whisper': transcripcion.datos_whisper or {},
                'datos_pyannote': transcripcion.datos_pyannote or {}
            }
            
            response.write(json.dumps(data_export, indent=2, ensure_ascii=False).encode('utf-8'))
            return response
        
        elif formato == 'srt':
            # Exportar como subtítulos SRT
            filename = f"{audio_titulo}_{timestamp}.srt"
            response = HttpResponse(content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            def segundos_a_srt_time(segundos):
                horas = int(segundos // 3600)
                minutos = int((segundos % 3600) // 60)
                segs = int(segundos % 60)
                milisegundos = int((segundos % 1) * 1000)
                return f"{horas:02d}:{minutos:02d}:{segs:02d},{milisegundos:03d}"
            
            contenido_srt = ""
            resultado_final = transcripcion.resultado_final or {}
            segmentos = resultado_final.get('segmentos_combinados', [])
            hablantes = transcripcion.hablantes_detectados or {}
            
            for i, segmento in enumerate(segmentos, 1):
                inicio = segundos_a_srt_time(segmento.get('inicio', 0))
                fin = segundos_a_srt_time(segmento.get('fin', 0))
                hablante = hablantes.get(segmento.get('hablante'), segmento.get('hablante', 'Desconocido'))
                texto = segmento.get('texto', '')
                
                contenido_srt += f"{i}\n"
                contenido_srt += f"{inicio} --> {fin}\n"
                contenido_srt += f"{hablante}: {texto}\n\n"
            
            response.write(contenido_srt.encode('utf-8'))
            return response
        
        else:
            messages.error(request, f'Formato "{formato}" no soportado')
            return redirect('transcripcion:vista_resultado', transcripcion_id=transcripcion_id)
        
    except Exception as e:
        logger.error(f"Error al exportar transcripción: {str(e)}")
        messages.error(request, f"Error al exportar: {str(e)}")
        return redirect('transcripcion:vista_resultado', transcripcion_id=transcripcion_id)
