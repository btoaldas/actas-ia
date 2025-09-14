# Módulo de Transcripción Avanzada – Actas IA

## Descripción General
Este módulo implementa el flujo completo de transcripción municipal con IA, integrando Whisper (transcripción automática) y pyannote (diarización de hablantes), adaptado para el Municipio de Pastaza.

### Proceso Principal
1. **Ingesta de audio**: El usuario sube o selecciona un audio desde el dashboard de audios por transcribir.
2. **Transcripción y diarización**: El sistema procesa el audio con Whisper y pyannote, generando segmentos con tiempos y hablantes detectados.
3. **Edición avanzada**: El usuario accede al editor avanzado para revisar, editar, insertar, eliminar segmentos y gestionar hablantes.
4. **Regeneración y reinicio**: El usuario puede eliminar la transcripción y reiniciar el proceso desde cero, dejando el audio listo para una nueva transcripción.

## Vistas Principales
- **Dashboard de audios por transcribir** (`dashboard_audios_transcribir`): Lista todos los audios listos para iniciar el proceso.
- **Dashboard de transcripciones realizadas** (`dashboard_transcripciones_hechas`): Muestra todas las transcripciones completadas y en proceso.
- **Editor avanzado** (`detalle_transcripcion_dashboard`): Permite edición granular de segmentos, hablantes, regeneración y visualización de la estructura JSON.
- **Vista de resultado** (`vista_resultado_transcripcion`): Presenta el acta final y métricas del proceso.

## APIs y Endpoints
- **CRUD de segmentos**: Editar, eliminar, insertar segmentos en posiciones específicas.
- **Gestión de hablantes**: Agregar, renombrar, eliminar hablantes.
- **Regeneración**: Elimina la transcripción y su historial, deja el audio listo para transcribir nuevamente.
- **Consulta de estado**: Verifica el progreso y estado de procesamiento vía Celery.
- **Normalización robusta**: Todas las APIs validan y normalizan la estructura JSON para evitar errores por datos inconsistentes.

## Integración IA
- **Whisper**: Transcribe el audio y genera texto con timestamps.
- **pyannote**: Diariza los segmentos, asignando hablantes y tiempos.
- **Celery**: Procesa tareas pesadas en segundo plano, con fallback si el worker no está disponible.

## Estructura de Datos
- **conversacion_json**: Dict principal con:
  - `cabecera`: Incluye `mapeo_hablantes` (siempre dict, normalizado).
  - `conversacion`: Lista de segmentos (inicio, fin, texto, hablante, hablante_id).
  - `metadata`: Información adicional del proceso.
- **Historial de ediciones**: Cada cambio relevante queda registrado para auditoría.

## Limpieza y Reinicio
- Al regenerar, se elimina la transcripción y todo su historial.
- El audio queda en estado `completado`, listo para iniciar una nueva transcripción.
- No quedan datos residuales en la base de datos.

## Templates y Frontend
- **AdminLTE**: Todas las vistas usan el framework municipal estándar.
- **Modales**: Para edición de segmentos y gestión de hablantes.
- **Filtros de plantilla**: `speaker_label` para mostrar etiquetas seguras de hablantes.
- **JS robusto**: Validaciones y normalización de datos en el frontend.

## Seguridad y Auditoría
- **Autenticación**: Requiere login para acciones críticas.
- **Auditoría**: Todas las acciones quedan registradas.
- **Validación de datos**: APIs y vistas robustas contra datos inconsistentes.

## Actualizaciones y Refactorizaciones
- Se eliminaron referencias obsoletas y se robusteció el manejo de errores.
- Se refactorizó el backend y frontend para mayor estabilidad y claridad.
- Se documentó el proceso completo y se mejoró la integración con Celery y el sistema de auditoría.

## Uso
1. Subir audio → aparece en dashboard de audios por transcribir.
2. Iniciar transcripción → procesamiento IA (Whisper + pyannote).
3. Editar y gestionar segmentos/hablantes en el editor avanzado.
4. Regenerar si es necesario → audio vuelve a estar disponible para nuevo proceso.

---

**Actas IA – Municipio de Pastaza**
