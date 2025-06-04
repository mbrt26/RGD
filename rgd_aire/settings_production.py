"""
Configuración de Django para producción en Google Cloud Platform
Optimizada siguiendo las mejores prácticas de Google Cloud
"""

import os
from .settings import *

# Configuración de producción
DEBUG = False

# Obtener el ID del proyecto de las variables de entorno
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')

# Usar variables de entorno en lugar de llamadas a Secret Manager API
# Esto mejora el rendimiento de arranque y evita problemas de autenticación
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or os.environ.get('SECRET_KEY')

# Hosts permitidos - expandido para mayor compatibilidad
ALLOWED_HOSTS = [
    '.run.app',  # Para Cloud Run
    '.googleapis.com',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',  # Para contenedores
]

# Si hay un dominio personalizado, agregarlo
if 'DOMAIN' in os.environ:
    ALLOWED_HOSTS.append(os.environ['DOMAIN'])

# Validar que CLOUD_SQL_CONNECTION_NAME esté presente cuando USE_CLOUD_SQL=true
if os.environ.get('USE_CLOUD_SQL') and not os.environ.get('CLOUD_SQL_CONNECTION_NAME'):
    raise ValueError(
        "CLOUD_SQL_CONNECTION_NAME debe estar definido cuando USE_CLOUD_SQL=true. "
        "Asegúrate de usar --set-cloudsql-instances en tu despliegue de Cloud Run."
    )

# Configuración de base de datos mejorada
if os.environ.get('USE_CLOUD_SQL'):
    # Validar que todas las variables requeridas estén presentes
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'CLOUD_SQL_CONNECTION_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Variables de entorno faltantes para Cloud SQL: {missing_vars}")
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': f'/cloudsql/{os.environ.get("CLOUD_SQL_CONNECTION_NAME")}',
            'PORT': '',  # Debe estar vacío para socket Unix
            'CONN_MAX_AGE': 600,  # Reutilizar conexiones para mejor rendimiento
            'OPTIONS': {
                'connect_timeout': 60,
                'application_name': 'rgd_aire',
            },
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
            'CONN_MAX_AGE': 300,
        }
    }

# Configuración de archivos estáticos y media con Google Cloud Storage
# Validar que GS_BUCKET_NAME esté definido
GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
if not GS_BUCKET_NAME:
    raise ValueError(
        "GS_BUCKET_NAME debe estar definido para usar Google Cloud Storage. "
        "Agrega --set-env-vars='GS_BUCKET_NAME=tu-bucket-name' en tu despliegue."
    )

DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

GS_PROJECT_ID = PROJECT_ID
GS_DEFAULT_ACL = 'publicRead'
GS_QUERYSTRING_AUTH = False  # No usar URLs firmadas para archivos públicos
GS_FILE_OVERWRITE = False  # No sobrescribir archivos con el mismo nombre

# URLs para archivos estáticos y media
STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

# Configuración de cache (opcional pero recomendado)
if os.environ.get('REDIS_URL'):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
        }
    }

# Configuración de seguridad mejorada
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuración de sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True

# Email configuration mejorada para producción
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
if os.environ.get('SENDGRID_API_KEY'):
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_API_KEY')  # Usar variable de entorno directamente
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@rgdaire.com')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
else:
    # Fallback para desarrollo
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración específica para Cloud Run
if os.environ.get('K_SERVICE'):  # Variable que existe solo en Cloud Run
    # Optimizaciones para Cloud Run
    USE_TZ = True
    TIME_ZONE = 'America/Bogota'  # Ajustar según tu zona horaria
    
    # Configuración de archivos estáticos para Cloud Run
    STATIC_ROOT = '/app/staticfiles'
    
    # Configuración de logging optimizada para Cloud Logging
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '[{levelname}] {asctime} {name} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '[{levelname}] {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
                'level': 'INFO',
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
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'WARNING',  # Reducir logs de DB en producción
                'propagate': False,
            },
            'rgd_aire': {  # Logger específico para tu aplicación
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }

# Configuración de internacionalización
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Configuración de archivos estáticos adicional
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Configuración de middleware optimizada para producción
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Para servir archivos estáticos si es necesario
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de WhiteNoise como backup para archivos estáticos
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False

print(f"✅ Configuración de producción cargada para proyecto: {PROJECT_ID}")
print(f"✅ Base de datos: {'Cloud SQL' if os.environ.get('USE_CLOUD_SQL') else 'Local PostgreSQL'}")
print(f"✅ Almacenamiento: Google Cloud Storage ({GS_BUCKET_NAME})")
print(f"✅ Email backend: {'SendGrid SMTP' if os.environ.get('SENDGRID_API_KEY') else 'Console'}")