#!/usr/bin/env python
"""
Script de diagnóstico para verificar la búsqueda normalizada en la base de datos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models import Q
from apps.pages.models import ActaMunicipal
from helpers.util import normalizar_busqueda

def diagnosticar_busqueda():
    """Diagnosticar problemas de búsqueda normalizada"""
    print("🔍 Diagnóstico de búsqueda normalizada")
    print("=" * 50)
    
    # 1. Verificar si hay datos con acentos
    print("\n1️⃣ Verificando datos con acentos en la base de datos:")
    actas_con_acentos = ActaMunicipal.objects.filter(
        Q(titulo__icontains='ó') | Q(titulo__icontains='á') | 
        Q(titulo__icontains='é') | Q(titulo__icontains='í') | 
        Q(titulo__icontains='ú') | Q(titulo__icontains='ñ')
    )[:5]
    
    if actas_con_acentos.exists():
        print(f"✅ Encontradas {actas_con_acentos.count()} actas con acentos:")
        for acta in actas_con_acentos:
            print(f"   - ID {acta.id}: {acta.titulo}")
    else:
        print("❌ No se encontraron actas con acentos en los títulos")
    
    # 2. Buscar específicamente "Fundación"
    print("\n2️⃣ Buscando específicamente 'Fundación':")
    actas_fundacion = ActaMunicipal.objects.filter(titulo__icontains='Fundación')
    print(f"   Resultados con 'Fundación': {actas_fundacion.count()}")
    for acta in actas_fundacion[:3]:
        print(f"   - ID {acta.id}: {acta.titulo}")
    
    # 3. Buscar con normalización actual
    print("\n3️⃣ Probando búsqueda normalizada:")
    busqueda_original = "fundacion"
    busqueda_normalizada = normalizar_busqueda(busqueda_original)
    
    print(f"   Término original: '{busqueda_original}'")
    print(f"   Término normalizado: '{busqueda_normalizada}'")
    
    # Probar búsqueda actual (como está implementada)
    filtros_busqueda = Q()
    campos_busqueda = ['titulo', 'numero_acta', 'resumen', 'contenido', 'palabras_clave', 'presidente']
    
    for campo in campos_busqueda:
        filtros_busqueda |= Q(**{f"{campo}__icontains": busqueda_original})
        if busqueda_normalizada != busqueda_original.lower():
            filtros_busqueda |= Q(**{f"{campo}__icontains": busqueda_normalizada})
    
    resultados_actuales = ActaMunicipal.objects.filter(filtros_busqueda)
    print(f"   Resultados con método actual: {resultados_actuales.count()}")
    
    # 4. Probar búsqueda directa por campo
    print("\n4️⃣ Pruebas por campo individual:")
    for campo in ['titulo', 'resumen', 'contenido']:
        if hasattr(ActaMunicipal, campo):
            # Búsqueda original
            count_original = ActaMunicipal.objects.filter(**{f"{campo}__icontains": busqueda_original}).count()
            # Búsqueda normalizada  
            count_normalizada = ActaMunicipal.objects.filter(**{f"{campo}__icontains": busqueda_normalizada}).count()
            print(f"   {campo}: original={count_original}, normalizada={count_normalizada}")
    
    # 5. Verificar capacidades de PostgreSQL
    print("\n5️⃣ Verificando capacidades de PostgreSQL:")
    from django.db import connection
    print(f"   Backend de BD: {connection.vendor}")
    
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            # Verificar si unaccent está disponible
            try:
                cursor.execute("SELECT unaccent('Fundación');")
                result = cursor.fetchone()
                print(f"   ✅ unaccent disponible: 'Fundación' → '{result[0]}'")
            except Exception as e:
                print(f"   ❌ unaccent NO disponible: {e}")
    
    # 6. Probar búsqueda manual con SQL
    print("\n6️⃣ Prueba manual con SQL:")
    with connection.cursor() as cursor:
        if connection.vendor == 'postgresql':
            try:
                # Intentar con unaccent si está disponible
                cursor.execute("""
                    SELECT id, titulo FROM pages_actamunicipal 
                    WHERE unaccent(titulo) ILIKE unaccent(%s) 
                    LIMIT 3;
                """, ['%fundacion%'])
                results = cursor.fetchall()
                if results:
                    print("   ✅ Búsqueda con unaccent funciona:")
                    for row in results:
                        print(f"      - ID {row[0]}: {row[1]}")
                else:
                    print("   ❌ Sin resultados con unaccent")
            except Exception as e:
                print(f"   ❌ Error con unaccent: {e}")
                
                # Fallback: búsqueda normal
                cursor.execute("""
                    SELECT id, titulo FROM pages_actamunicipal 
                    WHERE titulo ILIKE %s 
                    LIMIT 3;
                """, ['%fundacion%'])
                results = cursor.fetchall()
                if results:
                    print("   ✅ Búsqueda normal funciona:")
                    for row in results:
                        print(f"      - ID {row[0]}: {row[1]}")
                else:
                    print("   ❌ Sin resultados con búsqueda normal")

def probar_solucion_alternativa():
    """Probar una solución alternativa usando unaccent de PostgreSQL"""
    print("\n" + "="*50)
    print("🛠️  Probando solución alternativa con unaccent")
    print("="*50)
    
    from django.db import connection
    
    if connection.vendor == 'postgresql':
        # Verificar si unaccent está disponible
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
                print("✅ Extensión unaccent habilitada")
                
                # Probar búsqueda con unaccent
                busqueda = "fundacion"
                cursor.execute("""
                    SELECT id, titulo, resumen FROM pages_actamunicipal 
                    WHERE unaccent(titulo) ILIKE unaccent(%s) 
                       OR unaccent(resumen) ILIKE unaccent(%s)
                       OR unaccent(contenido) ILIKE unaccent(%s)
                    LIMIT 5;
                """, [f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'])
                
                results = cursor.fetchall()
                if results:
                    print(f"🎉 ¡Encontrados {len(results)} resultados con unaccent!")
                    for row in results:
                        titulo = row[1][:50] + "..." if len(row[1]) > 50 else row[1]
                        print(f"   - ID {row[0]}: {titulo}")
                else:
                    print("❌ Sin resultados aún con unaccent")
                    
            except Exception as e:
                print(f"❌ Error configurando unaccent: {e}")

if __name__ == "__main__":
    diagnosticar_busqueda()
    probar_solucion_alternativa()