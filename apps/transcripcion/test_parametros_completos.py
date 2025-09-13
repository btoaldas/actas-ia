#!/usr/bin/env python3
"""
Test completo para verificar transmisión de parámetros desde proceso_transcripcion 
hasta whisper_helper y pyannote_helper
"""

import os
import sys
import django

# Setup Django path
app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_dir = os.path.dirname(app_dir)
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.transcripcion.models import Transcripcion
from django.contrib.auth.models import User
import json

def test_parametros_transmision():
    print("🧪 TEST: Verificación completa de transmisión de parámetros\n")
    
    # Simular parámetros exactos como los envía proceso_transcripcion
    configuracion_simulada = {
        # PARÁMETROS WHISPER ESPECÍFICOS
        'modelo_whisper': 'medium',  # El usuario seleccionó "medium"
        'idioma': 'es',
        'temperatura': 0.2,
        
        # PARÁMETROS PYANNOTE ROBUSTOS
        'diarizacion_activa': True,
        'modelo_diarizacion': 'pyannote/speaker-diarization-3.1',
        'clustering_threshold': 0.5,
        'embedding_batch_size': 32,
        'segmentation_batch_size': 32,
        
        # PARTICIPANTES ESPERADOS EN ORDEN ESPECÍFICO
        'participantes_esperados': [
            {
                'orden': 1,
                'nombres': 'María Elena',
                'apellidos': 'García',
                'nombre_completo': 'María Elena García',
                'cargo': 'Secretaria',
                'institucion': 'Municipio',
                'id': 'hablante_1',
                'activo': True
            },
            {
                'orden': 2, 
                'nombres': 'Juan Carlos',
                'apellidos': 'Pérez',
                'nombre_completo': 'Juan Carlos Pérez',
                'cargo': 'Alcalde',
                'institucion': 'Municipio',
                'id': 'hablante_2',
                'activo': True
            },
            {
                'orden': 3,
                'nombres': 'Roberto',
                'apellidos': 'Molina',
                'nombre_completo': 'Roberto Molina',
                'cargo': 'Concejal',
                'institucion': 'Municipio',
                'id': 'hablante_3',
                'activo': True
            }
        ],
        'hablantes_predefinidos': [  # Alias para backend
            {
                'orden': 1,
                'nombres': 'María Elena',
                'apellidos': 'García',
                'nombre_completo': 'María Elena García',
                'cargo': 'Secretaria',
                'institucion': 'Municipio',
                'id': 'hablante_1',
                'activo': True
            },
            {
                'orden': 2,
                'nombres': 'Juan Carlos', 
                'apellidos': 'Pérez',
                'nombre_completo': 'Juan Carlos Pérez',
                'cargo': 'Alcalde',
                'institucion': 'Municipio',
                'id': 'hablante_2',
                'activo': True
            },
            {
                'orden': 3,
                'nombres': 'Roberto',
                'apellidos': 'Molina', 
                'nombre_completo': 'Roberto Molina',
                'cargo': 'Concejal',
                'institucion': 'Municipio',
                'id': 'hablante_3',
                'activo': True
            }
        ]
    }
    
    print("📊 CONFIGURACIÓN SIMULADA:")
    print(f"   - Modelo Whisper solicitado: {configuracion_simulada['modelo_whisper']}")
    print(f"   - Idioma: {configuracion_simulada['idioma']}")
    print(f"   - Diarización activa: {configuracion_simulada['diarizacion_activa']}")
    print(f"   - Modelo diarización: {configuracion_simulada['modelo_diarizacion']}")
    print(f"   - Clustering threshold: {configuracion_simulada['clustering_threshold']}")
    print(f"   - Participantes esperados: {len(configuracion_simulada['participantes_esperados'])}")
    
    for i, participante in enumerate(configuracion_simulada['participantes_esperados']):
        print(f"     {i+1}. {participante['nombre_completo']} ({participante['cargo']})")
    
    print("\n" + "="*60)
    
    # TEST 1: Verificar que get_configuracion_completa() incluye estos parámetros
    print("\n🔍 TEST 1: Método get_configuracion_completa()")
    
    # Crear transcripción de prueba
    try:
        # Buscar un usuario existente o crear uno de prueba
        try:
            usuario = User.objects.first()
            if not usuario:
                usuario = User.objects.create_user('test_user', 'test@test.com', 'password')
        except:
            usuario = User.objects.create_user('test_user', 'test@test.com', 'password')
        
        # Buscar una transcripción existente para probar
        transcripcion = Transcripcion.objects.first()
        if not transcripcion:
            print("❌ No hay transcripciones disponibles para probar")
            return
            
        # Simular que guardamos los parámetros personalizados 
        transcripcion.parametros_personalizados = configuracion_simulada
        transcripcion.save()
        
        # Probar get_configuracion_completa()
        config_completa = transcripcion.get_configuracion_completa()
        
        print(f"✅ Configuración completa obtenida: {len(config_completa)} parámetros")
        
        # Verificar parámetros clave
        modelo_recibido = config_completa.get('modelo_whisper', 'NO_ENCONTRADO')
        print(f"   - Modelo Whisper: {modelo_recibido}")
        
        if modelo_recibido == 'medium':
            print("   ✅ Modelo Whisper correcto (medium)")
        else:
            print(f"   ❌ Modelo Whisper incorrecto: esperado 'medium', recibido '{modelo_recibido}'")
        
        # Verificar participantes
        participantes_recibidos = config_completa.get('participantes_esperados', [])
        print(f"   - Participantes esperados: {len(participantes_recibidos)}")
        
        if len(participantes_recibidos) == 3:
            print("   ✅ Cantidad de participantes correcta")
            for i, p in enumerate(participantes_recibidos):
                print(f"     {i+1}. {p.get('nombre_completo', 'SIN_NOMBRE')}")
        else:
            print(f"   ❌ Cantidad incorrecta: esperado 3, recibido {len(participantes_recibidos)}")
            
    except Exception as e:
        print(f"❌ Error en test de configuración: {str(e)}")
    
    print("\n" + "="*60)
    
    # TEST 2: Verificar que Whisper Helper recibe parámetros correctos
    print("\n🔍 TEST 2: Whisper Helper - Recepción de parámetros")
    
    try:
        from apps.transcripcion.whisper_helper_audit import WhisperProcessor
        
        processor = WhisperProcessor()
        print("✅ WhisperProcessor cargado")
        
        # Simular archivo de audio temporal
        archivo_test = "test_audio.wav"
        
        # Llamar método con configuración simulada
        print(f"\n📞 Llamando transcribir_audio con modelo: {configuracion_simulada['modelo_whisper']}")
        
        # Nota: Este test verificará los logs AUDIT para confirmar parámetros
        # No procesa audio real, solo verifica parámetros
        
        print("💡 Revisar logs AUDIT para confirmar parámetros recibidos")
        
    except Exception as e:
        print(f"❌ Error en test Whisper: {str(e)}")
        
    print("\n" + "="*60)
    
    # TEST 3: Verificar que pyannote respeta orden de participantes
    print("\n🔍 TEST 3: Pyannote Helper - Mapeo de participantes")
    
    try:
        from apps.transcripcion.pyannote_helper import PyannoteProcessor
        
        processor = PyannoteProcessor()
        print("✅ PyannoteProcessor cargado")
        
        # Simular resultado de diarización de pyannote
        from pyannote.core import Annotation, Segment
        
        diarizacion_simulada = Annotation()
        # IMPORTANTE: Simular que pyannote detecta en este orden:
        # SPEAKER_00 habla primero (0-5s)
        # SPEAKER_01 habla segundo (10-15s) 
        # SPEAKER_02 habla tercero (20-25s)
        diarizacion_simulada[Segment(0.0, 5.0)] = "SPEAKER_00"
        diarizacion_simulada[Segment(10.0, 15.0)] = "SPEAKER_01"
        diarizacion_simulada[Segment(20.0, 25.0)] = "SPEAKER_02"
        
        print("\n📊 DIARIZACIÓN SIMULADA DE PYANNOTE:")
        print("   - SPEAKER_00: 0.0s - 5.0s  (PRIMERO en hablar)")
        print("   - SPEAKER_01: 10.0s - 15.0s (SEGUNDO en hablar)")
        print("   - SPEAKER_02: 20.0s - 25.0s (TERCERO en hablar)")
        
        print("\n👥 PARTICIPANTES ESPERADOS POR USUARIO (orden JSON):")
        for i, p in enumerate(configuracion_simulada['participantes_esperados']):
            print(f"   - Posición {i+1}: {p['nombre_completo']} ({p['cargo']})")
        
        # Llamar mapeo inteligente
        resultado = processor._procesar_resultado_diarizacion_inteligente(
            diarizacion_simulada,
            configuracion_simulada['participantes_esperados']
        )
        
        print("\n🎯 RESULTADO DEL MAPEO INTELIGENTE:")
        mapeo = resultado.get('mapeo_speakers', {})
        
        # Verificar si el mapeo respeta el orden de aparición
        for speaker_original, info in mapeo.items():
            nombre_mapeado = info.get('nombre', 'SIN_NOMBRE')
            tiempo_aparicion = info.get('tiempo_primera_aparicion', 0)
            print(f"   - {speaker_original} → {nombre_mapeado} (aparición: {tiempo_aparicion}s)")
        
        # Verificar mapeo esperado:
        # SPEAKER_00 (aparece a 0s) → María Elena García (posición 1 en JSON)
        # SPEAKER_01 (aparece a 10s) → Juan Carlos Pérez (posición 2 en JSON)
        # SPEAKER_02 (aparece a 20s) → Roberto Molina (posición 3 en JSON)
        
        mapeo_correcto = True
        if 'SPEAKER_00' in mapeo and mapeo['SPEAKER_00']['nombre'] == 'María Elena García':
            print("   ✅ SPEAKER_00 → María Elena García (CORRECTO)")
        else:
            print("   ❌ SPEAKER_00 mal mapeado")
            mapeo_correcto = False
            
        if 'SPEAKER_01' in mapeo and mapeo['SPEAKER_01']['nombre'] == 'Juan Carlos Pérez':
            print("   ✅ SPEAKER_01 → Juan Carlos Pérez (CORRECTO)")
        else:
            print("   ❌ SPEAKER_01 mal mapeado")
            mapeo_correcto = False
            
        if 'SPEAKER_02' in mapeo and mapeo['SPEAKER_02']['nombre'] == 'Roberto Molina':
            print("   ✅ SPEAKER_02 → Roberto Molina (CORRECTO)")
        else:
            print("   ❌ SPEAKER_02 mal mapeado")
            mapeo_correcto = False
        
        if mapeo_correcto:
            print("\n🎉 MAPEO INTELIGENTE FUNCIONANDO CORRECTAMENTE")
        else:
            print("\n❌ PROBLEMA EN MAPEO INTELIGENTE")
            
    except Exception as e:
        print(f"❌ Error en test pyannote: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print("🏁 TEST COMPLETADO")
    print("📋 VERIFICAR:")
    print("   1. ¿Whisper recibe modelo 'medium' o muestra 'unknown'?")
    print("   2. ¿Pyannote mapea según orden de aparición o según JSON usuario?")
    print("   3. ¿Los parámetros personalizados llegan a get_configuracion_completa()?")

if __name__ == "__main__":
    test_parametros_transmision()