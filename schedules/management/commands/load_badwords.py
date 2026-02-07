import csv
import os
from django.core.management.base import BaseCommand
from commentslikes.models import Badword
from django.conf import settings

class Command(BaseCommand):
    help = 'Carga palabras prohibidas desde un archivo CSV a la base de datos'

    def handle(self, *args, **options):
        # Ruta al archivo CSV (ajusta según tu estructura de directorios)
        csv_file_path = os.path.join(settings.BASE_DIR, 'data', 'ARG.csv')

        
        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                words_added = 0
                duplicates = 0
                
                for row in csv_reader:
                    word = row[0].strip()  # Columna A del CSV
                    
                    if word:  # Solo procesar si no está vacío
                        try:
                            # Crear registro sin reemplazo
                            Badword.objects.create(word=word.lower())
                            words_added += 1
                        except:
                            duplicates += 1
                            continue
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'¡Carga completada! \n'
                        f'Palabras añadidas: {words_added} \n'
                        f'Duplicados omitidos: {duplicates}'
                    )
                )
        
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('El archivo ARG.csv no se encontró en la ruta especificada')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ocurrió un error: {str(e)}')
            )