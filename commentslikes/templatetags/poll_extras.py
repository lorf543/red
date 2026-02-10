from django import template
import re
import os
from django.utils.safestring import mark_safe
from django.utils.html import escape
from commentslikes.models import Badword
from ..utils import get_badwords_pattern
from django.contrib.auth.models import User
from django.urls import reverse



register = template.Library()

@register.filter()
def highlight_mentions(text, current_user=None):
    if not text:
        return ''
    
    escaped = escape(text)
    
    def replace_mention(match):
        username_full = match.group(1)   # El texto completo (@usuario)
        username_clean = username_full[1:] # Solo el nombre (usuario)
        
        try:
            # 1. OPTIMIZACIÓN: Usamos select_related('profile') para traer el perfil 
            # en la misma consulta y evitar golpear la BD dos veces.
            user = User.objects.select_related('profile').get(username=username_clean)
            
            # 2. CORRECCIÓN: Accedemos a user.profile.slug (no user.slug)
            # Verificamos que tenga perfil y slug para evitar errores
            if hasattr(user, 'profile') and user.profile.slug:
                
                # Asegúrate que 'profile' es el name= en tu urls.py
                profile_url = reverse('profile', kwargs={'slug': user.profile.slug})
                
                # 3. CORRECCIÓN TYPO: 'hx-boots' -> 'hx-boost'
                return f'<a hx-boost="true" href="{profile_url}" class="mention-link text-primary hover:text-primary/80 hover:underline font-medium transition-colors duration-200" data-user-id="{user.id}">{username_full}</a>'
            
            # Si el usuario existe pero no tiene perfil/slug configurado
            return f'<span class="font-medium text-text">{username_full}</span>'

        except User.DoesNotExist:
            return f'<span class="mention-link text-muted/70">{username_full}</span>'
        except Exception:
            # Captura errores si el perfil no existe (RelatedObjectDoesNotExist)
            return f'<span class="font-medium text-text">{username_full}</span>'
    
    highlighted = re.sub(r'(@[\w.@+-]+)', replace_mention, escaped)
    return mark_safe(f'<span class="text-text">{highlighted}</span>')


@register.filter
def force_https(url):
    if url:
        url_str = str(url)
        if url_str.startswith('http://'):
            return url_str.replace('http://', 'https://', 1)
    return url

@register.filter()
def unread_count(user):
    if user.is_authenticated:
        return user.notifications.filter(read=False).count()
    return 0


@register.filter(name='censurar')
def censurar(value):
    """Censura las palabras prohibidas en el texto."""
    if not value:
        return value
    
    try:
        pattern = get_badwords_pattern()

        def replacer(match):
            matched_text = match.group()
            # Contar caracteres alfanuméricos
            alphanum_count = len(re.findall(r'[a-zA-Z0-9]', matched_text))
            return '*' * max(alphanum_count, 3)

        return pattern.sub(replacer, str(value))
    except Exception as e:
        print(f"Error en censurar: {e}")
        return value