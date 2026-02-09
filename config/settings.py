"""
Django settings for music_backend project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Detect if running on PythonAnywhere
ON_PYTHONANYWHERE = 'PYTHONANYWHERE_DOMAIN' in os.environ or 'kofficobbin.pythonanywhere.com' in os.environ.get('ALLOWED_HOSTS', '')

# Allowed hosts configuration
if ON_PYTHONANYWHERE or not DEBUG:
    ALLOWED_HOSTS = ['kofficobbin.pythonanywhere.com', 'www.kofficobbin.pythonanywhere.com']
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'musewave',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'musewave.middleware.RequestLoggingMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - Using SQLite for file-based storage similar to JSON
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

# Static files configuration for both local and PythonAnywhere
if ON_PYTHONANYWHERE:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')
else:
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Additional locations of static files (for development)
STATICFILES_DIRS = [
    # Add any additional static directories here if needed
    # BASE_DIR / 'static',
]

# Media files configuration
MEDIA_URL = '/media/'

if ON_PYTHONANYWHERE:
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
else:
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'EXCEPTION_HANDLER': 'musewave.exceptions.custom_exception_handler',
}

# CORS settings
# Adjust for production - don't allow all origins in production!
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # In production, specify exact origins
    CORS_ALLOWED_ORIGINS = [
        'https://kofficobbin.pythonanywhere.com',
        # Add your frontend domain here if different
    ]

CORS_ALLOW_CREDENTIALS = True

# Custom settings
DB_DATA_DIR = BASE_DIR / 'db-data'

# Security settings for production (PythonAnywhere)
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # PythonAnywhere handles SSL
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'