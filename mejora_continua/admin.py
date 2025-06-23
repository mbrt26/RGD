from django.contrib import admin
from .models import SolicitudMejora, ComentarioSolicitud, AdjuntoSolicitud

class ComentarioInline(admin.TabularInline):
    model = ComentarioSolicitud
    extra = 0
    readonly_fields = ('fecha_comentario',)

class AdjuntoInline(admin.TabularInline):
    model = AdjuntoSolicitud
    extra = 0
    readonly_fields = ('fecha_subida',)

@admin.register(SolicitudMejora)
class SolicitudMejoraAdmin(admin.ModelAdmin):
    list_display = [
        'numero_solicitud', 'titulo', 'estado', 'prioridad', 
        'tipo_solicitud', 'modulo_afectado', 'solicitante', 
        'asignado_a', 'fecha_solicitud'
    ]
    list_filter = [
        'estado', 'prioridad', 'tipo_solicitud', 'modulo_afectado',
        'fecha_solicitud', 'asignado_a'
    ]
    search_fields = ['numero_solicitud', 'titulo', 'descripcion']
    readonly_fields = [
        'numero_solicitud', 'fecha_solicitud', 'fecha_actualizacion'
    ]
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'numero_solicitud', 'titulo', 'descripcion', 
                'tipo_solicitud', 'modulo_afectado'
            )
        }),
        ('Estado y Prioridad', {
            'fields': ('estado', 'prioridad')
        }),
        ('Asignación', {
            'fields': (
                'solicitante', 'asignado_a', 'fecha_asignacion',
                'fecha_estimada_completado', 'fecha_completado'
            )
        }),
        ('Información Adicional', {
            'fields': (
                'pasos_reproducir', 'impacto_negocio', 'solucion_propuesta'
            ),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_solicitud', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )
    inlines = [ComentarioInline, AdjuntoInline]
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Si es nuevo
            obj.solicitante = request.user
        super().save_model(request, obj, form, change)

@admin.register(ComentarioSolicitud)
class ComentarioSolicitudAdmin(admin.ModelAdmin):
    list_display = [
        'solicitud', 'autor', 'fecha_comentario', 'es_interno'
    ]
    list_filter = ['fecha_comentario', 'es_interno', 'autor']
    search_fields = ['solicitud__numero_solicitud', 'comentario']
    readonly_fields = ['fecha_comentario']

@admin.register(AdjuntoSolicitud)
class AdjuntoSolicitudAdmin(admin.ModelAdmin):
    list_display = [
        'solicitud', 'nombre_original', 'tipo_archivo', 'tamaño_archivo_legible', 
        'subido_por', 'fecha_subida'
    ]
    list_filter = ['fecha_subida', 'subido_por', 'tipo_archivo']
    search_fields = ['solicitud__numero_solicitud', 'descripcion', 'nombre_original']
    readonly_fields = ['fecha_subida', 'tamaño_archivo', 'nombre_original', 'tipo_archivo']
    
    def tamaño_archivo_legible(self, obj):
        return obj.obtener_tamaño_legible()
    tamaño_archivo_legible.short_description = 'Tamaño'
