from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Cliente(models.Model):
    nombre = models.CharField('Nombre', max_length=200)
    sector_actividad = models.CharField('Sector de Actividad', max_length=100, blank=True)
    correo = models.EmailField('Correo Electrónico', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    direccion = models.TextField('Dirección', blank=True)
    notas = models.TextField('Notas', blank=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', default=timezone.now)
    direccion_linea1 = models.CharField('Dirección Línea 1', max_length=200, blank=True)
    direccion_linea2 = models.CharField('Dirección Línea 2', max_length=200, blank=True)
    ciudad = models.CharField('Ciudad', max_length=100, blank=True)
    estado = models.CharField('Estado/Departamento', max_length=100, blank=True)
    pais = models.CharField('País', max_length=100, blank=True)
    codigo_postal = models.CharField('Código Postal', max_length=20, blank=True)
    rut = models.FileField('RUT', upload_to='clientes/rut/', blank=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class DocumentoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, related_name='documentos', on_delete=models.CASCADE)
    archivo = models.FileField('Archivo', upload_to='clientes/documentos/')
    nombre = models.CharField('Nombre del documento', max_length=255)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True)

    class Meta:
        verbose_name = 'Documento del Cliente'
        verbose_name_plural = 'Documentos del Cliente'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.nombre} - {self.cliente.nombre}"

class Contacto(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='contactos')
    nombre = models.CharField('Nombre', max_length=200)
    cargo = models.CharField('Cargo', max_length=100, blank=True)
    correo = models.EmailField('Correo Electrónico', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    notas = models.TextField('Notas', blank=True)

    class Meta:
        verbose_name = 'Contacto'
        verbose_name_plural = 'Contactos'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} - {self.cliente}"

class RepresentanteVentas(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    meta_ventas = models.DecimalField('Meta de Ventas', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Representante de Ventas'
        verbose_name_plural = 'Representantes de Ventas'

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def nombre(self):
        """
        Returns the full name of the sales representative
        """
        if self.usuario:
            return self.usuario.get_full_name() or self.usuario.username
        return "Sin nombre"

class Trato(models.Model):
    """
    Modelo para representar un trato o negocio en el CRM.
    """
    ESTADO_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('cotizacion', 'Cotización Enviada'),
        ('negociacion', 'En Negociación'),
        ('ganado', 'Ganado'),
        ('perdido', 'Perdido'),
        ('cancelado', 'Cancelado'),
    ]
    
    FUENTE_CHOICES = [
        ('web', 'Sitio Web'),
        ('referido', 'Referido'),
        ('redes', 'Redes Sociales'),
        ('publicidad', 'Publicidad'),
        ('evento', 'Evento'),
        ('otro', 'Otro'),
    ]

    TIPO_CHOICES = [
        ('producto', 'Venta de Producto'),
        ('servicio', 'Prestación de Servicio'),
        ('proyecto', 'Proyecto'),
        ('mantenimiento', 'Mantenimiento'),
        ('consultoria', 'Consultoría'),
        ('otro', 'Otro'),
    ]
    
    numero_oferta = models.CharField('# Oferta', max_length=10, unique=True, blank=True)
    nombre = models.CharField('Nombre del Trato', max_length=200, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, verbose_name='Cliente', on_delete=models.CASCADE, related_name='tratos')
    contacto = models.CharField('Contacto', max_length=200, blank=True)
    correo = models.EmailField('Correo Electrónico', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    descripcion = models.TextField('Descripción', blank=True)
    valor = models.DecimalField('Valor Estimado', max_digits=12, decimal_places=2, default=0)
    probabilidad = models.PositiveIntegerField('Probabilidad (%)', default=0)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='nuevo')
    tipo_negociacion = models.CharField('Tipo de Negociación', max_length=20, choices=TIPO_CHOICES, default='producto')
    
    # Campos adicionales para proyectos
    centro_costos = models.CharField('Centro de Costos', max_length=100, blank=True)
    nombre_proyecto = models.CharField('Nombre Proyecto', max_length=200, blank=True)
    orden_contrato = models.CharField('Orden o Contrato', max_length=100, blank=True)
    dias_prometidos = models.PositiveIntegerField('Promesa de Días', null=True, blank=True)
    fuente = models.CharField('Fuente', max_length=20, choices=FUENTE_CHOICES, default='web')
    fecha_creacion = models.DateTimeField('Fecha de Creación', default=timezone.now)
    fecha_cierre = models.DateField('Fecha de Cierre', null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tratos')
    notas = models.TextField('Notas', blank=True)
    
    class Meta:
        verbose_name = 'Trato'
        verbose_name_plural = 'Tratos'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.nombre} - {self.cliente} ({self.get_estado_display()})"
    
    def save(self, *args, **kwargs):
        if not self.numero_oferta:
            # Obtener el último número de oferta
            ultimo_trato = Trato.objects.order_by('-numero_oferta').first()
            if ultimo_trato and ultimo_trato.numero_oferta:
                try:
                    ultimo_numero = int(ultimo_trato.numero_oferta)
                    self.numero_oferta = str(ultimo_numero + 1).zfill(4)
                except ValueError:
                    self.numero_oferta = '0001'
            else:
                self.numero_oferta = '0001'
        
        # Si es un nuevo trato, establecer la fecha de cierre por defecto a 30 días después
        if not self.pk and not self.fecha_cierre:
            self.fecha_cierre = timezone.now().date() + timezone.timedelta(days=30)
        # Actualizar la fecha de cierre si el trato se marca como ganado o perdido
        elif self.estado in ['ganado', 'perdido', 'cancelado'] and not self.fecha_cierre:
            self.fecha_cierre = timezone.now().date()
        
        super().save(*args, **kwargs)

class Cotizacion(models.Model):
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('enviada', 'Enviada'),
        ('aceptada', 'Aceptada'),
        ('rechazada', 'Rechazada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cotizaciones')
    trato = models.ForeignKey(Trato, on_delete=models.CASCADE, related_name='cotizaciones', null=True, blank=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_envio = models.DateTimeField('Fecha de Envío', null=True, blank=True)
    monto = models.DecimalField('Monto', max_digits=12, decimal_places=2, default=0)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='borrador')
    notas = models.TextField('Notas', blank=True)

    class Meta:
        verbose_name = 'Cotización'
        verbose_name_plural = 'Cotizaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"COT-{self.id} - {self.cliente}"

class VersionCotizacion(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='versiones')
    version = models.PositiveIntegerField('Número de Versión')
    archivo = models.FileField('Archivo', upload_to='cotizaciones/versiones/')
    razon_cambio = models.TextField('Razón del Cambio')
    valor = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = 'Versión de Cotización'
        verbose_name_plural = 'Versiones de Cotización'
        ordering = ['-version']
        unique_together = ['cotizacion', 'version']

    def __str__(self):
        return f"Versión {self.version} - {self.cotizacion}"

class TareaVenta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]

    TIPO_CHOICES = [
        ('llamada', 'Llamada'),
        ('reunion', 'Reunión'),
        ('email', 'Email'),
        ('seguimiento', 'Seguimiento'),
        ('otro', 'Otro'),
    ]

    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    titulo = models.CharField('Título', max_length=200, default='Nueva Tarea')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='tareas')
    trato = models.ForeignKey(Trato, on_delete=models.CASCADE, related_name='tareas', null=True, blank=True)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='seguimiento')
    descripcion = models.TextField('Descripción')
    fecha_vencimiento = models.DateTimeField('Fecha de Vencimiento', default=timezone.now)
    fecha_ejecucion = models.DateTimeField('Fecha de Ejecución', null=True, blank=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    prioridad = models.CharField('Prioridad', max_length=20, choices=PRIORIDAD_CHOICES, default='media')
    responsable = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tareas_asignadas')
    notas = models.TextField('Notas', blank=True)
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField('Fecha de Creación', default=timezone.now)
    fecha_actualizacion = models.DateTimeField('Última Actualización', auto_now=True)

    class Meta:
        verbose_name = 'Tarea de Venta'
        verbose_name_plural = 'Tareas de Venta'
        ordering = ['fecha_vencimiento']

    def __str__(self):
        return self.titulo

    def get_estado_class(self):
        """Retorna la clase CSS correspondiente al estado de la tarea."""
        estado_classes = {
            'pendiente': 'bg-warning text-dark',
            'en_progreso': 'bg-info text-white',
            'completada': 'bg-success text-white',
            'cancelada': 'bg-secondary text-white',
        }
        return estado_classes.get(self.estado, '')

    def get_prioridad_class(self):
        """Retorna la clase CSS correspondiente a la prioridad de la tarea."""
        prioridad_classes = {
            'baja': 'bg-success text-white',
            'media': 'bg-info text-white',
            'alta': 'bg-warning text-dark',
            'urgente': 'bg-danger text-white',
        }
        return prioridad_classes.get(self.prioridad, '')

    def get_numero_oferta(self):
        """Retorna el número de oferta del trato asociado."""
        if self.trato:
            return self.trato.numero_oferta
        return "Sin oferta"

    def get_nombre_trato(self):
        """Retorna el nombre del trato asociado."""
        if self.trato:
            return self.trato.nombre or "Sin nombre"
        return "Sin trato"

    def get_nombre_cliente(self):
        """Retorna el nombre del cliente."""
        return self.cliente.nombre if self.cliente else "Sin cliente"