#!/bin/bash

# Script para desplegar Cloud Run Job con Cloud SQL usando --set-cloudsql-instances
# Implementa las mejores prácticas de seguridad y configuración

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 3. Desplegando Cloud Run Job con Cloud SQL Integration${NC}"
echo ""

# Configurar variables
PROJECT_ID="appsindunnova"
SERVICE_NAME="rgd-aire"
REGION="us-central1"
JOB_NAME="create-superuser-job"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:latest"
CLOUD_SQL_INSTANCE="$PROJECT_ID:$REGION:rgd-aire-db"

echo -e "${BLUE}📋 Configuración del Job:${NC}"
echo "  Proyecto: $PROJECT_ID"
echo "  Región: $REGION"
echo "  Imagen: $IMAGE_NAME"
echo "  Cloud SQL Instance: $CLOUD_SQL_INSTANCE"
echo ""

# Función para validar prerrequisitos
validate_prerequisites() {
    echo -e "${YELLOW}🔍 Validando prerrequisitos...${NC}"
    
    # Verificar que la imagen existe
    if ! gcloud container images describe $IMAGE_NAME --project=$PROJECT_ID &>/dev/null; then
        echo -e "${RED}❌ Error: La imagen $IMAGE_NAME no existe${NC}"
        echo -e "${YELLOW}💡 Ejecuta primero el build de la imagen con:${NC}"
        echo "   gcloud builds submit --tag $IMAGE_NAME ."
        exit 1
    fi
    
    # Verificar que los secretos existen
    if ! gcloud secrets describe db-password --project=$PROJECT_ID &>/dev/null; then
        echo -e "${RED}❌ Error: El secreto 'db-password' no existe${NC}"
        echo -e "${YELLOW}💡 Crea el secreto con:${NC}"
        echo "   gcloud secrets create db-password --data-file=- <<< 'tu_password_aqui'"
        exit 1
    fi
    
    if ! gcloud secrets describe admin-password --project=$PROJECT_ID &>/dev/null; then
        echo -e "${RED}❌ Error: El secreto 'admin-password' no existe${NC}"
        echo -e "${YELLOW}💡 Crea el secreto con:${NC}"
        echo "   gcloud secrets create admin-password --data-file=- <<< 'RGDaire2024!'"
        exit 1
    fi
    
    # Verificar que Cloud SQL instance existe
    if ! gcloud sql instances describe rgd-aire-db --project=$PROJECT_ID &>/dev/null; then
        echo -e "${RED}❌ Error: La instancia Cloud SQL 'rgd-aire-db' no existe${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Todos los prerrequisitos están listos${NC}"
    echo ""
}

# Función principal para desplegar el Job
deploy_job() {
    echo -e "${YELLOW}🚀 3.1. Desplegando Cloud Run Job con configuración completa...${NC}"
    echo ""
    
    # Comando principal con todas las configuraciones necesarias
    gcloud run jobs deploy $JOB_NAME \
        --image=$IMAGE_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --task-timeout=300 \
        --memory=1Gi \
        --cpu=1 \
        --max-retries=3 \
        --parallelism=1 \
        --task-count=1 \
        --set-env-vars="DJANGO_SETTINGS_MODULE=rgd_aire.settings_production,USE_CLOUD_SQL=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_INSTANCE,DB_NAME=rgd_aire_db,DB_USER=rgd_aire_user,ADMIN_USERNAME=admin,ADMIN_EMAIL=admin@rgdaire.com" \
        --set-secrets="DB_PASSWORD=db-password:latest,ADMIN_PASSWORD=admin-password:latest" \
        --set-cloudsql-instances="$CLOUD_SQL_INSTANCE" \
        --command=python \
        --args="manage.py,createsuperuser,--noinput" \
        --quiet
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Job desplegado exitosamente${NC}"
        echo ""
    else
        echo -e "${RED}❌ Error al desplegar el Job${NC}"
        exit 1
    fi
}

# Función para validar la configuración del Job
validate_job_config() {
    echo -e "${YELLOW}🔍 3.2. Validando configuración del Job desplegado...${NC}"
    echo ""
    
    echo -e "${BLUE}📋 Variables de entorno configuradas:${NC}"
    gcloud run jobs describe $JOB_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="yaml(spec.template.spec.containers[0].env)" | grep -E "(name|value|secretKeyRef)" | head -30
    echo ""
    
    echo -e "${BLUE}🔌 Configuración de Cloud SQL:${NC}"
    gcloud run jobs describe $JOB_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="yaml(spec.template.spec.containers[0].volumeMounts,spec.template.spec.volumes)" | head -20
    echo ""
    
    # Validar que CLOUD_SQL_CONNECTION_NAME esté correctamente configurado
    CLOUD_SQL_ENV=$(gcloud run jobs describe $JOB_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(spec.template.spec.containers[0].env[].value)" \
        --filter="spec.template.spec.containers[0].env[].name=CLOUD_SQL_CONNECTION_NAME")
    
    if [ "$CLOUD_SQL_ENV" = "$CLOUD_SQL_INSTANCE" ]; then
        echo -e "${GREEN}✅ CLOUD_SQL_CONNECTION_NAME configurado correctamente: $CLOUD_SQL_ENV${NC}"
    else
        echo -e "${RED}❌ Error: CLOUD_SQL_CONNECTION_NAME mal configurado${NC}"
        echo "   Esperado: $CLOUD_SQL_INSTANCE"
        echo "   Actual: $CLOUD_SQL_ENV"
        return 1
    fi
    
    echo ""
}

# Función para ejecutar el Job
execute_job() {
    echo -e "${YELLOW}🎯 Ejecutando el Job...${NC}"
    echo ""
    
    EXECUTION_NAME=$(gcloud run jobs execute $JOB_NAME \
        --region=$REGION \
        --project=$PROJECT_ID \
        --format="value(metadata.name)")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Job ejecutado. ID de ejecución: $EXECUTION_NAME${NC}"
        echo ""
        
        # Esperar a que termine la ejecución
        echo -e "${YELLOW}⏳ Esperando finalización de la ejecución...${NC}"
        
        # Monitorear estado cada 10 segundos
        for i in {1..30}; do
            STATUS=$(gcloud run jobs executions describe $EXECUTION_NAME \
                --job=$JOB_NAME \
                --region=$REGION \
                --project=$PROJECT_ID \
                --format="value(status.conditions[0].type)")
            
            if [ "$STATUS" = "Completed" ]; then
                echo -e "${GREEN}✅ Ejecución completada exitosamente${NC}"
                break
            elif [ "$STATUS" = "Failed" ]; then
                echo -e "${RED}❌ Ejecución falló${NC}"
                break
            fi
            
            echo -e "${BLUE}⏳ Estado: $STATUS (${i}/30)${NC}"
            sleep 10
        done
        
        # Mostrar logs finales
        echo ""
        echo -e "${BLUE}📜 Logs de la ejecución:${NC}"
        if command -v gcloud beta &> /dev/null; then
            gcloud beta run jobs executions logs $EXECUTION_NAME \
                --job=$JOB_NAME \
                --region=$REGION \
                --project=$PROJECT_ID \
                --limit=50
        else
            echo -e "${YELLOW}⚠️  Para ver logs detallados, instala gcloud beta o visita:${NC}"
            echo "https://console.cloud.google.com/run/jobs/details/$REGION/$JOB_NAME?project=$PROJECT_ID"
        fi
    else
        echo -e "${RED}❌ Error al ejecutar el Job${NC}"
        exit 1
    fi
}

# Función para mostrar comandos de validación manual
show_validation_commands() {
    echo ""
    echo -e "${BLUE}🔧 Comandos de validación manual:${NC}"
    echo ""
    echo -e "${YELLOW}1. Listar ejecuciones:${NC}"
    echo "   gcloud run jobs executions list $JOB_NAME --region=$REGION"
    echo ""
    echo -e "${YELLOW}2. Describir Job:${NC}"
    echo "   gcloud run jobs describe $JOB_NAME --region=$REGION --format=yaml"
    echo ""
    echo -e "${YELLOW}3. Ver logs (beta):${NC}"
    echo "   gcloud beta run jobs executions logs [EXECUTION_ID] --job=$JOB_NAME --region=$REGION"
    echo ""
    echo -e "${YELLOW}4. Validar configuración de Cloud SQL:${NC}"
    echo "   gcloud run jobs describe $JOB_NAME --region=$REGION --format=\"yaml(spec.template.spec.containers[0].env)\""
    echo ""
    echo -e "${BLUE}🌐 Consola web:${NC}"
    echo "   https://console.cloud.google.com/run/jobs/details/$REGION/$JOB_NAME?project=$PROJECT_ID"
    echo ""
}

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}📖 Uso del script:${NC}"
    echo "  $0 [OPCIÓN]"
    echo ""
    echo -e "${BLUE}Opciones:${NC}"
    echo "  deploy     - Desplegar el Job completo (default)"
    echo "  validate   - Solo validar configuración del Job existente"
    echo "  execute    - Solo ejecutar el Job existente"
    echo "  commands   - Mostrar comandos de validación manual"
    echo "  help       - Mostrar esta ayuda"
    echo ""
}

# Función principal
main() {
    case ${1:-deploy} in
        deploy)
            validate_prerequisites
            deploy_job
            validate_job_config
            execute_job
            show_validation_commands
            ;;
        validate)
            validate_job_config
            ;;
        execute)
            execute_job
            ;;
        commands)
            show_validation_commands
            ;;
        help)
            show_help
            ;;
        *)
            show_help
            ;;
    esac
}

# Ejecutar función principal
main "$@"