"""
Configuración de Django para Google Cloud Run
"""

import os
from .settings import *

# Configuración de producción
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Secret Key desde variables de entorno
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here')

# Hosts permitidos para Cloud Run
ALLOWED_HOSTS = [
    '.run.app',
    'rgd-aire-381877373634.us-central1.run.app',
    'localhost',
    '127.0.0.1',
    '*',  # Permitir todos los hosts para Cloud Run
]

# Configuración CSRF para Cloud Run
CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',
    'https://rgd-aire-381877373634.us-central1.run.app',
]

# Configuración adicional de CSRF para Cloud Run
CSRF_COOKIE_HTTPONLY = False  # Permitir acceso a JavaScript
CSRF_USE_SESSIONS = False  # Usar cookies en lugar de sesiones
CSRF_COOKIE_SAMESITE = 'Lax'  # Permitir cookies en peticiones del mismo sitio
CSRF_COOKIE_NAME = 'csrftoken'  # Nombre estándar de la cookie
CSRF_COOKIE_DOMAIN = None  # Permitir cookies en el dominio actual
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'  # Nombre estándar del header

# Configuración de base de datos para Cloud Run + Cloud SQL
if os.environ.get('CLOUD_SQL_CONNECTION_NAME'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'rgdaire'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': f"/cloudsql/{os.environ.get('CLOUD_SQL_CONNECTION_NAME')}",
            'PORT': '5432',
        }
    }
else:
    # Base de datos local para desarrollo
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Configuración de seguridad para HTTPS
SECURE_SSL_REDIRECT = False  # Cloud Run maneja HTTPS automáticamente
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = False  # Cloud Run proxy puede usar HTTP internamente
CSRF_COOKIE_SECURE = False  # Cloud Run proxy puede usar HTTP internamente

# Configuración de archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise para servir archivos estáticos eficientemente
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración adicional de WhiteNoise para MIME types
WHITENOISE_MIMETYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
}
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']

# Configuración de archivos media
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Middleware configuration - add WhiteNoise for static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add this after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'rgd_aire.middleware.DebugCSRFMiddleware',  # Temporal para depuración
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Logging para Cloud Run
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}