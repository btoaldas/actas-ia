# 🚀 Guía de Instalación Completa - Rocky Linux 9 (Como Root)

## Instalación desde cero en Rocky Linux 9 con Nginx Proxy

Esta guía te llevará paso a paso para instalar el **Sistema de Actas Municipales de Pastaza** en Rocky Linux 9 desde cero, trabajando como **root** con un proxy Nginx externo.

---

## 📋 Arquitectura del Sistema

```
Internet → Nginx (Host) → Docker Containers
                ↓
         actas_web:8000 (Django)
         actas_postgres:5432
         actas_redis:6379
         actas_flower:5555
```

---

## 🔧 Paso 1: Preparar el Sistema Rocky Linux 9

```bash
# Conectarse como root
su -
# o
sudo -i

# Actualizar el sistema completamente
dnf update -y

# Instalar herramientas básicas
dnf install -y curl wget git vim htop unzip tar gzip firewalld epel-release

# Habilitar EPEL (Extra Packages for Enterprise Linux)
dnf install -y epel-release
dnf update -y
```

---

## 🔥 Paso 2: Configurar Firewall

```bash
# Iniciar y habilitar firewalld
systemctl start firewalld
systemctl enable firewalld

# Permitir servicios básicos
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https

# Permitir puertos específicos (si necesario)
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp

# Recargar configuración
firewall-cmd --reload

# Verificar reglas activas
firewall-cmd --list-all
```

---

## 🌐 Paso 3: Instalar y Configurar Nginx (Host)

```bash
# Instalar Nginx
dnf install -y nginx

# Iniciar y habilitar Nginx
systemctl start nginx
systemctl enable nginx

# Verificar que Nginx esté corriendo
systemctl status nginx

# Crear backup de configuración original
cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
```

### Configurar Nginx como Proxy Reverso

```bash
# Crear configuración del sitio
cat > /etc/nginx/conf.d/actas-municipales.conf << 'EOF'
# Configuración Nginx para Sistema de Actas Municipales
# Proxy reverso hacia contenedores Docker

upstream actas_backend {
    server 127.0.0.1:8000;
}

upstream actas_flower {
    server 127.0.0.1:5555;
}

# Configuración principal del sitio
server {
    listen 80;
    server_name _;  # Cambiar por tu dominio real: servidor.municipio.gov.ec
    
    # Configuración de seguridad básica
    server_tokens off;
    client_max_body_size 100M;
    
    # Logs
    access_log /var/log/nginx/actas_access.log;
    error_log /var/log/nginx/actas_error.log;
    
    # Proxy hacia aplicación Django principal
    location / {
        proxy_pass http://actas_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Archivos estáticos (servirlos directamente desde Nginx si se montan)
    location /static/ {
        alias /opt/actas-ia/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Archivos media (uploads, audio, etc.)
    location /media/ {
        alias /opt/actas-ia/media/;
        expires 30d;
        add_header Cache-Control "public";
        access_log off;
    }
    
    # Monitor Celery (Flower) - OPCIONAL, comentar si no se usa
    location /flower/ {
        proxy_pass http://actas_flower/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Seguridad adicional
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Bloquear acceso a archivos sensibles
    location ~* \.(sql|bak|backup|log)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Verificar sintaxis de Nginx
nginx -t

# Si no hay errores, recargar configuración
systemctl reload nginx
```

---

## 🐳 Paso 4: Instalar Docker y Docker Compose

```bash
# Remover versiones antiguas de Docker (si existen)
dnf remove -y docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine podman runc

# Instalar dependencias
dnf install -y yum-utils device-mapper-persistent-data lvm2

# Agregar repositorio oficial de Docker
dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Instalar Docker
dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Iniciar y habilitar Docker
systemctl start docker
systemctl enable docker

# Verificar instalación
docker --version
docker compose version

# Verificar que Docker funciona
docker run hello-world
```

### Instalar Docker Compose (método alternativo si no funciona el plugin)

```bash
# Si docker compose no funciona, instalar versión standalone
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Dar permisos de ejecución
chmod +x /usr/local/bin/docker-compose

# Crear enlace simbólico
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verificar
docker-compose --version
```

---

## 📂 Paso 5: Clonar y Configurar el Proyecto

```bash
# Crear directorio para aplicaciones
mkdir -p /opt
cd /opt

# Clonar el repositorio desde GitHub
git clone https://github.com/btoaldas/actas-ia.git

# Entrar al directorio
cd actas-ia

# Verificar que el código se clonó correctamente
ls -la

# Verificar archivos Docker
ls -la docker-compose*
```

---

## ⚙️ Paso 6: Configurar Variables de Entorno

```bash
# Copiar template de configuración
cp env.sample .env

# Editar configuración con vim
vim .env
```

### Configuración para Rocky Linux 9 (editar en vim):

```bash
# ===========================================
# CONFIGURACIÓN PARA ROCKY LINUX 9 - ROOT
# ===========================================

# Configuración general
DEBUG=False
SECRET_KEY=actas_municipales_pastaza_rocky_2025_CAMBIAR_EN_PRODUCCION_$(openssl rand -hex 32)

# Configuración de Base de Datos PostgreSQL
DB_ENGINE=postgresql
DB_HOST=actas_postgres
DB_NAME=actas_municipales_pastaza
DB_USERNAME=admin_actas
DB_PASS=RockyLinux_Actas_2025_CAMBIAR_PRODUCCION
DB_PORT=5432

# Configuración de Redis para Celery
REDIS_URL=redis://actas_redis:6379/0

# Configuración de aplicación
ALLOWED_HOSTS=localhost,127.0.0.1,tu-servidor.com
CSRF_TRUSTED_ORIGINS=http://localhost,https://tu-servidor.com

# Configuración OAuth (OPCIONAL - completar después)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Configuración SMTP (OPCIONAL)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Configuración para producción
MUNICIPIO_DOMAIN=tu-servidor.com
MUNICIPIO_NAME=Municipio de Pastaza - Rocky Linux

# Configuración para Transcripción con IA (OPCIONAL)
HUGGINGFACE_TOKEN=
OPENAI_API_KEY=
```

**Para salir de vim**: Presiona `Esc`, luego escribe `:wq` y presiona `Enter`

---

## 🐳 Paso 7: Configurar Docker Compose

```bash
# Verificar que el archivo docker-compose.yml existe
cat docker-compose.yml

# Si necesitas usar una versión específica (simple)
ls -la docker-compose*.yml

# Verificar configuración
docker compose config

# Si hay errores de sintaxis, revisarlos antes de continuar
```

---

## 🚀 Paso 8: Construir y Levantar los Contenedores

```bash
# Construir todas las imágenes
docker compose build --no-cache

# Levantar todos los servicios en segundo plano
docker compose up -d

# Verificar que todos los contenedores estén corriendo
docker compose ps

# Ver logs en tiempo real (opcional)
docker compose logs -f

# Verificar logs específicos si hay problemas
docker compose logs actas_web
docker compose logs actas_postgres
```

### Servicios que deberían estar corriendo:
- `actas_web` - Aplicación Django (puerto 8000)
- `actas_postgres` - Base de datos PostgreSQL (puerto 5432)
- `actas_redis` - Cache y broker (puerto 6379)
- `actas_celery_worker` - Procesador de tareas
- `actas_celery_beat` - Programador de tareas  
- `actas_flower` - Monitor Celery (puerto 5555)

---

## 🗄️ Paso 9: Configurar la Base de Datos

```bash
# Esperar a que PostgreSQL esté completamente listo
echo "Esperando que PostgreSQL esté listo..."
sleep 60

# Verificar conectividad a PostgreSQL
docker compose exec actas_postgres pg_isready -U admin_actas

# Ejecutar migraciones de Django
docker compose exec actas_web python manage.py migrate

# Crear usuarios iniciales del sistema
docker compose exec actas_web python manage.py crear_usuarios_iniciales

# Configurar permisos del sistema
docker compose exec actas_web python manage.py init_permissions_system

# Recopilar archivos estáticos
docker compose exec actas_web python manage.py collectstatic --noinput

# (OPCIONAL) Cargar datos de demostración
# docker compose exec actas_web python manage.py loaddata fixtures/demo_data.json
```

---

## 🔍 Paso 10: Verificar Instalación

```bash
# Verificar que todos los servicios estén corriendo
docker compose ps

# Verificar logs de la aplicación
docker compose logs --tail=50 actas_web

# Verificar conectividad a la base de datos
docker compose exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "SELECT version();"

# Probar conexión HTTP local
curl -I http://localhost:8000

# Verificar Nginx
systemctl status nginx
curl -I http://localhost
```

### URLs de Acceso:

1. **Aplicación principal**: `http://tu-servidor.com` (o IP del servidor)
2. **Panel administrativo**: `http://tu-servidor.com/admin/`
3. **Monitor de Celery**: `http://tu-servidor.com/flower/` (si está habilitado)

### Credenciales por defecto:

```
👤 Super Administrador:
   Usuario: superadmin
   Clave: AdminPuyo2025!

👤 Alcalde:
   Usuario: alcalde.pastaza
   Clave: AlcaldePuyo2025!
```

---

## 🔧 Paso 11: Scripts de Mantenimiento

### Crear script de inicio/parada del sistema

```bash
# Crear script de control del sistema
cat > /opt/actas-ia/control_sistema.sh << 'EOF'
#!/bin/bash

# Script de control del Sistema de Actas Municipales
# Uso: ./control_sistema.sh [start|stop|restart|status|logs]

DOCKER_COMPOSE_FILE="/opt/actas-ia/docker-compose.yml"

case "$1" in
    start)
        echo "🚀 Iniciando Sistema de Actas Municipales..."
        cd /opt/actas-ia
        docker compose up -d
        echo "✅ Sistema iniciado"
        ;;
    stop)
        echo "🛑 Deteniendo Sistema de Actas Municipales..."
        cd /opt/actas-ia
        docker compose down
        echo "✅ Sistema detenido"
        ;;
    restart)
        echo "🔄 Reiniciando Sistema de Actas Municipales..."
        cd /opt/actas-ia
        docker compose down
        sleep 5
        docker compose up -d
        echo "✅ Sistema reiniciado"
        ;;
    status)
        echo "📊 Estado del Sistema de Actas Municipales:"
        cd /opt/actas-ia
        docker compose ps
        ;;
    logs)
        echo "📋 Logs del Sistema:"
        cd /opt/actas-ia
        docker compose logs --tail=100 -f
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF

# Dar permisos de ejecución
chmod +x /opt/actas-ia/control_sistema.sh

# Crear enlace simbólico para uso global
ln -sf /opt/actas-ia/control_sistema.sh /usr/local/bin/actas-control
```

### Crear script de backup

```bash
cat > /opt/actas-ia/backup_sistema.sh << 'EOF'
#!/bin/bash

# Script de backup del Sistema de Actas Municipales
BACKUP_DIR="/opt/backups/actas-$(date +%Y%m%d_%H%M%S)"
mkdir -p /opt/backups

echo "🗄️  Iniciando backup del sistema..."

# Crear directorio de backup
mkdir -p $BACKUP_DIR

# Backup de base de datos
echo "📊 Backing up database..."
docker compose exec -T actas_postgres pg_dump -U admin_actas -d actas_municipales_pastaza > $BACKUP_DIR/database.sql

# Backup de archivos media
echo "📁 Backing up media files..."
docker cp $(docker compose ps -q actas_web):/app/media $BACKUP_DIR/media

# Backup de configuración
echo "⚙️  Backing up configuration..."
cp /opt/actas-ia/.env $BACKUP_DIR/env_backup
cp -r /opt/actas-ia/config $BACKUP_DIR/config_backup 2>/dev/null || true

# Comprimir backup
echo "🗜️  Compressing backup..."
tar -czf $BACKUP_DIR.tar.gz -C $(dirname $BACKUP_DIR) $(basename $BACKUP_DIR)
rm -rf $BACKUP_DIR

echo "✅ Backup completado: $BACKUP_DIR.tar.gz"
ls -lh $BACKUP_DIR.tar.gz
EOF

chmod +x /opt/actas-ia/backup_sistema.sh
ln -sf /opt/actas-ia/backup_sistema.sh /usr/local/bin/actas-backup
```

---

## 🔄 Paso 12: Configurar Servicios del Sistema

### Crear servicio systemd para auto-inicio

```bash
cat > /etc/systemd/system/actas-municipales.service << 'EOF'
[Unit]
Description=Sistema de Actas Municipales Docker
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/actas-ia
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
systemctl daemon-reload

# Habilitar servicio para auto-inicio
systemctl enable actas-municipales.service

# Verificar servicio
systemctl status actas-municipales.service
```

### Programar backups automáticos

```bash
# Editar crontab de root
crontab -e

# Agregar la siguiente línea para backup diario a las 2:30 AM:
# 30 2 * * * /usr/local/bin/actas-backup

# Verificar crontab
crontab -l
```

---

## 🔐 Paso 13: Configuraciones de Seguridad

### Configurar SELinux (si está habilitado)

```bash
# Verificar estado de SELinux
getenforce

# Si está en Enforcing, configurar para Docker
setsebool -P container_manage_cgroup true
setsebool -P httpd_can_network_connect true

# Permitir Nginx conectar a backend
setsebool -P httpd_can_network_relay true
```

### Configurar logrotate

```bash
cat > /etc/logrotate.d/actas-municipales << 'EOF'
/var/log/nginx/actas_*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 nginx nginx
    postrotate
        /bin/kill -USR1 `cat /run/nginx.pid 2>/dev/null` 2>/dev/null || true
    endscript
}

/opt/actas-ia/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF
```

---

## 📊 Paso 14: Comandos de Monitoreo y Mantenimiento

### Comandos útiles para administración:

```bash
# Control del sistema (usando script creado)
actas-control start      # Iniciar sistema
actas-control stop       # Detener sistema
actas-control restart    # Reiniciar sistema
actas-control status     # Ver estado
actas-control logs       # Ver logs en tiempo real

# Backup manual
actas-backup

# Ver uso de recursos
docker stats

# Ver logs específicos
docker compose logs actas_web
docker compose logs actas_postgres
docker compose logs actas_celery_worker

# Ejecutar comandos Django
docker compose exec actas_web python manage.py shell
docker compose exec actas_web python manage.py createsuperuser

# Actualizar el sistema
cd /opt/actas-ia
git pull origin main
docker compose build --no-cache
docker compose down
docker compose up -d

# Limpiar Docker (liberar espacio)
docker system prune -f
docker volume prune -f
```

---

## 🔍 Resolución de Problemas Comunes

### Problema: Nginx no puede conectar al backend

```bash
# Verificar que los contenedores estén corriendo
docker compose ps

# Verificar conectividad
curl -I http://127.0.0.1:8000

# Ver logs de Nginx
tail -f /var/log/nginx/actas_error.log

# Verificar configuración de Nginx
nginx -t

# Reiniciar Nginx
systemctl restart nginx
```

### Problema: Contenedores no inician

```bash
# Ver logs detallados
docker compose logs

# Verificar espacio en disco
df -h

# Verificar memoria
free -h

# Verificar puertos en uso
netstat -tulpn | grep -E ':(8000|5432|6379|5555)'

# Limpiar Docker y reiniciar
docker compose down
docker system prune -f
docker compose up -d
```

### Problema: Base de datos no conecta

```bash
# Verificar contenedor PostgreSQL
docker compose exec actas_postgres pg_isready -U admin_actas

# Conectar manualmente a la BD
docker compose exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza

# Recrear base de datos si es necesario
docker compose exec actas_postgres psql -U admin_actas -c "DROP DATABASE IF EXISTS actas_municipales_pastaza;"
docker compose exec actas_postgres psql -U admin_actas -c "CREATE DATABASE actas_municipales_pastaza;"
docker compose exec actas_web python manage.py migrate
```

### Problema: Permisos de archivos

```bash
# Verificar permisos
ls -la /opt/actas-ia/

# Corregir permisos si es necesario
chown -R root:root /opt/actas-ia/
chmod -R 755 /opt/actas-ia/

# Verificar volúmenes Docker
docker compose exec actas_web ls -la /app/media/
```

---

## 🎯 Verificación Final del Sistema

### Checklist de verificación:

```bash
# ✅ 1. Verificar servicios del sistema
systemctl status nginx
systemctl status docker
systemctl status firewalld

# ✅ 2. Verificar contenedores Docker
docker compose ps

# ✅ 3. Verificar conectividad web
curl -I http://localhost         # Nginx
curl -I http://localhost:8000    # Django directo

# ✅ 4. Verificar base de datos
docker compose exec actas_postgres psql -U admin_actas -l

# ✅ 5. Verificar logs
tail -n 20 /var/log/nginx/actas_access.log
docker compose logs --tail=20 actas_web

# ✅ 6. Verificar archivos estáticos
ls -la /opt/actas-ia/staticfiles/

# ✅ 7. Test de acceso al admin
curl -I http://localhost/admin/
```

---

## 🚀 ¡Sistema Listo!

Si todos los pasos se completaron correctamente, tu **Sistema de Actas Municipales** debería estar funcionando en Rocky Linux 9 con:

### ✅ **Componentes Instalados**:
- ✅ Rocky Linux 9 base system
- ✅ Nginx como proxy reverso (puerto 80/443)
- ✅ Docker y Docker Compose
- ✅ Sistema de Actas en contenedores
- ✅ PostgreSQL, Redis, Celery
- ✅ Scripts de mantenimiento
- ✅ Servicios systemd
- ✅ Backups automáticos
- ✅ Configuración de seguridad

### 🌐 **URLs de Acceso**:
- **Aplicación**: `http://tu-servidor.com`
- **Admin**: `http://tu-servidor.com/admin/`
- **Flower**: `http://tu-servidor.com/flower/`

### 🔑 **Credenciales**:
- **Superadmin**: `superadmin` / `AdminPuyo2025!`
- **Alcalde**: `alcalde.pastaza` / `AlcaldePuyo2025!`

### 📞 **Comandos de Administración**:
```bash
actas-control start/stop/restart/status/logs
actas-backup
systemctl status actas-municipales
```

**¡El Sistema de Actas Municipales está completamente operativo en Rocky Linux 9!** 🎉🏛️