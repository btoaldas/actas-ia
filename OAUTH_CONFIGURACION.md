# Configuración OAuth - GitHub y Google

## Estado Actual ✅

### Credenciales Configuradas
- **GitHub**: Client ID configurado, Client Secret configurado
- **Google**: Client ID configurado, Client Secret configurado
- **Site**: localhost:8000 (configurado para desarrollo local)

### URLs de Callback Registradas
- **GitHub**: `http://localhost:8000/accounts/github/login/callback/`
- **Google**: `http://localhost:8000/accounts/google/login/callback/`

### Configuración Django-Allauth
```python
# Configuración en config/settings.py
ACCOUNT_USERNAME_REQUIRED = False  # Permitir crear usuarios sin username
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Usar solo email
SOCIALACCOUNT_AUTO_SIGNUP = True  # Crear usuarios automáticamente
SOCIALACCOUNT_LOGIN_ON_GET = True  # Permitir login directo
SOCIALACCOUNT_QUERY_EMAIL = True  # Solicitar email siempre
```

### Adapter Personalizado
- **Ubicación**: `apps/config_system/adapters.py`
- **Función**: Resolver conflictos de SocialApp y garantizar login automático
- **Características**:
  - Creación automática de username a partir del email
  - Población automática de datos de perfil (nombre, email)
  - Logging de eventos OAuth

## URLs de Acceso

### Para Usuarios
- **Login Principal**: `http://localhost:8000/accounts/login/`
- **Login GitHub**: `http://localhost:8000/accounts/github/login/`
- **Login Google**: `http://localhost:8000/accounts/google/login/`

### Flujo de Autenticación
1. Usuario accede a `/accounts/github/login/` o `/accounts/google/login/`
2. Redirección automática al proveedor OAuth
3. Usuario autoriza la aplicación
4. Callback del proveedor a `/accounts/{provider}/login/callback/`
5. **RESULTADO ESPERADO**: Redirección automática a `/` (página principal)

## Configuración de Proveedores

### GitHub OAuth App
- **Homepage URL**: `http://localhost:8000/`
- **Authorization callback URL**: `http://localhost:8000/accounts/github/login/callback/`
- **Scopes solicitados**: `user:email`

### Google OAuth2 Client
- **Authorized JavaScript origins**: `http://localhost:8000`
- **Authorized redirect URIs**: `http://localhost:8000/accounts/google/login/callback/`
- **Scopes solicitados**: `profile`, `email`

## Resolución de Problemas

### Si aparece página de signup
**Problema**: El usuario es redirigido a `/accounts/social/signup/` en lugar de hacer login automático.

**Solución aplicada**:
- `ACCOUNT_USERNAME_REQUIRED = False`
- `SOCIALACCOUNT_AUTO_SIGNUP = True`
- Adapter personalizado que genera username automáticamente

### Si aparece error MultipleObjectsReturned
**Problema**: allauth no puede resolver qué SocialApp usar.

**Solución aplicada**:
- Adapter personalizado que selecciona la primera SocialApp por ID
- Eliminación de configuración 'APP' estática en SOCIALACCOUNT_PROVIDERS

## Para Producción

### Cambios necesarios:
1. **Dominio del Site**: Cambiar de `localhost:8000` a dominio real
2. **URLs de callback**: Actualizar en GitHub/Google Developer Console
3. **Verificación de email**: Cambiar `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'`
4. **HTTPS**: Configurar SSL y ajustar callback URLs
5. **Variables de entorno**: Asegurar que secrets no se commitean

### Comando de gestión para actualizar Site:
```bash
docker exec -it actas_web python manage.py shell -c "
from django.contrib.sites.models import Site
s = Site.objects.get(id=1)
s.domain = 'tu-dominio.com'
s.name = 'Tu Sitio'
s.save()
print(f'Site actualizado: {s.domain}')
"
```

### Comando para regenerar SocialApps:
```bash
docker exec -it actas_web python manage.py crear_social_apps_oauth
```

## Verificación del Estado

Para verificar que todo esté funcionando correctamente:

```bash
# Verificar SocialApps en BD
docker exec -it actas_web python manage.py shell -c "
from allauth.socialaccount.models import SocialApp
for app in SocialApp.objects.all():
    print(f'{app.provider}: {app.client_id} (sites: {[s.domain for s in app.sites.all()]})')
"

# Verificar Site actual
docker exec -it actas_web python manage.py shell -c "
from django.contrib.sites.models import Site
print('Site actual:', Site.objects.get_current())
"
```

---
*Configuración completada el 28 de septiembre de 2025*