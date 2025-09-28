import os
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

class Command(BaseCommand):
    help = "Crea o actualiza las SocialApp para GitHub y Google usando variables de entorno"

    def handle(self, *args, **options):
        site = Site.objects.get_current()
        creado_o_actualizado = []

        providers = [
            {
                'provider': 'github',
                'name': 'GitHub',
                'client_id_env': 'GITHUB_CLIENT_ID',
                'secret_env': 'GITHUB_CLIENT_SECRET'
            },
            {
                'provider': 'google',
                'name': 'Google',
                'client_id_env': 'GOOGLE_CLIENT_ID',
                'secret_env': 'GOOGLE_CLIENT_SECRET'
            }
        ]

        for p in providers:
            client_id = os.environ.get(p['client_id_env'])
            secret = os.environ.get(p['secret_env'])
            if not client_id or not secret:
                self.stdout.write(self.style.WARNING(f"[SKIP] {p['name']} sin variables {p['client_id_env']} / {p['secret_env']}"))
                continue

            app, created = SocialApp.objects.update_or_create(
                provider=p['provider'],
                defaults={
                    'name': p['name'],
                    'client_id': client_id.strip(),
                    'secret': secret.strip(),
                }
            )
            app.sites.set([site])
            creado_o_actualizado.append((p['name'], 'creado' if created else 'actualizado'))

        if not creado_o_actualizado:
            self.stdout.write(self.style.WARNING("No se creó ni actualizó ninguna SocialApp (revisar variables)."))
        else:
            for nombre, estado in creado_o_actualizado:
                self.stdout.write(self.style.SUCCESS(f"{nombre}: {estado}"))

        self.stdout.write(self.style.SUCCESS("Proceso finalizado."))
