# 🚀 Guía de Instalación Completa - Sistema de Actas Municipales

## Instalación desde cero en Ubuntu Linux

Esta guía te llevará paso a paso para instalar el **Sistema de Actas Municipales de Pastaza** en un servidor Ubuntu completamente limpio.

---

## 📋 Requisitos Previos

- Ubuntu 20.04 LTS o superior
- Usuario con permisos sudo
- Conexión a internet estable
- Al menos 4GB de RAM y 20GB de espacio libre

---

## 🔧 Paso 1: Actualizar el Sistema

```bash
# Actualizar lista de paquetes
sudo apt update && sudo apt upgrade -y

# Instalar herramientas básicas
sudo apt install -y curl wget git vim htop unzip software-properties-common
```

---

## 🐳 Paso 2: Instalar Docker y Docker Compose

### Instalar Docker Engine

```bash
# Instalar dependencias
sudo apt install -y apt-transport-https ca-certificates gnupg lsb-release

# Agregar clave GPG oficial de Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Agregar repositorio Docker
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Actualizar e instalar Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Agregar usuario actual al grupo docker
sudo usermod -aG docker $USER

# Aplicar cambios de grupo (o reiniciar sesión)
newgrp docker

# Verificar instalación
docker --version
```

### Instalar Docker Compose

```bash
# Descargar Docker Compose (versión más reciente)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permisos de ejecución
sudo chmod +x /usr/local/bin/docker-compose

# Crear enlace simbólico (opcional)
sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verificar instalación
docker-compose --version
```

---

## 📂 Paso 3: Clonar el Repositorio

```bash
# Clonar repositorio
git clone https://github.com/btoaldas/actas-ia.git

# Entrar al directorio
cd actas-ia

# Verificar que estás en la rama main
git branch
```

---

## ⚙️ Paso 4: Configurar Variables de Entorno

### Crear archivo de configuración

```bash
# Copiar template de configuración
cp env.sample .env

# Editar archivo de configuración
nano .env
```

### Configuración mínima requerida (editar en nano):

```bash
# ===========================================
# CONFIGURACIÓN BÁSICA REQUERIDA
# ===========================================

# Configuración general
DEBUG=False
SECRET_KEY=actas_municipales_pastaza_2025_clave_secreta_super_segura_CAMBIAR_EN_PRODUCCION

# Configuración de Base de Datos PostgreSQL
DB_ENGINE=postgresql
DB_HOST=db_postgres
DB_NAME=actas_municipales_pastaza
DB_USERNAME=admin_actas
DB_PASS=actas_pastaza_2025_CAMBIAR_EN_PRODUCCION
DB_PORT=5432

# Configuración de Redis para Celery
REDIS_URL=redis://redis:6379/0

# Configuración OAuth GitHub (OPCIONAL - Ver paso 8)
GITHUB_CLIENT_ID=tu_github_client_id_aqui
GITHUB_CLIENT_SECRET=tu_github_client_secret_aqui

# Configuración OAuth Google (OPCIONAL - Ver paso 8)
GOOGLE_CLIENT_ID=tu_google_client_id_aqui
GOOGLE_CLIENT_SECRET=tu_google_client_secret_aqui

# Configuración SMTP para correos (OPCIONAL)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_password_de_aplicacion

# Configuración para producción
MUNICIPIO_DOMAIN=tu-dominio.com
MUNICIPIO_NAME=Municipio de Pastaza

# Configuración para Transcripción con IA (OPCIONAL)
HUGGINGFACE_TOKEN=tu_token_huggingface_aqui
OPENAI_API_KEY=tu_openai_api_key_aqui
```

**💡 Importante**: Cambiar todas las contraseñas y claves secretas por valores seguros en producción.

---

## 🐳 Paso 5: Construir y Levantar los Contenedores

```bash
# Construir imágenes Docker
docker-compose build

# Levantar todos los servicios en segundo plano
docker-compose up -d

# Verificar que todos los contenedores estén corriendo
docker-compose ps
```

**Servicios que deberían estar ejecutándose**:
- `actas_web` - Aplicación Django
- `actas_postgres` - Base de datos PostgreSQL
- `actas_redis` - Cache y broker de Celery
- `actas_celery_worker` - Procesador de tareas
- `actas_celery_beat` - Programador de tareas
- `actas_flower` - Monitor de Celery
- `actas_nginx` - Servidor web (proxy inverso)

---

## 🗄️ Paso 6: Configurar la Base de Datos

```bash
# Esperar a que PostgreSQL esté listo (puede tomar 1-2 minutos)
sleep 120

# Ejecutar migraciones de Django
docker exec -it actas_web python manage.py migrate

# Crear usuarios iniciales del sistema
docker exec -it actas_web python manage.py crear_usuarios_iniciales

# Configurar permisos del sistema
docker exec -it actas_web python manage.py init_permissions_system

# (OPCIONAL) Poblar con datos de demostración
docker exec -it actas_web python manage.py loaddata fixtures/demo_data.json
```

---

## 🔐 Paso 7: Configurar OAuth (OPCIONAL pero Recomendado)

### Si quieres habilitar login con GitHub y Google:

```bash
# Configurar aplicaciones OAuth automáticamente
docker exec -it actas_web python manage.py crear_social_apps_oauth
```

### Para obtener credenciales OAuth:

#### **GitHub OAuth App**:
1. Ve a [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Completa:
   - **Application name**: `Sistema Actas Municipales`
   - **Homepage URL**: `http://tu-dominio.com` (o `http://localhost:8000` para desarrollo)
   - **Authorization callback URL**: `http://tu-dominio.com/accounts/github/login/callback/`
4. Copia el `Client ID` y genera un `Client Secret`
5. Actualiza las variables en `.env`

#### **Google OAuth2 Client**:
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la API "Google+ API"
4. Ve a "Credentials" → "Create Credentials" → "OAuth client ID"
5. Configura:
   - **Application type**: Web application
   - **Authorized JavaScript origins**: `http://tu-dominio.com`
   - **Authorized redirect URIs**: `http://tu-dominio.com/accounts/google/login/callback/`
6. Descarga el JSON y extrae `client_id` y `client_secret`
7. Actualiza las variables en `.env`

---

## 🌐 Paso 8: Configurar Nginx y Dominio

### Para producción con dominio real:

```bash
# Editar configuración de Nginx
docker exec -it actas_nginx nano /etc/nginx/conf.d/default.conf
```

**Configuración básica de Nginx**:
```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://actas_web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /app/media/;
        expires 30d;
    }
}
```

### Configurar HTTPS con Let's Encrypt (Recomendado para producción):

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Configurar renovación automática
sudo crontab -e
# Agregar línea: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 🔧 Paso 9: Configuraciones Adicionales

### Configurar firewall (UFW):

```bash
# Habilitar UFW
sudo ufw enable

# Permitir SSH
sudo ufw allow ssh

# Permitir HTTP y HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Verificar reglas
sudo ufw status
```

### Configurar logrotate para logs de Docker:

```bash
# Crear archivo de configuración
sudo nano /etc/logrotate.d/docker-containers

# Contenido del archivo:
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

---

## 🚀 Paso 10: Verificar Instalación

### Verificar servicios:

```bash
# Ver logs de la aplicación
docker logs --tail=50 actas_web

# Ver estado de todos los contenedores
docker-compose ps

# Verificar conectividad de la base de datos
docker exec -it actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "SELECT version();"
```

### Acceder al sistema:

1. **Aplicación principal**: `http://tu-dominio.com` (o `http://localhost:8000`)
2. **Panel administrativo**: `http://tu-dominio.com/admin/`
3. **Monitor de Celery (Flower)**: `http://tu-dominio.com:5555`

### Credenciales por defecto:

```
👤 Super Administrador:
   Usuario: superadmin
   Clave: AdminPuyo2025!

👤 Alcalde:
   Usuario: alcalde.pastaza
   Clave: AlcaldePuyo2025!
```

**⚠️ IMPORTANTE**: Cambiar estas contraseñas inmediatamente en producción.

---

## 📊 Paso 11: Monitoreo y Mantenimiento

### Scripts útiles para mantenimiento:

```bash
# Crear script de backup
nano backup_sistema.sh
```

**Contenido del script de backup**:
```bash
#!/bin/bash
BACKUP_DIR="/backups/actas-$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup de base de datos
docker exec actas_postgres pg_dump -U admin_actas -d actas_municipales_pastaza > $BACKUP_DIR/database.sql

# Backup de archivos media
docker cp actas_web:/app/media $BACKUP_DIR/media

# Comprimir backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completado: $BACKUP_DIR.tar.gz"
```

```bash
# Dar permisos de ejecución
chmod +x backup_sistema.sh

# Programar backup diario
crontab -e
# Agregar: 0 2 * * * /home/tu-usuario/actas-ia/backup_sistema.sh
```

### Comandos útiles de mantenimiento:

```bash
# Reiniciar todos los servicios
docker-compose restart

# Ver logs en tiempo real
docker-compose logs -f

# Actualizar el código
git pull origin main
docker-compose build
docker-compose up -d

# Limpiar contenedores no utilizados
docker system prune -f

# Ver uso de recursos
docker stats
```

---

## 🔍 Resolución de Problemas Comunes

### Problema: Contenedores no inician
```bash
# Verificar logs específicos
docker logs actas_web
docker logs actas_postgres

# Verificar espacio en disco
df -h

# Verificar memoria
free -h
```

### Problema: Error de conexión a la base de datos
```bash
# Verificar que PostgreSQL esté corriendo
docker exec -it actas_postgres psql -U admin_actas -l

# Recrear base de datos si es necesario
docker exec -it actas_postgres psql -U admin_actas -c "DROP DATABASE IF EXISTS actas_municipales_pastaza;"
docker exec -it actas_postgres psql -U admin_actas -c "CREATE DATABASE actas_municipales_pastaza;"
docker exec -it actas_web python manage.py migrate
```

### Problema: Permisos de archivos
```bash
# Corregir permisos de archivos media
docker exec -it actas_web chown -R www-data:www-data /app/media
docker exec -it actas_web chmod -R 755 /app/media
```

---

## 📚 Recursos Adicionales

- **Documentación completa**: Ver `OAUTH_CONFIGURACION.md` en el repositorio
- **API Documentation**: `http://tu-dominio.com/api/docs/`
- **Logs del sistema**: `docker logs --tail=100 actas_web`
- **Monitor Celery**: `http://tu-dominio.com:5555`

---

## 📞 Soporte

Para soporte técnico o reportar problemas:

1. **Revisar logs**: `docker logs --tail=100 actas_web`
2. **Crear issue en GitHub**: [https://github.com/btoaldas/actas-ia/issues](https://github.com/btoaldas/actas-ia/issues)
3. **Verificar documentación**: Revisar archivos `.md` en el repositorio

---

## 🎉 ¡Instalación Completada!

Si has seguido todos los pasos correctamente, tu **Sistema de Actas Municipales** debería estar funcionando perfectamente en Ubuntu.

**Próximos pasos recomendados**:
1. ✅ Cambiar todas las contraseñas por defecto
2. ✅ Configurar backup automático
3. ✅ Configurar SSL con Let's Encrypt
4. ✅ Configurar OAuth para login social
5. ✅ Crear usuarios adicionales según sea necesario

**¡El sistema está listo para ser utilizado por tu municipio!** 🏛️✨