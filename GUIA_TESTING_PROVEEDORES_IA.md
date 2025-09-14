# 🚀 GUÍA PASO A PASO: TESTING DEL SISTEMA DE PROVEEDORES DE IA

## 📋 PREPARACIÓN INICIAL

### 1. Configurar API Keys
- Editar el archivo `.env` con las API keys reales
- Reiniciar los contenedores Docker para aplicar cambios

### 2. Verificar Sistema
```bash
# Verificar que los contenedores estén ejecutándose
docker-compose -f docker-compose.simple.yml ps

# Verificar logs del servidor
docker logs --tail=20 actas_web
```

## 🧪 TESTING COMPLETO - PROVEEDOR OPENAI

### PASO 1: Acceder al Sistema
1. Abrir navegador en: `http://localhost:8000`
2. Iniciar sesión con:
   - Usuario: `superadmin`
   - Contraseña: `AdminPuyo2025!`

### PASO 2: Navegar a Proveedores de IA
1. En el menú lateral, ir a **"Generador de Actas"**
2. Expandir el submenú
3. Hacer clic en **"Proveedores de IA"**
4. Deberías ver la página con estadísticas y lista de proveedores

### PASO 3: Crear Proveedor OpenAI
1. Hacer clic en **"Crear Proveedor"**
2. Llenar el formulario:
   ```
   Nombre: OpenAI Producción
   Tipo: openai
   API Key: [TU_OPENAI_API_KEY_REAL]
   Modelo: gpt-4o-mini
   Temperatura: 0.7
   Max Tokens: 1000
   Prompt Sistema Global: "Eres un asistente especializado en actas municipales. Siempre responde en formato JSON válido."
   Activo: ✓ Marcado
   ```
3. Hacer clic en **"Crear Proveedor"**

### PASO 4: Verificar Creación
1. Deberías ser redirigido a la lista de proveedores
2. Verificar que aparezca "OpenAI Producción" en la lista
3. Verificar que tenga el badge "OpenAI" y estado "Activo"

### PASO 5: Probar Conexión
1. En la lista de proveedores, buscar "OpenAI Producción"
2. Hacer clic en el botón **"Probar"** (icono de flask)
3. Se abrirá un modal de prueba
4. En el campo de prompt, escribir:
   ```json
   Responde solo con JSON: {"mensaje": "Conexión exitosa", "proveedor": "OpenAI", "modelo": "gpt-4o-mini"}
   ```
5. Hacer clic en **"Probar Conexión"**
6. Verificar que la respuesta sea exitosa y en formato JSON

### PASO 6: Editar Proveedor
1. Hacer clic en **"Editar"** en el proveedor OpenAI
2. Cambiar la temperatura a `0.5`
3. Agregar en el prompt del sistema:
   ```
   Instrucciones adicionales: Mantén las respuestas concisas y precisas para documentos oficiales municipales.
   ```
4. Guardar cambios

### PASO 7: Testing Avanzado
1. Ir a **"Probar Proveedores"** (enlace en el menú)
2. Seleccionar el proveedor OpenAI recién creado
3. Probar con diferentes prompts:
   
   **Prueba 1: Formato JSON**
   ```
   Genera un resumen de acta en JSON con las siguientes claves: fecha, tipo_reunion, participantes, temas_principales, acuerdos
   ```
   
   **Prueba 2: Análisis de Texto**
   ```
   Analiza este texto de transcripción: "El alcalde mencionó la aprobación del presupuesto 2025..." y extrae los puntos clave en formato JSON
   ```

## 🔄 TESTING DE OTROS PROVEEDORES

### Para Claude (Anthropic):
```
Nombre: Claude Producción
Tipo: anthropic
API Key: [TU_ANTHROPIC_API_KEY]
Modelo: claude-3-5-sonnet-20241022
Temperatura: 0.5
Max Tokens: 2000
```

### Para Groq:
```
Nombre: Groq Rápido
Tipo: groq
API Key: [TU_GROQ_API_KEY]
Modelo: llama-3.1-70b-versatile
Temperatura: 0.3
Max Tokens: 1500
```

## ✅ VERIFICACIONES DE ÉXITO

### Funcionalidades que DEBEN funcionar:
1. ✅ **Creación de proveedores** - Sin errores de validación
2. ✅ **Listado dinámico** - Proveedores aparecen con badges correctos
3. ✅ **Cambio dinámico de campos** - Al seleccionar tipo, campos se adaptan
4. ✅ **Carga de modelos** - Dropdown se llena automáticamente
5. ✅ **Prueba de conexión** - Respuestas JSON válidas
6. ✅ **Edición** - Cambios se guardan correctamente
7. ✅ **Eliminación** - Con confirmación modal
8. ✅ **Filtros** - Por tipo y estado

### Indicadores de Funcionamiento:
- **Verde**: Conexiones exitosas
- **Rojo**: Errores de API o configuración
- **Amarillo**: Advertencias o timeouts

## 🐛 TROUBLESHOOTING

### Problemas Comunes:
1. **Error 401**: API Key incorrecta o expirada
2. **Error 429**: Límite de rate excedido
3. **Error 500**: Problema de configuración del servidor
4. **Timeout**: API externa no responde

### Soluciones:
1. Verificar que las API keys sean válidas y activas
2. Comprobar conectividad a internet
3. Revisar logs del contenedor: `docker logs actas_web`
4. Reiniciar servicios si es necesario

## 📊 MÉTRICAS ESPERADAS

Después de las pruebas, deberías ver:
- **Proveedores creados**: 1-3 proveedores activos
- **Pruebas realizadas**: 5-10 tests exitosos
- **Tokens consumidos**: Registro de uso
- **Tiempo de respuesta**: < 5 segundos por prueba

## 🎯 OBJETIVO FINAL

Al completar esta guía, tendrás:
1. ✅ Sistema de proveedores funcionando al 100%
2. ✅ Conexiones verificadas con APIs reales
3. ✅ Interface completamente funcional
4. ✅ Respuestas JSON validadas
5. ✅ Sistema listo para uso en producción