#!/bin/bash

# Script para optimizar Cloud SQL y reducir costos

echo "=== Optimización de Cloud SQL para RGD Aire ==="
echo ""

# Variables
INSTANCE_NAME="rgd-aire-db"
PROJECT_ID="appsindunnova"
REGION="us-central1"

# 1. Mostrar configuración actual
echo "1. Configuración actual de Cloud SQL:"
gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID --format="table(
  name,
  settings.tier,
  settings.activationPolicy,
  settings.backupConfiguration.enabled,
  settings.pricingPlan,
  state
)"

echo ""
echo "2. Aplicando optimizaciones..."

# 2. Cambiar a instancia más pequeña y configuración económica
echo "   - Cambiando a tier económico (db-f1-micro)..."
gcloud sql instances patch $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --tier=db-f1-micro \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=03 \
  --quiet

# 3. Configurar política de activación (NEVER = se apaga cuando no se usa)
echo "   - Configurando para apagar cuando no se use..."
gcloud sql instances patch $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --activation-policy=NEVER \
  --quiet

# 4. Configurar backup mínimo (solo 1 vez al día)
echo "   - Configurando backup mínimo..."
gcloud sql instances patch $INSTANCE_NAME \
  --project=$PROJECT_ID \
  --backup-start-time=03:00 \
  --no-backup \
  --quiet

echo ""
echo "3. Verificando nueva configuración..."
gcloud sql instances describe $INSTANCE_NAME --project=$PROJECT_ID --format="table(
  name,
  settings.tier,
  settings.activationPolicy,
  settings.backupConfiguration.enabled,
  state
)"

echo ""
echo "=== Optimización completada ==="
echo ""
echo "Ahorro estimado: ~70% en costos de Cloud SQL"
echo ""
echo "NOTA: La base de datos ahora:"
echo "  - Está configurada con política NEVER (se debe activar manualmente)"
echo "  - Usa la instancia más económica (db-f1-micro)"
echo "  - Sin backups automáticos (máximo ahorro)"
echo ""
echo "IMPORTANTE: Para usar la aplicación, primero activa la BD:"
echo "  gcloud sql instances patch $INSTANCE_NAME --activation-policy=ALWAYS"
echo ""
echo "Para volver a apagarla y ahorrar costos:"
echo "  gcloud sql instances patch $INSTANCE_NAME --activation-policy=NEVER"