# Usar imagen base de Python
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar dependencias adicionales para producción
RUN pip install gunicorn whitenoise google-cloud-storage django-storages

# Copiar el código de la aplicación
COPY . .

# Crear directorio para archivos estáticos
RUN mkdir -p /app/staticfiles

# Ejecutar collectstatic
RUN python manage.py collectstatic --noinput --settings=rgd_aire.settings_production

# Exponer el puerto
EXPOSE 8080

# Comando para ejecutar la aplicación
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 rgd_aire.wsgi:application