# Scripts de Base de Datos - Sistema de Actas Municipales

Esta carpeta contiene todos los scripts SQL para mantenimiento y actualización de la base de datos del sistema de actas municipales de Pastaza.

## Estructura de Carpetas

### 📁 `migrations/`
Scripts de migración para cambios en el esquema de la base de datos.
- Nomenclatura: `YYYY-MM-DD_descripcion.sql`
- Cada script debe ser idempotente (se puede ejecutar múltiples veces sin problemas)

### 📁 `data/`
Scripts para insertar, actualizar o limpiar datos.
- `initial_data.sql` - Datos iniciales del sistema
- `test_data.sql` - Datos de prueba para desarrollo
- `production_data.sql` - Datos específicos para producción

### 📁 `maintenance/`
Scripts para mantenimiento rutinario de la base de datos.
- Limpieza de datos antiguos
- Optimización de índices
- Respaldos y restauraciones

## Cómo usar estos scripts

### Desde contenedor Docker:
```bash
# Conectar al contenedor PostgreSQL
docker exec -it actas_postgres psql -U admin_actas -d actas_municipales_pastaza

# Ejecutar un script específico
docker exec -i actas_postgres psql -U admin_actas -d actas_municipales_pastaza < scripts/migrations/2025-09-06_inicial.sql
```

### Desde cliente externo:
```bash
# Con psql instalado localmente
psql -h localhost -p 5432 -U admin_actas -d actas_municipales_pastaza -f scripts/migrations/2025-09-06_inicial.sql
```

### Desde aplicación Django:
```bash
# Ejecutar migraciones Django
python manage.py migrate

# Cargar datos iniciales
python manage.py loaddata fixtures/initial_data.json
```

## Convenciones

1. **Siempre hacer backup antes de ejecutar scripts en producción**
2. **Probar scripts en ambiente de desarrollo primero**
3. **Usar transacciones para operaciones complejas**
4. **Documentar cada cambio con comentarios claros**
5. **Mantener historial de versiones de cada script**

## Contacto
Para dudas sobre estos scripts, contactar al equipo de desarrollo.
