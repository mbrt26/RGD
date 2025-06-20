# Documentación Pre-Reset: Módulo de Proyectos

## 1. Resumen de Arquitectura del Módulo

### **Estructura General:**
```
proyectos/
├── models.py                 # Modelos principales del dominio
├── admin.py                 # Configuración del admin de Django
├── views/                   # Vistas organizadas por funcionalidad
│   ├── __init__.py
│   ├── actividad/views.py   # CRUD de actividades
│   ├── bitacora/views.py    # Gestión de bitácoras
│   ├── colaborador/views.py # Gestión de equipos
│   ├── entregable/views.py  # Gestión de entregables
│   ├── proyecto/views.py    # CRUD principal de proyectos
│   ├── recurso/views.py     # Recursos del proyecto
│   └── api_views.py         # APIs para integración
├── forms/                   # Formularios especializados
│   ├── __init__.py
│   ├── actividad_forms.py   # Formularios de actividades
│   ├── entregable_forms.py  # Formularios de entregables
│   └── import_forms.py      # Importación de datos
├── templates/proyectos/     # Templates organizados por módulo
├── static/proyectos/js/     # JavaScript específico
├── templatetags/            # Filtros personalizados
├── management/commands/     # Comandos de gestión
└── migrations/              # Migraciones de base de datos
```

### **Patrones Arquitectónicos:**
- **MVT Pattern**: Models-Views-Templates de Django
- **Class-Based Views**: Uso extensivo de ListView, CreateView, etc.
- **Modular Design**: Vistas separadas por funcionalidad
- **Template Inheritance**: Base templates reutilizables
- **Form Validation**: Validación robusta en formularios

## 2. Lista de Archivos Clave y Ubicaciones

### **Archivos Modelo (Core del Negocio):**
```
/Users/miguelrodriguez/code/RGDAire/proyectos/models.py
- Contiene: Proyecto, Actividad, Colaborador, EntregableProyecto, BitacoraArchivo
```

### **Vistas Principales:**
```
/Users/miguelrodriguez/code/RGDAire/proyectos/views/proyecto/views.py
- ProyectoListView, ProyectoCreateView, ProyectoDetailView, ProyectoUpdateView

/Users/miguelrodriguez/code/RGDAire/proyectos/views/actividad/views.py
- ActividadListView, ActividadCreateView, ActividadDetailView, ActividadUpdateView

/Users/miguelrodriguez/code/RGDAire/proyectos/views/bitacora/views.py
- BitacoraListView, BitacoraCreateView, BitacoraDetailView

/Users/miguelrodriguez/code/RGDAire/proyectos/views/entregable/views.py
- EntregableListView, EntregableCreateView, configuracion_masiva_entregables
```

### **Formularios:**
```
/Users/miguelrodriguez/code/RGDAire/proyectos/forms/actividad_forms.py
- ActividadForm, ActividadImportForm

/Users/miguelrodriguez/code/RGDAire/proyectos/forms/entregable_forms.py
- EntregableForm, ConfiguracionMasivaForm
```

### **Templates Clave:**
```
/Users/miguelrodriguez/code/RGDAire/templates/proyectos/proyecto/
- list.html, detail.html, form.html

/Users/miguelrodriguez/code/RGDAire/templates/proyectos/entregables/
- gestion.html, configuracion_masiva.html, dashboard.html
```

### **URLs:**
```
/Users/miguelrodriguez/code/RGDAire/proyectos/urls.py
- Configuración de rutas del módulo
```

## 3. Modelos Existentes y Relaciones

### **Modelo Principal: Proyecto**
```python
class Proyecto(models.Model):
    # Identificación
    nombre = CharField(max_length=200)
    descripcion = TextField
    codigo = CharField(unique=True)
    
    # Fechas y Control
    fecha_inicio = DateField
    fecha_fin = DateField
    fecha_creacion = DateTimeField(auto_now_add=True)
    
    # Estado y Progreso
    estado = CharField(choices=ESTADO_CHOICES)
    avance = PositiveIntegerField(0-100)
    avance_planeado = PositiveIntegerField(0-100)
    
    # Responsables (Campos agregados recientemente)
    director_proyecto = ForeignKey(User, related_name='proyectos_dirigidos')
    ingeniero_proyecto = ForeignKey(User, related_name='proyectos_ingeniero')
    creado_por = ForeignKey(User, related_name='proyectos_creados')
    
    # Integración CRM
    cotizacion_aprobada = ForeignKey('crm.VersionCotizacion')
```

### **Estados del Proyecto:**
```python
ESTADO_CHOICES = [
    ('planificacion', 'Planificación'),
    ('en_proceso', 'En Proceso'),
    ('completado', 'Completado'),
    ('cancelado', 'Cancelado'),
    ('pausado', 'Pausado'),
]
```

### **Modelo: Colaborador**
```python
class Colaborador(models.Model):
    nombre = CharField(max_length=200)
    email = EmailField
    telefono = CharField(max_length=20)
    cargo = CharField(max_length=100)
    activo = BooleanField(default=True)
```

### **Modelo: Actividad**
```python
class Actividad(models.Model):
    proyecto = ForeignKey(Proyecto, related_name='actividades')
    nombre = CharField(max_length=200)
    descripcion = TextField
    fecha_inicio = DateField
    fecha_fin = DateField
    estado = CharField(choices=ESTADO_ACTIVIDAD_CHOICES)
    
    # Responsables (Campos agregados recientemente)
    responsable_principal = ForeignKey(Colaborador, related_name='actividades_principales')
    responsable_apoyo = ForeignKey(Colaborador, related_name='actividades_apoyo')
```

### **Modelo: EntregableProyecto**
```python
class EntregableProyecto(models.Model):
    proyecto = ForeignKey(Proyecto, related_name='entregables')
    nombre = CharField(max_length=200)
    descripcion = TextField
    fecha_entrega = DateField
    estado = CharField(choices=ESTADO_ENTREGABLE_CHOICES)
    archivo = FileField(upload_to='entregables/')
```

### **Modelo: BitacoraArchivo**
```python
class BitacoraArchivo(models.Model):
    proyecto = ForeignKey(Proyecto, related_name='bitacoras')
    actividad = ForeignKey(Actividad, related_name='bitacoras')
    fecha = DateField
    descripcion = TextField
    archivo = FileField(upload_to='bitacoras/')
    usuario = ForeignKey(User)
```

### **Relaciones Clave:**
- **Proyecto ↔ CRM**: `cotizacion_aprobada` → `crm.VersionCotizacion`
- **Proyecto → Actividades**: One-to-Many
- **Proyecto → Entregables**: One-to-Many  
- **Proyecto → Bitácoras**: One-to-Many
- **Actividad → Bitácoras**: One-to-Many
- **User → Proyectos**: Multiple ForeignKeys (director, ingeniero, creador)

## 4. Convenciones del Proyecto

### **Naming Conventions:**

#### **Modelos:**
- PascalCase: `Proyecto`, `EntregableProyecto`, `BitacoraArchivo`
- Campos en español: `nombre`, `descripcion`, `fecha_inicio`
- Foreign Keys descriptivos: `director_proyecto`, `ingeniero_proyecto`

#### **Vistas:**
- Pattern: `ModeloActionView` → `ProyectoListView`, `ActividadCreateView`
- Organizadas en subdirectorios por funcionalidad
- Herencia de: `LoginRequiredMixin`, `ListView`, `CreateView`, etc.

#### **Templates:**
- Estructura: `proyectos/modelo/accion.html`
- Ejemplos: `proyectos/proyecto/list.html`, `proyectos/actividad/form.html`
- Base templates: `base/base.html`, `base/list_base.html`

#### **URLs:**
- Pattern: `modelo_accion` → `proyecto_list`, `actividad_create`
- Namespace: `proyectos:proyecto_list`

### **Bootstrap y Styling:**
- **Bootstrap 5** como framework base
- **Font Awesome** para iconos
- **Cards** para interfaces principales
- **Tables** para listados
- **Badges** para estados: `.bg-success`, `.bg-warning`, `.bg-danger`

### **Forms Pattern:**
```python
class ModeloForm(forms.ModelForm):
    class Meta:
        model = Modelo
        fields = ['campo1', 'campo2']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 4})
        }
```

### **Template Patterns:**
```html
{% extends "base/base.html" %}
{% block title %}Título{% endblock %}
{% block content %}
    <div class="card">
        <div class="card-header">
            <h5>Header</h5>
        </div>
        <div class="card-body">
            <!-- Contenido -->
        </div>
    </div>
{% endblock %}
```

### **Estado de Badges:**
```python
def get_estado_class(self):
    estado_classes = {
        'en_proceso': 'bg-primary text-white',
        'completado': 'bg-success text-white',
        'cancelado': 'bg-danger text-white',
        'pausado': 'bg-warning text-dark',
    }
    return estado_classes.get(self.estado, 'bg-secondary text-white')
```

### **Configuración de Apps:**
```python
# settings.py
INSTALLED_APPS = [
    'proyectos',  # App principal
    'crm',        # Integración
    'crispy_forms',
    'crispy_bootstrap5',
]
```

### **Integración con CRM:**
- Campo `cotizacion_aprobada` conecta con última versión de cotización
- Relación establecida pero manual (pendiente automatización)

---

## **Archivos de Configuración JSON:**
```
/Users/miguelrodriguez/code/RGDAire/proyectos/Entregables.json
- Configuración de entregables por defecto
```

---

# Plan de Sesiones - Mejoras Módulo de Proyectos

## Sesión 1: Filtros y Gestión de Actividades (Estimado: 12,000 tokens)
**Objetivo**: Mejorar filtrado y funcionalidad básica de actividades
- ✅ Filtros de usuario por centro de costos, proyecto y clientes en actividades
- ✅ Quitar campo de prioridad de proyectos
- ✅ Cambiar "trato" por "oferta" en labels
- ✅ Quitar estado "atrasado" de proyectos
- ✅ En listado: reemplazar columna "Orden" por "# Oferta" con enlace a CRM

## Sesión 2: Gestión de Entregables Avanzada (Estimado: 16,000 tokens)
**Objetivo**: Sistema completo de configuración de entregables
- ✅ Modificar entregables obligatorios/opcionales por proyecto
- ✅ Incluir opción "No Aplica" en entregables
- ✅ Posibilidad de agregar entregables adicionales
- ✅ Campo fecha obligatorio con widget calendario
- ✅ Checklist en gestión de entregables
- ✅ Importación de entregables vía plantilla Excel

## Sesión 3: Fechas, Prórrogas y Control Temporal (Estimado: 14,000 tokens)
**Objetivo**: Sistema completo de control de fechas y retrasos
- ✅ Al editar fecha inicio: sumar promesa de días automáticamente
- ✅ Módulo de Prórrogas del proyecto
- ✅ Cálculo automático de días de retraso
- ✅ Control visual de proyectos atrasados con fechas en rojo
- ✅ Integración automática de última versión cotización desde CRM

## Sesión 4: Presupuestos y Bitácoras Avanzadas (Estimado: 18,000 tokens)
**Objetivo**: Control financiero y bitácoras con validación
- ✅ Campo presupuesto de gasto y % de ejecución vs gasto real
- ✅ Bitácoras con fecha de ejecución planeada
- ✅ Listado de bitácoras: rojas las "Planeadas" no registradas
- ✅ Campo líder de trabajo + equipo en bitácoras
- ✅ Validación con firma digital (móvil/PC) por director e ingeniero

## Sesión 5: Comité de Proyectos (Estimado: 12,000 tokens)
**Objetivo**: Módulo completo de seguimiento de comités
- ✅ Módulo de Comité de Proyectos
- ✅ Historial/trazabilidad de comités
- ✅ Auto-despliegue de proyectos activos al crear registro
- ✅ Campo de información por proyecto en comité
- ✅ Registro de participantes del comité

## Estimación Total:
- **Tokens totales**: 72,000 tokens
- **Costo total**: ~$2.70 USD (con contexto limpio)
- **Funcionalidades**: 25 mejoras
- **Costo por funcionalidad**: ~$0.11

---

## Ready for Context Reset

Esta documentación contiene toda la información necesaria para continuar el desarrollo del módulo de proyectos con contexto limpio.