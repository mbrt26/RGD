#!/bin/bash

# Script para ejecutar migraciones en Cloud SQL
# Este script debe ejecutarse después del despliegue

echo "Iniciando migraciones en Cloud SQL..."

# Ejecutar migraciones
python manage.py migrate --settings=rgd_aire.settings_production

# Crear superusuario si no existe
python manage.py shell --settings=rgd_aire.settings_production << EOF
from django.contrib.auth import get_user_model
import os

User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=os.environ.get('ADMIN_USERNAME', 'admin'),
        email=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
        password=os.environ.get('ADMIN_PASSWORD', 'changeme123')
    )
    print("Superusuario creado exitosamente")
else:
    print("Superusuario ya existe")
EOF

echo "Migraciones completadas"