#!/bin/bash

# Script de despliegue para RGD AIRE en Google Cloud Run
# Proyecto: APPIndunnova

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando despliegue de RGD AIRE en Google Cloud Run${NC}"

# Configurar variables
PROJECT_ID="appsindunnova"
SERVICE_NAME="rgd-aire"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
# Configuración de la base de datos
DB_NAME="rgd_aire_db"
DB_USER="rgd_aire_user"  # Cambiado de "postgres" a "rgd_aire_user"
CLOUD_SQL_INSTANCE="$PROJECT_ID:$REGION:rgd-aire-db"

echo -e "${YELLOW}📋 Configuración:${NC}"
echo "  Proyecto: $PROJECT_ID"
echo "  Servicio: $SERVICE_NAME"
echo "  Región: $REGION"
echo "  Base de datos: $DB_NAME"
echo "  Usuario DB: $DB_USER"  # Actualizado para mostrar el usuario correcto
echo "  Instancia Cloud SQL: $CLOUD_SQL_INSTANCE"
echo ""

# Verificar que estemos en el proyecto correcto
echo -e "${YELLOW}🔍 Verificando proyecto actual...${NC}"
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  Cambiando al proyecto $PROJECT_ID...${NC}"
    gcloud config set project $PROJECT_ID
fi

# Construir imagen con Cloud Build
echo -e "${YELLOW}🏗️  Construyendo imagen con Cloud Build...${NC}"
gcloud builds submit --tag $IMAGE_NAME

# Desplegar en Cloud Run
echo -e "${YELLOW}🚀 Desplegando en Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,DJANGO_SETTINGS_MODULE=rgd_aire.settings_production,USE_CLOUD_SQL=true,DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_INSTANCE" \
    --add-cloudsql-instances $CLOUD_SQL_INSTANCE

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ ¡Despliegue completado exitosamente!${NC}"
echo -e "${GREEN}🌐 Tu aplicación está disponible en: $SERVICE_URL${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo "1. Configurar secretos en Secret Manager si no lo has hecho"
echo "2. Asegurarse que la base de datos Cloud SQL está configurada correctamente"
echo "3. Configurar bucket de Cloud Storage para archivos estáticos"
echo "4. Configurar dominio personalizado si lo deseas"
echo ""
echo -e "${YELLOW}🔍 Para ver logs en tiempo real:${NC}"
echo "gcloud run services logs tail $SERVICE_NAME --region=$REGION"