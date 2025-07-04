# Dockerfile optimizado para Cloud Run (máximo ahorro)
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Instalar solo dependencias esenciales
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar y instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Verificar que los archivos se copiaron correctamente
RUN echo "=== Files in /app ===" && ls -la /app/ | head -20

# Configurar variables de entorno para el build
ENV GOOGLE_CLOUD_PROJECT=appsindunnova \
    DJANGO_SECRET_KEY=temp-build-key \
    GS_BUCKET_NAME=temp-bucket \
    DJANGO_SETTINGS_MODULE=rgd_aire.settings_appengine \
    PYTHONPATH=/app

# Debug: Verificar la estructura antes de collectstatic
RUN echo "=== Checking source static directory ===" && \
    ls -la /app/static/ && \
    echo "=== Checking static/images ===" && \
    ls -la /app/static/images/ || echo "No images directory" && \
    echo "=== Checking static/css ===" && \
    ls -la /app/static/css/ || echo "No css directory" && \
    echo "=== Checking static/js ===" && \
    ls -la /app/static/js/ || echo "No js directory"

# Recopilar archivos estáticos con verbosidad para debug
RUN python manage.py collectstatic --noinput --verbosity 2

# Verificar que los archivos estáticos se recopilaron correctamente
RUN echo "=== Checking collected static files ===" && \
    ls -la staticfiles/ && \
    echo "=== Checking staticfiles/images ===" && \
    ls -la staticfiles/images/ || echo "No images in staticfiles" && \
    echo "=== Checking staticfiles/css ===" && \
    ls -la staticfiles/css/ || echo "No css in staticfiles" && \
    echo "=== Total files in staticfiles ===" && \
    find staticfiles -type f | wc -l

# Ensure static files have proper permissions before changing user
RUN chmod -R 755 staticfiles/

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (for documentation purposes)
EXPOSE 8080

# Comando optimizado para Cloud Run
# - 1 worker (suficiente para Cloud Run)
# - 4 threads (mejor concurrencia)
# - timeout 0 (Cloud Run maneja timeouts)
CMD exec gunicorn rgd_aire.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --threads 4 \
    --timeout 0 \
    --access-logfile - \
    --error-logfile - \
    --env DJANGO_SETTINGS_MODULE=rgd_aire.settings_appengine