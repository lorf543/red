# adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invocado justo después de que el usuario se autentica exitosamente
        con un proveedor social pero antes de que se procese el login.
        """
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

        # Nombre
        user.first_name = extra_data.get("given_name", user.first_name)
        user.last_name = extra_data.get("family_name", user.last_name)

        # Foto de perfil (URL de Google)
        picture_url = extra_data.get("picture")
        if picture_url:
            profile = user.profile
            if not profile.profile_picture:
                profile.profile_picture = picture_url
                profile.save()

        # Username (si viene del form)
        if form and hasattr(form, "cleaned_data"):
            username = form.cleaned_data.get("username")
            if username:
                user.username = username

        user.save()
        return user
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Determina si se permite el registro automático.
        """
        # No permitir registro automático, usar nuestro formulario personalizado
        return False


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