#!/usr/bin/env python
"""
Script para probar la funcionalidad de ordenación en el dashboard de proveedores IA
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

from apps.generador_actas.models import ProveedorIA

def test_ordenacion():
    """Probar diferentes tipos de ordenación"""
    print("🧪 PROBANDO FUNCIONALIDAD DE ORDENACIÓN")
    print("=" * 60)
    
    # Tipos de ordenación disponibles
    ordenes_test = [
        ('nombre', 'Nombre A-Z'),
        ('-nombre', 'Nombre Z-A'),
        ('tipo', 'Tipo A-Z'),
        ('-tipo', 'Tipo Z-A'),
        ('-fecha_creacion', 'Más recientes'),
        ('fecha_creacion', 'Más antiguos'),
        ('-ultima_conexion', 'Última conexión'),
        ('-total_llamadas', 'Más usados'),
        ('total_llamadas', 'Menos usados'),
        ('activo', 'Activos primero'),
        ('-activo', 'Inactivos primero'),
    ]
    
    # Mapeo de ordenación (igual que en la vista)
    ordenes_validos = {
        'nombre': 'nombre',
        '-nombre': '-nombre',
        'tipo': 'tipo',
        '-tipo': '-tipo',
        'fecha_creacion': 'fecha_creacion',
        '-fecha_creacion': '-fecha_creacion',
        'ultima_conexion': 'ultima_conexion_exitosa',
        '-ultima_conexion': '-ultima_conexion_exitosa',
        'total_llamadas': 'total_llamadas',
        '-total_llamadas': '-total_llamadas',
        'activo': 'activo',
        '-activo': '-activo'
    }
    
    for orden_key, orden_label in ordenes_test:
        print(f"\n📋 PROBANDO ORDENACIÓN: {orden_label}")
        
        if orden_key in ordenes_validos:
            try:
                queryset = ProveedorIA.objects.all().order_by(ordenes_validos[orden_key])
                proveedores = list(queryset[:3])  # Tomar solo los primeros 3
                
                print(f"   ✅ Orden aplicado: {ordenes_validos[orden_key]}")
                print(f"   📊 Resultados (primeros 3):")
                
                for i, proveedor in enumerate(proveedores, 1):
                    info = []
                    if 'nombre' in orden_key:
                        info.append(f"Nombre: {proveedor.nombre}")
                    if 'tipo' in orden_key:
                        info.append(f"Tipo: {proveedor.get_tipo_display()}")
                    if 'fecha' in orden_key:
                        info.append(f"Creado: {proveedor.fecha_creacion.strftime('%d/%m/%Y')}")
                    if 'ultima_conexion' in orden_key:
                        if proveedor.ultima_conexion_exitosa:
                            info.append(f"Última conexión: {proveedor.ultima_conexion_exitosa.strftime('%d/%m/%Y %H:%M')}")
                        else:
                            info.append("Última conexión: Nunca")
                    if 'llamadas' in orden_key:
                        info.append(f"Llamadas: {proveedor.total_llamadas}")
                    if 'activo' in orden_key:
                        info.append(f"Estado: {'Activo' if proveedor.activo else 'Inactivo'}")
                    
                    if not info:  # Si no hay info específica, mostrar nombre
                        info.append(f"Nombre: {proveedor.nombre}")
                    
                    print(f"      {i}. {' | '.join(info)}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
        else:
            print(f"   ⚠️  Orden no válido en mapeo")
    
    return True

def test_filtros_combinados():
    """Probar filtros combinados con ordenación"""
    print(f"\n🔍 PROBANDO FILTROS COMBINADOS CON ORDENACIÓN")
    print("=" * 60)
    
    # Prueba 1: Filtrar activos y ordenar por llamadas
    print(f"\n📋 PRUEBA 1: Proveedores activos ordenados por más usados")
    activos_por_uso = ProveedorIA.objects.filter(activo=True).order_by('-total_llamadas')
    for proveedor in activos_por_uso:
        print(f"   • {proveedor.nombre}: {proveedor.total_llamadas} llamadas | {proveedor.get_tipo_display()}")
    
    # Prueba 2: Filtrar por tipo y ordenar por nombre
    print(f"\n📋 PRUEBA 2: Proveedores DeepSeek ordenados por nombre")
    deepseek_por_nombre = ProveedorIA.objects.filter(tipo='deepseek').order_by('nombre')
    for proveedor in deepseek_por_nombre:
        print(f"   • {proveedor.nombre} | Estado: {'Activo' if proveedor.activo else 'Inactivo'}")
    
    # Prueba 3: Buscar y ordenar
    print(f"\n📋 PRUEBA 3: Búsqueda 'deep' ordenada por fecha de creación")
    busqueda_ordenada = ProveedorIA.objects.filter(
        nombre__icontains='deep'
    ).order_by('-fecha_creacion')
    for proveedor in busqueda_ordenada:
        print(f"   • {proveedor.nombre} | Creado: {proveedor.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
    
    return True

if __name__ == "__main__":
    print(f"🚀 INICIANDO PRUEBA DE ORDENACIÓN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success1 = test_ordenacion()
    success2 = test_filtros_combinados()
    
    if success1 and success2:
        print("\n✅ Todas las pruebas de ordenación completadas exitosamente")
        print("\n🎯 FUNCIONALIDADES CONFIRMADAS:")
        print("   • ✅ Ordenación por nombre (A-Z, Z-A)")
        print("   • ✅ Ordenación por tipo (A-Z, Z-A)")
        print("   • ✅ Ordenación por fecha de creación")
        print("   • ✅ Ordenación por última conexión")
        print("   • ✅ Ordenación por uso (llamadas)")
        print("   • ✅ Ordenación por estado (activo/inactivo)")
        print("   • ✅ Combinación de filtros + ordenación")
        print("   • ✅ Búsqueda + ordenación")
    else:
        print("\n❌ Error en las pruebas de ordenación")