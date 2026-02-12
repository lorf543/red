from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.text import slugify
from django.dispatch import receiver
from datetime import date
from django.urls import reverse

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
from cloudinary import uploader as cloudinary_uploader
from cloudinary import api as cloudinary_api

import uuid


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    bio = models.TextField(max_length=250, blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    


    profile_picture = CloudinaryField(
        folder="red/profile_picture",
        null=True,
        blank=True,
        transformation={
            'quality': 'auto:good',
            'fetch_format': 'auto',
        }
    )

    #configuration
    background_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de la imagen de fondo"
    )
    
    cursor_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL del cursor personalizado (.cur o .png)"
    )
    
    cursor_hotspot_x = models.IntegerField(default=16, help_text="Posición X del punto de clic")
    cursor_hotspot_y = models.IntegerField(default=16, help_text="Posición Y del punto de clic")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_profile_url(self):
        return reverse('profile_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            if self.user.username:
                self.slug = slugify(self.user.username) 
            else:
                self.slug = slugify(self.user.email.split('@')[0]) or str(uuid.uuid4())[:8]

        try:
            old = UserProfile.objects.get(pk=self.pk) if self.pk else None
        except UserProfile.DoesNotExist:
            old = None

        super().save(*args, **kwargs)

        # Si había imagen anterior y es diferente, borrarla
        if old and old.profile_picture and str(old.profile_picture) != str(self.profile_picture):
            old_public_id = str(old.profile_picture)
            # Verificar que no sea la imagen por defecto
            if old_public_id and "default" not in old_public_id:
                try:
                    cloudinary_api.delete_resources([old_public_id])
                except Exception as e:
                    # Log error but don't fail the save
                    print(f"Error deleting old image: {e}")

    @property
    def get_profile_initials(self):
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name[0]}{self.user.last_name[0]}".upper()
        return self.user.username[0:2].upper()

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

    @property
    def age(self):
        if self.birth_date:
            today = date.today()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None

    @property
    def is_profile_complete(self):
        required_fields = ['bio', 'location']
        return all(getattr(self, field) for field in required_fields)

    @property
    def has_custom_profile_picture(self):
        default_url = "avatars/default"
        return self.profile_picture and str(self.profile_picture) != default_url

    def get_profile_image_url(self):
        if self.has_custom_profile_picture:
            return self.profile_picture.url
        return 'https://res.cloudinary.com/dvnfk6qn8/image/upload/v1755348916/avatars/default.png.jpg'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        # Only save if profile exists to avoid infinite recursion
        if hasattr(instance, 'profile'):
            instance.profile.save()