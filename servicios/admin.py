from django.contrib import admin
from django.utils.html import format_html
from .models import Tecnico, SolicitudServicio, InformeTrabajo, MaterialConsumible, UbicacionTecnico


@admin.register(Tecnico)
class TecnicoAdmin(admin.ModelAdmin):
    list_display = ['codigo_tecnico', 'get_nombre_completo', 'telefono', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['codigo_tecnico', 'usuario__first_name', 'usuario__last_name', 'telefono']
    readonly_fields = ['fecha_creacion']
    raw_id_fields = ['usuario']
    
    def get_nombre_completo(self, obj):
        return obj.nombre_completo
    get_nombre_completo.short_description = 'Nombre Completo'


class MaterialConsumibleInline(admin.TabularInline):
    model = MaterialConsumible
    extra = 1
    fields = ['descripcion', 'marca', 'referencia', 'cantidad', 'unidad_medida', 'suministrado_por', 'costo_unitario']


@admin.register(SolicitudServicio)
class SolicitudServicioAdmin(admin.ModelAdmin):
    list_display = ['numero_orden', 'cliente_crm', 'tipo_servicio', 'estado', 'prioridad', 
                   'fecha_programada', 'tecnico_asignado', 'fecha_creacion']
    list_filter = ['estado', 'tipo_servicio', 'prioridad', 'fecha_programada', 'fecha_creacion']
    search_fields = ['numero_orden', 'cliente_crm__nombre', 'direccion_servicio']
    readonly_fields = ['numero_orden', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['cliente_crm', 'contacto_crm', 'tecnico_asignado', 'creado_por']
    date_hierarchy = 'fecha_programada'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_orden', 'estado', 'tipo_servicio', 'prioridad')
        }),
        ('Cliente', {
            'fields': ('cliente_crm', 'contacto_crm', 'direccion_servicio', 'centro_costo')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'duracion_estimada', 'tecnico_asignado')
        }),
        ('Geolocalización', {
            'fields': ('latitud', 'longitud', 'direccion_gps'),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones_internas',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'creado_por'),
            'classes': ('collapse',)
        })
    )


@admin.register(InformeTrabajo)
class InformeTrabajoAdmin(admin.ModelAdmin):
    list_display = ['get_numero_orden', 'get_cliente', 'fecha_servicio', 'completado', 
                   'get_tiempo_total', 'fecha_creacion']
    list_filter = ['completado', 'fecha_servicio', 'satisfaccion_cliente', 'ubicacion_verificada']
    search_fields = ['solicitud_servicio__numero_orden', 'solicitud_servicio__cliente_crm__nombre', 
                    'descripcion_problema', 'detalle_trabajos']
    readonly_fields = ['tiempo_total_minutos', 'fecha_creacion', 'fecha_actualizacion']
    raw_id_fields = ['solicitud_servicio']
    date_hierarchy = 'fecha_servicio'
    inlines = [MaterialConsumibleInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('solicitud_servicio', 'fecha_servicio', 'completado')
        }),
        ('Control de Tiempo', {
            'fields': ('hora_ingreso', 'hora_salida', 'tiempo_total_minutos')
        }),
        ('Diagnóstico', {
            'fields': ('descripcion_problema', 'diagnostico_preliminar', 'detalle_trabajos',
                      'causas_problema', 'tipos_falla')
        }),
        ('Firmas del Técnico', {
            'fields': ('tecnico_nombre', 'tecnico_cargo', 'tecnico_fecha_firma', 'tecnico_firma'),
            'classes': ('collapse',)
        }),
        ('Firmas del Cliente', {
            'fields': ('cliente_nombre', 'cliente_cargo', 'cliente_fecha_firma', 'cliente_firma'),
            'classes': ('collapse',)
        }),
        ('Satisfacción y Observaciones', {
            'fields': ('satisfaccion_cliente', 'recomendaciones', 'observaciones_adicionales')
        }),
        ('Geolocalización', {
            'fields': ('latitud_servicio', 'longitud_servicio', 'ubicacion_verificada'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    
    def get_numero_orden(self, obj):
        return obj.solicitud_servicio.numero_orden
    get_numero_orden.short_description = 'Número de Orden'
    
    def get_cliente(self, obj):
        return obj.solicitud_servicio.cliente_crm.nombre
    get_cliente.short_description = 'Cliente'
    
    def get_tiempo_total(self, obj):
        return obj.tiempo_total_horas
    get_tiempo_total.short_description = 'Tiempo Total'


@admin.register(MaterialConsumible)
class MaterialConsumibleAdmin(admin.ModelAdmin):
    list_display = ['descripcion', 'marca', 'referencia', 'cantidad', 'unidad_medida', 
                   'suministrado_por', 'get_costo_total', 'get_informe']
    list_filter = ['suministrado_por', 'unidad_medida', 'fecha_creacion']
    search_fields = ['descripcion', 'marca', 'referencia']
    readonly_fields = ['fecha_creacion']
    raw_id_fields = ['informe']
    
    def get_costo_total(self, obj):
        return f"${obj.costo_total:,.2f}"
    get_costo_total.short_description = 'Costo Total'
    
    def get_informe(self, obj):
        return obj.informe.solicitud_servicio.numero_orden
    get_informe.short_description = 'Orden de Servicio'


@admin.register(UbicacionTecnico)
class UbicacionTecnicoAdmin(admin.ModelAdmin):
    list_display = ['tecnico', 'get_solicitud', 'latitud', 'longitud', 'precision', 'timestamp']
    list_filter = ['timestamp', 'tecnico']
    search_fields = ['tecnico__codigo_tecnico', 'tecnico__usuario__first_name', 
                    'solicitud_servicio__numero_orden']
    readonly_fields = ['timestamp']
    raw_id_fields = ['tecnico', 'solicitud_servicio']
    date_hierarchy = 'timestamp'
    
    def get_solicitud(self, obj):
        if obj.solicitud_servicio:
            return obj.solicitud_servicio.numero_orden
        return '-'
    get_solicitud.short_description = 'Solicitud de Servicio'
