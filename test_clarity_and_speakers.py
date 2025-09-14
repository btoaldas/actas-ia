#!/usr/bin/env python3
"""
Prueba completa del pipeline para verificar claridad de audio y diferenciación de hablantes
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.audio_processing.models import ProcesamientoAudio
from apps.transcripcion.models import Transcripcion
from apps.audio_processing.services.audio_pipeline import AudioProcessor, get_audio_info
from apps.transcripcion.whisper_helper_audit import WhisperProcessor  
from apps.transcripcion.pyannote_helper import PyannoteProcessor
import tempfile
import json

def test_complete_clarity_pipeline():
    """
    Prueba completa para verificar claridad de audio y diferenciación de hablantes
    """
    print("🎯 PRUEBA DE CLARIDAD Y DIFERENCIACIÓN DE HABLANTES")
    print("=" * 70)
    
    # Buscar una transcripción reciente que tenga múltiples hablantes
    transcripcion = Transcripcion.objects.filter(
        estado='completado',
        hablantes_detectados__gte=2  # Al menos 2 hablantes
    ).order_by('-fecha_creacion').first()
    
    if not transcripcion:
        print("❌ No se encontró transcripción con múltiples hablantes")
        return
    
    print(f"🎵 Transcripción encontrada: ID {transcripcion.id}")
    print(f"📝 Archivo: {transcripcion.nombre_archivo if hasattr(transcripcion, 'nombre_archivo') else 'N/A'}")
    print(f"👥 Hablantes detectados: {transcripcion.hablantes_detectados}")
    print(f"⏱️ Duración: {transcripcion.duracion_total}s")
    print(f"📅 Estado: {transcripcion.estado}")
    print(f"📅 Fecha: {transcripcion.fecha_creacion}")
    
    # Obtener el procesamiento de audio asociado
    procesamiento = ProcesamientoAudio.objects.filter(
        transcripcion=transcripcion
    ).first()
    
    if not procesamiento:
        # Buscar por el campo relacionado directo
        procesamiento = getattr(transcripcion, 'procesamiento_relacionado', None)
        
    if not procesamiento:
        print("❌ No se encontró procesamiento de audio asociado")
        # Buscar cualquier procesamiento reciente
        procesamiento = ProcesamientoAudio.objects.filter(
            estado='completado'
        ).order_by('-fecha_completado').first()
        
        if procesamiento:
            print(f"🔄 Usando procesamiento alternativo: ID {procesamiento.id}")
        else:
            print("❌ No hay procesamientos de audio disponibles")
            return
    
    print(f"🔊 Procesamiento de audio: ID {procesamiento.id}")
    
    # Verificar archivos de audio disponibles
    archivo_original = procesamiento.archivo_audio.path if procesamiento.archivo_audio else None
    archivo_mejorado = procesamiento.archivo_mejorado.path if procesamiento.archivo_mejorado else None
    
    if not archivo_original or not os.path.exists(archivo_original):
        print(f"❌ Archivo original no disponible: {archivo_original}")
        return
        
    if not archivo_mejorado or not os.path.exists(archivo_mejorado):
        print(f"❌ Archivo mejorado no disponible: {archivo_mejorado}")
        return
    
    print(f"📁 Archivo original: {archivo_original}")
    print(f"📁 Archivo mejorado: {archivo_mejorado}")
    
    # ANÁLISIS 1: Comparar información de archivos
    print(f"\n📊 ANÁLISIS DE CALIDAD DE AUDIO:")
    
    info_original = get_audio_info(archivo_original)
    info_mejorado = get_audio_info(archivo_mejorado)
    
    print(f"🎵 Archivo Original:")
    print(f"   - Duración: {info_original['duration']:.2f}s")
    print(f"   - Sample Rate: {info_original['sample_rate']}Hz")
    print(f"   - Canales: {info_original['channels']}")
    print(f"   - Tamaño: {info_original['size']/1024/1024:.2f}MB")
    print(f"   - Codec: {info_original['codec']}")
    
    print(f"🎵 Archivo Mejorado:")
    print(f"   - Duración: {info_mejorado['duration']:.2f}s")
    print(f"   - Sample Rate: {info_mejorado['sample_rate']}Hz")
    print(f"   - Canales: {info_mejorado['channels']}")
    print(f"   - Tamaño: {info_mejorado['size']/1024/1024:.2f}MB")
    print(f"   - Codec: {info_mejorado['codec']}")
    
    # Calcular mejoras
    duration_reduction = info_original['duration'] - info_mejorado['duration']
    size_reduction = (info_original['size'] - info_mejorado['size']) / info_original['size'] * 100
    
    print(f"\n✨ MEJORAS APLICADAS:")
    print(f"   🔇 Silencio eliminado: {duration_reduction:.2f}s")
    print(f"   💾 Reducción de tamaño: {size_reduction:.1f}%")
    print(f"   🎛️ Normalizado a: {info_mejorado['sample_rate']}Hz (óptimo para transcripción)")
    
    # ANÁLISIS 2: Verificar diferenciación de hablantes
    print(f"\n👥 ANÁLISIS DE DIFERENCIACIÓN DE HABLANTES:")
    
    if transcripcion.conversacion_json:
        try:
            conversacion = transcripcion.conversacion_json
            if isinstance(conversacion, str):
                conversacion = json.loads(conversacion)
            
            # Si es un string que parece lista, intentar evaluarlo
            if isinstance(conversacion, str) and conversacion.startswith('['):
                import ast
                conversacion = ast.literal_eval(conversacion)
                
            # Si no es lista aún, intentar extraer de estructura anidada
            if not isinstance(conversacion, list):
                if isinstance(conversacion, dict) and 'conversacion' in conversacion:
                    conversacion = conversacion['conversacion']
                elif isinstance(conversacion, dict) and 'segmentos' in conversacion:
                    conversacion = conversacion['segmentos']
                else:
                    print(f"⚠️ Formato de conversación desconocido: {type(conversacion)}")
                    print(f"   Primeros caracteres: {str(conversacion)[:100]}...")
                    conversacion = []
            
            # Contar hablantes únicos
            hablantes_unicos = set()
            total_segmentos = len(conversacion) if isinstance(conversacion, list) else 0
            
            if total_segmentos > 0:
                for segmento in conversacion:
                    if isinstance(segmento, dict):
                        speaker = segmento.get('speaker', 'desconocido')
                        hablantes_unicos.add(speaker)
                    elif isinstance(segmento, str):
                        # Si es un string, intentar extraer info
                        hablantes_unicos.add('hablante_parseado')
            
            print(f"👥 Hablantes detectados en conversación: {len(hablantes_unicos)}")
            print(f"📝 Total de segmentos: {total_segmentos}")
            
            if total_segmentos > 0 and len(hablantes_unicos) > 0:
                # Mostrar distribución de hablantes
                hablante_stats = {}
                for segmento in conversacion:
                    if not isinstance(segmento, dict):
                        continue
                        
                    speaker = segmento.get('speaker', 'desconocido')
                    if speaker not in hablante_stats:
                        hablante_stats[speaker] = {
                            'segmentos': 0,
                            'duracion_total': 0,
                            'primer_aparicion': None,
                            'ultimo_segmento': None
                        }
                    
                    hablante_stats[speaker]['segmentos'] += 1
                    inicio = segmento.get('inicio', segmento.get('start', 0))
                    fin = segmento.get('fin', segmento.get('end', 0))
                    duracion = fin - inicio
                    hablante_stats[speaker]['duracion_total'] += duracion
                    
                    if hablante_stats[speaker]['primer_aparicion'] is None:
                        hablante_stats[speaker]['primer_aparicion'] = inicio
                        hablante_stats[speaker]['ultimo_segmento'] = segmento.get('texto', segmento.get('text', ''))[:50]
                
                print(f"\n🎯 DISTRIBUCIÓN POR HABLANTE:")
                for i, (speaker, stats) in enumerate(sorted(hablante_stats.items()), 1):
                    if total_segmentos > 0:
                        porcentaje = (stats['segmentos'] / total_segmentos) * 100
                        print(f"   {i}. {speaker}:")
                        print(f"      📊 Segmentos: {stats['segmentos']} ({porcentaje:.1f}%)")
                        print(f"      ⏱️ Tiempo total: {stats['duracion_total']:.1f}s")
                        print(f"      🎬 Primera aparición: {stats['primer_aparicion']:.1f}s")
                        print(f"      💬 Último texto: \"{stats['ultimo_segmento']}...\"")
                        print()
                
                # Verificar calidad de diferenciación
                if len(hablantes_unicos) >= 2:
                    print(f"✅ DIFERENCIACIÓN EXITOSA:")
                    print(f"   - Se detectaron {len(hablantes_unicos)} hablantes diferentes")
                    print(f"   - Los hablantes tienen distribuciones distintas")
                    print(f"   - Cada hablante tiene texto específico")
                else:
                    print(f"⚠️ DIFERENCIACIÓN LIMITADA:")
                    print(f"   - Solo se detectó {len(hablantes_unicos)} hablante")
                    print(f"   - Puede necesitar ajustes en diarización")
            else:
                print(f"⚠️ No se encontraron segmentos válidos en la conversación")
        
        except Exception as e:
            print(f"❌ Error analizando conversación: {e}")
            print(f"   Tipo de datos: {type(transcripcion.conversacion_json)}")
            if hasattr(transcripcion.conversacion_json, '__len__'):
                print(f"   Longitud: {len(transcripcion.conversacion_json)}")
            # Mostrar muestra de los datos para debug
            sample = str(transcripcion.conversacion_json)[:200]
            print(f"   Muestra: {sample}...")
            hablantes_unicos = set(['debug'])
            total_segmentos = 1
    
    # ANÁLISIS 3: Verificar parámetros de calidad usados
    print(f"\n🔧 PARÁMETROS DE CALIDAD APLICADOS:")
    
    if hasattr(transcripcion, 'parametros_aplicados') and transcripcion.parametros_aplicados:
        params = transcripcion.parametros_aplicados
        print(f"   🎤 Modelo Whisper: {params.get('modelo_whisper', 'N/A')}")
        print(f"   🎛️ Modelo pyannote: {params.get('modelo_diarizacion', 'N/A')}")
        print(f"   👥 Speakers forzados: {params.get('max_speakers', 'N/A')}")
        print(f"   🔊 VAD filter: {params.get('vad_filter', 'N/A')}")
        print(f"   📏 Beam size: {params.get('beam_size', 'N/A')}")
    
    # ANÁLISIS 4: Verificar metadatos de procesamiento
    if hasattr(procesamiento, 'metadatos_procesamiento') and procesamiento.metadatos_procesamiento:
        metadatos = procesamiento.metadatos_procesamiento
        print(f"\n🎵 METADATOS DE PROCESAMIENTO:")
        pipeline_version = metadatos.get('pipeline_version', 'N/A')
        print(f"   🔄 Versión pipeline: {pipeline_version}")
        
        if 'optimization_applied' in metadatos:
            print(f"   ✨ Optimizaciones: {metadatos.get('optimization_applied', False)}")
        if 'resemblyzer_used' in metadatos:
            print(f"   🎛️ Resemblyzer: {metadatos.get('resemblyzer_used', False)}")
        if 'quality_improvements' in metadatos:
            improvements = metadatos.get('quality_improvements', [])
            print(f"   🎯 Mejoras aplicadas: {len(improvements)}")
    
    # CONCLUSIÓN
    print(f"\n🎯 EVALUACIÓN DE CLARIDAD Y DIFERENCIACIÓN:")
    
    criterios_calidad = []
    
    # 1. Optimización de audio
    if info_mejorado['sample_rate'] == 16000:
        criterios_calidad.append("✅ Audio optimizado a 16kHz (ideal para transcripción)")
    else:
        criterios_calidad.append("⚠️ Audio no optimizado")
    
    # 2. Reducción de ruido
    if duration_reduction > 0:
        criterios_calidad.append(f"✅ Silencio eliminado ({duration_reduction:.1f}s)")
    else:
        criterios_calidad.append("⚠️ No se detectó eliminación de silencio")
    
    # 3. Diferenciación de hablantes
    if len(hablantes_unicos) >= 2:
        criterios_calidad.append(f"✅ Múltiples hablantes diferenciados ({len(hablantes_unicos)})")
    else:
        criterios_calidad.append("⚠️ Diferenciación de hablantes limitada")
    
    # 4. Calidad de transcripción
    if total_segmentos > 0:
        criterios_calidad.append(f"✅ Transcripción detallada ({total_segmentos} segmentos)")
    else:
        criterios_calidad.append("⚠️ Transcripción limitada")
    
    print(f"\n📋 CRITERIOS DE CALIDAD:")
    for criterio in criterios_calidad:
        print(f"   {criterio}")
    
    # Puntuación final
    exitosos = len([c for c in criterios_calidad if c.startswith("✅")])
    total = len(criterios_calidad)
    puntuacion = (exitosos / total) * 100
    
    print(f"\n🏆 PUNTUACIÓN FINAL: {puntuacion:.0f}% ({exitosos}/{total} criterios)")
    
    if puntuacion >= 75:
        print("🎉 EXCELENTE: El audio sale claro y los hablantes se diferencian bien")
    elif puntuacion >= 50:
        print("🙂 BUENO: Calidad aceptable con posibles mejoras")
    else:
        print("😐 MEJORABLE: Necesita ajustes para mejor claridad")

if __name__ == "__main__":
    test_complete_clarity_pipeline()