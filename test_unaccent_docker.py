#!/usr/bin/env python
"""
Script simple para probar unaccent en PostgreSQL
"""
import os
import sys
import django

# Configurar Django para usar dentro de Docker
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def probar_unaccent():
    """Probar la función unaccent directamente en PostgreSQL"""
    print("🔧 Probando unaccent en PostgreSQL")
    print("=" * 40)
    
    with connection.cursor() as cursor:
        try:
            # Probar unaccent básico
            cursor.execute("SELECT unaccent('Fundación');")
            result = cursor.fetchone()
            print(f"✅ unaccent('Fundación') = '{result[0]}'")
            
            # Probar búsqueda con unaccent
            cursor.execute("""
                SELECT COUNT(*) FROM pages_actamunicipal 
                WHERE unaccent(titulo) ILIKE unaccent('fundacion');
            """)
            count = cursor.fetchone()[0]
            print(f"📊 Resultados con unaccent: {count}")
            
            # Probar búsqueda normal para comparar
            cursor.execute("""
                SELECT COUNT(*) FROM pages_actamunicipal 
                WHERE titulo ILIKE 'fundacion';
            """)
            count_normal = cursor.fetchone()[0]
            print(f"📊 Resultados sin unaccent: {count_normal}")
            
            # Mostrar algunos ejemplos de títulos que contienen la palabra
            cursor.execute("""
                SELECT id, titulo FROM pages_actamunicipal 
                WHERE unaccent(titulo) ILIKE unaccent('%fundacion%')
                LIMIT 5;
            """)
            results = cursor.fetchall()
            if results:
                print(f"\n🎯 Ejemplos encontrados con unaccent:")
                for row in results:
                    print(f"   - ID {row[0]}: {row[1]}")
            else:
                print("❌ No se encontraron ejemplos")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    probar_unaccent()