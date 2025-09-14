/**
 * Editor Avanzado de Transcripciones - Versión Simplificada
 * Permite editar la estructura JSON de transcripciones con interfaz intuitiva
 */

// Configuración global
window.TranscripcionEditor = window.TranscripcionEditor || {};

// Variables globales del editor
let editorState = {
    transcripcionId: null,
    modoEdicion: false,
    cambiosPendientes: false,
    estructuraOriginal: null,
    estructuraActual: null,
    segmentoEditando: null
};

// URLs de las APIs
let apiUrls = {};

// Colores para hablantes
const coloresHablantes = [
    '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
    '#6f42c1', '#fd7e14', '#20c997', '#6c757d', '#e74c3c'
];

/**
 * Inicialización del editor
 */
function initEditor() {
    console.log('🚀 Inicializando Editor Avanzado');
    
    // Obtener configuración desde el template
    if (window.TranscripcionEditor && window.TranscripcionEditor.transcripcionId) {
        editorState.transcripcionId = window.TranscripcionEditor.transcripcionId;
        apiUrls = window.TranscripcionEditor.urls || {};
        
        setupEventListeners();
        loadStructure();
        
        console.log('✅ Editor inicializado correctamente');
        console.log('📊 Datos disponibles:', window.TranscripcionEditor);
    } else {
        console.error('❌ No se encontró configuración de TranscripcionEditor');
        console.log('🔍 window.TranscripcionEditor:', window.TranscripcionEditor);
        
        // Intentar cargar desde el template directamente si no está en window
        const transcripcionId = document.querySelector('[data-transcripcion-id]')?.dataset?.transcripcionId;
        if (transcripcionId) {
            console.log('🔄 Intentando con ID desde DOM:', transcripcionId);
            editorState.transcripcionId = parseInt(transcripcionId);
            setupEventListeners();
            loadStructureBasica();
        } else {
            showError('No se pudo inicializar el editor. Recarga la página.');
        }
    }
}

/**
 * Configurar event listeners
 */
function setupEventListeners() {
    // Toggle modo edición
    $('#toggle-modo-edicion').on('click', toggleModoEdicion);
    
    // Botones principales
    $('#btn-agregar-segmento').on('click', openAddSegmentModal);
    $('#btn-gestionar-hablantes').on('click', openManageHablantesModal);
    $('#btn-vista-json').on('click', openEditJSONModal);
    
    // Botón flotante guardar
    $('#btn-guardar-cambios').on('click', saveAllChanges);
    
    // Eventos de modales
    $('#btn-guardar-segmento').on('click', saveEditedSegment);
    $('#btn-eliminar-segmento').on('click', deleteCurrentSegment);
    $('#btn-crear-segmento').on('click', createNewSegment);
    
    // Actualizar duraciones automáticamente
    $('#edit-inicio, #edit-fin').on('input', updateEditDuration);
    $('#nuevo-inicio, #nuevo-fin').on('input', updateNewDuration);
    
    // Detectar cambios no guardados
    $(window).on('beforeunload', function(e) {
        if (editorState.cambiosPendientes) {
            e.preventDefault();
            e.returnValue = '¿Estás seguro de que quieres salir? Hay cambios sin guardar.';
            return e.returnValue;
        }
    });
}

/**
 * Cargar estructura desde el servidor
 */
async function loadStructure() {
    try {
        showLoading(true);
        
        const response = await fetch(apiUrls.obtenerEstructura, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.exito) {
            editorState.estructuraOriginal = JSON.parse(JSON.stringify(data.estructura));
            editorState.estructuraActual = data.estructura;
            renderConversation();
            updateStatistics();
            updateJSONViews();
            
            console.log('✅ Estructura cargada:', data);
        } else {
            throw new Error(data.error || 'Error desconocido');
        }
        
    } catch (error) {
        console.error('❌ Error cargando estructura:', error);
        console.log('🔄 Intentando cargar estructura básica...');
        loadStructureBasica();
    } finally {
        showLoading(false);
    }
}

/**
 * Cargar estructura básica desde variables del template
 */
function loadStructureBasica() {
    try {
        console.log('📂 Cargando estructura básica...');
        
        // Intentar obtener desde variables globales del template
        let estructura = null;
        
        if (window.TranscripcionEditor && window.TranscripcionEditor.estructura) {
            estructura = window.TranscripcionEditor.estructura;
        } else if (window.estructuraTranscripcion) {
            estructura = window.estructuraTranscripcion;
        } else {
            // Crear estructura mínima si no hay datos
            estructura = {
                cabecera: { mapeo_hablantes: {} },
                conversacion: [],
                texto_estructurado: "",
                metadata: {}
            };
        }
        
        console.log('📊 Estructura obtenida:', estructura);
        
        editorState.estructuraOriginal = JSON.parse(JSON.stringify(estructura));
        editorState.estructuraActual = estructura;
        
        renderConversation();
        updateStatistics();
        updateJSONViews();
        
        if (estructura.conversacion && estructura.conversacion.length > 0) {
            showSuccess('Transcripción cargada correctamente');
        } else {
            showError('No hay datos de conversación disponibles');
        }
        
    } catch (error) {
        console.error('❌ Error en carga básica:', error);
        showError('Error al cargar los datos de la transcripción');
    }
}

/**
 * Renderizar la conversación
 */
function renderConversation() {
    const conversacion = editorState.estructuraActual?.conversacion || [];
    const mapeoHablantes = editorState.estructuraActual?.cabecera?.mapeo_hablantes || {};
    
    if (conversacion.length === 0) {
        $('#no-conversacion').show();
        $('#conversacion-container').hide();
        return;
    }
    
    $('#no-conversacion').hide();
    $('#conversacion-container').show();
    
    let html = '';
    
    conversacion.forEach((segmento, index) => {
        const hablante = segmento.hablante || 'Desconocido';
        const texto = segmento.texto || '[Sin texto]';
        const inicio = parseFloat(segmento.inicio || 0);
        const fin = parseFloat(segmento.fin || 0);
        const duracion = fin - inicio;
        
        // Obtener color del hablante
        const colorIndex = Object.values(mapeoHablantes).indexOf(hablante);
        const color = coloresHablantes[colorIndex % coloresHablantes.length];
        
        // Formatear tiempo
        const tiempoTexto = formatTime(inicio) + ' - ' + formatTime(fin);
        
        html += `
            <div class="direct-chat-msg chat-message animate-slide-in" 
                 data-tiempo-inicio="${inicio}"
                 data-tiempo-fin="${fin}"
                 data-mensaje-id="${index}"
                 data-hablante="${hablante}">
                
                <div class="direct-chat-infos clearfix">
                    <span class="direct-chat-name float-left">
                        <span class="hablante-color" style="background-color: ${color};"></span>
                        ${hablante}
                    </span>
                    <span class="direct-chat-timestamp float-right time-display">
                        ${tiempoTexto} (${duracion.toFixed(1)}s)
                    </span>
                </div>
                
                <div class="direct-chat-text position-relative" 
                     data-tipo="texto" 
                     data-mensaje-id="${index}">
                    <div class="editable-content" data-original="${texto}">
                        ${texto}
                    </div>
                    
                    <div class="segment-controls">
                        <button class="btn btn-xs btn-outline-primary btn-edit-segment" 
                                title="Editar segmento" data-index="${index}">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-xs btn-outline-info btn-play-segment" 
                                title="Reproducir segmento" data-inicio="${inicio}" data-fin="${fin}">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn btn-xs btn-outline-danger btn-delete-segment" 
                                title="Eliminar segmento" data-index="${index}">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    $('#conversacion-container').html(html);
    setupSegmentEvents();
}

/**
 * Configurar eventos de segmentos
 */
function setupSegmentEvents() {
    // Editar segmento
    $('.btn-edit-segment').on('click', function(e) {
        e.stopPropagation();
        const index = parseInt($(this).data('index'));
        editSegment(index);
    });
    
    // Reproducir segmento
    $('.btn-play-segment').on('click', function(e) {
        e.stopPropagation();
        const inicio = parseFloat($(this).data('inicio'));
        const fin = parseFloat($(this).data('fin'));
        playSegment(inicio, fin);
    });
    
    // Eliminar segmento
    $('.btn-delete-segment').on('click', function(e) {
        e.stopPropagation();
        const index = parseInt($(this).data('index'));
        confirmDeleteSegment(index);
    });
    
    // Click en mensaje para reproducir
    $('.chat-message').on('click', function(e) {
        if (!$(e.target).closest('.segment-controls').length) {
            const inicio = parseFloat($(this).data('tiempo-inicio'));
            playFromTime(inicio);
        }
    });
}

/**
 * Toggle modo edición
 */
function toggleModoEdicion() {
    editorState.modoEdicion = !editorState.modoEdicion;
    
    if (editorState.modoEdicion) {
        $('#indicador-modo-edicion').show();
        $('#modo-texto').text('Salir');
        $('#toggle-modo-edicion').removeClass('btn-warning').addClass('btn-danger');
        $('body').addClass('modo-edicion-activo');
    } else {
        $('#indicador-modo-edicion').hide();
        $('#modo-texto').text('Editar');
        $('#toggle-modo-edicion').removeClass('btn-danger').addClass('btn-warning');
        $('body').removeClass('modo-edicion-activo');
    }
    
    console.log('🔄 Modo edición:', editorState.modoEdicion ? 'ACTIVADO' : 'DESACTIVADO');
}

/**
 * Editar segmento específico
 */
function editSegment(index) {
    const conversacion = editorState.estructuraActual?.conversacion || [];
    
    if (index < 0 || index >= conversacion.length) {
        showError('Segmento no válido');
        return;
    }
    
    const segmento = conversacion[index];
    editorState.segmentoEditando = { index, ...segmento };
    
    // Llenar modal con datos del segmento
    $('#edit-hablante').val(segmento.hablante);
    $('#edit-texto').val(segmento.texto);
    $('#edit-inicio').val(segmento.inicio);
    $('#edit-fin').val(segmento.fin);
    $('#edit-posicion').val(index + 1);
    $('#total-segmentos-edit').text(conversacion.length);
    
    updateEditDuration();
    loadHablantesInSelect('#edit-hablante');
    
    $('#modal-editar-segmento').modal('show');
}

/**
 * Guardar segmento editado
 */
async function saveEditedSegment() {
    try {
        const datos = {
            indice: editorState.segmentoEditando.index,
            hablante: $('#edit-hablante').val().trim(),
            texto: $('#edit-texto').val().trim(),
            inicio: parseFloat($('#edit-inicio').val()),
            fin: parseFloat($('#edit-fin').val())
        };
        
        // Validaciones
        if (!datos.hablante) {
            showError('El hablante es requerido');
            return;
        }
        
        if (!datos.texto) {
            showError('El texto es requerido');
            return;
        }
        
        if (datos.inicio >= datos.fin) {
            showError('El tiempo de inicio debe ser menor al tiempo de fin');
            return;
        }
        
        showLoading(true);
        
        const response = await fetch(apiUrls.editarSegmento, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });
        
        const result = await response.json();
        
        if (result.exito) {
            // Actualizar estructura local
            editorState.estructuraActual.conversacion[datos.indice] = result.segmento_actualizado;
            editorState.estructuraActual.texto_estructurado = result.texto_estructurado;
            editorState.estructuraActual.metadata = result.metadata;
            
            markPendingChanges();
            renderConversation();
            updateStatistics();
            showSuccess('Segmento actualizado correctamente');
            
            $('#modal-editar-segmento').modal('hide');
        } else {
            throw new Error(result.error || 'Error desconocido');
        }
        
    } catch (error) {
        console.error('❌ Error editando segmento:', error);
        showError('Error al editar segmento: ' + error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Abrir modal para agregar segmento
 */
function openAddSegmentModal() {
    // Limpiar formulario
    $('#form-agregar-segmento')[0].reset();
    
    // Cargar hablantes disponibles
    loadHablantesInSelect('#nuevo-hablante');
    
    // Configurar tiempos por defecto
    const ultimoSegmento = editorState.estructuraActual?.conversacion?.slice(-1)[0];
    if (ultimoSegmento) {
        $('#nuevo-inicio').val(ultimoSegmento.fin);
        $('#nuevo-fin').val(ultimoSegmento.fin + 5);
    }
    
    updateNewDuration();
    
    $('#modal-agregar-segmento').modal('show');
}

/**
 * Crear nuevo segmento
 */
async function createNewSegment() {
    try {
        const datos = {
            hablante: $('#nuevo-hablante').val().trim(),
            texto: $('#nuevo-texto').val().trim(),
            inicio: parseFloat($('#nuevo-inicio').val()),
            fin: parseFloat($('#nuevo-fin').val()),
            posicion: $('#nuevo-posicion').val() || null
        };
        
        // Validaciones básicas
        if (!datos.hablante || !datos.texto) {
            showError('Hablante y texto son requeridos');
            return;
        }
        
        if (datos.inicio >= datos.fin) {
            showError('El tiempo de inicio debe ser menor al tiempo de fin');
            return;
        }
        
        showLoading(true);
        
        const response = await fetch(apiUrls.agregarSegmento, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });
        
        const result = await response.json();
        
        if (result.exito) {
            // Actualizar estructura local
            if (datos.posicion !== null) {
                editorState.estructuraActual.conversacion.splice(result.posicion, 0, result.segmento_creado);
            } else {
                editorState.estructuraActual.conversacion.push(result.segmento_creado);
            }
            
            editorState.estructuraActual.texto_estructurado = result.texto_estructurado;
            editorState.estructuraActual.metadata = result.metadata;
            
            markPendingChanges();
            renderConversation();
            updateStatistics();
            showSuccess('Nuevo segmento agregado correctamente');
            
            $('#modal-agregar-segmento').modal('hide');
        } else {
            throw new Error(result.error || 'Error desconocido');
        }
        
    } catch (error) {
        console.error('❌ Error creando segmento:', error);
        showError('Error al crear segmento: ' + error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Confirmar eliminación de segmento
 */
function confirmDeleteSegment(index) {
    const conversacion = editorState.estructuraActual?.conversacion || [];
    
    if (index < 0 || index >= conversacion.length) {
        showError('Segmento no válido');
        return;
    }
    
    const segmento = conversacion[index];
    const textoCorto = segmento.texto.length > 50 ? 
        segmento.texto.substring(0, 50) + '...' : 
        segmento.texto;
    
    if (confirm('¿Estás seguro de que quieres eliminar este segmento?\n\n"' + textoCorto + '"\n\nEsta acción no se puede deshacer.')) {
        deleteSegment(index);
    }
}

/**
 * Eliminar segmento
 */
async function deleteSegment(index) {
    try {
        showLoading(true);
        
        const response = await fetch(apiUrls.eliminarSegmento, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ indice: index })
        });
        
        const result = await response.json();
        
        if (result.exito) {
            // Actualizar estructura local
            editorState.estructuraActual.conversacion.splice(index, 1);
            editorState.estructuraActual.texto_estructurado = result.texto_estructurado;
            editorState.estructuraActual.metadata = result.metadata;
            
            markPendingChanges();
            renderConversation();
            updateStatistics();
            showSuccess('Segmento eliminado correctamente');
        } else {
            throw new Error(result.error || 'Error desconocido');
        }
        
    } catch (error) {
        console.error('❌ Error eliminando segmento:', error);
        showError('Error al eliminar segmento: ' + error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * Reproducir segmento de audio
 */
function playSegment(inicio, fin) {
    const audioPlayer = document.getElementById('audio-player');
    if (!audioPlayer) {
        showError('Reproductor de audio no disponible');
        return;
    }
    
    audioPlayer.currentTime = inicio;
    audioPlayer.play();
    
    // Pausar al final del segmento
    const pausarAlFinal = function() {
        if (audioPlayer.currentTime >= fin) {
            audioPlayer.pause();
            audioPlayer.removeEventListener('timeupdate', pausarAlFinal);
        }
    };
    
    audioPlayer.addEventListener('timeupdate', pausarAlFinal);
    
    // Resaltar segmento que se está reproduciendo
    $('.chat-message').removeClass('seleccionado');
    $('.chat-message[data-tiempo-inicio="' + inicio + '"]').addClass('seleccionado');
}

/**
 * Reproducir desde tiempo específico
 */
function playFromTime(tiempo) {
    const audioPlayer = document.getElementById('audio-player');
    if (!audioPlayer) return;
    
    audioPlayer.currentTime = tiempo;
    audioPlayer.play();
}

/**
 * Formatear tiempo en MM:SS
 */
function formatTime(segundos) {
    const minutos = Math.floor(segundos / 60);
    const segs = Math.floor(segundos % 60);
    return minutos.toString().padStart(2, '0') + ':' + segs.toString().padStart(2, '0');
}

/**
 * Actualizar estadísticas
 */
function updateStatistics() {
    const conversacion = editorState.estructuraActual?.conversacion || [];
    const hablantes = editorState.estructuraActual?.cabecera?.mapeo_hablantes || {};
    const metadata = editorState.estructuraActual?.metadata || {};
    
    $('#total-segmentos').text(conversacion.length);
    $('#total-hablantes').text(Object.keys(hablantes).length);
    $('#num-mensajes').text(conversacion.length);
    
    if (metadata.fecha_ultima_edicion) {
        const fecha = new Date(metadata.fecha_ultima_edicion);
        $('#fecha-edicion').text(fecha.toLocaleString());
    }
}

/**
 * Marcar cambios pendientes
 */
function markPendingChanges() {
    editorState.cambiosPendientes = true;
    $('#btn-guardar-cambios').fadeIn();
}

/**
 * Limpiar cambios pendientes
 */
function clearPendingChanges() {
    editorState.cambiosPendientes = false;
    $('#btn-guardar-cambios').fadeOut();
}

/**
 * Cargar hablantes en select
 */
function loadHablantesInSelect(selector) {
    const hablantes = editorState.estructuraActual?.cabecera?.mapeo_hablantes || {};
    const $select = $(selector);
    
    $select.empty();
    
    if (selector.includes('nuevo')) {
        $select.append('<option value="">Seleccionar hablante...</option>');
    }
    
    Object.values(hablantes).forEach(function(nombre) {
        $select.append('<option value="' + nombre + '">' + nombre + '</option>');
    });
}

/**
 * Actualizar duración en modal de edición
 */
function updateEditDuration() {
    const inicio = parseFloat($('#edit-inicio').val()) || 0;
    const fin = parseFloat($('#edit-fin').val()) || 0;
    const duracion = fin - inicio;
    
    $('#edit-duracion').val(duracion > 0 ? duracion.toFixed(1) : '0.0');
}

/**
 * Actualizar duración en modal de nuevo segmento
 */
function updateNewDuration() {
    const inicio = parseFloat($('#nuevo-inicio').val()) || 0;
    const fin = parseFloat($('#nuevo-fin').val()) || 0;
    const duracion = fin - inicio;
    
    $('#preview-duracion').text(duracion > 0 ? duracion.toFixed(1) + ' segundos' : '0.0 segundos');
    $('#preview-tiempo').text(formatTime(inicio) + ' - ' + formatTime(fin));
}

/**
 * Actualizar vistas JSON
 */
function updateJSONViews() {
    if (!editorState.estructuraActual) return;
    
    // Conversación
    $('#json-conversacion').html(formatJSONForView(editorState.estructuraActual.conversacion));
    
    // Cabecera
    $('#json-cabecera').html(formatJSONForView(editorState.estructuraActual.cabecera));
    
    // Metadata
    $('#json-metadata').html(formatJSONForView(editorState.estructuraActual.metadata));
    
    // Completo
    $('#json-completo').html(formatJSONForView(editorState.estructuraActual));
}

/**
 * Formatear JSON para vista
 */
function formatJSONForView(objeto) {
    return JSON.stringify(objeto, null, 2)
        .replace(/"([^"]+)":/g, '<span class="json-key">"$1":</span>')
        .replace(/: "([^"]*)"/g, ': <span class="json-string">"$1"</span>')
        .replace(/: (\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
        .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
        .replace(/: null/g, ': <span class="json-null">null</span>');
}

/**
 * Mostrar/ocultar loading
 */
function showLoading(show) {
    if (show) {
        $('#loading-overlay').show();
    } else {
        $('#loading-overlay').hide();
    }
}

/**
 * Mostrar mensaje de éxito
 */
function showSuccess(mensaje) {
    if (typeof toastr !== 'undefined') {
        toastr.success(mensaje, 'Éxito');
    } else {
        alert('✅ ' + mensaje);
    }
}

/**
 * Mostrar mensaje de error
 */
function showError(mensaje) {
    if (typeof toastr !== 'undefined') {
        toastr.error(mensaje, 'Error');
    } else {
        alert('❌ ' + mensaje);
    }
}

/**
 * Obtener CSRF token
 */
function getCSRFToken() {
    return $('[name=csrfmiddlewaretoken]').val();
}

// Funciones placeholder para completar luego
function openManageHablantesModal() {
    showError('Gestión de hablantes - próximamente');
}

function openEditJSONModal() {
    showError('Editor JSON - próximamente');
}

function saveAllChanges() {
    showError('Guardar todos los cambios - próximamente');
}

function deleteCurrentSegment() {
    if (editorState.segmentoEditando) {
        confirmDeleteSegment(editorState.segmentoEditando.index);
        $('#modal-editar-segmento').modal('hide');
    }
}

// Inicializar cuando el documento esté listo
$(document).ready(function() {
    console.log('📝 Cargando Editor de Transcripción...');
    
    // Verificar toastr
    if (typeof toastr === 'undefined') {
        window.toastr = {
            success: function(msg) { alert('✅ ' + msg); },
            error: function(msg) { alert('❌ ' + msg); },
            warning: function(msg) { alert('⚠️ ' + msg); },
            info: function(msg) { alert('ℹ️ ' + msg); }
        };
    }
    
    // Configurar CSRF para AJAX
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
            }
        }
    });
    
    // Inicializar editor
    initEditor();
    
    // Exponer función global para cargar estructura
    window.TranscripcionEditor.cargarEstructura = loadStructure;
});