#!/usr/bin/env python
"""
Script para poblar la base de datos con datos de demo realistas
Enlaza usuarios con perfiles y permisos específicos
"""

import os
import sys
import django
from django.contrib.auth.models import User
from django.db import transaction

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import (
    PerfilUsuario, PermisosDetallados, ConfiguracionIA, 
    ConfiguracionWhisper, LogConfiguracion
)

def crear_permisos_por_rol(rol):
    """Crear permisos específicos según el rol"""
    permisos = PermisosDetallados()
    
    # Permisos base para todos
    permisos.ver_dashboard = True
    permisos.acceder_sistema = True
    
    if rol == 'superadmin':
        # SuperAdmin tiene todos los permisos
        for field in PermisosDetallados._meta.get_fields():
            if field.name != 'id' and hasattr(permisos, field.name):
                setattr(permisos, field.name, True)
                
    elif rol == 'admin':
        # Administrador - mayoría de permisos excepto algunos críticos
        permisos.ver_menu_transcribir = True
        permisos.ver_menu_procesamiento = True
        permisos.ver_menu_digitalizacion = True
        permisos.ver_menu_generacion = True
        permisos.ver_menu_publicacion = True
        permisos.ver_menu_config_ia = True
        permisos.ver_menu_usuarios = True
        permisos.ver_menu_reportes = True
        
        # Funcionalidades de transcripción
        permisos.crear_transcripciones = True
        permisos.editar_transcripciones = True
        permisos.eliminar_transcripciones = True
        permisos.revisar_transcripciones = True
        permisos.aprobar_transcripciones = True
        
        # Procesamiento de audio
        permisos.procesar_audio = True
        permisos.configurar_whisper = True
        permisos.ver_cola_procesamiento = True
        permisos.pausar_procesamiento = True
        permisos.cancelar_procesamiento = True
        
        # Digitalización
        permisos.digitalizar_documentos = True
        permisos.editar_documentos_digitales = True
        permisos.aprobar_digitalizacion = True
        permisos.exportar_digitalizacion = True
        
        # Generación
        permisos.generar_actas = True
        permisos.editar_actas_generadas = True
        permisos.aprobar_actas = True
        permisos.configurar_plantillas = True
        
        # Publicación
        permisos.publicar_actas = True
        permisos.despublicar_actas = True
        permisos.programar_publicacion = True
        permisos.configurar_portales = True
        
        # Gestión de usuarios (limitada)
        permisos.ver_usuarios = True
        permisos.crear_usuarios = True
        permisos.editar_usuarios = True
        permisos.desactivar_usuarios = True
        
        # Reportes y configuración
        permisos.ver_reportes = True
        permisos.generar_reportes = True
        permisos.exportar_datos = True
        permisos.configurar_sistema = True
        
    elif rol == 'supervisor':
        # Supervisor - permisos de supervisión y aprobación
        permisos.ver_menu_transcribir = True
        permisos.ver_menu_procesamiento = True
        permisos.ver_menu_digitalizacion = True
        permisos.ver_menu_generacion = True
        permisos.ver_menu_publicacion = True
        permisos.ver_menu_reportes = True
        
        # Transcripción con supervisión
        permisos.crear_transcripciones = True
        permisos.editar_transcripciones = True
        permisos.revisar_transcripciones = True
        permisos.aprobar_transcripciones = True
        
        # Procesamiento supervisado
        permisos.procesar_audio = True
        permisos.ver_cola_procesamiento = True
        permisos.pausar_procesamiento = True
        
        # Digitalización supervisada
        permisos.digitalizar_documentos = True
        permisos.editar_documentos_digitales = True
        permisos.aprobar_digitalizacion = True
        
        # Generación supervisada
        permisos.generar_actas = True
        permisos.editar_actas_generadas = True
        permisos.aprobar_actas = True
        
        # Publicación supervisada
        permisos.publicar_actas = True
        permisos.programar_publicacion = True
        
        # Ver usuarios y reportes
        permisos.ver_usuarios = True
        permisos.ver_reportes = True
        permisos.generar_reportes = True
        
    elif rol == 'operador':
        # Operador - permisos básicos de operación
        permisos.ver_menu_transcribir = True
        permisos.ver_menu_procesamiento = True
        permisos.ver_menu_digitalizacion = True
        permisos.ver_menu_generacion = True
        
        # Operaciones básicas
        permisos.crear_transcripciones = True
        permisos.editar_transcripciones = True
        permisos.procesar_audio = True
        permisos.digitalizar_documentos = True
        permisos.editar_documentos_digitales = True
        permisos.generar_actas = True
        permisos.editar_actas_generadas = True
        
        # Solo lectura en otras áreas
        permisos.ver_cola_procesamiento = True
        permisos.ver_usuarios = True
        
    elif rol == 'consultor':
        # Consultor - solo lectura y reportes
        permisos.ver_menu_transcribir = True
        permisos.ver_menu_procesamiento = True
        permisos.ver_menu_digitalizacion = True
        permisos.ver_menu_generacion = True
        permisos.ver_menu_publicacion = True
        permisos.ver_menu_reportes = True
        
        # Solo visualización
        permisos.ver_cola_procesamiento = True
        permisos.ver_usuarios = True
        permisos.ver_reportes = True
        permisos.exportar_datos = True
    
    permisos.save()
    return permisos

def poblar_base_datos():
    """Poblar la base de datos con datos de demo realistas"""
    
    with transaction.atomic():
        print("🚀 Iniciando población de base de datos...")
        
        # 1. Crear usuarios con perfiles y permisos
        usuarios_demo = [
            {
                'username': 'admin_municipal',
                'email': 'admin@municipio.gob.ar',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'is_superuser': True,
                'is_staff': True,
                'password': 'admin123',
                'perfil': {
                    'rol': 'superadmin',
                    'departamento': 'Secretaría General',
                    'cargo': 'Secretario General',
                    'telefono': '+54 11 4123-4567'
                }
            },
            {
                'username': 'jefe_actas',
                'email': 'jefe.actas@municipio.gob.ar',
                'first_name': 'María',
                'last_name': 'González',
                'is_staff': True,
                'password': 'jefe123',
                'perfil': {
                    'rol': 'admin',
                    'departamento': 'Secretaría de Gobierno',
                    'cargo': 'Jefe de Actas Municipales',
                    'telefono': '+54 11 4123-4568'
                }
            },
            {
                'username': 'supervisor_sistemas',
                'email': 'supervisor@municipio.gob.ar',
                'first_name': 'Roberto',
                'last_name': 'Martínez',
                'password': 'super123',
                'perfil': {
                    'rol': 'supervisor',
                    'departamento': 'Sistemas e Innovación',
                    'cargo': 'Supervisor de Sistemas',
                    'telefono': '+54 11 4123-4569'
                }
            },
            {
                'username': 'operador_ana',
                'email': 'ana.lopez@municipio.gob.ar',
                'first_name': 'Ana',
                'last_name': 'López',
                'password': 'oper123',
                'perfil': {
                    'rol': 'operador',
                    'departamento': 'Secretaría de Gobierno',
                    'cargo': 'Operadora de Transcripciones',
                    'telefono': '+54 11 4123-4570'
                }
            },
            {
                'username': 'operador_juan',
                'email': 'juan.perez@municipio.gob.ar',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'password': 'oper123',
                'perfil': {
                    'rol': 'operador',
                    'departamento': 'Secretaría de Gobierno',
                    'cargo': 'Operador de Digitalización',
                    'telefono': '+54 11 4123-4571'
                }
            },
            {
                'username': 'consultor_ext',
                'email': 'consultor@external.com',
                'first_name': 'Patricia',
                'last_name': 'Silva',
                'password': 'cons123',
                'perfil': {
                    'rol': 'consultor',
                    'departamento': 'Consultoría Externa',
                    'cargo': 'Consultora en Transparencia',
                    'telefono': '+54 11 4123-4572'
                }
            }
        ]
        
        print("👤 Creando usuarios y perfiles...")
        for usuario_data in usuarios_demo:
            # Crear o actualizar usuario
            usuario, created = User.objects.get_or_create(
                username=usuario_data['username'],
                defaults={
                    'email': usuario_data['email'],
                    'first_name': usuario_data['first_name'],
                    'last_name': usuario_data['last_name'],
                    'is_superuser': usuario_data.get('is_superuser', False),
                    'is_staff': usuario_data.get('is_staff', False),
                    'is_active': True
                }
            )
            
            if created:
                usuario.set_password(usuario_data['password'])
                usuario.save()
                print(f"  ✅ Usuario creado: {usuario.username}")
            else:
                print(f"  ♻️ Usuario existe: {usuario.username}")
            
            # Crear o actualizar perfil
            perfil_data = usuario_data['perfil']
            perfil, created = PerfilUsuario.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'rol': perfil_data['rol'],
                    'departamento': perfil_data['departamento'],
                    'cargo': perfil_data['cargo'],
                    'telefono': perfil_data['telefono'],
                    'activo': True
                }
            )
            
            if created:
                print(f"    📋 Perfil creado: {perfil.get_rol_display()}")
                
                # Crear permisos específicos para el rol
                permisos = crear_permisos_por_rol(perfil_data['rol'])
                perfil.permisos_detallados = permisos
                perfil.save()
                print(f"    🔑 Permisos asignados para: {perfil.get_rol_display()}")
            else:
                print(f"    ♻️ Perfil existe: {perfil.get_rol_display()}")
        
        # 2. Crear configuraciones del sistema
        print("\n🔧 Creando configuraciones del sistema...")
        
        # Configuración IA
        config_ia, created = ConfiguracionIA.objects.get_or_create(
            nombre='Configuración Principal IA',
            defaults={
                'descripcion': 'Configuración principal para procesamiento con IA',
                'proveedor_ia': 'openai',
                'modelo_principal': 'gpt-4',
                'modelo_secundario': 'gpt-3.5-turbo',
                'temperatura': 0.3,
                'max_tokens': 2000,
                'activa': True,
                'configuracion_avanzada': {
                    'prompt_sistema': 'Eres un asistente especializado en actas municipales.',
                    'formato_salida': 'estructurado',
                    'idioma_principal': 'español',
                    'revision_automatica': True
                }
            }
        )
        if created:
            print("  ✅ Configuración IA creada")
        
        # Configuración Whisper
        config_whisper, created = ConfiguracionWhisper.objects.get_or_create(
            nombre='Whisper Producción',
            defaults={
                'descripcion': 'Configuración de Whisper para transcripciones automáticas',
                'modelo': 'large-v3',
                'idioma': 'es',
                'temperatura': 0.0,
                'beam_size': 5,
                'best_of': 5,
                'patience': 1.0,
                'suppress_blank': True,
                'suppress_tokens': '-1',
                'initial_prompt': 'Esta es una sesión del consejo municipal. Incluye nombres de funcionarios y términos administrativos.',
                'word_timestamps': True,
                'prepend_punctuations': '"¿¡',
                'append_punctuations': '".,;!?',
                'activa': True,
                'configuracion_avanzada': {
                    'chunk_length': 30,
                    'hop_length': 5,
                    'vad_filter': True,
                    'vad_parameters': {
                        'threshold': 0.5,
                        'min_speech_duration_ms': 250,
                        'max_speech_duration_s': 30,
                        'min_silence_duration_ms': 2000
                    }
                }
            }
        )
        if created:
            print("  ✅ Configuración Whisper creada")
        
        # 3. Crear logs de configuración
        print("\n📝 Creando logs de configuración...")
        logs_demo = [
            {
                'usuario': User.objects.get(username='admin_municipal'),
                'accion': 'CREAR',
                'modelo': 'ConfiguracionIA',
                'objeto_id': config_ia.id,
                'descripcion': 'Configuración inicial del sistema IA'
            },
            {
                'usuario': User.objects.get(username='admin_municipal'),
                'accion': 'CREAR',
                'modelo': 'ConfiguracionWhisper',
                'objeto_id': config_whisper.id,
                'descripcion': 'Configuración inicial de Whisper'
            },
            {
                'usuario': User.objects.get(username='jefe_actas'),
                'accion': 'MODIFICAR',
                'modelo': 'ConfiguracionWhisper',
                'objeto_id': config_whisper.id,
                'descripcion': 'Ajuste de parámetros de transcripción'
            }
        ]
        
        for log_data in logs_demo:
            LogConfiguracion.objects.create(**log_data)
        
        print(f"  ✅ {len(logs_demo)} logs de configuración creados")
        
        # 4. Estadísticas finales
        print("\n📊 Estadísticas finales:")
        print(f"  👤 Usuarios: {User.objects.count()}")
        print(f"  📋 Perfiles: {PerfilUsuario.objects.count()}")
        print(f"  🔑 Permisos: {PermisosDetallados.objects.count()}")
        print(f"  🤖 Configuraciones IA: {ConfiguracionIA.objects.count()}")
        print(f"  🎤 Configuraciones Whisper: {ConfiguracionWhisper.objects.count()}")
        print(f"  📝 Logs: {LogConfiguracion.objects.count()}")
        
        print("\n🎉 ¡Base de datos poblada exitosamente!")
        print("\n🔐 Credenciales de acceso:")
        print("  SuperAdmin: admin_municipal / admin123")
        print("  Admin: jefe_actas / jefe123") 
        print("  Supervisor: supervisor_sistemas / super123")
        print("  Operador: operador_ana / oper123")
        print("  Operador: operador_juan / oper123")
        print("  Consultor: consultor_ext / cons123")

if __name__ == '__main__':
    poblar_base_datos()
