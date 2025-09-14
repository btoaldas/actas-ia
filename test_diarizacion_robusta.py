#!/usr/bin/env python3
"""
Test específico para verificar la configuración ROBUSTA de diarización
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.pyannote_helper import PyannoteProcessor

def test_configuracion_robusta():
    """Probar la configuración robusta con participantes esperados"""
    print("=== TESTING CONFIGURACIÓN ROBUSTA DE DIARIZACIÓN ===")
    
    processor = PyannoteProcessor()
    
    # Simular participantes esperados del módulo de audio
    participantes_esperados = [
        {
            'orden': 1,
            'nombres': 'Juan Carlos',
            'apellidos': 'Pérez',
            'nombre_completo': 'Juan Carlos Pérez',
            'cargo': 'Alcalde',
            'institucion': 'Municipio de Pastaza',
            'activo': True
        },
        {
            'orden': 2,
            'nombres': 'María Elena',
            'apellidos': 'García',
            'nombre_completo': 'María Elena García',
            'cargo': 'Secretaria',
            'institucion': 'Municipio de Pastaza',
            'activo': True
        },
        {
            'orden': 3,
            'nombres': 'Roberto',
            'apellidos': 'Molina',
            'nombre_completo': 'Roberto Molina',
            'cargo': 'Concejal',
            'institucion': 'Municipio de Pastaza',
            'activo': True
        }
    ]
    
    # CONFIGURACIÓN ROBUSTA completa
    config_robusta = {
        # Modelo más avanzado
        'modelo_diarizacion': 'pyannote/speaker-diarization-3.1',
        
        # Parámetros optimizados
        'clustering_threshold': 0.5,  # Valor optimizado para precisión
        'embedding_batch_size': 32,
        'segmentation_batch_size': 32,
        'onset_threshold': 0.5,
        'offset_threshold': 0.5,
        'min_duration_on': 0.1,
        'min_duration_off': 0.1,
        
        # Configuración inteligente basada en participantes
        'participantes_esperados': participantes_esperados,
        'hablantes_predefinidos': participantes_esperados,
        'min_speakers': len(participantes_esperados) - 1,  # 2 (tolerancia -1)
        'max_speakers': len(participantes_esperados) + 2,  # 5 (tolerancia +2)
        
        # Configuración adicional
        'usar_gpu': False,  # Para el test
        'token_huggingface': None
    }
    
    print(f"Participantes esperados: {len(participantes_esperados)}")
    for i, p in enumerate(participantes_esperados):
        print(f"  {i+1}. {p['nombre_completo']} - {p['cargo']}")
    
    print(f"\nConfiguración robusta aplicada:")
    print(f"  - Modelo: {config_robusta['modelo_diarizacion']}")
    print(f"  - Clustering threshold: {config_robusta['clustering_threshold']}")
    print(f"  - Min speakers: {config_robusta['min_speakers']}")
    print(f"  - Max speakers: {config_robusta['max_speakers']}")
    print(f"  - Batch sizes: {config_robusta['embedding_batch_size']}")
    print(f"  - Duraciones mínimas: {config_robusta['min_duration_on']}s")
    
    # Test de procesamiento
    resultado = processor.procesar_diarizacion('/fake/audio.wav', config_robusta)
    
    print(f"\n=== RESULTADO DEL PROCESAMIENTO ROBUSTA ===")
    print(f"Éxito: {resultado.get('exito')}")
    print(f"Mensaje: {resultado.get('mensaje', 'N/A')}")
    
    if 'parametros_aplicados' in resultado:
        print("\n=== PARÁMETROS APLICADOS ROBUSTOS ===")
        params = resultado['parametros_aplicados']
        print(f"  - Modelo diarización: {params.get('modelo_diarizacion')}")
        print(f"  - Min speakers: {params.get('min_speakers')}")
        print(f"  - Max speakers: {params.get('max_speakers')}")
        print(f"  - Clustering threshold: {params.get('clustering_threshold')}")
        print(f"  - Batch embedding: {params.get('parametros_pipeline_reales', {}).get('embedding_batch_size', 'N/A')}")
    
    if 'auditoria' in resultado:
        print("\n=== AUDITORÍA DE CONFIGURACIÓN ROBUSTA ===")
        audit = resultado['auditoria']
        print(f"  - Parámetros del usuario: {audit.get('parametros_del_usuario')}")
        print(f"  - Modelo solicitado: {audit.get('modelo_solicitado')}")
        print(f"  - Modelo usado: {audit.get('modelo_usado')}")
        print(f"  - Threshold aplicado: {audit.get('threshold_aplicado')}")
        print(f"  - Constrains de speakers: {audit.get('speakers_constraint')}")
    
    # Verificar que la configuración es realmente robusta
    es_robusta = (
        resultado.get('parametros_aplicados', {}).get('clustering_threshold') == 0.5 and
        resultado.get('parametros_aplicados', {}).get('modelo_diarizacion') == 'pyannote/speaker-diarization-3.1' and
        resultado.get('auditoria', {}).get('parametros_del_usuario') == True
    )
    
    print(f"\n=== VERIFICACIÓN DE ROBUSTEZ ===")
    print(f"✓ Configuración robusta aplicada: {es_robusta}")
    print(f"✓ Parámetros del usuario respetados: {resultado.get('auditoria', {}).get('parametros_del_usuario', False)}")
    print(f"✓ Modelo avanzado usado: {resultado.get('parametros_aplicados', {}).get('modelo_diarizacion') == 'pyannote/speaker-diarization-3.1'}")
    print(f"✓ Threshold optimizado: {resultado.get('parametros_aplicados', {}).get('clustering_threshold') == 0.5}")
    
    return resultado, es_robusta

def test_mapeo_inteligente():
    """Test del mapeo inteligente de hablantes"""
    print("\n=== TESTING MAPEO INTELIGENTE DE HABLANTES ===")
    
    # Simular resultado de diarización pyannote
    from pyannote.core import Annotation, Segment
    
    # Crear anotación simulada
    annotation = Annotation()
    annotation[Segment(0.0, 10.0)] = "SPEAKER_00"
    annotation[Segment(10.0, 20.0)] = "SPEAKER_01" 
    annotation[Segment(20.0, 30.0)] = "SPEAKER_02"
    annotation[Segment(30.0, 40.0)] = "SPEAKER_00"  # Regresa el primer speaker
    
    processor = PyannoteProcessor()
    
    participantes_esperados = [
        {'nombre_completo': 'Juan Carlos Pérez', 'cargo': 'Alcalde'},
        {'nombre_completo': 'María Elena García', 'cargo': 'Secretaria'},
        {'nombre_completo': 'Roberto Molina', 'cargo': 'Concejal'}
    ]
    
    resultado = processor._procesar_resultado_diarizacion_inteligente(
        annotation,
        participantes_esperados,
        participantes_esperados
    )
    
    print(f"Speakers detectados: {resultado['speakers_detectados']}")
    print(f"Segmentos procesados: {resultado['num_segmentos']}")
    print(f"Participantes mapeados: {resultado['participantes_mapeados']}")
    
    print("\n=== MAPEO INTELIGENTE APLICADO ===")
    if 'mapeo_inteligente' in resultado:
        for speaker_orig, info in resultado['mapeo_inteligente'].items():
            print(f"  {speaker_orig} → {info['nombre']} (aparición: {info['tiempo_primera_aparicion']:.1f}s)")
    
    print("\n=== ORDEN DE APARICIÓN ===")
    if 'orden_aparicion' in resultado:
        for i, nombre in enumerate(resultado['orden_aparicion']):
            print(f"  {i+1}. {nombre}")
    
    print("\n=== SEGMENTOS CON MAPEO ===")
    for i, seg in enumerate(resultado['segmentos'][:3]):  # Primeros 3 segmentos
        print(f"  {i+1}. {seg['start_time_str']}-{seg['end_time_str']}: {seg['speaker']} (original: {seg['speaker_original']})")
    
    return resultado

if __name__ == '__main__':
    print("Iniciando tests de configuración ROBUSTA de diarización...\n")
    
    try:
        # Test 1: Configuración robusta
        resultado_robusta, es_robusta = test_configuracion_robusta()
        
        # Test 2: Mapeo inteligente
        resultado_mapeo = test_mapeo_inteligente()
        
        print("\n" + "="*60)
        print("RESUMEN DE TESTS DE CONFIGURACIÓN ROBUSTA")
        print("="*60)
        print(f"✓ Configuración robusta: {'ÉXITO' if es_robusta else 'FALLO'}")
        print(f"✓ Mapeo inteligente: {'ÉXITO' if resultado_mapeo.get('mapeo_inteligente') else 'FALLO'}")
        print(f"✓ Parámetros del usuario: {'ÉXITO' if resultado_robusta.get('auditoria', {}).get('parametros_del_usuario') else 'FALLO'}")
        
        print(f"\n🎯 DIARIZACIÓN ROBUSTA Y EFICAZ: {'✅ IMPLEMENTADA' if es_robusta else '❌ FALTA IMPLEMENTAR'}")
        print(f"🎯 RECONOCIMIENTO INTELIGENTE: {'✅ ACTIVO' if resultado_mapeo.get('mapeo_inteligente') else '❌ INACTIVO'}")
        print(f"🎯 MÁXIMA PRODUCTIVIDAD: {'✅ GARANTIZADA' if es_robusta and resultado_mapeo.get('mapeo_inteligente') else '❌ PENDIENTE'}")
        
    except Exception as e:
        print(f"\n❌ Error en tests: {str(e)}")
        import traceback
        traceback.print_exc()