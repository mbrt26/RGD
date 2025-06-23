from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Trato, ConfiguracionOferta

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

@admin.register(ConfiguracionOferta)
class ConfiguracionOfertaAdmin(admin.ModelAdmin):
    list_display = ('siguiente_numero', 'actualizado_en', 'actualizado_por')
    readonly_fields = ('creado_en', 'actualizado_en', 'actualizado_por')
    
    def get_queryset(self, request):
        # Solo mostrar la configuración existente
        return super().get_queryset(request)
    
    def has_add_permission(self, request):
        # Solo permitir agregar si no existe ninguna configuración
        return not ConfiguracionOferta.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False
    
    def save_model(self, request, obj, form, change):
        # Registrar quien actualiza la configuración
        obj.actualizado_por = request.user
        super().save_model(request, obj, form, change)
    
    def changelist_view(self, request, extra_context=None):
        # Si no existe configuración, crearla automáticamente
        if not ConfiguracionOferta.objects.exists():
            ConfiguracionOferta.objects.create(siguiente_numero=1)
        return super().changelist_view(request, extra_context)
    
    class Meta:
        verbose_name = 'Configuración de Oferta'
        verbose_name_plural = 'Configuración de Ofertas'
