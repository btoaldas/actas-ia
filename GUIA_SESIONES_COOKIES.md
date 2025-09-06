# 🔍 GUÍA COMPLETA: MANEJO DE SESIONES Y COOKIES EN DJANGO

## 📋 **CÓMO FUNCIONA EL SISTEMA DE SESIONES EN DJANGO**

### 1. **Configuración del Sistema**

El sistema de sesiones de Django está configurado en `config/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.sessions',  # ← Manejo de sesiones
    ...
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',  # ← Middleware de sesiones
    ...
]
```

### 2. **Almacenamiento de Sesiones**

En este proyecto, las sesiones se almacenan en **PostgreSQL** en la tabla `django_session`:

```sql
-- Estructura de la tabla django_session
CREATE TABLE django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMP WITH TIME ZONE NOT NULL
);
```

### 3. **Tipos de Datos Almacenados**

Las sesiones pueden contener:
- **ID del usuario autenticado** (`_auth_user_id`)
- **Backend de autenticación** (`_auth_user_backend`)
- **Hash de la sesión** (`_auth_user_hash`)
- **Datos personalizados** (cualquier cosa que agregues con `request.session['clave'] = valor`)
- **Tokens CSRF**
- **Configuraciones temporales**

## 🍪 **COOKIES Y SU RELACIÓN CON SESIONES**

### 1. **Cookie Principal: sessionid**

Django crea automáticamente una cookie llamada `sessionid` que contiene:
- La clave de la sesión (40 caracteres alfanuméricos)
- Se envía en cada request al servidor
- El servidor usa esta clave para buscar los datos en la tabla `django_session`

### 2. **Otras Cookies Importantes**

- **csrftoken**: Token de protección CSRF
- **messages**: Mensajes temporales de Django
- **cookies personalizadas**: Las que agregues manualmente

### 3. **Configuración de Seguridad**

```python
# En producción (settings.py)
SESSION_COOKIE_SECURE = True      # Solo HTTPS
CSRF_COOKIE_SECURE = True         # Solo HTTPS
SESSION_COOKIE_HTTPONLY = True    # No accesible desde JavaScript
SESSION_COOKIE_SAMESITE = 'Lax'   # Protección CSRF
```

## 🔍 **CÓMO VERIFICAR SESIONES Y COOKIES**

### 1. **En el Navegador Web**

#### **Opción A: DevTools del Navegador**
1. Presiona `F12` para abrir las herramientas de desarrollador
2. Ve a la pestaña **"Application"** (Chrome) o **"Storage"** (Firefox)
3. En el panel izquierdo, busca **"Cookies"**
4. Selecciona tu dominio (ej: `localhost:8000`)
5. Verás todas las cookies con sus valores

#### **Opción B: Pestaña Network**
1. Abre DevTools (`F12`)
2. Ve a **"Network"**
3. Haz cualquier request (navega a una página)
4. En los headers de la respuesta verás `Set-Cookie`
5. En los headers del request verás `Cookie`

### 2. **Usando las Herramientas de Debug del Sistema**

He creado herramientas especiales para este proyecto:

#### **Dashboard de Debug de Sesiones**
- **URL**: `http://localhost:8000/auditoria/debug/session/`
- **Funciones**:
  - Ver información completa de tu sesión actual
  - Ver todas las cookies del navegador
  - Probar modificaciones de sesión
  - Ver headers HTTP completos

#### **Vista de Todas las Sesiones Activas**
- **URL**: `http://localhost:8000/auditoria/debug/sessions/`
- **Funciones** (solo superusuarios):
  - Ver todas las sesiones activas en el servidor
  - Identificar usuarios autenticados vs anónimos
  - Ver tiempos de expiración
  - Monitorear sesiones en tiempo real

### 3. **Desde la Base de Datos**

```bash
# Conectar a PostgreSQL
docker-compose exec db_postgres psql -U admin_actas -d actas_municipales_pastaza

# Ver todas las sesiones
SELECT session_key, expire_date, 
       CASE WHEN expire_date > NOW() THEN 'Activa' ELSE 'Expirada' END as estado
FROM django_session;

# Ver datos decodificados de una sesión específica
SELECT session_data FROM django_session WHERE session_key = 'tu_session_key_aqui';
```

### 4. **Desde el Shell de Django**

```bash
# Entrar al shell
docker-compose exec web python manage.py shell

# Código Python para analizar sesiones
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone

# Ver todas las sesiones activas
active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
for session in active_sessions:
    data = session.get_decoded()
    user_id = data.get('_auth_user_id')
    if user_id:
        user = User.objects.get(id=user_id)
        print(f"Sesión: {session.session_key[:8]}... Usuario: {user.username}")
    else:
        print(f"Sesión: {session.session_key[:8]}... Usuario: Anónimo")
```

## 🧪 **PRUEBAS PRÁCTICAS**

### 1. **Probar Modificación de Sesiones**

En la URL `http://localhost:8000/auditoria/debug/session/`:

1. **Agregar datos de prueba**: Agrega datos temporales a tu sesión
2. **Limpiar datos**: Elimina solo los datos de prueba
3. **Limpiar sesión completa**: Elimina toda la sesión (te deslogueará)

### 2. **Probar Cookies**

1. **Ver cookies actuales**: En el debug dashboard
2. **Establecer cookie de prueba**: Usa el botón "Probar Cookies"
3. **Verificar en DevTools**: Ve si la nueva cookie aparece

### 3. **Simular Múltiples Usuarios**

1. Abre el navegador principal y loguéate como `admin`
2. Abre una ventana de incógnito y navega sin loguearte
3. Ve a `http://localhost:8000/auditoria/debug/sessions/` como admin
4. Verás ambas sesiones: una autenticada y una anónima

## ⚠️ **CONSIDERACIONES DE SEGURIDAD**

### 1. **En Desarrollo**
- Las cookies pueden ser inseguras (`SECURE=False`)
- Puedes usar HTTP en lugar de HTTPS
- Debug activado

### 2. **En Producción**
- Todas las cookies deben ser seguras (`SECURE=True`)
- Solo HTTPS permitido
- Sessions con tiempos de expiración cortos
- Limpieza automática de sesiones expiradas

### 3. **Mejores Prácticas**
- No almacenar datos sensibles en sesiones
- Regenerar session key después del login
- Limpiar sesiones al logout
- Monitorear sesiones activas regularmente

## 📊 **MONITOREO CONTINUO**

El sistema de auditoría integrado registra automáticamente:
- **Inicios de sesión** en `logs.acceso_usuarios`
- **Navegación por páginas** en `logs.navegacion_usuarios`
- **Cambios en datos** en `auditoria.cambios_bd`
- **Errores del sistema** en `logs.errores_sistema`

Esto te permite tener un control completo sobre la actividad de usuarios y sesiones en el sistema.

---

## 🚀 **URLs PARA TESTING INMEDIATO**

1. **Debug de tu sesión**: `http://localhost:8000/auditoria/debug/session/`
2. **Todas las sesiones**: `http://localhost:8000/auditoria/debug/sessions/`
3. **API de cookies**: `http://localhost:8000/auditoria/debug/cookies/`
4. **Login**: `http://localhost:8000/accounts/login/`
5. **Dashboard principal**: `http://localhost:8000/auditoria/`
