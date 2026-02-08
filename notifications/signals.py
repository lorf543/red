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


# @receiver(post_save, sender=Comment)
# def create_reply_notification(sender, instance, created, **kwargs):
#     """
#     Crear notificación cuando alguien responde a un comentario.
#     Ahora con WebSocket en tiempo real.
#     """
#     if created and instance.parent:
#         recipient = instance.parent.user
        
#         if recipient and recipient != instance.user:
#             # Crear la notificación
#             notification = Notification.objects.create(
#                 recipient=recipient,
#                 actor=instance.user,
#                 verb="respondió a tu comentario",
#                 content_object=instance,
#             )
            
#             # Enviar notificación en tiempo real vía WebSocket
#             send_notification_to_user(recipient.id, notification.id)


# @receiver(post_save, sender=Reaction)
# def notify_on_reaction(sender, instance, created, **kwargs):
#     """
#     Crear notificación cuando alguien reacciona a un comentario.
#     Ahora con WebSocket en tiempo real.
#     """
#     if created and instance.content_object.__class__.__name__ == "Comment":
#         comment = instance.content_object
        
#         if comment.user and comment.user != instance.user:
#             action = "le dio like a tu comentario" if instance.reaction_type == 1 else "no le gustó tu comentario"
            
#             # Crear la notificación
#             notification = Notification.objects.create(
#                 recipient=comment.user,
#                 actor=instance.user,
#                 verb=action,
#                 content_object=comment
#             )
            
#             # Enviar notificación en tiempo real vía WebSocket
#             send_notification_to_user(comment.user.id, notification.id)


# def send_notification_to_user(user_id, notification_id):
#     """
#     Helper function para enviar notificación via WebSocket.
    
#     Args:
#         user_id: ID del usuario destinatario
#         notification_id: ID de la notificación creada
#     """
#     channel_layer = get_channel_layer()
    
#     # Enviar al grupo de notificaciones del usuario
#     async_to_sync(channel_layer.group_send)(
#         f"notifications_{user_id}",
#         {
#             "type": "notification_message",
#             "type_message": "new_notification",
#             "notification_id": notification_id,
#         }
#     )
    
#     print(f"📨 Notificación {notification_id} enviada a usuario {user_id} via WebSocket")


# @receiver(post_save, sender=Notification)
# def notification_count_update(sender, instance, created, **kwargs):
    """
    Actualizar contador cuando se marca una notificación como leída.
    """
    if not created:  # Solo cuando se actualiza (marca como leída)
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"notifications_{instance.recipient.id}",
            {
                "type": "notification_message",
                "type_message": "count_update",
            }
        )