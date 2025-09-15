#!/usr/bin/env python
"""
Script para probar las métricas mejoradas del dashboard de proveedores IA
"""
import os
import sys
import django
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append('/app')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models import Sum
from apps.generador_actas.models import ProveedorIA

def test_metricas():
    """Probar el cálculo de métricas"""
    print("🧪 PROBANDO MÉTRICAS DEL DASHBOARD")
    print("=" * 60)
    
    # Obtener todos los proveedores
    todos_proveedores = ProveedorIA.objects.all()
    
    # Métricas básicas
    total_proveedores = todos_proveedores.count()
    activos = todos_proveedores.filter(activo=True).count()
    inactivos = todos_proveedores.filter(activo=False).count()
    con_errores = todos_proveedores.exclude(ultimo_error='').count()
    
    print(f"📊 MÉTRICAS BÁSICAS:")
    print(f"   • Total Proveedores: {total_proveedores}")
    print(f"   • Activos: {activos}")
    print(f"   • Inactivos: {inactivos}")
    print(f"   • Con Errores: {con_errores}")
    
    # Métricas avanzadas
    sin_configurar = sum(1 for p in todos_proveedores if not p.esta_configurado)
    total_llamadas_global = todos_proveedores.aggregate(
        total=Sum('total_llamadas')
    )['total'] or 0
    total_tokens_global = todos_proveedores.aggregate(
        total=Sum('total_tokens_usados')
    )['total'] or 0
    
    print(f"\n📈 MÉTRICAS AVANZADAS:")
    print(f"   • Sin configurar: {sin_configurar}")
    print(f"   • Total llamadas globales: {total_llamadas_global}")
    print(f"   • Total tokens globales: {total_tokens_global}")
    
    # Distribución por tipo
    print(f"\n🔧 DISTRIBUCIÓN POR TIPO:")
    tipos_stats = {}
    for tipo_code, tipo_name in ProveedorIA.TIPO_PROVEEDOR:
        count = todos_proveedores.filter(tipo=tipo_code).count()
        activos_tipo = todos_proveedores.filter(tipo=tipo_code, activo=True).count()
        if count > 0:
            porcentaje = round((count / total_proveedores) * 100, 1) if total_proveedores > 0 else 0
            tipos_stats[tipo_code] = {
                'nombre': tipo_name,
                'total': count,
                'activos': activos_tipo,
                'porcentaje': porcentaje
            }
            print(f"   • {tipo_name}: {activos_tipo}/{count} ({porcentaje}%)")
    
    # Proveedor más usado
    proveedor_mas_usado = todos_proveedores.filter(total_llamadas__gt=0).order_by('-total_llamadas').first()
    if proveedor_mas_usado:
        print(f"\n🏆 PROVEEDOR MÁS USADO:")
        print(f"   • Nombre: {proveedor_mas_usado.nombre}")
        print(f"   • Tipo: {proveedor_mas_usado.get_tipo_display()}")
        print(f"   • Llamadas: {proveedor_mas_usado.total_llamadas}")
        print(f"   • Tokens: {proveedor_mas_usado.total_tokens_usados}")
    else:
        print(f"\n🏆 PROVEEDOR MÁS USADO: Ninguno (sin llamadas registradas)")
    
    # Últimas conexiones
    ultimas_conexiones = todos_proveedores.exclude(
        ultima_conexion_exitosa__isnull=True
    ).order_by('-ultima_conexion_exitosa')[:5]
    
    print(f"\n🕒 ÚLTIMAS CONEXIONES:")
    if ultimas_conexiones:
        for proveedor in ultimas_conexiones:
            print(f"   • {proveedor.nombre} - {proveedor.ultima_conexion_exitosa.strftime('%d/%m/%Y %H:%M')}")
    else:
        print(f"   • No hay conexiones registradas")
    
    # Resumen de configuración
    print(f"\n⚙️  ESTADO DE CONFIGURACIÓN:")
    for proveedor in todos_proveedores:
        estado = "✅ OK" if proveedor.esta_configurado else "❌ Sin configurar"
        activo_estado = "🟢 Activo" if proveedor.activo else "🔴 Inactivo"
        print(f"   • {proveedor.nombre}: {estado} | {activo_estado}")
    
    return True

if __name__ == "__main__":
    print(f"🚀 INICIANDO PRUEBA DE MÉTRICAS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_metricas()
    
    if success:
        print("\n✅ Prueba de métricas completada exitosamente")
    else:
        print("\n❌ Error en la prueba de métricas")
    
    print("\n📋 NOTA: Las métricas del dashboard ahora incluyen:")
    print("   • Estadísticas básicas actualizadas dinámicamente")
    print("   • Métricas avanzadas (errores, sin configurar, tokens, llamadas)")
    print("   • Distribución por tipo de proveedor")
    print("   • Proveedor más usado")
    print("   • Historial de últimas conexiones")
    print("   • Ordenación por múltiples criterios")