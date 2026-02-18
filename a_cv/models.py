from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

User = get_user_model()

class CVTemplate(models.Model):
    CATEGORY_CHOICES = [
        ('professional', 'Profesional'),
        ('creative', 'Creativo'),
        ('minimal', 'Minimalista'),
        ('modern', 'Moderno'),
    ]
    
    name = models.CharField(max_length=100) 
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='professional')
    preview_image = CloudinaryField(
        'template_preview',
        folder='cv_templates',
        null=True,
        blank=True
    )
    

    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    

    template_code = models.CharField(max_length=50, unique=True)
    html_file = models.CharField(max_length=100)  
    
    order = models.IntegerField(default=0)  #
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Template de CV"
        verbose_name_plural = "Templates de CV"
    
    def __str__(self):
        return self.name


class CV(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cvs')
    template = models.ForeignKey(CVTemplate, on_delete=models.PROTECT)  # PROTECT para no borrar CVs si borro template
    
    # Información personal (nueva)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    
    # Resumen profesional
    professional_summary = models.TextField(blank=True, help_text="Breve resumen de tu perfil profesional")
    
    # Foto (opcional)
    profile_photo = CloudinaryField(
        'cv_photos',
        folder='cv_user_photos',
        null=True,
        blank=True
    )
    
    # Configuración
    public = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Curriculum Vitae"
        verbose_name_plural = "Curriculums Vitae"

    def __str__(self):
        return f"{self.full_name} - {self.template.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(f"{self.full_name}-{self.user.username}")
            slug = base_slug
            counter = 1
            while CV.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)



class Experience(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='experiences')  
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)  # Nueva
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null=True para "Actualidad"
    current = models.BooleanField(default=False)  # Trabajo actual
    responsibilities = models.TextField(help_text="Descripción de tus funciones")
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.position} en {self.company}"


class Education(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=100) 
    degree = models.CharField(max_length=100, null=True, blank=True) 
    field_of_study = models.CharField(max_length=100, blank=True)  # Ej: "Ingeniería de Software"
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    current = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "Educación"
        verbose_name_plural = "Educación"
    
    def __str__(self):
        return f"{self.degree} - {self.institution}"


class SkillCategory(models.Model): 
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skill_categories')
    name = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Categoría de Habilidad"
        verbose_name_plural = "Categorías de Habilidades"
    
    def __str__(self):
        return self.name


class Skill(models.Model):
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=50)
    proficiency = models.IntegerField(default=3, choices=[
        (1, 'Básico'),
        (2, 'Intermedio'),
        (3, 'Avanzado'),
        (4, 'Experto'),
    ], blank=True, null=True)
    
    def __str__(self):
        return self.name


class Language(models.Model):
    PROFICIENCY_CHOICES = [
        ('basic', 'Básico'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
        ('native', 'Nativo'),
    ]
    
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    language = models.CharField(max_length=50)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='intermediate')
    
    def __str__(self):
        return f"{self.language} ({self.get_proficiency_display()})"


class Certification(models.Model):
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=100)  # Nueva: "AWS Certified Solutions Architect"
    issuing_organization = models.CharField(max_length=100)  # Renombré de "entity"
    issue_date = models.DateField(null=True, blank=True)  # Renombré de certification_date
    expiration_date = models.DateField(null=True, blank=True)
    credential_id = models.CharField(max_length=100, blank=True)
    credential_url = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-issue_date']
        verbose_name = "Certificación"
        verbose_name_plural = "Certificaciones"
    
    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"