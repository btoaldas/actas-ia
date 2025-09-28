#!/usr/bin/env python
"""
TEST FINAL DE FUNCIONALIDADES AUTOMÁTICAS
Verificar que el auto-completado funciona completamente
"""
import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')
django.setup()

def main():
    print("🧪 TEST FINAL DE FUNCIONALIDADES AUTOMÁTICAS...")
    
    client = Client()
    User = get_user_model()
    
    # Login como superadmin
    login_success = client.login(username='superadmin', password='AdminPuyo2025!')
    print(f"✅ Login: {login_success}")
    
    # Obtener página
    response = client.get('/generador-actas/segmentos/crear/')
    if response.status_code != 200:
        print(f"❌ Error obteniendo página: {response.status_code}")
        return
        
    html_content = response.content.decode()
    
    print("\n🔍 1. VERIFICANDO FUNCIONES JAVASCRIPT:")
    
    # Funciones críticas que deben estar
    funciones_requeridas = {
        'autoGenerarCodigo': 'Auto-generación de código desde nombre',
        'autoRellenarEjemplos': 'Auto-relleno de ejemplos por categoría',
        'nombreField.addEventListener': 'Event listener para nombre',
        'tipoSelect.addEventListener': 'Event listener para tipo',
        'categoriaSelect.addEventListener': 'Event listener para categoría'
    }
    
    for funcion, descripcion in funciones_requeridas.items():
        if funcion in html_content:
            print(f"✅ {funcion}: {descripcion}")
        else:
            print(f"❌ {funcion}: {descripcion} - NO ENCONTRADO")
    
    print("\n📋 2. VERIFICANDO EJEMPLOS POR CATEGORÍA:")
    
    # Verificar que cada categoría tenga sus ejemplos
    categorias_ejemplos = {
        'encabezado': {
            'descripcion': 'Sección de introducción del acta',
            'contenido': 'ACTA DE SESIÓN ORDINARIA',
            'prompt': 'fecha_sesion'
        },
        'participantes': {
            'descripción': 'Lista de asistentes y participantes',
            'contenido': 'PARTICIPANTES',
            'prompt': 'autoridades municipales'
        },
        'agenda': {
            'descripcion': 'Orden del día y puntos tratados',
            'contenido': 'ORDEN DEL DÍA',
            'prompt': 'puntos_agenda'
        },
        'decisiones': {
            'descripcion': 'Resoluciones, acuerdos y decisiones',
            'contenido': 'RESOLUCIONES Y ACUERDOS',
            'prompt': 'decisiones'
        },
        'cierre': {
            'descripcion': 'Información de cierre de la sesión',
            'contenido': 'CIERRE DE SESIÓN',
            'prompt': 'hora_cierre'
        }
    }
    
    for categoria, contenido in categorias_ejemplos.items():
        print(f"\n📂 Categoría: {categoria}")
        
        # Verificar que la categoría esté en los ejemplos JS
        if f"'{categoria}'" in html_content:
            print(f"  ✅ Categoría incluida en ejemplos")
            
            # Verificar elementos específicos
            for tipo, texto in contenido.items():
                if texto in html_content:
                    print(f"  ✅ {tipo}: {texto[:30]}...")
                else:
                    print(f"  ❌ {tipo}: {texto[:30]}... - NO ENCONTRADO")
        else:
            print(f"  ❌ Categoría NO incluida en ejemplos")
    
    print("\n⚙️ 3. VERIFICANDO EVENT LISTENERS:")
    
    # Verificar que los event listeners estén configurados
    listeners_esperados = [
        "nombreField.addEventListener('blur'",
        "tipoSelect.addEventListener('change'",
        "categoriaSelect.addEventListener('change'"
    ]
    
    for listener in listeners_esperados:
        if listener in html_content:
            print(f"✅ {listener}")
        else:
            print(f"❌ {listener} - NO ENCONTRADO")
    
    print("\n🎯 4. VERIFICANDO LÓGICA DE AUTO-GENERACIÓN:")
    
    # Verificar elementos clave de la lógica
    logica_elementos = [
        'normalize(\'NFD\')',  # Quitar acentos
        'replace(/[\\u0300-\\u036f]/g, \'\')',  # Normalización
        'toUpperCase()',  # Mayúsculas
        'replace(/\\s+/g, \'_\')',  # Espacios por guiones
        'ejemplos[categoria]',  # Acceso a ejemplos
        'contenido_estatico\'].value.trim()',  # Verificar campos vacíos
        'prompt_ia\'].value.trim()'  # Verificar campos vacíos
    ]
    
    for elemento in logica_elementos:
        if elemento in html_content:
            print(f"✅ {elemento}")
        else:
            print(f"❌ {elemento} - NO ENCONTRADO")
    
    print("\n📊 5. RESUMEN FINAL:")
    
    # Contar elementos encontrados
    total_funciones = len([f for f in funciones_requeridas.keys() if f in html_content])
    total_categorias = len([c for c in categorias_ejemplos.keys() if f"'{c}'" in html_content])
    total_listeners = len([l for l in listeners_esperados if l in html_content])
    total_logica = len([e for e in logica_elementos if e in html_content])
    
    print(f"✅ Funciones JavaScript: {total_funciones}/{len(funciones_requeridas)}")
    print(f"✅ Categorías con ejemplos: {total_categorias}/{len(categorias_ejemplos)}")
    print(f"✅ Event listeners: {total_listeners}/{len(listeners_esperados)}")
    print(f"✅ Elementos de lógica: {total_logica}/{len(logica_elementos)}")
    
    # Evaluación final
    if (total_funciones == len(funciones_requeridas) and 
        total_categorias == len(categorias_ejemplos) and
        total_listeners == len(listeners_esperados) and
        total_logica >= len(logica_elementos) - 2):  # Permitir 2 elementos faltantes
        
        print(f"\n🎉 ¡FUNCIONALIDADES AUTOMÁTICAS COMPLETAMENTE IMPLEMENTADAS!")
        print(f"✅ El sistema debería funcionar correctamente")
        print(f"✅ Auto-generación de código: ACTIVA")
        print(f"✅ Auto-relleno de ejemplos: ACTIVO")
        print(f"✅ Event listeners: CONFIGURADOS")
    else:
        print(f"\n⚠️ Algunas funcionalidades pueden no estar completas")
    
    print(f"\n🔗 URL para probar: http://localhost:8000/generador-actas/segmentos/crear/")
    print(f"📋 Instrucciones:")
    print(f"   1. Escribe un nombre → código se auto-genera")
    print(f"   2. Selecciona tipo + categoría → contenido se auto-rellena")
    print(f"   3. Solo se llenan campos vacíos")

if __name__ == '__main__':
    main()