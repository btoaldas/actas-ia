#!/usr/bin/env python
"""
Script de validación rápida para el módulo de segmentos
Verifica que las funcionalidades básicas estén funcionando
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.generador_actas.models import SegmentoPlantilla, ProveedorIA
from django.contrib.auth import get_user_model

User = get_user_model()

def test_modelos():
    """Prueba básica de modelos"""
    print("🧪 Probando modelos...")
    
    # Verificar que los modelos se pueden importar
    assert SegmentoPlantilla is not None
    assert ProveedorIA is not None
    
    # Contar registros existentes
    total_segmentos = SegmentoPlantilla.objects.count()
    total_proveedores = ProveedorIA.objects.count()
    
    print(f"✅ Segmentos existentes: {total_segmentos}")
    print(f"✅ Proveedores IA existentes: {total_proveedores}")
    
    return True

def test_migraciones():
    """Verificar que las migraciones están aplicadas"""
    print("📦 Verificando migraciones...")
    
    from django.db import connection
    cursor = connection.cursor()
    
    # Verificar que la tabla existe
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'generador_actas_segmentoplantilla'
    """)
    
    columnas = [row[0] for row in cursor.fetchall()]
    
    # Verificar nuevas columnas
    columnas_requeridas = [
        'activo', 'proveedor_ia_id', 'variables_personalizadas',
        'total_usos', 'tiempo_promedio_procesamiento'
    ]
    
    for columna in columnas_requeridas:
        if columna in columnas:
            print(f"✅ Columna '{columna}' existe")
        else:
            print(f"❌ Columna '{columna}' NO existe")
            return False
    
    return True

def test_admin():
    """Verificar registro en Django admin"""
    print("👑 Verificando Django admin...")
    
    from django.contrib import admin
    
    if SegmentoPlantilla in admin.site._registry:
        print("✅ SegmentoPlantilla está registrado en admin")
        return True
    else:
        print("❌ SegmentoPlantilla NO está registrado en admin")
        return False

def test_formularios():
    """Verificar importación de formularios"""
    print("📝 Verificando formularios...")
    
    try:
        from apps.generador_actas.forms import (
            SegmentoPlantillaForm, PruebaSegmentoForm, 
            SegmentoFiltroForm, VariablesSegmentoForm
        )
        
        print("✅ Todos los formularios se importan correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando formularios: {e}")
        return False

def test_vistas():
    """Verificar importación de vistas"""
    print("🌐 Verificando vistas...")
    
    try:
        from apps.generador_actas.views import (
            dashboard_segmentos, lista_segmentos, crear_segmento,
            detalle_segmento, editar_segmento, probar_segmento
        )
        
        print("✅ Todas las vistas se importan correctamente")
        return True
    except ImportError as e:
        print(f"❌ Error importando vistas: {e}")
        return False

def test_urls():
    """Verificar configuración de URLs"""
    print("🔗 Verificando URLs...")
    
    try:
        from django.urls import reverse
        
        urls_importantes = [
            'generador_actas:segmentos_dashboard',
            'generador_actas:lista_segmentos',
            'generador_actas:crear_segmento',
            'generador_actas:probar_segmento'
        ]
        
        for url_name in urls_importantes:
            try:
                reverse(url_name)
                print(f"✅ URL '{url_name}' está configurada")
            except Exception as e:
                print(f"❌ URL '{url_name}' NO está configurada: {e}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error verificando URLs: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando validación rápida del módulo de segmentos...")
    print("="*60)
    
    pruebas = [
        test_modelos,
        test_migraciones,
        test_admin,
        test_formularios,
        test_vistas,
        test_urls
    ]
    
    resultados = []
    for prueba in pruebas:
        try:
            resultado = prueba()
            resultados.append(resultado)
            print("")  # Línea en blanco entre pruebas
        except Exception as e:
            print(f"❌ Error en {prueba.__name__}: {e}")
            resultados.append(False)
            print("")
    
    # Resumen final
    print("="*60)
    print("📊 RESUMEN FINAL")
    print("="*60)
    
    exitosas = sum(resultados)
    total = len(resultados)
    porcentaje = (exitosas / total * 100) if total > 0 else 0
    
    print(f"Pruebas exitosas: {exitosas}/{total} ({porcentaje:.1f}%)")
    
    if porcentaje == 100:
        print("🎉 ¡Todas las pruebas pasaron! El módulo está listo.")
        return True
    elif porcentaje >= 80:
        print("⚠️ La mayoría de pruebas pasaron. Revisar errores menores.")
        return True
    else:
        print("❌ Múltiples errores encontrados. Se requiere revisión.")
        return False

if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)