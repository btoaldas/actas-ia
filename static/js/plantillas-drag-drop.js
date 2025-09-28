/**
 * Sistema Drag & Drop para Plantillas de Actas IA
 * Permite reordenar segmentos mediante arrastrar y soltar
 * Integración con backend Django + AdminLTE
 */

class PlantillasDragDrop {
    constructor(containerId, apiEndpoint, csrfToken) {
        this.container = document.getElementById(containerId);
        this.apiEndpoint = apiEndpoint;
        this.csrfToken = csrfToken;
        this.draggedElement = null;
        this.hasChanges = false;
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Container para drag & drop no encontrado');
            return;
        }
        
        this.setupDragDrop();
        this.setupEventListeners();
        this.addSortableEffects();
        
        console.log('Sistema Drag & Drop inicializado');
    }
    
    setupDragDrop() {
        const items = this.container.querySelectorAll('.segmento-item');
        
        items.forEach(item => {
            item.draggable = true;
            item.addEventListener('dragstart', this.handleDragStart.bind(this));
            item.addEventListener('dragover', this.handleDragOver.bind(this));
            item.addEventListener('drop', this.handleDrop.bind(this));
            item.addEventListener('dragend', this.handleDragEnd.bind(this));
        });
    }
    
    handleDragStart(e) {
        this.draggedElement = e.target;
        e.target.style.opacity = '0.5';
        
        // Guardar datos del segmento
        const segmentoId = e.target.dataset.segmentoId;
        const orden = e.target.dataset.orden;
        
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);
        e.dataTransfer.setData('text/plain', JSON.stringify({
            segmentoId: segmentoId,
            orden: orden
        }));
        
        // Añadir clase visual
        e.target.classList.add('dragging');
    }
    
    handleDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        
        e.dataTransfer.dropEffect = 'move';
        
        // Efectos visuales de drop zone
        const item = e.target.closest('.segmento-item');
        if (item && item !== this.draggedElement) {
            item.classList.add('drop-target');
        }
        
        return false;
    }
    
    handleDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        
        const dropTarget = e.target.closest('.segmento-item');
        
        if (dropTarget && dropTarget !== this.draggedElement) {
            // Intercambiar posiciones
            this.swapElements(this.draggedElement, dropTarget);
            this.hasChanges = true;
            
            // Mostrar indicador de cambios
            this.showUnsavedChanges();
        }
        
        // Limpiar efectos visuales
        this.clearDropEffects();
        
        return false;
    }
    
    handleDragEnd(e) {
        e.target.style.opacity = '';
        e.target.classList.remove('dragging');
        this.clearDropEffects();
    }
    
    swapElements(elem1, elem2) {
        const nextSibling = elem2.nextElementSibling;
        const parent = elem2.parentNode;
        
        elem1.parentNode.insertBefore(elem2, elem1.nextElementSibling);
        parent.insertBefore(elem1, nextSibling);
        
        // Actualizar números de orden visibles
        this.updateOrderNumbers();
    }
    
    updateOrderNumbers() {
        const items = this.container.querySelectorAll('.segmento-item');
        items.forEach((item, index) => {
            const orderBadge = item.querySelector('.orden-badge');
            const orderInput = item.querySelector('input[name*="orden"]');
            
            if (orderBadge) {
                orderBadge.textContent = index + 1;
            }
            
            if (orderInput) {
                orderInput.value = index + 1;
            }
            
            // Actualizar data attribute
            item.dataset.orden = index + 1;
        });
    }
    
    clearDropEffects() {
        const items = this.container.querySelectorAll('.segmento-item');
        items.forEach(item => {
            item.classList.remove('drop-target', 'dragging');
        });
    }
    
    addSortableEffects() {
        // Añadir estilos CSS dinámicos
        const style = document.createElement('style');
        style.textContent = `
            .segmento-item {
                transition: all 0.3s ease;
                cursor: move;
                user-select: none;
            }
            
            .segmento-item:hover {
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                transform: translateY(-2px);
            }
            
            .segmento-item.dragging {
                opacity: 0.5;
                transform: rotate(5deg);
                z-index: 1000;
            }
            
            .segmento-item.drop-target {
                border: 2px dashed #007bff;
                background-color: rgba(0,123,255,0.1);
            }
            
            .drag-handle {
                color: #6c757d;
                cursor: grab;
                font-size: 1.2em;
                padding: 5px;
            }
            
            .drag-handle:hover {
                color: #007bff;
            }
            
            .drag-handle:active {
                cursor: grabbing;
            }
            
            .unsaved-changes-indicator {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #ffc107;
                color: #212529;
                padding: 10px 15px;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                z-index: 9999;
                animation: slideIn 0.3s ease-out;
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    showUnsavedChanges() {
        // Remover indicador anterior si existe
        const existing = document.querySelector('.unsaved-changes-indicator');
        if (existing) {
            existing.remove();
        }
        
        // Crear nuevo indicador
        const indicator = document.createElement('div');
        indicator.className = 'unsaved-changes-indicator';
        indicator.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <strong>Cambios sin guardar</strong>
            <button class="btn btn-sm btn-outline-dark ml-2" onclick="plantillasDragDrop.guardarOrden()">
                <i class="fas fa-save"></i> Guardar
            </button>
        `;
        
        document.body.appendChild(indicator);
        
        // Auto-ocultar después de 10 segundos
        setTimeout(() => {
            if (indicator && indicator.parentNode) {
                indicator.remove();
            }
        }, 10000);
    }
    
    async guardarOrden() {
        if (!this.hasChanges) {
            return;
        }
        
        const items = this.container.querySelectorAll('.segmento-item');
        const ordenData = [];
        
        items.forEach((item, index) => {
            ordenData.push({
                segmento_id: item.dataset.segmentoId,
                orden: index + 1
            });
        });
        
        try {
            // Mostrar loading
            this.showLoading();
            
            const response = await fetch(this.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    segmentos_orden: ordenData
                })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.hasChanges = false;
                this.showSuccess('Orden guardado correctamente');
                
                // Remover indicador de cambios
                const indicator = document.querySelector('.unsaved-changes-indicator');
                if (indicator) {
                    indicator.remove();
                }
            } else {
                throw new Error(result.error || 'Error al guardar el orden');
            }
            
        } catch (error) {
            console.error('Error al guardar orden:', error);
            this.showError('Error al guardar el orden: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }
    
    showLoading() {
        const indicator = document.querySelector('.unsaved-changes-indicator');
        if (indicator) {
            indicator.innerHTML = `
                <i class="fas fa-spinner fa-spin"></i>
                <strong>Guardando...</strong>
            `;
        }
    }
    
    hideLoading() {
        // Implementado en showSuccess/showError
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-success' : 'bg-danger';
        
        notification.className = `alert ${bgColor} text-white notification-toast`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;
        notification.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check' : 'fa-exclamation-triangle'}"></i>
            ${message}
            <button type="button" class="close ml-2" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification && notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    setupEventListeners() {
        // Shortcut para guardar (Ctrl+S)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.guardarOrden();
            }
        });
        
        // Confirmar salida si hay cambios sin guardar
        window.addEventListener('beforeunload', (e) => {
            if (this.hasChanges) {
                const message = 'Tienes cambios sin guardar. ¿Estás seguro de que quieres salir?';
                e.returnValue = message;
                return message;
            }
        });
    }
    
    // Método público para refrescar el sistema
    refresh() {
        this.hasChanges = false;
        const indicator = document.querySelector('.unsaved-changes-indicator');
        if (indicator) {
            indicator.remove();
        }
        this.setupDragDrop();
    }
    
    // Método público para añadir nuevos elementos
    addNewItem(itemHtml) {
        this.container.insertAdjacentHTML('beforeend', itemHtml);
        const newItem = this.container.lastElementChild;
        
        // Configurar drag & drop para el nuevo elemento
        newItem.draggable = true;
        newItem.addEventListener('dragstart', this.handleDragStart.bind(this));
        newItem.addEventListener('dragover', this.handleDragOver.bind(this));
        newItem.addEventListener('drop', this.handleDrop.bind(this));
        newItem.addEventListener('dragend', this.handleDragEnd.bind(this));
        
        this.updateOrderNumbers();
        this.hasChanges = true;
        this.showUnsavedChanges();
    }
}

// Inicialización automática cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Buscar elementos que requieran drag & drop
    const dragDropContainers = document.querySelectorAll('[data-drag-drop="true"]');
    
    dragDropContainers.forEach(container => {
        const apiEndpoint = container.dataset.apiEndpoint;
        const csrfToken = container.dataset.csrfToken;
        
        if (apiEndpoint && csrfToken) {
            new PlantillasDragDrop(container.id, apiEndpoint, csrfToken);
        }
    });
});

// Variable global para acceso desde templates
window.PlantillasDragDrop = PlantillasDragDrop;