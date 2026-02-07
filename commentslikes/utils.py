import re
from .models import Badword
from django.contrib.auth import get_user_model
import hashlib

from django.core.cache import cache
from commentslikes.models import Badword

BADWORDS_CACHE_KEY = 'badwords_regex_v2'
BADWORDS_CACHE_TIMEOUT = 60 * 60  # 1 hora


User = get_user_model()



NSFW_CACHE_TTL = 60 * 60 * 24  # 24 horas

def check_nsfw_cached(image_url, ai):
    cache_key = "nsfw:" + hashlib.sha256(image_url.encode()).hexdigest()

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        print("⚡ NSFW desde cache")
        return cached_result

    print("🌐 NSFW desde API")
    is_nsfw = ai.validate.nsfw({"url": image_url})

    cache.set(cache_key, is_nsfw, NSFW_CACHE_TTL)
    return is_nsfw



def is_username_taken(username, exclude_user_id=None):
    query = User.objects.filter(username__iexact=username.strip())
    if exclude_user_id:
        query = query.exclude(pk=exclude_user_id)
    return query.exists()


class UsernameValidator:
    MIN_LENGTH = 2
    MAX_LENGTH = 15
    MIN_RECOMMENDED_LENGTH = 4 
    @classmethod
    def validate_username(cls, username, current_user_id=None):
        username = username.strip()

        # Validación de longitud
        if len(username) < cls.MIN_LENGTH:
            return False, f"El nombre debe tener al menos {cls.MIN_LENGTH} caracteres"
        
        if len(username) > cls.MAX_LENGTH:
            return False, f"El nombre no puede exceder {cls.MAX_LENGTH} caracteres"
        
        if username.isdigit():
            return False, "El nombre de usuario no puede contener solo números"

        # Si tiene exactamente 2 caracteres (mínimo pero no recomendado)
        if len(username) == cls.MIN_LENGTH:
            return False, "Por seguridad, usa un nombre más largo (4+ caracteres)"

        # Palabras prohibidas
        if contains_admin(username):
            return False, "No puedes usar términos como 'admin'"

        if contains_badwords(username):
            return False, "El nombre contiene palabras prohibidas"

        # Verificar si ya existe (excluyendo al usuario actual si se pasa su id)
        if is_username_taken(username, exclude_user_id=current_user_id):
            return False, "El nombre de usuario ya está en uso"

        # Si pasa todas las validaciones
        return True, "✔ Nombre disponible"




CHAR_SUBSTITUTIONS = {
    'a': r'[a4@]',
    'e': r'[e3]',
    'i': r'[i1!]',
    'o': r'[o0]',
    's': r'[s5$]',
    't': r'[t7]',
    'g': r'[g9]',
}

SEPARATOR = r'[\s\.\-_]{0,2}'

def contains_admin(text):
    pattern = r'''
        adm[1i]n|          # admin, adm1n, admin
        adm[1i]n[i1]str|   # administrator con números
        moderador|         # moderador en español
        \badmin\b|         # palabra exacta admin
        [a@]dmin|          # @dmin, admin con caracteres especiales
        adm1n1str4d0r       # variante compleja
    '''
    return bool(re.search(pattern, text.lower(), re.VERBOSE))

def get_badwords_pattern():
    cached = cache.get(BADWORDS_CACHE_KEY)
    if cached:
        return cached

    badwords = list(
        Badword.objects.values_list('word', flat=True)
    )

    regex_patterns = []

    for word in badwords:
        if not word:
            continue

        word = word.lower()
        parts = []

        for char in word:
            if char in CHAR_SUBSTITUTIONS:
                parts.append(CHAR_SUBSTITUTIONS[char])
            elif char.isalpha():
                parts.append(f'[{char}{char.upper()}]')
            else:
                parts.append(re.escape(char))

        regex_patterns.append(SEPARATOR.join(parts))

    if not regex_patterns:
        pattern = re.compile(r'(?!)', re.IGNORECASE)
    else:
        pattern = re.compile(
            r'(?:' + '|'.join(regex_patterns) + r')',
            re.IGNORECASE
        )

    cache.set(BADWORDS_CACHE_KEY, pattern, BADWORDS_CACHE_TIMEOUT)
    return pattern

def get_simple_badwords_pattern():
    """Versión simplificada más robusta."""
    badwords = Badword.objects.values_list('word', flat=True)
    
    # Sustituciones comunes de leetspeak
    substitutions = {
        'a': 'a4@',
        'e': 'e3',
        'i': 'i1!',
        'o': 'o0',
        's': 's5$',
        't': 't7',
        'g': 'g9'
    }
    
    regex_patterns = []
    
    for word in badwords:
        if not word:
            continue
            
        pattern_parts = []
        
        for char in word.lower():
            if char in substitutions:
                # Crear alternativas para cada carácter
                chars = substitutions[char]
                char_pattern = '[' + re.escape(''.join(chars)) + ']'
            else:
                char_pattern = re.escape(char)
            
            pattern_parts.append(char_pattern)
        
        # Unir con separadores opcionales
        word_pattern = r'[^a-zA-Z0-9]*?'.join(pattern_parts)
        regex_patterns.append(word_pattern)
    
    if regex_patterns:
        try:
            pattern = '(?:' + '|'.join(regex_patterns) + ')'
            return re.compile(pattern, re.IGNORECASE)
        except re.error:
            # Si aún falla, usar patrón muy básico
            return get_basic_pattern()
    else:
        return re.compile(r'(?!)', re.IGNORECASE)

def get_basic_pattern():
    """Patrón básico como último recurso."""
    badwords = Badword.objects.values_list('word', flat=True)
    
    if not badwords:
        return re.compile(r'(?!)', re.IGNORECASE)
    
    # Escapar todas las palabras y unirlas con OR
    escaped_words = [re.escape(word) for word in badwords if word]
    
    if escaped_words:
        pattern = r'\b(?:' + '|'.join(escaped_words) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    else:
        return re.compile(r'(?!)', re.IGNORECASE)

def contains_badwords(content):
    if not content:
        return False

    try:
        return bool(get_badwords_pattern().search(content))
    except Exception:
        return False


def get_badwords_in_text(content):
    if not content:
        return []

    try:
        pattern = get_badwords_pattern()
        return [m.group() for m in pattern.finditer(content)]
    except Exception:
        return []