from django.contrib import admin
from .models import EntregableProyecto, Proyecto

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre_proyecto', 'cliente', 'centro_costos', 'estado')
    search_fields = ('nombre_proyecto', 'cliente', 'centro_costos')
    list_filter = ('estado',)
    ordering = ('nombre_proyecto',)

@admin.register(EntregableProyecto)
class EntregableProyectoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'nombre', 
        'proyecto',
        'fase',
        'estado',
        'obligatorio',
        'seleccionado',
        'medio',
        'dossier_cliente'
    )
    
    list_filter = (
        'fase',
        'estado',
        'obligatorio',
        'seleccionado',
        'medio',
        'dossier_cliente',
        'proyecto'
    )
    
    search_fields = (
        'codigo',
        'nombre',
        'proyecto__nombre_proyecto',
        'proyecto__cliente',
        'proyecto__centro_costos'
    )
    
    readonly_fields = (
        'fecha_creacion',
        'fecha_actualizacion'
    )
    
    autocomplete_fields = ['proyecto']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'codigo',
                'nombre',
                'proyecto',
                'fase',
                'estado'
            )
        }),
        ('Configuración', {
            'fields': (
                'obligatorio',
                'seleccionado',
                'medio',
                'dossier_cliente'
            )
        }),
        ('Responsables', {
            'fields': (
                'creador',
                'consolidador'
            )
        }),
        ('Documentación', {
            'fields': (
                'archivo',
                'fecha_entrega',
                'observaciones'
            )
        }),
        ('Información del Sistema', {
            'classes': ('collapse',),
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion'
            )
        }),
    )
    
    ordering = ('codigo',)
    
    list_per_page = 20
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('proyecto')

    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva instancia
            if not obj.creador:
                obj.creador = request.user.get_full_name() or request.user.username
        super().save_model(request, obj, form, change)