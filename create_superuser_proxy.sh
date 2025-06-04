#!/bin/bash

# Script simplificado para crear superusuario usando Cloud SQL Proxy
# Este método es más directo y confiable

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔑 Método Alternativo: Crear superusuario usando Cloud SQL Proxy${NC}"

# Configurar variables
PROJECT_ID="appsindunnova"
SERVICE_NAME="rgd-aire"
REGION="us-central1"
CLOUD_SQL_INSTANCE="$PROJECT_ID:$REGION:rgd-aire-db"
JOB_NAME="create-superuser-job"

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}📖 Uso del script:${NC}"
    echo "  $0 [OPCIÓN]"
    echo ""
    echo -e "${BLUE}Opciones:${NC}"
    echo "  run        - Ejecutar creación de superusuario usando Cloud SQL Proxy"
    echo "  logs       - Mostrar logs de ejecuciones del Job"
    echo "  list       - Listar ejecuciones del Job"
    echo "  describe   - Describir la última ejecución fallida"
    echo "  help       - Mostrar esta ayuda"
    echo ""
}

# Función para listar ejecuciones del Job
list_executions() {
    echo -e "${BLUE}📋 4.1. Listando ejecuciones del Job...${NC}"
    echo ""
    gcloud run jobs executions list $JOB_NAME --region=$REGION
    echo ""
}

# Función para describir una ejecución específica
describe_execution() {
    echo -e "${BLUE}📊 4.2. Obteniendo detalles de ejecuciones...${NC}"
    echo ""
    
    # Obtener la última ejecución
    LATEST_EXECUTION=$(gcloud run jobs executions list $JOB_NAME --region=$REGION --format="value(metadata.name)" --limit=1)
    
    if [ -z "$LATEST_EXECUTION" ]; then
        echo -e "${RED}❌ No se encontraron ejecuciones del Job${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}🔍 Describiendo ejecución: $LATEST_EXECUTION${NC}"
    echo ""
    
    gcloud run jobs executions describe $LATEST_EXECUTION \
        --job=$JOB_NAME \
        --region=$REGION \
        --format="yaml"
    echo ""
}

# Función para mostrar logs
show_logs() {
    echo -e "${BLUE}📜 4.3. Mostrando logs de ejecuciones...${NC}"
    echo ""
    
    # Obtener la última ejecución
    LATEST_EXECUTION=$(gcloud run jobs executions list $JOB_NAME --region=$REGION --format="value(metadata.name)" --limit=1)
    
    if [ -z "$LATEST_EXECUTION" ]; then
        echo -e "${RED}❌ No se encontraron ejecuciones del Job${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}📖 Mostrando logs de: $LATEST_EXECUTION${NC}"
    echo ""
    
    # Intentar con gcloud beta primero
    if gcloud beta run jobs executions logs $LATEST_EXECUTION \
        --job=$JOB_NAME \
        --region=$REGION \
        --limit=100 2>/dev/null; then
        echo ""
    else
        echo -e "${YELLOW}⚠️  gcloud beta no disponible, usando método alternativo...${NC}"
        echo ""
        
        # Método alternativo usando Cloud Logging
        echo -e "${BLUE}🔗 Para ver logs detallados, visita:${NC}"
        echo "https://console.cloud.google.com/run/jobs/details/$REGION/$JOB_NAME?project=$PROJECT_ID"
        echo ""
        
        # Intentar obtener logs via Cloud Logging
        echo -e "${YELLOW}📋 Intentando obtener logs via Cloud Logging...${NC}"
        gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
            --limit=50 \
            --format="table(timestamp,severity,textPayload)" \
            --freshness=1h
    fi
}

# Función para ejecutar el método completo de logs
run_logs_analysis() {
    echo -e "${BLUE}🔍 4. Análisis completo de logs de ejecución del Job${NC}"
    echo ""
    
    list_executions
    echo -e "${YELLOW}────────────────────────────────────────${NC}"
    describe_execution
    echo -e "${YELLOW}────────────────────────────────────────${NC}"
    show_logs
    
    echo ""
    echo -e "${BLUE}💡 4.4. Acceso vía consola web de GCP:${NC}"
    echo "   1. Ve a Cloud Run → Jobs → $JOB_NAME"
    echo "   2. En la sección Ejecuciones, haz clic en la ejecución deseada"
    echo "   3. Accede a la pestaña LOGS para ver todos los mensajes"
    echo "   4. Filtra por severidad ERROR para ubicar rápidamente errores"
    echo ""
    echo -e "${BLUE}🌐 URL directa:${NC}"
    echo "   https://console.cloud.google.com/run/jobs/details/$REGION/$JOB_NAME?project=$PROJECT_ID"
    echo ""
}

# Función principal para crear superusuario
run_superuser_creation() {
    echo -e "${YELLOW}📋 Este método usa Cloud SQL Proxy para conectarse directamente a tu base de datos${NC}"
    echo ""

    # Verificar que Cloud SQL Proxy esté instalado
    if ! command -v cloud_sql_proxy &> /dev/null; then
        echo -e "${YELLOW}⚠️  Cloud SQL Proxy no encontrado. Instalándolo...${NC}"
        
        # Descargar Cloud SQL Proxy
        curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64
        chmod +x cloud_sql_proxy
        sudo mv cloud_sql_proxy /usr/local/bin/
        echo -e "${GREEN}✅ Cloud SQL Proxy instalado${NC}"
    fi

    echo -e "${YELLOW}🚀 Iniciando Cloud SQL Proxy...${NC}"

    # Iniciar Cloud SQL Proxy en background
    cloud_sql_proxy -instances=$CLOUD_SQL_INSTANCE=tcp:5432 &
    PROXY_PID=$!

    # Esperar a que el proxy se conecte
    sleep 5

    echo -e "${YELLOW}🔧 Configurando variables de entorno para conexión local...${NC}"

    # Configurar variables de entorno para conexión a través del proxy
    export DJANGO_SETTINGS_MODULE=rgd_aire.settings_production
    export USE_CLOUD_SQL=false  # Usar conexión local a través del proxy
    export DB_HOST=localhost
    export DB_PORT=5432
    export DB_NAME=rgd_aire_db
    export DB_USER=rgd_aire_user
    export DB_PASSWORD="Tu_Contraseña_Aqui"  # Necesitarás ingresar la contraseña real
    export ADMIN_USERNAME=admin
    export ADMIN_EMAIL=admin@rgdaire.com
    export ADMIN_PASSWORD=RGDaire2024!

    echo -e "${YELLOW}📝 Ejecutando script de creación de superusuario...${NC}"

    # Ejecutar el script de Python
    python create_superuser_cloudrun.py

    # Detener Cloud SQL Proxy
    echo -e "${YELLOW}🛑 Deteniendo Cloud SQL Proxy...${NC}"
    kill $PROXY_PID

    echo ""
    echo -e "${GREEN}✅ ¡Proceso completado!${NC}"
    echo -e "${GREEN}🔑 Credenciales de acceso:${NC}"
    echo "   Usuario: admin"
    echo "   Contraseña: RGDaire2024!"
    echo ""
    echo -e "${YELLOW}🌐 Puedes acceder al admin en:${NC}"
    echo "   https://rgd-aire-rvfp6uj2va-uc.a.run.app/admin/"
}

# Ejecutar según opción
case $1 in
    run)
        run_superuser_creation
        ;;
    logs)
        show_logs
        ;;
    list)
        list_executions
        ;;
    describe)
        describe_execution
        ;;
    help|*)
        show_help
        ;;
esac