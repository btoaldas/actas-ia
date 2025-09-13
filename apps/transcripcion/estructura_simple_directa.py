"""
Estructura JSON simplificada y directa
Convierte resultados de whisper + pyannote a estructura conversacional
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

def generar_estructura_simple(resultado_whisper: Dict[str, Any], 
                            resultado_pyannote: Dict[str, Any],
                            procesamiento_audio,
                            transcripcion) -> Dict[str, Any]:
    """
    Genera estructura JSON SIMPLE y DIRECTA:
    
    {
        "cabecera": {
            "audio": { metadata del audio },
            "transcripcion": { metadata transcripción },
            "hablantes": { mapeo completo de speakers },
            "mapeo_hablantes": { "Hablante 0": "Beto", "Hablante 1": "Ely" }
        },
        "conversacion": [
            {
                "inicio": 5.23,
                "fin": 12.45,
                "hablante": "Beto",
                "hablante_id": 0,
                "texto": "Buenos días, comenzamos la sesión..."
            }
        ],
        "metadata": { estadísticas y info adicional }
    }
    """
    
    logger.info("🔧 GENERANDO ESTRUCTURA JSON SIMPLE Y DIRECTA")
    
    try:
        # PASO 1: Extraer datos básicos
        segmentos_whisper = resultado_whisper.get('segmentos', [])
        segmentos_pyannote = resultado_pyannote.get('segmentos_hablantes', [])
        
        # Validar que procesamiento_audio existe
        if not procesamiento_audio:
            logger.error("❌ procesamiento_audio es None")
            return {
                "cabecera": {"error": "No hay procesamiento_audio"},
                "conversacion": [],
                "metadata": {"error": "procesamiento_audio es None"}
            }
        
        participantes = procesamiento_audio.participantes_detallados if hasattr(procesamiento_audio, 'participantes_detallados') else []
        
        logger.info(f"📊 Datos básicos:")
        logger.info(f"  - Segmentos Whisper: {len(segmentos_whisper)}")
        logger.info(f"  - Segmentos Pyannote: {len(segmentos_pyannote)}")
        logger.info(f"  - Participantes configurados: {len(participantes)}")
        
        # PASO 2: Crear mapeo de hablantes mejorado
        mapeo_hablantes = {}
        hablantes_info = {}
        
        if participantes:
            for i, participante in enumerate(participantes):
                nombre = participante.get('nombres', f'Participante {i+1}')
                # 🔥 MAPEO DIRECTO PARA CONVERSACIÓN
                mapeo_hablantes[f'Hablante {i}'] = nombre
                hablantes_info[str(i)] = {
                    'nombre': nombre,
                    'participante': participante,
                    'id': i
                }
                logger.info(f"🎯 MAPEO DIRECTO: Hablante {i} → {nombre}")
        else:
            # Si no hay participantes, crear mapeo básico
            mapeo_hablantes['Hablante 0'] = 'Hablante Único'
            hablantes_info['0'] = {
                'nombre': 'Hablante Único',
                'participante': {},
                'id': 0
            }
        
        # PASO 3: Crear cabecera completa
        cabecera = {
            "audio": {
                "id": procesamiento_audio.id,
                "archivo_audio": procesamiento_audio.archivo_audio.name if procesamiento_audio.archivo_audio else "",
                "duracion": getattr(procesamiento_audio, 'duracion', 0),
                "created_at": procesamiento_audio.created_at.isoformat() if hasattr(procesamiento_audio, 'created_at') else "",
                "tipo_reunion": str(procesamiento_audio.tipo_reunion) if procesamiento_audio.tipo_reunion else "",
                "ubicacion": getattr(procesamiento_audio, 'ubicacion', ''),
                "participantes_detallados": participantes
            },
            "transcripcion": {
                "id": transcripcion.id,
                "fecha_procesamiento": datetime.now().isoformat(),
                "estado": str(transcripcion.estado),
                "modelo_whisper": getattr(transcripcion, 'modelo_whisper', 'medium'),
                "idioma_detectado": getattr(transcripcion, 'idioma_detectado', 'es'),
                "total_segmentos": len(segmentos_whisper)
            },
            "hablantes": hablantes_info,
            "mapeo_hablantes": mapeo_hablantes,
            "total_hablantes": len(participantes) if participantes else 1
        }
        
        # PASO 4: Crear conversación con estructura mejorada
        # 🎯 ESTRUCTURA SOLICITADA: inicio, hablante, texto
        conversacion = []
        
        logger.info(f"🔧 Generando conversación estructurada...")
        
        for i, segmento in enumerate(segmentos_whisper):
            # 1. OBTENER TIEMPO DE INICIO
            inicio = segmento.get('start', 0)
            fin = segmento.get('end', 0)
            texto = segmento.get('text', '').strip()
            
            # Saltar segmentos sin texto
            if not texto:
                continue
            
            # 2. BUSCAR HABLANTE EN PYANNOTE POR COINCIDENCIA TEMPORAL
            speaker_id = 0  # Default
            speaker_name = "Hablante 0"  # Default para mapeo
            
            if segmentos_pyannote:
                # Buscar segmento de pyannote que coincida temporalmente
                for seg_pya in segmentos_pyannote:
                    inicio_pya = seg_pya.get('inicio', 0)
                    fin_pya = seg_pya.get('fin', 0)
                    
                    # Si hay overlap temporal entre whisper y pyannote
                    if not (fin <= inicio_pya or inicio >= fin_pya):  # Hay overlap
                        speaker_id = seg_pya.get('speaker', 0)
                        speaker_name_pyannote = seg_pya.get('speaker_name', f'Hablante {speaker_id}')
                        speaker_name = f'Hablante {speaker_id}'  # Para buscar en mapeo
                        break
            
            # 3. APLICAR MAPEO DE NOMBRES REALES
            nombre_final = speaker_name  # Default
            if speaker_name in mapeo_hablantes:
                nombre_final = mapeo_hablantes[speaker_name]
            elif f'Hablante {speaker_id}' in mapeo_hablantes:
                nombre_final = mapeo_hablantes[f'Hablante {speaker_id}']
            
            # 4. CREAR SEGMENTO CON ESTRUCTURA SOLICITADA
            segmento_estructurado = {
                "inicio": round(inicio, 2),  # Tiempo en segundos
                "fin": round(fin, 2),        # Tiempo fin (opcional pero útil)
                "hablante": nombre_final,    # Nombre real del hablante
                "hablante_id": speaker_id,   # ID numérico del hablante
                "texto": texto,              # Texto transcrito
                "duracion": round(fin - inicio, 2)  # Duración del segmento
            }
            
            conversacion.append(segmento_estructurado)
            
            if i < 3:  # Log primeros 3 para debug
                logger.info(f"📝 Segmento {i+1}: {inicio:.1f}s → {nombre_final}: '{texto[:50]}...'")
        
        logger.info(f"✅ Conversación generada: {len(conversacion)} segmentos válidos")
        
        # PASO 5: Generar texto bruto estructurado (Tiempo,hablante,texto)
        texto_estructurado_lineas = []
        for seg in conversacion:
            # Formato: "00:05.2,Beto,Hola muy buenas noches..."
            minutos = int(seg['inicio'] // 60)
            segundos = seg['inicio'] % 60
            tiempo_formato = f"{minutos:02d}:{segundos:05.2f}"
            
            linea = f"{tiempo_formato},{seg['hablante']},{seg['texto']}"
            texto_estructurado_lineas.append(linea)
        
        texto_bruto_estructurado = '\n'.join(texto_estructurado_lineas)
        
        logger.info(f"📝 Texto estructurado generado: {len(texto_estructurado_lineas)} líneas")
        
        # PASO 6: Metadata adicional
        metadata = {
            "generado_en": datetime.now().isoformat(),
            "backend_whisper": "openai-whisper",
            "backend_diarizacion": "pyannote-audio" if segmentos_pyannote else "sin_diarizacion",
            "total_duracion": sum(seg.get('duracion', 0) for seg in conversacion),
            "total_palabras": len(' '.join(seg.get('texto', '') for seg in conversacion).split()),
            "total_segmentos": len(conversacion),
            "mapeo_aplicado": bool(participantes and len(participantes) > 0),
            "formato_tiempo": "MM:SS.ss",
            "estructura_segmentos": ["inicio", "fin", "hablante", "hablante_id", "texto", "duracion"]
        }
        
        # RESULTADO FINAL COMPLETO
        estructura_final = {
            "cabecera": cabecera,
            "conversacion": conversacion,  # 🎯 Array con: inicio, hablante, texto
            "texto_estructurado": texto_bruto_estructurado,  # 🎯 Texto bruto: Tiempo,hablante,texto
            "metadata": metadata
        }
        
        logger.info(f"✅ ESTRUCTURA COMPLETA GENERADA:")
        logger.info(f"  - Cabecera: ✓ (audio + transcripcion + mapeo)")
        logger.info(f"  - Conversación: {len(conversacion)} segmentos estructurados")
        logger.info(f"  - Texto estructurado: {len(texto_estructurado_lineas)} líneas")
        logger.info(f"  - Hablantes mapeados: {len(mapeo_hablantes)}")
        logger.info(f"  - Metadata: ✓")
        
        return estructura_final
        
    except Exception as e:
        logger.error(f"❌ Error generando estructura simple: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Estructura mínima de fallback sin usar variables que pueden no estar en scope
        audio_info = {"error": "Error procesando metadata audio"}
        transcripcion_info = {"error": "Error procesando metadata transcripción"}
        
        # Intentar obtener info básica si las variables están disponibles
        try:
            if 'procesamiento_audio' in locals() and procesamiento_audio:
                audio_info = {
                    "id": getattr(procesamiento_audio, 'id', 'N/A'),
                    "error": "Error parcial procesando audio"
                }
        except:
            pass
            
        try:
            if 'transcripcion' in locals() and transcripcion:
                transcripcion_info = {
                    "id": getattr(transcripcion, 'id', 'N/A'),
                    "error": "Error parcial procesando transcripción"
                }
        except:
            pass
        
        return {
            "cabecera": {
                "audio": audio_info,
                "transcripcion": transcripcion_info,
                "hablantes": {},
                "mapeo_hablantes": {}
            },
            "conversacion": [],
            "texto_estructurado": "",
            "metadata": {
                "error": str(e),
                "generado_en": datetime.now().isoformat(),
                "estructura_segmentos": "Error - fallback generado"
            }
        }