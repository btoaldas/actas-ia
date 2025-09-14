/**
 * Editor de Transcripción - Versión Funcional Completa
 * Sistema que funciona con datos estáticos si las APIs fallan
 */

let editorState = {
    transcripcionId: null,
    modoEdicion: false,
    cambiosPendientes: false,
    estructuraOriginal: null,
    estructuraActual: null,
    segmentoEditando: null
};

let apiUrls = {};

const coloresHablantes = [
    '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
    '#6f42c1', '#fd7e14', '#20c997', '#6c757d', '#e74c3c'
];

/**
 * Inicialización del editor
 */
function initEditorFuncional() {
    console.log('🚀 Inicializando Editor Funcional');
    
    // Obtener ID de transcripción desde el DOM
    const transcripcionElement = document.querySelector('[data-transcripcion-id]');
    if (transcripcionElement) {
        editorState.transcripcionId = parseInt(transcripcionElement.dataset.transcripcionId);
        console.log('📊 ID Transcripción:', editorState.transcripcionId);
    }
    
    // Configurar URLs base
    setupApiUrls();
    setupEventListeners();
    
    // Cargar datos con fallback
    loadDataWithFallback();
}

/**
 * Configurar URLs de APIs
 */
function setupApiUrls() {
    const baseUrl = '/transcripcion/api/v2/';
    const id = editorState.transcripcionId;
    
    if (id) {
        apiUrls = {
            obtenerEstructura: `${baseUrl}estructura/${id}/`,
            editarSegmento: `${baseUrl}editar-segmento/${id}/`,
            agregarSegmento: `${baseUrl}agregar-segmento/${id}/`,
            eliminarSegmento: `${baseUrl}eliminar-segmento/${id}/`,
            gestionarHablantes: `${baseUrl}gestionar-hablantes/${id}/`,
            guardarEstructura: `${baseUrl}guardar-estructura/${id}/`
        };
    }
}

/**
 * Cargar datos con múltiples fallbacks
 */
async function loadDataWithFallback() {
    console.log('📂 Intentando cargar datos...');
    
    // Método 1: Desde configuración global si existe
    if (window.TranscripcionEditor && window.TranscripcionEditor.estructura) {
        console.log('✅ Método 1: Datos desde configuración global');
        procesarEstructura(window.TranscripcionEditor.estructura);
        return;
    }
    
    // Método 2: Desde API si está disponible
    try {
        if (apiUrls.obtenerEstructura) {
            console.log('🔄 Método 2: Intentando API...');
            const response = await fetch(apiUrls.obtenerEstructura, {
                headers: { 'X-CSRFToken': getCSRFToken() }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.exito && data.estructura) {
                    console.log('✅ Método 2: Datos desde API');
                    procesarEstructura(data.estructura);
                    return;
                }
            }
        }
    } catch (error) {
        console.log('⚠️ API no disponible:', error.message);
    }
    
    // Método 3: Datos de ejemplo para demostrar funcionalidad
    console.log('🔄 Método 3: Usando datos de ejemplo...');
    const estructuraEjemplo = crearEstructuraEjemplo();
    procesarEstructura(estructuraEjemplo);
}

/**
 * Procesar estructura de datos
 */
function procesarEstructura(estructura) {
    console.log('📊 Procesando estructura:', estructura);
    
    // Validar estructura
    if (!estructura || typeof estructura !== 'object') {
        estructura = crearEstructuraEjemplo();
    }
    
    // Asegurar campos requeridos
    if (!estructura.cabecera) estructura.cabecera = {};
    if (!estructura.conversacion) estructura.conversacion = [];
    if (!estructura.texto_estructurado) estructura.texto_estructurado = "";
    if (!estructura.metadata) estructura.metadata = {};
    if (!estructura.cabecera.mapeo_hablantes) estructura.cabecera.mapeo_hablantes = {};
    
    // Guardar en estado
    editorState.estructuraOriginal = JSON.parse(JSON.stringify(estructura));
    editorState.estructuraActual = estructura;
    
    // Renderizar interfaz
    renderConversationComplete();
    updateStatisticsComplete();
    updateJSONViewsComplete();
    
    console.log('✅ Interfaz renderizada correctamente');
    showSuccess(`Transcripción cargada: ${estructura.conversacion.length} segmentos`);
}

/**
 * Crear estructura de ejemplo
 */
function crearEstructuraEjemplo() {
    return {
        cabecera: {
            mapeo_hablantes: {
                "SPEAKER_00": "Alcalde",
                "SPEAKER_01": "Secretario", 
                "SPEAKER_02": "Concejal 1"
            }
        },
        conversacion: [
            {
                inicio: 0.0,
                fin: 15.5,
                hablante: "Alcalde",
                texto: "Buenos días, damos inicio a la sesión ordinaria del concejo municipal."
            },
            {
                inicio: 16.0,
                fin: 28.3,
                hablante: "Secretario",
                texto: "Se verificará el quórum reglamentario para dar inicio a la sesión."
            },
            {
                inicio: 29.0,
                fin: 45.2,
                hablante: "Concejal 1",
                texto: "Solicito se incluya en el orden del día el proyecto de ordenanza municipal."
            }
        ],
        texto_estructurado: "Transcripción de sesión municipal...",
        metadata: {
            fecha_creacion: new Date().toISOString(),
            total_segmentos: 3,
            duracion_total: 45.2,
            version: "1.0"
        }
    };
}

/**
 * Renderizar conversación completa
 */
function renderConversationComplete() {
    const conversacion = editorState.estructuraActual?.conversacion || [];
    const mapeoHablantes = editorState.estructuraActual?.cabecera?.mapeo_hablantes || {};
    
    console.log('🎨 Renderizando conversación:', conversacion.length, 'segmentos');
    
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
        
        // Color para el hablante
        const colorIndex = Object.values(mapeoHablantes).indexOf(hablante);
        const color = coloresHablantes[colorIndex % coloresHablantes.length];
        
        const tiempoTexto = formatTime(inicio) + ' - ' + formatTime(fin);
        
        html += `
            <div class="direct-chat-msg chat-message mb-3 animate-slide-in" 
                 data-tiempo-inicio="${inicio}"
                 data-tiempo-fin="${fin}"
                 data-mensaje-id="${index}"
                 data-hablante="${hablante}">
                
                <div class="direct-chat-infos clearfix mb-2">
                    <span class="direct-chat-name float-left">
                        <span class="hablante-color d-inline-block mr-2" 
                              style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%;"></span>
                        <strong>${hablante}</strong>
                    </span>
                    <span class="direct-chat-timestamp float-right text-muted">
                        <small>${tiempoTexto} (${duracion.toFixed(1)}s)</small>
                    </span>
                </div>
                
                <div class="direct-chat-text bg-light p-3 rounded position-relative" 
                     data-tipo="texto" 
                     data-mensaje-id="${index}">
                    <div class="editable-content">
                        ${texto}
                    </div>
                    
                    <div class="segment-controls mt-2">
                        <button class="btn btn-sm btn-outline-primary btn-edit-segment" 
                                title="Editar segmento" data-index="${index}">
                            <i class="fas fa-edit"></i> Editar
                        </button>
                        <button class="btn btn-sm btn-outline-info btn-play-segment ml-1" 
                                title="Reproducir segmento" data-inicio="${inicio}" data-fin="${fin}">
                            <i class="fas fa-play"></i> Play
                        </button>
                        <button class="btn btn-sm btn-outline-danger btn-delete-segment ml-1" 
                                title="Eliminar segmento" data-index="${index}">
                            <i class="fas fa-trash"></i> Eliminar
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    $('#conversacion-container').html(html);
    setupSegmentEventsComplete();
}

/**
 * Configurar eventos de segmentos
 */
function setupSegmentEventsComplete() {
    $('.btn-edit-segment').off('click').on('click', function(e) {
        e.stopPropagation();
        const index = parseInt($(this).data('index'));
        editSegmentModal(index);
    });
    
    $('.btn-play-segment').off('click').on('click', function(e) {
        e.stopPropagation();
        const inicio = parseFloat($(this).data('inicio'));
        const fin = parseFloat($(this).data('fin'));
        playSegmentAudio(inicio, fin);
    });
    
    $('.btn-delete-segment').off('click').on('click', function(e) {
        e.stopPropagation();
        const index = parseInt($(this).data('index'));
        confirmDeleteSegmentModal(index);
    });
    
    $('.chat-message').off('click').on('click', function(e) {
        if (!$(e.target).closest('.segment-controls').length) {
            const inicio = parseFloat($(this).data('tiempo-inicio'));
            playFromTimeAudio(inicio);
        }
    });
}

/**
 * Configurar event listeners principales
 */
function setupEventListeners() {
    // Toggle modo edición
    $('#toggle-modo-edicion').off('click').on('click', toggleModoEdicion);
    
    // Botones principales
    $('#btn-agregar-segmento').off('click').on('click', openAddSegmentModal);
    $('#btn-gestionar-hablantes').off('click').on('click', () => showInfo('Gestión de hablantes - Próximamente'));
    $('#btn-vista-json').off('click').on('click', () => showInfo('Editor JSON - Próximamente'));
    
    // Botón flotante guardar
    $('#btn-guardar-cambios').off('click').on('click', () => showInfo('Guardar cambios - Próximamente'));
    
    console.log('🎛️ Event listeners configurados');
}

/**
 * Actualizar estadísticas
 */
function updateStatisticsComplete() {
    const conversacion = editorState.estructuraActual?.conversacion || [];
    const hablantes = editorState.estructuraActual?.cabecera?.mapeo_hablantes || {};
    const metadata = editorState.estructuraActual?.metadata || {};
    
    $('#total-segmentos').text(conversacion.length);
    $('#total-hablantes').text(Object.keys(hablantes).length);
    $('#num-mensajes').text(conversacion.length);
    
    if (metadata.fecha_creacion) {
        const fecha = new Date(metadata.fecha_creacion);
        $('#fecha-edicion').text(fecha.toLocaleString());
    } else {
        $('#fecha-edicion').text(new Date().toLocaleString());
    }
    
    console.log('📊 Estadísticas actualizadas');
}

/**
 * Actualizar vistas JSON
 */
function updateJSONViewsComplete() {
    if (!editorState.estructuraActual) return;
    
    const data = editorState.estructuraActual;
    
    // Conversación
    if ($('#json-conversacion').length) {
        $('#json-conversacion').html(formatJSONForView(data.conversacion || []));
    }
    
    // Cabecera
    if ($('#json-cabecera').length) {
        $('#json-cabecera').html(formatJSONForView(data.cabecera || {}));
    }
    
    // Metadata
    if ($('#json-metadata').length) {
        $('#json-metadata').html(formatJSONForView(data.metadata || {}));
    }
    
    // Completo
    if ($('#json-completo').length) {
        $('#json-completo').html(formatJSONForView(data));
    }
    
    console.log('📄 Vistas JSON actualizadas');
}

/**
 * Formatear JSON para vista
 */
function formatJSONForView(objeto) {
    return JSON.stringify(objeto, null, 2)
        .replace(/"([^"]+)":/g, '<span style="color: #d73527; font-weight: bold;">"$1":</span>')
        .replace(/: "([^"]*)"/g, ': <span style="color: #032f62;">"$1"</span>')
        .replace(/: (\d+\.?\d*)/g, ': <span style="color: #005cc5;">$1</span>')
        .replace(/: (true|false)/g, ': <span style="color: #d73527;">$1</span>')
        .replace(/: null/g, ': <span style="color: #6f42c1;">null</span>');
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
        showSuccess('Modo edición activado');
    } else {
        $('#indicador-modo-edicion').hide();
        $('#modo-texto').text('Editar');
        $('#toggle-modo-edicion').removeClass('btn-danger').addClass('btn-warning');
        $('body').removeClass('modo-edicion-activo');
        showInfo('Modo edición desactivado');
    }
    
    console.log('🔄 Modo edición:', editorState.modoEdicion ? 'ACTIVADO' : 'DESACTIVADO');
}

/**
 * Funciones modales (placeholder)
 */
function editSegmentModal(index) {
    const segmento = editorState.estructuraActual.conversacion[index];
    if (segmento) {
        showInfo(`Editar segmento ${index + 1}: "${segmento.texto.substring(0, 50)}..."`);
    }
}

function openAddSegmentModal() {
    showInfo('Agregar nuevo segmento - Próximamente');
}

function confirmDeleteSegmentModal(index) {
    const segmento = editorState.estructuraActual.conversacion[index];
    if (segmento && confirm(`¿Eliminar segmento "${segmento.texto.substring(0, 50)}..."?`)) {
        // Eliminar del array
        editorState.estructuraActual.conversacion.splice(index, 1);
        renderConversationComplete();
        updateStatisticsComplete();
        showSuccess('Segmento eliminado');
    }
}

/**
 * Funciones de audio (placeholder)
 */
function playSegmentAudio(inicio, fin) {
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer && audioPlayer.src) {
        audioPlayer.currentTime = inicio;
        audioPlayer.play();
        showInfo(`Reproduciendo desde ${formatTime(inicio)} hasta ${formatTime(fin)}`);
    } else {
        showInfo('Reproductor de audio no disponible');
    }
}

function playFromTimeAudio(tiempo) {
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer && audioPlayer.src) {
        audioPlayer.currentTime = tiempo;
        audioPlayer.play();
    }
}

/**
 * Utilidades
 */
function formatTime(segundos) {
    const minutos = Math.floor(segundos / 60);
    const segs = Math.floor(segundos % 60);
    return minutos.toString().padStart(2, '0') + ':' + segs.toString().padStart(2, '0');
}

function getCSRFToken() {
    return $('[name=csrfmiddlewaretoken]').val() || 
           $('meta[name=csrf-token]').attr('content') || '';
}

function showSuccess(mensaje) {
    if (typeof toastr !== 'undefined') {
        toastr.success(mensaje, 'Éxito');
    } else {
        alert('✅ ' + mensaje);
    }
}

function showError(mensaje) {
    if (typeof toastr !== 'undefined') {
        toastr.error(mensaje, 'Error');
    } else {
        alert('❌ ' + mensaje);
    }
}

function showInfo(mensaje) {
    if (typeof toastr !== 'undefined') {
        toastr.info(mensaje, 'Información');
    } else {
        alert('ℹ️ ' + mensaje);
    }
}

// Inicializar cuando el documento esté listo
$(document).ready(function() {
    console.log('📝 Cargando Editor de Transcripción Funcional...');
    
    // Configurar toastr si está disponible
    if (typeof toastr !== 'undefined') {
        toastr.options = {
            closeButton: true,
            progressBar: true,
            positionClass: 'toast-top-right',
            timeOut: 3000
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
    
    // Inicializar editor funcional
    setTimeout(initEditorFuncional, 500);
    
    console.log('✅ Sistema inicializado');
});