/**
 * JavaScript para el detalle de transcripción
 * Maneja chat interactivo, sincronización de audio, edición de segmentos
 */

// Variables globales
let transcripcionId = null;
let audio = null;
let editandoJSON = false;
let mensajeEditando = null;
let conversacionData = [];

$(document).ready(function() {
    // Inicializar
    transcripcionId = $('#transcripcion-id').data('id');
    audio = document.getElementById('main-audio');
    
    console.log('Detalle transcripción cargado, ID:', transcripcionId);
    
    // Cargar datos de conversación
    cargarConversacion();
    
    // Inicializar tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Eventos
    inicializarEventos();
});

function inicializarEventos() {
    // Sincronización de audio con chat
    $(document).on('click', '.chat-message', function() {
        const tiempoInicio = parseFloat($(this).data('tiempo-inicio')) || 0;
        
        if (audio && tiempoInicio >= 0) {
            audio.currentTime = tiempoInicio;
            audio.play();
            
            // Marcar mensaje como reproduciéndose
            $('.chat-message').removeClass('playing');
            $(this).addClass('playing');
            
            console.log('Reproduciendo desde:', tiempoInicio, 'segundos');
        }
    });
    
    // Actualizar mensaje activo mientras se reproduce
    if (audio) {
        audio.addEventListener('timeupdate', function() {
            const tiempoActual = audio.currentTime;
            let mensajeActivo = null;
            
            $('.chat-message').each(function() {
                const inicio = parseFloat($(this).data('tiempo-inicio')) || 0;
                const fin = parseFloat($(this).data('tiempo-fin')) || inicio + 5;
                
                if (tiempoActual >= inicio && tiempoActual <= fin) {
                    mensajeActivo = $(this);
                    return false;
                }
            });
            
            $('.chat-message').removeClass('playing');
            if (mensajeActivo) {
                mensajeActivo.addClass('playing');
                
                // Auto-scroll al mensaje activo
                const container = $('#chat-messages');
                if (container.length && mensajeActivo.length) {
                    const scrollTop = mensajeActivo.offset().top - container.offset().top + container.scrollTop() - 100;
                    container.animate({scrollTop: scrollTop}, 300);
                }
            }
        });
    }
    
    // Edición de JSON
    $('#btn-editar-json').on('click', function() {
        if (!editandoJSON) {
            iniciarEdicionJSON();
        }
    });
    
    $('#btn-cancelar-json').on('click', function() {
        cancelarEdicionJSON();
    });
    
    $('#btn-guardar-json').on('click', function() {
        guardarJSON();
    });
    
    // Edición de segmentos
    $(document).on('click', '.btn-edit-segment', function(e) {
        e.stopPropagation();
        const mensajeId = $(this).closest('.chat-message').data('mensaje-id');
        editarSegmento(mensajeId);
    });
    
    $(document).on('click', '.btn-delete-segment', function(e) {
        e.stopPropagation();
        if (confirm('¿Está seguro de eliminar este segmento?')) {
            const mensajeId = $(this).closest('.chat-message').data('mensaje-id');
            eliminarSegmento(mensajeId);
        }
    });
    
    // Gestión de hablantes
    $('#btn-editar-hablantes').on('click', function() {
        cargarHablantes();
        $('#modal-hablantes').modal('show');
    });
    
    // Agregar nuevo mensaje
    $('#btn-enviar-mensaje').on('click', function() {
        agregarNuevoMensaje();
    });
    
    $('#nuevo-mensaje-texto').on('keypress', function(e) {
        if (e.which === 13) { // Enter
            agregarNuevoMensaje();
        }
    });
    
    // Guardar segmento editado
    $('#btn-guardar-segmento').on('click', function() {
        guardarSegmentoEditado();
    });
    
    // Guardar hablantes
    $('#btn-guardar-hablantes').on('click', function() {
        guardarHablantes();
    });
}

// ========================================
// FUNCIONES DE CARGA DE DATOS
// ========================================

function cargarConversacion() {
    if (!transcripcionId) return;
    
    $.ajax({
        url: `/transcripcion/api/estado/${transcripcionId}/`,
        method: 'GET',
        success: function(data) {
            console.log('Datos de transcripción cargados:', data);
            if (data.conversacion_json) {
                conversacionData = data.conversacion_json;
                actualizarChat();
            }
        },
        error: function(xhr, status, error) {
            console.error('Error cargando conversación:', error);
        }
    });
}

function actualizarChat() {
    const container = $('#chat-messages');
    container.empty();
    
    if (conversacionData.length === 0) {
        container.html(`
            <div class="alert alert-info text-center">
                <i class="fas fa-info-circle"></i>
                No hay conversación transcrita disponible.
                <br><small>Los datos aparecerán aquí una vez completado el procesamiento.</small>
            </div>
        `);
        return;
    }
    
    conversacionData.forEach((mensaje, index) => {
        const mensajeHtml = crearMensajeHTML(mensaje, index);
        container.append(mensajeHtml);
    });
}

function crearMensajeHTML(mensaje, index) {
    const hablante = mensaje.hablante || "Hablante Desconocido";
    const texto = mensaje.texto || "[Sin texto]";
    const inicio = mensaje.inicio || 0;
    const fin = mensaje.fin || inicio + 5;
    const color = mensaje.color || '#007bff';
    
    return `
        <div class="direct-chat-msg chat-message" 
             data-tiempo-inicio="${inicio}"
             data-tiempo-fin="${fin}"
             data-mensaje-id="${index}">
            <div class="direct-chat-infos clearfix">
                <span class="direct-chat-name float-left">
                    ${hablante}
                </span>
                <span class="direct-chat-timestamp float-right timestamp-indicator">
                    ${inicio.toFixed(1)}s - ${fin.toFixed(1)}s
                </span>
            </div>
            <div class="speaker-avatar" style="background-color: ${color};">
                ${hablante.charAt(0).toUpperCase()}
            </div>
            <div class="direct-chat-text editable-segment" 
                 data-tipo="texto" 
                 data-mensaje-id="${index}">
                ${texto}
                <div class="text-right mt-1">
                    <button class="btn btn-xs btn-outline-primary btn-edit-segment" 
                            title="Editar segmento">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-xs btn-outline-danger btn-delete-segment" 
                            title="Eliminar segmento">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// ========================================
// FUNCIONES DE EDICIÓN JSON
// ========================================

function iniciarEdicionJSON() {
    editandoJSON = true;
    $('#btn-editar-json').addClass('d-none');
    $('#btn-guardar-json, #btn-cancelar-json').removeClass('d-none');
    
    // Convertir pre a textarea editable
    $('pre[id$="-json"]').each(function() {
        const contenido = $(this).text();
        const textarea = $('<textarea class="form-control json-textarea" rows="10"></textarea>');
        textarea.val(contenido);
        $(this).after(textarea).hide();
    });
}

function cancelarEdicionJSON() {
    editandoJSON = false;
    $('#btn-editar-json').removeClass('d-none');
    $('#btn-guardar-json, #btn-cancelar-json').addClass('d-none');
    
    $('.json-textarea').remove();
    $('pre[id$="-json"]').show();
}

function guardarJSON() {
    const jsonData = {};
    
    $('.json-textarea').each(function() {
        const textarea = $(this);
        const preElement = textarea.prev('pre');
        const jsonType = preElement.attr('id').replace('-json', '');
        
        try {
            jsonData[jsonType] = JSON.parse(textarea.val());
        } catch (e) {
            alert(`Error en JSON de ${jsonType}: ${e.message}`);
            return false;
        }
    });
    
    // Enviar datos al servidor
    $.ajax({
        url: `/transcripcion/api/actualizar-json/${transcripcionId}/`,
        method: 'POST',
        data: {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val(),
            'json_data': JSON.stringify(jsonData)
        },
        success: function(response) {
            if (response.success) {
                alert('JSON actualizado correctamente');
                cancelarEdicionJSON();
                location.reload(); // Recargar para mostrar cambios
            } else {
                alert('Error: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            alert('Error al guardar: ' + error);
        }
    });
}

// ========================================
// FUNCIONES DE EDICIÓN DE SEGMENTOS
// ========================================

function editarSegmento(mensajeId) {
    if (mensajeId >= conversacionData.length) return;
    
    mensajeEditando = mensajeId;
    const mensaje = conversacionData[mensajeId];
    
    // Cargar datos en el modal
    $('#edit-hablante').val(mensaje.hablante || '');
    $('#edit-texto').val(mensaje.texto || '');
    $('#edit-inicio').val(mensaje.inicio || 0);
    $('#edit-fin').val(mensaje.fin || 0);
    
    // Cargar lista de hablantes disponibles
    cargarHablantesEnSelect();
    
    $('#modal-editar-segmento').modal('show');
}

function cargarHablantesEnSelect() {
    const select = $('#edit-hablante');
    select.empty();
    
    // Obtener hablantes únicos
    const hablantes = [...new Set(conversacionData.map(m => m.hablante).filter(h => h))];
    
    hablantes.forEach(hablante => {
        select.append(`<option value="${hablante}">${hablante}</option>`);
    });
    
    // Opción para nuevo hablante
    select.append('<option value="__nuevo__">+ Nuevo Hablante</option>');
}

function guardarSegmentoEditado() {
    if (mensajeEditando === null) return;
    
    const nuevoHablante = $('#edit-hablante').val();
    const nuevoTexto = $('#edit-texto').val();
    const nuevoInicio = parseFloat($('#edit-inicio').val()) || 0;
    const nuevoFin = parseFloat($('#edit-fin').val()) || 0;
    
    if (nuevoHablante === '__nuevo__') {
        const nombreHablante = prompt('Nombre del nuevo hablante:');
        if (!nombreHablante) return;
        nuevoHablante = nombreHablante;
    }
    
    // Actualizar datos localmente
    conversacionData[mensajeEditando] = {
        ...conversacionData[mensajeEditando],
        hablante: nuevoHablante,
        texto: nuevoTexto,
        inicio: nuevoInicio,
        fin: nuevoFin
    };
    
    // Enviar al servidor
    $.ajax({
        url: `/transcripcion/api/editar-segmento/${transcripcionId}/`,
        method: 'POST',
        data: {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val(),
            'segmento_id': mensajeEditando,
            'hablante': nuevoHablante,
            'texto': nuevoTexto,
            'inicio': nuevoInicio,
            'fin': nuevoFin
        },
        success: function(response) {
            if (response.success) {
                actualizarChat();
                $('#modal-editar-segmento').modal('hide');
                mensajeEditando = null;
            } else {
                alert('Error: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            alert('Error al guardar: ' + error);
        }
    });
}

function eliminarSegmento(mensajeId) {
    $.ajax({
        url: `/transcripcion/api/eliminar-segmento/${transcripcionId}/`,
        method: 'POST',
        data: {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val(),
            'segmento_id': mensajeId
        },
        success: function(response) {
            if (response.success) {
                conversacionData.splice(mensajeId, 1);
                actualizarChat();
            } else {
                alert('Error: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            alert('Error al eliminar: ' + error);
        }
    });
}

function agregarNuevoMensaje() {
    const texto = $('#nuevo-mensaje-texto').val().trim();
    if (!texto) return;
    
    const tiempoActual = audio ? audio.currentTime : 0;
    const hablantePorDefecto = 'Nuevo Hablante';
    
    // Agregar localmente
    const nuevoMensaje = {
        hablante: hablantePorDefecto,
        texto: texto,
        inicio: tiempoActual,
        fin: tiempoActual + 5,
        color: '#28a745'
    };
    
    conversacionData.push(nuevoMensaje);
    
    // Enviar al servidor
    $.ajax({
        url: `/transcripcion/api/agregar-segmento/${transcripcionId}/`,
        method: 'POST',
        data: {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val(),
            'mensaje': JSON.stringify(nuevoMensaje)
        },
        success: function(response) {
            if (response.success) {
                actualizarChat();
                $('#nuevo-mensaje-texto').val('');
            } else {
                alert('Error: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            alert('Error al agregar: ' + error);
        }
    });
}

// ========================================
// FUNCIONES DE GESTIÓN DE HABLANTES
// ========================================

function cargarHablantes() {
    const container = $('#lista-hablantes');
    container.html('<p>Cargando hablantes...</p>');
    
    // Obtener hablantes únicos de la conversación
    const hablantes = [...new Set(conversacionData.map(m => m.hablante).filter(h => h))];
    
    let html = '<div class="row">';
    hablantes.forEach((hablante, index) => {
        const color = `hsl(${index * 360 / hablantes.length}, 70%, 50%)`;
        html += `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex align-items-center">
                            <div class="speaker-avatar mr-3" style="background-color: ${color};">
                                ${hablante.charAt(0).toUpperCase()}
                            </div>
                            <div class="flex-grow-1">
                                <input type="text" class="form-control hablante-nombre" 
                                       value="${hablante}" data-original="${hablante}">
                            </div>
                            <button class="btn btn-sm btn-danger ml-2 btn-eliminar-hablante" 
                                    data-hablante="${hablante}">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    container.html(html);
}

function guardarHablantes() {
    const cambios = {};
    
    $('.hablante-nombre').each(function() {
        const original = $(this).data('original');
        const nuevo = $(this).val().trim();
        if (original !== nuevo && nuevo) {
            cambios[original] = nuevo;
        }
    });
    
    if (Object.keys(cambios).length === 0) {
        $('#modal-hablantes').modal('hide');
        return;
    }
    
    $.ajax({
        url: `/transcripcion/api/renombrar-hablantes/${transcripcionId}/`,
        method: 'POST',
        data: {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val(),
            'cambios': JSON.stringify(cambios)
        },
        success: function(response) {
            if (response.success) {
                // Actualizar datos localmente
                conversacionData.forEach(mensaje => {
                    if (cambios[mensaje.hablante]) {
                        mensaje.hablante = cambios[mensaje.hablante];
                    }
                });
                
                actualizarChat();
                $('#modal-hablantes').modal('hide');
            } else {
                alert('Error: ' + response.error);
            }
        },
        error: function(xhr, status, error) {
            alert('Error al guardar: ' + error);
        }
    });
}

// Eliminar hablante
$(document).on('click', '.btn-eliminar-hablante', function() {
    const hablante = $(this).data('hablante');
    if (confirm(`¿Eliminar todos los mensajes de "${hablante}"?`)) {
        conversacionData = conversacionData.filter(m => m.hablante !== hablante);
        actualizarChat();
        cargarHablantes();
    }
});

// ========================================
// UTILIDADES
// ========================================

function formatearTiempo(segundos) {
    const minutos = Math.floor(segundos / 60);
    const segs = (segundos % 60).toFixed(1);
    return `${minutos}:${segs.padStart(4, '0')}`;
}

// Exportar funciones globalmente si es necesario
window.transcripcionDetalle = {
    cargarConversacion,
    editarSegmento,
    eliminarSegmento,
    agregarNuevoMensaje
};