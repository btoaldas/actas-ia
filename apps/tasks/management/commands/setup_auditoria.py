# ============================================================================
# Comando de Django para configurar sistema de auditoría
# Archivo: apps/tasks/management/commands/setup_auditoria.py
# ============================================================================

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
import json

class Command(BaseCommand):
    help = 'Configura el sistema completo de auditoría y logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--incluir-tablas-sistema',
            action='store_true',
            help='Incluir tablas del sistema Django (auth_user, etc.)'
        )
        parser.add_argument(
            '--excluir-tablas',
            type=str,
            help='Lista de tablas a excluir separadas por coma'
        )
        parser.add_argument(
            '--solo-mostrar',
            action='store_true',
            help='Solo mostrar qué tablas se auditarían, sin crear triggers'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Configurando sistema de auditoría...')
        )

        # Obtener lista de tablas
        tablas_para_auditar = self.obtener_tablas_para_auditar(
            incluir_sistema=options['incluir_tablas_sistema'],
            excluir=options['excluir_tablas']
        )

        if options['solo_mostrar']:
            self.mostrar_tablas(tablas_para_auditar)
            return

        # Crear triggers de auditoría
        with transaction.atomic():
            self.crear_triggers_auditoria(tablas_para_auditar)
            self.configurar_logging()
            self.crear_indices_adicionales()

        self.stdout.write(
            self.style.SUCCESS('✅ Sistema de auditoría configurado correctamente')
        )

    def obtener_tablas_para_auditar(self, incluir_sistema=False, excluir=None):
        """Obtiene lista de tablas que deben tener auditoría"""
        
        # Tablas que siempre se excluyen
        excluir_siempre = {
            'logs_sistema_logs',
            'logs_acceso_usuarios', 
            'logs_navegacion_usuarios',
            'logs_celery_logs',
            'logs_api_logs',
            'logs_archivo_logs',
            'logs_errores_sistema',
            'logs_admin_logs',
            'auditoria_cambios_bd',
            'django_migrations',
            'django_session',
            'django_admin_log',
            'django_content_type',
            'auth_permission',
            'django_site'
        }

        # Tablas del sistema Django (opcional)
        tablas_sistema = {
            'auth_user',
            'auth_group',
            'auth_user_groups',
            'auth_user_user_permissions',
            'auth_group_permissions'
        }

        # Tablas adicionales a excluir por parámetro
        if excluir:
            excluir_adicionales = set(excluir.split(','))
            excluir_siempre.update(excluir_adicionales)

        with connection.cursor() as cursor:
            # Obtener todas las tablas de la base de datos
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            todas_las_tablas = [row[0] for row in cursor.fetchall()]

        # Filtrar tablas
        tablas_para_auditar = []
        for tabla in todas_las_tablas:
            # Saltar tablas siempre excluidas
            if tabla in excluir_siempre:
                continue
                
            # Saltar tablas del sistema si no se incluyen
            if not incluir_sistema and tabla in tablas_sistema:
                continue
                
            tablas_para_auditar.append(tabla)

        return tablas_para_auditar

    def mostrar_tablas(self, tablas):
        """Muestra las tablas que serían auditadas"""
        self.stdout.write('\n📋 Tablas que serían auditadas:')
        for i, tabla in enumerate(tablas, 1):
            self.stdout.write(f'  {i:2d}. {tabla}')
        
        self.stdout.write(f'\n📊 Total: {len(tablas)} tablas')

    def crear_triggers_auditoria(self, tablas):
        """Crea triggers de auditoría para las tablas especificadas"""
        
        triggers_creados = 0
        triggers_fallidos = 0

        with connection.cursor() as cursor:
            for tabla in tablas:
                try:
                    # Verificar si ya existe el trigger
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM information_schema.triggers 
                        WHERE trigger_name = %s AND event_object_table = %s
                    """, [f'audit_trigger_{tabla}', tabla])
                    
                    existe_trigger = cursor.fetchone()[0] > 0
                    
                    if existe_trigger:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Trigger ya existe para tabla: {tabla}')
                        )
                        continue

                    # Crear trigger
                    sql_trigger = f"""
                        CREATE TRIGGER audit_trigger_{tabla}
                            AFTER INSERT OR UPDATE OR DELETE ON {tabla}
                            FOR EACH ROW 
                            EXECUTE FUNCTION auditoria.registrar_cambio_automatico();
                    """
                    
                    cursor.execute(sql_trigger)
                    triggers_creados += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Trigger creado para tabla: {tabla}')
                    )
                    
                except Exception as e:
                    triggers_fallidos += 1
                    self.stdout.write(
                        self.style.ERROR(f'❌ Error creando trigger para {tabla}: {e}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎯 Triggers creados: {triggers_creados} | Fallidos: {triggers_fallidos}'
            )
        )

    def configurar_logging(self):
        """Configura ajustes adicionales de logging"""
        
        with connection.cursor() as cursor:
            # Configurar log_statement para PostgreSQL (si es posible)
            try:
                cursor.execute("SHOW log_statement")
                current_setting = cursor.fetchone()[0]
                
                if current_setting != 'all':
                    self.stdout.write(
                        self.style.WARNING(
                            '⚠️  Considera configurar log_statement = "all" en postgresql.conf '
                            'para logging completo de SQL'
                        )
                    )
            except Exception:
                pass

            # Crear función para limpiar logs antiguos
            cursor.execute("""
                CREATE OR REPLACE FUNCTION logs.limpiar_logs_antiguos(dias_conservar INTEGER DEFAULT 90)
                RETURNS TABLE(tabla TEXT, registros_eliminados BIGINT) AS $$
                DECLARE
                    fecha_limite TIMESTAMP;
                    rec RECORD;
                    eliminados BIGINT;
                BEGIN
                    fecha_limite := CURRENT_TIMESTAMP - (dias_conservar || ' days')::INTERVAL;
                    
                    -- Limpiar logs del sistema
                    DELETE FROM logs.sistema_logs WHERE timestamp < fecha_limite;
                    GET DIAGNOSTICS eliminados = ROW_COUNT;
                    tabla := 'logs.sistema_logs';
                    registros_eliminados := eliminados;
                    RETURN NEXT;
                    
                    -- Limpiar logs de acceso (mantener más tiempo)
                    DELETE FROM logs.acceso_usuarios WHERE timestamp < (fecha_limite - '30 days'::INTERVAL);
                    GET DIAGNOSTICS eliminados = ROW_COUNT;
                    tabla := 'logs.acceso_usuarios';
                    registros_eliminados := eliminados;
                    RETURN NEXT;
                    
                    -- Limpiar navegación (mantener menos tiempo)
                    DELETE FROM logs.navegacion_usuarios WHERE timestamp < (fecha_limite + '30 days'::INTERVAL);
                    GET DIAGNOSTICS eliminados = ROW_COUNT;
                    tabla := 'logs.navegacion_usuarios';
                    registros_eliminados := eliminados;
                    RETURN NEXT;
                    
                    -- Limpiar logs de Celery
                    DELETE FROM logs.celery_logs WHERE timestamp < fecha_limite;
                    GET DIAGNOSTICS eliminados = ROW_COUNT;
                    tabla := 'logs.celery_logs';
                    registros_eliminados := eliminados;
                    RETURN NEXT;
                    
                    -- Limpiar errores resueltos antiguos
                    DELETE FROM logs.errores_sistema 
                    WHERE timestamp < fecha_limite AND resuelto = true;
                    GET DIAGNOSTICS eliminados = ROW_COUNT;
                    tabla := 'logs.errores_sistema';
                    registros_eliminados := eliminados;
                    RETURN NEXT;
                END;
                $$ LANGUAGE plpgsql;
            """)

            self.stdout.write(
                self.style.SUCCESS('✅ Función de limpieza de logs creada')
            )

    def crear_indices_adicionales(self):
        """Crea índices adicionales para optimización"""
        
        indices_adicionales = [
            # Índices compuestos para consultas frecuentes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sistema_logs_usuario_fecha ON logs.sistema_logs(usuario_id, timestamp DESC) WHERE usuario_id IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_cambios_bd_usuario_tabla ON auditoria.cambios_bd(usuario_id, tabla, timestamp DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_navegacion_session_tiempo ON logs.navegacion_usuarios(session_id, timestamp DESC)",
            
            # Índices para reportes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_acceso_usuarios_fecha_tipo ON logs.acceso_usuarios(DATE(timestamp), tipo_evento)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_errores_no_resueltos ON logs.errores_sistema(resuelto, timestamp DESC) WHERE resuelto = false",
            
            # Índices para análisis de rendimiento
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sistema_logs_tiempo_respuesta ON logs.sistema_logs(tiempo_respuesta_ms) WHERE tiempo_respuesta_ms > 1000",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_celery_logs_duracion ON logs.celery_logs(duracion_segundos) WHERE duracion_segundos > 60"
        ]

        indices_creados = 0
        
        with connection.cursor() as cursor:
            for sql_indice in indices_adicionales:
                try:
                    cursor.execute(sql_indice)
                    indices_creados += 1
                    
                    # Extraer nombre del índice del SQL
                    nombre_indice = sql_indice.split('IF NOT EXISTS ')[1].split(' ON')[0]
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Índice creado: {nombre_indice}')
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  No se pudo crear índice: {e}')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'📊 Índices adicionales creados: {indices_creados}')
        )

    def verificar_configuracion(self):
        """Verifica que el sistema de auditoría esté configurado correctamente"""
        
        verificaciones = []
        
        with connection.cursor() as cursor:
            # Verificar existencia de esquemas
            cursor.execute("""
                SELECT schema_name FROM information_schema.schemata 
                WHERE schema_name IN ('logs', 'auditoria')
            """)
            esquemas = [row[0] for row in cursor.fetchall()]
            
            verificaciones.append({
                'item': 'Esquemas logs y auditoria',
                'status': len(esquemas) == 2,
                'detalle': f'Encontrados: {", ".join(esquemas)}'
            })
            
            # Verificar tablas de logs
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'logs' AND table_type = 'BASE TABLE'
            """)
            tablas_logs = len(cursor.fetchall())
            
            verificaciones.append({
                'item': 'Tablas de logs',
                'status': tablas_logs >= 6,
                'detalle': f'{tablas_logs} tablas encontradas'
            })
            
            # Verificar función de auditoría
            cursor.execute("""
                SELECT routine_name FROM information_schema.routines 
                WHERE routine_schema = 'auditoria' 
                AND routine_name = 'registrar_cambio_automatico'
            """)
            funcion_auditoria = cursor.fetchone() is not None
            
            verificaciones.append({
                'item': 'Función de auditoría',
                'status': funcion_auditoria,
                'detalle': 'Función registrar_cambio_automatico'
            })
            
            # Verificar triggers activos
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.triggers 
                WHERE trigger_name LIKE 'audit_trigger_%'
            """)
            triggers_activos = cursor.fetchone()[0]
            
            verificaciones.append({
                'item': 'Triggers de auditoría',
                'status': triggers_activos > 0,
                'detalle': f'{triggers_activos} triggers activos'
            })

        # Mostrar resultados
        self.stdout.write('\n🔍 Verificación del sistema:')
        for verificacion in verificaciones:
            status_icon = '✅' if verificacion['status'] else '❌'
            self.stdout.write(
                f'  {status_icon} {verificacion["item"]}: {verificacion["detalle"]}'
            )

        return all(v['status'] for v in verificaciones)
