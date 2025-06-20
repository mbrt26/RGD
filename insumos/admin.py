from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    # Catálogo
    CategoriaProducto, Marca, UnidadMedida, Proveedor, Producto,
    ImagenProducto, EspecificacionTecnica, CompatibilidadEquipo, ProductoEquivalente,
    # Precios
    SegmentoCliente, ListaPrecio, PrecioProducto, DescuentoVolumen,
    # Inventario
    Almacen, Inventario, MovimientoInventario,
    # Cotizaciones y Pedidos
    Cotizacion, ItemCotizacion, Pedido, ItemPedido, EntregaPedido, ItemEntrega,
    # Integración
    RecomendacionProducto, KitMantenimiento, ItemKit
)

# ============================================================================
# CONFIGURACIÓN DEL CATÁLOGO
# ============================================================================

@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'categoria_padre', 'activa', 'orden']
    list_filter = ['activa', 'categoria_padre']
    search_fields = ['nombre', 'codigo', 'descripcion']
    ordering = ['orden', 'nombre']
    list_editable = ['orden', 'activa']

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activa', 'sitio_web', 'productos_count']
    list_filter = ['activa']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['productos_count']
    
    def productos_count(self, obj):
        return obj.productos.count()
    productos_count.short_description = 'Productos'

@admin.register(UnidadMedida)
class UnidadMedidaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'simbolo', 'tipo']
    list_filter = ['tipo']
    search_fields = ['nombre', 'simbolo']

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'contacto', 'telefono', 'email', 'activo', 'descuento_volumen']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'nit', 'contacto', 'email']
    date_hierarchy = 'fecha_creacion'
    list_editable = ['activo']

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1
    fields = ['imagen', 'descripcion', 'orden']

class EspecificacionTecnicaInline(admin.TabularInline):
    model = EspecificacionTecnica
    extra = 1
    fields = ['nombre', 'valor', 'unidad', 'orden']

class CompatibilidadEquipoInline(admin.TabularInline):
    model = CompatibilidadEquipo
    extra = 1
    fields = ['tipo_equipo', 'marca_equipo', 'modelo_equipo', 'capacidad_btu']

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_interno', 'nombre', 'categoria', 'marca', 'precio_venta_base', 
        'stock_total', 'margen_display', 'activo', 'destacado'
    ]
    list_filter = [
        'categoria', 'marca', 'activo', 'destacado', 'requiere_refrigeracion',
        'perecedero', 'peligroso', 'fecha_creacion'
    ]
    search_fields = [
        'codigo_interno', 'codigo_fabricante', 'codigo_barras', 
        'nombre', 'descripcion_corta'
    ]
    readonly_fields = ['margen_display', 'precio_con_iva', 'stock_total', 'fecha_creacion', 'fecha_actualizacion']
    date_hierarchy = 'fecha_creacion'
    list_editable = ['activo', 'destacado']
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                ('codigo_interno', 'codigo_fabricante', 'codigo_barras'),
                'nombre',
                ('descripcion_corta', 'descripcion_tecnica'),
                ('categoria', 'marca', 'modelo'),
                'unidad_medida'
            )
        }),
        ('Especificaciones Físicas', {
            'fields': (
                ('peso', 'largo', 'ancho', 'alto'),
            ),
            'classes': ('collapse',)
        }),
        ('Información Comercial', {
            'fields': (
                ('precio_compra', 'precio_venta_base', 'moneda'),
                ('margen_display', 'precio_con_iva'),
                'iva',
                ('proveedor_principal',),
                'proveedores_alternos'
            )
        }),
        ('Estado y Control', {
            'fields': (
                ('activo', 'destacado'),
                ('requiere_refrigeracion', 'perecedero', 'peligroso'),
            )
        }),
        ('Media y Documentación', {
            'fields': (
                'imagen_principal',
                'ficha_tecnica',
                'manual_instalacion'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': (
                'stock_total',
                ('fecha_creacion', 'fecha_actualizacion'),
                'creado_por'
            ),
            'classes': ('collapse',)
        })
    )
    
    inlines = [ImagenProductoInline, EspecificacionTecnicaInline, CompatibilidadEquipoInline]
    
    def margen_display(self, obj):
        margen = obj.margen_utilidad
        if margen < 10:
            color = 'red'
        elif margen < 25:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, margen
        )
    margen_display.short_description = 'Margen'
    
    def stock_total(self, obj):
        total = sum(inv.stock_actual for inv in obj.inventarios.all())
        if total <= 0:
            color = 'red'
        elif any(inv.requiere_reorden for inv in obj.inventarios.all()):
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {};">{}</span>',
            color, total
        )
    stock_total.short_description = 'Stock Total'

@admin.register(ProductoEquivalente)
class ProductoEquivalenteAdmin(admin.ModelAdmin):
    list_display = ['producto_original', 'producto_equivalente', 'tipo_equivalencia']
    list_filter = ['tipo_equivalencia']
    search_fields = [
        'producto_original__codigo_interno', 'producto_original__nombre',
        'producto_equivalente__codigo_interno', 'producto_equivalente__nombre'
    ]

# ============================================================================
# GESTIÓN DE PRECIOS
# ============================================================================

@admin.register(SegmentoCliente)
class SegmentoClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descuento_general', 'activo']
    list_editable = ['descuento_general', 'activo']
    search_fields = ['nombre', 'descripcion']

class PrecioProductoInline(admin.TabularInline):
    model = PrecioProducto
    extra = 0
    fields = ['producto', 'precio', 'descuento_adicional', 'cantidad_minima']

@admin.register(ListaPrecio)
class ListaPrecioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'segmento', 'fecha_inicio', 'fecha_fin', 'activa', 'productos_count']
    list_filter = ['segmento', 'activa', 'fecha_inicio']
    search_fields = ['nombre', 'segmento__nombre']
    date_hierarchy = 'fecha_inicio'
    list_editable = ['activa']
    inlines = [PrecioProductoInline]
    
    def productos_count(self, obj):
        return obj.precios.count()
    productos_count.short_description = 'Productos'

@admin.register(DescuentoVolumen)
class DescuentoVolumenAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cantidad_minima', 'descuento_porcentaje', 'activo', 'fecha_inicio', 'fecha_fin']
    list_filter = ['activo', 'fecha_inicio', 'producto__categoria']
    search_fields = ['producto__codigo_interno', 'producto__nombre']
    list_editable = ['activo']

# ============================================================================
# GESTIÓN DE INVENTARIO
# ============================================================================

@admin.register(Almacen)
class AlmacenAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'responsable', 'activo', 'productos_count']
    list_filter = ['activo', 'responsable']
    search_fields = ['codigo', 'nombre', 'direccion']
    list_editable = ['activo']
    
    def productos_count(self, obj):
        return obj.inventarios.count()
    productos_count.short_description = 'Productos en Inventario'

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = [
        'producto', 'almacen', 'stock_actual', 'stock_minimo', 'stock_disponible',
        'requiere_reorden_display', 'ubicacion_display'
    ]
    list_filter = [
        'almacen', 'producto__categoria', 'producto__marca', 
        'fecha_vencimiento', 'fecha_actualizacion'
    ]
    search_fields = [
        'producto__codigo_interno', 'producto__nombre', 
        'almacen__codigo', 'almacen__nombre', 'lote'
    ]
    readonly_fields = ['stock_disponible', 'fecha_actualizacion']
    date_hierarchy = 'fecha_actualizacion'
    
    fieldsets = (
        ('Producto y Ubicación', {
            'fields': (
                ('producto', 'almacen'),
                ('pasillo', 'estante', 'nivel', 'posicion')
            )
        }),
        ('Control de Stock', {
            'fields': (
                ('stock_actual', 'stock_minimo', 'stock_maximo'),
                ('stock_reservado', 'stock_disponible')
            )
        }),
        ('Control de Calidad', {
            'fields': (
                ('lote', 'fecha_vencimiento'),
                ('fecha_ultima_entrada', 'fecha_ultima_salida'),
                'fecha_actualizacion'
            )
        })
    )
    
    def requiere_reorden_display(self, obj):
        if obj.requiere_reorden:
            return format_html('<span style="color: red;">SÍ</span>')
        return format_html('<span style="color: green;">NO</span>')
    requiere_reorden_display.short_description = 'Requiere Reorden'
    
    def ubicacion_display(self, obj):
        ubicacion = []
        if obj.pasillo:
            ubicacion.append(f"P:{obj.pasillo}")
        if obj.estante:
            ubicacion.append(f"E:{obj.estante}")
        if obj.nivel:
            ubicacion.append(f"N:{obj.nivel}")
        return " - ".join(ubicacion) if ubicacion else "-"
    ubicacion_display.short_description = 'Ubicación'

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = [
        'inventario', 'tipo_movimiento', 'cantidad', 'costo_unitario',
        'documento_referencia', 'fecha_movimiento', 'usuario'
    ]
    list_filter = [
        'tipo_movimiento', 'fecha_movimiento', 'inventario__almacen',
        'inventario__producto__categoria'
    ]
    search_fields = [
        'inventario__producto__codigo_interno', 'inventario__producto__nombre',
        'documento_referencia', 'pedido_compra', 'orden_venta'
    ]
    readonly_fields = ['fecha_movimiento']
    date_hierarchy = 'fecha_movimiento'

# ============================================================================
# COTIZACIONES Y PEDIDOS
# ============================================================================

class ItemCotizacionInline(admin.TabularInline):
    model = ItemCotizacion
    extra = 0
    fields = [
        'producto', 'cantidad', 'precio_unitario', 'descuento_porcentaje',
        'total_linea', 'tiempo_entrega_dias'
    ]
    readonly_fields = ['total_linea']

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = [
        'numero_cotizacion', 'cliente', 'estado', 'total_general',
        'fecha_creacion', 'fecha_validez', 'esta_vencida_display'
    ]
    list_filter = ['estado', 'fecha_creacion', 'fecha_validez']
    search_fields = [
        'numero_cotizacion', 'cliente__nombre', 'contacto__nombre',
        'trato_crm__numero_oferta'
    ]
    readonly_fields = [
        'numero_cotizacion', 'subtotal', 'total_descuentos', 'total_iva', 'total_general',
        'fecha_creacion', 'fecha_actualizacion', 'esta_vencida_display'
    ]
    date_hierarchy = 'fecha_creacion'
    inlines = [ItemCotizacionInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'numero_cotizacion',
                ('cliente', 'contacto'),
                'estado'
            )
        }),
        ('Referencias', {
            'fields': (
                ('trato_crm', 'orden_mantenimiento'),
                'equipo_referencia'
            ),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': (
                ('fecha_creacion', 'fecha_envio'),
                ('fecha_validez', 'esta_vencida_display'),
                'fecha_respuesta'
            )
        }),
        ('Información Comercial', {
            'fields': (
                ('descuento_general', 'incremento_flete'),
                'observaciones',
                'terminos_condiciones'
            )
        }),
        ('Totales', {
            'fields': (
                ('subtotal', 'total_descuentos'),
                ('total_iva', 'total_general')
            )
        }),
        ('Auditoría', {
            'fields': (
                ('creado_por', 'actualizado_por'),
                'fecha_actualizacion'
            ),
            'classes': ('collapse',)
        })
    )
    
    def esta_vencida_display(self, obj):
        if obj.esta_vencida:
            return format_html('<span style="color: red;">VENCIDA</span>')
        return format_html('<span style="color: green;">VIGENTE</span>')
    esta_vencida_display.short_description = 'Estado Validez'

class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = [
        'producto', 'cantidad_solicitada', 'cantidad_entregada', 'precio_unitario',
        'estado_item', 'almacen_origen'
    ]
    readonly_fields = ['cantidad_entregada']

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_pedido', 'cliente', 'estado', 'total_general',
        'fecha_pedido', 'fecha_entrega_solicitada', 'forma_pago'
    ]
    list_filter = ['estado', 'forma_pago', 'fecha_pedido', 'requiere_instalacion']
    search_fields = [
        'numero_pedido', 'cliente__nombre', 'orden_compra_cliente',
        'cotizacion__numero_cotizacion'
    ]
    readonly_fields = [
        'numero_pedido', 'subtotal', 'total_descuentos', 'total_iva', 'total_general',
        'fecha_pedido', 'fecha_actualizacion'
    ]
    date_hierarchy = 'fecha_pedido'
    inlines = [ItemPedidoInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'numero_pedido',
                ('cliente', 'contacto'),
                'estado'
            )
        }),
        ('Referencias', {
            'fields': (
                ('cotizacion', 'orden_compra_cliente'),
            )
        }),
        ('Fechas', {
            'fields': (
                ('fecha_pedido', 'fecha_entrega_solicitada'),
                ('fecha_entrega_estimada', 'fecha_entrega_real')
            )
        }),
        ('Información Comercial y Logística', {
            'fields': (
                'forma_pago',
                'direccion_entrega',
                'observaciones_entrega',
                ('requiere_instalacion', 'costo_flete')
            )
        }),
        ('Totales', {
            'fields': (
                ('subtotal', 'total_descuentos'),
                'total_iva',
                'total_general'
            )
        }),
        ('Auditoría', {
            'fields': (
                'creado_por',
                'fecha_actualizacion'
            ),
            'classes': ('collapse',)
        })
    )

class ItemEntregaInline(admin.TabularInline):
    model = ItemEntrega
    extra = 0
    fields = ['item_pedido', 'cantidad_entregada', 'lote_entregado', 'observaciones']

@admin.register(EntregaPedido)
class EntregaPedidoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_remision', 'pedido', 'fecha_entrega', 'recibido_por',
        'transportador', 'entregado_por'
    ]
    list_filter = ['fecha_entrega', 'transportador', 'entregado_por']
    search_fields = [
        'numero_remision', 'pedido__numero_pedido', 'recibido_por',
        'cedula_receptor', 'transportador'
    ]
    date_hierarchy = 'fecha_entrega'
    inlines = [ItemEntregaInline]

# ============================================================================
# INTEGRACIÓN Y RECOMENDACIONES
# ============================================================================

@admin.register(RecomendacionProducto)
class RecomendacionProductoAdmin(admin.ModelAdmin):
    list_display = [
        'cliente', 'producto', 'origen_recomendacion', 'prioridad',
        'cantidad_sugerida', 'procesada', 'fecha_creacion'
    ]
    list_filter = [
        'origen_recomendacion', 'prioridad', 'procesada', 'fecha_creacion'
    ]
    search_fields = [
        'cliente__nombre', 'producto__codigo_interno', 'producto__nombre',
        'equipo_mantenimiento', 'orden_trabajo'
    ]
    list_editable = ['procesada']
    date_hierarchy = 'fecha_creacion'

class ItemKitInline(admin.TabularInline):
    model = ItemKit
    extra = 1
    fields = ['producto', 'cantidad', 'opcional', 'orden']

@admin.register(KitMantenimiento)
class KitMantenimientoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_equipo', 'marca_equipo', 'precio_kit',
        'descuento_kit', 'ahorro_display', 'activo'
    ]
    list_filter = ['activo', 'tipo_equipo', 'marca_equipo']
    search_fields = ['nombre', 'descripcion', 'tipo_equipo', 'marca_equipo']
    list_editable = ['activo']
    inlines = [ItemKitInline]
    
    def ahorro_display(self, obj):
        ahorro = obj.ahorro_kit
        if ahorro > 0:
            return format_html(
                '<span style="color: green;">${:,.2f}</span>',
                ahorro
            )
        return format_html('<span style="color: red;">$0.00</span>')
    ahorro_display.short_description = 'Ahorro vs Individual'

# Personalización del sitio de administración
admin.site.site_header = "RGD AIRE - Administración de Insumos"
admin.site.site_title = "RGD AIRE Insumos"
admin.site.index_title = "Panel de Administración de Insumos HVAC"