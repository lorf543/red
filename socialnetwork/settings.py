from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

import cloudinary
import cloudinary.uploader
import cloudinary.api

# Carga las variables desde .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG=False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",") 


CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:8000"
).split(",")


ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# INSTALLED APPS

INSTALLED_APPS = [
    # 'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.sites',

    #Terceros
    'gunicorn',
    'whitenoise.runserver_nostatic',
    'cloudinary',
    'cloudinary_storage',
    'django_cleanup',
    'debug_toolbar',
    'widget_tweaks',
    'psycopg2',
    'django.contrib.humanize',
    'schema_viewer',
    'ckeditor',
    'ckeditor_uploader',

    # Tus apps
    'core',
    'schedules',
    'teachers',
    'commentslikes',
    'notifications.apps.NotificationsConfig',
    'a_blog.apps.ABlogConfig',

    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]


TEXT_EDITOR = "djangocms_text_ckeditor5.ckeditor5"

SITE_ID = 1

# MIDDLEWARE
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    # 'core.middleware.ProfileCompletionMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'socialnetwork.urls'

# ----------------------------
# TEMPLATES
# ----------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.profile_data',
            ],
        },
    },
]

WSGI_APPLICATION = 'socialnetwork.wsgi.application'

ASGI_APPLICATION = 'socialnetwork.asgi.application'

# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer",
#     }
# }

# ----------------------------
# DATABASE
# ----------------------------

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',    
#     }
# }

DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv("DATABASE_PUBLIC_URL")
    )
}

# ----------------------------
# PASSWORD VALIDATION
# ----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ----------------------------
# INTERNATIONALIZATION
# ----------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Santo_Domingo'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]


STATIC_URL = "/static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Crear directorio media si no existe
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)



if DEBUG:
    # ========== DESARROLLO ==========
    # Sirve archivos desde el sistema local
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
    CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

else:
    # ========== PRODUCCIÓN ==========

    # WhiteNoise para servir archivos estáticos de manera eficiente
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

    # Cloudinary para archivos media
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
    CKEDITOR_5_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

    # Configuración de Cloudinary
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME", "dvnfk6qn8"),
        "API_KEY": os.getenv("CLOUDINARY_API_KEY"),
        "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
        "max_image_width": 4000,
        "max_image_height": 4000,
        "secure": True,
        "SECURE_URL": True
    }



    cloudinary.config(
        cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
        api_key=CLOUDINARY_STORAGE["API_KEY"],
        api_secret=CLOUDINARY_STORAGE["API_SECRET"],
        secure=True,
    )

    MEDIA_URL = f"https://res.cloudinary.com/{CLOUDINARY_STORAGE['CLOUD_NAME']}/"



WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# ----------------------------
# ALLAUTH CONFIG
# ----------------------------
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]


SOCIALACCOUNT_ADAPTER = "core.adapters.CustomSocialAccountAdapter"
ACCOUNT_ADAPTER = "core.adapters.CustomAccountAdapter"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": os.getenv("google_client_id"),
                "secret": os.getenv("google_secret"),
                "key": "",
                "settings": {
                    "scope": ["profile", "email"],
                    "auth_params": {"access_type": "online"},
                },
            }
        ]
    }
}


ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_USERNAME_REQUIRED = False

ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]

ACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_LOGIN_ON_GET = True

LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "/accounts/login/"

ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = True

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ACCOUNT_PASSWORD_RESET_REDIRECT_URL = '/accounts/login/?password_changed=true'

# ----------------------------
# Archivos media & tamaño máximo
# ----------------------------
MAX_UPLOAD_SIZE = 5242880  # 5MB
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ----------------------------
# CACHE (opcional)
# ----------------------------
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
#         'LOCATION': os.path.join(BASE_DIR, 'django_cache'),
#     }
# }


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'), 
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,

            'IGNORE_EXCEPTIONS': True,  #
        },
        'KEY_PREFIX': 'https://itlasocial.org/', 
        'TIMEOUT': 300, 
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'height': 300,
        
        # 1. ESTO ASEGURA QUE EL EDITOR TOME EL 100% DEL ANCHO DE SU CONTENEDOR
        'width': '100%', 
        
        # 2. AGREGAMOS 'maximize' A LOS PLUGINS EXTRA
        'extraPlugins': 'autogrow,justify,maximize',
        
        'toolbarGroups': [
            {'name': 'basicstyles', 'groups': ['basicstyles', 'cleanup']},
            {'name': 'paragraph', 'groups': ['list', 'align']},
            
            # 3. AGREGAMOS EL GRUPO 'tools' QUE CONTIENE EL BOTÓN DE PANTALLA COMPLETA
            {'name': 'tools'}, 
        ],
        
        'removeButtons': 'Strike,Subscript,Superscript,CreateDiv,Blockquote,BidiLtr,BidiRtl,Language,Indent,Outdent',
        'autoGrow_minHeight': 200,
        'justifyClasses': [], 
        'allowedContent': True,
    }
}


CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"