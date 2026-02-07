from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from commentslikes.models import Comment, Reaction
from .models import Notification


User = get_user_model()
# @receiver(post_save, sender=Comment)
# def create_reply_notification(sender, instance, created, **kwargs):
#     # Solo proceder si es un nuevo comentario y tiene un padre (es una respuesta)
#     if created and instance.parent:
#         # Obtener el usuario del comentario padre (el que va a recibir la notificación)
#         recipient = instance.parent.user
        
#         # Solo crear notificación si hay un destinatario y no es el mismo que está comentando
#         if recipient and recipient != instance.user:
#             Notification.objects.create(
#                 recipient=recipient,
#                 actor=instance.user,
#                 verb="respondió a tu comentario",
#                 content_object=instance,
#             )



# @receiver(post_save, sender=Comment)
# def notify_on_reply(sender, instance, created, **kwargs):
#     if created and instance.parent and instance.parent.user != instance.user:
#         print("trigger?")
#         Notification.objects.create(
#             recipient=instance.parent.user,
#             actor=instance.user,
#             verb="respondió a tu comentario",
#             content_object=instance
#         )

# @receiver(post_save, sender=Reaction)
# def notify_on_reaction(sender, instance, created, **kwargs):
#     if created and instance.content_object.__class__.__name__ == "Comment":
#         comment = instance.content_object
#         if comment.user and comment.user != instance.user:
#             action = "le dio like a tu comentario" if instance.reaction_type == 1 else "no le gustó tu comentario"
#             Notification.objects.create(
#                 recipient=comment.user,
#                 actor=instance.user,
#                 verb=action,
#                 content_object=comment
#             )