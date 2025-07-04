"""
Configuración de Django optimizada para Google App Engine Standard
"""

import os
from .settings import *

# Configuración de producción
DEBUG = False

# Obtener el ID del proyecto de las variables de entorno
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT')
if not PROJECT_ID:
    raise ValueError("GOOGLE_CLOUD_PROJECT debe estar definido en las variables de entorno")

# Secret Key desde variables de entorno
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY debe estar definido en las variables de entorno")

# Hosts permitidos para App Engine y Cloud Run
ALLOWED_HOSTS = [
    '.appspot.com',   # Dominio de App Engine
    '.googleapis.com',
    'localhost',
    '127.0.0.1',
    'rgd-aire-dot-appsindunnova.rj.r.appspot.com',  # URL específica de App Engine
    '.run.app',  # Dominio de Cloud Run
    'rgd-aire-ovihj2yjrq-uc.a.run.app',  # URL específica de Cloud Run
    '*',  # Temporalmente para debugging (quitar en producción)
]

# Configuración CSRF específica para App Engine y Cloud Run
CSRF_TRUSTED_ORIGINS = [
    'https://*.appspot.com',
    'https://rgd-aire-dot-appsindunnova.rj.r.appspot.com',
    'https://*.run.app',
    'https://rgd-aire-ovihj2yjrq-uc.a.run.app',
]

# Configuraciones adicionales de CSRF para App Engine
CSRF_COOKIE_DOMAIN = None  # Permitir dominios de App Engine
CSRF_USE_SESSIONS = True   # Usar sesiones para tokens CSRF en lugar de cookies
CSRF_COOKIE_HTTPONLY = False  # Permitir acceso desde JavaScript si es necesario

# Configuración de base de datos para App Engine + Cloud SQL
if os.environ.get('USE_CLOUD_SQL') == 'true':
    # Validar variables requeridas
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'CLOUD_SQL_CONNECTION_NAME']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        raise ValueError(f"Variables de entorno faltantes para Cloud SQL: {missing_vars}")

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ['DB_NAME'],
            'USER': os.environ['DB_USER'],
            'PASSWORD': os.environ['DB_PASSWORD'],
            'HOST': f'/cloudsql/{os.environ["CLOUD_SQL_CONNECTION_NAME"]}',
            'PORT': '',
            'CONN_MAX_AGE': 300,
            'OPTIONS': {
                'connect_timeout': 60,
                'application_name': 'rgd_aire_appengine',
                'client_encoding': 'UTF8',
                'options': '-c client_encoding=UTF8'
            },
        }
    }
else:
    # Para desarrollo local: usar PostgreSQL en localhost o mediante Cloud SQL Proxy
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

# Configuración de archivos estáticos con WhiteNoise (más económico para Cloud Run)
# WhiteNoise sirve archivos estáticos directamente desde el contenedor
# (WhiteNoise ya está configurado en la lista MIDDLEWARE más abajo)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_AUTOREFRESH = False
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_MAX_AGE = 31536000  # 1 año de cache

# URLs y directorios para archivos estáticos
STATIC_URL = '/static/'
# Ensure BASE_DIR is a string for os.path.join compatibility
STATIC_ROOT = os.path.join(str(BASE_DIR), 'staticfiles')
STATICFILES_DIRS = [os.path.join(str(BASE_DIR), 'static')]

# Configuración de Google Cloud Storage SOLO para archivos de media (uploads)
GS_BUCKET_NAME = os.environ.get('GS_BUCKET_NAME')
if not GS_BUCKET_NAME:
    raise ValueError("GS_BUCKET_NAME debe estar definido en las variables de entorno")

# En App Engine, las credenciales de GCS se manejan automáticamente
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

GS_PROJECT_ID = PROJECT_ID
GS_DEFAULT_ACL = 'publicRead'
GS_QUERYSTRING_AUTH = False
GS_FILE_OVERWRITE = False

# URL para archivos de media en GCS
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/'

# Configuración de seguridad para App Engine
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuración de email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
if os.environ.get('SENDGRID_API_KEY'):
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = os.environ['SENDGRID_API_KEY']
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@rgdaire.com')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración de logging para App Engine
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
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
        'rgd_aire': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuración de cache mejorada para evitar errores de pymemcache:
if os.environ.get('DISABLE_MEMCACHE') == 'true':
    # Cache desactivado para evitar problemas de dependencias
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
elif os.environ.get('USE_CLOUD_SQL') == 'true':
    # En App Engine: usar cache en memoria local como alternativa segura
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'rgd-aire-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }
else:
    # En local/desarrollo: usar caché en memoria 
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# Configuración de internacionalización
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# Middleware optimizado para App Engine
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Debe ir después de SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración optimizada para arranque rápido en App Engine
DEBUG = False

# Optimizaciones de rendimiento para arranque rápido
CONN_MAX_AGE = 300  # Reutilizar conexiones de BD por 5 minutos
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'  # Evitar warnings

# Deshabilitar migraciones automáticas en runtime para arranque más rápido
# Las migraciones se ejecutan solo durante deployment
MIGRATION_MODULES = {}

# Optimizar INSTALLED_APPS - remover apps innecesarias en producción
INSTALLED_APPS = [
    # Django core (mínimo necesario)
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # Para formateo de números y fechas en templates
    
    # Apps del proyecto
    'users',
    'crm',
    'proyectos', 
    'servicios',
    'mantenimiento',
    'mejora_continua',
    'tasks',
    
    # Third party (solo los esenciales)
    'storages',  # Para Google Cloud Storage
    'crispy_forms',  # Para formularios en templates
    'crispy_bootstrap5',  # Bootstrap 5 para crispy forms (ya instalado)
]

# Configuración de crispy forms para Bootstrap 5
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Mensajes de verificación al iniciar
print(f"✅ App Engine configuración cargada para proyecto: {PROJECT_ID}")
print(f"✅ Base de datos: {'Cloud SQL' if os.environ.get('USE_CLOUD_SQL') == 'true' else 'Configuración local'}")
print(f"✅ Almacenamiento: Google Cloud Storage ({GS_BUCKET_NAME})")
print(f"✅ Cache: {'Memcache nativo' if os.environ.get('USE_CLOUD_SQL') == 'true' else 'LocMemCache (dev)'}")
