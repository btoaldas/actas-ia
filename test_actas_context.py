#!/usr/bin/env python
"""
Script para probar el nuevo context processor de últimas actas publicadas
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.pages.models import ActaMunicipal, EstadoActa, TipoSesion
from apps.auditoria.context_processors import ultimas_actas_publicadas_context
from django.contrib.auth.models import User
from django.utils import timezone

class MockRequest:
    def __init__(self, user):
        self.user = user

def main():
    print("🔍 Verificando últimas actas publicadas...")
    
    # Crear un mock request con usuario autenticado
    try:
        user = User.objects.get(username='superadmin')
    except User.DoesNotExist:
        user = User.objects.filter(is_superuser=True).first()
    
    if not user:
        print("❌ No se encontró usuario autenticado")
        return
    
    request = MockRequest(user)
    
    # Verificar que existan estados
    print(f"📊 Estados disponibles:")
    for estado in EstadoActa.objects.all():
        print(f"  - {estado.nombre}: {estado.descripcion}")
    
    # Verificar que existan tipos de sesión
    print(f"📋 Tipos de sesión disponibles:")
    for tipo in TipoSesion.objects.all():
        print(f"  - {tipo.nombre}: {tipo.get_nombre_display()}")
    
    # Verificar actas totales
    total_actas = ActaMunicipal.objects.count()
    print(f"📁 Total de actas en BD: {total_actas}")
    
    # Verificar actas publicadas
    estado_publicada = EstadoActa.objects.filter(nombre='publicada').first()
    if estado_publicada:
        actas_publicadas = ActaMunicipal.objects.filter(
            estado=estado_publicada,
            activo=True,
            acceso='publico'
        ).count()
        print(f"✅ Actas publicadas públicas: {actas_publicadas}")
        
        # Mostrar las últimas 5
        actas_recientes = ActaMunicipal.objects.filter(
            estado=estado_publicada,
            activo=True,
            acceso='publico'
        ).select_related('tipo_sesion', 'secretario').order_by('-fecha_publicacion', '-fecha_sesion')[:5]
        
        print(f"📄 Últimas 5 actas publicadas:")
        for i, acta in enumerate(actas_recientes, 1):
            print(f"  {i}. {acta.numero_acta} - {acta.titulo[:50]}...")
            print(f"     Tipo: {acta.tipo_sesion.get_nombre_display() if acta.tipo_sesion else 'Sin tipo'}")
            print(f"     Secretario: {acta.secretario.get_full_name() or acta.secretario.username}")
            print(f"     Fecha: {acta.fecha_sesion}")
            print(f"     URL: {acta.get_absolute_url()}")
            print()
    else:
        print("❌ No se encontró estado 'publicada'")
    
    # Probar el context processor
    print("🧪 Probando context processor...")
    result = ultimas_actas_publicadas_context(request)
    
    actas = result.get('ultimas_actas_publicadas', [])
    print(f"✅ Context processor devolvió {len(actas)} actas")
    
    for i, acta in enumerate(actas, 1):
        print(f"  {i}. {acta['numero_acta']} - {acta['titulo']}")
        print(f"     Tipo: {acta['tipo_sesion']}")
        print(f"     Tiempo: {acta['tiempo_hace']}")
        print(f"     URL: {acta['url']}")
        print(f"     Icono: {acta['icono']}")
        print(f"     Color: {acta['color']}")
        print()

if __name__ == '__main__':
    main()