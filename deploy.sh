#!/bin/bash

# Script de despliegue automatizado para Google Cloud Platform
# Asegúrate de tener gcloud CLI instalado y configurado

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando despliegue en Google Cloud Platform${NC}"

# Verificar si gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI no está instalado. Instálalo desde: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Variables de configuración
PROJECT_ID=${1:-"mi-proyecto-rgd-aire"}
REGION="us-central1"
DB_INSTANCE_NAME="rgd-aire-db"
BUCKET_NAME="${PROJECT_ID}-rgd-aire-storage"
SERVICE_NAME="rgd-aire"

echo -e "${YELLOW}📋 Configuración del despliegue:${NC}"
echo "  - Proyecto: $PROJECT_ID"
echo "  - Región: $REGION"
echo "  - Base de datos: $DB_INSTANCE_NAME"
echo "  - Bucket: $BUCKET_NAME"
echo "  - Servicio: $SERVICE_NAME"

read -p "¿Continuar con el despliegue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Despliegue cancelado."
    exit 0
fi

# Configurar proyecto
echo -e "${YELLOW}⚙️  Configurando proyecto...${NC}"
gcloud config set project $PROJECT_ID

# Habilitar APIs necesarias
echo -e "${YELLOW}🔧 Habilitando APIs necesarias...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sql-component.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com

# Crear Cloud SQL instance
echo -e "${YELLOW}💾 Creando instancia de Cloud SQL...${NC}"
if ! gcloud sql instances describe $DB_INSTANCE_NAME --quiet 2>/dev/null; then
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_14 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=10GB \
        --no-backup
    
    # Crear base de datos
    gcloud sql databases create rgd_aire_db --instance=$DB_INSTANCE_NAME
    
    # Crear usuario de base de datos
    gcloud sql users create rgd_user \
        --instance=$DB_INSTANCE_NAME \
        --password="$(openssl rand -base64 32)"
    
    echo -e "${GREEN}✅ Instancia de Cloud SQL creada${NC}"
else
    echo -e "${GREEN}✅ Instancia de Cloud SQL ya existe${NC}"
fi

# Crear bucket de Cloud Storage
echo -e "${YELLOW}🪣 Creando bucket de Cloud Storage...${NC}"
if ! gsutil ls gs://$BUCKET_NAME &>/dev/null; then
    gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME
    gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
    echo -e "${GREEN}✅ Bucket de Cloud Storage creado${NC}"
else
    echo -e "${GREEN}✅ Bucket de Cloud Storage ya existe${NC}"
fi

# Crear secretos en Secret Manager
echo -e "${YELLOW}🔐 Configurando secretos...${NC}"

# Django Secret Key
if ! gcloud secrets describe django-secret-key --quiet 2>/dev/null; then
    echo "$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" | \
    gcloud secrets create django-secret-key --data-file=-
    echo -e "${GREEN}✅ Secret Key de Django creado${NC}"
fi

# Database Password
if ! gcloud secrets describe db-password --quiet 2>/dev/null; then
    echo "$(openssl rand -base64 32)" | \
    gcloud secrets create db-password --data-file=-
    echo -e "${GREEN}✅ Password de base de datos creado${NC}"
fi

# Construir y desplegar con Cloud Build
echo -e "${YELLOW}🏗️  Construyendo y desplegando aplicación...${NC}"
gcloud builds submit . \
    --config=cloudbuild.yaml \
    --substitutions=_PROJECT_ID=$PROJECT_ID

# Configurar variables de entorno del servicio
echo -e "${YELLOW}⚙️  Configurando variables de entorno...${NC}"
gcloud run services update $SERVICE_NAME \
    --region=$REGION \
    --set-env-vars="DJANGO_SETTINGS_MODULE=rgd_aire.settings_production" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
    --set-env-vars="USE_CLOUD_SQL=true" \
    --set-env-vars="DB_NAME=rgd_aire_db" \
    --set-env-vars="DB_USER=rgd_user" \
    --set-env-vars="CLOUD_SQL_CONNECTION_NAME=$PROJECT_ID:$REGION:$DB_INSTANCE_NAME" \
    --set-env-vars="GS_BUCKET_NAME=$BUCKET_NAME"

# Obtener URL del servicio
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

echo -e "${GREEN}🎉 ¡Despliegue completado exitosamente!${NC}"
echo -e "${GREEN}🌐 URL de la aplicación: $SERVICE_URL${NC}"
echo
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo "1. Ejecutar migraciones: gcloud run jobs execute rgd-aire-migrate --region=$REGION"
echo "2. Crear superusuario accediendo a: $SERVICE_URL/admin/"
echo "3. Configurar dominio personalizado (opcional)"
echo
echo -e "${YELLOW}⚠️  Importante:${NC}"
echo "- Cambia las credenciales por defecto del admin"
echo "- Configura los secretos de producción"
echo "- Revisa los logs: gcloud run services logs tail $SERVICE_NAME --region=$REGION"