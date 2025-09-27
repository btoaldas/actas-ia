# 🚀 SCRIPTS LINUX COMPLETOS - ACTAS IA

## 📋 **SCRIPTS CREADOS PARA LINUX/MACOS**

### 🔧 **SCRIPTS PRINCIPALES**

#### **1. INSTALADOR_ACTAS_IA.sh** - **INSTALADOR COMPLETO**
- **Función:** Menú interactivo completo con 10 opciones
- **Características:**
  - ✅ Instalación completa (Primera vez)
  - ✅ Iniciar sistema existente  
  - ✅ Reparar sistema
  - ✅ Verificar estado
  - ✅ Crear backup
  - ✅ Restaurar backup
  - ✅ Detener sistema
  - ✅ Limpiar y reinstalar
  - ✅ **🆕 Aplicar solo schema de logs (reparación rápida)**
  - ✅ Salir

**Uso:**
```bash
chmod +x INSTALADOR_ACTAS_IA.sh
./INSTALADOR_ACTAS_IA.sh
```

**Mejoras Preventivas:**
- 🗄️ **Schema de logs automático** en instalación y reparación
- 🔍 **Verificación robusta** de servicios y dependencias
- 🎨 **Interfaz colorizada** para mejor experiencia
- ⚠️ **Manejo de errores** detallado con mensajes informativos

---

#### **2. iniciar_sistema.sh** - **INICIO MEJORADO**
- **Función:** Iniciar sistema con verificaciones automáticas
- **Características:**
  - 🐳 Verificación de Docker
  - 🔨 Construcción de imágenes
  - 📊 Inicio secuencial de servicios
  - 🗄️ **Auto-aplicación de schema de logs**
  - 🔍 **Verificación de schema crítico**
  - 📋 Información completa de acceso

**Uso:**
```bash
chmod +x iniciar_sistema.sh
./iniciar_sistema.sh
```

**Mejoras Clave:**
- **Detección automática** de schema de logs faltante
- **Aplicación automática** si no existe
- **Feedback visual** con colores y emojis

---

#### **3. detener_sistema.sh** - **DETENER LIMPIO**
- **Función:** Detener todos los servicios de forma ordenada
- **Características:**
  - 📊 Mostrar servicios activos antes de detener
  - 🛑 Detención ordenada de todos los servicios
  - 🧹 Limpieza de contenedores huérfanos
  - 📊 Estado final del sistema
  - 🔧 Comandos para reiniciar

**Uso:**
```bash
chmod +x detener_sistema.sh
./detener_sistema.sh
```

---

#### **4. reiniciar_sistema.sh** - **REINICIO INTELIGENTE**
- **Función:** Reinicio completo con verificaciones
- **Características:**
  - 🛑 Detención ordenada
  - 🧹 Limpieza de contenedores
  - 🔨 Reconstrucción de imágenes
  - 📊 Verificación de migraciones pendientes
  - 🗄️ **Verificación y aplicación de schema de logs**
  - 🔍 **Verificación final de todos los servicios**

**Uso:**
```bash
chmod +x reiniciar_sistema.sh
./reiniciar_sistema.sh
```

**Funciones Avanzadas:**
- Detección de migraciones pendientes
- Aplicación automática de schema de logs
- Verificación completa de servicios
- Diagnóstico de problemas

---

#### **5. verificar_estado.sh** - **DIAGNÓSTICO COMPLETO**
- **Función:** Verificación exhaustiva del sistema
- **Características:**
  - 🐳 Estado de Docker y versión
  - 📦 Estado detallado de contenedores
  - 🔧 Verificación de servicios específicos
  - 🗄️ **Verificación crítica de schema de logs**
  - 🌐 Conectividad HTTP de todos los endpoints
  - 💾 Estado de volúmenes y directorios
  - 📊 Estadísticas de rendimiento
  - 📋 Logs recientes de cada servicio
  - 🎯 **Resumen final con recomendaciones**

**Uso:**
```bash
chmod +x verificar_estado.sh
./verificar_estado.sh
```

**Verificaciones Incluidas:**
- PostgreSQL: Conectividad, versión, schemas
- Redis: Conectividad, versión
- Django: Estado, versión, migraciones
- Celery: Estado, tareas activas
- Schema de logs: Existencia y completitud
- HTTP: Endpoints principales
- Sistema: Volúmenes, directorios, rendimiento

---

## 🔄 **EQUIVALENCIAS LINUX ↔ WINDOWS**

| **Función**                    | **Linux/MacOS**              | **Windows**                 |
|--------------------------------|------------------------------|----------------------------|
| Instalador completo           | `INSTALADOR_ACTAS_IA.sh`     | `INSTALADOR_ACTAS_IA.bat`  |
| Iniciar sistema               | `iniciar_sistema.sh`         | `iniciar_sistema.bat`      |
| Detener sistema              | `detener_sistema.sh`         | `parar_sistema.bat`        |
| Reiniciar sistema            | `reiniciar_sistema.sh`       | *(Crear equivalente)*      |
| Verificar estado             | `verificar_estado.sh`        | *(Incluido en instalador)*|
| Aplicar solo schema logs     | *Instalador → Opción 9*      | *Instalador → Opción 9*    |

---

## 🎯 **FUNCIONES PREVENTIVAS IMPLEMENTADAS**

### **🔄 Instalación Completa**
```bash
# Secuencia mejorada:
1. Verificar Docker
2. Limpiar instalaciones anteriores
3. Construir imágenes
4. Iniciar servicios base
5. Aplicar migraciones Django
6. Crear usuarios iniciales
7. 🆕 Aplicar schema de logs automáticamente
8. Iniciar todos los servicios
9. Verificar funcionamiento
```

### **🚀 Inicio del Sistema**
```bash
# Verificación automática:
1. Construir imágenes
2. Iniciar servicios
3. 🆕 Verificar schema de logs existe
4. 🆕 Si no existe → aplicar automáticamente
5. Mostrar URLs y credenciales
```

### **🔧 Reparación Rápida**
```bash
# Opción 9 en instalador:
1. Verificar PostgreSQL disponible
2. Aplicar solo schema de logs
3. No tocar otros datos
4. Tiempo: <30 segundos
```

---

## 🌟 **CARACTERÍSTICAS AVANZADAS**

### **🎨 Interfaz Visual Mejorada**
- **Colores**: Verde (✅), Rojo (❌), Amarillo (⚠️), Azul (📊), Cian (🌐)
- **Emojis**: Categorización visual de acciones y estados
- **Mensajes**: Claros, informativos y accionables

### **🛡️ Manejo Robusto de Errores**
- **Verificaciones previas**: Docker, archivos, servicios
- **Mensajes específicos**: Qué falló y cómo solucionarlo
- **Continuidad**: El sistema continúa aunque algunos pasos fallen
- **Recuperación**: Sugerencias automáticas de reparación

### **📊 Feedback Detallado**
- **Progreso**: Cada paso se reporta claramente  
- **Estado**: Verificación en tiempo real
- **Diagnóstico**: Información técnica cuando es necesario
- **Recomendaciones**: Próximos pasos sugeridos

### **🔄 Compatibilidad Cruzada**
- **Misma funcionalidad** que versiones Windows
- **Comandos nativos** para Linux/MacOS (cat, grep, curl)
- **Detección automática** de entorno y herramientas

---

## 📋 **COMANDOS RÁPIDOS**

### **Primer Uso (Instalación Completa)**
```bash
chmod +x INSTALADOR_ACTAS_IA.sh
./INSTALADOR_ACTAS_IA.sh
# Seleccionar Opción 1
```

### **Uso Diario**
```bash
# Iniciar
./iniciar_sistema.sh

# Verificar estado
./verificar_estado.sh

# Detener
./detener_sistema.sh

# Reiniciar
./reiniciar_sistema.sh
```

### **Reparaciones**
```bash
# Reparación rápida (solo logs)
./INSTALADOR_ACTAS_IA.sh  # Opción 9

# Reparación completa
./INSTALADOR_ACTAS_IA.sh  # Opción 3

# Limpiar y reinstalar
./INSTALADOR_ACTAS_IA.sh  # Opción 8
```

---

## ✅ **BENEFICIOS DE LOS SCRIPTS LINUX**

### **🔄 Prevención Automática**
- ✅ **Schema de logs incluido** en instalación desde el inicio
- ✅ **Verificación automática** en cada inicio del sistema
- ✅ **Reparación transparente** sin intervención del usuario

### **🛠️ Opciones Flexibles**
- ✅ **Reparación rápida** sin reinstalar todo
- ✅ **Diagnóstico completo** del sistema
- ✅ **Backup y restauración** integrados

### **🎯 Experiencia de Usuario**
- ✅ **Una sola línea** para iniciar todo
- ✅ **Feedback visual** claro y comprensible
- ✅ **Manejo de errores** informativo y accionable
- ✅ **Compatibilidad** con distribuciones Linux y MacOS

### **🔧 Mantenimiento**  
- ✅ **Scripts modulares** fáciles de mantener
- ✅ **Funciones reutilizables** entre scripts
- ✅ **Logging y diagnóstico** integrados
- ✅ **Actualización fácil** de funcionalidades

---

## 🎉 **RESULTADO FINAL**

### **❌ Antes (Problemático en Linux)**
```
- Sin scripts equivalentes para Linux
- Instalación manual compleja
- Errores de schema no prevenidos
- Experiencia inconsistente multiplataforma
```

### **✅ Después (Sistema Robusto)**
```
- ✅ Paridad completa Windows ↔ Linux
- ✅ Scripts inteligentes con prevención automática  
- ✅ Experiencia fluida en cualquier plataforma
- ✅ Mantenimiento simplificado
- ✅ Diagnóstico avanzado integrado
```

---

**Fecha:** 27 de septiembre de 2025  
**Estado:** ✅ **SCRIPTS LINUX COMPLETOS**  
**Cobertura:** **5 scripts principales + funcionalidad completa**  
**Compatibilidad:** **Linux, MacOS, WSL**