// Funcionalidades avanzadas para comparación de audio
class AudioComparator {
    constructor() {
        this.originalWave = null;
        this.processedWave = null;
        this.isPlaying = false;
        this.syncMode = false;
    }

    // Inicializar comparador de audio
    init(originalUrl, processedUrl) {
        this.setupWaveforms(originalUrl, processedUrl);
        this.setupControls();
        this.setupSyncMode();
    }

    // Configurar formas de onda
    setupWaveforms(originalUrl, processedUrl) {
        try {
            // Configuración común para ambas ondas
            const commonConfig = {
                height: 100,
                normalize: true,
                responsive: true,
                barWidth: 2,
                barHeight: 1,
                backend: 'MediaElement',
                interact: true,
                scrollParent: true
            };

            // Onda del audio original
            this.originalWave = WaveSurfer.create({
                ...commonConfig,
                container: '#waveform-original',
                waveColor: '#007bff',
                progressColor: '#0056b3',
                cursorColor: '#ff6b6b'
            });

            // Onda del audio procesado
            this.processedWave = WaveSurfer.create({
                ...commonConfig,
                container: '#waveform-processed',
                waveColor: '#28a745',
                progressColor: '#1e7e34',
                cursorColor: '#ff6b6b'
            });

            // Cargar archivos de audio
            this.originalWave.load(originalUrl);
            this.processedWave.load(processedUrl);

            // Eventos de sincronización
            this.originalWave.on('seek', (progress) => {
                if (this.syncMode && !this.isSeekingProgrammatically) {
                    this.isSeekingProgrammatically = true;
                    this.processedWave.seekTo(progress);
                    this.isSeekingProgrammatically = false;
                }
            });

            this.processedWave.on('seek', (progress) => {
                if (this.syncMode && !this.isSeekingProgrammatically) {
                    this.isSeekingProgrammatically = true;
                    this.originalWave.seekTo(progress);
                    this.isSeekingProgrammatically = false;
                }
            });

            // Eventos de finalización
            this.originalWave.on('finish', () => this.onFinish('original'));
            this.processedWave.on('finish', () => this.onFinish('processed'));

            // Eventos de carga completada
            this.originalWave.on('ready', () => this.onWaveReady('original'));
            this.processedWave.on('ready', () => this.onWaveReady('processed'));

        } catch (error) {
            console.error('Error configurando formas de onda:', error);
            this.showError('Error al cargar las formas de onda de audio');
        }
    }

    // Configurar controles de reproducción
    setupControls() {
        // Controles para audio original
        $('#play-original').click(() => this.playAudio('original'));
        $('#pause-original').click(() => this.pauseAudio('original'));
        $('#stop-original').click(() => this.stopAudio('original'));

        // Controles para audio procesado
        $('#play-processed').click(() => this.playAudio('processed'));
        $('#pause-processed').click(() => this.pauseAudio('processed'));
        $('#stop-processed').click(() => this.stopAudio('processed'));

        // Controles de comparación
        $('#play-both').click(() => this.playBoth());
        $('#stop-both').click(() => this.stopBoth());
        $('#toggle-sync').click(() => this.toggleSyncMode());
    }

    // Configurar modo de sincronización
    setupSyncMode() {
        // Agregar controles adicionales si no existen
        if (!$('#comparison-controls').length) {
            const controlsHtml = `
                <div id="comparison-controls" class="text-center mt-3">
                    <button id="play-both" class="control-button" style="background: #9c27b0;">
                        <i class="fas fa-play"></i> Reproducir Ambos
                    </button>
                    <button id="stop-both" class="control-button" style="background: #f44336;">
                        <i class="fas fa-stop"></i> Detener Ambos
                    </button>
                    <button id="toggle-sync" class="control-button" style="background: #ff9800;">
                        <i class="fas fa-link"></i> Modo Sincronizado: OFF
                    </button>
                </div>
            `;
            $('.vs-divider').after(controlsHtml);
        }
    }

    // Reproducir audio específico
    playAudio(type) {
        const wave = type === 'original' ? this.originalWave : this.processedWave;
        const prefix = type === 'original' ? 'original' : 'processed';

        wave.play();
        $(`#play-${prefix}`).prop('disabled', true);
        $(`#pause-${prefix}, #stop-${prefix}`).prop('disabled', false);
    }

    // Pausar audio específico
    pauseAudio(type) {
        const wave = type === 'original' ? this.originalWave : this.processedWave;
        const prefix = type === 'original' ? 'original' : 'processed';

        wave.pause();
        $(`#play-${prefix}`).prop('disabled', false);
        $(`#pause-${prefix}`).prop('disabled', true);
    }

    // Detener audio específico
    stopAudio(type) {
        const wave = type === 'original' ? this.originalWave : this.processedWave;
        const prefix = type === 'original' ? 'original' : 'processed';

        wave.stop();
        $(`#play-${prefix}`).prop('disabled', false);
        $(`#pause-${prefix}, #stop-${prefix}`).prop('disabled', true);
    }

    // Reproducir ambos audios simultáneamente
    playBoth() {
        if (this.originalWave && this.processedWave) {
            this.originalWave.play();
            this.processedWave.play();
            
            // Actualizar controles
            $('#play-original, #play-processed').prop('disabled', true);
            $('#pause-original, #pause-processed, #stop-original, #stop-processed').prop('disabled', false);
        }
    }

    // Detener ambos audios
    stopBoth() {
        if (this.originalWave && this.processedWave) {
            this.originalWave.stop();
            this.processedWave.stop();
            
            // Actualizar controles
            $('#play-original, #play-processed').prop('disabled', false);
            $('#pause-original, #pause-processed, #stop-original, #stop-processed').prop('disabled', true);
        }
    }

    // Alternar modo de sincronización
    toggleSyncMode() {
        this.syncMode = !this.syncMode;
        const button = $('#toggle-sync');
        const icon = button.find('i');
        
        if (this.syncMode) {
            button.html('<i class="fas fa-unlink"></i> Modo Sincronizado: ON')
                  .css('background', '#4caf50');
        } else {
            button.html('<i class="fas fa-link"></i> Modo Sincronizado: OFF')
                  .css('background', '#ff9800');
        }
    }

    // Manejar finalización de reproducción
    onFinish(type) {
        const prefix = type === 'original' ? 'original' : 'processed';
        $(`#play-${prefix}`).prop('disabled', false);
        $(`#pause-${prefix}, #stop-${prefix}`).prop('disabled', true);
    }

    // Manejar carga completada de onda
    onWaveReady(type) {
        console.log(`Forma de onda ${type} cargada correctamente`);
        
        // Mostrar información adicional
        const wave = type === 'original' ? this.originalWave : this.processedWave;
        const duration = wave.getDuration();
        
        // Actualizar duración en la interfaz si es necesario
        if (duration) {
            const minutes = Math.floor(duration / 60);
            const seconds = Math.floor(duration % 60);
            const formattedDuration = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            // Puedes agregar aquí lógica para mostrar la duración
            console.log(`Duración ${type}: ${formattedDuration}`);
        }
    }

    // Mostrar mensaje de error
    showError(message) {
        const errorHtml = `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            </div>
        `;
        
        $('.audio-comparison').prepend(errorHtml);
    }

    // Análisis de diferencias (función avanzada)
    analyzeAudioDifferences() {
        // Esta función podría implementarse para comparar características
        // como volumen promedio, frecuencias dominantes, etc.
        console.log('Análisis de diferencias de audio (función futura)');
    }

    // Exportar configuraciones de comparación
    exportComparisonSettings() {
        const settings = {
            syncMode: this.syncMode,
            originalDuration: this.originalWave ? this.originalWave.getDuration() : null,
            processedDuration: this.processedWave ? this.processedWave.getDuration() : null,
            timestamp: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'audio-comparison-settings.json';
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Inicializar cuando el documento esté listo
$(document).ready(function() {
    // Solo inicializar si estamos en la página de detalle con audios
    if ($('#waveform-original').length && $('#waveform-processed').length) {
        window.audioComparator = new AudioComparator();
        
        // Los URLs se pasarán desde el template Django
        if (window.originalAudioUrl && window.processedAudioUrl) {
            window.audioComparator.init(window.originalAudioUrl, window.processedAudioUrl);
        }
    }
});
