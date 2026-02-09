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
    def populate_user(self, request, sociallogin, data):

        user = super().populate_user(request, sociallogin, data)

        email = data.get("email", "")
        name = data.get("name", "")

        if name:
            base_username = slugify(name)
        else:
            base_username = slugify(email.split("@")[0])

        username = base_username
        while User.objects.filter(username=username).exists():
            username = f"{base_username}-{uuid.uuid4().hex[:6]}"

        user.username = username
        user.email = email

        return user
    
    def is_auto_signup_allowed(self, request, sociallogin):
        return True


class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        
        if user.email and user.email.endswith('@temp.noemail'):
            pass
        
        if commit:
            user.save()
        
        return user