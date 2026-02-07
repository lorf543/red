# adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Si el usuario ya está autenticado, conectar la cuenta social
        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
            return
        
        # Buscar si ya existe un usuario con este email
        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                # Conectar la cuenta social al usuario existente
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Guardar usuario desde login social (Google)
        """
        extra_data = sociallogin.account.extra_data
        
        # Obtener datos de Google
        email = extra_data.get('email', '')
        given_name = extra_data.get('given_name', '')
        family_name = extra_data.get('family_name', '')
        picture_url = extra_data.get('picture', '')
        
        # Crear username único ANTES de llamar super()
        if extra_data.get('name'):
            base_username = slugify(extra_data.get('name'))
        else:
            base_username = slugify(email.split('@')[0])
        
        # Asegurar que el username sea único
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}-{uuid.uuid4().hex[:4]}"
            counter += 1
            if counter > 10:  # Evitar loop infinito
                username = f"{base_username}-{uuid.uuid4().hex[:8]}"
                break
        
        # Ahora llamar super() que creará el usuario
        user = super().save_user(request, sociallogin, form)
        
        # Actualizar el usuario con los datos correctos
        user.username = username
        user.first_name = given_name
        user.last_name = family_name
        user.save()
        
        # Actualizar el perfil (ya existe por el signal)
        profile = user.profile
        
        # Actualizar slug basado en el username final
        profile.slug = slugify(username)
        
        # Guardar la foto de Google solo si no tiene una ya
        if picture_url and not profile.profile_picture:
            profile.profile_picture = picture_url
        
        profile.save()
        
        return user
    
    def is_auto_signup_allowed(self, request, sociallogin):
        return True


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        
        # Manejar emails temporales si es necesario
        if user.email and user.email.endswith('@temp.noemail'):
            pass
        
        if commit:
            user.save()
        
        return user