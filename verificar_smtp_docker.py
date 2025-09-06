#!/usr/bin/env python
"""
Verificar configuración SMTP en PostgreSQL
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.config_system.models import ConfiguracionSMTP
from apps.config_system.smtp_service import smtp_service

print('📧 === VERIFICANDO CONFIGURACIÓN SMTP EN POSTGRESQL ===')
print()

# Mostrar configuraciones
configs = ConfiguracionSMTP.objects.all()
for config in configs:
    print(f'✅ {config.nombre}')
    print(f'   Proveedor: {config.get_proveedor_display()}')
    print(f'   Servidor: {config.servidor_smtp}:{config.puerto}')
    print(f'   Usuario: {config.usuario_smtp}')
    print(f'   Remitente: {config.email_remitente}')
    activo_icon = "🟢" if config.activo else "🔴"
    default_icon = "⭐" if config.por_defecto else "⚪"
    print(f'   Activo: {activo_icon}')
    print(f'   Por defecto: {default_icon}')
    print()

# Probar estadísticas del servicio
try:
    stats = smtp_service.get_estadisticas_envio()
    print(f'📊 Proveedores activos: {stats["proveedores_activos"]}')
    if stats["proveedor_por_defecto"]:
        print(f'⭐ Proveedor por defecto: {stats["proveedor_por_defecto"].nombre}')
    print()
except Exception as e:
    print(f'❌ Error obteniendo estadísticas: {e}')

print('🎉 ¡Configuración verificada en PostgreSQL!')
