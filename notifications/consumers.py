# notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 1. Obtenemos el usuario de la sesión (scope)
        self.user = self.scope["user"]

        # 2. Solo aceptamos la conexión si el usuario está logueado
        if self.user.is_authenticated:
            # Definimos un nombre de grupo único para este usuario
            self.group_name = f"user_{self.user.id}_notifications"

            # 3. Unimos este "canal" (esta pestaña del navegador) al grupo del usuario
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            # 4. Aceptamos la conexión WebSocket
            await self.accept()
        else:
            # Si no está logueado, rechazamos la conexión
            await self.close()

    async def disconnect(self, close_code):
        # Al cerrar la pestaña, lo sacamos del grupo para no enviar datos a la nada
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name, 
                self.channel_name
            )

    # 5. Este método es el que se activa desde el Signal (update_notification_count)
    async def send_notification_update(self, event):
        count = event["count"]
        
        # 6. Creamos el HTML que HTMX recibirá
        # hx-swap-oob="true" le dice a HTMX: "busca este ID en cualquier parte y cámbialo"
        html = f'<span id="notification-count" hx-swap-oob="true">{count}</span>'
        
        # Si quieres que el círculo rojo desaparezca cuando sea 0
        display = "inline-flex" if count > 0 else "none"
        html += f'<span id="notification-badge" hx-swap-oob="true" style="display: {display};" class="relative inline-flex items-center justify-center bg-error h-5 w-5 rounded-full text-white text-xs font-bold"></span>'

        # 7. Enviamos el HTML puro por el socket
        await self.send(text_data=html)