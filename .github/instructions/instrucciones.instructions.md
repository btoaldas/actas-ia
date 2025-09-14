---
applyTo: '**'
---
Cuando tengas que compilar migraciones, siempre hazlo dentro del entorno Docker, porque este proyecto está trabajando y ejecutándose en Docker, tanto la base de datos como el sistema. Específicamente, cuando debas ejecutar comandos de migrate o de actualización de base de datos.
Nunca debes cambiar a otra base de datos que no sea la que ya se está utilizando, que es PostgreSQL. Por más que haya equivocaciones, nunca intentes pasar a otra tecnología de base de datos, como por ejemplo SQLite. Indícame qué hacer en esos casos.
Espera el tiempo prudente cuando envíes a levantar el Docker, porque puede demorar hasta 300 segundos para continuar con las interacciones de comandos.
Cuando tengas que probar algo y quieras abrir la web y el puerto para explorar, no abras el explorador de contenido simple en VSCode. Mejor consulta con curl en la línea de comandos y envía ahí los parámetros o la URL necesarios para que responda. Es preferible hacerlo tanto para el frontend como para el backend cuando sientas necesidad de verificar si está levantado el sitio o algo así.
Si solo cambias codigo del framework o de backend o apis y nada de infraestructura, no es necesario que vuelvas a reinicializar o iniciar o indiques que levante el Docker. Solo indícame que ejecute el comando que necesites.
Cuando hagas cualquier modificación en el código por favor revisa los logs de los contenedores para verificar si no existe algun problema en lo realizado al menos los 20 últimos, pero utiliza un timer para espera antes de ver de al menos 60 segundos.
No intentes verificar por web ni por comando si una funcion esta activa en vista de que no tienes la posibilidad de interactuar con la web y no vas a saber, en cambio preguntame a mi que yo si veo y si funciona o no funciona la funcionalidad que asumes que deberia valer o no.
En lo psoible en la visata html y demas siempre seccioanr los javascript y css en otros archvios aparte conetados a eso para poder ser mas efectivo en el codigo y los cambios, es decir crear archvios. css y .js recuerda siempre copupar el modelo de css del template del sistema que es AdminLTE
Si vas a eliminar cualquier codigo o archvio completo o reemplazar con otro porfavor muy importante saca un backup de lo que vas a eliminar o reemplazar por si hay algun problema despues y guardalo en la carpeta de scripts con un nombre que indique que es un back up y la fecha y hora, por ejemplo scripts/backup/2024-09-06_backup_nombrearchivo.ext
No reinicies el docker a menos que sea estrictamente necesario, por ejemplo si hay cambios en la infraestructura o en la base de datos, si solo son cambios de codigo no es necesario reiniciar el docker.
Nunca expongas credenciales en el codigo, si necesitas usarlas siempre usa las variables de entorno que estan en el archivo .env
Al reiniciar un contenedor docker espera al menos 60 segundos antes de verificar los logs o intentar acceder a la web o api, no lo reinicies y de inmediato intentes acceder, espera el tiempo prudente no reinicies a menos que sea estrictamente necesario.
Cuando debas ejecutar comandos de manage.py como migrate, createsuperuser, etc, siempre hazlo dentro del contenedor docker, nunca lo hagas fuera del contenedor.

# Copilot Instructions – Actas IA (Django + Docker + AdminLTE)

Estas instrucciones guían a agentes IA para trabajar productivamente en este repositorio. NO inventes estructuras nuevas: sigue lo que ya existe.

## 1. Principios Operativos
1. Siempre trabajar DENTRO de Docker. Nunca ejecutes migrate, createsuperuser, ni accesos directos fuera del contenedor.
2. Base de datos: PostgreSQL (actas_municipales_pastaza). Prohibido cambiar a SQLite u otra.
3. Espera prudencial: tras cambios de backend significativos, espera ~60s antes de inspeccionar logs (tail).
4. Verificaciones: usa curl (no navegadores simulados). Pide confirmación al usuario sobre el estado visual.
5. No expongas credenciales. Si necesitas usarlas, referencia variables de entorno (.env).

## 2. Arquitectura Clave (Resumen)
- Django 4.2.9 modular (apps: audio_processing, transcripcion, auditoria, pages/portal_ciudadano, etc.).
- Pipeline de audio: Ingesta → Mejora → Transcripción (Whisper) + Diarización (pyannote) → Curado → Generación Acta → Aprobación → Publicación.
- Celery + Redis para tareas pesadas (procesamiento audio, transcripción).
- AdminLTE como capa UI (usa sus clases/boxes/cards; no crear frameworks CSS paralelos).
- Configuraciones centralizadas: el administrador define defaults (modelos de configuración). El usuario final puede sobrescribir por instancia, pero siempre partiendo de los valores admin.

## 3. Patrones de Código y Convenciones
1. Prefijos de tareas Celery: procesar_audio_, procesar_transcripcion_… (reutiliza naming).
2. Modelos con contexto municipal: tipo_reunion, participantes, confidencial, metadatos JSON.
3. Estados (workflow): Ingestado → Optimizado → Transcrito → Curado → Acta generada → En aprobación → Aprobado → Publicado → Archivado/Rechazado.
4. Logging/Auditoría: usar helpers existentes antes de crear nuevos. Si falta algo, extender respetando nombres.
5. JSONFields: no almacenar blobs arbitrarios sin llaves semánticas (ej: { "snr": 23.1, "modelo": "whisper-medium" }).

## 4. Operaciones en Docker (Ejemplos)
```bash
# Migraciones
docker exec -it actas_web python [manage.py](http://_vscodecontentref_/0) migrate

# Crear usuarios iniciales / permisos
docker exec -it actas_web python [manage.py](http://_vscodecontentref_/1) crear_usuarios_iniciales
docker exec -it actas_web python [manage.py](http://_vscodecontentref_/2) init_permissions_system

# Revisar últimos logs (ejecutar tras esperar ~60s)
docker logs --tail=50 actas_web
docker logs --tail=50 actas_celery_worker

5. Validaciones con curl (Patrón)
# Ver portal ciudadano
curl -I http://localhost:8000/portal-ciudadano/

# Probar API (ejemplo, adaptar a endpoint real)
curl -X POST http://localhost:8000/api/audio/procesar/ -F "archivo=@sample.wav"

Para endpoints protegidos: autenticar primero (login form) o usar token/session ya existente (pedir al usuario si es necesario).

6. Transcripción & Diarización
Parámetros (Whisper / pyannote) salen de modelos de configuración (ej: ConfiguracionTranscripcion).
Si falla modelo premium (pyannote), hacer fallback a uno básico sin token.
Guardar: texto plano, segmentos con timestamps, hablante, confianza, métricas (duración procesada, latencia).
7. Portal Ciudadano
Ordenación soportada: -fecha_sesion (default), fecha_publicacion, -fecha_publicacion, titulo, -titulo, tipo_sesion__nombre, prioridad…
UI: secciones colapsables (filtros y métricas) deben respetar estado (localStorage).
Resultados: grid de tarjetas AdminLTE (card-outline) – no revertir a listas planas.
8. Al Añadir / Modificar Código
Reutiliza estilos/clases AdminLTE.
Antes de crear un helper nuevo, busca en /helpers, /apps//utils, /apps//logging_helper.py.
Si agregas campo a un modelo:
Crea migración dentro de Docker.
No forzar default incoherente; usar null=True si la data histórica no lo posee.
Mantén consistencia i18n: textos en español neutro administrativo.
9. Errores Frecuentes a Evitar
Usar .url / .path en FileField sin verificar existencia física (envolver con if campo).
Duplicar nombres de vistas (ej: configurar_transcripcion) → causa TypeError (args no coinciden).
Hardcodear rutas de media → usar settings.MEDIA_URL / MEDIA_ROOT.
Hacer consultas costosas en templates (prefetch/select_related en vistas).
10. Checklist al Cerrar una Tarea
¿Migraciones aplicadas en Docker?
¿Logs limpios (sin stacktrace nuevo)?
¿Fallbacks implementados si Celery o modelos IA fallan?
¿Configuraciones respetan defaults de administrador?
¿Sin estilos custom fuera de AdminLTE innecesarios?
¿Endpoints probados con curl?
11. Solicitar Confirmación al Usuario
Cuando la acción implique UI (grid, botón, colapso, etc.), pedir al usuario que confirme visualmente (el agente no navega). No asumir éxito sin esa confirmación.


usario administrador  Super Administrador:
   Usuario: superadmin
   Clave:   AdminPuyo2025!
para enviar por culr siempre autenticarte con este suario para poder ver y acceder a los vistas que necesitan auteticacion

usuarios y coenxion base dedatos


🌐 URL de acceso: http://localhost:8000
🔧 Panel admin: http://localhost:8000/admin/

📊 BASE DE DATOS:
   Host: localhost
   Puerto: 5432
   BD: actas_municipales_pastaza
   Usuario: admin_actas
   Clave: actas_pastaza_2025

🔄 Usuario adicional para BD:
   Usuario: desarrollador_actas
   Clave: dev_actas_2025