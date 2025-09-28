/**
 * Sistema robusto para procesamiento de actas
 * Version mejorada con logging detallado y manejo de errores
 */

$(document).ready(function() {
    console.log('🚀 INICIANDO SISTEMA DE PROCESAMIENTO DE ACTAS');
    console.log('📅 Fecha:', new Date().toLocaleString());
    
    // Verificar dependencias
    if (typeof jQuery === 'undefined') {
        console.error('❌ jQuery no está cargado');
        return;
    }
    
    if (typeof Swal === 'undefined') {
        console.error('❌ SweetAlert2 no está cargado');
        return;
    }
    
    console.log('✅ Dependencias OK (jQuery + SweetAlert2)');
    
    // ========== INICIALIZAR BOTONES ==========
    function initializeProcesarButtons() {
        console.log('🔧 Inicializando botones procesar...');
        
        // Buscar botones
        const botones = $('.procesar-btn');
        console.log('🔍 Botones encontrados:', botones.length);
        
        if (botones.length === 0) {
            console.warn('⚠️ NO SE ENCONTRARON BOTONES CON CLASE .procesar-btn');
            return;
        }
        
        // Configurar cada botón
        botones.each(function(index) {
            const btn = $(this);
            const actaId = btn.data('acta-id');
            
            console.log(`🎯 Configurando botón ${index + 1}:`, {
                elemento: this,
                actaId: actaId,
                clases: this.className,
                deshabilitado: this.disabled
            });
            
            // Remover eventos anteriores y agregar nuevos
            btn.off('click.procesarActa').on('click.procesarActa', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                console.log('🚀 ¡¡¡BOTÓN CLICKEADO!!!');
                console.log('🎯 Acta ID:', actaId);
                
                procesarActaConfirmacion(actaId, $(this));
            });
        });
        
        console.log('✅ Botones inicializados correctamente');
    }
    
    // ========== CONFIRMACIÓN ==========
    function procesarActaConfirmacion(actaId, btn) {
        console.log('❓ Pidiendo confirmación para Acta:', actaId);
        
        // Validar CSRF token
        const csrfToken = $('[name=csrfmiddlewaretoken]').val();
        console.log('🔑 CSRF Token:', csrfToken ? 'ENCONTRADO' : 'NO ENCONTRADO');
        
        if (!csrfToken) {
            console.error('❌ NO HAY CSRF TOKEN');
            Swal.fire({
                title: 'Error',
                text: 'No se encontró el token de seguridad. Recarga la página.',
                icon: 'error'
            });
            return;
        }
        
        // Mostrar confirmación
        Swal.fire({
            title: '🤖 ¿Procesar con IA?',
            html: `
                <p><strong>Acta ID:</strong> ${actaId}</p>
                <p>Se iniciará el procesamiento automático usando Inteligencia Artificial.</p>
                <p>Este proceso puede tomar varios minutos.</p>
            `,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: '✅ Sí, procesar',
            cancelButtonText: '❌ Cancelar',
            confirmButtonColor: '#28a745',
            cancelButtonColor: '#dc3545',
            allowOutsideClick: false
        }).then((result) => {
            console.log('👤 Respuesta del usuario:', result);
            
            if (result.isConfirmed) {
                console.log('✅ Usuario confirmó - INICIANDO PROCESAMIENTO');
                ejecutarProcesamiento(actaId, csrfToken, btn);
            } else {
                console.log('❌ Usuario canceló');
            }
        });
    }
    
    // ========== EJECUTAR PROCESAMIENTO ==========
    function ejecutarProcesamiento(actaId, csrfToken, btn) {
        console.log('🔄 EJECUTANDO PROCESAMIENTO REAL');
        console.log('📋 Parámetros:', {
            actaId: actaId,
            csrfToken: csrfToken.substring(0, 10) + '...',
            boton: btn.get(0)
        });
        
        // Cambiar estado del botón INMEDIATAMENTE
        btn.prop('disabled', true);
        btn.html('<i class="fas fa-spinner fa-spin"></i> Procesando con IA...');
        console.log('🔄 Botón modificado - disabled=true, texto=Procesando');
        
        // Preparar petición
        const url = `/generador-actas/actas/${actaId}/procesar/`;
        console.log('📡 URL:', url);
        
        const requestData = {
            url: url,
            type: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            data: JSON.stringify({}),
            dataType: 'json',
            timeout: 120000, // 2 minutos
            cache: false
        };
        
        console.log('📤 Configuración de petición:', requestData);
        
        // Ejecutar petición AJAX
        $.ajax(requestData)
        .done(function(response, textStatus, xhr) {
            console.log('✅ PETICIÓN EXITOSA');
            console.log('✅ Status:', textStatus);
            console.log('✅ XHR Status:', xhr.status);
            console.log('✅ Response:', response);
            
            manejarRespuestaExitosa(response, btn);
        })
        .fail(function(xhr, textStatus, errorThrown) {
            console.error('❌ PETICIÓN FALLÓ');
            console.error('❌ XHR Status:', xhr.status);
            console.error('❌ Status Text:', xhr.statusText);
            console.error('❌ Text Status:', textStatus);
            console.error('❌ Error:', errorThrown);
            console.error('❌ Response Text:', xhr.responseText);
            
            manejarError(xhr, textStatus, errorThrown, btn);
        })
        .always(function() {
            console.log('🏁 Petición completada (siempre se ejecuta)');
        });
    }
    
    // ========== MANEJAR RESPUESTA EXITOSA ==========
    function manejarRespuestaExitosa(response, btn) {
        console.log('🎉 PROCESANDO RESPUESTA EXITOSA:', response);
        
        if (response && response.success) {
            console.log('✅ SUCCESS = TRUE - Todo OK');
            
            const mensaje = response.message || 'Procesamiento iniciado exitosamente';
            const taskId = response.task_id || 'N/A';
            
            Swal.fire({
                title: '🎉 ¡Procesamiento Iniciado!',
                html: `
                    <div style="text-align: center;">
                        <p><strong>${mensaje}</strong></p>
                        <hr>
                        <p><small><strong>Task ID:</strong> ${taskId}</small></p>
                        <p><small>La página se recargará automáticamente en 5 segundos...</small></p>
                    </div>
                `,
                icon: 'success',
                timer: 5000,
                timerProgressBar: true,
                allowOutsideClick: false,
                showConfirmButton: false
            }).then(() => {
                console.log('🔄 Recargando página...');
                window.location.reload();
            });
            
        } else {
            console.error('❌ SUCCESS = FALSE o no existe');
            const mensaje = response.message || 'Error desconocido del servidor';
            mostrarErrorAlUsuario('Error en el procesamiento', mensaje);
            restaurarBoton(btn);
        }
    }
    
    // ========== MANEJAR ERROR ==========
    function manejarError(xhr, textStatus, errorThrown, btn) {
        console.error('💥 MANEJANDO ERROR DE PETICIÓN');
        
        let titulo = 'Error de Comunicación';
        let mensaje = `Error al comunicarse con el servidor (Status: ${xhr.status})`;
        
        // Intentar extraer mensaje específico
        try {
            if (xhr.responseJSON && xhr.responseJSON.message) {
                mensaje = xhr.responseJSON.message;
            } else if (xhr.responseText) {
                // Limitar longitud del mensaje
                const maxLength = 300;
                mensaje = xhr.responseText.length > maxLength ? 
                    xhr.responseText.substring(0, maxLength) + '...' : 
                    xhr.responseText;
            }
            
            // Casos específicos
            if (xhr.status === 403) {
                titulo = 'Acceso Denegado';
                mensaje = 'No tienes permisos para realizar esta acción. Verifica tu sesión.';
            } else if (xhr.status === 404) {
                titulo = 'Recurso No Encontrado';
                mensaje = 'El acta o endpoint no fue encontrado.';
            } else if (xhr.status === 500) {
                titulo = 'Error del Servidor';
                mensaje = 'Error interno del servidor. Contacta al administrador.';
            }
            
        } catch (e) {
            console.error('Error parseando respuesta de error:', e);
        }
        
        mostrarErrorAlUsuario(titulo, mensaje);
        restaurarBoton(btn);
    }
    
    // ========== MOSTRAR ERROR AL USUARIO ==========
    function mostrarErrorAlUsuario(titulo, mensaje) {
        console.error('🚨 MOSTRANDO ERROR AL USUARIO:', {titulo, mensaje});
        
        Swal.fire({
            title: titulo,
            html: `<div style="text-align: left; max-height: 200px; overflow-y: auto;"><strong>Detalle:</strong><br>${mensaje}</div>`,
            icon: 'error',
            width: 600,
            confirmButtonText: 'Entendido',
            confirmButtonColor: '#dc3545'
        });
    }
    
    // ========== RESTAURAR BOTÓN ==========
    function restaurarBoton(btn) {
        console.log('🔄 Restaurando estado del botón...');
        btn.prop('disabled', false);
        btn.html('<i class="fas fa-play"></i> Procesar Acta');
        console.log('✅ Botón restaurado');
    }
    
    // ========== INICIALIZACIÓN PRINCIPAL ==========
    console.log('🚀 Inicializando sistema...');
    
    // Inicializar inmediatamente
    initializeProcesarButtons();
    
    // Verificar después de 2 segundos (por si hay carga dinámica)
    setTimeout(function() {
        console.log('🔍 Verificación secundaria...');
        const botones = $('.procesar-btn').length;
        if (botones === 0) {
            console.warn('⚠️ SEGUNDA VERIFICACIÓN: No hay botones');
        } else {
            console.log(`✅ SEGUNDA VERIFICACIÓN: ${botones} botones encontrados`);
        }
    }, 2000);
    
    console.log('🎯 SISTEMA DE PROCESAMIENTO LISTO');
});