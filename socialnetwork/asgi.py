# myproject/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialnetwork.settings')

django_asgi_app = get_asgi_application()

# Importa tus rutas websocket aquí (las crearemos después)
from notifications import routing as notifications_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                notifications_routing.websocket_urlpatterns
            )
        )
    ),
})