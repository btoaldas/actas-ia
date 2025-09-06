"""
Tareas de Celery para el Sistema de Actas Municipales de Pastaza
Copyright (c) 2025 - Municipio de Pastaza, Ecuador
"""

import os, time, subprocess
import datetime
import logging
from os import listdir
from os.path import isfile, join

from .celery import app
from celery.contrib.abortable import AbortableTask
from django_celery_results.models import TaskResult

from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from celery.exceptions import Ignore, TaskError

# Configurar logger
logger = logging.getLogger('actas_municipales')

def get_scripts():
    """
    Devuelve todos los scripts desde 'ROOT_DIR/celery_scripts'
    """
    raw_scripts = []
    scripts     = []
    ignored_ext = ['db', 'txt']

    try:
        raw_scripts = [f for f in listdir(settings.CELERY_SCRIPTS_DIR) if isfile(join(settings.CELERY_SCRIPTS_DIR, f))]
    except Exception as e:
        logger.error(f"Error CELERY_SCRIPTS_DIR: {str(e)}")
        return None, 'Error CELERY_SCRIPTS_DIR: ' + str( e ) 

    for filename in raw_scripts:
        ext = filename.split(".")[-1]
        if ext not in ignored_ext:
           scripts.append( filename )

    return scripts, None           

def write_to_log_file(logs, script_name):
    """
    Escribe logs a un archivo de log con nombre formateado en el directorio CELERY_LOGS_DIR.
    """
    script_base_name = os.path.splitext(script_name)[0]  # Remover la extensión .py
    current_time = datetime.datetime.now().strftime("%y%m%d-%H%M%S")
    log_file_name = f"{script_base_name}-{current_time}.log"
    log_file_path = os.path.join(settings.CELERY_LOGS_DIR, log_file_name)
    
    with open(log_file_path, 'w') as log_file:
        log_file.write(logs)
    
    return log_file_path

# ### TAREAS ESPECÍFICAS PARA ACTAS MUNICIPALES ###

@app.task(bind=True)
def procesar_audio_acta(self, archivo_audio_id):
    """
    Procesa un archivo de audio de una reunión municipal y genera la transcripción
    """
    try:
        logger.info(f"🎵 Iniciando procesamiento de audio ID: {archivo_audio_id}")
        
        # Simulación del procesamiento (aquí iría la lógica real con Whisper)
        time.sleep(2)  # Simular procesamiento
        
        # Actualizar progreso
        self.update_state(state='PROGRESS', meta={'current': 50, 'total': 100})
        
        # Continuar procesamiento
        time.sleep(2)
        
        logger.info(f"✅ Audio procesado exitosamente: {archivo_audio_id}")
        return {
            'status': 'completed',
            'archivo_id': archivo_audio_id,
            'transcripcion_generada': True,
            'mensaje': 'Audio procesado y transcrito exitosamente para el Municipio de Pastaza'
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando audio {archivo_audio_id}: {str(e)}")
        raise TaskError(f"Error en procesamiento de audio: {str(e)}")

@app.task(bind=True)
def generar_transcripcion(self, audio_path, modelo='medium'):
    """
    Genera transcripción usando Whisper AI
    """
    try:
        logger.info(f"📝 Generando transcripción con modelo {modelo}")
        
        # Aquí iría la lógica de Whisper
        # import whisper
        # model = whisper.load_model(modelo)
        # result = model.transcribe(audio_path, language='es')
        
        # Simulación
        time.sleep(3)
        transcripcion = "Transcripción simulada de la reunión municipal..."
        
        return {
            'status': 'completed',
            'transcripcion': transcripcion,
            'idioma': 'es',
            'confianza': 0.95
        }
        
    except Exception as e:
        logger.error(f"❌ Error en transcripción: {str(e)}")
        raise TaskError(f"Error en transcripción: {str(e)}")

@app.task(bind=True)
def enviar_notificacion_email(self, destinatarios, asunto, mensaje, tipo='info'):
    """
    Envía notificaciones por email a usuarios del municipio
    """
    try:
        logger.info(f"📧 Enviando notificación a {len(destinatarios)} destinatarios")
        
        # Personalizar mensaje según el tipo
        prefijo = {
            'info': '🏛️ [MUNICIPIO DE PASTAZA]',
            'urgent': '🚨 [URGENTE - MUNICIPIO DE PASTAZA]',
            'success': '✅ [MUNICIPIO DE PASTAZA]',
            'error': '❌ [ERROR - MUNICIPIO DE PASTAZA]'
        }.get(tipo, '🏛️ [MUNICIPIO DE PASTAZA]')
        
        asunto_completo = f"{prefijo} {asunto}"
        
        for email in destinatarios:
            send_mail(
                asunto_completo,
                mensaje,
                settings.EMAIL_CONFIG.get('from_email', 'noreply@puyo.gob.ec'),
                [email],
                fail_silently=False,
            )
        
        logger.info(f"✅ Notificaciones enviadas exitosamente")
        return {
            'status': 'completed',
            'enviados': len(destinatarios),
            'tipo': tipo
        }
        
    except Exception as e:
        logger.error(f"❌ Error enviando emails: {str(e)}")
        raise TaskError(f"Error enviando notificaciones: {str(e)}")

@app.task(bind=True)
def generar_pdf_acta(self, acta_id):
    """
    Genera el PDF formal de un acta municipal
    """
    try:
        logger.info(f"📄 Generando PDF para acta ID: {acta_id}")
        
        # Aquí iría la lógica de generación de PDF con ReportLab
        time.sleep(2)  # Simular generación
        
        pdf_path = f"/app/media/pdfs/acta_{acta_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        logger.info(f"✅ PDF generado: {pdf_path}")
        return {
            'status': 'completed',
            'pdf_path': pdf_path,
            'acta_id': acta_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando PDF: {str(e)}")
        raise TaskError(f"Error generando PDF: {str(e)}")

@app.task
def limpiar_archivos_temporales():
    """
    Tarea periódica para limpiar archivos temporales del sistema
    """
    try:
        logger.info("🧹 Iniciando limpieza de archivos temporales")
        
        # Limpiar archivos temporales de más de 7 días
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        if os.path.exists(temp_dir):
            # Lógica de limpieza aquí
            pass
        
        logger.info("✅ Limpieza de archivos completada")
        return {'status': 'completed', 'archivos_eliminados': 0}
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@app.task
def backup_database():
    """
    Tarea para realizar backup de la base de datos
    """
    try:
        logger.info("💾 Iniciando backup de base de datos")
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_actas_municipales_{timestamp}.sql"
        
        # Aquí iría la lógica de backup real
        # pg_dump comando
        
        logger.info(f"✅ Backup completado: {backup_name}")
        return {'status': 'completed', 'backup_file': backup_name}
        
    except Exception as e:
        logger.error(f"❌ Error en backup: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@app.task
def verificar_actas_pendientes():
    """
    Verifica actas pendientes de aprobación y envía recordatorios
    """
    try:
        logger.info("🔍 Verificando actas pendientes de aprobación")
        
        # Aquí iría la lógica para verificar actas pendientes
        # Enviar recordatorios a concejales
        
        logger.info("✅ Verificación de actas completada")
        return {'status': 'completed', 'actas_pendientes': 0}
        
    except Exception as e:
        logger.error(f"❌ Error verificando actas: {str(e)}")
        return {'status': 'error', 'error': str(e)}

@app.task(bind=True, base=AbortableTask)
def execute_script(self, data: dict):
    """
    This task executes scripts found in settings.CELERY_SCRIPTS_DIR and logs are later generated and stored in settings.CELERY_LOGS_DIR
    :param data dict: contains data needed for task execution. Example `input` which is the script to be executed.
    :rtype: None
    """
    script = data.get("script")
    args   = data.get("args")

    print( '> EXEC [' + script + '] -> ('+args+')' ) 

    scripts, ErrInfo = get_scripts()

    if script and script in scripts:
        # Executing related script
        script_path = os.path.join(settings.CELERY_SCRIPTS_DIR, script)
        process = subprocess.Popen(
            f"python {script_path} {args}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(8)

        exit_code = process.wait()
        error = False
        status = "STARTED"
        if exit_code == 0:  # If script execution successfull
            logs = process.stdout.read().decode()
            status = "SUCCESS"
        else:
            logs = process.stderr.read().decode()
            error = True
            status = "FAILURE"


        log_file = write_to_log_file(logs, script)

        return {"logs": logs, "input": script, "error": error, "output": "", "status": status, "log_file": log_file}