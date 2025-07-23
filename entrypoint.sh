#!/bin/sh
set -e

echo "Starting RGD Aire application..."
echo "PORT: $PORT"
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Esperar un momento para que Cloud SQL esté listo
echo "Waiting for Cloud SQL to be ready..."
sleep 5

# Ejecutar migraciones con manejo de errores
echo "Running database migrations..."
python manage.py migrate --noinput || echo "Migration failed, but continuing..."

# Recolectar archivos estáticos
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Collectstatic failed, but continuing..."

# Iniciar el servidor con gunicorn
echo "Starting Gunicorn server..."
exec gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile - rgd_aire.wsgi:application