from django.core.management.base import BaseCommand
from core.models import UserProfile

class Command(BaseCommand):
    help = 'Update Cloudinary URLs from HTTP to HTTPS'

    def handle(self, *args, **options):
        # Update all models with Cloudinary image fields
        models_to_update = [
            (UserProfile, 'profile_picture'),  # (Model, field_name)
            # Add more models/fields as needed
        ]
        
        total_updated = 0
        
        for model, field_name in models_to_update:
            updated = model.objects.filter(
                **{f'{field_name}__startswith': 'http://res.cloudinary.com'}
            ).update(
                **{field_name: UserProfile.F(field_name).replace('http://', 'https://')}
            )
            
            total_updated += updated
            self.stdout.write(
                self.style.SUCCESS(
                    f'Updated {updated} records in {model.__name__}.{field_name}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Total updated: {total_updated}')
        )