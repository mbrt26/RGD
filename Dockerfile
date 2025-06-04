# Usar imagen base de Python con Alpine para menor tamaño
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DJANGO_SETTINGS_MODULE=rgd_aire.settings_production

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear usuario no-root para seguridad
RUN adduser --disabled-password --gecos '' appuser

# Copiar el código de la aplicación
COPY . .

# Crear directorio para archivos estáticos y cambiar permisos
RUN mkdir -p /app/staticfiles \
    && chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Ejecutar collectstatic (solo si no usa Cloud Storage)
# RUN python manage.py collectstatic --noinput

# Exponer el puerto
EXPOSE 8080

# Comando para ejecutar la aplicación con mejores configuraciones para producción
CMD exec gunicorn \
    --bind :$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    --keep-alive 2 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile - \
    rgd_aire.wsgi:application