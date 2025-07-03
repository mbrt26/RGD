#!/bin/bash

echo "🚀 Iniciando aplicación en modo desarrollo..."

# Esperar a que PostgreSQL esté listo
echo "⏳ Esperando que PostgreSQL esté listo..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "✅ PostgreSQL está listo!"

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate --settings=rgd_aire.settings_local

# Crear superusuario si no existe
echo "👤 Creando superusuario de desarrollo..."
python manage.py shell --settings=rgd_aire.settings_local << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
    print('✅ Superusuario creado: admin/admin123')
else:
    print('✅ Superusuario ya existe')
EOF

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --settings=rgd_aire.settings_local

echo "🎉 Inicialización completa!"

# Iniciar servidor de desarrollo
exec python manage.py runserver 0.0.0.0:8000 --settings=rgd_aire.settings_local