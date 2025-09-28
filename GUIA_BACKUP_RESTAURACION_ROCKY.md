# 🗄️ Guía de Backup y Restauración - Rocky Linux 9

## Restaurar Base de Datos en Servidor Rocky Linux

Esta guía te explica cómo transferir y restaurar el backup de la base de datos desde tu entorno de desarrollo hacia el servidor Rocky Linux 9.

---

## 📋 Archivos de Backup Disponibles

Los siguientes backups han sido generados desde el entorno de desarrollo:
- `backup_bd_rocky_linux_20250928_171820.sql` (7.2MB)
- `backup_bd_rocky_linux_20250928_171826.sql` (7.1MB) 
- `backup_bd_rocky_linux_20250928_171833.sql` (7.1MB)

**Recomendación**: Usar el backup más reciente para tener todos los datos actualizados.

---

## 🚀 Paso 1: Transferir Backup al Servidor Rocky Linux

### Opción A: Usando SCP (Secure Copy)

```bash
# Desde tu máquina local (Windows/desarrollo)
scp backup_bd_rocky_linux_20250928_171833.sql root@TU_IP_SERVIDOR:/opt/actas-ia/

# Ejemplo con IP específica:
# scp backup_bd_rocky_linux_20250928_171833.sql root@192.168.1.100:/opt/actas-ia/
```

### Opción B: Usando WinSCP o FileZilla (GUI)

1. **Abrir WinSCP o FileZilla**
2. **Conectar al servidor**:
   - Host: IP de tu servidor Rocky Linux
   - Usuario: `root`
   - Puerto: `22`
3. **Navegar a**: `/opt/actas-ia/`
4. **Subir archivo**: `backup_bd_rocky_linux_20250928_171833.sql`

### Opción C: Usando Git (si el archivo no es muy grande)

```bash
# En tu máquina de desarrollo
git add backup_bd_rocky_linux_20250928_171833.sql
git commit -m "📦 Backup BD para restauración Rocky Linux"
git push

# En el servidor Rocky Linux
cd /opt/actas-ia
git pull origin main
```

---

## 🗄️ Paso 2: Restaurar Base de Datos en Rocky Linux

### Conectarse al servidor como root:

```bash
# SSH al servidor
ssh root@TU_IP_SERVIDOR

# Navegar al directorio del proyecto
cd /opt/actas-ia

# Verificar que el archivo de backup existe
ls -la backup_bd_*.sql
```

### Restaurar la base de datos:

```bash
# 1. Verificar que los contenedores estén corriendo
docker compose ps

# 2. Si los contenedores no están corriendo, levantarlos
docker compose up -d

# 3. Esperar a que PostgreSQL esté listo
sleep 30
docker compose exec actas_postgres pg_isready -U admin_actas

# 4. Eliminar base de datos existente (si existe)
docker compose exec actas_postgres psql -U admin_actas -c "DROP DATABASE IF EXISTS actas_municipales_pastaza;"

# 5. Crear nueva base de datos limpia
docker compose exec actas_postgres psql -U admin_actas -c "CREATE DATABASE actas_municipales_pastaza;"

# 6. Restaurar backup (usar el archivo más reciente)
cat backup_bd_rocky_linux_20250928_171833.sql | docker compose exec -T actas_postgres psql -U admin_actas -d actas_municipales_pastaza

# 7. Verificar que la restauración fue exitosa
docker compose exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "\dt"
```

---

## 🔍 Paso 3: Verificar Restauración

### Verificar tablas y datos:

```bash
# Conectar a la base de datos y verificar tablas principales
docker compose exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza

# Dentro de psql, ejecutar:
\dt  # Listar todas las tablas
\d auth_user  # Ver estructura tabla usuarios
SELECT count(*) FROM auth_user;  # Contar usuarios
SELECT username FROM auth_user WHERE is_superuser = true;  # Ver superusers
\q  # Salir de psql
```

### Verificar aplicación web:

```bash
# Ejecutar migraciones por si acaso
docker compose exec actas_web python manage.py migrate

# Recopilar archivos estáticos
docker compose exec actas_web python manage.py collectstatic --noinput

# Verificar que la aplicación responde
curl -I http://localhost:8000

# Verificar a través de Nginx
curl -I http://localhost
```

---

## 🚀 Paso 4: Acceso al Sistema Restaurado

### URLs de acceso:

1. **Aplicación principal**: `http://TU_IP_SERVIDOR` o tu dominio
2. **Panel administrativo**: `http://TU_IP_SERVIDOR/admin/`
3. **Monitor Celery**: `http://TU_IP_SERVIDOR/flower/`

### Credenciales restauradas:

```
👤 Super Administrador:
   Usuario: superadmin
   Clave: AdminPuyo2025!

👤 Alcalde:
   Usuario: alcalde.pastaza  
   Clave: AlcaldePuyo2025!
```

**⚠️ IMPORTANTE**: Estas son las credenciales del entorno de desarrollo. **CAMBIARLAS INMEDIATAMENTE** en producción.

---

## 🔐 Paso 5: Configuración Post-Restauración

### Cambiar contraseñas de producción:

```bash
# Crear nuevo superusuario para producción
docker compose exec actas_web python manage.py createsuperuser

# Cambiar contraseña del superadmin existente
docker compose exec actas_web python manage.py changepassword superadmin
```

### Actualizar configuración para producción:

```bash
# Editar variables de entorno
vim /opt/actas-ia/.env

# Cambiar estas variables críticas:
# DEBUG=False
# SECRET_KEY=nueva_clave_secreta_muy_segura_para_produccion
# ALLOWED_HOSTS=tu-dominio.com,tu-ip-servidor
# DB_PASS=nueva_password_postgresql_segura
```

### Reiniciar servicios con nueva configuración:

```bash
# Reiniciar todos los contenedores
docker compose down
docker compose up -d

# Verificar que todo funciona
docker compose ps
curl -I http://localhost
```

---

## 📊 Paso 6: Verificación Final Completa

### Checklist de verificación post-restauración:

```bash
# ✅ 1. Servicios del sistema
systemctl status nginx
systemctl status docker
actas-control status

# ✅ 2. Contenedores Docker
docker compose ps

# ✅ 3. Base de datos
docker compose exec actas_postgres psql -U admin_actas -d actas_municipales_pastaza -c "SELECT count(*) FROM auth_user;"

# ✅ 4. Aplicación web
curl -I http://localhost/admin/

# ✅ 5. Archivos estáticos
ls -la /opt/actas-ia/staticfiles/

# ✅ 6. Logs del sistema
docker compose logs --tail=20 actas_web
tail -n 10 /var/log/nginx/actas_access.log
```

### Probar funcionalidades principales:

```bash
# Acceder al admin y verificar:
# - Usuarios existentes
# - Configuración OAuth (si aplica)  
# - Permisos del sistema
# - Portal ciudadano

# Verificar con curl:
curl -I http://localhost/admin/
curl -I http://localhost/portal-ciudadano/
curl -I http://localhost/api/
```

---

## 🛠️ Comandos de Mantenimiento Post-Restauración

### Scripts disponibles:

```bash
# Control del sistema
actas-control start      # Iniciar
actas-control stop       # Detener  
actas-control restart    # Reiniciar
actas-control status     # Estado
actas-control logs       # Ver logs

# Backup del nuevo sistema
actas-backup

# Ver recursos del sistema
docker stats
free -h
df -h
```

### Programar backups regulares:

```bash
# Verificar que el cron de backup esté configurado
crontab -l

# Si no existe, configurarlo:
crontab -e
# Agregar: 30 2 * * * /usr/local/bin/actas-backup
```

---

## 🔧 Resolución de Problemas Post-Restauración

### Problema: Error de conexión BD después de restaurar

```bash
# Verificar contraseña en .env
cat /opt/actas-ia/.env | grep DB_PASS

# Verificar usuario PostgreSQL
docker compose exec actas_postgres psql -U admin_actas -l

# Recrear usuario si es necesario
docker compose exec actas_postgres psql -U postgres -c "ALTER USER admin_actas PASSWORD 'nueva_password';"
```

### Problema: Archivos estáticos no se ven

```bash
# Recopilar archivos estáticos
docker compose exec actas_web python manage.py collectstatic --noinput

# Verificar permisos Nginx
ls -la /opt/actas-ia/staticfiles/
chown -R root:root /opt/actas-ia/staticfiles/
chmod -R 755 /opt/actas-ia/staticfiles/
```

### Problema: OAuth no funciona

```bash
# Verificar configuración OAuth
docker compose exec actas_web python manage.py shell -c "
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
print('Site:', Site.objects.get(id=1).domain)
print('GitHub App:', SocialApp.objects.filter(provider='github').exists())
print('Google App:', SocialApp.objects.filter(provider='google').exists())
"

# Reconfigurar si es necesario
docker compose exec actas_web python manage.py crear_social_apps_oauth
```

---

## ✅ Restauración Completada

¡Excelente! Si has seguido todos los pasos, tu **Sistema de Actas Municipales** debería estar completamente restaurado en Rocky Linux 9 con:

### ✅ **Base de Datos Restaurada**:
- ✅ Todos los usuarios y permisos
- ✅ Configuraciones del sistema  
- ✅ Datos de aplicaciones
- ✅ Configuración OAuth (si aplicaba)

### ✅ **Sistema Operativo**:
- ✅ Rocky Linux 9 configurado
- ✅ Nginx proxy funcionando
- ✅ Docker contenedores activos
- ✅ Scripts de mantenimiento
- ✅ Backups programados

### 📞 **Próximos Pasos Recomendados**:
1. ✅ Cambiar todas las contraseñas por defecto
2. ✅ Configurar dominio real en Nginx
3. ✅ Configurar SSL con Let's Encrypt
4. ✅ Probar todas las funcionalidades
5. ✅ Crear usuarios adicionales según necesidad

**¡El sistema está listo para producción!** 🎉🏛️

---

## 📞 Soporte Técnico

Si tienes problemas durante la restauración:

1. **Ver logs**: `docker compose logs actas_web`
2. **Verificar conectividad**: `curl -I http://localhost:8000`
3. **Estado servicios**: `actas-control status`
4. **GitHub Issues**: https://github.com/btoaldas/actas-ia/issues