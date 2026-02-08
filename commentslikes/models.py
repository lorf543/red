from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.apps import apps

from cloudinary.models import CloudinaryField

from django.core.cache import cache
BADWORDS_CACHE_KEY = 'badwords_regex_v2'
BADWORDS_CACHE_TIMEOUT = 60 * 60  # 1 hora

from django.db.models.signals import post_save
from django.db.models.signals import post_delete
from django.dispatch import receiver
import re

from schedules.models import Subject,Teacher

from notifications.models import Notification

User = get_user_model()

# Create your models here.
def censor_badwords(text):
    badwords = Badword.objects.all().values('pattern', 'replacement')
    for bw in badwords:
        pattern = re.compile(bw['pattern'], re.IGNORECASE)
        if bw['replacement']:
            text = pattern.sub(bw['replacement'], text)
        else:
            def repl(m):
                return '*' * len(m.group())
            text = pattern.sub(repl, text)
    return text


class Reaction(models.Model):
    LIKE = 1
    DISLIKE = -1
    REACTION_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    reaction_type = models.SmallIntegerField(choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
        verbose_name = "Reacción"
        verbose_name_plural = "Reacciones"

    def __str__(self):
        return f"{self.user.username} - {self.get_reaction_type_display()}"

class Comment(models.Model):
    subject = models.ForeignKey(
        'schedules.Subject',
        on_delete=models.CASCADE,
        related_name='comments',
        blank=True,
        null=True,
        verbose_name="Materia"
    )
    
    image_status = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        choices=[
            ('pending', 'Pending'),
            ('safe', 'Safe'),
            ('nsfw', 'NSFW'),
        ],
        default='pending'
    )
    
    image = CloudinaryField(
        folder="red",
        null=True,
        blank=True,
        transformation={
            'quality': 'auto:good',
            'fetch_format': 'auto',
        }
    )
    
    teacher = models.ForeignKey(
        'schedules.Teacher',
        on_delete=models.CASCADE,
        related_name='comments',
        blank=True,
        null=True,
        verbose_name="Profesor"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments',
        verbose_name="Usuario"
    )
    content = models.TextField(verbose_name="Contenido")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='replies',
        blank=True,
        null=True,
        verbose_name="Comentario padre"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="Activo/Moderado")
    moderated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='moderated_comments'
    )
    moderated_at = models.DateTimeField(null=True, blank=True)
    
    reactions = GenericRelation(Reaction, related_query_name='comments')

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['-created_at']

    def __str__(self):
        if self.subject:
            return f"Comentario sobre {self.subject}"
        elif self.teacher:
            return f"Comentario sobre {self.teacher}"
        else:
            return "Comentario"
        
    @property
    def likes_count(self):
        return self.reactions.filter(reaction_type=Reaction.LIKE).count()
    
    @property
    def dislikes_count(self):
        return self.reactions.filter(reaction_type=Reaction.DISLIKE).count()
    
    @property
    def has_like(self):
        """Verifica si tiene al menos un like"""
        return self.reactions.filter(reaction_type=Reaction.LIKE).exists()
    
    @property
    def has_dislike(self):
        """Verifica si tiene al menos un dislike"""
        return self.reactions.filter(reaction_type=Reaction.DISLIKE).exists()
    
    @property
    def any_reaction(self):
        """Verifica si tiene cualquier reacción"""
        return self.reactions.exists() 
    
    @property
    def replies_count(self):
        return self.replies.count()
    
    def user_reaction(self, user):
        if not user.is_authenticated:
            return None
        reaction = self.reactions.filter(user=user).first()
        return reaction.reaction_type if reaction else None
    
    
    def get_absolute_url(self):
        if self.subject:
            return f"/materias/{self.subject.slug}/#comment-{self.id}"
        elif self.teacher:
            return f"/profesores/{self.teacher.slug}/#comment-{self.id}"
        return "#"
    
    
    @property
    def preview_replies(self):
        replies_list = list(self.replies.all())
        return replies_list[:3]

    @property
    def has_more_replies(self):
        if hasattr(self, 'total_replies'):
            return self.total_replies > 3
        return self.replies.count() > 3
    
    
    
    # ---- MENCIONES ----
    def process_mentions(self):
        mentioned_usernames = set(re.findall(r'@(\w+)', self.content or ""))
        if not mentioned_usernames:
            return

        self.mentions.all().delete()

        users = User.objects.filter(username__in=mentioned_usernames)
        for user in users:
            Mention.objects.create(comment=self, user=user)
            self.notify_mentioned_user(user)

    def notify_mentioned_user(self, user):
        try:
            NotificationModel = apps.get_model('notifications', 'Notification')
            notification = NotificationModel.objects.create(
                recipient=user,
                actor=self.user,
                verb="te mencionó en un comentario",
                content_object=self
            )

            from notifications.utils import send_notification_ws
            send_notification_ws(notification)

        except LookupError:
            pass
        
    def save(self, *args, **kwargs):
        content_changed = False
        if self.pk:
            old_content = Comment.objects.filter(pk=self.pk).values_list('content', flat=True).first()
            if old_content != self.content:
                content_changed = True
        else:
            content_changed = True

        super().save(*args, **kwargs)

        if content_changed:
            try:
                self.process_mentions()
            except Exception as e:
                import traceback
                print("❌ ERROR EN process_mentions ❌")
                print(f"Comentario ID: {self.pk}")
                traceback.print_exc()
  
  
@receiver(post_delete, sender=Comment)
def delete_comment_notifications(sender, instance, **kwargs):
    Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id
    ).delete()  
  
class Badword(models.Model):  
    word = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Palabra prohibida"
    )
    replacement = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Reemplazo (opcional)",
        help_text="Si se especifica, reemplazará la palabra prohibida"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    
    class Meta:
        verbose_name = "Palabra prohibida"
        verbose_name_plural = "Palabras prohibidas"
        ordering = ['word']
    
    def __str__(self):
        return self.word
    
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        cache.delete(BADWORDS_CACHE_KEY)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        cache.delete(BADWORDS_CACHE_KEY)
      
  
    
class Mention(models.Model):
    comment = models.ForeignKey(
        Comment, 
        on_delete=models.CASCADE,
        related_name='mentions'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mentions_received'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.comment.content + " " + self.user.username

    class Meta:
        unique_together = ('comment', 'user')
        ordering = ['-created_at']    
    
def create_reply_notification(sender, instance, created, **kwargs):
    if created and instance.parent and instance.user:
        recipient = instance.parent.user
        # if recipient and recipient != instance.user:  # Evita notificarse a sí mismo

        Notification.objects.create(
                recipient=recipient,
                actor=instance.user,
                verb="respondió a tu comentario",
                content_object=instance,
        )

post_save.connect(create_reply_notification, sender=Comment)

class Vote(models.Model):
    VOTE_CHOICES = [
        (1, 'Guagua 🚍'),
        (2, 'Te va a quemar 🔥'),
        (3, 'Se aprende 📚'),
        (4, 'Vago 😴'),
    ]

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='votes', blank=True, null=True)
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='votes', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes',null=True )
    user_name = models.CharField(max_length=100)
    vote_type = models.PositiveSmallIntegerField(choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True, null=True)  # Campo añadido para comentarios

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.subject or self.teacher
        return f"{self.get_vote_type_display()} por {self.user_name} a {target}"

    def get_target(self):
        return self.teacher if self.teacher else self.subject



