# 🚀 Scripts de Gestión del Sistema - Actas IA

Este directorio contiene scripts mejorados para la gestión completa del sistema de Actas Municipales de Pastaza.

## 📋 Scripts Disponibles

### 🔧 Scripts Principales

| Script | Descripción | Cuándo usar |
|--------|-------------|-------------|
| `iniciar_sistema_mejorado.bat` | **Script principal mejorado** - Inicia todo el sistema paso a paso | Uso diario normal |
| `parar_sistema_mejorado.bat` | **Detiene el sistema** - Limpia contenedores y libera recursos | Para detener el sistema |
| `diagnosticar_sistema.bat` | **Diagnóstico completo** - Verifica estado y problemas | Cuando hay errores |
| `reparar_sistema_completo.bat` | **Reparación automática** - Limpia y reconstruye todo | Cuando nada funciona |

### 🔄 Scripts Legacy (Original)

| Script | Estado | Nota |
|--------|--------|------|
| `iniciar_sistema.bat` | ⚠️ Problemas | Usar la versión mejorada |
| `parar_sistema.bat` | ⚠️ Básico | Usar la versión mejorada |

## 🎯 Uso Recomendado

### ✅ Inicio Normal (Primera vez o uso diario)
```bash
# Ejecuta el script mejorado
.\iniciar_sistema_mejorado.bat
```

### 🔍 Si hay problemas (Diagnóstico)
```bash  
# 1. Primero diagnóstica el problema
.\diagnosticar_sistema.bat

# 2. Si es un problema menor, intenta iniciar normalmente
.\iniciar_sistema_mejorado.bat

# 3. Si persisten los problemas, repara el sistema completo
.\reparar_sistema_completo.bat
```

### 🛠️ Problemas Graves (Reparación completa)
```bash
# Este script limpia TODO y reconstruye desde cero
.\reparar_sistema_completo.bat
```

### ⏹️ Detener el sistema
```bash
# Para detener correctamente todos los servicios
.\parar_sistema_mejorado.bat
```

## 🚨 Solución de Problemas Comunes

### Problema 1: "Docker no está ejecutándose"
**Solución:**
1. Abrir Docker Desktop
2. Esperar que aparezca el ícono verde en la barra de tareas
3. Ejecutar `.\diagnosticar_sistema.bat`
4. Ejecutar `.\iniciar_sistema_mejorado.bat`

### Problema 2: "Error al construir imágenes"  
**Solución:**
1. Verificar conexión a internet
2. Ejecutar `.\reparar_sistema_completo.bat`
3. Si persiste, eliminar imágenes: `docker rmi -f $(docker images -q)`

### Problema 3: "Puerto está siendo utilizado"
**Solución:**
1. Ejecutar `.\diagnosticar_sistema.bat` para ver qué puertos
2. Detener otros servicios en los puertos 8000, 5432, 6379
3. O ejecutar `.\reparar_sistema_completo.bat`

### Problema 4: "Error en migraciones de base de datos"
**Solución:**
1. Ejecutar `.\reparar_sistema_completo.bat` (recrea la BD)
2. Si persiste, eliminar volúmenes: `docker volume prune -f`

### Problema 5: "La aplicación no responde en localhost:8000"
**Solución:**
1. Esperar 2-3 minutos (los contenedores tardan en iniciar)
2. Verificar logs: `docker-compose logs web`
3. Si hay errores, ejecutar `.\reparar_sistema_completo.bat`

## 📊 Verificaciones Post-Inicio

Después de ejecutar cualquier script, verifica que todo funciona:

### ✅ URLs que deben responder:
- **Principal**: http://localhost:8000 
- **Admin**: http://localhost:8000/admin/
- **OAuth**: http://localhost:8000/accounts/login/
- **Flower**: http://localhost:5555

### ✅ Comandos de verificación:
```bash
# Estado de contenedores
docker-compose ps

# Logs si hay problemas
docker-compose logs web
docker-compose logs db_postgres
docker-compose logs celery_worker

# Test de conectividad
curl -I http://localhost:8000
```

## 🎛️ Comandos Útiles Adicionales

### Reiniciar un servicio específico:
```bash
docker-compose restart web
docker-compose restart celery_worker
```

### Ver logs en tiempo real:
```bash
docker-compose logs -f web
```

### Ejecutar comandos Django:
```bash
docker-compose exec web python manage.py [comando]
```

### Entrar al contenedor web:
```bash
docker-compose exec web bash
```

## 📧 Soporte

Si los scripts no resuelven el problema:

1. **Recopila información**:
   - Output del `diagnosticar_sistema.bat`
   - Logs: `docker-compose logs > logs_error.txt`
   - Screenshot de errores

2. **Contacta soporte técnico**:
   - Email: tecnico@puyo.gob.ec
   - Incluye: logs, screenshots, descripción del problema

## 🔄 Actualización de Scripts

Para mantener los scripts actualizados:

1. Los scripts se versionar con el proyecto
2. Antes de usar, verifica si hay versiones nuevas en el repositorio
3. Los scripts son compatibles con Windows 10/11 y Docker Desktop

---

**Municipio de Pastaza - Sistema de Actas Municipales**  
*Generado automáticamente - Fecha: 25 de septiembre de 2025*