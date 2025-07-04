#!/bin/bash

# Script de despliegue con configuración optimizada para App Engine

set -e

echo "=== Despliegue Optimizado de RGD Aire ==="
echo ""
echo "Este script desplegará con configuración de bajo costo."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "app-optimized.yaml" ]; then
    echo "Error: No se encuentra app-optimized.yaml"
    echo "Asegúrate de estar en el directorio del proyecto"
    exit 1
fi

# Preguntar confirmación
echo "CAMBIOS IMPORTANTES:"
echo "  - min_instances: 0 (no habrá instancias permanentes)"
echo "  - memory: 1GB (reducido de 2GB)"
echo "  - Latencia tolerada: 100-500ms"
echo "  - Workers: 1 (reducido de 2)"
echo ""
echo "¿Deseas continuar con el despliegue optimizado? (s/n)"
read -r respuesta

if [[ ! "$respuesta" =~ ^[Ss]$ ]]; then
    echo "Despliegue cancelado."
    exit 0
fi

# Desplegar con la configuración optimizada
echo ""
echo "Desplegando con app-optimized.yaml..."
gcloud app deploy app-optimized.yaml \
  --project=appsindunnova \
  --version=optimized-$(date +%Y%m%d-%H%M%S) \
  --quiet

echo ""
echo "=== Despliegue completado ==="
echo ""
echo "SIGUIENTES PASOS:"
echo ""
echo "1. Optimizar Cloud SQL (ejecutar por separado):"
echo "   ./optimize-cloudsql.sh"
echo ""
echo "2. Monitorear el rendimiento:"
echo "   - Ver logs: gcloud app logs tail -s rgd-aire"
echo "   - Ver métricas: https://console.cloud.google.com/appengine/services"
echo ""
echo "3. Si hay problemas de rendimiento, puedes revertir:"
echo "   gcloud app deploy app.yaml --project=appsindunnova"
echo ""
echo "AHORRO ESTIMADO: ~$80-100/mes en App Engine"