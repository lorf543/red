# management/commands/check_minio.py
# Guardar en: tu_app/management/commands/check_minio.py
# Ejecutar con: python manage.py check_minio

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class Command(BaseCommand):
    help = 'Verifica la configuración y conectividad de MinIO'

    def add_arguments(self, parser):
        parser.add_argument(
            '--upload-test',
            action='store_true',
            help='Ejecuta test de subida de archivo',
        )
        parser.add_argument(
            '--fix-policies',
            action='store_true',
            help='Intenta corregir políticas de bucket',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== VERIFICACIÓN MINIO ===\n')
        )

        # Verificar configuración
        self.check_configuration()
        
        # Verificar conectividad
        self.check_connectivity()
        
        if options['upload_test']:
            self.test_upload()
            
        if options['fix_policies']:
            self.fix_bucket_policies()

    def check_configuration(self):
        self.stdout.write('1. Verificando configuración...')
        
        required_settings = [
            'MINIO_STORAGE_ENDPOINT',
            'MINIO_STORAGE_ACCESS_KEY',
            'MINIO_STORAGE_SECRET_KEY',
            'MINIO_STORAGE_MEDIA_BUCKET_NAME'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                # Ocultar claves sensibles
                if 'KEY' in setting:
                    display_value = f"{value[:4]}...{value[-4:]}"
                else:
                    display_value = value
                self.stdout.write(f"   ✅ {setting}: {display_value}")
            else:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ {setting}: NO DEFINIDO")
                )

    def check_connectivity(self):
        self.stdout.write('\n2. Verificando conectividad...')
        
        try:
            # Intentar listar contenido
            dirs, files = default_storage.listdir('')
            self.stdout.write('   ✅ Conexión exitosa a MinIO')
            self.stdout.write(f'   📁 Directorios encontrados: {len(dirs)}')
            self.stdout.write(f'   📄 Archivos encontrados: {len(files)}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error de conexión: {e}')
            )

    def test_upload(self):
        self.stdout.write('\n3. Test de subida...')
        
        test_content = "Test file from Django management command"
        test_file_name = 'test/management_test.txt'
        
        try:
            # Subir archivo
            test_file = ContentFile(test_content.encode('utf-8'))
            saved_name = default_storage.save(test_file_name, test_file)
            
            self.stdout.write(f'   ✅ Archivo subido: {saved_name}')
            
            # Verificar URL
            file_url = default_storage.url(saved_name)
            self.stdout.write(f'   📎 URL generada: {file_url}')
            
            # Verificar existencia
            if default_storage.exists(saved_name):
                self.stdout.write('   ✅ Archivo confirmado en storage')
                
                # Limpiar
                default_storage.delete(saved_name)
                self.stdout.write('   🗑️ Archivo de prueba eliminado')
            else:
                self.stdout.write(
                    self.style.ERROR('   ❌ Archivo no encontrado')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error en subida: {e}')
            )

    def fix_bucket_policies(self):
        self.stdout.write('\n4. Intentando corregir políticas...')
        
        try:
            if 'minio_storage' in settings.DEFAULT_FILE_STORAGE:
                from minio_storage.storage import MinioMediaStorage
                from minio.commonconfig import ENABLED, Filter
                from minio.notificationconfig import NotificationConfig
                import json
                
                storage = MinioMediaStorage()
                bucket_name = storage.bucket_name
                
                # Política para hacer el bucket público para lectura
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": "s3:GetObject",
                            "Resource": f"arn:aws:s3:::{bucket_name}/*"
                        }
                    ]
                }
                
                # Aplicar política
                storage.client.set_bucket_policy(
                    bucket_name, 
                    json.dumps(policy)
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Política aplicada al bucket {bucket_name}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Error aplicando políticas: {e}')
            )