/**
 * Script para el formulario de proveedores de IA
 * Mejora la experiencia del usuario para manejar la API key
 */

// Función para mostrar/ocultar la API key
function toggleApiKey() {
    const apiKeyField = document.getElementById('id_api_key');
    const eyeIcon = document.getElementById('eyeIcon');
    
    if (apiKeyField.type === 'password') {
        apiKeyField.type = 'text';
        eyeIcon.className = 'fas fa-eye-slash';
    } else {
        apiKeyField.type = 'password';
        eyeIcon.className = 'fas fa-eye';
    }
}

// Función para limpiar el campo API key (usar .env)
function clearApiKey() {
    const apiKeyField = document.getElementById('id_api_key');
    const helpText = apiKeyField.parentElement.parentElement.querySelector('.form-text');
    
    // Limpiar el campo
    apiKeyField.value = '';
    
    // Actualizar el texto de ayuda
    helpText.innerHTML = '<strong>Se usará la configuración del .env</strong>';
    helpText.className = 'form-text text-success';
    
    // Cambiar el placeholder
    apiKeyField.placeholder = 'Se usará la configuración del .env';
    
    // Mostrar mensaje temporal
    showTemporaryMessage('Campo limpiado. Se usará la configuración del .env', 'success');
}

// Función para mostrar mensajes temporales
function showTemporaryMessage(message, type = 'info') {
    // Crear elemento de mensaje
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type} alert-dismissible fade show`;
    messageDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    
    // Agregar al inicio del formulario
    const form = document.querySelector('form');
    form.insertBefore(messageDiv, form.firstChild);
    
    // Auto-eliminar después de 3 segundos
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 3000);
}

// Mejorar la experiencia para usuarios que quieren limpiar el campo en modo edición
document.addEventListener('DOMContentLoaded', function() {
    const apiKeyField = document.getElementById('id_api_key');
    
    if (apiKeyField) {
        // Agregar botón de "limpiar" si es modo edición y hay una API key configurada
        const placeholder = apiKeyField.placeholder;
        if (placeholder && placeholder.includes('••••••••')) {
            // Es modo edición con API key existente
            const inputGroup = apiKeyField.parentElement;
            const appendDiv = inputGroup.querySelector('.input-group-append');
            
            // Agregar botón de limpiar
            const clearButton = document.createElement('button');
            clearButton.className = 'btn btn-outline-warning';
            clearButton.type = 'button';
            clearButton.onclick = clearApiKey;
            clearButton.innerHTML = '<i class="fas fa-trash"></i>';
            clearButton.title = 'Limpiar y usar configuración del .env';
            
            appendDiv.appendChild(clearButton);
        }
        
        // Evento para detectar cuando el usuario escriba en el campo
        apiKeyField.addEventListener('input', function() {
            const helpText = this.parentElement.parentElement.querySelector('.form-text');
            
            if (this.value.length > 0) {
                helpText.innerHTML = 'Nueva clave API será guardada';
                helpText.className = 'form-text text-info';
            } else {
                helpText.innerHTML = 'Dejar vacío para usar la configuración del .env';
                helpText.className = 'form-text text-muted';
            }
        });
        
        // Detectar cuando el usuario presiona delete o backspace para limpiar completamente
        apiKeyField.addEventListener('keydown', function(e) {
            // Si es Delete o Backspace y el campo tiene solo caracteres ocultos (placeholder)
            if ((e.key === 'Delete' || e.key === 'Backspace') && this.value === '') {
                const placeholder = this.placeholder;
                if (placeholder && placeholder.includes('••••••••')) {
                    // Confirmar limpieza
                    if (confirm('¿Desea limpiar la API key y usar la configuración del .env?')) {
                        clearApiKey();
                    }
                }
            }
        });
    }
});

// Funciones de carga de valores por defecto (existentes)
function cargarValoresPorDefecto() {
    fetch('/generador-actas/proveedores/valores-defecto/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Object.keys(data.valores).forEach(campo => {
                    const element = document.getElementById(`id_${campo}`);
                    if (element) {
                        element.value = data.valores[campo];
                        // Trigger change event para actualizar UI
                        element.dispatchEvent(new Event('change'));
                    }
                });
                showTemporaryMessage('Valores por defecto cargados correctamente', 'success');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showTemporaryMessage('Error al cargar valores por defecto', 'danger');
        });
}