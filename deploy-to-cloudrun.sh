#!/bin/bash
# Script de despliegue para RGD Aire en Cloud Run

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue a Cloud Run..."

# Configuración
PROJECT_ID="appsindunnova"
SERVICE_NAME="rgd-aire"
REGION="us-central1"
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Variables de entorno para Cloud Run
ENV_VARS="DJANGO_SETTINGS_MODULE=rgd_aire.settings_cloudrun,\
GOOGLE_CLOUD_PROJECT=appsindunnova,\
USE_CLOUD_SQL=true,\
DJANGO_SECRET_KEY=RGD-Aire-2024-SuperSecure-Key-For-Production-9j8h7g6f5d4s3a2,\
DB_NAME=rgd_aire_db_new,\
DB_USER=rgd_aire_user,\
DB_PASSWORD=RGD2024SecureDB!,\
CLOUD_SQL_CONNECTION_NAME=appsindunnova:us-central1:rgd-aire-db,\
GS_BUCKET_NAME=appsindunnova-rgd-aire-storage,\
DEFAULT_FROM_EMAIL=noreply@rgdaire.com,\
ADMIN_USERNAME=rgd_admin,\
ADMIN_EMAIL=admin@rgdaire.com,\
ADMIN_PASSWORD=Catalina18,\
DISABLE_MEMCACHE=true"

# Cloud SQL instance
CLOUD_SQL_INSTANCE="appsindunnova:us-central1:rgd-aire-db"

echo "📦 Construyendo imagen Docker..."
echo "   Tag: ${IMAGE_NAME}:${IMAGE_TAG}"
# Usar cloudbuild.yaml con sustituciones
gcloud builds submit --config=cloudbuild.yaml --substitutions=_IMAGE_TAG="${IMAGE_TAG}" .

echo "🎯 Desplegando a Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image "${IMAGE_NAME}:${IMAGE_TAG}" \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars="${ENV_VARS}" \
  --add-cloudsql-instances=${CLOUD_SQL_INSTANCE} \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300

echo "🔄 Actualizando tráfico al 100%..."
gcloud run services update-traffic ${SERVICE_NAME} --to-latest --region ${REGION}

echo "✅ Despliegue completado!"
echo "🌐 URL: https://rgd-aire-381877373634.us-central1.run.app/"
echo "📊 Vista Kanban: https://rgd-aire-381877373634.us-central1.run.app/crm/proyectoscrm/"