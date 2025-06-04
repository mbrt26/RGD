#!/bin/bash

# Script mejorado para crear superusuario usando Cloud Run Jobs
# Implementa mejores prácticas de desarrollo en la nube y manejo de errores robusto
# Versión: 2.0 - Mejorado con validaciones y retry logic

set -euo pipefail  # Modo estricto: falla en errores, variables no definidas y pipes

# Configuración de colores para output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuración de variables (readonly para inmutabilidad)
readonly PROJECT_ID="appsindunnova"
readonly SERVICE_NAME="rgd-aire"
readonly REGION="us-central1"
readonly JOB_NAME="create-superuser-job"
readonly CLOUD_SQL_INSTANCE="$PROJECT_ID:$REGION:rgd-aire-db"
readonly IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
readonly MAX_RETRIES=3
readonly RETRY_DELAY=10

# Configuración de logging
readonly LOG_FILE="/tmp/create_superuser_$(date +%Y%m%d_%H%M%S).log"

# Función de logging
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() { log "INFO" "$@"; }
log_warn() { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }
log_success() { log "SUCCESS" "$@"; }

# Función para mostrar banner
show_banner() {
    echo -e "${GREEN}🔑 RGD AIRE - Cloud Run Jobs Superuser Creation (v2.0)${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
    echo ""
    log_info "Iniciando proceso de creación de superusuario"
    log_info "Log file: $LOG_FILE"
}

# Función para mostrar configuración
show_configuration() {
    echo -e "${YELLOW}📋 Configuración del entorno:${NC}"
    echo "  Proyecto:           $PROJECT_ID"
    echo "  Servicio/Imagen:    $IMAGE_NAME"
    echo "  Región:             $REGION"
    echo "  Job:                $JOB_NAME"
    echo "  Cloud SQL Instance: $CLOUD_SQL_INSTANCE"
    echo "  Max Retries:        $MAX_RETRIES"
    echo ""
    log_info "Configuración validada"
}

# Función para validar prerrequisitos
validate_prerequisites() {
    log_info "Validando prerrequisitos del sistema..."
    
    # Verificar gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI no está instalado"
        echo -e "${RED}❌ Error: gcloud CLI requerido${NC}"
        exit 1
    fi
    
    # Verificar autenticación
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_error "No hay autenticación activa en gcloud"
        echo -e "${RED}❌ Error: Ejecuta 'gcloud auth login' primero${NC}"
        exit 1
    fi
    
    # Verificar proyecto actual
    local current_project
    current_project=$(gcloud config get-value project 2>/dev/null || echo "")
    if [ "$current_project" != "$PROJECT_ID" ]; then
        log_warn "Cambiando al proyecto $PROJECT_ID (actual: $current_project)"
        echo -e "${YELLOW}⚠️  Cambiando al proyecto $PROJECT_ID...${NC}"
        gcloud config set project "$PROJECT_ID" || {
            log_error "Error al cambiar al proyecto $PROJECT_ID"
            exit 1
        }
    fi
    
    log_success "Prerrequisitos validados correctamente"
}

# Función para validar recursos existentes
validate_resources() {
    log_info "Validando recursos de GCP..."
    
    # Verificar que la imagen existe
    if ! gcloud container images describe "$IMAGE_NAME" --project="$PROJECT_ID" &>/dev/null; then
        log_error "La imagen $IMAGE_NAME no existe"
        echo -e "${RED}❌ Error: La imagen Docker no existe${NC}"
        echo -e "${YELLOW}💡 Ejecuta el build primero: gcloud builds submit --tag $IMAGE_NAME .${NC}"
        exit 1
    fi
    
    # Verificar Cloud SQL instance
    if ! gcloud sql instances describe rgd-aire-db --project="$PROJECT_ID" &>/dev/null; then
        log_error "La instancia Cloud SQL 'rgd-aire-db' no existe"
        echo -e "${RED}❌ Error: Instancia Cloud SQL no encontrada${NC}"
        exit 1
    fi
    
    # Verificar secretos
    local secrets=("db-password" "admin-password")
    for secret in "${secrets[@]}"; do
        if ! gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
            log_error "El secreto '$secret' no existe"
            echo -e "${RED}❌ Error: Secreto '$secret' no encontrado${NC}"
            echo -e "${YELLOW}💡 Crea el secreto con: echo 'tu_password' | gcloud secrets create $secret --data-file=-${NC}"
            exit 1
        fi
    done
    
    log_success "Todos los recursos validados correctamente"
}

# Función para limpiar recursos existentes
cleanup_existing_job() {
    log_info "Limpiando job existente si existe..."
    
    if gcloud run jobs describe "$JOB_NAME" --region="$REGION" &>/dev/null; then
        echo -e "${YELLOW}🧹 Eliminando job existente: $JOB_NAME${NC}"
        if gcloud run jobs delete "$JOB_NAME" --region="$REGION" --quiet; then
            log_success "Job existente eliminado correctamente"
        else
            log_warn "No se pudo eliminar el job existente, continuando..."
        fi
    else
        log_info "No existe un job previo con el nombre $JOB_NAME"
    fi
}

# Función para crear el job con retry logic
create_job_with_retry() {
    log_info "Creando Cloud Run Job con todas las configuraciones..."
    
    local attempt=1
    while [ $attempt -le $MAX_RETRIES ]; do
        echo -e "${YELLOW}🚀 Intento $attempt/$MAX_RETRIES: Creando job...${NC}"
        
        if gcloud run jobs deploy "$JOB_NAME" \
            --image="$IMAGE_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --task-timeout=30 \
            --memory=1Gi \
            --cpu=1 \
            --max-retries=2 \
            --parallelism=1 \
            --set-env-vars="DJANGO_SETTINGS_MODULE=rgd_aire.settings_production,USE_CLOUD_SQL=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,CLOUD_SQL_CONNECTION_NAME=$CLOUD_SQL_INSTANCE,DB_NAME=rgd_aire_db,DB_USER=rgd_aire_user,ADMIN_USERNAME=admin,ADMIN_EMAIL=admin@rgdaire.com,GS_BUCKET_NAME=$PROJECT_ID-rgd-aire-storage" \
            --set-secrets="DB_PASSWORD=db-password:latest,ADMIN_PASSWORD=admin-password:latest" \
            --set-cloudsql-instances="$CLOUD_SQL_INSTANCE" \
            --command=python \
            --args="manage.py,create_superuser_cloudrun,--username=\${ADMIN_USERNAME},--email=\${ADMIN_EMAIL},--password=\${ADMIN_PASSWORD},--update" \
            --quiet; then
            
            log_success "Job creado exitosamente en el intento $attempt"
            return 0
        else
            log_warn "Intento $attempt falló"
            if [ $attempt -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}⏳ Esperando $RETRY_DELAY segundos antes del siguiente intento...${NC}"
                sleep $RETRY_DELAY
            fi
            ((attempt++))
        fi
    done
    
    log_error "Error: No se pudo crear el job después de $MAX_RETRIES intentos"
    echo -e "${RED}❌ Error: Job creation failed después de $MAX_RETRIES intentos${NC}"
    return 1
}

# Función para ejecutar el job
execute_job() {
    log_info "Ejecutando job de creación de superusuario..."
    
    echo -e "${YELLOW}⚡ Ejecutando job: $JOB_NAME...${NC}"
    
    local execution_name
    if execution_name=$(gcloud run jobs execute "$JOB_NAME" --region="$REGION" --project="$PROJECT_ID" --format="value(metadata.name)" 2>/dev/null); then
        log_success "Job ejecutado. ID de ejecución: $execution_name"
        
        # Monitorear la ejecución
        monitor_execution "$execution_name"
        
        return 0
    else
        log_error "Error al ejecutar el job"
        echo -e "${RED}❌ Error: No se pudo ejecutar el job${NC}"
        return 1
    fi
}

# Función para monitorear la ejecución
monitor_execution() {
    local execution_name="$1"
    log_info "Monitoreando ejecución: $execution_name"
    
    echo -e "${YELLOW}⏳ Monitoreando ejecución (máximo 1 minuto)...${NC}"
    
    local max_checks=6  # 6 checks * 10 segundos = 1 minuto (suficiente para timeout de 30s + overhead)
    local check=1
    
    while [ $check -le $max_checks ]; do
        local status
        status=$(gcloud run jobs executions describe "$execution_name" \
            --job="$JOB_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.conditions[0].type)" 2>/dev/null || echo "Unknown")
        
        case "$status" in
            "Completed")
                log_success "Ejecución completada exitosamente"
                echo -e "${GREEN}✅ Ejecución completada exitosamente${NC}"
                show_execution_logs "$execution_name"
                return 0
                ;;
            "Failed")
                log_error "Ejecución falló"
                echo -e "${RED}❌ Ejecución falló${NC}"
                show_execution_logs "$execution_name"
                return 1
                ;;
            *)
                echo -e "${BLUE}⏳ Estado: $status (Check $check/$max_checks)${NC}"
                sleep 10
                ((check++))
                ;;
        esac
    done
    
    log_warn "Timeout de monitoreo: La ejecución no terminó en el tiempo esperado"
    echo -e "${YELLOW}⚠️  Timeout de monitoreo: Revisa el estado manualmente${NC}"
    show_execution_logs "$execution_name"
    return 1
}

# Función para mostrar logs de ejecución
show_execution_logs() {
    local execution_name="$1"
    log_info "Obteniendo logs de la ejecución: $execution_name"
    
    echo -e "${YELLOW}📋 Logs de la ejecución:${NC}"
    echo ""
    
    # Intentar con gcloud beta primero
    if command -v gcloud &> /dev/null && gcloud components list --filter="id:beta" --format="value(state.name)" 2>/dev/null | grep -q "Installed"; then
        if gcloud beta run jobs executions logs "$execution_name" \
            --job="$JOB_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --limit=50 2>/dev/null; then
            return 0
        fi
    fi
    
    # Fallback: usar Cloud Logging
    echo -e "${YELLOW}💡 Usando Cloud Logging como fallback...${NC}"
    gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" \
        --limit=20 \
        --project="$PROJECT_ID" \
        --format="table(timestamp,severity,textPayload)" \
        --freshness=10m 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Para ver logs detallados, visita la consola web:${NC}"
        echo "https://console.cloud.google.com/run/jobs/details/$REGION/$JOB_NAME?project=$PROJECT_ID"
    }
}

# Función para mostrar resultado final
show_final_result() {
    echo ""
    echo -e "${GREEN}✅ ¡Proceso completado exitosamente!${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════════════${NC}"
    
    echo -e "${GREEN}🔑 Credenciales de acceso:${NC}"
    echo "   Usuario: admin"
    echo "   Contraseña: RGDaire2024!"
    echo ""
    
    # Obtener URL del servicio
    local service_url
    service_url=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)" 2>/dev/null || echo "")
    
    if [ -n "$service_url" ]; then
        echo -e "${YELLOW}🌐 Acceso al admin:${NC}"
        echo "   $service_url/admin/"
    else
        echo -e "${YELLOW}🌐 Servicio Cloud Run no encontrado o no desplegado${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}💡 Recomendaciones de seguridad:${NC}"
    echo "1. 🔐 Cambia la contraseña después del primer login"
    echo "2. 🔍 Revisa los logs si hay problemas de acceso"
    echo "3. 🛡️  Considera usar 2FA para mayor seguridad"
    echo "4. 📊 Monitorea el acceso en Cloud Console"
    echo ""
    
    echo -e "${BLUE}🔧 Comandos útiles:${NC}"
    echo "• Ver logs: gcloud beta run jobs executions logs [EXECUTION_ID] --job=$JOB_NAME --region=$REGION"
    echo "• Listar ejecuciones: gcloud run jobs executions list $JOB_NAME --region=$REGION"
    echo "• Eliminar job: gcloud run jobs delete $JOB_NAME --region=$REGION"
    echo ""
    
    log_success "Proceso de creación de superusuario completado"
    log_info "Log completo guardado en: $LOG_FILE"
}

# Función para manejar errores
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    log_error "Error en línea $line_number (código de salida: $exit_code)"
    echo ""
    echo -e "${RED}❌ Error inesperado en línea $line_number${NC}"
    echo -e "${YELLOW}📋 Revisa el log completo en: $LOG_FILE${NC}"
    echo -e "${YELLOW}💡 Para depuración, ejecuta con: bash -x $0${NC}"
    echo ""
    
    exit $exit_code
}

# Función de limpieza al salir
cleanup_on_exit() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Script terminado con errores (código: $exit_code)"
    else
        log_success "Script completado exitosamente"
    fi
}

# Configurar manejo de errores y señales
trap 'handle_error $LINENO' ERR
trap 'cleanup_on_exit' EXIT

# Función principal
main() {
    show_banner
    show_configuration
    validate_prerequisites
    validate_resources
    cleanup_existing_job
    
    if create_job_with_retry; then
        if execute_job; then
            show_final_result
        else
            echo -e "${RED}❌ Error en la ejecución del job${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Error en la creación del job${NC}"
        exit 1
    fi
}

# Verificar si se ejecuta directamente (no sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi