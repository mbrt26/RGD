# Configuración optimizada para bajo costo
from .settings_appengine import *

# Optimizaciones de base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}' if USE_CLOUD_SQL else DB_HOST,
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'CONN_MAX_AGE': 0,  # Cerrar conexiones inmediatamente (ahorra recursos)
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 segundos timeout
            'sslmode': 'disable',  # Reducir overhead SSL interno
        },
        'ATOMIC_REQUESTS': True,  # Mejor manejo de transacciones
    }
}

# Cache mínimo (sin Memcache para ahorrar costos)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 100,  # Límite bajo para memoria
        }
    }
}

# Sesiones optimizadas
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hora (reducido de 2 semanas)
SESSION_SAVE_EVERY_REQUEST = False  # No guardar en cada request

# Logging mínimo (reduce escrituras)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',  # Solo warnings y errores
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django.db.backends': {
            'handlers': [],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Middleware optimizado (quitar innecesarios)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Servir estáticos eficientemente
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Archivos estáticos con WhiteNoise (más eficiente)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_AUTOREFRESH = False
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_MAX_AGE = 31536000  # 1 año

# Optimizaciones de rendimiento
CONN_MAX_AGE = 0  # No mantener conexiones abiertas
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Límite razonable

# Desactivar características no usadas
USE_I18N = False  # Si no usas internacionalización
USE_L10N = False  # Si no usas localización

# Email optimizado (usar servicio externo es más barato)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Solo para desarrollo