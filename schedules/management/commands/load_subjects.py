from django.core.management.base import BaseCommand
from schedules.models import Teacher, Subject
import random

class Command(BaseCommand):
    help = 'Creates 5 subjects for each teacher'

    def handle(self, *args, **options):
        teachers = Teacher.objects.all()
        if not teachers.exists():
            self.stdout.write(self.style.ERROR('No hay profesores en la base de datos.'))
            return

        subject_names = [
            "Matemáticas Avanzadas", "Física Cuántica", "Programación Python", 
            "Base de Datos", "Inteligencia Artificial", "Redes de Computadoras",
            "Cálculo Diferencial", "Álgebra Lineal", "Estadística", "Machine Learning"
        ]
        
        subject_codes = [f"{name[:3].upper()}{random.randint(100, 999)}" for name in subject_names]
        
        created_count = 0
        
        for teacher in teachers:
            for i in range(5):
                name_idx = random.randint(0, len(subject_names)-1)
                name = subject_names[name_idx]

                
                Subject.objects.create(
                    name=name,

                    description=f"Descripción para {name}",
                    credits=random.choice([3, 4, 5]),
                    modalidad=random.choice(['Prencecial', 'Virtual']),
                    day=random.choice(['mon', 'tue', 'wed', 'thu', 'fri']),
                    hour=random.choice(['08:00', '10:00', '12:00', '14:00', '16:00']),
                    teacher=teacher
                )
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Se crearon {created_count} materias para {teachers.count()} profesores.'
            )
        )