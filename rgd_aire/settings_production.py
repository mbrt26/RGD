"""
Configuración de Django para producción en Google Cloud Platform
"""

import os
from .settings import *
from google.cloud import secretmanager

# Configuración de producción
DEBUG = False

# Obtener el ID del proyecto de las variables de entorno
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

# Función para obtener secretos de Secret Manager
def get_secret(secret_id):
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error al obtener el secreto {secret_id}: {e}")
        return None

# Secret Key desde Secret Manager
SECRET_KEY = get_secret('django-secret-key') or os.environ.get('SECRET_KEY')

# Hosts permitidos
ALLOWED_HOSTS = [
    '.run.app',  # Para Cloud Run
    '.googleapis.com',
    'localhost',
    '127.0.0.1',
]

# Si hay un dominio personalizado, agregarlo
if 'DOMAIN' in os.environ:
    ALLOWED_HOSTS.append(os.environ['DOMAIN'])

# Configuración de base de datos (Cloud SQL)
if os.environ.get('USE_CLOUD_SQL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': get_secret('db-password') or os.environ.get('DB_PASSWORD'),
            'HOST': f'/cloudsql/{os.environ.get("CLOUD_SQL_CONNECTION_NAME")}',
            'PORT': '5432',
        }
    }
else:
    # Para desarrollo local con PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'rgd_aire_db'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Configuración de archivos estáticos y media con Google Cloud Storage
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
GS_PROJECT_ID = PROJECT_ID
GS_DEFAULT_ACL = 'publicRead'

# URLs para archivos estáticos y media
STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

# Configuración de seguridad
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuración de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
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

# Email configuration para producción
if os.environ.get('SENDGRID_API_KEY'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = get_secret('sendgrid-api-key') or os.environ.get('SENDGRID_API_KEY')