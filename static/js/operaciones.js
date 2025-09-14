/**
 * JavaScript para el módulo de Operaciones del Sistema
 * Actas IA - Sistema de Gestión Municipal
 */

class OperacionesManager {
    constructor() {
        this.autoRefreshInterval = null;
        this.refreshRate = 10000; // 10 segundos
        this.init();
    }

    init() {
        this.bindEvents();
        this.initTooltips();
        
        // Auto-iniciar refresh si hay operaciones en progreso
        if (this.hasActiveOperations()) {
            this.startAutoRefresh();
        }
    }

    bindEvents() {
        // Eventos del modal de nueva operación
        $('#modalTipo').on('change', this.onTipoOperacionChange.bind(this));
        
        // Eventos de formularios
        $('form[data-form-type="operacion"]').on('submit', this.onSubmitOperacion.bind(this));
        
        // Eventos de botones de acción rápida
        $('.btn-operacion-rapida').on('click', this.onOperacionRapida.bind(this));
        
        // Eventos de cancelación
        $('.btn-cancelar-operacion').on('click', this.onCancelarOperacion.bind(this));
        
        // Eventos de descarga
        $('.btn-descargar-resultado').on('click', this.onDescargarResultado.bind(this));
        
        // Eventos del modal de configuración
        $('.btn-nueva-configuracion').on('click', this.onNuevaConfiguracion.bind(this));
        
        // Limpiar interval al salir
        $(window).on('beforeunload', this.cleanup.bind(this));
    }

    initTooltips() {
        $('[data-toggle="tooltip"]').tooltip();
        
        // Tooltips personalizados para estados
        $('.operation-status').each(function() {
            const estado = $(this).data('estado') || $(this).text().toLowerCase();
            let tooltip = '';
            
            switch(estado) {
                case 'pending':
                    tooltip = 'Operación creada, esperando ser procesada';
                    break;
                case 'queued':
                    tooltip = 'En cola de procesamiento, será ejecutada pronto';
                    break;
                case 'running':
                    tooltip = 'Operación en ejecución';
                    break;
                case 'completed':
                    tooltip = 'Operación completada exitosamente';
                    break;
                case 'failed':
                    tooltip = 'La operación falló durante la ejecución';
                    break;
                case 'cancelled':
                    tooltip = 'Operación cancelada por el usuario';
                    break;
            }
            
            if (tooltip) {
                $(this).attr('title', tooltip).tooltip();
            }
        });
    }

    // Manejo del cambio de tipo de operación en el modal
    onTipoOperacionChange(event) {
        const tipo = $(event.target).val();
        
        // Ocultar todos los contenedores de parámetros
        $('.parametros-container').slideUp(300);
        
        if (tipo) {
            // Mostrar el contenedor específico
            const containerId = `#parametros-${tipo.replace('_', '-')}`;
            $(containerId).slideDown(300);
            
            // Cargar parámetros específicos si es necesario
            this.loadParametrosEspecificos(tipo);
        }
    }

    // Cargar parámetros específicos para cada tipo de operación
    loadParametrosEspecificos(tipo) {
        switch(tipo) {
            case 'probar_proveedores':
                this.loadProveedoresDisponibles();
                break;
            case 'reiniciar_servicios':
                this.loadServiciosDisponibles();
                break;
        }
    }

    // Cargar proveedores disponibles
    loadProveedoresDisponibles() {
        const container = $('#parametros-proveedores');
        const loadingHtml = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Cargando proveedores...</div>';
        
        container.find('.proveedores-list').html(loadingHtml);
        
        $.get('/generador-actas/api/proveedores-disponibles/')
            .done((response) => {
                if (response.success && response.data.length > 0) {
                    const proveedoresHtml = response.data.map(proveedor => `
                        <div class="form-check">
                            <input type="checkbox" name="proveedores" value="${proveedor.id}" 
                                   class="form-check-input" id="prov_${proveedor.id}">
                            <label class="form-check-label" for="prov_${proveedor.id}">
                                ${proveedor.nombre} 
                                <span class="badge badge-${proveedor.activo ? 'success' : 'warning'} ml-1">
                                    ${proveedor.activo ? 'Activo' : 'Inactivo'}
                                </span>
                            </label>
                        </div>
                    `).join('');
                    
                    container.find('.proveedores-list').html(proveedoresHtml);
                } else {
                    container.find('.proveedores-list').html('<p class="text-muted">No hay proveedores configurados</p>');
                }
            })
            .fail(() => {
                container.find('.proveedores-list').html('<p class="text-danger">Error al cargar proveedores</p>');
            });
    }

    // Cargar servicios disponibles
    loadServiciosDisponibles() {
        // Esta función verificaría qué servicios están activos
        $.get('/generador-actas/api/estado-servicios/')
            .done((response) => {
                if (response.success) {
                    // Actualizar checkboxes según el estado actual
                    if (!response.data.celery.activo) {
                        $('#serv_celery').prop('checked', true);
                    }
                    if (!response.data.redis.activo) {
                        $('#serv_redis').prop('checked', true);
                    }
                }
            });
    }

    // Manejo de operaciones rápidas
    onOperacionRapida(event) {
        event.preventDefault();
        const tipo = $(event.currentTarget).data('tipo');
        
        if (tipo) {
            $('#modalTipo').val(tipo).trigger('change');
            $('#nuevaOperacionModal').modal('show');
        }
    }

    // Manejo del envío de operación
    onSubmitOperacion(event) {
        event.preventDefault();
        
        const form = $(event.target);
        const formData = new FormData(form[0]);
        const submitBtn = form.find('button[type="submit"]');
        
        // Deshabilitar botón y mostrar loading
        submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin mr-1"></i> Iniciando...');
        
        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false
        })
        .done((response) => {
            if (response.success) {
                this.showNotification('Operación iniciada exitosamente', 'success');
                
                // Cerrar modal y redirigir o refrescar
                $('#nuevaOperacionModal').modal('hide');
                
                if (response.operacion_id) {
                    // Redirigir al detalle de la operación
                    window.location.href = `/generador-actas/operaciones/${response.operacion_id}/`;
                } else {
                    // Refrescar página actual
                    setTimeout(() => window.location.reload(), 1000);
                }
            } else {
                this.showNotification(response.message || 'Error al iniciar la operación', 'error');
            }
        })
        .fail((xhr) => {
            let message = 'Error de conexión';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                message = xhr.responseJSON.message;
            }
            this.showNotification(message, 'error');
        })
        .always(() => {
            // Rehabilitar botón
            submitBtn.prop('disabled', false).html('<i class="fas fa-play mr-1"></i> Iniciar Operación');
        });
    }

    // Cancelar operación
    onCancelarOperacion(event) {
        event.preventDefault();
        
        const operacionId = $(event.currentTarget).data('operacion-id');
        
        if (!operacionId) return;
        
        this.showConfirmDialog(
            '¿Cancelar Operación?',
            '¿Está seguro de que desea cancelar esta operación? Esta acción no se puede deshacer.',
            () => this.cancelarOperacion(operacionId)
        );
    }

    // Ejecutar cancelación
    cancelarOperacion(operacionId) {
        $.post(`/generador-actas/api/operaciones/${operacionId}/cancelar/`, {
            csrfmiddlewaretoken: this.getCSRFToken()
        })
        .done((response) => {
            if (response.success) {
                this.showNotification('Operación cancelada exitosamente', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                this.showNotification(response.message || 'Error al cancelar la operación', 'error');
            }
        })
        .fail(() => {
            this.showNotification('Error de conexión al cancelar la operación', 'error');
        });
    }

    // Descargar resultado
    onDescargarResultado(event) {
        event.preventDefault();
        
        const operacionId = $(event.currentTarget).data('operacion-id');
        const url = `/generador-actas/api/operaciones/${operacionId}/descargar/`;
        
        // Crear enlace temporal para descarga
        const link = document.createElement('a');
        link.href = url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Auto-refresh de datos
    startAutoRefresh() {
        if (this.autoRefreshInterval) {
            this.stopAutoRefresh();
        }
        
        this.autoRefreshInterval = setInterval(() => {
            this.refreshOperationsData();
        }, this.refreshRate);
        
        console.log('Auto-refresh iniciado');
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
            console.log('Auto-refresh detenido');
        }
    }

    // Refrescar datos de operaciones
    refreshOperationsData() {
        // Si estamos en la página de detalle de operación
        if (window.location.pathname.includes('/operaciones/') && window.location.pathname.endsWith('/')) {
            this.refreshOperationDetail();
        } 
        // Si estamos en la lista de operaciones
        else if (window.location.pathname.includes('/operaciones')) {
            this.refreshOperationsList();
        }
    }

    // Refrescar detalle de operación
    refreshOperationDetail() {
        const operacionId = this.extractOperationIdFromURL();
        
        if (!operacionId) return;
        
        $.get(`/generador-actas/api/operaciones/${operacionId}/estado/`)
            .done((response) => {
                if (response.success) {
                    this.updateOperationDetailUI(response.data);
                    
                    // Detener auto-refresh si la operación terminó
                    if (['completed', 'failed', 'cancelled'].includes(response.data.estado)) {
                        this.stopAutoRefresh();
                    }
                }
            })
            .fail((xhr) => {
                // Si hay error 404, la operación no existe
                if (xhr.status === 404) {
                    this.stopAutoRefresh();
                }
            });
    }

    // Actualizar UI del detalle de operación
    updateOperationDetailUI(data) {
        // Actualizar progreso
        const progressBar = $('.progress-bar');
        progressBar.css('width', data.progreso + '%')
                  .attr('aria-valuenow', data.progreso);
        
        // Actualizar texto de progreso
        $('.progress-text, .progreso-numero').text(data.progreso + '%');
        
        // Actualizar estado si cambió
        const currentEstado = $('.operation-status').data('estado');
        if (currentEstado !== data.estado) {
            window.location.reload(); // Recargar si cambió el estado
        }
        
        // Actualizar timestamp de última actualización
        this.updateLastRefreshTime();
    }

    // Refrescar lista de operaciones  
    refreshOperationsList() {
        const currentURL = new URL(window.location);
        currentURL.searchParams.set('ajax', '1');
        
        $.get(currentURL.toString())
            .done((response) => {
                if (response.success) {
                    this.updateOperationsListUI(response.data);
                }
            })
            .fail(() => {
                console.error('Error al refrescar lista de operaciones');
            });
    }

    // Verificar si hay operaciones activas
    hasActiveOperations() {
        return $('.status-running, .status-queued, .status-pending').length > 0;
    }

    // Extraer ID de operación de la URL
    extractOperationIdFromURL() {
        const matches = window.location.pathname.match(/\/operaciones\/([a-f0-9-]+)\//);
        return matches ? matches[1] : null;
    }

    // Actualizar timestamp de última actualización
    updateLastRefreshTime() {
        const now = new Date();
        const timestamp = now.toLocaleTimeString();
        
        let indicator = $('#last-refresh-indicator');
        if (indicator.length === 0) {
            indicator = $('<small id="last-refresh-indicator" class="text-muted"></small>');
            $('.card-header').first().append(indicator);
        }
        
        indicator.text(`Última actualización: ${timestamp}`);
    }

    // Mostrar notificación
    showNotification(message, type = 'info') {
        const alertClass = type === 'error' ? 'alert-danger' : 
                          type === 'success' ? 'alert-success' : 
                          type === 'warning' ? 'alert-warning' : 'alert-info';
        
        const notification = $(`
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="close" data-dismiss="alert">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
        `);
        
        // Buscar container de notificaciones o crear uno
        let container = $('#notifications-container');
        if (container.length === 0) {
            container = $('<div id="notifications-container" class="position-fixed" style="top: 20px; right: 20px; z-index: 9999; max-width: 400px;"></div>');
            $('body').append(container);
        }
        
        container.append(notification);
        
        // Auto-eliminar después de 5 segundos
        setTimeout(() => {
            notification.fadeOut(() => notification.remove());
        }, 5000);
    }

    // Mostrar diálogo de confirmación
    showConfirmDialog(title, message, onConfirm) {
        const modal = $(`
            <div class="modal fade" id="confirmModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h4 class="modal-title">${title}</h4>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p>${message}</p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancelar</button>
                            <button type="button" class="btn btn-warning" id="confirmButton">Confirmar</button>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        $('body').append(modal);
        
        modal.find('#confirmButton').on('click', () => {
            modal.modal('hide');
            onConfirm();
        });
        
        modal.on('hidden.bs.modal', () => {
            modal.remove();
        });
        
        modal.modal('show');
    }

    // Obtener CSRF token
    getCSRFToken() {
        return $('[name=csrfmiddlewaretoken]').val() || 
               $('meta[name=csrf-token]').attr('content') || 
               '';
    }

    // Limpiar recursos
    cleanup() {
        this.stopAutoRefresh();
    }
}

// Utilidades específicas para configuración
class ConfiguracionManager {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Eventos para gestión de configuraciones
        $('.btn-ver-configuracion').on('click', this.onVerConfiguracion.bind(this));
        $('.btn-activar-configuracion').on('click', this.onActivarConfiguracion.bind(this));
        $('.btn-exportar-configuracion').on('click', this.onExportarConfiguracion.bind(this));
        
        // Eventos para verificación de servicios
        $('.btn-verificar-servicios').on('click', this.onVerificarServicios.bind(this));
    }

    onVerConfiguracion(event) {
        const configId = $(event.currentTarget).data('config-id');
        this.cargarDetallesConfiguracion(configId);
    }

    cargarDetallesConfiguracion(configId) {
        const modal = $('#detallesConfigModal');
        const content = $('#config-details-content');
        
        content.html('<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Cargando...</div>');
        modal.modal('show');
        
        $.get(`/generador-actas/api/configuracion/${configId}/`)
            .done((response) => {
                if (response.success) {
                    content.html(this.buildConfigurationDetailsHTML(response.data));
                } else {
                    content.html(`<div class="alert alert-danger">Error: ${response.message}</div>`);
                }
            })
            .fail(() => {
                content.html('<div class="alert alert-danger">Error al cargar los detalles</div>');
            });
    }

    buildConfigurationDetailsHTML(data) {
        return `
            <div class="row">
                <div class="col-md-6">
                    <h5>Información General</h5>
                    <dl class="row">
                        <dt class="col-sm-5">Versión:</dt>
                        <dd class="col-sm-7">v${data.version}</dd>
                        <dt class="col-sm-5">Fecha:</dt>
                        <dd class="col-sm-7">${data.fecha_creacion}</dd>
                        <dt class="col-sm-5">Usuario:</dt>
                        <dd class="col-sm-7">${data.usuario || 'Sistema'}</dd>
                        <dt class="col-sm-5">Estado:</dt>
                        <dd class="col-sm-7">
                            <span class="badge badge-${data.activa ? 'success' : 'secondary'}">
                                ${data.activa ? 'Activa' : 'Historial'}
                            </span>
                        </dd>
                    </dl>
                </div>
                <div class="col-md-6">
                    <h5>Descripción</h5>
                    <p>${data.descripcion || 'Sin descripción'}</p>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <h5>Configuración JSON</h5>
                    <pre class="code-block">${JSON.stringify(data.configuracion, null, 2)}</pre>
                </div>
            </div>
        `;
    }

    onVerificarServicios() {
        this.verificarEstadoServicios();
    }

    verificarEstadoServicios() {
        $('#celery-status, #redis-status').removeClass('badge-success badge-danger')
                                          .addClass('badge-secondary')
                                          .text('Verificando...');
        
        $.get('/generador-actas/api/estado-servicios/')
            .done((response) => {
                if (response.success) {
                    this.updateServiceStatus('celery', response.data.celery);
                    this.updateServiceStatus('redis', response.data.redis);
                }
            })
            .fail(() => {
                $('#celery-status, #redis-status').removeClass('badge-secondary badge-success')
                                                  .addClass('badge-danger')
                                                  .text('Error');
            });
    }

    updateServiceStatus(service, status) {
        const badge = $(`#${service}-status`);
        
        if (status.activo) {
            badge.removeClass('badge-secondary badge-danger')
                 .addClass('badge-success')
                 .text('Activo');
        } else {
            badge.removeClass('badge-secondary badge-success')
                 .addClass('badge-danger')
                 .text('Inactivo');
        }
    }
}

// Inicialización cuando el DOM esté listo
$(document).ready(function() {
    // Inicializar managers
    window.operacionesManager = new OperacionesManager();
    window.configuracionManager = new ConfiguracionManager();
    
    // Funciones globales para compatibilidad con templates
    window.iniciarOperacion = function(tipo) {
        $('#modalTipo').val(tipo).trigger('change');
        $('#nuevaOperacionModal').modal('show');
    };
    
    window.cancelarOperacion = function(operacionId) {
        window.operacionesManager.onCancelarOperacion({
            preventDefault: () => {},
            currentTarget: { dataset: { operacionId } }
        });
    };
    
    window.refrescarPagina = function() {
        window.location.reload();
    };
    
    window.refrescarLogs = function() {
        // Implementar carga específica de logs
        window.location.reload();
    };
    
    window.verificarServicios = function() {
        window.configuracionManager.verificarEstadoServicios();
    };
    
    window.verConfiguracion = function(configId) {
        window.configuracionManager.cargarDetallesConfiguracion(configId);
    };
    
    window.copiarTexto = function(texto) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(texto).then(() => {
                window.operacionesManager.showNotification('Texto copiado al portapapeles', 'success');
            });
        } else {
            // Fallback
            const textArea = document.createElement('textarea');
            textArea.value = texto;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            window.operacionesManager.showNotification('Texto copiado al portapapeles', 'success');
        }
    };
});