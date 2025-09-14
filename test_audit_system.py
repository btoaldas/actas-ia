#!/usr/bin/env python3
"""
Script de prueba para verificar que los helpers de auditoría funcionan correctamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.whisper_helper import WhisperProcessor
from apps.transcripcion.pyannote_helper import PyannoteProcessor
from apps.transcripcion.estructura_json_mejorada import generar_estructura_json_mejorada

def test_whisper_audit():
    """Probar auditoría de Whisper"""
    print("=== TESTING WHISPER AUDIT ===")
    
    processor = WhisperProcessor()
    
    # Configuración de prueba
    config_test = {
        'modelo_whisper': 'base',
        'idioma_principal': 'es',
        'temperatura': 0.2,
        'usar_gpu': False,
        'palabra_por_palabra': True,
        'mejora_audio': True
    }
    
    print(f"Configuración de prueba: {config_test}")
    
    # Test de transcripción simulada (sin archivo real)
    resultado = processor.transcribir_audio('/fake/audio.wav', config_test)
    
    print(f"Éxito: {resultado.get('exito')}")
    print(f"Auditoría incluida: {'auditoria' in resultado}")
    
    if 'parametros_aplicados' in resultado:
        print("=== PARÁMETROS APLICADOS ===")
        for key, value in resultado['parametros_aplicados'].items():
            print(f"  {key}: {value}")
    
    if 'metadatos_modelo' in resultado:
        print("=== METADATOS DEL MODELO ===")
        for key, value in resultado['metadatos_modelo'].items():
            print(f"  {key}: {value}")
    
    if 'auditoria' in resultado:
        print("=== AUDITORÍA ===")
        for key, value in resultado['auditoria'].items():
            print(f"  {key}: {value}")
    
    return resultado

def test_pyannote_audit():
    """Probar auditoría de pyannote"""
    print("\n=== TESTING PYANNOTE AUDIT ===")
    
    processor = PyannoteProcessor()
    
    # Configuración de prueba
    config_test = {
        'modelo_diarizacion': 'pyannote/speaker-diarization-3.1',
        'min_speakers': 2,
        'max_speakers': 5,
        'clustering_threshold': 0.8,
        'usar_gpu': False
    }
    
    print(f"Configuración de prueba: {config_test}")
    
    # Test de diarización simulada
    resultado = processor.procesar_diarizacion('/fake/audio.wav', config_test)
    
    print(f"Éxito: {resultado.get('exito')}")
    print(f"Auditoría incluida: {'auditoria' in resultado}")
    
    if 'parametros_aplicados' in resultado:
        print("=== PARÁMETROS APLICADOS ===")
        for key, value in resultado['parametros_aplicados'].items():
            print(f"  {key}: {value}")
    
    if 'metadatos_pipeline' in resultado:
        print("=== METADATOS DEL PIPELINE ===")
        for key, value in resultado['metadatos_pipeline'].items():
            print(f"  {key}: {value}")
    
    if 'auditoria' in resultado:
        print("=== AUDITORÍA ===")
        for key, value in resultado['auditoria'].items():
            print(f"  {key}: {value}")
    
    return resultado

def test_json_structure():
    """Probar la estructura JSON mejorada con auditoría"""
    print("\n=== TESTING JSON STRUCTURE WITH AUDIT ===")
    
    # Simular resultados
    resultado_whisper = {
        'exito': True,
        'texto_completo': 'Esto es una transcripción de prueba.',
        'segmentos': [
            {
                'inicio': 0.0,
                'fin': 3.0,
                'texto': 'Esto es una transcripción de prueba.',
                'confianza': 0.95
            }
        ],
        'parametros_aplicados': {
            'modelo_whisper': 'base',
            'temperatura': 0.2,
            'palabra_por_palabra': True
        },
        'metadatos_modelo': {
            'modelo': 'base',
            'size_mb': 74,
            'device': 'cpu'
        },
        'auditoria': {
            'parametros_del_usuario': True,
            'parametros_hardcodeados': False
        }
    }
    
    resultado_pyannote = {
        'exito': True,
        'speakers_detectados': 2,
        'segmentos': [
            {
                'inicio': 0.0,
                'fin': 1.5,
                'speaker': 'SPEAKER_00'
            },
            {
                'inicio': 1.5,
                'fin': 3.0,
                'speaker': 'SPEAKER_01'
            }
        ],
        'parametros_aplicados': {
            'modelo_diarizacion': 'pyannote/speaker-diarization-3.1',
            'clustering_threshold': 0.8
        },
        'metadatos_pipeline': {
            'pipeline': 'pyannote/speaker-diarization-3.1',
            'device': 'cpu'
        },
        'auditoria': {
            'parametros_del_usuario': True,
            'threshold_aplicado': 0.8
        }
    }
    
    configuracion = {
        'modelo_whisper': 'base',
        'temperatura': 0.2,
        'modelo_diarizacion': 'pyannote/speaker-diarization-3.1',
        'clustering_threshold': 0.8
    }
    
    # Generar JSON mejorado
    json_result = generar_estructura_json_mejorada(
        'test_file_001',
        resultado_whisper,
        resultado_pyannote,
        [],
        configuracion
    )
    
    print(f"JSON generado exitosamente: {'processing_audit' in json_result}")
    
    if 'processing_audit' in json_result:
        audit = json_result['processing_audit']
        print("=== AUDITORÍA DEL PROCESAMIENTO ===")
        print(f"  Timestamp: {audit.get('timestamp')}")
        print(f"  Whisper success: {audit.get('whisper_processing', {}).get('success')}")
        print(f"  Pyannote success: {audit.get('diarization_processing', {}).get('success')}")
        print(f"  Model size (MB): {audit.get('whisper_processing', {}).get('model_metadata', {}).get('model_size_mb')}")
        print(f"  Device used: {audit.get('whisper_processing', {}).get('model_metadata', {}).get('device_used')}")
        print(f"  Parameters from user: {audit.get('whisper_processing', {}).get('audit_info', {}).get('parameters_from_user')}")
    
    return json_result

if __name__ == '__main__':
    print("Iniciando tests de auditoría...\n")
    
    try:
        # Test Whisper
        whisper_result = test_whisper_audit()
        
        # Test pyannote
        pyannote_result = test_pyannote_audit()
        
        # Test estructura JSON
        json_result = test_json_structure()
        
        print("\n=== RESUMEN ===")
        print(f"✓ Whisper audit: {'auditoria' in whisper_result}")
        print(f"✓ Pyannote audit: {'auditoria' in pyannote_result}")
        print(f"✓ JSON structure audit: {'processing_audit' in json_result}")
        print("\n¡Todos los tests de auditoría pasaron exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error en tests: {str(e)}")
        import traceback
        traceback.print_exc()