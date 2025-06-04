# Guía de Despliegue: RGD AIRE en Google Cloud Platform
## Proyecto: APPIndunnova

### ✅ Resumen
Esta aplicación Django se desplegará en **Cloud Run** dentro de tu proyecto existente APPIndunnova. Cloud Run permite múltiples servicios independientes, por lo que tu aplicación actual seguirá funcionando normalmente.

### 🏗️ Arquitectura Propuesta
```
APPIndunnova (Proyecto GCP)
├── Tu aplicación actual (sin cambios)
├── rgd-aire (nuevo servicio Cloud Run)
├── rgd-aire-db (Cloud SQL PostgreSQL)
└── appindunnova-rgd-aire-storage (Cloud Storage)
```

### 📋 Pasos de Configuración Previa

#### 1. Configurar Secret Manager
```bash
# Generar una SECRET_KEY segura para Django
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" > secret_key.txt

# Crear secretos en Google Cloud
gcloud secrets create django-secret-key --data-file=secret_key.txt
gcloud secrets create db-password --data-file=-
# (ingresa una contraseña segura cuando se solicite)

# Limpiar archivo temporal
rm secret_key.txt
```

#### 2. Crear Base de Datos Cloud SQL
```bash
# Crear instancia de PostgreSQL
gcloud sql instances create rgd-aire-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1

# Crear base de datos
gcloud sql databases create rgd_aire_db --instance=rgd-aire-db

# Crear usuario
gcloud sql users create rgd_aire_user \
    --instance=rgd-aire-db \
    --password=[PASSWORD_FROM_SECRET_MANAGER]
```

#### 3. Crear Bucket de Cloud Storage
```bash
# Crear bucket para archivos estáticos y media
gsutil mb gs://appindunnova-rgd-aire-storage

# Configurar permisos públicos para archivos estáticos
gsutil iam ch allUsers:objectViewer gs://appindunnova-rgd-aire-storage
```

#### 4. Configurar IAM (Permisos)
```bash
# Obtener la cuenta de servicio de Cloud Run
SERVICE_ACCOUNT=$(gcloud run services describe rgd-aire --region=us-central1 --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")

# Si no existe, Cloud Run usará la cuenta por defecto
if [ -z "$SERVICE_ACCOUNT" ]; then
    SERVICE_ACCOUNT="$(gcloud config get-value project)-compute@developer.gserviceaccount.com"
fi

# Otorgar permisos necesarios
gcloud projects add-iam-policy-binding appindunnova \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding appindunnova \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding appindunnova \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/storage.objectAdmin"
```

### 🚀 Despliegue

#### Opción 1: Script Automatizado (Recomendado)
```bash
# Desde el directorio de tu proyecto
./deploy_cloudrun.sh
```

#### Opción 2: Manual
```bash
# Construir y desplegar
gcloud builds submit --tag gcr.io/appindunnova/rgd-aire
gcloud run deploy rgd-aire \
    --image gcr.io/appindunnova/rgd-aire \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated
```

### 🔧 Configuración Post-Despliegue

#### 1. Ejecutar Migraciones
```bash
# Conectar a Cloud SQL y ejecutar migraciones
gcloud run jobs create rgd-aire-migrate \
    --image gcr.io/appindunnova/rgd-aire \
    --region us-central1 \
    --task-restart-policy OnFailure \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=appindunnova,DJANGO_SETTINGS_MODULE=rgd_aire.settings_production" \
    --command "python,manage.py,migrate"

gcloud run jobs execute rgd-aire-migrate --region us-central1
```

#### 2. Crear Superusuario
```bash
# Ejecutar comando para crear superusuario
gcloud run jobs create rgd-aire-createsuperuser \
    --image gcr.io/appindunnova/rgd-aire \
    --region us-central1 \
    --task-restart-policy OnFailure \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=appindunnova,DJANGO_SETTINGS_MODULE=rgd_aire.settings_production" \
    --command "python,manage.py,createsuperuser,--noinput" \
    --set-env-vars "DJANGO_SUPERUSER_USERNAME=admin,DJANGO_SUPERUSER_EMAIL=admin@indunnova.com"

# Nota: Necesitarás configurar la contraseña del admin después
```

### 🌐 URLs de Acceso

Después del despliegue, tu aplicación estará disponible en:
- **RGD AIRE**: `https://rgd-aire-[hash]-uc.a.run.app`
- **Tu aplicación actual**: Sin cambios en su URL

### 💰 Costos Estimados

Cloud Run es muy eficiente en costos:
- **Sin tráfico**: $0 (instancias mínimas = 0)
- **Uso básico**: $5-15/mes
- **Escalado automático**: Solo pagas por uso real

### 🔍 Monitoreo y Logs

```bash
# Ver logs en tiempo real
gcloud run services logs tail rgd-aire --region=us-central1

# Ver métricas en Cloud Console
https://console.cloud.google.com/run/detail/us-central1/rgd-aire
```

### ⚠️ Consideraciones Importantes

1. **Separación de Servicios**: Cada aplicación tendrá su propia URL y recursos
2. **Base de Datos**: Usa Cloud SQL independiente para mayor aislamiento
3. **Storage**: Bucket separado para archivos de RGD AIRE
4. **Escalado**: Configurado para 0-10 instancias según demanda
5. **Seguridad**: Todos los secretos manejados por Secret Manager

### 🆘 Solución de Problemas

#### Error de conexión a BD:
```bash
# Verificar conexión Cloud SQL
gcloud sql instances describe rgd-aire-db
```

#### Error de permisos:
```bash
# Verificar IAM
gcloud projects get-iam-policy appindunnova
```

#### Ver logs detallados:
```bash
gcloud run services logs read rgd-aire --region=us-central1 --limit=50
```