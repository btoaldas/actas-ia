# ============================================================================
# Script de demostración del sistema de auditoría
# Archivo: scripts\demo_sistema_auditoria.ps1
# ============================================================================

param(
    [string]$TipoDemo = "completo"  # completo, basico, reportes
)

Write-Host "🎬 Demostración del Sistema de Auditoría - Actas Municipales" -ForegroundColor Cyan
Write-Host "=============================================================" -ForegroundColor Cyan

function Show-DatabaseStats {
    Write-Host ""
    Write-Host "📊 Estadísticas actuales de la base de datos:" -ForegroundColor Yellow
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    # Estadísticas de logs del sistema
    cursor.execute('SELECT COUNT(*) FROM logs.sistema_logs')
    sistema_logs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM logs.acceso_usuarios')
    acceso_logs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM logs.navegacion_usuarios')
    navegacion_logs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM auditoria.cambios_bd')
    cambios_bd = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM logs.errores_sistema')
    errores = cursor.fetchone()[0]
    
    print(f'📋 Logs del sistema:      {sistema_logs:,}')
    print(f'🔐 Logs de acceso:        {acceso_logs:,}')
    print(f'🌐 Logs de navegación:    {navegacion_logs:,}')
    print(f'🔄 Cambios en BD:         {cambios_bd:,}')
    print(f'❌ Errores registrados:   {errores:,}')
"
}

function Test-AuditSystem {
    Write-Host ""
    Write-Host "🧪 Probando el sistema de auditoría..." -ForegroundColor Yellow
    
    # Crear usuario de prueba
    Write-Host "1. Creando usuario de prueba..." -ForegroundColor Gray
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.contrib.auth.models import User
from django.db import connection
import json

# Configurar contexto de auditoría
with connection.cursor() as cursor:
    cursor.execute(\"SELECT set_config('audit.user_id', '1', true)\")
    cursor.execute(\"SELECT set_config('audit.session_id', 'demo_session', true)\")
    cursor.execute(\"SELECT set_config('audit.ip_address', '127.0.0.1', true)\")

# Crear o actualizar usuario de prueba
user, created = User.objects.get_or_create(
    username='demo_audit',
    defaults={
        'email': 'demo@actas.municipales',
        'first_name': 'Usuario',
        'last_name': 'Demo'
    }
)

if created:
    print('✅ Usuario demo_audit creado')
else:
    # Actualizar para generar cambio en auditoría
    user.first_name = 'Usuario Demo'
    user.save()
    print('✅ Usuario demo_audit actualizado')

print(f'   ID del usuario: {user.id}')
"

    # Registrar log de navegación
    Write-Host "2. Registrando navegación de prueba..." -ForegroundColor Gray
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
import json

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT logs.registrar_navegacion(
            1, 'demo_session', '/demo/auditoria/', 
            '/admin/', 'GET', 'DEMO_VISIT', '127.0.0.1',
            %s, NULL
        )
    \"\"\", [json.dumps({'demo': True, 'timestamp': 'now'})])
    
    log_id = cursor.fetchone()[0]
    print(f'✅ Log de navegación registrado (ID: {log_id})')
"

    # Registrar error de prueba
    Write-Host "3. Registrando error de prueba..." -ForegroundColor Gray
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        INSERT INTO logs.errores_sistema (
            nivel_error, codigo_error, mensaje_error, 
            usuario_id, session_id, ip_address, entorno
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    \"\"\", [
        'WARNING', 'DEMO_ERROR', 'Error de demostración del sistema de auditoría',
        1, 'demo_session', '127.0.0.1', 'demo'
    ])
    
    print('✅ Error de demostración registrado')
"

    # Registrar actividad del sistema
    Write-Host "4. Registrando actividad del sistema..." -ForegroundColor Gray
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
import json

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT logs.registrar_log_sistema(
            'INFO', 'DEMO', 'SYSTEM_TEST', 
            'Demostración del sistema de auditoría funcionando correctamente',
            1, 'demo_session', '127.0.0.1',
            %s, 'auditoria', '/demo/', 'GET', 250, 200
        )
    \"\"\", [json.dumps({
        'demo_mode': True,
        'test_timestamp': 'now',
        'features_tested': ['navigation', 'errors', 'database_changes']
    })])
    
    log_id = cursor.fetchone()[0]
    print(f'✅ Log del sistema registrado (ID: {log_id})')
"
}

function Show-RecentActivity {
    Write-Host ""
    Write-Host "📝 Actividad reciente (últimos 10 registros):" -ForegroundColor Yellow
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT 
            timestamp,
            categoria,
            subcategoria,
            mensaje,
            COALESCE(username, 'Sistema') as usuario
        FROM logs.sistema_logs s
        LEFT JOIN auth_user u ON s.usuario_id = u.id
        ORDER BY timestamp DESC
        LIMIT 10
    \"\"\")
    
    print('Timestamp           | Categoría  | Subcategoría    | Usuario    | Mensaje')
    print('-' * 85)
    
    for row in cursor.fetchall():
        timestamp = row[0].strftime('%Y-%m-%d %H:%M:%S')
        categoria = row[1][:10]
        subcategoria = row[2][:15] if row[2] else ''
        mensaje = row[3][:40] + '...' if len(row[3]) > 40 else row[3]
        usuario = row[4][:10]
        
        print(f'{timestamp} | {categoria:<10} | {subcategoria:<15} | {usuario:<10} | {mensaje}')
"
}

function Show-AuditChanges {
    Write-Host ""
    Write-Host "🔄 Cambios recientes en la base de datos:" -ForegroundColor Yellow
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT 
            timestamp,
            tabla,
            operacion,
            COALESCE(username, 'Sistema') as usuario,
            array_length(campos_modificados, 1) as campos_modificados
        FROM auditoria.cambios_bd c
        LEFT JOIN auth_user u ON c.usuario_id = u.id
        ORDER BY timestamp DESC
        LIMIT 10
    \"\"\")
    
    print('Timestamp           | Tabla           | Operación | Usuario    | Campos')
    print('-' * 70)
    
    for row in cursor.fetchall():
        timestamp = row[0].strftime('%Y-%m-%d %H:%M:%S')
        tabla = row[1][:15]
        operacion = row[2]
        usuario = row[3][:10]
        campos = row[4] or 0
        
        print(f'{timestamp} | {tabla:<15} | {operacion:<9} | {usuario:<10} | {campos}')
"
}

function Show-ErrorSummary {
    Write-Host ""
    Write-Host "❌ Resumen de errores por nivel:" -ForegroundColor Yellow
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT 
            nivel_error,
            COUNT(*) as total,
            COUNT(CASE WHEN resuelto = false THEN 1 END) as pendientes,
            MAX(timestamp) as ultimo_error
        FROM logs.errores_sistema
        GROUP BY nivel_error
        ORDER BY 
            CASE nivel_error 
                WHEN 'CRITICAL' THEN 1
                WHEN 'ERROR' THEN 2
                WHEN 'WARNING' THEN 3
                ELSE 4
            END
    \"\"\")
    
    print('Nivel      | Total | Pendientes | Último Error')
    print('-' * 50)
    
    for row in cursor.fetchall():
        nivel = row[0]
        total = row[1]
        pendientes = row[2]
        ultimo = row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else 'N/A'
        
        print(f'{nivel:<10} | {total:>5} | {pendientes:>10} | {ultimo}')
"
}

function Show-UserActivity {
    Write-Host ""
    Write-Host "👥 Actividad de usuarios (últimos 7 días):" -ForegroundColor Yellow
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT 
            u.username,
            COUNT(DISTINCT DATE(a.timestamp)) as dias_activos,
            COUNT(*) as total_accesos,
            MAX(a.timestamp) as ultimo_acceso,
            COUNT(CASE WHEN a.tipo_evento = 'LOGIN_FAILED' THEN 1 END) as fallos_login
        FROM auth_user u
        LEFT JOIN logs.acceso_usuarios a ON u.id = a.usuario_id
        WHERE a.timestamp >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY u.id, u.username
        HAVING COUNT(*) > 0
        ORDER BY total_accesos DESC
        LIMIT 10
    \"\"\")
    
    print('Usuario        | Días | Accesos | Último Acceso       | Fallos')
    print('-' * 65)
    
    for row in cursor.fetchall():
        username = row[0][:14]
        dias = row[1] or 0
        accesos = row[2] or 0
        ultimo = row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else 'N/A'
        fallos = row[4] or 0
        
        print(f'{username:<14} | {dias:>4} | {accesos:>7} | {ultimo} | {fallos:>6}')
"
}

function Show-SystemHealth {
    Write-Host ""
    Write-Host "🏥 Estado de salud del sistema de auditoría:" -ForegroundColor Yellow
    
    & python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
from datetime import datetime, timedelta

with connection.cursor() as cursor:
    # Verificar que las tablas existen
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema IN ('logs', 'auditoria')
    \"\"\")
    tablas = cursor.fetchone()[0]
    
    # Verificar triggers activos
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM information_schema.triggers 
        WHERE trigger_name LIKE 'audit_trigger_%'
    \"\"\")
    triggers = cursor.fetchone()[0]
    
    # Verificar actividad reciente (última hora)
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM logs.sistema_logs 
        WHERE timestamp >= %s
    \"\"\", [datetime.now() - timedelta(hours=1)])
    actividad_reciente = cursor.fetchone()[0]
    
    # Verificar tamaño de los logs
    cursor.execute(\"\"\"
        SELECT 
            schemaname,
            tablename,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
        FROM pg_tables 
        WHERE schemaname IN ('logs', 'auditoria')
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    \"\"\")
    
    print(f'📊 Tablas de auditoría:     {tablas}/8')
    print(f'⚡ Triggers activos:       {triggers}')
    print(f'🔄 Actividad última hora:  {actividad_reciente}')
    print('')
    print('💾 Tamaño de tablas:')
    
    for row in cursor.fetchall():
        schema = row[0]
        table = row[1]
        size = row[2]
        print(f'   {schema}.{table}: {size}')
"
}

# Ejecutar demostración según el tipo
switch ($TipoDemo) {
    "basico" {
        Show-DatabaseStats
        Test-AuditSystem
        Show-RecentActivity
    }
    "reportes" {
        Show-DatabaseStats
        Show-RecentActivity
        Show-AuditChanges
        Show-ErrorSummary
        Show-UserActivity
        Show-SystemHealth
    }
    "completo" {
        Show-DatabaseStats
        Test-AuditSystem
        Show-RecentActivity
        Show-AuditChanges
        Show-ErrorSummary
        Show-UserActivity
        Show-SystemHealth
    }
    default {
        Write-Host "❌ Tipo de demo no válido. Usa: basico, reportes, completo" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 Demostración completada!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Comandos útiles para monitoreo:" -ForegroundColor Cyan
Write-Host "   # Ver logs en tiempo real:" -ForegroundColor White
Write-Host "   Get-Content logs\auditoria.log -Wait" -ForegroundColor Gray
Write-Host ""
Write-Host "   # Limpiar logs de demostración:" -ForegroundColor White
Write-Host "   python manage.py shell -c \"\"from django.db import connection; cursor = connection.cursor(); cursor.execute('DELETE FROM logs.sistema_logs WHERE mensaje LIKE \\'%demostración%\\''); print('Logs limpiados')\"\"" -ForegroundColor Gray
Write-Host ""
Write-Host "   # Ver estadísticas frontend:" -ForegroundColor White
Write-Host "   Start-Process 'http://localhost:8000/api/frontend-stats/'" -ForegroundColor Gray
