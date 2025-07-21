# Guía de Despliegue a Cloud Run

## Requisitos previos

1. Tener instalado Google Cloud SDK (`gcloud`)
2. Estar autenticado: `gcloud auth login`
3. Tener el proyecto configurado: `gcloud config set project appsindunnova`

## Proceso de despliegue

### Método 1: Script automatizado (RECOMENDADO)

Simplemente ejecuta:

```bash
./deploy-to-cloudrun.sh
```

Este script automáticamente:
- Construye la imagen Docker con un tag único basado en fecha/hora
- Despliega a Cloud Run con todas las variables de entorno necesarias
- Configura la conexión a Cloud SQL
- Actualiza el tráfico al 100%

### Método 2: Comandos manuales

Si necesitas más control, puedes ejecutar los comandos manualmente:

1. **Construir la imagen:**
   ```bash
   gcloud builds submit --tag gcr.io/appsindunnova/rgd-aire:latest . --timeout=20m
   ```

2. **Desplegar a Cloud Run:**
   ```bash
   gcloud run deploy rgd-aire \
     --image gcr.io/appsindunnova/rgd-aire:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="[VER ARCHIVO .env.cloudrun.example]" \
     --add-cloudsql-instances=appsindunnova:us-central1:rgd-aire-db \
     --memory=512Mi \
     --cpu=1 \
     --timeout=300
   ```

3. **Actualizar tráfico:**
   ```bash
   gcloud run services update-traffic rgd-aire --to-latest --region us-central1
   ```

## Configuración

### Variables de entorno

Las variables de entorno están documentadas en `.env.cloudrun.example`. 

**IMPORTANTE**: Nunca subas las credenciales reales a Git.

### Base de datos

- **Instancia Cloud SQL**: `rgd-aire-db`
- **Base de datos**: `rgd_aire_db_new`
- **Usuario**: `rgd_aire_user`

### Archivos importantes

- `Dockerfile.cloudrun`: Dockerfile optimizado para Cloud Run
- `rgd_aire/settings_appengine.py`: Configuración de Django para producción
- `.env.cloudrun.example`: Plantilla de variables de entorno

## URLs de la aplicación

- **Aplicación principal**: https://rgd-aire-381877373634.us-central1.run.app/
- **Vista Kanban CRM**: https://rgd-aire-381877373634.us-central1.run.app/crm/proyectoscrm/
- **Admin Django**: https://rgd-aire-381877373634.us-central1.run.app/admin/

## Solución de problemas

### Error de base de datos (no such table)

Si aparece este error, verifica:
1. Que `DJANGO_SETTINGS_MODULE=rgd_aire.settings_appengine`
2. Que `USE_CLOUD_SQL=true`
3. Que las credenciales de la base de datos sean correctas

### El contenedor no inicia

Revisa los logs:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rgd-aire" --limit=50
```

### Rollback a versión anterior

Si algo sale mal, puedes volver a una revisión anterior:
```bash
# Listar revisiones
gcloud run revisions list --service rgd-aire --region us-central1

# Volver a una revisión específica
gcloud run services update-traffic rgd-aire --to-revisions=REVISION_NAME=100 --region us-central1
```

## Mejores prácticas

1. **Siempre prueba localmente primero**
2. **Usa el script de despliegue** para consistencia
3. **Revisa los logs** después de cada despliegue
4. **Mantén un registro** de las versiones desplegadas
5. **No modifiques** las variables de entorno de producción sin coordinar con el equipo