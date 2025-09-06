#!/usr/bin/env python
"""
Script para configurar aplicaciones OAuth sociales de ejemplo
para que los botones aparezcan en la página de login
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def configurar_oauth_demo():
    """Configura aplicaciones OAuth de demostración"""
    
    print("🔐 Configurando aplicaciones OAuth de demostración...")
    
    # Obtener o crear el site
    try:
        site = Site.objects.get(id=1)
        site.domain = 'localhost:8000'
        site.name = 'Sistema Actas Municipales - Pastaza'
        site.save()
        print(f"✅ Site actualizado: {site.domain}")
    except Site.DoesNotExist:
        site = Site.objects.create(
            id=1,
            domain='localhost:8000',
            name='Sistema Actas Municipales - Pastaza'
        )
        print(f"✅ Site creado: {site.domain}")
    
    # Configurar GitHub OAuth (demo)
    github_app, created = SocialApp.objects.get_or_create(
        provider='github',
        defaults={
            'name': 'GitHub - Municipio Pastaza (DEMO)',
            'client_id': 'demo_github_client_id',
            'secret': 'demo_github_client_secret',
        }
    )
    
    if created:
        print("✅ Aplicación GitHub creada (DEMO)")
    else:
        print("ℹ️  Aplicación GitHub ya existe")
    
    # Asociar con el site
    github_app.sites.add(site)
    
    # Configurar Google OAuth (demo)
    google_app, created = SocialApp.objects.get_or_create(
        provider='google',
        defaults={
            'name': 'Google - Municipio Pastaza (DEMO)',
            'client_id': 'demo_google_client_id',
            'secret': 'demo_google_client_secret',
        }
    )
    
    if created:
        print("✅ Aplicación Google creada (DEMO)")
    else:
        print("ℹ️  Aplicación Google ya existe")
    
    # Asociar con el site
    google_app.sites.add(site)
    
    print("\n🎉 Configuración OAuth de demostración completada!")
    print("\n📋 IMPORTANTE:")
    print("   • Los botones OAuth ahora aparecerán en http://localhost:8000/accounts/login/")
    print("   • Para que funcionen realmente, configura las credenciales reales:")
    print("     1. Ve a http://localhost:8000/admin/socialaccount/socialapp/")
    print("     2. Edita las aplicaciones GitHub y Google")
    print("     3. Reemplaza client_id y secret con valores reales")
    print("   • O ejecuta: configurar_oauth.bat para configuración automática")
    print("\n📖 Ver GUIA_OAUTH.md para obtener credenciales reales")
    
    return True

if __name__ == '__main__':
    try:
        configurar_oauth_demo()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
