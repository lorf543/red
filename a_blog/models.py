from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
User = get_user_model()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, max_length=100)
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

    main_image = models.ImageField(upload_to='blog_images/', null=True, blank=True, verbose_name="Imagen Principal")
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