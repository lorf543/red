# notifications/utils.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

def send_notification_ws(notification):
    """Envía una notificación via WebSocket"""
    channel_layer = get_channel_layer()
    
    notification_data = {
        'id': notification.id,
        'actor': notification.actor.username,
        'verb': notification.verb,
        'timestamp': notification.timestamp.isoformat(),
        'preview': notification.get_comment_preview(),
    }
    
    async_to_sync(channel_layer.group_send)(
        f"user_{notification.recipient.id}",
        {
            'type': 'send_notification',
            'notification': notification_data
        }
    )