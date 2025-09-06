-- Script de inicialización para la base de datos del Sistema de Actas Municipales de Pastaza
-- Este script se ejecuta automáticamente cuando se crea el contenedor de PostgreSQL

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Configurar zona horaria
SET timezone = 'America/Guayaquil';

-- Crear usuario adicional para desarrollo si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'desarrollador_actas') THEN
        CREATE USER desarrollador_actas WITH PASSWORD 'dev_actas_2025';
        GRANT ALL PRIVILEGES ON DATABASE actas_municipales_pastaza TO desarrollador_actas;
    END IF;
END
$$;

-- Comentarios sobre la base de datos
COMMENT ON DATABASE actas_municipales_pastaza IS 'Sistema de Gestión de Actas Municipales - Municipio de Pastaza';
