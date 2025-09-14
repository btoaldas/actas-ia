$(document).ready(function() {
    let contadorParticipantes = parseInt($('#participantes-container .participante-row').length) || 0;
    
    console.log('Script de transcripción cargado, participantes detectados:', contadorParticipantes);
    
    // Manejo de la activación/desactivación de diarización
    $('#diarizacion_activa').on('change', function() {
        if ($(this).is(':checked')) {
            $('#opciones-diarizacion').removeClass('d-none');
        } else {
            $('#opciones-diarizacion').addClass('d-none');
        }
    });
    
    // Actualizar descripción del modelo
    $('#modelo_whisper').on('change', function() {
        var descripcion = $(this).find('option:selected').data('descripcion');
        $('#descripcion-modelo').text(descripcion);
    });
    
    // Agregar participante
    $('#agregar-participante').on('click', function() {
        contadorParticipantes++;
        console.log('Agregando participante:', contadorParticipantes);
        
        var nuevaFila = `
            <div class="card card-outline card-secondary mb-3 participante-row">
                <div class="card-header">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-user"></i> Hablante ${contadorParticipantes}
                    </h5>
                    <div class="card-tools">
                        <button type="button" class="btn btn-danger btn-sm eliminar-participante" title="Eliminar participante">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Nombres:</label>
                                <input type="text" class="form-control" name="participante_nombres_${contadorParticipantes}" placeholder="Nombres">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Apellidos:</label>
                                <input type="text" class="form-control" name="participante_apellidos_${contadorParticipantes}" placeholder="Apellidos">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Cargo/Función:</label>
                                <input type="text" class="form-control" name="participante_cargo_${contadorParticipantes}" placeholder="Ej: Alcalde, Secretario">
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label>Institución:</label>
                                <input type="text" class="form-control" name="participante_institucion_${contadorParticipantes}" placeholder="Ej: Municipio">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>ID de Hablante para Diarización:</label>
                                <input type="text" class="form-control" name="participante_id_${contadorParticipantes}" 
                                       value="hablante_${contadorParticipantes}" readonly>
                                <small class="form-text text-muted">Este ID se usará para identificar al hablante en la transcripción</small>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Estado:</label>
                                <div class="form-check pt-2">
                                    <input type="checkbox" class="form-check-input" name="participante_activo_${contadorParticipantes}" checked>
                                    <label class="form-check-label">Incluir en transcripción</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        $('#participantes-container').append(nuevaFila);
    });
    
    // Eliminar participante
    $(document).on('click', '.eliminar-participante', function() {
        $(this).closest('.participante-row').remove();
    });
    
    // Manejo del formulario
    $('#form-configuracion').on('submit', function(e) {
        e.preventDefault();
        
        console.log('Formulario enviado');
        
        // Deshabilitar botón y mostrar estado
        $('#btn-iniciar').prop('disabled', true).html('<i class="fas fa-spinner fa-spin"></i> Iniciando...');
        $('#card-estado').removeClass('d-none');
        
        // Recopilar datos de participantes con estructura completa
        var participantes = [];
        $('.participante-row').each(function(index) {
            var nombres = $(this).find('input[name^="participante_nombres_"]').val() || '';
            var apellidos = $(this).find('input[name^="participante_apellidos_"]').val() || '';
            var cargo = $(this).find('input[name^="participante_cargo_"]').val() || '';
            var institucion = $(this).find('input[name^="participante_institucion_"]').val() || '';
            var id_hablante = $(this).find('input[name^="participante_id_"]').val() || ('hablante_' + (index + 1));
            var activo = $(this).find('input[name^="participante_activo_"]').is(':checked');
            
            if (nombres.trim() || apellidos.trim()) {
                participantes.push({
                    orden: index + 1,
                    nombres: nombres.trim(),
                    apellidos: apellidos.trim(),
                    nombre_completo: (nombres + ' ' + apellidos).trim(),
                    cargo: cargo.trim(),
                    institucion: institucion.trim(),
                    id: id_hablante,
                    activo: activo
                });
            }
        });
        
        console.log('Participantes recopilados:', participantes);
        
        // Obtener la URL del formulario
        var url = $(this).attr('action') || window.location.href;
        console.log('URL de envío:', url);
        
        // Enviar datos
        var formData = new FormData(this);
        formData.append('participantes_json', JSON.stringify(participantes));
        formData.append('num_hablantes_detectados', participantes.length);
        
        console.log('Enviando AJAX...');
        
        $.ajax({
            url: url,
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                console.log('Respuesta recibida:', response);
                
                if (response && response.success) {
                    $('#estado-texto').text('Transcripción iniciada correctamente');
                    $('#progress-bar').css('width', '25%').attr('aria-valuenow', 25);
                    
                    // Redirigir después de un momento
                    setTimeout(function() {
                        // Usar URL relativa en lugar de template tag
                        window.location.href = '/transcripcion/transcripciones/';
                    }, 2000);
                } else {
                    var errorMsg = (response && response.error) ? response.error : 'Error desconocido';
                    alert('Error: ' + errorMsg);
                    $('#btn-iniciar').prop('disabled', false).html('<i class="fas fa-play"></i> Iniciar Transcripción');
                    $('#card-estado').addClass('d-none');
                }
            },
            error: function(xhr, status, error) {
                console.log('Error AJAX:', {xhr: xhr, status: status, error: error});
                console.log('Response text:', xhr.responseText);
                
                alert('Error al iniciar la transcripción: ' + error);
                $('#btn-iniciar').prop('disabled', false).html('<i class="fas fa-play"></i> Iniciar Transcripción');
                $('#card-estado').addClass('d-none');
            }
        });
    });
    
    // ========================================
    // FUNCIONES DE MONITOREO EN TIEMPO REAL
    // ========================================
    
    let intervalId = null;
    let transcripcionId = null;
    
    // Función para iniciar el monitoreo de progreso
    function iniciarMonitoreo(transcripcionIdParam) {
        transcripcionId = transcripcionIdParam;
        console.log('Iniciando monitoreo para transcripción:', transcripcionId);
        
        // Mostrar panel de progreso
        $('#panel-progreso').show();
        $('#formulario-configuracion').hide();
        
        // Iniciar polling cada 3 segundos
        intervalId = setInterval(consultarEstado, 3000);
        
        // Primera consulta inmediata
        consultarEstado();
    }
    
    // Función para consultar el estado
    function consultarEstado() {
        if (!transcripcionId) return;
        
        $.ajax({
            url: `/transcripcion/api/estado/${transcripcionId}/`,
            method: 'GET',
            success: function(data) {
                console.log('Estado recibido:', data);
                actualizarInterfaz(data);
                
                // Si está completada o con error, detener monitoreo
                if (data.es_completa || data.tiene_errores) {
                    detenerMonitoreo();
                    if (data.es_completa) {
                        mostrarCompletado(data);
                    } else if (data.tiene_errores) {
                        mostrarError(data);
                    }
                }
            },
            error: function(xhr, status, error) {
                console.error('Error consultando estado:', error);
                agregarLog(`ERROR: No se pudo consultar el estado - ${error}`, 'error');
            }
        });
    }
    
    // Función para actualizar la interfaz
    function actualizarInterfaz(data) {
        // Actualizar barra de progreso
        const progreso = data.progreso || 0;
        $('#progreso-porcentaje').text(progreso);
        $('#barra-progreso').css('width', progreso + '%').attr('aria-valuenow', progreso);
        
        // Actualizar mensaje de estado
        const mensaje = data.mensaje_estado || `Estado: ${data.estado}`;
        $('#mensaje-estado').text(mensaje);
        
        // Cambiar color de la alerta según el estado
        const $alerta = $('#estado-actual');
        $alerta.removeClass('alert-info alert-warning alert-success alert-danger');
        
        switch(data.estado) {
            case 'pendiente':
                $alerta.addClass('alert-info');
                break;
            case 'en_proceso':
            case 'transcribiendo':
            case 'diarizando':
                $alerta.addClass('alert-warning');
                break;
            case 'completado':
            case 'curada':
                $alerta.addClass('alert-success');
                break;
            case 'error':
                $alerta.addClass('alert-danger');
                break;
            default:
                $alerta.addClass('alert-info');
        }
        
        // Agregar log si hay información de tarea
        if (data.task_info && data.task_info.state) {
            agregarLog(`Estado Celery: ${data.task_info.state}`, 'info');
            
            if (data.task_info.info && data.task_info.info.current) {
                agregarLog(`Progreso: ${data.task_info.info.current}`, 'info');
            }
        }
        
        // Log del estado general
        agregarLog(`${new Date().toLocaleTimeString()} - ${mensaje}`, 'info');
    }
    
    // Función para agregar logs
    function agregarLog(mensaje, tipo = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        let claseColor = 'text-info';
        
        switch(tipo) {
            case 'error':
                claseColor = 'text-danger';
                break;
            case 'warning':
                claseColor = 'text-warning';
                break;
            case 'success':
                claseColor = 'text-success';
                break;
        }
        
        const logEntry = `<span class="${claseColor}">[${timestamp}]</span> ${mensaje}<br>`;
        $('#logs-content').append(logEntry);
        
        // Auto-scroll
        const container = $('#logs-container')[0];
        container.scrollTop = container.scrollHeight;
    }
    
    // Función para mostrar transcripción completada
    function mostrarCompletado(data) {
        agregarLog('¡Transcripción completada exitosamente!', 'success');
        $('#btn-ver-detalle').show().attr('onclick', `window.location.href='/transcripcion/detalle/${data.transcripcion_id}/'`);
        $('#btn-cancelar').hide();
        
        // Actualizar progreso a 100%
        $('#progreso-porcentaje').text(100);
        $('#barra-progreso').css('width', '100%').removeClass('progress-bar-animated');
    }
    
    // Función para mostrar error
    function mostrarError(data) {
        agregarLog('ERROR: La transcripción falló', 'error');
        $('#btn-cancelar').text('Volver').removeClass('btn-danger').addClass('btn-secondary');
    }
    
    // Función para detener monitoreo
    function detenerMonitoreo() {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
            console.log('Monitoreo detenido');
        }
    }
    
    // Limpiar logs
    $('#btn-limpiar-logs').on('click', function() {
        $('#logs-content').html('');
        agregarLog('Logs limpiados', 'info');
    });
    
    // Cancelar procesamiento
    $('#btn-cancelar').on('click', function() {
        if (confirm('¿Estás seguro de que quieres cancelar el procesamiento?')) {
            detenerMonitoreo();
            window.location.href = '/transcripcion/audios/';
        }
    });
    
    // Si se carga la página con progreso activo, iniciar monitoreo automáticamente
    $(document).ready(function() {
        // Buscar si hay variables de transcripción en el template
        if (typeof window.transcripcionId !== 'undefined') {
            iniciarMonitoreo(window.transcripcionId);
        }
    });
});

// Exponer función globalmente para uso desde template
window.iniciarMonitoreoTranscripcion = function(transcripcionId) {
    iniciarMonitoreo(transcripcionId);
};