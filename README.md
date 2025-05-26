# RGD AIRE - Sistema CRM

Sistema de gestión de relaciones con clientes (CRM) desarrollado en Django para RGD AIRE.

## Características

- Gestión de clientes y contactos
- Seguimiento de tratos y oportunidades de venta
- Gestión de cotizaciones y versiones
- Sistema de tareas de venta
- Gestión de proyectos
- Gestión de documentos de clientes

## Estructura del Proyecto

- `crm/` - Aplicación principal del CRM
- `proyectos/` - Aplicación de gestión de proyectos
- `users/` - Aplicación de gestión de usuarios
- `templates/` - Plantillas HTML
- `static/` - Archivos estáticos (CSS, JS, imágenes)

## Instalación

1. Clona el repositorio
2. Crea un entorno virtual:
   ```bash
   python -m venv env
   source env/bin/activate  # En Windows: env\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Ejecuta las migraciones:
   ```bash
   python manage.py migrate
   ```
5. Crea un superusuario:
   ```bash
   python manage.py createsuperuser
   ```
6. Ejecuta el servidor de desarrollo:
   ```bash
   python manage.py runserver
   ```

## Configuración

Crea un archivo `local_settings.py` en el directorio `rgd_aire/` para configuraciones específicas del entorno.

## Tecnologías Utilizadas

- Django
- Python
- SQLite (desarrollo)
- HTML/CSS/JavaScript

## Contribución

Para contribuir al proyecto, por favor:
1. Haz fork del repositorio
2. Crea una rama para tu feature
3. Realiza tus cambios
4. Envía un pull request