#!/usr/bin/env python
"""
Script para poblar la base de datos con configuraciones demo para Actas.IA
Incluye configuraciones reales de OpenAI, DeepSeek, Ollama y Whisper
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.config_system.models import ConfiguracionIA, ConfiguracionWhisper, PerfilUsuario, LogConfiguracion

User = get_user_model()

def crear_superuser():
    """Crear superusuario demo si no existe"""
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@actas.ia',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        print(f"✅ Superusuario creado: {admin.username}")
    else:
        admin = User.objects.get(username='admin')
        print(f"ℹ️  Superusuario ya existe: {admin.username}")
    
    return admin

def crear_configuraciones_ia():
    """Crear configuraciones de ejemplo para diferentes proveedores de IA"""
    
    configs_ia = [
        {
            'nombre': 'OpenAI GPT-4 Principal',
            'proveedor': 'openai',
            'activo': True,
            'es_principal': True,
            'api_key': 'sk-demo-openai-key-replace-with-real',
            'modelo': 'gpt-4',
            'temperatura': 0.3,
            'max_tokens': 4000,
            'top_p': 0.9,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'prompt_sistema': '''Eres un asistente especializado en la redacción y análisis de actas municipales.
Tu función es procesar transcripciones de audio de sesiones municipales y generar actas oficiales estructuradas.

INSTRUCCIONES:
- Mantén un lenguaje formal y técnico apropiado para documentos oficiales
- Organiza la información cronológicamente
- Identifica claramente a los participantes y sus intervenciones
- Resalta acuerdos, votaciones y decisiones tomadas
- Incluye referencias a normativas cuando sea pertinente''',
            'prompt_generacion_acta': '''Basándote en la transcripción proporcionada, genera un acta municipal oficial con la siguiente estructura:

1. ENCABEZADO:
   - Fecha, hora y lugar de la sesión
   - Tipo de sesión (ordinaria/extraordinaria)
   - Funcionarios presentes y ausentes

2. ORDEN DEL DIA:
   - Lista numerada de temas tratados

3. DESARROLLO:
   - Resumen detallado de cada punto
   - Intervenciones relevantes de funcionarios
   - Debates y discusiones principales

4. ACUERDOS Y RESOLUCIONES:
   - Decisiones tomadas con detalle de votaciones
   - Compromisos adquiridos con plazos

5. CIERRE:
   - Hora de finalización
   - Próxima sesión programada

Mantén el formato oficial y la terminología legal apropiada.''',
            'limite_requests_minuto': 20,
            'timeout_segundos': 30,
            'orden_prioridad': 1,
            'configuraciones_extra': {
                'system_fingerprint': 'fp_demo',
                'logit_bias': {},
                'response_format': {'type': 'text'}
            }
        },
        {
            'nombre': 'OpenAI GPT-3.5 Turbo Backup',
            'proveedor': 'openai',
            'activo': True,
            'es_principal': False,
            'api_key': 'sk-demo-openai-backup-key-replace-with-real',
            'modelo': 'gpt-3.5-turbo',
            'temperatura': 0.2,
            'max_tokens': 2000,
            'top_p': 0.8,
            'frequency_penalty': 0.1,
            'presence_penalty': 0.1,
            'prompt_sistema': '''Asistente para procesamiento rápido de actas municipales.
Enfoque en eficiencia y claridad en la redacción de documentos oficiales.''',
            'prompt_generacion_acta': '''Genera un acta municipal concisa pero completa basada en la transcripción.
Incluye: participantes, temas tratados, decisiones y acuerdos principales.''',
            'limite_requests_minuto': 30,
            'timeout_segundos': 20,
            'orden_prioridad': 2,
            'configuraciones_extra': {}
        },
        {
            'nombre': 'DeepSeek Chat Principal',
            'proveedor': 'deepseek',
            'activo': True,
            'es_principal': False,
            'api_key': 'sk-demo-deepseek-key-replace-with-real',
            'base_url': 'https://api.deepseek.com/v1',
            'modelo': 'deepseek-chat',
            'temperatura': 0.25,
            'max_tokens': 3000,
            'top_p': 0.85,
            'frequency_penalty': 0.0,
            'presence_penalty': 0.0,
            'prompt_sistema': '''Sistema de IA especializado en documentación gubernamental y actas oficiales.
Procesamiento eficiente de transcripciones para generar documentos estructurados.''',
            'prompt_generacion_acta': '''Procesa la transcripción y genera un acta municipal oficial.
Enfoque en precisión, estructura clara y cumplimiento de formatos legales.''',
            'limite_requests_minuto': 25,
            'timeout_segundos': 25,
            'orden_prioridad': 3,
            'configuraciones_extra': {
                'stream': False,
                'top_k': 40
            }
        },
        {
            'nombre': 'Ollama Llama2 Local',
            'proveedor': 'ollama',
            'activo': False,  # Inactivo por defecto ya que requiere setup local
            'es_principal': False,
            'base_url': 'http://localhost:11434',
            'modelo': 'llama2',
            'temperatura': 0.4,
            'max_tokens': 2000,
            'top_p': 0.9,
            'prompt_sistema': '''Asistente local para procesamiento de actas municipales.
Sistema privado sin envío de datos a servicios externos.''',
            'prompt_generacion_acta': '''Genera acta municipal basada en transcripción.
Formato oficial, estructura clara, datos precisos.''',
            'limite_requests_minuto': 10,
            'timeout_segundos': 60,
            'orden_prioridad': 4,
            'configuraciones_extra': {
                'num_predict': 2000,
                'num_ctx': 4096,
                'repeat_penalty': 1.1
            }
        },
        {
            'nombre': 'Ollama Mistral Local',
            'proveedor': 'ollama',
            'activo': False,
            'es_principal': False,
            'base_url': 'http://localhost:11434',
            'modelo': 'mistral',
            'temperatura': 0.3,
            'max_tokens': 3000,
            'top_p': 0.85,
            'prompt_sistema': '''Modelo local Mistral para documentación municipal.
Especializado en español y documentos oficiales.''',
            'prompt_generacion_acta': '''Basándote en la transcripción en español, crea un acta municipal 
que cumpla con los estándares legales y administrativos de Ecuador.''',
            'limite_requests_minuto': 8,
            'timeout_segundos': 45,
            'orden_prioridad': 5,
            'configuraciones_extra': {
                'temperature': 0.3,
                'top_k': 35,
                'repeat_penalty': 1.05
            }
        }
    ]
    
    for config_data in configs_ia:
        config, created = ConfiguracionIA.objects.get_or_create(
            nombre=config_data['nombre'],
            defaults=config_data
        )
        if created:
            print(f"✅ Configuración IA creada: {config.nombre}")
        else:
            print(f"ℹ️  Configuración IA ya existe: {config.nombre}")

def crear_configuraciones_whisper():
    """Crear configuraciones de ejemplo para Whisper"""
    
    configs_whisper = [
        {
            'nombre': 'Whisper Large Español Principal',
            'activo': True,
            'modelo_whisper': 'large',
            'idioma': 'es',
            'temperatura': 0.0,
            'usar_vad': True,
            'usar_pyannote': True,
            'modelo_pyannote': 'pyannote/speaker-diarization-3.1',
            'min_speakers': 2,
            'max_speakers': 12,
            'tiene_failover': True,
            'failover_metodo': 'modelo_pequeño'
        },
        {
            'nombre': 'Whisper Medium Multiidioma',
            'activo': True,
            'modelo_whisper': 'medium',
            'idioma': '',  # Auto-detección
            'temperatura': 0.1,
            'usar_vad': True,
            'usar_pyannote': True,
            'modelo_pyannote': 'pyannote/speaker-diarization-3.1',
            'min_speakers': 1,
            'max_speakers': 8,
            'tiene_failover': True,
            'failover_metodo': 'sin_pyannote'
        },
        {
            'nombre': 'Whisper Base Rápido',
            'activo': True,
            'modelo_whisper': 'base',
            'idioma': 'es',
            'temperatura': 0.0,
            'usar_vad': False,
            'usar_pyannote': False,
            'min_speakers': 1,
            'max_speakers': 5,
            'tiene_failover': True,
            'failover_metodo': 'basico'
        },
        {
            'nombre': 'Whisper Small Backup',
            'activo': False,  # Como backup
            'modelo_whisper': 'small',
            'idioma': 'es',
            'temperatura': 0.2,
            'usar_vad': True,
            'usar_pyannote': False,
            'min_speakers': 1,
            'max_speakers': 6,
            'tiene_failover': False,
            'failover_metodo': ''
        },
        {
            'nombre': 'Whisper Tiny Emergencia',
            'activo': False,
            'modelo_whisper': 'tiny',
            'idioma': 'es',
            'temperatura': 0.0,
            'usar_vad': False,
            'usar_pyannote': False,
            'min_speakers': 1,
            'max_speakers': 3,
            'tiene_failover': False,
            'failover_metodo': ''
        }
    ]
    
    for config_data in configs_whisper:
        config, created = ConfiguracionWhisper.objects.get_or_create(
            nombre=config_data['nombre'],
            defaults=config_data
        )
        if created:
            print(f"✅ Configuración Whisper creada: {config.nombre}")
        else:
            print(f"ℹ️  Configuración Whisper ya existe: {config.nombre}")

def crear_perfiles_usuarios():
    """Crear perfiles de usuario para los superadministradores"""
    
    # Obtener todos los superusuarios
    superusers = User.objects.filter(is_superuser=True)
    
    for user in superusers:
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=user,
            defaults={
                'rol': 'superadmin',
                'puede_gestionar_ia': True,
                'puede_gestionar_whisper': True,
                'puede_configurar_usuarios': True,
                'puede_ver_logs': True,
                'puede_exportar_configuraciones': True,
                'notificaciones_email': True,
                'configuraciones_preferidas': {
                    'tema_interfaz': 'claro',
                    'items_por_pagina': 20,
                    'mostrar_ayuda': True,
                    'auto_backup': True
                }
            }
        )
        if created:
            print(f"✅ Perfil de usuario creado: {user.username} -> {perfil.rol}")
        else:
            print(f"ℹ️  Perfil de usuario ya existe: {user.username}")

def crear_logs_iniciales(admin_user):
    """Crear logs de configuración iniciales"""
    
    logs_iniciales = [
        {
            'usuario': admin_user,
            'configuracion_tipo': 'ia',
            'configuracion_nombre': 'OpenAI GPT-4 Principal',
            'accion': 'crear',
            'detalles': 'Configuración inicial del sistema - OpenAI GPT-4 como principal',
            'ip_address': '127.0.0.1'
        },
        {
            'usuario': admin_user,
            'configuracion_tipo': 'whisper',
            'configuracion_nombre': 'Whisper Large Español Principal',
            'accion': 'crear',
            'detalles': 'Configuración inicial de transcripción - Whisper Large con Pyannote',
            'ip_address': '127.0.0.1'
        },
        {
            'usuario': admin_user,
            'configuracion_tipo': 'sistema',
            'configuracion_nombre': 'Sistema Actas.IA',
            'accion': 'inicializar',
            'detalles': 'Inicialización del sistema de configuraciones demo',
            'ip_address': '127.0.0.1'
        }
    ]
    
    for log_data in logs_iniciales:
        log, created = LogConfiguracion.objects.get_or_create(
            usuario=log_data['usuario'],
            configuracion_tipo=log_data['configuracion_tipo'],
            configuracion_nombre=log_data['configuracion_nombre'],
            accion=log_data['accion'],
            defaults=log_data
        )
        if created:
            print(f"✅ Log creado: {log.accion} - {log.configuracion_nombre}")

def main():
    """Función principal para poblar la base de datos"""
    
    print("🚀 Iniciando población de base de datos con configuraciones demo...")
    print("=" * 60)
    
    # 1. Crear superusuario
    print("\n👤 CREANDO SUPERUSUARIO...")
    admin_user = crear_superuser()
    
    # 2. Crear configuraciones de IA
    print("\n🤖 CREANDO CONFIGURACIONES DE IA...")
    crear_configuraciones_ia()
    
    # 3. Crear configuraciones de Whisper
    print("\n🎤 CREANDO CONFIGURACIONES DE WHISPER...")
    crear_configuraciones_whisper()
    
    # 4. Crear perfiles de usuario
    print("\n👥 CREANDO PERFILES DE USUARIO...")
    crear_perfiles_usuarios()
    
    # 5. Crear logs iniciales
    print("\n📝 CREANDO LOGS INICIALES...")
    crear_logs_iniciales(admin_user)
    
    print("\n" + "=" * 60)
    print("✅ POBLACIÓN DE BASE DE DATOS COMPLETADA")
    print("\n📊 RESUMEN:")
    print(f"   - Configuraciones IA: {ConfiguracionIA.objects.count()}")
    print(f"   - Configuraciones Whisper: {ConfiguracionWhisper.objects.count()}")
    print(f"   - Perfiles de usuario: {PerfilUsuario.objects.count()}")
    print(f"   - Logs de configuración: {LogConfiguracion.objects.count()}")
    
    print("\n🔑 CREDENCIALES DE ACCESO:")
    print("   Usuario: admin")
    print("   Contraseña: admin123")
    print("   URL: http://localhost:8000/config-system/")
    
    print("\n💡 CONFIGURACIONES ACTIVAS:")
    configs_activas = ConfiguracionIA.objects.filter(activo=True)
    for config in configs_activas:
        status = "🌟 PRINCIPAL" if config.es_principal else "⚡ ACTIVA"
        print(f"   {status}: {config.nombre} ({config.proveedor})")
    
    print("\n⚠️  IMPORTANTE:")
    print("   - Reemplaza las API keys demo con tus claves reales")
    print("   - Configura Ollama localmente si deseas usar modelos locales")
    print("   - Las configuraciones están listas para producción")

if __name__ == "__main__":
    main()
