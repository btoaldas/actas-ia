"""
Comando de gestión para demostrar el sistema de auditoría
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.contrib.auth.models import User
from helpers.auditoria_logger import AuditoriaLogger
import json
import uuid


class Command(BaseCommand):
    help = 'Demuestra el funcionamiento del sistema de auditoría'
    
    def handle(self, *args, **options):
        logger = AuditoriaLogger()
        
        self.stdout.write('🧪 Iniciando demostración del sistema de auditoría...')
        
        # 1. Log del sistema directo
        try:
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.sistema_logs (
                        nivel, categoria, subcategoria, mensaje, 
                        usuario_id, session_id, ip_address, 
                        datos_extra, modulo, url_solicitada, metodo_http, 
                        tiempo_respuesta_ms, codigo_respuesta
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                ''', [
                    'INFO', 'DEMO', 'SYSTEM_TEST',
                    'Demostración del sistema de auditoría funcionando correctamente',
                    1, str(uuid.uuid4()), '127.0.0.1',
                    json.dumps({'demo_mode': True, 'test_timestamp': 'now'}),
                    'auditoria', '/demo/', 'GET', 250, 200
                ])
                self.stdout.write('✅ Log del sistema registrado directamente')
        except Exception as e:
            self.stdout.write(f'❌ Error registrando log del sistema: {e}')
        
        # 2. Log de navegación directo
        try:
            session_id = str(uuid.uuid4())
            with connection.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO logs.navegacion_usuarios (
                        usuario_id, session_id, url_visitada, url_anterior,
                        metodo_http, accion_realizada, ip_address
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                ''', [
                    1, session_id, '/demo/auditoria/', '/admin/',
                    'GET', 'DEMO_VISIT', '127.0.0.1'
                ])
                self.stdout.write('✅ Log de navegación registrado directamente')
        except Exception as e:
            self.stdout.write(f'❌ Error registrando log de navegación: {e}')
        
        # 3. Probar auditoría automática con triggers
        try:
            user, created = User.objects.get_or_create(
                username='demo_audit_user',
                defaults={
                    'email': 'demo@actas.municipales',
                    'first_name': 'Usuario',
                    'last_name': 'Demo Auditoría'
                }
            )
            
            if created:
                self.stdout.write(f'✅ Usuario demo creado (ID: {user.id}) - Trigger de auditoría ejecutado')
            else:
                # Actualizar para generar cambio
                user.first_name = f'Usuario Demo {uuid.uuid4().hex[:8]}'
                user.save()
                self.stdout.write(f'✅ Usuario demo actualizado (ID: {user.id}) - Trigger de auditoría ejecutado')
                
        except Exception as e:
            self.stdout.write(f'❌ Error en prueba de triggers: {e}')
        
        # 4. Log de API usando AuditoriaLogger
        try:
            logger.registrar_log_api(
                endpoint='/api/demo',
                metodo_http='POST',
                usuario_id=1,
                parametros_query={'demo': True},
                payload_response={'status': 'success'},
                codigo_respuesta=200,
                tiempo_respuesta_ms=150,
                ip_address='127.0.0.1'
            )
            self.stdout.write('✅ Log de API registrado usando AuditoriaLogger')
        except Exception as e:
            self.stdout.write(f'❌ Error registrando log de API: {e}')
        
        # 5. Log de errores
        try:
            logger.registrar_error(
                mensaje_error='Error de demostración - No es un error real',
                codigo_error='DEMO_ERROR',
                stack_trace='Demo traceback for testing',
                usuario_id=1,
                nivel_error='INFO',
                contexto_aplicacion={'demo_error': True}
            )
            self.stdout.write('✅ Log de error registrado usando AuditoriaLogger')
        except Exception as e:
            self.stdout.write(f'❌ Error registrando log de error: {e}')
        
        # 6. Verificar estadísticas
        self.mostrar_estadisticas()
        
        self.stdout.write('\n🎉 ¡Demostración del sistema de auditoría completada!')
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas del sistema de auditoría"""
        try:
            estadisticas = AuditoriaLogger().obtener_estadisticas_hoy()
            
            self.stdout.write('\n📊 Estadísticas del día de hoy:')
            self.stdout.write(f'   - Logs del sistema: {estadisticas.get("logs_sistema", 0)}')
            self.stdout.write(f'   - Logs de navegación: {estadisticas.get("navegacion", 0)}')
            self.stdout.write(f'   - Cambios en BD (triggers): {estadisticas.get("cambios_bd", 0)}')
            self.stdout.write(f'   - Logs de API: {estadisticas.get("api_calls", 0)}')
            self.stdout.write(f'   - Logs de errores: {estadisticas.get("errores", 0)}')
            self.stdout.write(f'   - Logs de accesos: {estadisticas.get("accesos", 0)}')
            self.stdout.write(f'   - Tasks de Celery: {estadisticas.get("celery_tasks", 0)}')
                
        except Exception as e:
            self.stdout.write(f'❌ Error obteniendo estadísticas: {e}')
