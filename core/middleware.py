from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 1. Definir URLs estáticas que siempre están exentas
        # Asegúrate de usar los nombres correctos de tus URLs (ej. 'profile_edit')
        exempt_urls = [
            reverse('account_logout'),
            reverse('account_login'),
            reverse('account_signup'),
            reverse('profile_edit'),
        ] + getattr(settings, 'PROFILE_COMPLETION_EXEMPT_URLS', [])
        
        # 2. Verificar si es un archivo estático (CSS, JS, imágenes)
        # Hacemos esto ANTES de tocar la base de datos para no gastar recursos
        is_static_request = (
            any(request.path.startswith(path) for path in ['/static/', '/media/']) or
            any(request.path.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'])
        )

        if is_static_request:
            return self.get_response(request)

        # 3. Lógica para usuarios autenticados
        if request.user.is_authenticated:
            try:
                # Intentamos obtener el perfil. Usamos select_related si fuera necesario, 
                # pero el ORM de Django suele cachear request.user.profile
                profile = request.user.profile

                # --- CAMBIO IMPORTANTE AQUÍ ---
                # Agregamos la URL del perfil del usuario actual a las exentas usando el SLUG
                # Asumimos que tu URL se llama 'profile_detail' como configuramos antes
                if profile.slug:
                    try:
                        profile_url = reverse('profile_detail', kwargs={'slug': profile.slug})
                        exempt_urls.append(profile_url)
                    except Exception:
                        # Si falla el reverse (ej. url mal configurada), no bloqueamos todo
                        pass

                # Verificar si la URL actual está en la lista de exentas
                if request.path in exempt_urls:
                    return self.get_response(request)
                
                # --- VERIFICACIÓN DE CAMPOS ---
                # Si falta información requerida
                if not profile.bio or not profile.bio.strip() or \
                   not profile.location or not profile.location.strip():
                    
                    logger.debug(f"Perfil incompleto para {request.user.username}")
                    
                    # Redirigir si no estamos ya en la página de edición
                    # (aunque ya estaba en exempt_urls, doble seguridad)
                    if request.path != reverse('profile_edit'):
                        return HttpResponseRedirect(reverse('profile_edit') + '?required_fields=true')

            except ObjectDoesNotExist:
                # El usuario existe pero no tiene perfil (caso raro, pero posible)
                logger.error(f"Usuario {request.user.username} no tiene perfil asociado")
                # Opcional: Podrías redirigir a una vista de 'crear perfil' si existe
                pass
            except Exception as e:
                logger.error(f"Error verificando perfil en middleware: {str(e)}")
                # En caso de error crítico, mejor dejar pasar al usuario que bloquearlo en un bucle
                return self.get_response(request)
        
        return self.get_response(request)