# Guía Completa de Despliegue - RGD AIRE en App Engine con Cloud SQL

## 📋 Resumen

Esta guía te ayudará a configurar desde cero tu proyecto Django RGD AIRE en Google App Engine con Cloud SQL PostgreSQL.

## 🚀 Pasos de Configuración

### Paso 1: Preparar el Repositorio Local

Tu proyecto ya está configurado correctamente con:
- ✅ `requirements.txt` actualizado con todas las dependencias
- ✅ `rgd_aire/settings_appengine.py` configurado para Cloud SQL
- ✅ `app.yaml` optimizado para App Engine Standard
- ✅ Endpoint de health check en `/health/`

### Paso 2: Configurar Cloud SQL (Automatizado)

Ejecuta el script de configuración completa:

```bash
./complete_setup.sh
```

Este script:
- Verifica tu autenticación con gcloud
- Habilita las APIs necesarias
- Crea/configura la instancia de Cloud SQL
- Configura Google Cloud Storage
- Verifica las migraciones de Django
- Opcionalmente despliega la aplicación

### Paso 3: Despliegue Rápido (Si Cloud SQL ya existe)

Si ya tienes Cloud SQL configurado, usa el script de despliegue directo:

```bash
./deploy_appengine.sh
```

## 🔧 Configuración Manual (Alternativa)

### 2.1 Crear Instancia de Cloud SQL

```bash
# Configurar proyecto
gcloud config set project appsindunnova

# Habilitar APIs
gcloud services enable sqladmin.googleapis.com appengine.googleapis.com storage.googleapis.com

# Crear instancia PostgreSQL
gcloud sql instances create rgd-aire-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --project=appsindunnova

# Configurar contraseña
gcloud sql users set-password postgres no-host \
  --instance=rgd-aire-db \
  --password="RGD2024SecureDB!" \
  --project=appsindunnova

# Crear base de datos
gcloud sql databases create rgd_aire_db \
  --instance=rgd-aire-db \
  --project=appsindunnova
```

### 2.2 Crear Bucket de Almacenamiento

```bash
# Crear bucket
gsutil mb -p appsindunnova -c STANDARD -l us-central1 gs://appsindunnova-rgd-aire-storage

# Configurar permisos públicos
gsutil iam ch allUsers:objectViewer gs://appsindunnova-rgd-aire-storage
```

### 2.3 Desplegar Aplicación

```bash
# Preparar archivos estáticos
python manage.py collectstatic --noinput --settings=rgd_aire.settings

# Desplegar
gcloud app deploy app.yaml --project=appsindunnova
```

## 🔐 Credenciales de Acceso

Después del despliegue, puedes acceder con:

- **URL de la aplicación**: https://rgd-aire-dot-appsindunnova.appspot.com
- **Panel de administración**: https://rgd-aire-dot-appsindunnova.appspot.com/admin/
- **Usuario administrador**: `rgd_admin`
- **Contraseña**: `RGDAdmin2024Secure!`
- **Email**: `admin@rgdaire.com`

## 📊 Información de Recursos

### Cloud SQL
- **Instancia**: `rgd-aire-db`
- **Base de datos**: `rgd_aire_db`
- **Usuario**: `postgres`
- **Región**: `us-central1`
- **Connection Name**: `appsindunnova:us-central1:rgd-aire-db`

### App Engine
- **Servicio**: `rgd-aire`
- **Runtime**: `python312`
- **Escalado**: 1-10 instancias automáticas
- **Recursos**: 1 CPU, 2GB RAM

### Storage
- **Bucket**: `appsindunnova-rgd-aire-storage`
- **Tipo**: Standard
- **Región**: `us-central1`

## 🛠️ Comandos Útiles

### Monitoreo y Logs
```bash
# Ver logs de la aplicación
gcloud app logs tail --service=rgd-aire

# Ver estado de la aplicación
gcloud app instances list --service=rgd-aire

# Abrir la aplicación
gcloud app browse --service=rgd-aire
```

### Gestión de Cloud SQL
```bash
# Conectar a Cloud SQL desde local
gcloud sql connect rgd-aire-db --user=postgres

# Ver información de la instancia
gcloud sql instances describe rgd-aire-db

# Ver bases de datos
gcloud sql databases list --instance=rgd-aire-db
```

### Comandos Django en Producción
```bash
# Ejecutar migraciones
gcloud app deploy app.yaml --quiet

# Acceder al shell de Django (no recomendado en producción)
# Usar Cloud Shell o una instancia temporal
```

## 🔄 Actualizaciones

Para actualizar la aplicación:

1. Hacer cambios en el código
2. Commitear cambios a git
3. Ejecutar: `./deploy_appengine.sh`

## 🚨 Solución de Problemas

### Error de Conexión a Base de Datos
- Verificar que la instancia de Cloud SQL esté activa
- Comprobar las variables de entorno en `app.yaml`
- Revisar logs: `gcloud app logs tail --service=rgd-aire`

### Error 502/503
- Verificar el endpoint de health check: `/health/`
- Revisar configuración de readiness/liveness checks
- Aumentar `app_start_timeout_sec` si es necesario

### Problemas con Archivos Estáticos
- Verificar permisos del bucket de GCS
- Ejecutar `collectstatic` antes del despliegue
- Comprobar configuración de `STATIC_URL` y `MEDIA_URL`

### Credenciales Inválidas
- El superusuario se crea automáticamente en el primer despliegue
- Si no funciona, ejecutar: `python set_admin_password.py`
- Verificar variables de entorno de admin en `app.yaml`

## 📞 Soporte

Para problemas específicos:
1. Revisar logs de App Engine
2. Verificar estado de Cloud SQL
3. Comprobar configuración de variables de entorno
4. Validar conectividad entre servicios

## 🎯 Siguientes Pasos

1. Configurar dominio personalizado
2. Implementar SSL/TLS personalizado
3. Configurar backups automáticos
4. Establecer alertas de monitoreo
5. Configurar CI/CD con GitHub Actions