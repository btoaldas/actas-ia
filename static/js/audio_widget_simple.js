/**
 * Audio Widget Simple - Compatible con navegadores antiguos
 */

// Objeto global simple para el widget de audio
var SimpleAudioWidget = {
    audioPlayer: null,
    audioPlayerWidget: null,
    audioTitle: null,
    audioDetails: null,
    isInitialized: false,
    
    init: function() {
        var self = this;
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                self.initElements();
            });
        } else {
            self.initElements();
        }
    },
    
    initElements: function() {
        this.audioPlayer = document.getElementById('audioPlayer');
        this.audioPlayerWidget = document.getElementById('audioPlayerWidget');
        this.audioTitle = document.getElementById('audioTitle');
        this.audioDetails = document.getElementById('audioDetails');
        
        console.log('SimpleAudioWidget initElements:', {
            audioPlayer: this.audioPlayer,
            audioPlayerWidget: this.audioPlayerWidget,
            audioTitle: this.audioTitle,
            audioDetails: this.audioDetails
        });
        
        if (this.audioPlayer && this.audioPlayerWidget && this.audioTitle && this.audioDetails) {
            this.isInitialized = true;
            this.setupEventListeners();
            console.log('SimpleAudioWidget inicializado correctamente');
        } else {
            console.log('SimpleAudioWidget: elementos del DOM no encontrados');
        }
    },
    
    setupEventListeners: function() {
        var self = this;
        
        // Event listener para errores de audio
        this.audioPlayer.addEventListener('error', function(e) {
            console.error('Error en reproductor de audio:', e);
            self.showError('Error al cargar el archivo de audio');
        });
        
        // Event listener para cuando el audio termina
        this.audioPlayer.addEventListener('ended', function() {
            self.audioTitle.innerHTML = '<i class="fas fa-check"></i> Reproducción completada';
        });
        
        // Event listener para cuando comienza la reproducción
        this.audioPlayer.addEventListener('play', function() {
            self.audioTitle.innerHTML = '<i class="fas fa-play text-success"></i> Reproduciendo...';
        });
        
        // Event listener para cuando se pausa
        this.audioPlayer.addEventListener('pause', function() {
            self.audioTitle.innerHTML = '<i class="fas fa-pause text-warning"></i> Pausado';
        });
    },
    
    cargarAudio: function(url, titulo, tipoReunion, fechaCreacion) {
        console.log('cargarAudio llamado:', {url: url, titulo: titulo, tipo: tipoReunion, fecha: fechaCreacion});
        
        if (!this.isInitialized) {
            console.error('SimpleAudioWidget no está inicializado');
            alert('Widget de audio no está inicializado');
            return;
        }
        
        // Mostrar el widget
        this.audioPlayerWidget.style.display = 'block';
        if (this.audioPlayerWidget.classList) {
            this.audioPlayerWidget.classList.add('show');
        }
        
        // Actualizar información del audio
        this.audioTitle.innerHTML = '<i class="fas fa-music"></i> ' + titulo;
        this.audioDetails.innerHTML = 
            '<div class="d-flex justify-content-between">' +
                '<span><i class="fas fa-tag text-primary"></i> ' + tipoReunion + '</span>' +
                '<span><i class="fas fa-calendar text-info"></i> ' + fechaCreacion + '</span>' +
            '</div>';
        
        // Cargar el audio
        this.audioPlayer.src = url;
        this.audioPlayer.load();
        
        // Scroll hacia el reproductor
        this.audioPlayerWidget.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
        
        // Intentar reproducir automáticamente
        var self = this;
        this.audioPlayer.addEventListener('loadeddata', function() {
            self.audioPlayer.play().catch(function(error) {
                console.log('Reproducción automática bloqueada:', error);
                self.audioDetails.innerHTML += 
                    '<div class="mt-2">' +
                        '<small class="text-info">' +
                            '<i class="fas fa-info-circle"></i> ' +
                            'Haz clic en play para reproducir' +
                        '</small>' +
                    '</div>';
            });
        }, { once: true });
    },
    
    cerrarReproductor: function() {
        if (!this.isInitialized) {
            return;
        }
        
        // Pausar audio
        this.audioPlayer.pause();
        this.audioPlayer.src = '';
        
        // Ocultar widget
        if (this.audioPlayerWidget.classList) {
            this.audioPlayerWidget.classList.remove('show');
        }
        var self = this;
        setTimeout(function() {
            self.audioPlayerWidget.style.display = 'none';
        }, 300);
        
        // Limpiar información
        this.audioTitle.innerHTML = '';
        this.audioDetails.innerHTML = '';
    },
    
    showError: function(message) {
        if (this.audioDetails) {
            this.audioDetails.innerHTML = 
                '<div class="alert alert-danger alert-sm mt-2">' +
                    '<i class="fas fa-exclamation-triangle"></i> ' + message +
                '</div>';
        }
    }
};

// Inicializar el widget
SimpleAudioWidget.init();

// Funciones globales para compatibilidad
function cargarAudio(url, titulo, tipoReunion, fechaCreacion) {
    console.log('Función global cargarAudio llamada');
    SimpleAudioWidget.cargarAudio(url, titulo, tipoReunion, fechaCreacion);
}

function cerrarReproductor() {
    console.log('Función global cerrarReproductor llamada');
    SimpleAudioWidget.cerrarReproductor();
}

function reproducirAudio(url) {
    console.log('Función global reproducirAudio llamada');
    SimpleAudioWidget.cargarAudio(url, 'Audio', 'Procesamiento', 'Fecha desconocida');
}

// Debug info
console.log('audio_widget_simple.js cargado');
console.log('Funciones disponibles:', {
    cargarAudio: typeof cargarAudio,
    cerrarReproductor: typeof cerrarReproductor,
    reproducirAudio: typeof reproducirAudio
});