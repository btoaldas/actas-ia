# 🔐 Guía de Configuración OAuth - Sistema de Actas Municipales

Esta guía te ayudará a configurar la autenticación OAuth con GitHub y Google para el Sistema de Actas Municipales del Municipio de Pastaza.

## 📋 Configuración de GitHub OAuth

### 1. Crear una GitHub App

1. Ve a [GitHub Developer Settings](https://github.com/settings/developers)
2. Click en "New OAuth App"
3. Completa la información:
   ```
   Application name: Sistema de Actas Municipales - Pastaza
   Homepage URL: http://localhost:8000 (desarrollo) / https://tu-dominio.com (producción)
   Authorization callback URL: http://localhost:8000/accounts/github/login/callback/
   ```
4. Click "Register application"
5. Copia el **Client ID** y **Client Secret**

### 2. Configurar en el Sistema

Edita el archivo `.env` y agrega:
```env
GITHUB_CLIENT_ID=tu_client_id_aqui
GITHUB_CLIENT_SECRET=tu_client_secret_aqui
```

### 3. Para Producción (Render)

En Render, agrega las siguientes variables de entorno:
```
GITHUB_CLIENT_ID=tu_client_id_aqui
GITHUB_CLIENT_SECRET=tu_client_secret_aqui
```

Y actualiza la callback URL a:
```
https://tu-app.onrender.com/accounts/github/login/callback/
```

## 🔑 Configuración de Google OAuth

### 1. Crear un Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Google+ API**

### 2. Configurar OAuth 2.0

1. Ve a "Credenciales" en el menú lateral
2. Click "Crear credenciales" > "ID de cliente de OAuth 2.0"
3. Selecciona "Aplicación web"
4. Configura:
   ```
   Nombre: Sistema de Actas Municipales Pastaza
   Orígenes de JavaScript autorizados:
   - http://localhost:8000 (desarrollo)
   - https://tu-dominio.com (producción)
   
   URI de redirección autorizados:
   - http://localhost:8000/accounts/google/login/callback/
   - https://tu-dominio.com/accounts/google/login/callback/
   ```
5. Copia el **Client ID** y **Client Secret**

### 3. Configurar en el Sistema

Edita el archivo `.env` y agrega:
```env
GOOGLE_CLIENT_ID=tu_client_id_aqui
GOOGLE_CLIENT_SECRET=tu_client_secret_aqui
```

## 🚀 Aplicar Configuración

### 1. Reiniciar el Sistema
```bash
# Parar el sistema
docker-compose -f docker-compose.simple.yml down

# Reiniciar
iniciar_sistema.bat
```

### 2. Configurar en Django Admin

1. Ve a http://localhost:8000/admin/
2. Accede con: `superadmin` / `AdminPuyo2025!`
3. Ve a "Sites" y edita el site con ID 1:
   ```
   Domain name: localhost:8000 (desarrollo) / tu-dominio.com (producción)
   Display name: Sistema de Actas Municipales - Pastaza
   ```

4. Ve a "Social applications" y agrega:

   **Para GitHub:**
   ```
   Provider: GitHub
   Name: GitHub - Municipio Pastaza
   Client id: [tu GitHub client ID]
   Secret key: [tu GitHub client secret]
   Sites: Selecciona tu site
   ```

   **Para Google:**
   ```
   Provider: Google
   Name: Google - Municipio Pastaza
   Client id: [tu Google client ID]
   Secret key: [tu Google client secret]
   Sites: Selecciona tu site
   ```

## 🔒 Configuración de Seguridad

### Variables de Entorno Completas

Tu archivo `.env` debe incluir:
```env
# OAuth GitHub
GITHUB_CLIENT_ID=tu_github_client_id
GITHUB_CLIENT_SECRET=tu_github_client_secret

# OAuth Google
GOOGLE_CLIENT_ID=tu_google_client_id
GOOGLE_CLIENT_SECRET=tu_google_client_secret

# Para Producción (Render)
RENDER_EXTERNAL_HOSTNAME=tu-app.onrender.com
```

### Configuración de Producción

Para un entorno de producción seguro:

1. **Dominios autorizados**: Solo incluye dominios oficiales del municipio
2. **HTTPS**: Asegúrate de usar HTTPS en producción
3. **Validación de email**: Cambia `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'`
4. **Dominios restringidos**: Considera limitar OAuth solo a emails @puyo.gob.ec

## 🧪 Probar OAuth

### 1. Acceder al Login
Ve a: http://localhost:8000/accounts/login/

### 2. Probar GitHub OAuth
1. Click en "Continuar con GitHub"
2. Autoriza la aplicación
3. Deberías ser redirigido al sistema logueado

### 3. Probar Google OAuth
1. Click en "Continuar con Google"
2. Selecciona o ingresa tu cuenta Google
3. Autoriza la aplicación
4. Deberías ser redirigido al sistema logueado

## 🛠️ Solución de Problemas

### Error: "Invalid client_id"
- Verifica que el CLIENT_ID esté correctamente configurado
- Asegúrate de que no hay espacios extra

### Error: "redirect_uri_mismatch"
- Verifica que la URL de callback coincida exactamente
- Para desarrollo: `http://localhost:8000/accounts/github/login/callback/`
- Para producción: `https://tu-dominio.com/accounts/github/login/callback/`

### Los botones OAuth no aparecen
- Verifica que las apps estén configuradas en Django Admin
- Asegúrate de que el site esté asociado a las aplicaciones sociales

## 📞 Soporte

Si tienes problemas con la configuración OAuth:
- **Email**: tecnico@puyo.gob.ec
- **Documentación**: Ver logs con `docker-compose -f docker-compose.simple.yml logs web`

---

**Municipio de Pastaza** - Sistema de Actas Municipales 🏛️
