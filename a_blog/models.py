from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone
from cloudinary.models import CloudinaryField

from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver

from cloudinary import api as cloudinary_api
from datetime import timedelta

User = get_user_model()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=100, blank=True, null=True)
    color = models.CharField(max_length=7, default='#4f46e5')  # Color HEX
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class BlogPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_authored')
    title = models.CharField(max_length=255, verbose_name="Título del Header")
    subtitle = models.CharField(max_length=255, blank=True, null=True, verbose_name="Subtítulo")
    tags = models.ManyToManyField(Tag, related_name='blog_posts', blank=True)
    slug = models.SlugField(unique=True, max_length=255, blank=True)

    main_image = CloudinaryField(
        folder="blogs",
        null=True,
        blank=True,
        transformation={
            'quality': 'auto:good',
            'fetch_format': 'auto',
        }
    )
    main_paragraph = models.TextField(verbose_name="Párrafo Principal (Intro)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at'] 
        verbose_name = "Blog"
        verbose_name_plural = "Blogs"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title
    
    
    def get_total_views(self):
        """Total de vistas de este post"""
        return self.views.count()
    
    def get_unique_views(self):
        """Vistas únicas (por IP)"""
        return self.views.values('ip_address').distinct().count()
    
    def get_views_today(self):
        """Vistas de hoy"""
        today = timezone.now().date()
        return self.views.filter(viewed_at__date=today).count()
    
    def get_views_this_week(self):
        """Vistas de esta semana"""
        week_ago = timezone.now() - timedelta(days=7)
        return self.views.filter(viewed_at__gte=week_ago).count()
    
    def get_views_this_month(self):
        """Vistas de este mes"""
        month_ago = timezone.now() - timedelta(days=30)
        return self.views.filter(viewed_at__gte=month_ago).count()
    
    def get_views_by_day(self, days=7):
        """Obtener vistas agrupadas por día (últimos N días)"""
        from django.db.models import Count
        from django.db.models.functions import TruncDate
        
        start_date = timezone.now() - timedelta(days=days)
        return self.views.filter(
            viewed_at__gte=start_date
        ).annotate(
            date=TruncDate('viewed_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')



class BlogPostView(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    referrer = models.URLField(max_length=500, blank=True, null=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Vista de Blog"
        verbose_name_plural = "Vistas de Blog"
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['post', '-viewed_at']),
            models.Index(fields=['ip_address', 'post']),
        ]
    
    def __str__(self):
        return f"{self.post.title} - {self.viewed_at.strftime('%Y-%m-%d %H:%M')}"


class BlogPostStatistics(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='daily_stats')
    date = models.DateField()
    views_count = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = "Estadística Diaria"
        verbose_name_plural = "Estadísticas Diarias"
        unique_together = [['post', 'date']]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.post.title} - {self.date}"


class PostSection(models.Model):
    # related_name='sections' permite acceder desde el padre así: blog.sections.all()
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='sections')
    
    subtitle = models.CharField(max_length=255, verbose_name="Subtítulo")
    content = models.TextField(verbose_name="Contenido del tema")
    
    order = models.PositiveIntegerField(default=0, verbose_name="Orden de aparición")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        verbose_name = "Sub-tema"
        verbose_name_plural = "Sub-temas"

    def __str__(self):
        return f"{self.post.title} - {self.subtitle}"
    
    
    
    
@receiver(pre_save, sender=BlogPost)
def delete_old_image_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = BlogPost.objects.get(pk=instance.pk)
    except BlogPost.DoesNotExist:
        return

    if old.main_image and old.main_image != instance.main_image:
        public_id = old.main_image.public_id
        if public_id and "default" not in public_id:
            try:
                cloudinary_api.delete_resources([public_id])
            except Exception as e:
                print(f"Cloudinary delete error: {e}")


@receiver(post_delete, sender=BlogPost)
def delete_image_on_delete(sender, instance, **kwargs):
    if instance.main_image:
        public_id = instance.main_image.public_id
        if public_id and "default" not in public_id:
            try:
                cloudinary_api.delete_resources([public_id])
            except Exception as e:
                print(f"Cloudinary delete error: {e}")