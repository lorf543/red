# notifications/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType



class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    
    verb = models.CharField(max_length=255)  # Ej: "te respondió", "le dio like a tu comentario"
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')  # El objeto relacionado (comentario, etc.)

    read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.actor} {self.verb} {self.content_object} → {self.recipient}"
    
    def get_absolute_url(self):
        if self.content_object:
            # Si el objeto tiene get_absolute_url, úsalo
            if hasattr(self.content_object, 'get_absolute_url'):
                return self.content_object.get_absolute_url()
            
            # Si es un comentario, construir URL manualmente
            if hasattr(self.content_object, 'teacher'):
                # Comentario en profesor
                return f"{self.content_object.teacher.get_absolute_url()}#comment-{self.content_object.id}"
            elif hasattr(self.content_object, 'parent'):
                # Es una respuesta (reply)
                parent = self.content_object.parent
                if hasattr(parent, 'teacher'):
                    return f"{parent.teacher.get_absolute_url()}#comment-{self.content_object.id}"
        
        return "#"
    
    def mark_as_read(self):
        if not self.read:
            self.read = True
            self.save()
            return True
        return False


    def get_comment_preview(self):
        if hasattr(self.content_object, 'content'):
            return self.content_object.content[:100] + "..." if len(self.content_object.content) > 100 else self.content_object.content
        return ""

