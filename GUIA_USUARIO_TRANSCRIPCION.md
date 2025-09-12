# 📋 Guía de Acceso para Usuarios - Módulo de Transcripción

## 🎯 **Dónde encontrar la funcionalidad de Transcripción**

### 1. **Acceso al Sistema**
```
URL principal: http://localhost:8000
```

### 2. **Navegación en el Menú Principal**

Una vez que inicies sesión, encontrarás en el **sidebar izquierdo** la siguiente estructura:

```
🗣️ Transcripción
 ├── 🎵 Audios Listos para Transcribir    ← NUEVA FUNCIONALIDAD
 ├── 📋 Lista de Transcripciones
 ├── ⚙️ Configuración
 └── 📊 Estadísticas
```

### 3. **Flujo de Trabajo Completo**

#### **Paso 1: Procesamiento de Audio**
```
🎙️ Proceso de Audio
 ├── 🎯 Centro de Audio              ← Grabar o subir archivos
 ├── 📋 Lista de Procesos           ← Ver estado de procesamiento
 └── ⚙️ Tipos de Reunión           ← Configurar tipos
```

#### **Paso 2: Transcripción** (Nueva funcionalidad implementada)
```
🗣️ Transcripción
 └── 🎵 Audios Listos para Transcribir  ← ¡AQUÍ ES DONDE TRABAJAS!
```

### 4. **URLs Directas**

| Funcionalidad | URL Directa |
|---------------|-------------|
| **🎵 Audios Listos** | `http://localhost:8000/transcripcion/audios-listos/` |
| **🔧 Configurar Audio** | `http://localhost:8000/transcripcion/configurar/{id}/` |
| **📋 Lista Transcripciones** | `http://localhost:8000/transcripcion/` |
| **🎯 Centro de Audio** | `http://localhost:8000/audio/centro-audio/` |

---

## 🎵 **Funcionalidad: "Audios Listos para Transcribir"**

### **¿Qué encuentras aquí?**

1. **📊 Panel de Estadísticas**
   - Número total de audios listos
   - Configuración activa actual

2. **🔍 Filtros Avanzados**
   - Búsqueda por nombre/título
   - Filtro por tipo de reunión
   - Filtro por rango de fechas

3. **📋 Lista de Audios**
   Cada audio muestra:
   - **Información básica**: nombre, título, tipo de reunión
   - **Metadatos técnicos**: duración, calidad, fecha de procesamiento
   - **Participantes**: número de participantes registrados
   - **Reproductor integrado**: para escuchar el audio
   - **Botones de acción**:
     - 🎤 **TRANSCRIBIR** ← Botón principal
     - ▶️ **ESCUCHAR** ← Reproductor
     - ℹ️ **DETALLE** ← Información completa

### **¿Cómo usar el botón "TRANSCRIBIR"?**

Al hacer clic en **🎤 TRANSCRIBIR** en cualquier audio:

1. **Se abre la página de configuración individual**
2. **Puedes personalizar parámetros**:
   - Modelo Whisper (tiny, base, small, medium, large, large-v3)
   - Temperatura de procesamiento
   - Configuración VAD (Voice Activity Detection)
   - Número de hablantes (mínimo/máximo)
   - Parámetros de diarización
   - Configuraciones de procesamiento
3. **Botón final**: **🎤 Transcribir Audio**

---

## 🚀 **Cómo empezar ahora**

### **Opción 1: Usuario con archivos existentes**
```
1. Ir a: 🗣️ Transcripción → 🎵 Audios Listos para Transcribir
2. Buscar tu audio procesado
3. Hacer clic en 🎤 TRANSCRIBIR
4. Configurar parámetros según necesidades
5. Presionar "Transcribir Audio"
```

### **Opción 2: Usuario nuevo sin archivos**
```
1. Ir a: 🎙️ Proceso de Audio → 🎯 Centro de Audio
2. Subir o grabar nuevo archivo
3. Esperar que se complete el procesamiento
4. Ir a: 🗣️ Transcripción → 🎵 Audios Listos para Transcribir
5. Encontrar tu archivo y transcribir
```

---

## 🔐 **Permisos y Acceso**

- **Login requerido**: Todas las funcionalidades requieren autenticación
- **Roles soportados**: Usuarios autenticados del sistema municipal
- **OAuth integrado**: Login con GitHub/Google disponible

---

## 📞 **Soporte**

Si no ves audios en "Audios Listos para Transcribir":

1. ✅ Verificar que tienes archivos en "Lista de Procesos" con estado "Completado"
2. ✅ Verificar que has iniciado sesión
3. ✅ Verificar que el audio se procesó correctamente

**Estado del sistema**: ✅ Funcional en `localhost:8000`
