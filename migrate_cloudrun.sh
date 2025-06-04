#!/bin/bash

# Script para ejecutar migraciones de Django en Cloud SQL
# Proyecto: RGD AIRE

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 Iniciando migraciones de Django en Cloud SQL${NC}"

# Configurar variables
PROJECT_ID="appsindunnova"
SERVICE_NAME="rgd-aire-migrate"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
DB_NAME="rgd_aire_db"
DB_USER="rgd_aire_user"
CLOUD_SQL_INSTANCE="$PROJECT_ID:$REGION:rgd-aire-db"

echo -e "${YELLOW}📋 Configuración:${NC}"
echo "  Proyecto: $PROJECT_ID"
echo "  Base de datos: $DB_NAME"
echo "  Usuario DB: $DB_USER"
echo "  Instancia Cloud SQL: $CLOUD_SQL_INSTANCE"
echo ""

# Verificar que estemos en el proyecto correcto
echo -e "${YELLOW}🔍 Verificando proyecto actual...${NC}"
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo -e "${YELLOW}⚠️  Cambiando al proyecto $PROJECT_ID...${NC}"
    gcloud config set project $PROJECT_ID
fi

# Crear un Dockerfile temporal para migraciones
cat > Dockerfile.migrate << EOF
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para ejecutar migraciones
CMD ["sh", "-c", "python manage.py migrate --settings=rgd_aire.settings_production && python manage.py createsuperuser --noinput --settings=rgd_aire.settings_production || echo 'El superusuario ya existe'"]
EOF

# Crear un archivo de configuración para Cloud Build
cat > cloudbuild-migrate.yaml << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '$IMAGE_NAME', '-f', 'Dockerfile.migrate', '.']
images:
- '$IMAGE_NAME'
EOF

echo -e "${YELLOW}🏗️  Construyendo imagen para migraciones...${NC}"
gcloud builds submit --config cloudbuild-migrate.yaml .

echo -e "${YELLOW}🚀 Ejecutando migraciones en Cloud Run...${NC}"

# Eliminar el job si ya existe para recrearlo
gcloud run jobs delete $SERVICE_NAME --region $REGION --quiet 2>/dev/null || echo "Job no existía previamente"

# Crear el job con el flag correcto
gcloud run jobs create $SERVICE_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,DJANGO_SETTINGS_MODULE=rgd_aire.settings_production,USE_CLOUD_SQL=true,DB_NAME=$DB_NAME,DB_USER=$DB_USER,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_INSTANCE,DJANGO_SUPERUSER_USERNAME=admin,DJANGO_SUPERUSER_PASSWORD=admin123,DJANGO_SUPERUSER_EMAIL=admin@example.com" \
    --set-cloudsql-instances $CLOUD_SQL_INSTANCE \
    --max-retries 3 \
    --task-timeout 10m

echo -e "${YELLOW}⏳ Ejecutando job de migraciones...${NC}"
gcloud run jobs execute $SERVICE_NAME --region $REGION

echo ""
echo -e "${GREEN}✅ Proceso de migraciones completado${NC}"
echo ""
echo -e "${YELLOW}📝 Próximos pasos:${NC}"
echo "1. Despliega tu aplicación con: ./deploy_cloudrun.sh"
echo "2. Verifica que todo funcione correctamente"
echo ""

# Limpiar archivos temporales
rm -f Dockerfile.migrate cloudbuild-migrate.yaml