# 🏛️ Sistema de Actas Municipales - Municipio de Pastaza

**Sistema Integral de Gestión de Actas Municipales** desarrollado sobre **[Django Actas IA PRO](https://app-generator.dev/product/adminlte-pro/django/)**, diseñado específicamente para el Municipio de Pastaza, Ecuador.

## 🚀 Características Premium Activas

- ✅ **OAuth Authentication** - GitHub y Google
- ✅ **Celery Async Tasks** - Procesamiento asíncrono 
- ✅ **CI/CD for Render** - Despliegue automático

## 🏛️ Funcionalidades Municipales

- **Gestión de Actas de Sesiones** - Registro completo de sesiones municipales
- **Procesamiento de Audio** - Transcripción automática con IA
- **Workflow de Aprobación** - Proceso formal de revisión y aprobación
- **Notificaciones Automáticas** - Email y webhook para funcionarios
- **Dashboard Municipal** - Estadísticas y reportes ejecutivos
- **Gestión de Asistentes** - Control de participantes y quórum

<br /> 

## 🔐 Configuración OAuth

### 🚀 Configuración Rápida
```bash
# 1. Ejecutar configurador automático
configurar_oauth.bat

# 2. O configurar manualmente
cp .env.example .env
# Editar .env con tus credenciales OAuth

# 3. Iniciar sistema
iniciar_sistema.bat

# 4. Verificar configuración
python verificar_oauth.py
```

### 📖 Guía Detallada
Ver **[GUIA_OAUTH.md](GUIA_OAUTH.md)** para configuración paso a paso de GitHub y Google OAuth.

### 🔑 Accesos del Sistema
- **URL**: http://localhost:8000
- **Admin**: http://localhost:8000/admin/
- **Login**: `superadmin` / `AdminPuyo2025!`
- **OAuth**: http://localhost:8000/accounts/login/

<br />

## 🔧 Tecnologías Base

- **Framework**: Django 4.2.9 con Actas IA PRO
- **Base de Datos**: PostgreSQL 15 (actas_municipales_pastaza)
- **Cache/Queue**: Redis 7 para Celery
- **Autenticación**: Django Allauth con OAuth GitHub/Google
- **Procesamiento Asíncrono**: Celery con workers especializados
- **Despliegue**: Docker + Render con CI/CD automático
- **Monitoreo**: Flower para tareas Celery

### 📱 Aplicaciones Principales
- **Dynamic DataTables** - Tablas de datos dinámicas
- **Dynamic APIs** - APIs RESTful automáticas  
- **Charts Dashboard** - Estadísticas con ApexCharts
- **React Integration** - Componentes modernos
- **File Manager** - Gestión de archivos multimedia
- **Tasks (Celery)** - Procesamiento asíncrono municipal

<br />

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- Git
- Puerto 8000 disponible

### Instalación
```bash
# 1. Clonar repositorio
git clone <repo-url> actas-municipio-pastaza
cd actas-municipio-pastaza

# 2. Configurar OAuth (opcional)
configurar_oauth.bat

# 3. Iniciar sistema completo
iniciar_sistema.bat
```

### Servicios Activos
- **Web App**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **OAuth Login**: http://localhost:8000/accounts/login/
- **Flower Monitor**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

<br />

## 🏛️ Información Municipal

**Municipio de Pastaza**
- **Cantón**: Pastaza
- **Provincia**: Pastaza
- **Alcalde**: [Nombre del Alcalde]
- **Código Municipal**: 15001
- **Dirección**: Av. Francisco de Orellana y 9 de Octubre
- **Teléfono**: (03) 2883-340
- **Email**: alcaldia@puyo.gob.ec
- **Web**: https://www.puyo.gob.ec

### 👥 Usuarios del Sistema
- **Alcalde** - Revisión y aprobación final
- **Secretario Municipal** - Gestión de actas y transcripciones
- **Concejales** - Revisión y comentarios
- **Técnicos** - Operación del sistema

<br />

## 📞 Soporte Técnico

**Desarrollado para el Municipio de Pastaza**
- **Soporte**: tecnico@puyo.gob.ec
- **Documentación**: Ver archivos .md en el repositorio
- **Issues**: Reportar problemas vía Git

---

*Sistema de Actas Municipales - Municipio de Pastaza, Ecuador* 🏛️
- (Optional) Edit the fields for the extended user model
- (Optional) Enable OAuth for GitHub
- (Optional) Add Celery (async tasks)
- (Optional) Enable Dynamic API Module
- Docker Scripts
- Render CI/Cd Scripts

**The generated Django project is available as a ZIP Archive and also uploaded to GitHub.**

![Django Generator - User Interface for choosing the Design](https://github.com/user-attachments/assets/b989c434-1c53-49ff-8dda-b46dbfc142ac) 

![Django App Generator - User Interface for Edit the Extended User Model](https://github.com/user-attachments/assets/f1a5fb68-a5ba-49c9-a3ae-91716de09912) 

<br />

---
[Django Actas IA PRO](https://app-generator.dev/product/adminlte-pro/django/) - Open-Source **Django** Starter provided by [App Generator](https://app-generator.dev)
