#!/usr/bin/env python3
"""
Archivo principal para Google App Engine
Este archivo es requerido por App Engine cuando se usa 'script: auto' en app.yaml
"""

import os
import sys
import logging
from django.core.wsgi import get_wsgi_application
from django.core.management import execute_from_command_line, call_command
from django.conf import settings

# Agregar el directorio actual al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_appengine')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_database():
    """Ejecuta migraciones con manejo de errores mejorado y forzado"""
    try:
        logger.info("🔄 Iniciando proceso de migraciones completo...")
        
        # Paso 1: Verificar y crear migraciones si es necesario
        logger.info("📋 Generando migraciones si es necesario...")
        try:
            call_command('makemigrations', verbosity=1, interactive=False)
        except Exception as e:
            logger.warning(f"⚠️ Advertencia en makemigrations: {e}")
        
        # Paso 2: Ejecutar migraciones críticas primero
        logger.info("🚀 Ejecutando migraciones críticas de users...")
        try:
            call_command('migrate', 'users', '0004_add_missing_fields', verbosity=2, interactive=False)
        except Exception as users_migrate_error:
            logger.warning(f"⚠️ Error en migración específica de users: {users_migrate_error}")
        
        # Paso 3: Ejecutar todas las migraciones
        logger.info("🚀 Ejecutando todas las migraciones...")
        call_command(
            'migrate', 
            verbosity=2, 
            interactive=False,
            run_syncdb=True,  # Forzar creación de tablas si es necesario
            fake_initial=False
        )
        logger.info("✅ Migraciones ejecutadas exitosamente")
        
        # Paso 4: Verificar estado de migraciones
        logger.info("🔍 Verificando estado de migraciones...")
        call_command('showmigrations', verbosity=1)
        
        # Paso 5: Crear superusuario
        ensure_admin_user()
        
    except Exception as e:
        logger.error(f"❌ Error crítico en migraciones: {e}")
        logger.info("🔄 Intentando migración de emergencia...")
        
        # Migración de emergencia: intentar migrar app por app
        apps_to_migrate = [
            'contenttypes', 'auth', 'users', 'admin', 'sessions',
            'crm', 'proyectos', 'servicios', 'mantenimiento', 
            'mejora_continua', 'tasks'
        ]
        
        for app in apps_to_migrate:
            try:
                logger.info(f"🔧 Migrando app: {app}")
                call_command('migrate', app, verbosity=1, interactive=False)
            except Exception as app_error:
                logger.warning(f"⚠️ Error migrando {app}: {app_error}")
        
        # Intentar crear superusuario aunque fallen algunas migraciones
        try:
            ensure_admin_user()
        except Exception as admin_error:
            logger.error(f"❌ Error creando admin: {admin_error}")

def ensure_admin_user():
    """Asegurar que el usuario administrador existe con la contraseña correcta"""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        username = os.environ.get('ADMIN_USERNAME', 'rgd_admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@rgdaire.com')
        password = os.environ.get('ADMIN_PASSWORD', 'Catalina18')

        # Buscar o crear el usuario administrador
        admin_user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        
        if created:
            logger.info(f'✅ Usuario administrador "{username}" creado exitosamente')
        else:
            logger.info(f'✅ Usuario administrador "{username}" ya existe')
        
        # Actualizar la contraseña y otros campos
        admin_user.set_password(password)
        admin_user.email = email
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()
        
        logger.info(f'✅ Contraseña actualizada para "{username}"')
        
    except Exception as e:
        logger.error(f'❌ Error al crear/actualizar usuario administrador: {e}')

# Inicializar Django
import django
django.setup()

# Ejecutar inicialización de base de datos solo en App Engine
if os.getenv('GAE_ENV', '').startswith('standard'):
    initialize_database()

# Importar la aplicación WSGI de Django
from rgd_aire.wsgi import application

# App Engine busca una variable llamada 'app'
app = application

# Para compatibilidad con diferentes versiones
if __name__ == '__main__':
    # Para desarrollo local (opcional)
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)