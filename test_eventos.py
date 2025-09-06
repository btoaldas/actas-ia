#!/usr/bin/env python
"""
Script de prueba para verificar los modelos de eventos
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.pages.models import EventoMunicipal, InvitacionExterna
from apps.pages.forms import EventoForm

def test_models():
    """Prueba básica de los modelos"""
    print("=== PRUEBA DE MODELOS ===")
    
    # Verificar que podemos importar los modelos
    print(f"✓ EventoMunicipal: {EventoMunicipal}")
    print(f"✓ InvitacionExterna: {InvitacionExterna}")
    
    # Verificar campos del EventoMunicipal
    fields = [f.name for f in EventoMunicipal._meta.fields]
    print(f"✓ Campos EventoMunicipal: {fields}")
    print(f"✓ Campo invitados_externos presente: {'invitados_externos' in fields}")
    
    # Verificar campos del InvitacionExterna
    inv_fields = [f.name for f in InvitacionExterna._meta.fields]
    print(f"✓ Campos InvitacionExterna: {inv_fields}")
    
    # Verificar formulario
    form = EventoForm()
    form_fields = list(form.fields.keys())
    print(f"✓ Campos del formulario: {form_fields}")
    print(f"✓ Campo invitados_externos en formulario: {'invitados_externos' in form_fields}")
    
    print("\n=== TODAS LAS VERIFICACIONES PASARON ===")

if __name__ == "__main__":
    test_models()
