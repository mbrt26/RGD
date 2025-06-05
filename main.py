#!/usr/bin/env python3
"""
Archivo principal para Google App Engine
Este archivo es requerido por App Engine cuando se usa 'script: auto' en app.yaml
"""

import os
import sys

# Agregar el directorio actual al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_appengine')

# Configurar Django
import django
django.setup()

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
            print(f'✅ Usuario administrador "{username}" creado exitosamente')
        else:
            print(f'✅ Usuario administrador "{username}" ya existe')
        
        # Actualizar la contraseña y otros campos
        admin_user.set_password(password)
        admin_user.email = email
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()
        
        print(f'✅ Contraseña actualizada para "{username}"')
        print(f'📧 Email: {email}')
        print(f'🔐 Contraseña configurada desde variables de entorno')
        
    except Exception as e:
        print(f'❌ Error al crear/actualizar usuario administrador: {e}')

# Ejecutar la creación del usuario administrador solo en App Engine
if os.environ.get('GAE_ENV', '') == 'standard':
    try:
        ensure_admin_user()
    except Exception as e:
        print(f'❌ Error en ensure_admin_user: {e}')

# Importar la aplicación WSGI de Django
from rgd_aire.wsgi import application

# App Engine busca una variable llamada 'app'
app = application

# Para compatibilidad con diferentes versiones
if __name__ == '__main__':
    # Para desarrollo local (opcional)
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)