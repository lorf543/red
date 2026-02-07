from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.text import slugify



class Subject(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Lunes'),
        ('tue', 'Martes'),
        ('wed', 'Miércoles'),
        ('thu', 'Jueves'),
        ('fri', 'Viernes'),
        ('sat', 'Sábado'),
        ('sun', 'Domingo'),
    ]

    HOURS_CHOICES = [
        ('08:00', '08:00 AM'),
        ('10:00', '10:00 AM'),
        ('12:00', '12:00 PM'),
        ('14:00', '02:00 PM'),
        ('16:00', '04:00 PM'),
        ('18:00', '06:00 PM'),
        ('20:00', '08:00 PM'),
    ]
    
    MODALIDAD = [
        ('Presencial','presencial'),
        ('Virtual','Virtual')
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    credits = models.PositiveIntegerField(default=3)
    
    modalidad = models.CharField(max_length=50, choices=MODALIDAD, blank=True, null=True)

    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK, verbose_name="Dia", blank=True, null=True)
    hour = models.CharField(max_length=5, choices=HOURS_CHOICES, verbose_name="Hora", blank=True, null=True)
    
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True) 

    teacher = models.ForeignKey(
        "Teacher", 
        on_delete=models.SET_NULL,
        blank=True, 
        null=True,
        related_name='subjects',
        verbose_name="Profesor"
    )

    def __str__(self):
        return f"{self.name}"


        
    def subject_schedule(self):
        if self.hour:
            try:
                # Convierte el string (ej: "14:30") a objeto time
                parsed_hour = datetime.strptime(self.hour, "%H:%M").time()
                return f"{self.get_day_display()} - {parsed_hour.strftime('%I:%M %p')}"
            except ValueError:
                return f"{self.get_day_display()} - {self.hour}"  # por si el formato es raro
        return f"{self.get_day_display()} - —"
    
    def total_score(self):
        return self.votes.aggregate(total=models.Sum('vote_type'))['total'] or 0

from django.db import models
from django.utils.text import slugify

class Teacher(models.Model):
    full_name = models.CharField(max_length=100)
    area = models.CharField(max_length=100, blank=True)
    slug = models.SlugField(blank=True)  

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.full_name)  
            slug = base_slug
            counter = 1
            while Teacher.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

    def total_score(self):
        return self.votes.aggregate(total=models.Sum('vote_type'))['total'] or 0



