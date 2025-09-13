/**
 * Audio Widget - Reproductor de audio persistente
 * Compatible con AdminLTE y Bootstrap
 */

class AudioWidget {
    constructor() {
        this.audioPlayer = null;
        this.audioPlayerWidget = null;
        this.audioTitle = null;
        this.audioDetails = null;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        // Inicializar elementos del DOM cuando el documento esté listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initElements());
        } else {
            this.initElements();
        }
    }
    
    initElements() {
        this.audioPlayer = document.getElementById('audioPlayer');
        this.audioPlayerWidget = document.getElementById('audioPlayerWidget');
        this.audioTitle = document.getElementById('audioTitle');
        this.audioDetails = document.getElementById('audioDetails');
        
        if (this.audioPlayer && this.audioPlayerWidget && this.audioTitle && this.audioDetails) {
            this.isInitialized = true;
            this.setupEventListeners();
        }
    }
    
    setupEventListeners() {
        // Event listener para manejar errores de audio
        this.audioPlayer.addEventListener('error', (e) => {
            console.error('Error en reproductor de audio:', e);
            this.showError('Error al cargar el archivo de audio');
        });
        
        // Event listener para cuando el audio termina
        this.audioPlayer.addEventListener('ended', () => {
            this.audioTitle.innerHTML = '<i class="fas fa-check"></i> Reproducción completada';
        });
        
        // Event listener para cuando comienza la reproducción
        this.audioPlayer.addEventListener('play', () => {
            this.audioTitle.innerHTML = '<i class="fas fa-play text-success"></i> Reproduciendo...';
        });
        
        // Event listener para cuando se pausa
        this.audioPlayer.addEventListener('pause', () => {
            this.audioTitle.innerHTML = '<i class="fas fa-pause text-warning"></i> Pausado';
        });
    }
    
    cargarAudio(url, titulo, tipoReunion, fechaCreacion) {
        if (!this.isInitialized) {
            console.error('AudioWidget no está inicializado');
            return;
        }
        
        // Mostrar el widget si está oculto
        this.audioPlayerWidget.style.display = 'block';
        this.audioPlayerWidget.classList.add('show');
        
        // Actualizar información del audio
        this.audioTitle.innerHTML = `<i class="fas fa-music"></i> ${titulo}`;
        this.audioDetails.innerHTML = `
            <div class="d-flex justify-content-between">
                <span><i class="fas fa-tag text-primary"></i> ${tipoReunion}</span>
                <span><i class="fas fa-calendar text-info"></i> ${fechaCreacion}</span>
            </div>
        `;
        
        // Cargar el audio
        this.audioPlayer.src = url;
        this.audioPlayer.load();
        
        // Scroll suave hacia el reproductor
        this.audioPlayerWidget.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        
        // Intentar reproducir automáticamente después de cargar
        this.audioPlayer.addEventListener('loadeddata', () => {
            this.audioPlayer.play().catch((error) => {
                console.log('Reproducción automática bloqueada:', error);
                this.audioDetails.innerHTML += `
                    <div class="mt-2">
                        <small class="text-info">
                            <i class="fas fa-info-circle"></i> 
                            Haz clic en play para reproducir
                        </small>
                    </div>
                `;
            });
        }, { once: true });
    }
    
    cerrarReproductor() {
        if (!this.isInitialized) {
            return;
        }
        
        // Pausar audio
        this.audioPlayer.pause();
        this.audioPlayer.src = '';
        
        // Ocultar widget con animación
        this.audioPlayerWidget.classList.remove('show');
        setTimeout(() => {
            this.audioPlayerWidget.style.display = 'none';
        }, 300);
        
        // Limpiar información
        this.audioTitle.innerHTML = '';
        this.audioDetails.innerHTML = '';
    }
    
    showError(message) {
        if (this.audioDetails) {
            this.audioDetails.innerHTML = `
                <div class="alert alert-danger alert-sm mt-2">
                    <i class="fas fa-exclamation-triangle"></i> ${message}
                </div>
            `;
        }
    }
}

// Crear instancia global del widget
const audioWidget = new AudioWidget();

// Funciones globales para compatibilidad con templates
function cargarAudio(url, titulo, tipoReunion, fechaCreacion) {
    audioWidget.cargarAudio(url, titulo, tipoReunion, fechaCreacion);
}

function cerrarReproductor() {
    audioWidget.cerrarReproductor();
}

// Función para reproducir audio (mantener compatibilidad)
function reproducirAudio(url) {
    audioWidget.cargarAudio(url, 'Audio', 'Procesamiento', 'Fecha desconocida');
}