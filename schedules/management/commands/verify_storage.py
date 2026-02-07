# management/commands/verify_storage.py
# Ejecutar con: python manage.py verify_storage

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage

class Command(BaseCommand):
    help = 'Verifica la configuración del storage por defecto'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== VERIFICACIÓN DE STORAGE ===\n')
        )

        # 1. Verificar configuración en settings
        self.check_settings_config()
        
        # 2. Verificar default_storage real
        self.check_default_storage()
        
        # 3. Verificar importaciones
        self.check_imports()
        
        # 4. Test de uso real
        self.test_real_usage()

    def check_settings_config(self):
        self.stdout.write('1. CONFIGURACIÓN EN SETTINGS:')
        
        self.stdout.write(f'   DEBUG: {settings.DEBUG}')
        self.stdout.write(f'   DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}')
        
        # Verificar si la clase existe
        try:
            from django.utils.module_loading import import_string
            storage_class = import_string(settings.DEFAULT_FILE_STORAGE)
            self.stdout.write(f'   ✅ Clase de storage importable: {storage_class}')
        except Exception as e:
            self.stdout.write(f'   ❌ Error importando storage class: {e}')

    def check_default_storage(self):
        self.stdout.write('\n2. DEFAULT_STORAGE REAL:')
        
        self.stdout.write(f'   Clase real: {default_storage.__class__.__name__}')
        self.stdout.write(f'   Módulo: {default_storage.__class__.__module__}')
        self.stdout.write(f'   Path completo: {default_storage.__class__}')
        
        # Verificar si es realmente MinIO
        if 'MinioMediaStorage' in default_storage.__class__.__name__:
            self.stdout.write('   ✅ Usando MinIO Storage')
            
            # Verificar atributos específicos de MinIO
            if hasattr(default_storage, 'bucket_name'):
                self.stdout.write(f'   Bucket: {default_storage.bucket_name}')
            if hasattr(default_storage, 'client'):
                self.stdout.write(f'   Cliente MinIO: {default_storage.client._base_url}')
        else:
            self.stdout.write('   ❌ NO usando MinIO Storage')

    def check_imports(self):
        self.stdout.write('\n3. VERIFICACIÓN DE IMPORTACIONES:')
        
        # Verificar django-minio-storage
        try:
            import minio_storage
            self.stdout.write(f'   ✅ django-minio-storage: {minio_storage.__version__}')
        except ImportError:
            self.stdout.write('   ❌ django-minio-storage no instalado')
            return
        
        # Verificar MinioMediaStorage
        try:
            from minio_storage.storage import MinioMediaStorage
            storage_instance = MinioMediaStorage()
            self.stdout.write('   ✅ MinioMediaStorage importable')
            self.stdout.write(f'   Bucket: {storage_instance.bucket_name}')
        except Exception as e:
            self.stdout.write(f'   ❌ Error creando MinioMediaStorage: {e}')
        
        # Verificar cliente MinIO
        try:
            from minio import Minio
            self.stdout.write('   ✅ Cliente MinIO importable')
        except ImportError:
            self.stdout.write('   ❌ Cliente MinIO no instalado')

    def test_real_usage(self):
        self.stdout.write('\n4. TEST DE USO REAL:')
        
        from django.core.files.base import ContentFile
        
        try:
            # Test usando default_storage (lo que usa Django realmente)
            test_content = "Test de uso real"
            test_file = ContentFile(test_content.encode('utf-8'))
            
            saved_name = default_storage.save('test/real_usage_test.txt', test_file)
            self.stdout.write(f'   ✅ Archivo guardado: {saved_name}')
            
            file_url = default_storage.url(saved_name)
            self.stdout.write(f'   📎 URL: {file_url}')
            
            # Verificar si la URL apunta a MinIO
            if 'bucket-production-266a.up.railway.app' in file_url:
                self.stdout.write('   ✅ URL apunta a MinIO - CORRECTO')
            else:
                self.stdout.write('   ❌ URL NO apunta a MinIO - PROBLEMA')
            
            # Limpiar
            default_storage.delete(saved_name)
            self.stdout.write('   🗑️ Archivo eliminado')
            
        except Exception as e:
            self.stdout.write(f'   ❌ Error en test real: {e}')
            import traceback
            traceback.print_exc()

        # 5. Verificar configuración de apps instaladas
        self.stdout.write('\n5. APPS INSTALADAS:')
        installed_apps = getattr(settings, 'INSTALLED_APPS', [])
        minio_apps = [app for app in installed_apps if 'minio' in app.lower()]
        if minio_apps:
            self.stdout.write(f'   ✅ Apps MinIO encontradas: {minio_apps}')
        else:
            self.stdout.write('   ⚠️ No se encontraron apps relacionadas con MinIO')
            self.stdout.write('   💡 Asegúrate de agregar "minio_storage" a INSTALLED_APPS')