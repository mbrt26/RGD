#!/bin/bash

# Script de configuración inicial para RGD AIRE en Google Cloud
# Proyecto: APPIndunnova

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Configuración inicial de RGD AIRE en Google Cloud${NC}"
echo -e "${BLUE}Proyecto: APPIndunnova${NC}"
echo ""

# Variables
PROJECT_ID="appsindunnova"
REGION="us-central1"
DB_INSTANCE="rgd-aire-db"
BUCKET_NAME="appsindunnova-rgd-aire-storage"

# Verificar gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI no está instalado${NC}"
    exit 1
fi

# Configurar proyecto
echo -e "${YELLOW}📋 Configurando proyecto...${NC}"
gcloud config set project $PROJECT_ID

# Habilitar APIs necesarias
echo -e "${YELLOW}🔌 Habilitando APIs necesarias...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com

echo -e "${GREEN}✅ APIs habilitadas${NC}"

# Configurar Secret Manager
echo -e "${YELLOW}🔐 Configurando Secret Manager...${NC}"

# Generar SECRET_KEY para Django
echo -e "${BLUE}Generando SECRET_KEY para Django...${NC}"
python3 -c "
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
" > /tmp/django_secret_key.txt

# Crear secreto para Django SECRET_KEY
if gcloud secrets describe django-secret-key >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Secreto django-secret-key ya existe${NC}"
else
    gcloud secrets create django-secret-key --data-file=/tmp/django_secret_key.txt
    echo -e "${GREEN}✅ Secreto django-secret-key creado${NC}"
fi

# Solicitar contraseña para la base de datos
echo -e "${BLUE}Por favor, ingresa una contraseña segura para la base de datos:${NC}"
read -s db_password
echo "$db_password" > /tmp/db_password.txt

if gcloud secrets describe db-password >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Secreto db-password ya existe${NC}"
else
    gcloud secrets create db-password --data-file=/tmp/db_password.txt
    echo -e "${GREEN}✅ Secreto db-password creado${NC}"
fi

# Limpiar archivos temporales
rm -f /tmp/django_secret_key.txt /tmp/db_password.txt

# Crear instancia de Cloud SQL
echo -e "${YELLOW}🗄️  Configurando Cloud SQL...${NC}"
if gcloud sql instances describe $DB_INSTANCE >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Instancia $DB_INSTANCE ya existe${NC}"
else
    echo -e "${BLUE}Creando instancia de PostgreSQL...${NC}"
    gcloud sql instances create $DB_INSTANCE \
        --database-version=POSTGRES_14 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase
    
    echo -e "${GREEN}✅ Instancia de Cloud SQL creada${NC}"
fi

# Crear base de datos
echo -e "${BLUE}Configurando base de datos...${NC}"
if gcloud sql databases describe rgd_aire_db --instance=$DB_INSTANCE >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Base de datos rgd_aire_db ya existe${NC}"
else
    gcloud sql databases create rgd_aire_db --instance=$DB_INSTANCE
    echo -e "${GREEN}✅ Base de datos rgd_aire_db creada${NC}"
fi

# Crear usuario de base de datos
echo -e "${BLUE}Configurando usuario de base de datos...${NC}"
if gcloud sql users describe rgd_aire_user --instance=$DB_INSTANCE >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Usuario rgd_aire_user ya existe${NC}"
else
    gcloud sql users create rgd_aire_user \
        --instance=$DB_INSTANCE \
        --password="$db_password"
    echo -e "${GREEN}✅ Usuario rgd_aire_user creado${NC}"
fi

# Crear bucket de Cloud Storage
echo -e "${YELLOW}💾 Configurando Cloud Storage...${NC}"
if gsutil ls -b gs://$BUCKET_NAME >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Bucket $BUCKET_NAME ya existe${NC}"
else
    gsutil mb gs://$BUCKET_NAME
    gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
    echo -e "${GREEN}✅ Bucket de Cloud Storage creado${NC}"
fi

# Configurar permisos IAM
echo -e "${YELLOW}🔑 Configurando permisos IAM...${NC}"
COMPUTE_SA="$PROJECT_ID-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/secretmanager.secretAccessor" >/dev/null

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/cloudsql.client" >/dev/null

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$COMPUTE_SA" \
    --role="roles/storage.objectAdmin" >/dev/null

echo -e "${GREEN}✅ Permisos IAM configurados${NC}"

# Mostrar resumen de configuración
echo ""
echo -e "${GREEN}🎉 ¡Configuración inicial completada!${NC}"
echo ""
echo -e "${BLUE}📋 Resumen de recursos creados:${NC}"
echo "  • Proyecto: $PROJECT_ID"
echo "  • Cloud SQL: $DB_INSTANCE"
echo "  • Base de datos: rgd_aire_db"
echo "  • Usuario DB: rgd_aire_user"
echo "  • Bucket: $BUCKET_NAME"
echo "  • Secretos: django-secret-key, db-password"
echo ""
echo -e "${YELLOW}🚀 Próximo paso:${NC}"
echo "  Ejecuta: ./deploy_cloudrun.sh"
echo ""
echo -e "${BLUE}📍 Información importante:${NC}"
echo "  • Connection String: $PROJECT_ID:$REGION:$DB_INSTANCE"
echo "  • URL del bucket: gs://$BUCKET_NAME"
echo ""