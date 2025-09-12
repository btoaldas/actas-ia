#!/usr/bin/env python3
"""
Script para inicializar datos por defecto en el módulo de transcripción
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/code')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import ConfiguracionTranscripcion
from apps.audio_processing.models import TipoReunion

def crear_configuraciones_por_defecto():
    """Crear configuraciones por defecto para transcripción"""
    
    # Configuración Básica
    config_basica, created = ConfiguracionTranscripcion.objects.get_or_create(
        nombre="Configuración Básica",
        defaults={
            'descripcion': 'Configuración rápida para reuniones cortas',
            'activa': True,
            'modelo_whisper': 'base',
            'temperatura': 0.0,
            'usar_vad': True,
            'vad_filtro': 'silero',
            'min_hablantes': 2,
            'max_hablantes': 5,
            'umbral_clustering': 0.5,
            'chunk_duracion': 30,
            'overlap_duracion': 2,
            'usar_gpu': True,
            'usar_enhanced_diarization': False,
            'filtro_ruido': True,
            'normalizar_audio': True,
        }
    )
    
    if created:
        print("✓ Configuración Básica creada")
    else:
        print("- Configuración Básica ya existe")
    
    # Configuración Avanzada
    config_avanzada, created = ConfiguracionTranscripcion.objects.get_or_create(
        nombre="Configuración Avanzada",
        defaults={
            'descripcion': 'Configuración de alta precisión para reuniones importantes',
            'activa': False,
            'modelo_whisper': 'large-v3',
            'temperatura': 0.2,
            'usar_vad': True,
            'vad_filtro': 'silero',
            'min_hablantes': 1,
            'max_hablantes': 10,
            'umbral_clustering': 0.3,
            'chunk_duracion': 20,
            'overlap_duracion': 3,
            'usar_gpu': True,
            'usar_enhanced_diarization': True,
            'filtro_ruido': True,
            'normalizar_audio': True,
        }
    )
    
    if created:
        print("✓ Configuración Avanzada creada")
    else:
        print("- Configuración Avanzada ya existe")
    
    # Configuración Rápida
    config_rapida, created = ConfiguracionTranscripcion.objects.get_or_create(
        nombre="Configuración Rápida",
        defaults={
            'descripcion': 'Procesamiento rápido para pruebas y bocetos',
            'activa': False,
            'modelo_whisper': 'tiny',
            'temperatura': 0.0,
            'usar_vad': False,
            'vad_filtro': 'silero',
            'min_hablantes': 1,
            'max_hablantes': 3,
            'umbral_clustering': 0.7,
            'chunk_duracion': 60,
            'overlap_duracion': 1,
            'usar_gpu': False,
            'usar_enhanced_diarization': False,
            'filtro_ruido': False,
            'normalizar_audio': False,
        }
    )
    
    if created:
        print("✓ Configuración Rápida creada")
    else:
        print("- Configuración Rápida ya existe")

def crear_tipos_reunion_por_defecto():
    """Crear tipos de reunión por defecto si no existen"""
    
    tipos_defecto = [
        {"nombre": "Sesión Ordinaria", "descripcion": "Sesión ordinaria del concejo municipal"},
        {"nombre": "Sesión Extraordinaria", "descripcion": "Sesión extraordinaria del concejo municipal"},
        {"nombre": "Comisión", "descripcion": "Reunión de comisión municipal"},
        {"nombre": "Audiencia Pública", "descripcion": "Audiencia pública con la ciudadanía"},
        {"nombre": "Reunión de Trabajo", "descripcion": "Reunión de trabajo interno"},
    ]
    
    for tipo_data in tipos_defecto:
        tipo, created = TipoReunion.objects.get_or_create(
            nombre=tipo_data["nombre"],
            defaults={'descripcion': tipo_data["descripcion"]}
        )
        if created:
            print(f"✓ Tipo de reunión '{tipo.nombre}' creado")
        else:
            print(f"- Tipo de reunión '{tipo.nombre}' ya existe")

def main():
    print("Inicializando datos por defecto para el módulo de transcripción...")
    print("=" * 60)
    
    # Crear tipos de reunión
    print("\n1. Creando tipos de reunión por defecto:")
    crear_tipos_reunion_por_defecto()
    
    # Crear configuraciones
    print("\n2. Creando configuraciones de transcripción por defecto:")
    crear_configuraciones_por_defecto()
    
    # Resumen
    print("\n" + "=" * 60)
    print("Resumen:")
    print(f"- Tipos de reunión: {TipoReunion.objects.count()}")
    print(f"- Configuraciones de transcripción: {ConfiguracionTranscripcion.objects.count()}")
    print(f"- Configuración activa: {ConfiguracionTranscripcion.objects.filter(activa=True).first()}")
    
    print("\n✅ Inicialización completada correctamente")

if __name__ == "__main__":
    main()
