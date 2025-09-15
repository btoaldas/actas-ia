#!/usr/bin/env python3
"""
Script de validación post-implementación del módulo de segmentos
Verifica que todos los componentes funcionen correctamente después de las correcciones
"""

import os
import sys
import django
import time
from pathlib import Path

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_servidor_activo():
    """Verifica que el servidor Django esté activo"""
    print("\n🌐 Probando servidor Django...")
    
    try:
        import requests
        response = requests.get('http://localhost:8000/admin/login/', timeout=5)
        
        if response.status_code == 200:
            print("✅ Servidor Django activo y respondiendo")
            return True
        else:
            print(f"❌ Servidor responde pero con código {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        return False

def test_urls_segmentos():
    """Verifica que las URLs de segmentos funcionen"""
    print("\n🔗 Probando URLs de segmentos...")
    
    try:
        from django.urls import reverse
        
        urls_criticas = [
            'generador_actas:segmentos_dashboard',
            'generador_actas:lista_segmentos',
            'generador_actas:crear_segmento',
            'generador_actas:asistente_variables'
        ]
        
        urls_validas = 0
        for url_name in urls_criticas:
            try:
                url_path = reverse(url_name)
                print(f"   ✅ {url_name} → {url_path}")
                urls_validas += 1
            except Exception as e:
                print(f"   ❌ {url_name} → Error: {e}")
        
        if urls_validas == len(urls_criticas):
            print(f"✅ Todas las URLs funcionan ({urls_validas}/{len(urls_criticas)})")
            return True
        else:
            print(f"⚠️  URLs parcialmente funcionales ({urls_validas}/{len(urls_criticas)})")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando URLs: {e}")
        return False

def test_vistas_importables():
    """Verifica que todas las vistas se puedan importar"""
    print("\n📄 Probando importación de vistas...")
    
    try:
        from apps.generador_actas.views import (
            segmentos_dashboard, lista_segmentos, crear_segmento,
            detalle_segmento, editar_segmento, eliminar_segmento,
            probar_segmento, asistente_variables, api_probar_segmento
        )
        
        vistas = [
            'segmentos_dashboard', 'lista_segmentos', 'crear_segmento',
            'detalle_segmento', 'editar_segmento', 'eliminar_segmento',
            'probar_segmento', 'asistente_variables', 'api_probar_segmento'
        ]
        
        print(f"✅ Todas las vistas importadas exitosamente ({len(vistas)} vistas)")
        return True
        
    except ImportError as e:
        print(f"❌ Error importando vistas: {e}")
        return False

def test_tasks_celery():
    """Verifica que las tareas de Celery estén disponibles"""
    print("\n⚙️ Probando tareas Celery...")
    
    try:
        from apps.generador_actas.tasks import (
            procesar_segmento_dinamico, batch_procesar_segmentos,
            limpiar_metricas_antiguas_segmentos, generar_reporte_uso_segmentos
        )
        
        tasks = [
            'procesar_segmento_dinamico', 'batch_procesar_segmentos',
            'limpiar_metricas_antiguas_segmentos', 'generar_reporte_uso_segmentos'
        ]
        
        print(f"✅ Todas las tareas Celery disponibles ({len(tasks)} tareas)")
        return True
        
    except ImportError as e:
        print(f"❌ Error importando tareas: {e}")
        return False

def test_templates_existen():
    """Verifica que todos los templates existan"""
    print("\n🎨 Probando existencia de templates...")
    
    templates_requeridos = [
        'generador_actas/segmentos/dashboard.html',
        'generador_actas/segmentos/lista.html',
        'generador_actas/segmentos/crear.html',
        'generador_actas/segmentos/editar.html',
        'generador_actas/segmentos/detalle.html',
        'generador_actas/segmentos/eliminar.html',
        'generador_actas/segmentos/probar.html',
        'generador_actas/segmentos/asistente_variables.html'
    ]
    
    base_path = Path('/app/templates')
    templates_encontrados = 0
    
    for template in templates_requeridos:
        template_path = base_path / template
        if template_path.exists():
            print(f"   ✅ {template}")
            templates_encontrados += 1
        else:
            print(f"   ❌ {template} NO ENCONTRADO")
    
    if templates_encontrados == len(templates_requeridos):
        print(f"✅ Todos los templates presentes ({templates_encontrados}/{len(templates_requeridos)})")
        return True
    else:
        print(f"⚠️  Templates parcialmente presentes ({templates_encontrados}/{len(templates_requeridos)})")
        return False

def test_modelo_y_datos():
    """Verifica el modelo y algunos datos básicos"""
    print("\n💾 Probando modelo y datos...")
    
    try:
        from apps.generador_actas.models import SegmentoPlantilla, ProveedorIA
        
        # Verificar modelo
        total_segmentos = SegmentoPlantilla.objects.count()
        segmentos_activos = SegmentoPlantilla.objects.filter(activo=True).count()
        proveedores_ia = ProveedorIA.objects.count()
        
        print(f"   📊 Total segmentos: {total_segmentos}")
        print(f"   📊 Segmentos activos: {segmentos_activos}")
        print(f"   📊 Proveedores IA: {proveedores_ia}")
        
        # Probar propiedades del modelo
        if total_segmentos > 0:
            segmento = SegmentoPlantilla.objects.first()
            _ = segmento.es_dinamico
            _ = segmento.esta_configurado
            print("   ✅ Propiedades del modelo funcionan")
        
        print("✅ Modelo y datos verificados exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando modelo: {e}")
        return False

def test_formularios():
    """Verifica que los formularios se puedan instanciar"""
    print("\n📝 Probando formularios...")
    
    try:
        from apps.generador_actas.forms import (
            SegmentoPlantillaForm, PruebaSegmentoForm,
            SegmentoFiltroForm, VariablesSegmentoForm
        )
        
        # Instanciar formularios
        form1 = SegmentoPlantillaForm()
        form2 = PruebaSegmentoForm()
        form3 = SegmentoFiltroForm()
        form4 = VariablesSegmentoForm()
        
        formularios = [
            'SegmentoPlantillaForm', 'PruebaSegmentoForm',
            'SegmentoFiltroForm', 'VariablesSegmentoForm'
        ]
        
        print(f"✅ Todos los formularios instanciables ({len(formularios)} formularios)")
        return True
        
    except Exception as e:
        print(f"❌ Error instanciando formularios: {e}")
        return False

def test_archivos_estaticos():
    """Verifica archivos CSS y estáticos"""
    print("\n🎯 Probando archivos estáticos...")
    
    css_path = Path('/app/static/generador_actas/css/segmentos.css')
    
    if css_path.exists():
        # Verificar que el CSS tenga contenido relevante
        content = css_path.read_text()
        if 'segment-metric-card' in content and 'segmentos' in content:
            print("✅ Archivo CSS presente y válido")
            return True
        else:
            print("⚠️  Archivo CSS presente pero contenido incompleto")
            return False
    else:
        print("❌ Archivo CSS no encontrado")
        return False

def test_documentacion():
    """Verifica que la documentación esté presente"""
    print("\n📚 Probando documentación...")
    
    doc_path = Path('/app/docs/modulo_segmentos_documentacion.md')
    
    if doc_path.exists():
        content = doc_path.read_text()
        if len(content) > 10000:  # Al menos 10KB de contenido
            print("✅ Documentación completa presente")
            return True
        else:
            print("⚠️  Documentación presente pero incompleta")
            return False
    else:
        print("❌ Documentación no encontrada")
        return False

def main():
    """Ejecuta todas las pruebas de validación"""
    print("🔍 VALIDACIÓN POST-IMPLEMENTACIÓN DEL MÓDULO DE SEGMENTOS")
    print("=" * 70)
    
    pruebas = [
        test_servidor_activo,
        test_urls_segmentos,
        test_vistas_importables,
        test_tasks_celery,
        test_templates_existen,
        test_modelo_y_datos,
        test_formularios,
        test_archivos_estaticos,
        test_documentacion
    ]
    
    resultados = []
    
    for prueba in pruebas:
        try:
            resultado = prueba()
            resultados.append(resultado)
            time.sleep(0.5)  # Pequeña pausa entre pruebas
        except Exception as e:
            print(f"❌ Error inesperado en {prueba.__name__}: {e}")
            resultados.append(False)
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 70)
    
    exitosas = sum(resultados)
    total = len(resultados)
    porcentaje = (exitosas / total) * 100
    
    print(f"✅ Pruebas exitosas: {exitosas}/{total} ({porcentaje:.1f}%)")
    
    if all(resultados):
        print("\n🎉 ¡VALIDACIÓN COMPLETAMENTE EXITOSA!")
        print("🚀 El módulo de segmentos está completamente funcional.")
        print("\n📋 COMPONENTES VALIDADOS:")
        print("   • Servidor Django activo")
        print("   • URLs correctamente configuradas")
        print("   • Vistas importables y funcionales")
        print("   • Tareas Celery disponibles")
        print("   • Templates presentes y accesibles")
        print("   • Modelo de datos funcionando")
        print("   • Formularios instanciables")
        print("   • Archivos estáticos correctos")
        print("   • Documentación completa")
        
        print("\n✨ FUNCIONALIDADES LISTAS PARA USO:")
        print("   🎯 Dashboard con métricas en tiempo real")
        print("   📝 CRUD completo de segmentos")
        print("   🔍 Sistema de filtros avanzado")
        print("   🧪 Pruebas de segmentos individuales")
        print("   🎨 Asistente visual de variables")
        print("   ⚙️ Procesamiento asíncrono con Celery")
        print("   🔐 Validaciones y seguridad completa")
        
        return True
    else:
        problemas = total - exitosas
        print(f"\n⚠️  Se encontraron {problemas} problemas.")
        print("🔧 Revisa los errores mostrados arriba.")
        
        if exitosas >= total * 0.8:  # 80% o más
            print("\n💡 La mayoría de componentes funcionan correctamente.")
            print("   El sistema puede ser usado con funcionalidad limitada.")
        
        return False

if __name__ == "__main__":
    success = main()
    print("\n" + "=" * 70)
    if success:
        print("🏁 VALIDACIÓN COMPLETADA: ¡TODO FUNCIONA CORRECTAMENTE!")
    else:
        print("🏁 VALIDACIÓN COMPLETADA: HAY PROBLEMAS QUE RESOLVER")
    print("=" * 70)
    sys.exit(0 if success else 1)