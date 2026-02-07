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


# ----------------------------
# SECURITY
# ----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "valor_por_defecto_para_dev")
DEBUG = os.getenv("DEBUG", "False") == "True"



# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
ALLOWED_HOSTS = ['*']
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

# ESTO ES VITAL PARA TÚNELES:
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Tu lógica de CSRF está bien para testear
CSRF_TRUSTED_ORIGINS = [
    "https://*.devtunnels.ms",
    "http://localhost:8000"
]

# ----------------------------
# INSTALLED APPS
# ----------------------------
INSTALLED_APPS = [
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

    # Tus apps
    'core',
    'schedules',
    'teachers',
    'commentslikes',
    'notifications.apps.NotificationsConfig',

    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

# ----------------------------
# MIDDLEWARE
# ----------------------------
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
    'core.middleware.ProfileCompletionMiddleware',
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
LANGUAGE_CODE = 'es-la'
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


# CONFIGURACIÓN SEGÚN ENTORNO (Desarrollo vs Producción)


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
    }



    cloudinary.config(
        cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
        api_key=CLOUDINARY_STORAGE["API_KEY"],
        api_secret=CLOUDINARY_STORAGE["API_SECRET"],
        secure=True,
    )

    MEDIA_URL = f"https://res.cloudinary.com/{CLOUDINARY_STORAGE['CLOUD_NAME']}/"


# CONFIGURACIÓN DE WHITENOISE


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


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'METHOD': 'oauth2',
        'VERIFIED_EMAIL': False,
        'APP': {
            'client_id': os.getenv("google_client_id"),
            'secret': os.getenv("google_secret"),
            'key': ''
        }
    }
}


# Configuración de allauth
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = True

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_SESSION_REMEMBER = True

LOGIN_REDIRECT_URL = 'home'

LOGIN_URL = 'account_login'

ACCOUNT_FORMS = {
    'login': 'core.forms.CustomLoginForm',
    'signup': 'core.forms.CustomSignupForm',
}

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
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'django_cache'),
    }
}
