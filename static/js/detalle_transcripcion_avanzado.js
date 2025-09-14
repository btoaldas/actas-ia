/**
 * Editor Avanzado de Transcripciones
 * Permite editar completamente la estructura JSON de transcripciones
 * con interfaz intuitiva y validación en tiempo real
 */

class TranscripcionEditorAvanzado {
    constructor() {
        this.transcripcionId = window.TranscripcionEditor?.transcripcionId;
        this.urls = window.TranscripcionEditor?.urls || {};
        this.audioUrl = window.TranscripcionEditor?.audioUrl;
        
        // Estado del editor
        this.modoEdicion = false;
        this.cambiosPendientes = false;
        this.estructuraOriginal = null;
        this.estructuraActual = null;
        this.segmentoEditando = null;
        
        // Referencias DOM
        this.elementos = {
            chatMessages: $('#chat-messages'),
            conversacionContainer: $('#conversacion-container'),
            noConversacion: $('#no-conversacion'),
            loadingOverlay: $('#loading-overlay'),
            floatingSaveBtn: $('#btn-guardar-cambios'),
            indicadorModoEdicion: $('#indicador-modo-edicion'),
            toggleModoEdicion: $('#toggle-modo-edicion'),
            modoTexto: $('#modo-texto'),
            totalSegmentos: $('#total-segmentos'),
            totalHablantes: $('#total-hablantes'),
            fechaEdicion: $('#fecha-edicion'),
            audioPlayer: $('#audio-player')[0]
        };
        
        // Colores para hablantes
        this.coloresHablantes = [
            '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8',
            '#6f42c1', '#fd7e14', '#20c997', '#6c757d', '#f8f9fa'
        ];
        
        this.init();
    }
    
    /**
     * Inicialización del editor
     */
    init() {
        console.log('🚀 Inicializando Editor Avanzado de Transcripción');
        
        if (!this.transcripcionId) {
            console.error('❌ No se encontró ID de transcripción');
            return;
        }
        
        this.configurarEventos();
        this.cargarEstructura();
        
        console.log('✅ Editor Avanzado inicializado');
    }
    
    /**
     * Configurar todos los event listeners
     */
    configurarEventos() {
        // Toggle modo edición
        this.elementos.toggleModoEdicion.on('click', () => this.toggleModoEdicion());
        
        // Botones principales
        $('#btn-agregar-segmento').on('click', () => this.abrirModalAgregarSegmento());
        $('#btn-gestionar-hablantes').on('click', () => this.abrirModalGestionarHablantes());
        $('#btn-vista-json').on('click', () => this.abrirModalEditarJSON());
        
        // Botón flotante guardar
        this.elementos.floatingSaveBtn.on('click', () => this.guardarTodosLosCambios());
        
        // Eventos de modales
        this.configurarEventosModales();
        
        // Eventos de reproducción de audio
        if (this.elementos.audioPlayer) {
            $(this.elementos.audioPlayer).on('timeupdate', () => this.actualizarTiempoAudio());
        }
        
        // Detectar cambios no guardados
        $(window).on('beforeunload', (e) => {
            if (this.cambiosPendientes) {
                e.preventDefault();
                e.returnValue = '¿Estás seguro de que quieres salir? Hay cambios sin guardar.';
                return e.returnValue;
            }
        });
    }
    
    /**
     * Configurar eventos específicos de modales
     */
    configurarEventosModales() {
        // Modal editar segmento
        $('#btn-guardar-segmento').on('click', () => this.guardarSegmentoEditado());
        $('#btn-eliminar-segmento').on('click', () => this.eliminarSegmentoActual());
        
        // Modal agregar segmento
        $('#btn-crear-segmento').on('click', () => this.crearNuevoSegmento());
        
        // Actualizar duraciones automáticamente
        $('#edit-inicio, #edit-fin').on('input', () => this.actualizarDuracionEdit());
        $('#nuevo-inicio, #nuevo-fin').on('input', () => this.actualizarDuracionNuevo());
        
        // Modal gestionar hablantes
        $('#btn-guardar-hablante').on('click', () => this.guardarHablante());
        $('#btn-aplicar-cambios-hablantes').on('click', () => this.aplicarCambiosHablantes());
        
        // Modal editar JSON
        $('#btn-guardar-json').on('click', () => this.guardarEstructuraJSON());
        $('#btn-format-json').on('click', () => this.formatearJSON());
        $('#btn-validate-json').on('click', () => this.validarJSON());
    }
    
    /**
     * Cargar estructura completa desde el servidor
     */
    async cargarEstructura() {
        try {
            this.mostrarCargando(true);
            
            const response = await fetch(this.urls.obtenerEstructura, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.exito) {
                this.estructuraOriginal = JSON.parse(JSON.stringify(data.estructura));
                this.estructuraActual = data.estructura;
                this.renderizarConversacion();
                this.actualizarEstadisticas();
                this.actualizarVistaJSON();
                
                console.log('✅ Estructura cargada:', data);
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
            
        } catch (error) {
            console.error('❌ Error cargando estructura:', error);
            this.mostrarError('Error al cargar la transcripción: ' + error.message);
        } finally {
            this.mostrarCargando(false);
        }
    }
    
    /**
     * Renderizar la conversación en el chat
     */
    renderizarConversacion() {
        const conversacion = this.estructuraActual?.conversacion || [];
        const mapeoHablantes = this.estructuraActual?.cabecera?.mapeo_hablantes || {};
        
        if (conversacion.length === 0) {
            this.elementos.noConversacion.show();
            this.elementos.conversacionContainer.hide();
            return;
        }
        
        this.elementos.noConversacion.hide();
        this.elementos.conversacionContainer.show();
        
        let html = '';
        
        conversacion.forEach((segmento, index) => {
            const hablante = segmento.hablante || 'Desconocido';
            const texto = segmento.texto || '[Sin texto]';
            const inicio = parseFloat(segmento.inicio || 0);
            const fin = parseFloat(segmento.fin || 0);
            const duracion = fin - inicio;
            
            // Obtener color del hablante
            const colorIndex = Object.values(mapeoHablantes).indexOf(hablante);
            const color = this.coloresHablantes[colorIndex % this.coloresHablantes.length];
            
            // Formatear tiempo
            const tiempoTexto = this.formatearTiempo(inicio) + ' - ' + this.formatearTiempo(fin);
            
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
                        
                        <!-- Controles de segmento -->
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
        
        this.elementos.conversacionContainer.html(html);
        
        // Configurar eventos de los controles
        this.configurarEventosSegmentos();
    }
    
    /**
     * Configurar eventos para los controles de segmentos
     */
    configurarEventosSegmentos() {
        // Editar segmento
        $('.btn-edit-segment').on('click', (e) => {
            e.stopPropagation();
            const index = parseInt($(e.currentTarget).data('index'));
            this.editarSegmento(index);
        });
        
        // Reproducir segmento
        $('.btn-play-segment').on('click', (e) => {
            e.stopPropagation();
            const inicio = parseFloat($(e.currentTarget).data('inicio'));
            const fin = parseFloat($(e.currentTarget).data('fin'));
            this.reproducirSegmento(inicio, fin);
        });
        
        // Eliminar segmento
        $('.btn-delete-segment').on('click', (e) => {
            e.stopPropagation();
            const index = parseInt($(e.currentTarget).data('index'));
            this.confirmarEliminarSegmento(index);
        });
        
        // Click en mensaje para sincronizar audio
        $('.chat-message').on('click', (e) => {
            if (!$(e.target).closest('.segment-controls').length) {
                const inicio = parseFloat($(e.currentTarget).data('tiempo-inicio'));
                this.reproducirDesde(inicio);
            }
        });
        
        // Edición en línea en modo edición
        $('.editable-content').on('click', (e) => {
            if (this.modoEdicion) {
                e.stopPropagation();
                this.activarEdicionEnLinea($(e.currentTarget));
            }
        });
    }
    
    /**
     * Toggle modo edición
     */
    toggleModoEdicion() {
        this.modoEdicion = !this.modoEdicion;
        
        if (this.modoEdicion) {
            this.elementos.indicadorModoEdicion.show();
            this.elementos.modoTexto.text('Salir');
            this.elementos.toggleModoEdicion.removeClass('btn-warning').addClass('btn-danger');
            $('body').addClass('modo-edicion-activo');
        } else {
            this.elementos.indicadorModoEdicion.hide();
            this.elementos.modoTexto.text('Editar');
            this.elementos.toggleModoEdicion.removeClass('btn-danger').addClass('btn-warning');
            $('body').removeClass('modo-edicion-activo');
            this.desactivarEdicionEnLinea();
        }
        
        console.log('🔄 Modo edición:', this.modoEdicion ? 'ACTIVADO' : 'DESACTIVADO');
    }
    
    /**
     * Editar segmento específico
     */
    editarSegmento(index) {
        const conversacion = this.estructuraActual?.conversacion || [];
        
        if (index < 0 || index >= conversacion.length) {
            this.mostrarError('Segmento no válido');
            return;
        }
        
        const segmento = conversacion[index];
        this.segmentoEditando = { index, ...segmento };
        
        // Llenar modal con datos del segmento
        $('#edit-hablante').val(segmento.hablante);
        $('#edit-texto').val(segmento.texto);
        $('#edit-inicio').val(segmento.inicio);
        $('#edit-fin').val(segmento.fin);
        $('#edit-posicion').val(index + 1);
        $('#total-segmentos-edit').text(conversacion.length);
        
        this.actualizarDuracionEdit();
        this.cargarHablantesEnSelect('#edit-hablante');
        
        $('#modal-editar-segmento').modal('show');
    }
    
    /**
     * Guardar segmento editado
     */
    async guardarSegmentoEditado() {
        try {
            const datos = {
                indice: this.segmentoEditando.index,
                hablante: $('#edit-hablante').val().trim(),
                texto: $('#edit-texto').val().trim(),
                inicio: parseFloat($('#edit-inicio').val()),
                fin: parseFloat($('#edit-fin').val())
            };
            
            // Validaciones
            if (!datos.hablante) {
                this.mostrarError('El hablante es requerido');
                return;
            }
            
            if (!datos.texto) {
                this.mostrarError('El texto es requerido');
                return;
            }
            
            if (datos.inicio >= datos.fin) {
                this.mostrarError('El tiempo de inicio debe ser menor al tiempo de fin');
                return;
            }
            
            this.mostrarCargando(true);
            
            const response = await fetch(this.urls.editarSegmento, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(datos)
            });
            
            const result = await response.json();
            
            if (result.exito) {
                // Actualizar estructura local
                this.estructuraActual.conversacion[datos.indice] = result.segmento_actualizado;
                this.estructuraActual.texto_estructurado = result.texto_estructurado;
                this.estructuraActual.metadata = result.metadata;
                
                this.marcarCambiosPendientes();
                this.renderizarConversacion();
                this.actualizarEstadisticas();
                this.mostrarExito('Segmento actualizado correctamente');
                
                $('#modal-editar-segmento').modal('hide');
            } else {
                throw new Error(result.error || 'Error desconocido');
        } catch (error) {
            console.error('❌ Error editando segmento:', error);
            this.mostrarError('Error al editar segmento: ' + error.message);
        } finally {
            this.mostrarCargando(false);
        }
    }\n    \n    /**\n     * Abrir modal para agregar nuevo segmento\n     */\n    abrirModalAgregarSegmento() {\n        // Limpiar formulario\n        $('#form-agregar-segmento')[0].reset();\n        \n        // Cargar hablantes disponibles\n        this.cargarHablantesEnSelect('#nuevo-hablante');\n        \n        // Cargar posiciones disponibles\n        this.cargarPosicionesEnSelect();\n        \n        // Configurar tiempos por defecto\n        const ultimoSegmento = this.estructuraActual?.conversacion?.slice(-1)[0];\n        if (ultimoSegmento) {\n            $('#nuevo-inicio').val(ultimoSegmento.fin);\n            $('#nuevo-fin').val(ultimoSegmento.fin + 5); // 5 segundos por defecto\n        }\n        \n        this.actualizarDuracionNuevo();\n        \n        $('#modal-agregar-segmento').modal('show');\n    }\n    \n    /**\n     * Crear nuevo segmento\n     */\n    async crearNuevoSegmento() {\n        try {\n            const datos = {\n                hablante: $('#nuevo-hablante').val().trim(),\n                texto: $('#nuevo-texto').val().trim(),\n                inicio: parseFloat($('#nuevo-inicio').val()),\n                fin: parseFloat($('#nuevo-fin').val()),\n                posicion: $('#nuevo-posicion').val() || null\n            };\n            \n            // Validaciones\n            if (!datos.hablante) {\n                this.mostrarError('Selecciona un hablante');\n                return;\n            }\n            \n            if (!datos.texto) {\n                this.mostrarError('El texto es requerido');\n                return;\n            }\n            \n            if (datos.inicio >= datos.fin) {\n                this.mostrarError('El tiempo de inicio debe ser menor al tiempo de fin');\n                return;\n            }\n            \n            this.mostrarCargando(true);\n            \n            const response = await fetch(this.urls.agregarSegmento, {\n                method: 'POST',\n                headers: {\n                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify(datos)\n            });\n            \n            const result = await response.json();\n            \n            if (result.exito) {\n                // Actualizar estructura local\n                if (datos.posicion !== null) {\n                    this.estructuraActual.conversacion.splice(result.posicion, 0, result.segmento_creado);\n                } else {\n                    this.estructuraActual.conversacion.push(result.segmento_creado);\n                }\n                \n                this.estructuraActual.texto_estructurado = result.texto_estructurado;\n                this.estructuraActual.metadata = result.metadata;\n                \n                this.marcarCambiosPendientes();\n                this.renderizarConversacion();\n                this.actualizarEstadisticas();\n                this.mostrarExito('Nuevo segmento agregado correctamente');\n                \n                $('#modal-agregar-segmento').modal('hide');\n            } else {\n                throw new Error(result.error || 'Error desconocido');\n            }\n            \n        } catch (error) {\n            console.error('❌ Error creando segmento:', error);\n            this.mostrarError('Error al crear segmento: ' + error.message);\n        } finally {\n            this.mostrarCargando(false);\n        }\n    }\n    \n    /**\n     * Confirmar eliminación de segmento\n     */\n    confirmarEliminarSegmento(index) {\n        const conversacion = this.estructuraActual?.conversacion || [];\n        \n        if (index < 0 || index >= conversacion.length) {\n            this.mostrarError('Segmento no válido');\n            return;\n        }\n        \n        const segmento = conversacion[index];\n        const textoCorto = segmento.texto.length > 50 ? \n            segmento.texto.substring(0, 50) + '...' : \n            segmento.texto;\n        \n        if (confirm(`¿Estás seguro de que quieres eliminar este segmento?\\n\\n\"${textoCorto}\"\\n\\nEsta acción no se puede deshacer.`)) {\n            this.eliminarSegmento(index);\n        }\n    }\n    \n    /**\n     * Eliminar segmento\n     */\n    async eliminarSegmento(index) {\n        try {\n            this.mostrarCargando(true);\n            \n            const response = await fetch(this.urls.eliminarSegmento, {\n                method: 'POST',\n                headers: {\n                    'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val(),\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify({ indice: index })\n            });\n            \n            const result = await response.json();\n            \n            if (result.exito) {\n                // Actualizar estructura local\n                this.estructuraActual.conversacion.splice(index, 1);\n                this.estructuraActual.texto_estructurado = result.texto_estructurado;\n                this.estructuraActual.metadata = result.metadata;\n                \n                this.marcarCambiosPendientes();\n                this.renderizarConversacion();\n                this.actualizarEstadisticas();\n                this.mostrarExito('Segmento eliminado correctamente');\n            } else {\n                throw new Error(result.error || 'Error desconocido');\n            }\n            \n        } catch (error) {\n            console.error('❌ Error eliminando segmento:', error);\n            this.mostrarError('Error al eliminar segmento: ' + error.message);\n        } finally {\n            this.mostrarCargando(false);\n        }\n    }\n    \n    /**\n     * Reproducir segmento de audio\n     */\n    reproducirSegmento(inicio, fin) {\n        if (!this.elementos.audioPlayer) {\n            this.mostrarError('Reproductor de audio no disponible');\n            return;\n        }\n        \n        this.elementos.audioPlayer.currentTime = inicio;\n        this.elementos.audioPlayer.play();\n        \n        // Pausar al final del segmento\n        const pausarAlFinal = () => {\n            if (this.elementos.audioPlayer.currentTime >= fin) {\n                this.elementos.audioPlayer.pause();\n                this.elementos.audioPlayer.removeEventListener('timeupdate', pausarAlFinal);\n            }\n        };\n        \n        this.elementos.audioPlayer.addEventListener('timeupdate', pausarAlFinal);\n        \n        // Resaltar segmento que se está reproduciendo\n        $('.chat-message').removeClass('seleccionado');\n        $(`.chat-message[data-tiempo-inicio=\"${inicio}\"]`).addClass('seleccionado');\n    }\n    \n    /**\n     * Reproducir desde tiempo específico\n     */\n    reproducirDesde(tiempo) {\n        if (!this.elementos.audioPlayer) return;\n        \n        this.elementos.audioPlayer.currentTime = tiempo;\n        this.elementos.audioPlayer.play();\n    }\n    \n    /**\n     * Formatear tiempo en MM:SS\n     */\n    formatearTiempo(segundos) {\n        const minutos = Math.floor(segundos / 60);\n        const segs = Math.floor(segundos % 60);\n        return `${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;\n    }\n    \n    /**\n     * Actualizar estadísticas en la interfaz\n     */\n    actualizarEstadisticas() {\n        const conversacion = this.estructuraActual?.conversacion || [];\n        const hablantes = this.estructuraActual?.cabecera?.mapeo_hablantes || {};\n        const metadata = this.estructuraActual?.metadata || {};\n        \n        this.elementos.totalSegmentos.text(conversacion.length);\n        this.elementos.totalHablantes.text(Object.keys(hablantes).length);\n        \n        if (metadata.fecha_ultima_edicion) {\n            const fecha = new Date(metadata.fecha_ultima_edicion);\n            this.elementos.fechaEdicion.text(fecha.toLocaleString());\n        }\n        \n        // Actualizar contador en el chat\n        $('#num-mensajes').text(conversacion.length);\n    }\n    \n    /**\n     * Marcar que hay cambios pendientes\n     */\n    marcarCambiosPendientes() {\n        this.cambiosPendientes = true;\n        this.elementos.floatingSaveBtn.fadeIn();\n    }\n    \n    /**\n     * Limpiar cambios pendientes\n     */\n    limpiarCambiosPendientes() {\n        this.cambiosPendientes = false;\n        this.elementos.floatingSaveBtn.fadeOut();\n    }\n    \n    /**\n     * Mostrar/ocultar indicador de carga\n     */\n    mostrarCargando(mostrar) {\n        if (mostrar) {\n            this.elementos.loadingOverlay.show();\n        } else {\n            this.elementos.loadingOverlay.hide();\n        }\n    }\n    \n    /**\n     * Mostrar mensaje de éxito\n     */\n    mostrarExito(mensaje) {\n        toastr.success(mensaje, 'Éxito', {\n            timeOut: 3000,\n            positionClass: 'toast-top-right'\n        });\n    }\n    \n    /**\n     * Mostrar mensaje de error\n     */\n    mostrarError(mensaje) {\n        toastr.error(mensaje, 'Error', {\n            timeOut: 5000,\n            positionClass: 'toast-top-right'\n        });\n    }\n    \n    /**\n     * Cargar hablantes en select\n     */\n    cargarHablantesEnSelect(selector) {\n        const hablantes = this.estructuraActual?.cabecera?.mapeo_hablantes || {};\n        const $select = $(selector);\n        \n        $select.empty();\n        \n        if (selector.includes('nuevo')) {\n            $select.append('<option value=\"\">Seleccionar hablante...</option>');\n        }\n        \n        Object.values(hablantes).forEach(nombre => {\n            $select.append(`<option value=\"${nombre}\">${nombre}</option>`);\n        });\n    }\n    \n    /**\n     * Cargar posiciones disponibles en select\n     */\n    cargarPosicionesEnSelect() {\n        const conversacion = this.estructuraActual?.conversacion || [];\n        const $select = $('#nuevo-posicion');\n        \n        $select.empty();\n        $select.append('<option value=\"\">Al final de la conversación</option>');\n        \n        conversacion.forEach((segmento, index) => {\n            const textoCorto = segmento.texto.length > 30 ? \n                segmento.texto.substring(0, 30) + '...' : \n                segmento.texto;\n            $select.append(`<option value=\"${index}\">Antes de: \"${textoCorto}\"</option>`);\n        });\n    }\n    \n    /**\n     * Actualizar duración calculada en modal de edición\n     */\n    actualizarDuracionEdit() {\n        const inicio = parseFloat($('#edit-inicio').val()) || 0;\n        const fin = parseFloat($('#edit-fin').val()) || 0;\n        const duracion = fin - inicio;\n        \n        $('#edit-duracion').val(duracion > 0 ? duracion.toFixed(1) : '0.0');\n    }\n    \n    /**\n     * Actualizar duración calculada en modal de nuevo segmento\n     */\n    actualizarDuracionNuevo() {\n        const inicio = parseFloat($('#nuevo-inicio').val()) || 0;\n        const fin = parseFloat($('#nuevo-fin').val()) || 0;\n        const duracion = fin - inicio;\n        \n        $('#preview-duracion').text(duracion > 0 ? duracion.toFixed(1) + ' segundos' : '0.0 segundos');\n        $('#preview-tiempo').text(this.formatearTiempo(inicio) + ' - ' + this.formatearTiempo(fin));\n        \n        const posicion = $('#nuevo-posicion').val();\n        $('#preview-posicion').text(posicion ? `Posición ${parseInt(posicion) + 1}` : 'Al final');\n    }\n    \n    /**\n     * Actualizar vista JSON en tabs\n     */\n    actualizarVistaJSON() {\n        if (!this.estructuraActual) return;\n        \n        // Conversación\n        $('#json-conversacion').html(this.formatearJSONParaVista(this.estructuraActual.conversacion));\n        \n        // Cabecera\n        $('#json-cabecera').html(this.formatearJSONParaVista(this.estructuraActual.cabecera));\n        \n        // Metadata\n        $('#json-metadata').html(this.formatearJSONParaVista(this.estructuraActual.metadata));\n        \n        // Completo\n        $('#json-completo').html(this.formatearJSONParaVista(this.estructuraActual));\n    }\n    \n    /**\n     * Formatear JSON para vista con sintaxis coloreada\n     */\n    formatearJSONParaVista(objeto) {\n        return JSON.stringify(objeto, null, 2)\n            .replace(/\"([^\"]+)\":/g, '<span class=\"json-key\">\"$1\":</span>')\n            .replace(/: \"([^\"]*)\"/g, ': <span class=\"json-string\">\"$1\"</span>')\n            .replace(/: (\\d+\\.?\\d*)/g, ': <span class=\"json-number\">$1</span>')\n            .replace(/: (true|false)/g, ': <span class=\"json-boolean\">$1</span>')\n            .replace(/: null/g, ': <span class=\"json-null\">null</span>');\n    }\n    \n    // Métodos adicionales para gestión de hablantes y JSON se implementarán en la siguiente parte...\n}\n\n// Inicializar el editor cuando el documento esté listo\n$(document).ready(function() {\n    // Verificar si toastr está disponible, si no, usar alertas básicas\n    if (typeof toastr === 'undefined') {\n        window.toastr = {\n            success: (msg) => alert('✅ ' + msg),\n            error: (msg) => alert('❌ ' + msg),\n            warning: (msg) => alert('⚠️ ' + msg),\n            info: (msg) => alert('ℹ️ ' + msg)\n        };\n    }\n    \n    // Inicializar editor\n    window.transcripcionEditor = new TranscripcionEditorAvanzado();\n    \n    // Exponer función de carga para el template\n    window.TranscripcionEditor = window.TranscripcionEditor || {};\n    window.TranscripcionEditor.cargarEstructura = () => {\n        return window.transcripcionEditor.cargarEstructura();\n    };\n});\n\n// Estilos para coloreo de JSON\nconst estilosJSON = `\n<style>\n.json-key { color: #0366d6; font-weight: bold; }\n.json-string { color: #032f62; }\n.json-number { color: #005cc5; }\n.json-boolean { color: #d73a49; }\n.json-null { color: #6f42c1; }\n</style>\n`;\n$('head').append(estilosJSON);\n