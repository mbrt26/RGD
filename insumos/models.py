from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import os

User = get_user_model()

class CategoriaProducto(models.Model):
    """Categorías principales de productos HVAC"""
    CATEGORIA_CHOICES = [
        ('filtros', 'Filtros y Elementos Filtrantes'),
        ('refrigerantes', 'Refrigerantes y Gases'),
        ('repuestos', 'Repuestos y Componentes'),
        ('herramientas', 'Herramientas y Equipos'),
        ('instalacion', 'Materiales de Instalación'),
        ('quimicos', 'Químicos y Lubricantes'),
    ]
    
    nombre = models.CharField('Nombre', max_length=100, unique=True)
    codigo = models.CharField('Código', max_length=20, unique=True)
    descripcion = models.TextField('Descripción', blank=True)
    categoria_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategorias')
    activa = models.BooleanField('Activa', default=True)
    orden = models.PositiveIntegerField('Orden', default=0)
    
    class Meta:
        verbose_name = 'Categoría de Producto'
        verbose_name_plural = 'Categorías de Producto'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre

class Marca(models.Model):
    """Marcas de productos"""
    nombre = models.CharField('Nombre', max_length=100, unique=True)
    descripcion = models.TextField('Descripción', blank=True)
    sitio_web = models.URLField('Sitio Web', blank=True)
    logo = models.ImageField('Logo', upload_to='insumos/marcas/', blank=True)
    activa = models.BooleanField('Activa', default=True)
    
    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class UnidadMedida(models.Model):
    """Unidades de medida para productos"""
    nombre = models.CharField('Nombre', max_length=50, unique=True)
    simbolo = models.CharField('Símbolo', max_length=10, unique=True)
    tipo = models.CharField('Tipo', max_length=20, choices=[
        ('cantidad', 'Cantidad'),
        ('peso', 'Peso'),
        ('volumen', 'Volumen'),
        ('longitud', 'Longitud'),
        ('area', 'Área'),
    ], default='cantidad')
    
    class Meta:
        verbose_name = 'Unidad de Medida'
        verbose_name_plural = 'Unidades de Medida'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.simbolo})"

class Proveedor(models.Model):
    """Proveedores de productos"""
    nombre = models.CharField('Nombre', max_length=200)
    nit = models.CharField('NIT', max_length=50, blank=True)
    contacto = models.CharField('Contacto', max_length=100, blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    email = models.EmailField('Email', blank=True)
    direccion = models.TextField('Dirección', blank=True)
    terminos_pago = models.CharField('Términos de Pago', max_length=100, blank=True)
    descuento_volumen = models.DecimalField('Descuento por Volumen (%)', max_digits=5, decimal_places=2, default=0)
    activo = models.BooleanField('Activo', default=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    """Catálogo principal de productos"""
    # Información básica
    codigo_interno = models.CharField('Código Interno', max_length=50, unique=True)
    codigo_fabricante = models.CharField('Código Fabricante', max_length=100, blank=True)
    codigo_barras = models.CharField('Código de Barras', max_length=50, blank=True)
    nombre = models.CharField('Nombre', max_length=200)
    descripcion_corta = models.CharField('Descripción Corta', max_length=500, blank=True)
    descripcion_tecnica = models.TextField('Descripción Técnica', blank=True)
    
    # Categorización
    categoria = models.ForeignKey(CategoriaProducto, on_delete=models.CASCADE, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='productos')
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    
    # Especificaciones físicas
    unidad_medida = models.ForeignKey(UnidadMedida, on_delete=models.CASCADE)
    peso = models.DecimalField('Peso (kg)', max_digits=10, decimal_places=3, null=True, blank=True)
    largo = models.DecimalField('Largo (cm)', max_digits=10, decimal_places=2, null=True, blank=True)
    ancho = models.DecimalField('Ancho (cm)', max_digits=10, decimal_places=2, null=True, blank=True)
    alto = models.DecimalField('Alto (cm)', max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Información comercial
    precio_compra = models.DecimalField('Precio de Compra', max_digits=12, decimal_places=2, default=0)
    precio_venta_base = models.DecimalField('Precio de Venta Base', max_digits=12, decimal_places=2, default=0)
    moneda = models.CharField('Moneda', max_length=3, choices=[
        ('COP', 'Peso Colombiano'),
        ('USD', 'Dólar Americano'),
    ], default='COP')
    iva = models.DecimalField('IVA (%)', max_digits=5, decimal_places=2, default=19)
    
    # Proveedores
    proveedor_principal = models.ForeignKey(
        Proveedor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='productos_principales'
    )
    proveedores_alternos = models.ManyToManyField(
        Proveedor, 
        blank=True, 
        related_name='productos_alternos'
    )
    
    # Estado y control
    activo = models.BooleanField('Activo', default=True)
    destacado = models.BooleanField('Producto Destacado', default=False)
    requiere_refrigeracion = models.BooleanField('Requiere Refrigeración', default=False)
    perecedero = models.BooleanField('Perecedero', default=False)
    peligroso = models.BooleanField('Material Peligroso', default=False)
    
    # Media
    imagen_principal = models.ImageField('Imagen Principal', upload_to='insumos/productos/', blank=True)
    ficha_tecnica = models.FileField('Ficha Técnica', upload_to='insumos/fichas/', blank=True)
    manual_instalacion = models.FileField('Manual de Instalación', upload_to='insumos/manuales/', blank=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['categoria', 'marca', 'nombre']
        indexes = [
            models.Index(fields=['codigo_interno']),
            models.Index(fields=['categoria', 'marca']),
            models.Index(fields=['activo']),
        ]
    
    def __str__(self):
        return f"{self.codigo_interno} - {self.nombre}"
    
    @property
    def margen_utilidad(self):
        """Calcula el margen de utilidad en porcentaje"""
        if self.precio_compra > 0:
            return ((self.precio_venta_base - self.precio_compra) / self.precio_compra) * 100
        return 0
    
    @property
    def precio_con_iva(self):
        """Precio de venta incluyendo IVA"""
        return self.precio_venta_base * (1 + self.iva / 100)
    
    def clean(self):
        if self.precio_venta_base < self.precio_compra:
            raise ValidationError('El precio de venta no puede ser menor al precio de compra.')

class ImagenProducto(models.Model):
    """Imágenes adicionales de productos"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField('Imagen', upload_to='insumos/productos/')
    descripcion = models.CharField('Descripción', max_length=200, blank=True)
    orden = models.PositiveIntegerField('Orden', default=0)
    
    class Meta:
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Producto'
        ordering = ['orden']

class EspecificacionTecnica(models.Model):
    """Especificaciones técnicas detalladas de productos"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='especificaciones')
    nombre = models.CharField('Especificación', max_length=100)
    valor = models.CharField('Valor', max_length=200)
    unidad = models.CharField('Unidad', max_length=50, blank=True)
    orden = models.PositiveIntegerField('Orden', default=0)
    
    class Meta:
        verbose_name = 'Especificación Técnica'
        verbose_name_plural = 'Especificaciones Técnicas'
        ordering = ['orden', 'nombre']
        unique_together = ['producto', 'nombre']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.nombre}: {self.valor}"

class CompatibilidadEquipo(models.Model):
    """Compatibilidad de productos con equipos del módulo de mantenimiento"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='compatibilidades')
    # Relación con el módulo de mantenimiento
    tipo_equipo = models.CharField('Tipo de Equipo', max_length=100)
    marca_equipo = models.CharField('Marca del Equipo', max_length=100, blank=True)
    modelo_equipo = models.CharField('Modelo del Equipo', max_length=100, blank=True)
    capacidad_btu = models.CharField('Capacidad BTU', max_length=50, blank=True)
    notas = models.TextField('Notas de Compatibilidad', blank=True)
    
    class Meta:
        verbose_name = 'Compatibilidad con Equipo'
        verbose_name_plural = 'Compatibilidades con Equipos'
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.tipo_equipo}"

class ProductoEquivalente(models.Model):
    """Productos equivalentes o sustitutos"""
    producto_original = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='equivalentes'
    )
    producto_equivalente = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='original_de'
    )
    tipo_equivalencia = models.CharField('Tipo', max_length=20, choices=[
        ('exacto', 'Equivalente Exacto'),
        ('similar', 'Similar'),
        ('mejor', 'Upgrade/Mejora'),
        ('economico', 'Opción Económica'),
    ], default='similar')
    notas = models.TextField('Notas', blank=True)
    
    class Meta:
        verbose_name = 'Producto Equivalente'
        verbose_name_plural = 'Productos Equivalentes'
        unique_together = ['producto_original', 'producto_equivalente']
    
    def __str__(self):
        return f"{self.producto_original.codigo_interno} ≈ {self.producto_equivalente.codigo_interno}"

# ============================================================================
# GESTIÓN DE PRECIOS Y DESCUENTOS
# ============================================================================

class SegmentoCliente(models.Model):
    """Segmentos de clientes para precios diferenciados"""
    nombre = models.CharField('Nombre', max_length=100, unique=True)
    descripcion = models.TextField('Descripción', blank=True)
    descuento_general = models.DecimalField('Descuento General (%)', max_digits=5, decimal_places=2, default=0)
    activo = models.BooleanField('Activo', default=True)
    
    class Meta:
        verbose_name = 'Segmento de Cliente'
        verbose_name_plural = 'Segmentos de Cliente'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class ListaPrecio(models.Model):
    """Listas de precios por segmento"""
    nombre = models.CharField('Nombre', max_length=100)
    segmento = models.ForeignKey(SegmentoCliente, on_delete=models.CASCADE, related_name='listas_precios')
    fecha_inicio = models.DateField('Fecha de Inicio')
    fecha_fin = models.DateField('Fecha de Fin', null=True, blank=True)
    activa = models.BooleanField('Activa', default=True)
    observaciones = models.TextField('Observaciones', blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Lista de Precios'
        verbose_name_plural = 'Listas de Precios'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.nombre} - {self.segmento.nombre}"

class PrecioProducto(models.Model):
    """Precios específicos por producto y lista"""
    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.CASCADE, related_name='precios')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='precios_especiales')
    precio = models.DecimalField('Precio', max_digits=12, decimal_places=2)
    descuento_adicional = models.DecimalField('Descuento Adicional (%)', max_digits=5, decimal_places=2, default=0)
    cantidad_minima = models.PositiveIntegerField('Cantidad Mínima', default=1)
    
    class Meta:
        verbose_name = 'Precio de Producto'
        verbose_name_plural = 'Precios de Producto'
        unique_together = ['lista_precio', 'producto', 'cantidad_minima']
    
    def __str__(self):
        return f"{self.producto.codigo_interno} - {self.lista_precio.nombre}: ${self.precio}"

class DescuentoVolumen(models.Model):
    """Descuentos por volumen de compra"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='descuentos_volumen')
    cantidad_minima = models.PositiveIntegerField('Cantidad Mínima')
    descuento_porcentaje = models.DecimalField('Descuento (%)', max_digits=5, decimal_places=2)
    activo = models.BooleanField('Activo', default=True)
    fecha_inicio = models.DateField('Fecha de Inicio', default=timezone.now)
    fecha_fin = models.DateField('Fecha de Fin', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Descuento por Volumen'
        verbose_name_plural = 'Descuentos por Volumen'
        ordering = ['producto', 'cantidad_minima']
    
    def __str__(self):
        return f"{self.producto.codigo_interno} - {self.cantidad_minima}+ unidades: {self.descuento_porcentaje}%"

# ============================================================================
# GESTIÓN DE INVENTARIO
# ============================================================================

class Almacen(models.Model):
    """Almacenes o bodegas"""
    nombre = models.CharField('Nombre', max_length=100, unique=True)
    codigo = models.CharField('Código', max_length=20, unique=True)
    direccion = models.TextField('Dirección', blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    activo = models.BooleanField('Activo', default=True)
    
    class Meta:
        verbose_name = 'Almacén'
        verbose_name_plural = 'Almacenes'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class Inventario(models.Model):
    """Control de inventario por producto y almacén"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='inventarios')
    almacen = models.ForeignKey(Almacen, on_delete=models.CASCADE, related_name='inventarios')
    
    # Cantidades
    stock_actual = models.DecimalField('Stock Actual', max_digits=10, decimal_places=2, default=0)
    stock_minimo = models.DecimalField('Stock Mínimo', max_digits=10, decimal_places=2, default=0)
    stock_maximo = models.DecimalField('Stock Máximo', max_digits=10, decimal_places=2, default=0)
    stock_reservado = models.DecimalField('Stock Reservado', max_digits=10, decimal_places=2, default=0)
    
    # Ubicación física
    pasillo = models.CharField('Pasillo', max_length=10, blank=True)
    estante = models.CharField('Estante', max_length=10, blank=True)
    nivel = models.CharField('Nivel', max_length=10, blank=True)
    posicion = models.CharField('Posición', max_length=20, blank=True)
    
    # Control de calidad
    lote = models.CharField('Lote', max_length=50, blank=True)
    fecha_vencimiento = models.DateField('Fecha de Vencimiento', null=True, blank=True)
    fecha_ultima_entrada = models.DateTimeField('Última Entrada', null=True, blank=True)
    fecha_ultima_salida = models.DateTimeField('Última Salida', null=True, blank=True)
    
    # Auditoría
    fecha_actualizacion = models.DateTimeField('Última Actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventarios'
        unique_together = ['producto', 'almacen']
        indexes = [
            models.Index(fields=['producto', 'almacen']),
            models.Index(fields=['stock_actual']),
        ]
    
    def __str__(self):
        return f"{self.producto.codigo_interno} - {self.almacen.codigo}: {self.stock_actual}"
    
    @property
    def stock_disponible(self):
        """Stock disponible para venta (actual - reservado)"""
        return self.stock_actual - self.stock_reservado
    
    @property
    def requiere_reorden(self):
        """Indica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo
    
    @property
    def dias_hasta_vencimiento(self):
        """Días hasta el vencimiento del producto"""
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - timezone.now().date()
            return delta.days
        return None

class MovimientoInventario(models.Model):
    """Registro de movimientos de inventario"""
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('transferencia', 'Transferencia'),
        ('devolucion', 'Devolución'),
    ]
    
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField('Tipo de Movimiento', max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.DecimalField('Cantidad', max_digits=10, decimal_places=2)
    costo_unitario = models.DecimalField('Costo Unitario', max_digits=12, decimal_places=2, default=0)
    
    # Referencias
    documento_referencia = models.CharField('Documento de Referencia', max_length=100, blank=True)
    pedido_compra = models.CharField('Pedido de Compra', max_length=100, blank=True)
    orden_venta = models.CharField('Orden de Venta', max_length=100, blank=True)
    
    # Detalles
    observaciones = models.TextField('Observaciones', blank=True)
    lote = models.CharField('Lote', max_length=50, blank=True)
    fecha_vencimiento = models.DateField('Fecha de Vencimiento', null=True, blank=True)
    
    # Auditoría
    fecha_movimiento = models.DateTimeField('Fecha del Movimiento', default=timezone.now)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha_movimiento']
        indexes = [
            models.Index(fields=['inventario', 'fecha_movimiento']),
            models.Index(fields=['tipo_movimiento']),
        ]
    
    def __str__(self):
        return f"{self.inventario.producto.codigo_interno} - {self.tipo_movimiento}: {self.cantidad}"
    
    def save(self, *args, **kwargs):
        """Actualizar el inventario cuando se guarda un movimiento"""
        super().save(*args, **kwargs)
        
        # Actualizar stock actual según el tipo de movimiento
        if self.tipo_movimiento in ['entrada', 'devolucion']:
            self.inventario.stock_actual += self.cantidad
        elif self.tipo_movimiento == 'salida':
            self.inventario.stock_actual -= self.cantidad
        elif self.tipo_movimiento == 'ajuste':
            # En ajustes, la cantidad representa el nuevo stock total
            self.inventario.stock_actual = self.cantidad
        
        # Actualizar fechas de última entrada/salida
        if self.tipo_movimiento in ['entrada', 'devolucion']:
            self.inventario.fecha_ultima_entrada = self.fecha_movimiento
        elif self.tipo_movimiento == 'salida':
            self.inventario.fecha_ultima_salida = self.fecha_movimiento
        
        self.inventario.save()

# ============================================================================
# GESTIÓN DE COTIZACIONES Y PEDIDOS
# ============================================================================

class Cotizacion(models.Model):
    """Cotizaciones de insumos"""
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('en_negociacion', 'En Negociación'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('vencida', 'Vencida'),
    ]
    
    # Información básica
    numero_cotizacion = models.CharField('Número de Cotización', max_length=20, unique=True, blank=True)
    cliente = models.ForeignKey('crm.Cliente', on_delete=models.CASCADE, related_name='cotizaciones_insumos')
    contacto = models.ForeignKey('crm.Contacto', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Referencias de integración
    trato_crm = models.ForeignKey('crm.Trato', on_delete=models.SET_NULL, null=True, blank=True, related_name='cotizaciones_insumos')
    orden_mantenimiento = models.CharField('Orden de Mantenimiento', max_length=100, blank=True)
    equipo_referencia = models.CharField('Equipo de Referencia', max_length=200, blank=True)
    
    # Estado y fechas
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='borrador')
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_envio = models.DateTimeField('Fecha de Envío', null=True, blank=True)
    fecha_validez = models.DateField('Válida Hasta')
    fecha_respuesta = models.DateTimeField('Fecha de Respuesta', null=True, blank=True)
    
    # Información comercial
    descuento_general = models.DecimalField('Descuento General (%)', max_digits=5, decimal_places=2, default=0)
    incremento_flete = models.DecimalField('Flete', max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField('Observaciones', blank=True)
    terminos_condiciones = models.TextField('Términos y Condiciones', blank=True)
    
    # Totales calculados
    subtotal = models.DecimalField('Subtotal', max_digits=12, decimal_places=2, default=0)
    total_descuentos = models.DecimalField('Total Descuentos', max_digits=12, decimal_places=2, default=0)
    total_iva = models.DecimalField('Total IVA', max_digits=12, decimal_places=2, default=0)
    total_general = models.DecimalField('Total General', max_digits=12, decimal_places=2, default=0)
    
    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cotizaciones_creadas')
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cotizaciones_actualizadas')
    fecha_actualizacion = models.DateTimeField('Última Actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['numero_cotizacion']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['fecha_creacion']),
        ]
    
    def __str__(self):
        return f"{self.numero_cotizacion} - {self.cliente.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.numero_cotizacion:
            # Generar número de cotización automático
            year = timezone.now().year
            count = Cotizacion.objects.filter(fecha_creacion__year=year).count() + 1
            self.numero_cotizacion = f"COT-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        """Calcula los totales de la cotización"""
        items = self.items.all()
        
        self.subtotal = sum(item.total_linea for item in items)
        self.total_descuentos = sum(item.descuento_aplicado for item in items)
        self.total_iva = sum(item.iva_linea for item in items)
        self.total_general = self.subtotal - self.total_descuentos + self.total_iva + self.incremento_flete
        
        # Aplicar descuento general
        if self.descuento_general > 0:
            descuento_general_valor = (self.subtotal * self.descuento_general) / 100
            self.total_descuentos += descuento_general_valor
            self.total_general -= descuento_general_valor
        
        self.save(update_fields=['subtotal', 'total_descuentos', 'total_iva', 'total_general'])
    
    @property
    def esta_vencida(self):
        """Verifica si la cotización está vencida"""
        return timezone.now().date() > self.fecha_validez

class ItemCotizacion(models.Model):
    """Items de una cotización"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    # Cantidades y precios
    cantidad = models.DecimalField('Cantidad', max_digits=10, decimal_places=2)
    precio_unitario = models.DecimalField('Precio Unitario', max_digits=12, decimal_places=2)
    descuento_porcentaje = models.DecimalField('Descuento (%)', max_digits=5, decimal_places=2, default=0)
    descuento_valor = models.DecimalField('Descuento Valor', max_digits=12, decimal_places=2, default=0)
    
    # Información adicional
    observaciones = models.TextField('Observaciones', blank=True)
    tiempo_entrega_dias = models.PositiveIntegerField('Tiempo de Entrega (días)', default=0)
    
    # Campos calculados
    total_linea = models.DecimalField('Total Línea', max_digits=12, decimal_places=2, default=0)
    descuento_aplicado = models.DecimalField('Descuento Aplicado', max_digits=12, decimal_places=2, default=0)
    iva_linea = models.DecimalField('IVA Línea', max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Item de Cotización'
        verbose_name_plural = 'Items de Cotización'
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        # Calcular totales automáticamente
        self.total_linea = self.cantidad * self.precio_unitario
        
        # Calcular descuento
        if self.descuento_porcentaje > 0:
            self.descuento_aplicado = (self.total_linea * self.descuento_porcentaje) / 100
        else:
            self.descuento_aplicado = self.descuento_valor
        
        # Calcular IVA sobre el total menos descuento
        base_iva = self.total_linea - self.descuento_aplicado
        self.iva_linea = (base_iva * self.producto.iva) / 100
        
        super().save(*args, **kwargs)
        
        # Actualizar totales de la cotización
        self.cotizacion.calcular_totales()
    
    def __str__(self):
        return f"{self.cotizacion.numero_cotizacion} - {self.producto.codigo_interno}"

class Pedido(models.Model):
    """Pedidos de insumos"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('en_preparacion', 'En Preparación'),
        ('listo_despacho', 'Listo para Despacho'),
        ('despachado', 'Despachado'),
        ('entregado', 'Entregado'),
        ('facturado', 'Facturado'),
        ('cancelado', 'Cancelado'),
    ]
    
    FORMA_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito_30', 'Crédito 30 días'),
        ('credito_60', 'Crédito 60 días'),
        ('credito_90', 'Crédito 90 días'),
        ('consignacion', 'Consignación'),
    ]
    
    # Información básica
    numero_pedido = models.CharField('Número de Pedido', max_length=20, unique=True, blank=True)
    cliente = models.ForeignKey('crm.Cliente', on_delete=models.CASCADE, related_name='pedidos_insumos')
    contacto = models.ForeignKey('crm.Contacto', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Referencias
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='pedidos')
    orden_compra_cliente = models.CharField('Orden de Compra del Cliente', max_length=100, blank=True)
    
    # Estado y fechas
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_pedido = models.DateTimeField('Fecha del Pedido', auto_now_add=True)
    fecha_entrega_solicitada = models.DateField('Fecha de Entrega Solicitada')
    fecha_entrega_estimada = models.DateField('Fecha de Entrega Estimada', null=True, blank=True)
    fecha_entrega_real = models.DateTimeField('Fecha de Entrega Real', null=True, blank=True)
    
    # Información comercial y logística
    forma_pago = models.CharField('Forma de Pago', max_length=20, choices=FORMA_PAGO_CHOICES)
    direccion_entrega = models.TextField('Dirección de Entrega')
    observaciones_entrega = models.TextField('Observaciones de Entrega', blank=True)
    requiere_instalacion = models.BooleanField('Requiere Instalación', default=False)
    
    # Totales
    subtotal = models.DecimalField('Subtotal', max_digits=12, decimal_places=2, default=0)
    total_descuentos = models.DecimalField('Total Descuentos', max_digits=12, decimal_places=2, default=0)
    total_iva = models.DecimalField('Total IVA', max_digits=12, decimal_places=2, default=0)
    costo_flete = models.DecimalField('Costo de Flete', max_digits=10, decimal_places=2, default=0)
    total_general = models.DecimalField('Total General', max_digits=12, decimal_places=2, default=0)
    
    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_actualizacion = models.DateTimeField('Última Actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_pedido']
        indexes = [
            models.Index(fields=['numero_pedido']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['fecha_pedido']),
        ]
    
    def __str__(self):
        return f"{self.numero_pedido} - {self.cliente.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            # Generar número de pedido automático
            year = timezone.now().year
            count = Pedido.objects.filter(fecha_pedido__year=year).count() + 1
            self.numero_pedido = f"PED-{year}-{count:04d}"
        super().save(*args, **kwargs)
    
    def calcular_totales(self):
        """Calcula los totales del pedido"""
        items = self.items.all()
        
        self.subtotal = sum(item.total_linea for item in items)
        self.total_descuentos = sum(item.descuento_aplicado for item in items)
        self.total_iva = sum(item.iva_linea for item in items)
        self.total_general = self.subtotal - self.total_descuentos + self.total_iva + self.costo_flete
        
        self.save(update_fields=['subtotal', 'total_descuentos', 'total_iva', 'total_general'])

class ItemPedido(models.Model):
    """Items de un pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    
    # Cantidades y precios
    cantidad_solicitada = models.DecimalField('Cantidad Solicitada', max_digits=10, decimal_places=2)
    cantidad_entregada = models.DecimalField('Cantidad Entregada', max_digits=10, decimal_places=2, default=0)
    precio_unitario = models.DecimalField('Precio Unitario', max_digits=12, decimal_places=2)
    descuento_porcentaje = models.DecimalField('Descuento (%)', max_digits=5, decimal_places=2, default=0)
    
    # Estado del item
    estado_item = models.CharField('Estado del Item', max_length=20, choices=[
        ('pendiente', 'Pendiente'),
        ('reservado', 'Reservado'),
        ('alistado', 'Alistado'),
        ('despachado', 'Despachado'),
        ('entregado', 'Entregado'),
        ('devuelto', 'Devuelto'),
    ], default='pendiente')
    
    # Información de inventario
    almacen_origen = models.ForeignKey(Almacen, on_delete=models.SET_NULL, null=True, blank=True)
    lote = models.CharField('Lote', max_length=50, blank=True)
    
    # Campos calculados
    total_linea = models.DecimalField('Total Línea', max_digits=12, decimal_places=2, default=0)
    descuento_aplicado = models.DecimalField('Descuento Aplicado', max_digits=12, decimal_places=2, default=0)
    iva_linea = models.DecimalField('IVA Línea', max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Items de Pedido'
        ordering = ['id']
    
    def save(self, *args, **kwargs):
        # Calcular totales automáticamente
        self.total_linea = self.cantidad_solicitada * self.precio_unitario
        
        # Calcular descuento
        if self.descuento_porcentaje > 0:
            self.descuento_aplicado = (self.total_linea * self.descuento_porcentaje) / 100
        
        # Calcular IVA
        base_iva = self.total_linea - self.descuento_aplicado
        self.iva_linea = (base_iva * self.producto.iva) / 100
        
        super().save(*args, **kwargs)
        
        # Actualizar totales del pedido
        self.pedido.calcular_totales()
    
    @property
    def cantidad_pendiente(self):
        """Cantidad pendiente por entregar"""
        return self.cantidad_solicitada - self.cantidad_entregada
    
    def __str__(self):
        return f"{self.pedido.numero_pedido} - {self.producto.codigo_interno}"

class EntregaPedido(models.Model):
    """Registro de entregas de pedidos"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='entregas')
    numero_remision = models.CharField('Número de Remisión', max_length=50, unique=True)
    fecha_entrega = models.DateTimeField('Fecha de Entrega')
    
    # Información del receptor
    recibido_por = models.CharField('Recibido Por', max_length=200)
    cedula_receptor = models.CharField('Cédula del Receptor', max_length=20, blank=True)
    telefono_receptor = models.CharField('Teléfono del Receptor', max_length=20, blank=True)
    
    # Detalles de la entrega
    observaciones = models.TextField('Observaciones', blank=True)
    foto_entrega = models.ImageField('Foto de Entrega', upload_to='insumos/entregas/', blank=True)
    firma_digital = models.TextField('Firma Digital (Base64)', blank=True)
    
    # Información del transportador
    transportador = models.CharField('Transportador', max_length=200, blank=True)
    vehiculo = models.CharField('Vehículo/Placa', max_length=50, blank=True)
    conductor = models.CharField('Conductor', max_length=200, blank=True)
    
    # Auditoría
    entregado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Entrega de Pedido'
        verbose_name_plural = 'Entregas de Pedido'
        ordering = ['-fecha_entrega']
    
    def __str__(self):
        return f"Remisión {self.numero_remision} - {self.pedido.numero_pedido}"

class ItemEntrega(models.Model):
    """Items específicos entregados en cada entrega"""
    entrega = models.ForeignKey(EntregaPedido, on_delete=models.CASCADE, related_name='items_entregados')
    item_pedido = models.ForeignKey(ItemPedido, on_delete=models.CASCADE)
    cantidad_entregada = models.DecimalField('Cantidad Entregada', max_digits=10, decimal_places=2)
    lote_entregado = models.CharField('Lote Entregado', max_length=50, blank=True)
    observaciones = models.TextField('Observaciones', blank=True)
    
    class Meta:
        verbose_name = 'Item de Entrega'
        verbose_name_plural = 'Items de Entrega'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Actualizar cantidad entregada en el item del pedido
        total_entregado = ItemEntrega.objects.filter(
            item_pedido=self.item_pedido
        ).aggregate(
            total=models.Sum('cantidad_entregada')
        )['total'] or 0
        
        self.item_pedido.cantidad_entregada = total_entregado
        self.item_pedido.save()
    
    def __str__(self):
        return f"{self.entrega.numero_remision} - {self.item_pedido.producto.codigo_interno}"

# ============================================================================
# INTEGRACIÓN CON OTROS MÓDULOS
# ============================================================================

class RecomendacionProducto(models.Model):
    """Recomendaciones automáticas de productos"""
    ORIGEN_CHOICES = [
        ('mantenimiento', 'Mantenimiento Preventivo'),
        ('servicios', 'Servicio Técnico'),
        ('historial', 'Historial de Compras'),
        ('compatibilidad', 'Compatibilidad de Equipo'),
        ('cross_selling', 'Venta Cruzada'),
    ]
    
    cliente = models.ForeignKey('crm.Cliente', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    origen_recomendacion = models.CharField('Origen', max_length=20, choices=ORIGEN_CHOICES)
    
    # Referencias opcionales
    equipo_mantenimiento = models.CharField('Equipo de Mantenimiento', max_length=200, blank=True)
    orden_trabajo = models.CharField('Orden de Trabajo', max_length=100, blank=True)
    
    # Detalles de la recomendación
    prioridad = models.CharField('Prioridad', max_length=10, choices=[
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ], default='media')
    
    motivo = models.TextField('Motivo de la Recomendación')
    cantidad_sugerida = models.DecimalField('Cantidad Sugerida', max_digits=10, decimal_places=2, default=1)
    fecha_sugerida = models.DateField('Fecha Sugerida', null=True, blank=True)
    
    # Estado
    procesada = models.BooleanField('Procesada', default=False)
    cotizacion_generada = models.ForeignKey(Cotizacion, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_procesamiento = models.DateTimeField('Fecha de Procesamiento', null=True, blank=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Recomendación de Producto'
        verbose_name_plural = 'Recomendaciones de Producto'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['cliente', 'procesada']),
            models.Index(fields=['origen_recomendacion']),
        ]
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.producto.codigo_interno} ({self.origen_recomendacion})"

class KitMantenimiento(models.Model):
    """Kits pre-configurados de productos para mantenimiento"""
    nombre = models.CharField('Nombre del Kit', max_length=200)
    descripcion = models.TextField('Descripción')
    
    # Compatibilidad
    tipo_equipo = models.CharField('Tipo de Equipo', max_length=100, blank=True)
    marca_equipo = models.CharField('Marca del Equipo', max_length=100, blank=True)
    capacidad_btu = models.CharField('Capacidad BTU', max_length=50, blank=True)
    
    # Configuración
    activo = models.BooleanField('Activo', default=True)
    frecuencia_uso = models.PositiveIntegerField('Frecuencia de Uso (meses)', default=12)
    precio_kit = models.DecimalField('Precio del Kit', max_digits=12, decimal_places=2, default=0)
    descuento_kit = models.DecimalField('Descuento del Kit (%)', max_digits=5, decimal_places=2, default=0)
    
    # Auditoría
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = 'Kit de Mantenimiento'
        verbose_name_plural = 'Kits de Mantenimiento'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def calcular_precio_individual(self):
        """Calcula el precio sumando productos individuales"""
        total = sum(item.producto.precio_venta_base * item.cantidad for item in self.items.all())
        return total
    
    @property
    def ahorro_kit(self):
        """Calcula el ahorro al comprar el kit vs productos individuales"""
        precio_individual = self.calcular_precio_individual()
        if precio_individual > 0:
            return precio_individual - self.precio_kit
        return 0

class ItemKit(models.Model):
    """Items que componen un kit de mantenimiento"""
    kit = models.ForeignKey(KitMantenimiento, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.DecimalField('Cantidad', max_digits=10, decimal_places=2)
    opcional = models.BooleanField('Opcional', default=False)
    orden = models.PositiveIntegerField('Orden', default=0)
    
    class Meta:
        verbose_name = 'Item de Kit'
        verbose_name_plural = 'Items de Kit'
        ordering = ['orden']
        unique_together = ['kit', 'producto']
    
    def __str__(self):
        return f"{self.kit.nombre} - {self.producto.codigo_interno}"