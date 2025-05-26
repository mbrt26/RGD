from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Trato

User = get_user_model()

@admin.register(Trato)
class TratoAdmin(admin.ModelAdmin):
    list_display = ('numero_oferta', 'nombre', 'cliente', 'contacto', 'valor', 'estado', 'fuente', 'fecha_creacion')
    list_filter = ('estado', 'fuente', 'fecha_creacion')
    search_fields = ('numero_oferta', 'nombre', 'cliente', 'contacto', 'correo', 'telefono')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'numero_oferta')
    fieldsets = (
        ('Información Básica', {
            'fields': ('numero_oferta', 'nombre', 'cliente', 'contacto', 'correo', 'telefono', 'descripcion')
        }),
        ('Detalles del Trato', {
            'fields': ('valor', 'probabilidad', 'estado', 'fuente', 'fecha_cierre')
        }),
        ('Información de Proyecto', {
            'fields': ('centro_costos', 'nombre_proyecto', 'orden_contrato', 'dias_prometidos')
        }),
        ('Responsable y Notas', {
            'fields': ('responsable', 'notas')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Si es un nuevo trato, establecer el responsable como el usuario actual
            obj.responsable = request.user
        super().save_model(request, obj, form, change)
