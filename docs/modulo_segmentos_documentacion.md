# 📋 Módulo de Segmentos de Plantillas - Documentación Completa

## 🎯 Introducción

El **Módulo de Segmentos de Plantillas** es un componente avanzado del sistema Actas IA que permite crear, gestionar y procesar segmentos reutilizables para la generación automática de actas municipales utilizando Inteligencia Artificial.

### ✨ Características Principales

- **Segmentos Estáticos y Dinámicos**: Soporte para contenido fijo y generado por IA
- **Integración IA**: Compatible con múltiples proveedores (OpenAI, Anthropic, modelos locales)
- **Variables Personalizadas**: Sistema flexible de variables con valores por defecto
- **Procesamiento Asíncrono**: Tareas Celery para operaciones de larga duración
- **Dashboard en Tiempo Real**: Métricas y estadísticas actualizadas
- **Sistema de Filtros**: 15 criterios de búsqueda y filtrado avanzado
- **Audit Trail**: Seguimiento completo de cambios y uso

---

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─ Modelo de Datos ─────┐   ┌─ Procesamiento ─────┐   ┌─ Interface ──────┐
│ • SegmentoPlantilla   │   │ • Tasks Celery      │   │ • Dashboard      │
│ • ProveedorIA         │ ←→│ • Generación IA     │ ←→│ • CRUD Completo  │
│ • Variables JSON      │   │ • Métricas          │   │ • Asistente      │
└───────────────────────┘   └─────────────────────┘   └──────────────────┘
```

### Tecnologías Utilizadas

- **Backend**: Django 4.2.9 con PostgreSQL
- **Queue**: Celery + Redis para procesamiento asíncrono  
- **Frontend**: AdminLTE + jQuery + Bootstrap
- **IA**: Integración con OpenAI, Anthropic y modelos locales

---

## 📊 Modelo de Datos

### SegmentoPlantilla

Modelo principal que representa un segmento reutilizable:

```python
class SegmentoPlantilla(models.Model):
    # Campos básicos
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=100)
    
    # Configuración del segmento
    tipo = models.CharField(max_length=20)  # 'estatico' o 'dinamico'
    activo = models.BooleanField(default=True)
    proveedor_ia = models.ForeignKey(ProveedorIA, null=True, blank=True)
    
    # Contenido y variables
    prompt_ia = models.TextField()
    variables_personalizadas = models.JSONField(default=dict)
    estructura_json = models.JSONField(default=dict)
    
    # Métricas de uso
    total_usos = models.PositiveIntegerField(default=0)
    tiempo_promedio_procesamiento = models.FloatField(null=True)
    ultima_prueba = models.DateTimeField(null=True)
    ultimo_resultado_prueba = models.JSONField(null=True)
    
    # Audit trail
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario_creacion = models.ForeignKey(User, on_delete=models.SET_NULL)
```

### Propiedades Dinámicas

```python
@property
def es_dinamico(self) -> bool:
    """Verifica si el segmento requiere procesamiento IA"""
    return self.tipo == 'dinamico'

@property
def esta_configurado(self) -> bool:
    """Verifica si el segmento está completamente configurado"""
    if self.es_dinamico:
        return bool(self.proveedor_ia and self.prompt_ia)
    return bool(self.estructura_json)
```

---

## 🎛️ Dashboard y Métricas

### Métricas Disponibles

El dashboard proporciona 8 métricas clave en tiempo real:

1. **Total Segmentos**: Cantidad total de segmentos creados
2. **Segmentos Activos**: Segmentos habilitados para uso
3. **Segmentos Dinámicos**: Segmentos que usan IA
4. **Segmentos Estáticos**: Segmentos con contenido fijo
5. **Tiempo Promedio**: Tiempo promedio de procesamiento IA
6. **Total Usos**: Número total de ejecuciones
7. **Últimas Pruebas**: Resultados de pruebas recientes
8. **Distribución por Categoría**: Agrupación por tipo de contenido

### Acceso al Dashboard

```
URL: /generador-actas/segmentos/
Vista: segmentos_dashboard
Template: generador_actas/segmentos/dashboard.html
```

---

## 🔧 CRUD de Segmentos

### Operaciones Disponibles

#### 1. Listar Segmentos
- **URL**: `/generador-actas/segmentos/lista/`
- **Filtros**: 15 criterios de filtrado
- **Paginación**: 20 elementos por página
- **Búsqueda**: Por nombre, código, descripción

#### 2. Crear Segmento
- **URL**: `/generador-actas/segmentos/crear/`
- **Validaciones**: Código único, proveedor IA requerido para dinámicos
- **Campos**: Todos los campos del modelo más validación JSON

#### 3. Ver Detalle
- **URL**: `/generador-actas/segmentos/<id>/`
- **Información**: Datos completos + métricas de uso
- **Acciones**: Editar, eliminar, probar, duplicar

#### 4. Editar Segmento  
- **URL**: `/generador-actas/segmentos/<id>/editar/`
- **Preservación**: Mantiene métricas existentes
- **Historial**: Registra cambios en audit trail

#### 5. Eliminar Segmento
- **URL**: `/generador-actas/segmentos/<id>/eliminar/`
- **Validación**: Verifica dependencias antes de eliminar
- **Confirmación**: Modal de confirmación con información

---

## 🧪 Sistema de Pruebas

### Prueba Individual

Permite probar un segmento específico con datos reales:

```python
# Endpoint de prueba
URL: /generador-actas/segmentos/probar/
Método: POST

# Datos de ejemplo
{
    "segmento_id": 1,
    "datos_contexto": {
        "fecha_reunion": "2025-09-14",
        "asistentes": ["Juan Pérez", "María García"],
        "tema_principal": "Presupuesto Municipal"
    },
    "usar_celery": true
}
```

### API de Prueba Asíncrona

```python
# Endpoint API
URL: /api/segmentos/probar/
Método: POST

# Respuesta para Celery
{
    "success": true,
    "tipo": "celery", 
    "task_id": "uuid-task-id",
    "status_url": "/api/segmentos/task-status/uuid-task-id/"
}

# Respuesta directa
{
    "success": true,
    "tipo": "directo",
    "contenido": "Contenido generado...",
    "tiempo_procesamiento": 2.34,
    "tokens_usados": 245
}
```

---

## 🎨 Asistente de Variables

### Funcionalidad

El asistente ayuda a configurar variables personalizadas de forma visual:

- **Variables Comunes**: 12 variables predefinidas
- **Configuración Visual**: Checkboxes con valores por defecto
- **Variables Adicionales**: Editor JSON para variables personalizadas
- **Ejemplos Predefinidos**: Plantillas para casos comunes
- **Validación en Tiempo Real**: Verificación de sintaxis JSON

### Variables Comunes Disponibles

```json
{
    "fecha_reunion": {
        "tipo": "date",
        "ejemplo": "2025-09-14",
        "descripcion": "Fecha de la reunión"
    },
    "asistentes": {
        "tipo": "array",
        "ejemplo": ["Juan Pérez", "María García"],
        "descripcion": "Lista de asistentes"
    },
    "tema_principal": {
        "tipo": "string", 
        "ejemplo": "Presupuesto Municipal",
        "descripcion": "Tema principal tratado"
    },
    "ubicacion": {
        "tipo": "string",
        "ejemplo": "Salón de Sesiones",
        "descripcion": "Lugar de la reunión"
    }
    // ... 8 variables más
}
```

### Uso del Asistente

```
URL: /generador-actas/segmentos/asistente-variables/
Proceso:
1. Seleccionar variables necesarias
2. Definir valores por defecto
3. Agregar variables adicionales (opcional)
4. Generar JSON
5. Copiar al portapapeles
6. Usar en formulario de segmento
```

---

## ⚙️ Tareas Celery

### Tareas Implementadas

#### 1. Procesamiento Individual
```python
procesar_segmento_dinamico.delay(
    segmento_id=1,
    datos_contexto={"fecha": "2025-09-14"},
    configuracion={"max_tokens": 1500}
)
```

#### 2. Procesamiento en Lote
```python
batch_procesar_segmentos.delay({
    "segmentos": [
        {
            "segmento_id": 1,
            "datos_contexto": {"tema": "Presupuesto"},
            "configuracion": {"temperature": 0.8}
        },
        {
            "segmento_id": 2, 
            "datos_contexto": {"tema": "Obras"},
            "configuracion": {"max_tokens": 2000}
        }
    ],
    "datos_contexto": {
        "fecha_reunion": "2025-09-14",
        "municipio": "Pastaza"
    }
})
```

#### 3. Mantenimiento
```python
# Limpiar métricas antiguas (>90 días)
limpiar_metricas_antiguas_segmentos.delay()

# Generar reporte de uso
generar_reporte_uso_segmentos.delay()
```

### Configuración Celery

```python
# settings.py
CELERY_TASK_ROUTES = {
    'apps.generador_actas.tasks.procesar_segmento_dinamico': {'queue': 'ia_processing'},
    'apps.generador_actas.tasks.batch_procesar_segmentos': {'queue': 'ia_batch'},
    'apps.generador_actas.tasks.limpiar_metricas_antiguas_segmentos': {'queue': 'maintenance'},
}

CELERY_TASK_TIME_LIMIT = 600  # 10 minutos
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutos
```

---

## 🔍 Sistema de Filtros

### Filtros Disponibles (15 opciones)

1. **Búsqueda General**: Por nombre, código, descripción
2. **Tipo**: Estático o dinámico
3. **Estado**: Activo o inactivo  
4. **Categoría**: Apertura, desarrollo, cierre, etc.
5. **Proveedor IA**: Por proveedor específico
6. **Fecha Creación**: Rango de fechas
7. **Usuario Creación**: Por creador
8. **Tiene Variables**: Con/sin variables personalizadas
9. **Total Usos**: Rango numérico
10. **Tiempo Procesamiento**: Rango de tiempo
11. **Última Prueba**: Rango de fechas
12. **Resultado Última Prueba**: Exitoso/fallido
13. **Ordenar Por**: 8 opciones de ordenamiento
14. **Elementos por Página**: 10, 20, 50, 100
15. **Exportar**: CSV, JSON, Excel

### Uso de Filtros

```python
# Ejemplo de filtro
GET /generador-actas/segmentos/lista/?tipo=dinamico&categoria=apertura&activo=true&ordenar_por=-total_usos
```

---

## 🔐 Seguridad y Permisos

### Niveles de Acceso

- **superadmin**: Acceso completo a todas las funciones
- **admin_pastaza**: Gestión de segmentos y configuración
- **alcalde**: Visualización y pruebas de segmentos
- **secretario**: Uso de segmentos en generación de actas

### Validaciones de Seguridad

```python
# Validación de permisos
@login_required
def crear_segmento(request):
    if not request.user.has_perm('generador_actas.add_segmentoplantilla'):
        raise PermissionDenied

# Validación de datos
class SegmentoPlantillaForm(forms.ModelForm):
    def clean_variables_personalizadas(self):
        data = self.cleaned_data['variables_personalizadas']
        try:
            json.loads(json.dumps(data))  # Validar JSON
        except:
            raise ValidationError("JSON inválido")
        return data
```

---

## 📱 Frontend y UX

### Componentes UI

#### Dashboard Cards
```html
<div class="row">
    <div class="col-lg-3 col-6">
        <div class="small-box bg-info">
            <div class="inner">
                <h3>{{ metricas.total_segmentos }}</h3>
                <p>Total Segmentos</p>
            </div>
            <div class="icon">
                <i class="fas fa-puzzle-piece"></i>
            </div>
        </div>
    </div>
    <!-- Más cards... -->
</div>
```

#### Formularios Dinámicos
```javascript
// Validación JSON en tiempo real
$('#id_variables_personalizadas').on('input', function() {
    const valor = $(this).val().trim();
    if (valor) {
        try {
            JSON.parse(valor);
            $(this).removeClass('is-invalid').addClass('is-valid');
        } catch (e) {
            $(this).removeClass('is-valid').addClass('is-invalid');
        }
    }
});
```

#### Modales de Confirmación
```html
<div class="modal" id="confirmarEliminacion">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h4>Confirmar Eliminación</h4>
            </div>
            <div class="modal-body">
                <p>¿Estás seguro de eliminar el segmento "{{ segmento.nombre }}"?</p>
                <div class="alert alert-warning">
                    Esta acción no se puede deshacer.
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-default" data-dismiss="modal">Cancelar</button>
                <button type="submit" class="btn btn-danger">Eliminar</button>
            </div>
        </div>
    </div>
</div>
```

---

## 🚀 Guía de Uso

### Caso de Uso 1: Crear Segmento Estático

```
1. Ir a Dashboard Segmentos
2. Clic en "Crear Nuevo Segmento"
3. Llenar campos básicos:
   - Código: "APERTURA_SESION"
   - Nombre: "Apertura de Sesión Municipal"
   - Tipo: "Estático"
   - Categoría: "Apertura"
4. Definir estructura JSON:
   {
     "titulo": "APERTURA DE SESIÓN",
     "contenido": "Se declara abierta la sesión municipal...",
     "campos": ["fecha", "hora", "asistentes"]
   }
5. Guardar segmento
```

### Caso de Uso 2: Crear Segmento Dinámico

```
1. Ir a Dashboard Segmentos  
2. Clic en "Crear Nuevo Segmento"
3. Llenar campos básicos:
   - Código: "RESUMEN_TEMAS"
   - Nombre: "Resumen de Temas Tratados"
   - Tipo: "Dinámico" 
   - Categoría: "Desarrollo"
4. Seleccionar Proveedor IA
5. Definir prompt:
   "Genera un resumen ejecutivo de los temas tratados en la reunión municipal del {{fecha_reunion}}. Temas: {{temas_tratados}}. Formato formal y conciso."
6. Usar Asistente de Variables:
   - Seleccionar: fecha_reunion, temas_tratados
   - Definir valores por defecto
7. Generar JSON y pegarlo en Variables Personalizadas
8. Guardar segmento
```

### Caso de Uso 3: Probar Segmento

```
1. Ir a lista de segmentos
2. Buscar segmento deseado
3. Clic en "Acciones" → "Probar"
4. Llenar datos de contexto:
   {
     "fecha_reunion": "2025-09-14",
     "temas_tratados": "Presupuesto 2026, Obras públicas, Ordenanzas"
   }
5. Seleccionar modo:
   - Directo: Resultado inmediato
   - Celery: Procesamiento asíncrono
6. Ver resultado y métricas
```

---

## 🔧 Configuración y Despliegue

### Variables de Entorno

```bash
# Configuración IA
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=ant-...

# Configuración Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Configuración BD
DATABASE_URL=postgresql://admin_actas:password@localhost:5432/actas_municipales_pastaza
```

### Comandos de Despliegue

```bash
# Aplicar migraciones
docker exec -it actas_web python manage.py migrate

# Crear datos iniciales
docker exec -it actas_web python manage.py crear_usuarios_iniciales

# Inicializar permisos
docker exec -it actas_web python manage.py init_permissions_system

# Verificar sistema
docker exec -it actas_web python test_segmentos_final.py
```

### Monitoreo

```bash
# Ver logs en tiempo real
docker logs -f actas_web
docker logs -f actas_celery_worker

# Monitoreo Celery
# Acceder a: http://localhost:5555 (Flower)

# Verificar estado
docker exec -it actas_web python manage.py shell -c "
from apps.generador_actas.models import SegmentoPlantilla
print(f'Segmentos activos: {SegmentoPlantilla.objects.filter(activo=True).count()}')
"
```

---

## 🐛 Troubleshooting

### Problemas Comunes

#### 1. Error de URLs
```bash
# Síntoma: AttributeError: module 'apps.generador_actas.views' has no attribute 'dashboard_segmentos'
# Solución: Verificar nombres de funciones en views.py y urls.py

# Verificar
grep -n "def.*dashboard" apps/generador_actas/views.py
grep -n "dashboard" apps/generador_actas/urls.py
```

#### 2. Templates No Encontrados
```bash
# Síntoma: TemplateDoesNotExist
# Solución: Verificar estructura de directorios

# Estructura correcta:
templates/
  generador_actas/
    segmentos/
      dashboard.html
      lista.html
      crear.html
      # etc...
```

#### 3. Errores de Celery
```bash
# Síntoma: Tareas no se ejecutan
# Verificar worker activo
docker logs actas_celery_worker

# Verificar Redis
docker exec -it actas_redis redis-cli ping
```

#### 4. Errores de JSON
```javascript
// Frontend: Validación en tiempo real
function validarJSON(texto) {
    try {
        JSON.parse(texto);
        return true;
    } catch (e) {
        return false;
    }
}
```

### Comandos de Diagnóstico

```bash
# Script de validación completa
docker exec -it actas_web python test_segmentos_final.py

# Verificar migración específica
docker exec -it actas_web python manage.py showmigrations generador_actas

# Verificar permisos
docker exec -it actas_web python manage.py shell -c "
from django.contrib.auth.models import Permission
perms = Permission.objects.filter(content_type__app_label='generador_actas')
for p in perms: print(f'{p.codename}: {p.name}')
"
```

---

## 📈 Roadmap y Mejoras Futuras

### Funcionalidades Planificadas

#### Corto Plazo (1-2 meses)
- [ ] Integración real con APIs de OpenAI y Anthropic
- [ ] Sistema de plantillas predefinidas
- [ ] Exportación masiva de segmentos
- [ ] Versionado de segmentos

#### Mediano Plazo (3-6 meses)
- [ ] Editor visual de segmentos (drag & drop)
- [ ] Sistema de aprobación de cambios
- [ ] Métricas avanzadas con gráficos
- [ ] Integración con sistema de notificaciones

#### Largo Plazo (6+ meses)
- [ ] Machine Learning para optimización automática
- [ ] Marketplace de segmentos comunitarios
- [ ] API pública para integraciones externas
- [ ] Soporte multi-idioma

### Optimizaciones Técnicas

- **Performance**: Cache de Redis para consultas frecuentes
- **Escalabilidad**: Separación de colas Celery por prioridad
- **Monitoring**: Integración con Prometheus/Grafana
- **Security**: Cifrado de API keys en base de datos

---

## 👥 Soporte y Contribución

### Contacto

- **Desarrollador Principal**: GitHub Copilot
- **Repositorio**: [actas-ia](https://github.com/btoaldas/actas-ia)
- **Documentación**: `/docs/segmentos/`

### Contribuir

```bash
# Fork del repositorio
git clone https://github.com/tu-usuario/actas-ia.git

# Crear rama para feature
git checkout -b feature/mejora-segmentos

# Desarrollar y probar
docker exec -it actas_web python test_segmentos_final.py

# Commit y push
git add .
git commit -m "feat: nueva funcionalidad en segmentos"
git push origin feature/mejora-segmentos

# Crear Pull Request
```

### Reportar Bugs

Usar el template de issues del repositorio con:
- Descripción detallada del problema
- Pasos para reproducir
- Logs relevantes
- Entorno (SO, versión Docker, etc.)

---

## 📋 Checklist de Implementación

### ✅ Completado

- [x] Modelo de datos extendido
- [x] CRUD completo con validaciones
- [x] Dashboard con métricas en tiempo real
- [x] Sistema de filtros avanzado (15 opciones)
- [x] Pruebas individuales y API
- [x] Asistente visual de variables
- [x] Tareas Celery para procesamiento asíncrono
- [x] Templates responsivos con AdminLTE
- [x] Integración con proveedores IA
- [x] Audit trail completo
- [x] Validación JSON robusta
- [x] Scripts de validación automatizada
- [x] Documentación completa

### 🔄 En Progreso

- [ ] Navegación en menú principal
- [ ] Pruebas unitarias automatizadas
- [ ] Configuración de colas Celery por prioridad

### 📋 Pendiente

- [ ] Integración real con APIs externas
- [ ] Sistema de notificaciones
- [ ] Métricas de costos detalladas
- [ ] Backup automatizado de segmentos

---

*Documentación actualizada: 14 de septiembre de 2025*
*Versión del módulo: 1.0.0*
*Sistema Actas IA - Municipio de Pastaza, Ecuador*