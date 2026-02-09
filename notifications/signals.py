# notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from commentslikes.models import Comment, Reaction
from .models import Notification




@receiver(post_save, sender=Notification)
def update_notification_count(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        recipient = instance.recipient
        # Contamos las no leídas
        count = recipient.notifications.filter(read=False).count()
        
        # Enviamos al grupo del usuario
        async_to_sync(channel_layer.group_send)(
            f"user_{recipient.id}_notifications",
            {
                "type": "send_notification_update",
                "count": count,
            }
        )

