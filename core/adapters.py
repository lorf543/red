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
        user = super().save_user(request, sociallogin, form)
        extra_data = sociallogin.account.extra_data

        # 1. Asegurar que el usuario tenga un username si está vacío
        if not user.username:
            # Intentar usar el 'name' de Google, si no el email, si no un UUID
            full_name = extra_data.get("name") or extra_data.get("email").split('@')[0]
            user.username = slugify(full_name)
            
            # Verificar si el username ya existe para evitar duplicados
            if User.objects.filter(username=user.username).exists():
                user.username = f"{user.username}-{uuid.uuid4().hex[:4]}"

        # 2. Guardar nombres
        user.first_name = extra_data.get("given_name", "")
        user.last_name = extra_data.get("family_name", "")
        user.save()

        # 3. Actualizar el perfil (esto disparará el save del modelo UserProfile)
        picture_url = extra_data.get("picture")
        profile = user.profile 
        
        if picture_url and not profile.profile_picture:
            profile.profile_picture = picture_url
        
        # Forzar que el slug se genere basándose en el nuevo username
        profile.slug = slugify(user.username)
        profile.save()

        return user
    
    def is_auto_signup_allowed(self, request, sociallogin):
        # No permitir registro automático, usar nuestro formulario personalizado
        return True


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        Guarda el usuario durante el registro tradicional.
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Manejar emails temporales
        if user.email and user.email.endswith('@temp.noemail'):
            # No hacer nada especial con emails temporales
            pass
        
        if commit:
            user.save()
        
        return user