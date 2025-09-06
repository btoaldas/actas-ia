/**
 * ============================================================================
 * Sistema de Logging Frontend - Actas Municipales
 * Descripción: Captura automática de actividades del usuario en el frontend
 * ============================================================================
 */

class FrontendAuditLogger {
    constructor() {
        this.sessionId = this.getSessionId();
        this.userId = this.getUserId();
        this.pageLoadTime = Date.now();
        this.lastActivityTime = Date.now();
        this.currentPage = window.location.pathname;
        this.eventQueue = [];
        this.isOnline = navigator.onLine;
        
        // Configuración
        this.config = {
            batchSize: 10,
            flushInterval: 5000, // 5 segundos
            maxQueueSize: 100,
            trackClicks: true,
            trackFormSubmissions: true,
            trackPageViews: true,
            trackErrors: true,
            trackPerformance: true,
            apiEndpoint: '/api/frontend-logs/',
            debounceTime: 300
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startPeriodicFlush();
        this.trackPageView();
        this.trackPerformanceMetrics();
        
        console.log('🔍 Sistema de auditoría frontend iniciado');
    }
    
    setupEventListeners() {
        // Tracking de clics
        if (this.config.trackClicks) {
            document.addEventListener('click', this.debounce(this.handleClick.bind(this), this.config.debounceTime));
        }
        
        // Tracking de envío de formularios
        if (this.config.trackFormSubmissions) {
            document.addEventListener('submit', this.handleFormSubmit.bind(this));
        }
        
        // Tracking de errores JavaScript
        if (this.config.trackErrors) {
            window.addEventListener('error', this.handleError.bind(this));
            window.addEventListener('unhandledrejection', this.handlePromiseRejection.bind(this));
        }
        
        // Tracking de cambios de página (SPA)
        window.addEventListener('popstate', this.handlePageChange.bind(this));
        
        // Tracking de actividad del usuario
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, this.debounce(this.updateActivity.bind(this), 1000));
        });
        
        // Tracking de visibilidad de página
        document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));
        
        // Tracking de salida de página
        window.addEventListener('beforeunload', this.handlePageUnload.bind(this));
        
        // Tracking de estado de conexión
        window.addEventListener('online', () => this.handleConnectionChange(true));
        window.addEventListener('offline', () => this.handleConnectionChange(false));
    }
    
    // ========================================================================
    // Event Handlers
    // ========================================================================
    
    handleClick(event) {
        const element = event.target;
        const elementInfo = this.getElementInfo(element);
        
        this.logEvent({
            tipo: 'CLICK',
            categoria: 'INTERACCION',
            elemento: elementInfo.selector,
            texto_elemento: elementInfo.text,
            tipo_elemento: elementInfo.tagName,
            coordenadas: {
                x: event.clientX,
                y: event.clientY
            },
            url_actual: window.location.href,
            timestamp: Date.now()
        });
        
        // Tracking especial para botones importantes
        if (element.type === 'submit' || element.classList.contains('btn-primary')) {
            this.logEvent({
                tipo: 'ACCION_IMPORTANTE',
                categoria: 'FORM_ACTION',
                accion: 'BUTTON_CLICK',
                elemento: elementInfo.selector,
                formulario_padre: this.getParentForm(element)?.id || null
            });
        }
    }
    
    handleFormSubmit(event) {
        const form = event.target;
        const formData = new FormData(form);
        const formInfo = this.getFormInfo(form, formData);
        
        this.logEvent({
            tipo: 'FORM_SUBMIT',
            categoria: 'ACCION',
            formulario_id: form.id,
            formulario_action: form.action,
            formulario_method: form.method,
            campos_form: formInfo.fields,
            validacion_estado: form.checkValidity() ? 'VALIDO' : 'INVALIDO',
            url_actual: window.location.href,
            timestamp: Date.now()
        });
    }
    
    handleError(event) {
        this.logEvent({
            tipo: 'ERROR_JS',
            categoria: 'ERROR',
            mensaje: event.message,
            archivo: event.filename,
            linea: event.lineno,
            columna: event.colno,
            stack: event.error ? event.error.stack : null,
            url_actual: window.location.href,
            user_agent: navigator.userAgent,
            timestamp: Date.now()
        });
    }
    
    handlePromiseRejection(event) {
        this.logEvent({
            tipo: 'PROMISE_REJECTION',
            categoria: 'ERROR',
            razon: event.reason ? event.reason.toString() : 'Unknown',
            stack: event.reason && event.reason.stack ? event.reason.stack : null,
            url_actual: window.location.href,
            timestamp: Date.now()
        });
    }
    
    handlePageChange() {
        const newPage = window.location.pathname;
        if (newPage !== this.currentPage) {
            this.trackPageExit(this.currentPage);
            this.currentPage = newPage;
            this.trackPageView();
        }
    }
    
    handleVisibilityChange() {
        const isVisible = !document.hidden;
        
        this.logEvent({
            tipo: 'VISIBILITY_CHANGE',
            categoria: 'NAVEGACION',
            visible: isVisible,
            tiempo_en_pagina: Date.now() - this.pageLoadTime,
            url_actual: window.location.href,
            timestamp: Date.now()
        });
    }
    
    handlePageUnload() {
        this.trackPageExit(this.currentPage);
        this.flushEvents(true); // Flush inmediato
    }
    
    handleConnectionChange(isOnline) {
        this.isOnline = isOnline;
        
        this.logEvent({
            tipo: 'CONNECTION_CHANGE',
            categoria: 'SISTEMA',
            estado_conexion: isOnline ? 'ONLINE' : 'OFFLINE',
            timestamp: Date.now()
        });
        
        // Si volvemos online, intentar enviar eventos pendientes
        if (isOnline) {
            this.flushEvents();
        }
    }
    
    updateActivity() {
        this.lastActivityTime = Date.now();
    }
    
    // ========================================================================
    // Tracking Methods
    // ========================================================================
    
    trackPageView() {
        this.pageLoadTime = Date.now();
        
        this.logEvent({
            tipo: 'PAGE_VIEW',
            categoria: 'NAVEGACION',
            url: window.location.href,
            referrer: document.referrer,
            titulo: document.title,
            tiempo_carga: this.getPageLoadTime(),
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            },
            timestamp: Date.now()
        });
    }
    
    trackPageExit(url) {
        const timeOnPage = Date.now() - this.pageLoadTime;
        
        this.logEvent({
            tipo: 'PAGE_EXIT',
            categoria: 'NAVEGACION',
            url: url,
            tiempo_permanencia: timeOnPage,
            timestamp: Date.now()
        });
    }
    
    trackPerformanceMetrics() {
        if ('performance' in window && this.config.trackPerformance) {
            setTimeout(() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                
                this.logEvent({
                    tipo: 'PERFORMANCE',
                    categoria: 'SISTEMA',
                    metricas: {
                        dom_content_loaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                        load_complete: navigation.loadEventEnd - navigation.loadEventStart,
                        dns_lookup: navigation.domainLookupEnd - navigation.domainLookupStart,
                        tcp_connection: navigation.connectEnd - navigation.connectStart,
                        server_response: navigation.responseEnd - navigation.requestStart,
                        dom_processing: navigation.domComplete - navigation.domLoading,
                        first_paint: paint.find(p => p.name === 'first-paint')?.startTime || null,
                        first_contentful_paint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || null
                    },
                    timestamp: Date.now()
                });
            }, 2000);
        }
    }
    
    // ========================================================================
    // API Methods
    // ========================================================================
    
    async trackCustomEvent(tipo, categoria, datos = {}) {
        this.logEvent({
            tipo: tipo,
            categoria: categoria,
            ...datos,
            timestamp: Date.now()
        });
    }
    
    async trackFileUpload(fileName, fileSize, fileType) {
        this.logEvent({
            tipo: 'FILE_UPLOAD',
            categoria: 'ARCHIVO',
            nombre_archivo: fileName,
            tamaño_archivo: fileSize,
            tipo_archivo: fileType,
            url_actual: window.location.href,
            timestamp: Date.now()
        });
    }
    
    async trackFileDownload(fileName, downloadUrl) {
        this.logEvent({
            tipo: 'FILE_DOWNLOAD',
            categoria: 'ARCHIVO',
            nombre_archivo: fileName,
            url_descarga: downloadUrl,
            url_actual: window.location.href,
            timestamp: Date.now()
        });
    }
    
    async trackSearch(query, resultCount) {
        this.logEvent({
            tipo: 'SEARCH',
            categoria: 'ACCION',
            consulta_busqueda: query,
            resultados_count: resultCount,
            url_actual: window.location.href,
            timestamp: Date.now()
        });
    }
    
    // ========================================================================
    // Utility Methods
    // ========================================================================
    
    logEvent(eventData) {
        const enrichedEvent = {
            ...eventData,
            session_id: this.sessionId,
            user_id: this.userId,
            user_agent: navigator.userAgent,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            url_actual: window.location.href
        };
        
        this.eventQueue.push(enrichedEvent);
        
        // Flush si llegamos al límite
        if (this.eventQueue.length >= this.config.maxQueueSize) {
            this.flushEvents();
        }
    }
    
    async flushEvents(force = false) {
        if (this.eventQueue.length === 0) return;
        if (!this.isOnline && !force) return;
        
        const eventsToSend = this.eventQueue.splice(0, this.config.batchSize);
        
        try {
            const response = await fetch(this.config.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    events: eventsToSend,
                    metadata: {
                        session_id: this.sessionId,
                        user_id: this.userId,
                        batch_timestamp: Date.now()
                    }
                })
            });
            
            if (!response.ok) {
                // Devolver eventos a la cola si falló el envío
                this.eventQueue.unshift(...eventsToSend);
                console.error('Error enviando logs frontend:', response.statusText);
            }
            
        } catch (error) {
            // Devolver eventos a la cola si falló el envío
            this.eventQueue.unshift(...eventsToSend);
            console.error('Error enviando logs frontend:', error);
        }
    }
    
    startPeriodicFlush() {
        setInterval(() => {
            this.flushEvents();
        }, this.config.flushInterval);
    }
    
    getElementInfo(element) {
        return {
            tagName: element.tagName.toLowerCase(),
            id: element.id,
            className: element.className,
            text: element.textContent?.trim().substring(0, 100) || '',
            selector: this.getElementSelector(element)
        };
    }
    
    getElementSelector(element) {
        if (element.id) return `#${element.id}`;
        if (element.className) return `.${element.className.split(' ')[0]}`;
        return element.tagName.toLowerCase();
    }
    
    getParentForm(element) {
        return element.closest('form');
    }
    
    getFormInfo(form, formData) {
        const fields = {};
        
        for (let [key, value] of formData.entries()) {
            // No registrar campos sensibles
            if (!this.isSensitiveField(key)) {
                fields[key] = typeof value === 'string' ? value.substring(0, 100) : '[FILE]';
            } else {
                fields[key] = '[REDACTED]';
            }
        }
        
        return { fields };
    }
    
    isSensitiveField(fieldName) {
        const sensitiveFields = [
            'password', 'password1', 'password2', 'old_password', 'new_password',
            'csrfmiddlewaretoken', 'api_key', 'secret', 'token', 'credit_card',
            'ssn', 'social_security'
        ];
        
        return sensitiveFields.some(sensitive => 
            fieldName.toLowerCase().includes(sensitive)
        );
    }
    
    getSessionId() {
        // Intentar obtener session ID de Django
        const csrfInput = document.querySelector('[name="csrfmiddlewaretoken"]');
        if (csrfInput) {
            return csrfInput.value.substring(0, 16);
        }
        
        // Fallback: generar session ID temporal
        return 'frontend_' + Math.random().toString(36).substring(2, 15);
    }
    
    getUserId() {
        // Intentar obtener user ID de un elemento en la página
        const userIdElement = document.querySelector('[data-user-id]');
        if (userIdElement) {
            return parseInt(userIdElement.dataset.userId);
        }
        
        return null;
    }
    
    getCSRFToken() {
        const csrfInput = document.querySelector('[name="csrfmiddlewaretoken"]');
        return csrfInput ? csrfInput.value : '';
    }
    
    getPageLoadTime() {
        if ('performance' in window) {
            const navigation = performance.getEntriesByType('navigation')[0];
            return navigation ? navigation.loadEventEnd - navigation.fetchStart : 0;
        }
        return 0;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// ============================================================================
// Auto-inicialización
// ============================================================================

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.frontendLogger = new FrontendAuditLogger();
    });
} else {
    window.frontendLogger = new FrontendAuditLogger();
}

// ============================================================================
// API Pública para uso manual
// ============================================================================

window.logCustomEvent = function(tipo, categoria, datos = {}) {
    if (window.frontendLogger) {
        window.frontendLogger.trackCustomEvent(tipo, categoria, datos);
    }
};

window.logFileUpload = function(fileName, fileSize, fileType) {
    if (window.frontendLogger) {
        window.frontendLogger.trackFileUpload(fileName, fileSize, fileType);
    }
};

window.logFileDownload = function(fileName, downloadUrl) {
    if (window.frontendLogger) {
        window.frontendLogger.trackFileDownload(fileName, downloadUrl);
    }
};

window.logSearch = function(query, resultCount) {
    if (window.frontendLogger) {
        window.frontendLogger.trackSearch(query, resultCount);
    }
};

// Ejemplo de uso:
// logCustomEvent('ACTA_CREATED', 'MUNICIPAL', { acta_id: 123, tipo: 'ordinaria' });
// logFileUpload('acta_2025_01.pdf', 1024000, 'application/pdf');
// logSearch('presupuesto 2025', 15);
