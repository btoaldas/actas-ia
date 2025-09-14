/**
 * JavaScript dinámico para gestión de proveedores IA
 * Incluye funcionalidades AJAX y cambios dinámicos de campos
 */

// Configuración global
const ProveedoresIA = {
    // URLs de APIs (se sobrescribirán desde el template)
    urls: {
        probar_conexion: '',
        modelos_proveedor: '',
        configuracion_defecto: ''
    },
    
    // Token CSRF
    csrfToken: '',
    
    // Configuraciones por defecto por proveedor
    configuracionesDefecto: {
        'openai': {
            api_url: 'https://api.openai.com/v1',
            modelo: 'gpt-4o',
            temperatura: 0.7,
            max_tokens: 4000,
            timeout: 60
        },
        'anthropic': {
            api_url: 'https://api.anthropic.com',
            modelo: 'claude-3-5-sonnet-20241022',
            temperatura: 0.7,
            max_tokens: 4000,
            timeout: 60
        },
        'deepseek': {
            api_url: 'https://api.deepseek.com',
            modelo: 'deepseek-chat',
            temperatura: 0.7,
            max_tokens: 4000,
            timeout: 60
        },
        'google': {
            api_url: 'https://generativelanguage.googleapis.com',
            modelo: 'gemini-1.5-flash',
            temperatura: 0.7,
            max_tokens: 2048,
            timeout: 60
        },
        'groq': {
            api_url: 'https://api.groq.com/openai/v1',
            modelo: 'llama-3.1-70b-versatile',
            temperatura: 0.7,
            max_tokens: 4000,
            timeout: 60
        },
        'ollama': {
            api_url: 'http://localhost:11434',
            modelo: 'llama3.2:3b',
            temperatura: 0.7,
            max_tokens: 2048,
            timeout: 120
        },
        'lmstudio': {
            api_url: 'http://localhost:1234/v1',
            modelo: 'lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF',
            temperatura: 0.7,
            max_tokens: 2048,
            timeout: 120
        },
        'generic1': {
            api_url: '',
            modelo: 'custom-model-1',
            temperatura: 0.7,
            max_tokens: 2048,
            timeout: 60
        },
        'generic2': {
            api_url: '',
            modelo: 'custom-model-2',
            temperatura: 0.7,
            max_tokens: 2048,
            timeout: 60
        }
    },

    // Modelos disponibles por proveedor
    modelosDisponibles: {
        'openai': [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo',
            'gpt-3.5-turbo-16k'
        ],
        'anthropic': [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ],
        'deepseek': [
            'deepseek-chat',
            'deepseek-coder',
            'deepseek-reasoning'
        ],
        'google': [
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-1.0-pro'
        ],
        'groq': [
            'llama-3.1-70b-versatile',
            'llama-3.1-8b-instant',
            'mixtral-8x7b-32768',
            'gemma2-9b-it'
        ],
        'ollama': [
            'llama3.2:3b',
            'llama3.2:1b',
            'llama3.1:8b',
            'llama3.1:70b',
            'mistral:7b',
            'mixtral:8x7b',
            'qwen2.5:7b',
            'gemma2:9b'
        ],
        'lmstudio': [
            'lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF',
            'lmstudio-ai/gemma-2b-it-GGUF',
            'microsoft/DialoGPT-medium',
            'microsoft/Phi-3-mini-4k-instruct-gguf'
        ],
        'generic1': ['custom-model-1', 'custom-model-2'],
        'generic2': ['custom-model-1', 'custom-model-2']
    },

    // Inicialización
    init: function(config = {}) {
        this.urls = { ...this.urls, ...config.urls };
        this.csrfToken = config.csrfToken || '';
        
        this.bindEvents();
        this.initializeForm();
    },

    // Vincular eventos
    bindEvents: function() {
        // Cambio de tipo de proveedor
        const tipoSelect = document.getElementById('id_tipo');
        if (tipoSelect) {
            tipoSelect.addEventListener('change', (e) => {
                this.onTipoProveedorChange(e.target.value);
            });
            
            // Disparar evento inicial si ya hay un valor
            if (tipoSelect.value) {
                this.onTipoProveedorChange(tipoSelect.value);
            }
        }

        // Actualizar valor de temperatura en tiempo real
        const temperaturaInput = document.getElementById('id_temperatura');
        if (temperaturaInput) {
            temperaturaInput.addEventListener('input', (e) => {
                const tempValue = document.getElementById('tempValue');
                if (tempValue) {
                    tempValue.textContent = e.target.value;
                }
            });
        }

        // Toggle API Key visibility
        window.toggleApiKey = () => {
            this.toggleApiKeyVisibility();
        };

        // Cargar configuración por defecto
        window.cargarConfiguracionDefecto = () => {
            this.cargarConfiguracionDefecto();
        };

        // Funciones para pruebas
        window.probarConexion = (proveedorId) => {
            this.probarConexion(proveedorId);
        };

        window.confirmarEliminacion = (proveedorId, proveedorNombre) => {
            this.confirmarEliminacion(proveedorId, proveedorNombre);
        };
    },

    // Inicializar formulario
    initializeForm: function() {
        // Cargar valor inicial de temperatura
        const temperaturaInput = document.getElementById('id_temperatura');
        const tempValue = document.getElementById('tempValue');
        if (temperaturaInput && tempValue) {
            tempValue.textContent = temperaturaInput.value || '0.7';
        }
    },

    // Manejar cambio de tipo de proveedor
    onTipoProveedorChange: function(tipo) {
        if (!tipo) return;

        this.actualizarModelosDisponibles(tipo);
        this.actualizarConfiguracionDefecto(tipo);
        this.actualizarInformacionProveedor(tipo);
    },

    // Actualizar modelos disponibles
    actualizarModelosDisponibles: function(tipo) {
        const modeloInput = document.getElementById('id_modelo');
        const datalist = document.getElementById('modelos_disponibles');
        const modelosDiv = document.getElementById('modelosDisponibles');
        
        if (!modeloInput || !tipo) return;

        const modelos = this.modelosDisponibles[tipo] || [];
        
        // Actualizar datalist si existe
        if (datalist) {
            datalist.innerHTML = '';
            modelos.forEach(modelo => {
                const option = document.createElement('option');
                option.value = modelo;
                datalist.appendChild(option);
            });
        }
        
        // Actualizar panel de ayuda si existe
        if (modelosDiv) {
            let html = `<h6><strong>Modelos para ${tipo.toUpperCase()}:</strong></h6><ul class="list-unstyled">`;
            modelos.forEach(modelo => {
                html += `<li><code>${modelo}</code></li>`;
            });
            html += '</ul>';
            modelosDiv.innerHTML = html;
        }

        // Si el campo modelo está vacío, sugerir el primer modelo
        if (!modeloInput.value && modelos.length > 0) {
            modeloInput.value = modelos[0];
        }
    },

    // Actualizar configuración por defecto
    actualizarConfiguracionDefecto: function(tipo) {
        const config = this.configuracionesDefecto[tipo];
        if (!config) return;

        // Solo actualizar campos que estén vacíos
        Object.keys(config).forEach(campo => {
            const input = document.getElementById(`id_${campo}`);
            if (input && !input.value && config[campo] !== null) {
                input.value = config[campo];
                
                // Actualizar display de temperatura si aplica
                if (campo === 'temperatura') {
                    const tempValue = document.getElementById('tempValue');
                    if (tempValue) {
                        tempValue.textContent = config[campo];
                    }
                }
            }
        });
    },

    // Actualizar información del proveedor en panel de ayuda
    actualizarInformacionProveedor: function(tipo) {
        const infoDiv = document.getElementById('proveedorInfo');
        if (!infoDiv) return;

        const descripciones = {
            'openai': 'OpenAI es el creador de GPT. Requiere API key de OpenAI.',
            'anthropic': 'Anthropic desarrolla Claude, conocido por conversaciones largas y seguras.',
            'deepseek': 'DeepSeek es especialista en código y razonamiento matemático.',
            'google': 'Google Gemini es multimodal y maneja texto, imágenes y video.',
            'groq': 'Groq ofrece inferencia ultrarrápida con modelos open source.',
            'ollama': 'Ollama permite ejecutar modelos localmente sin internet.',
            'lmstudio': 'LM Studio es una interfaz gráfica para modelos locales.',
            'generic1': 'Proveedor genérico personalizable para APIs compatibles.',
            'generic2': 'Segundo proveedor genérico para configuraciones alternativas.'
        };

        const descripcion = descripciones[tipo] || 'Proveedor de IA configurable.';
        
        infoDiv.innerHTML = `
            <h6><strong>${tipo.toUpperCase()}:</strong></h6>
            <p class="text-muted">${descripcion}</p>
            <hr>
            <h6><strong>Configuración recomendada:</strong></h6>
            <ul class="list-unstyled">
                <li><strong>Temperatura:</strong> ${this.configuracionesDefecto[tipo]?.temperatura || '0.7'}</li>
                <li><strong>Max Tokens:</strong> ${this.configuracionesDefecto[tipo]?.max_tokens || '2048'}</li>
                <li><strong>Timeout:</strong> ${this.configuracionesDefecto[tipo]?.timeout || '60'}s</li>
            </ul>
        `;
    },

    // Cargar configuración por defecto (forzado)
    cargarConfiguracionDefecto: function() {
        const tipoSelect = document.getElementById('id_tipo');
        if (!tipoSelect || !tipoSelect.value) {
            this.showAlert('Primero selecciona un tipo de proveedor', 'warning');
            return;
        }

        if (!confirm('¿Cargar los valores por defecto? Esto sobrescribirá los valores actuales.')) {
            return;
        }

        const tipo = tipoSelect.value;
        const config = this.configuracionesDefecto[tipo];
        
        if (!config) {
            this.showAlert('No hay configuración por defecto para este proveedor', 'warning');
            return;
        }

        // Aplicar configuración forzadamente
        Object.keys(config).forEach(campo => {
            const input = document.getElementById(`id_${campo}`);
            if (input && config[campo] !== null) {
                input.value = config[campo];
                
                // Disparar evento de cambio
                input.dispatchEvent(new Event('input', { bubbles: true }));
                
                if (campo === 'temperatura') {
                    const tempValue = document.getElementById('tempValue');
                    if (tempValue) {
                        tempValue.textContent = config[campo];
                    }
                }
            }
        });

        this.showAlert('Configuración por defecto cargada exitosamente', 'success');
    },

    // Toggle visibilidad de API Key
    toggleApiKeyVisibility: function() {
        const input = document.getElementById('id_api_key');
        const icon = document.getElementById('eyeIcon');
        
        if (!input || !icon) return;
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.className = 'fas fa-eye-slash';
        } else {
            input.type = 'password';
            icon.className = 'fas fa-eye';
        }
    },

    // Probar conexión con proveedor
    probarConexion: function(proveedorId) {
        if (!this.urls.probar_conexion) {
            this.showAlert('URL de prueba de conexión no configurada', 'error');
            return;
        }

        // Mostrar modal de prueba
        const modal = document.getElementById('testModal');
        if (modal) {
            $(modal).modal('show');
            this.mostrarResultadoPrueba('loading', 'Probando conexión...');
        }

        // Ejecutar prueba
        fetch(this.urls.probar_conexion, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                'proveedor_id': proveedorId,
                'prompt_prueba': 'Responde únicamente con el siguiente JSON exacto: {"status": "ok", "test": "exitoso"}'
            })
        })
        .then(response => response.json())
        .then(data => {
            this.mostrarResultadoPrueba('result', data);
            
            // Auto-recargar la página después de 3 segundos para mostrar última conexión
            setTimeout(() => {
                location.reload();
            }, 3000);
        })
        .catch(error => {
            this.mostrarResultadoPrueba('error', error.message || 'Error de conexión');
        });
    },

    // Mostrar resultado de prueba
    mostrarResultadoPrueba: function(tipo, data) {
        const resultDiv = document.getElementById('testResult');
        if (!resultDiv) return;

        if (tipo === 'loading') {
            resultDiv.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-spinner fa-spin fa-2x"></i>
                    <p class="mt-2">${data}</p>
                </div>
            `;
            return;
        }

        if (tipo === 'error') {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h5><i class="fas fa-times-circle"></i> Error</h5>
                    <p>${data}</p>
                </div>
            `;
            return;
        }

        // Resultado exitoso o con datos
        let html = '';
        if (data.success) {
            html = `
                <div class="alert alert-success">
                    <h5><i class="fas fa-check-circle"></i> Conexión Exitosa</h5>
                    <p><strong>Proveedor:</strong> ${data.proveedor?.nombre || 'N/A'}</p>
                    <p><strong>Tipo:</strong> ${data.proveedor?.tipo || 'N/A'}</p>
                    <p><strong>Modelo:</strong> ${data.proveedor?.modelo || 'N/A'}</p>
                    <p><strong>Tiempo de respuesta:</strong> ${data.tiempo_respuesta || 'N/A'}s</p>
                </div>
            `;
            
            if (data.prueba_prompt?.exito) {
                html += `
                    <div class="alert alert-info">
                        <h6><i class="fas fa-comment"></i> Respuesta del Modelo</h6>
                        <pre class="bg-light p-2">${data.prueba_prompt.respuesta}</pre>
                    </div>
                `;
            }
        } else {
            html = `
                <div class="alert alert-danger">
                    <h5><i class="fas fa-times-circle"></i> Error de Conexión</h5>
                    <p>${data.error || data.mensaje || 'Error desconocido'}</p>
                </div>
            `;
        }

        resultDiv.innerHTML = html;
    },

    // Confirmar eliminación
    confirmarEliminacion: function(proveedorId, proveedorNombre) {
        const modal = document.getElementById('deleteModal');
        const nombreSpan = document.getElementById('proveedorNombre');
        const form = document.getElementById('deleteForm');
        
        if (!modal || !nombreSpan || !form) return;

        nombreSpan.textContent = proveedorNombre;
        form.action = form.action.replace(/\/\d+\//, `/${proveedorId}/`);
        
        $(modal).modal('show');
    },

    // Mostrar alerta
    showAlert: function(message, type = 'info') {
        // Si toastr está disponible, usarlo
        if (typeof toastr !== 'undefined') {
            toastr[type](message);
            return;
        }

        // Fallback a alert básico
        alert(message);
    }
};

// Auto-inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Configuración desde el template se inyectará aquí
    window.ProveedoresIA = ProveedoresIA;
});