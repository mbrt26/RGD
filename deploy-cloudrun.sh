#!/bin/bash

# Script de despliegue a Cloud Run (más económico que App Engine)

set -e

# Configuración
PROJECT_ID="appsindunnova"
SERVICE_NAME="rgd-aire"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "=== Desplegando RGD Aire en Cloud Run ==="
echo ""

# 1. Construir imagen Docker
echo "1. Construyendo imagen Docker..."
gcloud builds submit \
  --tag $IMAGE_NAME \
  --project $PROJECT_ID \
  --timeout=20m

# 2. Desplegar en Cloud Run
echo ""
echo "2. Desplegando en Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 3 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 100 \
  --cpu-throttling \
  --set-env-vars "DJANGO_SETTINGS_MODULE=rgd_aire.settings_cloudrun" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=appsindunnova" \
  --set-env-vars "USE_CLOUD_SQL=true" \
  --set-env-vars "DJANGO_SECRET_KEY=RGD-Aire-2024-SuperSecure-Key-For-Production-9j8h7g6f5d4s3a2" \
  --set-env-vars "DB_NAME=rgd_aire_db_new" \
  --set-env-vars "DB_USER=rgd_aire_user" \
  --set-env-vars "DB_PASSWORD=RGD2024SecureDB!" \
  --set-env-vars "CLOUD_SQL_CONNECTION_NAME=appsindunnova:us-central1:rgd-aire-db" \
  --set-env-vars "GS_BUCKET_NAME=appsindunnova-rgd-aire-storage" \
  --set-env-vars "DEFAULT_FROM_EMAIL=noreply@rgdaire.com" \
  --set-env-vars "ADMIN_USERNAME=rgd_admin" \
  --set-env-vars "ADMIN_EMAIL=admin@rgdaire.com" \
  --set-env-vars "ADMIN_PASSWORD=Catalina18" \
  --set-env-vars "DISABLE_MEMCACHE=true" \
  --add-cloudsql-instances appsindunnova:us-central1:rgd-aire-db

# 3. Obtener URL del servicio
echo ""
echo "3. Obteniendo URL del servicio..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --region $REGION \
  --project $PROJECT_ID \
  --format 'value(status.url)')

echo ""
echo "=== Despliegue completado ==="
echo ""
echo "URL del servicio: $SERVICE_URL"
echo ""
echo "Ventajas de Cloud Run vs App Engine:"
echo "  - Costo $0 cuando no hay tráfico"
echo "  - Escalado más eficiente"
echo "  - Arranque en frío más rápido"
echo "  - Facturación por milisegundos"
echo ""
echo "Ahorro estimado: ~90% vs App Engine actual"