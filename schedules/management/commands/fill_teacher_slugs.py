from django.core.management.base import BaseCommand
from schedules.models import Teacher
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Genera slugs únicos para todos los Teachers, corrigiendo vacíos y duplicados"

    def handle(self, *args, **options):
        teachers = Teacher.objects.all()
        slug_map = set()  # para llevar control de slugs ya usados
        updated_count = 0

        for t in teachers:
            original_slug = t.slug

            # Si no tiene slug o está duplicado
            if not t.slug or t.slug in slug_map or Teacher.objects.filter(slug=t.slug).exclude(id=t.id).exists():
                base_slug = slugify(t.full_name)
                slug = base_slug
                counter = 1
                while slug in slug_map or Teacher.objects.filter(slug=slug).exclude(id=t.id).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                t.slug = slug
                t.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"Slug generado/corregido para: {t.full_name} -> {t.slug}"))

            # Añadir el slug al set
            slug_map.add(t.slug)

        if updated_count == 0:
            self.stdout.write(self.style.WARNING("Todos los teachers ya tenían slugs únicos."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Se generaron/corregieron {updated_count} slugs correctamente."))
