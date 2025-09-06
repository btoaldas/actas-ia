import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection

# Función para registrar logs del sistema
print('Ejecutando creación de función registrar_log_sistema...')
with connection.cursor() as cursor:
    cursor.execute("""
    CREATE OR REPLACE FUNCTION logs.registrar_log_sistema(
        p_nivel VARCHAR(20),
        p_categoria VARCHAR(50),
        p_subcategoria VARCHAR(100),
        p_mensaje TEXT,
        p_usuario_id INTEGER DEFAULT NULL,
        p_session_id VARCHAR(255) DEFAULT NULL,
        p_ip_address INET DEFAULT NULL,
        p_datos_extra JSONB DEFAULT NULL,
        p_modulo VARCHAR(100) DEFAULT NULL,
        p_url VARCHAR(255) DEFAULT NULL,
        p_metodo_http VARCHAR(10) DEFAULT NULL,
        p_tiempo_respuesta_ms INTEGER DEFAULT NULL,
        p_codigo_respuesta INTEGER DEFAULT NULL
    )
    RETURNS BIGINT AS $function$
    DECLARE
        log_id BIGINT;
    BEGIN
        INSERT INTO logs.sistema_logs (
            nivel, categoria, subcategoria, mensaje, usuario_id, session_id,
            ip_address, datos_extra, modulo, url_solicitada, metodo_http,
            tiempo_respuesta_ms, codigo_respuesta
        ) VALUES (
            p_nivel, p_categoria, p_subcategoria, p_mensaje, p_usuario_id, p_session_id,
            p_ip_address, p_datos_extra, p_modulo, p_url, p_metodo_http,
            p_tiempo_respuesta_ms, p_codigo_respuesta
        ) RETURNING id INTO log_id;
        
        RETURN log_id;
    END;
    $function$ LANGUAGE plpgsql;
    """)
    
print('✅ Función registrar_log_sistema creada')

# Función para registrar navegación
print('Ejecutando creación de función registrar_navegacion...')
with connection.cursor() as cursor:
    cursor.execute("""
    CREATE OR REPLACE FUNCTION logs.registrar_navegacion(
        p_usuario_id INTEGER,
        p_session_id VARCHAR(255),
        p_url_visitada TEXT,
        p_url_anterior TEXT DEFAULT NULL,
        p_metodo_http VARCHAR(10) DEFAULT 'GET',
        p_accion_realizada VARCHAR(100) DEFAULT 'VISIT',
        p_ip_address INET DEFAULT NULL,
        p_parametros_get JSONB DEFAULT NULL,
        p_parametros_post JSONB DEFAULT NULL
    )
    RETURNS BIGINT AS $function$
    DECLARE
        log_id BIGINT;
    BEGIN
        INSERT INTO logs.navegacion_usuarios (
            usuario_id, session_id, url_visitada, url_anterior, metodo_http,
            accion_realizada, ip_address, parametros_get, parametros_post
        ) VALUES (
            p_usuario_id, p_session_id, p_url_visitada, p_url_anterior, p_metodo_http,
            p_accion_realizada, p_ip_address, p_parametros_get, p_parametros_post
        ) RETURNING id INTO log_id;
        
        RETURN log_id;
    END;
    $function$ LANGUAGE plpgsql;
    """)
    
print('✅ Función registrar_navegacion creada')

# Función de trigger para auditoría automática
print('Ejecutando creación de función de trigger...')
with connection.cursor() as cursor:
    cursor.execute("""
    CREATE OR REPLACE FUNCTION auditoria.registrar_cambio_automatico()
    RETURNS TRIGGER AS $function$
    DECLARE
        usuario_actual INTEGER;
        session_actual VARCHAR(255);
        ip_actual INET;
        campos_modificados TEXT[] := ARRAY[]::TEXT[];
        campo_nombre TEXT;
        transaccion_id BIGINT;
    BEGIN
        -- Obtener información del usuario actual desde variables de sesión
        BEGIN
            usuario_actual := COALESCE(current_setting('audit.user_id', true)::INTEGER, NULL);
            session_actual := COALESCE(current_setting('audit.session_id', true), NULL);
            ip_actual := COALESCE(current_setting('audit.ip_address', true)::INET, NULL);
            transaccion_id := COALESCE(current_setting('audit.transaction_id', true)::BIGINT, txid_current());
        EXCEPTION
            WHEN OTHERS THEN
                usuario_actual := NULL;
                session_actual := NULL;
                ip_actual := NULL;
                transaccion_id := txid_current();
        END;

        -- Para UPDATE, determinar qué campos cambiaron
        IF TG_OP = 'UPDATE' THEN
            FOR campo_nombre IN 
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = TG_TABLE_NAME 
                AND table_schema = TG_TABLE_SCHEMA
            LOOP
                IF (to_jsonb(OLD) ->> campo_nombre) IS DISTINCT FROM (to_jsonb(NEW) ->> campo_nombre) THEN
                    campos_modificados := array_append(campos_modificados, campo_nombre);
                END IF;
            END LOOP;
        END IF;

        -- Insertar registro de auditoría
        IF TG_OP = 'DELETE' THEN
            INSERT INTO auditoria.cambios_bd (
                esquema, tabla, operacion, registro_id, usuario_id, session_id, ip_address,
                valores_anteriores, transaccion_id
            ) VALUES (
                TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP, 
                COALESCE((row_to_json(OLD) ->> 'id')::INTEGER, NULL),
                usuario_actual, session_actual, ip_actual,
                row_to_json(OLD), transaccion_id
            );
            RETURN OLD;
            
        ELSIF TG_OP = 'UPDATE' THEN
            INSERT INTO auditoria.cambios_bd (
                esquema, tabla, operacion, registro_id, usuario_id, session_id, ip_address,
                campos_modificados, valores_anteriores, valores_nuevos, transaccion_id
            ) VALUES (
                TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP,
                COALESCE((row_to_json(NEW) ->> 'id')::INTEGER, NULL),
                usuario_actual, session_actual, ip_actual,
                campos_modificados, row_to_json(OLD), row_to_json(NEW), transaccion_id
            );
            RETURN NEW;
            
        ELSIF TG_OP = 'INSERT' THEN
            INSERT INTO auditoria.cambios_bd (
                esquema, tabla, operacion, registro_id, usuario_id, session_id, ip_address,
                valores_nuevos, transaccion_id
            ) VALUES (
                TG_TABLE_SCHEMA, TG_TABLE_NAME, TG_OP,
                COALESCE((row_to_json(NEW) ->> 'id')::INTEGER, NULL),
                usuario_actual, session_actual, ip_actual,
                row_to_json(NEW), transaccion_id
            );
            RETURN NEW;
        END IF;
        
        RETURN NULL;
    END;
    $function$ LANGUAGE plpgsql;
    """)
    
print('✅ Función de trigger de auditoría creada')

print('🎉 ¡Todas las funciones del sistema de auditoría han sido creadas exitosamente!')
