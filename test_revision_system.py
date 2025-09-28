#!/usr/bin/env python
"""
Script de prueba para el sistema de revisión de actas
Simula el flujo completo de revisión
"""

import os
import django
import sys

# Configurar Django
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from gestion_actas.models import GestionActa, ProcesoRevision, RevisionIndividual, EstadoGestionActa
from django.utils import timezone

def test_revision_workflow():
    print("🧪 INICIANDO PRUEBA DEL SISTEMA DE REVISIÓN")
    print("=" * 50)
    
    try:
        # 1. Verificar que existe el acta de prueba
        acta = GestionActa.objects.get(id=35)
        print(f"✅ Acta encontrada: {acta.titulo}")
        print(f"   Estado actual: {acta.estado.nombre}")
        print(f"   Permite edición: {acta.estado.permite_edicion}")
        
        # 2. Verificar usuarios disponibles
        revisores = User.objects.filter(is_active=True).exclude(id=1)  # Excluir superadmin
        print(f"✅ Usuarios disponibles para revisión: {revisores.count()}")
        for revisor in revisores[:3]:
            print(f"   - {revisor.username} ({revisor.email or 'Sin email'})")
        
        # 3. Verificar estados disponibles
        estado_revision = EstadoGestionActa.objects.get(codigo='en_revision')
        estado_edicion = EstadoGestionActa.objects.get(codigo='en_edicion')
        print(f"✅ Estados configurados:")
        print(f"   - En Revisión: {estado_revision.nombre} (permite_edicion: {estado_revision.permite_edicion})")
        print(f"   - En Edición: {estado_edicion.nombre} (permite_edicion: {estado_edicion.permite_edicion})")
        
        # 4. Verificar procesos existentes
        procesos_existentes = ProcesoRevision.objects.filter(gestion_acta=acta)
        print(f"✅ Procesos de revisión existentes: {procesos_existentes.count()}")
        
        # 5. Simular configuración SMTP (sin enviar realmente)
        from django.conf import settings
        print(f"✅ Configuración de email:")
        print(f"   - Backend: {settings.EMAIL_BACKEND}")
        if hasattr(settings, 'EMAIL_HOST'):
            print(f"   - Host: {settings.EMAIL_HOST}")
            print(f"   - Puerto: {settings.EMAIL_PORT}")
            print(f"   - TLS: {settings.EMAIL_USE_TLS}")
        
        print("\n🎉 SISTEMA PREPARADO PARA PRUEBAS")
        print("=" * 50)
        print("FLUJO DE PRUEBA RECOMENDADO:")
        print("1. Acceder a: http://localhost:8000/gestion-actas/acta/35/configurar-revision/")
        print("2. Seleccionar 1-2 revisores")
        print("3. Configurar tipo de aprobación")
        print("4. Enviar a revisión")
        print("5. Verificar que el estado cambió y el editor se bloqueó")
        print("6. Acceder a: http://localhost:8000/gestion-actas/acta/35/")
        print("7. Probar botón 'Activar Edición (Emergencia)' como superadmin")
        print("8. Verificar logs de correos enviados")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_revision_workflow()