# management/commands/debug_minio_complete.py
# Guardar en: tu_app/management/commands/debug_minio_complete.py
# Ejecutar con: python manage.py debug_minio_complete

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import io
from PIL import Image

class Command(BaseCommand):
    help = 'Diagnóstico completo de MinIO con imágenes'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== DIAGNÓSTICO COMPLETO MINIO ===\n')
        )

        # 1. Verificar configuración
        self.check_configuration()
        
        # 2. Test de conectividad básica
        self.test_basic_connectivity()
        
        # 3. Test de subida de texto
        self.test_text_upload()
        
        # 4. Test de subida de imagen
        self.test_image_upload()
        
        # 5. Verificar cliente MinIO directo
        self.test_direct_minio()
        
        # 6. Verificar políticas del bucket
        self.check_bucket_policies()

    def check_configuration(self):
        self.stdout.write('1. VERIFICACIÓN DE CONFIGURACIÓN:')
        
        config_items = [
            ('DEBUG', getattr(settings, 'DEBUG', 'NO DEFINIDO')),
            ('DEFAULT_FILE_STORAGE', getattr(settings, 'DEFAULT_FILE_STORAGE', 'NO DEFINIDO')),
            ('MEDIA_URL', getattr(settings, 'MEDIA_URL', 'NO DEFINIDO')),
            ('MINIO_STORAGE_ENDPOINT', getattr(settings, 'MINIO_STORAGE_ENDPOINT', 'NO DEFINIDO')),
            ('MINIO_STORAGE_MEDIA_BUCKET_NAME', getattr(settings, 'MINIO_STORAGE_MEDIA_BUCKET_NAME', 'NO DEFINIDO')),
            ('MINIO_STORAGE_USE_HTTPS', getattr(settings, 'MINIO_STORAGE_USE_HTTPS', 'NO DEFINIDO')),
            ('MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET', getattr(settings, 'MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET', 'NO DEFINIDO')),
            ('MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY', getattr(settings, 'MINIO_STORAGE_AUTO_CREATE_MEDIA_POLICY', 'NO DEFINIDO')),
            ('MINIO_STORAGE_MEDIA_USE_PRESIGNED', getattr(settings, 'MINIO_STORAGE_MEDIA_USE_PRESIGNED', 'NO DEFINIDO')),
        ]
        
        for key, value in config_items:
            if 'KEY' in key and value != 'NO DEFINIDO':
                display_value = f"{str(value)[:4]}...{str(value)[-4:]}"
            else:
                display_value = value
            self.stdout.write(f'   {key}: {display_value}')

    def test_basic_connectivity(self):
        self.stdout.write('\n2. TEST DE CONECTIVIDAD BÁSICA:')
        
        try:
            # Verificar que podemos acceder al storage
            storage_class = default_storage.__class__.__name__
            self.stdout.write(f'   Storage Class: {storage_class}')
            
            if 'MinioMediaStorage' in storage_class:
                self.stdout.write('   ✅ Usando MinIO Storage')
            else:
                self.stdout.write(f'   ❌ NO usando MinIO Storage. Usando: {storage_class}')
                return False
            
            # Intentar listar contenido
            dirs, files = default_storage.listdir('')
            self.stdout.write(f'   ✅ Conexión exitosa')
            self.stdout.write(f'   📁 Directorios: {len(dirs)}')
            self.stdout.write(f'   📄 Archivos: {len(files)}')
            return True
            
        except Exception as e:
            self.stdout.write(f'   ❌ Error de conectividad: {e}')
            return False

    def test_text_upload(self):
        self.stdout.write('\n3. TEST DE SUBIDA DE TEXTO:')
        
        try:
            test_content = "Archivo de prueba MinIO"
            test_file = ContentFile(test_content.encode('utf-8'))
            test_filename = 'debug/test_text.txt'
            
            # Subir archivo
            saved_name = default_storage.save(test_filename, test_file)
            self.stdout.write(f'   ✅ Archivo de texto subido: {saved_name}')
            
            # Verificar URL
            file_url = default_storage.url(saved_name)
            self.stdout.write(f'   📎 URL: {file_url}')
            
            # Verificar existencia
            if default_storage.exists(saved_name):
                self.stdout.write('   ✅ Archivo confirmado en storage')
                
                # Verificar contenido
                with default_storage.open(saved_name, 'r') as f:
                    retrieved_content = f.read()
                    if retrieved_content.strip() == test_content:
                        self.stdout.write('   ✅ Contenido verificado')
                    else:
                        self.stdout.write('   ❌ Contenido no coincide')
                
                # Limpiar
                default_storage.delete(saved_name)
                self.stdout.write('   🗑️ Archivo eliminado')
                return True
            else:
                self.stdout.write('   ❌ Archivo no encontrado')
                return False
                
        except Exception as e:
            self.stdout.write(f'   ❌ Error en subida de texto: {e}')
            import traceback
            traceback.print_exc()
            return False

    def test_image_upload(self):
        self.stdout.write('\n4. TEST DE SUBIDA DE IMAGEN:')
        
        try:
            # Crear imagen de prueba
            img = Image.new('RGB', (100, 100), color='red')
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='JPEG')
            img_buffer.seek(0)
            
            # Crear ContentFile con la imagen
            image_file = ContentFile(img_buffer.getvalue(), name='test_image.jpg')
            test_filename = 'debug/test_image.jpg'
            
            self.stdout.write(f'   📝 Imagen creada: {len(image_file.read())} bytes')
            image_file.seek(0)  # Reset pointer
            
            # Subir imagen
            saved_name = default_storage.save(test_filename, image_file)
            self.stdout.write(f'   ✅ Imagen subida: {saved_name}')
            
            # Verificar URL
            file_url = default_storage.url(saved_name)
            self.stdout.write(f'   📎 URL: {file_url}')
            
            # Verificar existencia y tamaño
            if default_storage.exists(saved_name):
                file_size = default_storage.size(saved_name)
                self.stdout.write(f'   ✅ Imagen confirmada en storage ({file_size} bytes)')
                
                # Verificar que se puede abrir
                try:
                    with default_storage.open(saved_name, 'rb') as f:
                        img_data = f.read()
                        if len(img_data) > 0:
                            self.stdout.write('   ✅ Imagen legible desde storage')
                        else:
                            self.stdout.write('   ❌ Imagen vacía en storage')
                except Exception as e:
                    self.stdout.write(f'   ❌ Error leyendo imagen: {e}')
                
                # Limpiar
                default_storage.delete(saved_name)
                self.stdout.write('   🗑️ Imagen eliminada')
                return True
            else:
                self.stdout.write('   ❌ Imagen no encontrada')
                return False
                
        except Exception as e:
            self.stdout.write(f'   ❌ Error en subida de imagen: {e}')
            import traceback
            traceback.print_exc()
            return False

    def test_direct_minio(self):
        self.stdout.write('\n5. TEST DIRECTO CLIENTE MINIO:')
        
        try:
            from minio import Minio
            
            # Crear cliente directo
            client = Minio(
                settings.MINIO_STORAGE_ENDPOINT,
                access_key=settings.MINIO_STORAGE_ACCESS_KEY,
                secret_key=settings.MINIO_STORAGE_SECRET_KEY,
                secure=settings.MINIO_STORAGE_USE_HTTPS
            )
            
            # Verificar buckets
            buckets = list(client.list_buckets())
            bucket_names = [b.name for b in buckets]
            self.stdout.write(f'   📦 Buckets disponibles: {bucket_names}')
            
            # Verificar bucket específico
            bucket_name = settings.MINIO_STORAGE_MEDIA_BUCKET_NAME
            if bucket_name in bucket_names:
                self.stdout.write(f'   ✅ Bucket "{bucket_name}" existe')
                
                # Listar objetos en el bucket
                objects = list(client.list_objects(bucket_name, recursive=True))
                self.stdout.write(f'   📄 Objetos en bucket: {len(objects)}')
                
                if len(objects) > 0:
                    self.stdout.write('   Algunos objetos:')
                    for obj in objects[:5]:
                        self.stdout.write(f'     - {obj.object_name} ({obj.size} bytes)')
                
                # Test de subida directa
                test_content = b"Test directo MinIO"
                test_object = 'debug/direct_test.txt'
                
                client.put_object(
                    bucket_name,
                    test_object,
                    data=io.BytesIO(test_content),
                    length=len(test_content)
                )
                
                self.stdout.write(f'   ✅ Subida directa exitosa: {test_object}')
                
                # Verificar que se subió
                try:
                    obj_stat = client.stat_object(bucket_name, test_object)
                    self.stdout.write(f'   ✅ Objeto confirmado: {obj_stat.size} bytes')
                    
                    # Limpiar
                    client.remove_object(bucket_name, test_object)
                    self.stdout.write('   🗑️ Objeto eliminado')
                    
                except Exception as e:
                    self.stdout.write(f'   ❌ Error verificando objeto: {e}')
                
            else:
                self.stdout.write(f'   ❌ Bucket "{bucket_name}" no existe')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Error en test directo: {e}')

    def check_bucket_policies(self):
        self.stdout.write('\n6. VERIFICACIÓN DE POLÍTICAS:')
        
        try:
            from minio import Minio
            import json
            
            client = Minio(
                settings.MINIO_STORAGE_ENDPOINT,
                access_key=settings.MINIO_STORAGE_ACCESS_KEY,
                secret_key=settings.MINIO_STORAGE_SECRET_KEY,
                secure=settings.MINIO_STORAGE_USE_HTTPS
            )
            
            bucket_name = settings.MINIO_STORAGE_MEDIA_BUCKET_NAME
            
            try:
                policy = client.get_bucket_policy(bucket_name)
                self.stdout.write(f'   ✅ Bucket tiene política configurada')
                
                # Intentar parsear la política
                try:
                    policy_json = json.loads(policy)
                    statements = policy_json.get('Statement', [])
                    self.stdout.write(f'   📋 Statements en política: {len(statements)}')
                    
                    for i, stmt in enumerate(statements):
                        effect = stmt.get('Effect', 'Unknown')
                        actions = stmt.get('Action', [])
                        self.stdout.write(f'     Statement {i+1}: {effect} - {actions}')
                        
                except:
                    self.stdout.write('   ⚠️ No se pudo parsear la política')
                    
            except Exception as e:
                self.stdout.write(f'   ❌ No hay política o error: {e}')
                self.stdout.write('   🔧 Intentando crear política pública...')
                
                # Crear política pública
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
                
                try:
                    client.set_bucket_policy(bucket_name, json.dumps(policy))
                    self.stdout.write('   ✅ Política pública creada')
                except Exception as e:
                    self.stdout.write(f'   ❌ Error creando política: {e}')
                
        except Exception as e:
            self.stdout.write(f'   ❌ Error verificando políticas: {e}')