import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from typing import cast, List
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from allauth.account.utils import user_email, user_field

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Adapter que fuerza selección determinística de SocialApp.

    Maneja el caso anómalo donde allauth lanza MultipleObjectsReturned aun cuando
    aparenta existir un único registro (condición observada en entorno actual).
    Selecciona la primera coincidencia ordenada por ID para garantizar
    funcionamiento del flujo OAuth en desarrollo.
    """

    def get_app(self, request, provider):  # type: ignore[override]
        site = None
        try:
            # En Django>=4.0 get_current puede aceptar request; si falla se recurre sin request.
            try:
                site = Site.objects.get_current(request)
            except TypeError:  # fallback si firma distinta
                site = Site.objects.get_current()

            qs = SocialApp.objects.filter(provider=provider)
            if site:
                qs = qs.filter(sites=site)

            apps = list(qs.order_by('id'))
            if not apps:
                raise SocialApp.DoesNotExist(f"No SocialApp configurada para provider={provider}")
            if len(apps) > 1:
                logger.warning(
                    "[OAuth] Multiple SocialApp coincidencias para provider=%s (count=%d). Usando la primera.",
                    provider,
                    len(apps),
                )
            return apps[0]
        except Exception:
            logger.exception("[OAuth] Error resolviendo SocialApp para provider=%s", provider)
            raise

    def is_auto_signup_allowed(self, request, sociallogin):
        """Siempre permitir registro automático para usuarios OAuth."""
        # Log para debug
        logger.info("[OAuth] Auto signup para %s con email %s", 
                   sociallogin.account.provider, sociallogin.user.email)
        return True

    def pre_social_login(self, request, sociallogin):
        """Intentar conectar con usuario existente por email antes del signup."""
        if sociallogin.is_existing:
            return
            
        try:
            email = sociallogin.user.email
            if email:
                # Buscar usuario existente con el mismo email
                existing_user = User.objects.filter(email=email).first()
                if existing_user:
                    # Conectar la cuenta social al usuario existente
                    sociallogin.connect(request, existing_user)
                    logger.info("[OAuth] Conectada cuenta %s a usuario existente %s", 
                              sociallogin.account.provider, existing_user.username)
        except Exception as e:
            logger.warning("[OAuth] Error en pre_social_login: %s", e)

    def populate_user(self, request, sociallogin, data):
        """Poblar usuario con datos del proveedor OAuth."""
        user = sociallogin.user
        email = data.get('email')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        name = data.get('name', '')
        
        # Datos específicos por proveedor
        if sociallogin.account.provider == 'github':
            name = sociallogin.account.extra_data.get('name', name)
            login = sociallogin.account.extra_data.get('login', '')
            if not first_name and name:
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''
        elif sociallogin.account.provider == 'google':
            first_name = sociallogin.account.extra_data.get('given_name', first_name)
            last_name = sociallogin.account.extra_data.get('family_name', last_name)
            name = sociallogin.account.extra_data.get('name', name)
        
        # Si no hay first_name/last_name pero sí name, intentar dividir
        if not first_name and not last_name and name:
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        if email:
            user_email(user, email)
        if first_name:
            user_field(user, 'first_name', first_name)
        if last_name:
            user_field(user, 'last_name', last_name)
        
        # Generar username si no existe
        if not user.username and email:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            user.username = username
            
        logger.info("[OAuth] Usuario populado: %s (%s %s) - %s", 
                   user.username, first_name, last_name, email)
        return user

    def save_user(self, request, sociallogin, form=None):
        """Guardar usuario después del login social."""
        user = super().save_user(request, sociallogin, form)
        logger.info("[OAuth] Usuario creado/actualizado: %s (%s)", user.username, user.email)
        return user
