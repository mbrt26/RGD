from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()

def fecha_actual():
    """Retorna la fecha actual sin hora"""
    return timezone.now().date()

class ConfiguracionOferta(models.Model):
    """
    Modelo singleton para configurar el sistema de numeración de ofertas.
    """
    siguiente_numero = models.PositiveIntegerField(
        'Siguiente Número de Oferta',
        default=1,
        help_text='El próximo número que se asignará a una nueva oferta'
    )
    creado_en = models.DateTimeField('Creado en', default=timezone.now)
    actualizado_en = models.DateTimeField('Actualizado en', auto_now=True)
    actualizado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Actualizado por'
    )

    class Meta:
        verbose_name = 'Configuración de Oferta'
        verbose_name_plural = 'Configuración de Ofertas'

    def __str__(self):
        return f"Siguiente número de oferta: {self.siguiente_numero:04d}"

    def clean(self):
        if self.siguiente_numero < 1:
            raise ValidationError("El siguiente número debe ser mayor a 0")

    def save(self, *args, **kwargs):
        self.clean()
        # Asegurar que solo exista una instancia (patrón singleton)
        if not self.pk and ConfiguracionOferta.objects.exists():
            raise ValidationError("Solo puede existir una configuración de oferta")
        super().save(*args, **kwargs)

    @classmethod
    def obtener_configuracion(cls):
        """
        Obtiene o crea la configuración de oferta (singleton).
        """
        config, created = cls.objects.get_or_create(defaults={'siguiente_numero': 1})
        return config

    @classmethod
    def obtener_siguiente_numero(cls):
        """
        Obtiene el siguiente número de oferta y lo incrementa automáticamente.
        """
        config = cls.obtener_configuracion()
        numero_actual = config.siguiente_numero
        config.siguiente_numero += 1
        config.save()
        return numero_actual

class Cliente(models.Model):
    nombre = models.CharField('Nombre', max_length=200)
    SECTOR_ACTIVIDAD_CHOICES = [
        ('alimentos', 'Alimentos'),
        ('comercio', 'Comercio'),
        ('construccion', 'Construcción'),
        ('cosmeticos', 'Cosméticos'),
        ('educacion', 'Educación'),
        ('farmaceutico', 'Farmacéutico'),
        ('fitoterapeuta', 'Fitoterapeuta'),
        ('industrial', 'Industrial'),
        ('infraestructura', 'Infraestructura'),
        ('salud', 'Salud'),
        ('servicios_financieros', 'Servicios Financieros'),
    ]
    
    sector_actividad = models.CharField('Sector de Actividad', max_length=100, choices=SECTOR_ACTIVIDAD_CHOICES, blank=True)
    nit = models.CharField('NIT', max_length=50, blank=True)
    correo = models.EmailField('Correo Electrónico', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    direccion = models.CharField('Dirección', max_length=300, blank=True)
    notas = models.TextField('Notas', blank=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', default=timezone.now)
    direccion_linea1 = models.CharField('Dirección Línea 1', max_length=200, blank=True)
    direccion_linea2 = models.CharField('Dirección Línea 2', max_length=200, blank=True)
    ciudad = models.CharField('Ciudad', max_length=100, blank=True)
    estado = models.CharField('Estado/Departamento', max_length=100, blank=True)
    rut = models.FileField('RUT', upload_to='clientes/rut/', blank=True)
    cedula = models.FileField('Cédula de Ciudadanía', upload_to='clientes/cedula/', blank=True)
    ef = models.FileField('Estados Financieros', upload_to='clientes/ef/', blank=True)
    camara = models.FileField('Cámara de Comercio', upload_to='clientes/camara/', blank=True)
    formulario_vinculacion = models.FileField('Formulario de Vinculación', upload_to='clientes/vinculacion/', blank=True)

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
        ('revision_tecnica', 'Revisión Técnica'),
        ('elaboracion_oferta', 'Elaboración de oferta'),
        ('envio_negociacion', 'Envío de Oferta - Negociación'),
        ('formalizacion', 'Formalización'),
        ('ganado', 'Ganado'),
        ('perdido', 'Perdido'),
        ('sin_informacion', 'Sin información'),
    ]
    
    FUENTE_CHOICES = [
        ('visita', 'Visita'),
        ('informe_tecnico', 'Informe Técnico'),
        ('email', 'Email'),
        ('telefono', 'Teléfono'),
        ('whatsapp', 'Whatsapp'),
        ('otro', 'Otro'),
    ]

    TIPO_CHOICES = [
        ('contrato', 'Contrato'),
        ('control', 'Control'),
        ('diseno', 'Diseño'),
        ('filtros', 'Filtros'),
        ('mantenimiento', 'Mantenimiento'),
        ('servicios', 'Servicios'),
    ]
    
    numero_oferta = models.CharField('# Oferta', max_length=10, unique=True, blank=True)
    nombre = models.CharField('Descripción', max_length=200, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, verbose_name='Cliente', on_delete=models.CASCADE, related_name='tratos')
    contacto = models.ForeignKey(Contacto, verbose_name='Contacto', on_delete=models.SET_NULL, null=True, blank=True, related_name='tratos')
    correo = models.EmailField('Correo Electrónico', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    descripcion = models.TextField('Descripción', blank=True)
    valor = models.DecimalField('Valor Estimado', max_digits=12, decimal_places=2, default=0)
    probabilidad = models.PositiveIntegerField('Probabilidad (%)', default=0)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='revision_tecnica')
    tipo_negociacion = models.CharField('Tipo de Negociación', max_length=20, choices=TIPO_CHOICES, default='contrato')
    
    # Campos adicionales para proyectos
    centro_costos = models.CharField('Centro de Costos', max_length=100, blank=True)
    nombre_proyecto = models.CharField('Nombre Proyecto', max_length=200, blank=True)
    orden_contrato = models.CharField('Orden o Contrato', max_length=100, blank=True)
    dias_prometidos = models.PositiveIntegerField('Promesa de Días', null=True, blank=True)
    fuente = models.CharField('Fuente', max_length=20, choices=FUENTE_CHOICES, default='visita')
    fecha_creacion = models.DateField('Fecha de Creación', default=fecha_actual)
    fecha_cierre = models.DateField('Fecha de Cierre', null=True, blank=True)
    fecha_envio_cotizacion = models.DateField('Fecha de Envío de Cotización', null=True, blank=True)
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tratos')
    notas = models.TextField('Notas', blank=True)
    
    class Meta:
        verbose_name = 'Trato'
        verbose_name_plural = 'Tratos'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        if self.descripcion:
            # Truncar la descripción para que no sea demasiado larga
            descripcion_corta = self.descripcion[:80] + "..." if len(self.descripcion) > 80 else self.descripcion
            return f"#{self.numero_oferta} - {descripcion_corta}"
        elif self.nombre:
            # Si no hay descripción, usar el nombre
            nombre_corto = self.nombre[:80] + "..." if len(self.nombre) > 80 else self.nombre
            return f"#{self.numero_oferta} - {nombre_corto}"
        return f"#{self.numero_oferta} - {self.cliente}"
    
    def save(self, *args, **kwargs):
        if not self.numero_oferta:
            # Usar la configuración centralizada para obtener el siguiente número
            numero = ConfiguracionOferta.obtener_siguiente_numero()
            self.numero_oferta = str(numero).zfill(4)
        else:
            # Validate manual offer number doesn't conflict with existing ones
            existing_trato = Trato.objects.filter(numero_oferta=self.numero_oferta).exclude(pk=self.pk).first()
            if existing_trato:
                from django.core.exceptions import ValidationError
                raise ValidationError(f'El número de oferta {self.numero_oferta} ya existe. Use un número diferente o deje el campo vacío para asignar automáticamente.')
        
        # Si es un nuevo trato, establecer la fecha de cierre por defecto a 30 días después
        if not self.pk and not self.fecha_cierre:
            self.fecha_cierre = timezone.now().date() + timezone.timedelta(days=30)
        # Actualizar la fecha de cierre si el trato se marca como ganado o perdido
        elif self.estado in ['ganado', 'perdido', 'cancelado'] and not self.fecha_cierre:
            self.fecha_cierre = timezone.now().date()
        
        super().save(*args, **kwargs)
    
    def is_fecha_cierre_vencida(self):
        """Retorna True si la fecha de cierre está vencida y el trato no está ganado o perdido."""
        if not self.fecha_cierre:
            return False
        return (self.fecha_cierre < timezone.now().date() and 
                self.estado not in ['ganado', 'perdido'])
    
    def get_fecha_cierre_class(self):
        """Retorna la clase CSS para la fecha de cierre según si está vencida."""
        if self.is_fecha_cierre_vencida():
            return 'text-danger fw-bold'
        return ''

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
        if self.cotizacion.trato and self.cotizacion.trato.numero_oferta:
            return f"#{self.cotizacion.trato.numero_oferta} - V{self.version} - {self.cotizacion.cliente.nombre}"
        return f"COT-{self.cotizacion.id} - V{self.version} - {self.cotizacion.cliente.nombre}"

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
        ('modificacion', 'Modificación'),
        ('otro', 'Otro'),
    ]


    titulo = models.CharField('Título', max_length=200, default='Nueva Tarea')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='tareas')
    trato = models.ForeignKey(Trato, on_delete=models.CASCADE, related_name='tareas', null=True, blank=True)
    tipo = models.CharField('Tipo', max_length=20, choices=TIPO_CHOICES, default='seguimiento')
    descripcion = models.TextField('Descripción')
    fecha_vencimiento = models.DateField('Fecha de Vencimiento', default=fecha_actual)
    fecha_ejecucion = models.DateTimeField('Fecha de Ejecución', null=True, blank=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='pendiente')
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

    def is_vencida(self):
        """Retorna True si la tarea está vencida."""
        if not self.fecha_vencimiento:
            return False
        return self.fecha_vencimiento < timezone.now().date() and self.estado not in ['completada', 'cancelada']
    
    def get_fecha_class(self):
        """Retorna la clase CSS para la fecha según si está vencida."""
        if self.is_vencida():
            return 'text-danger fw-bold'
        return ''

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


class Lead(models.Model):
    ESTADO_CHOICES = [
        ('nuevo', 'Nuevo'),
        ('contactado', 'Contactado'),
        ('calificado', 'Calificado'),
        ('propuesta', 'Propuesta Enviada'),
        ('negociacion', 'En Negociación'),
        ('convertido', 'Convertido'),
        ('perdido', 'Perdido'),
        ('descalificado', 'Descalificado'),
    ]
    
    FUENTE_CHOICES = [
        ('web', 'Página Web'),
        ('referido', 'Referido'),
        ('publicidad', 'Publicidad'),
        ('evento', 'Evento'),
        ('llamada_fria', 'Llamada Fría'),
        ('email', 'Email Marketing'),
        ('redes_sociales', 'Redes Sociales'),
        ('otro', 'Otro'),
    ]
    
    INTERES_CHOICES = [
        ('bajo', 'Bajo'),
        ('medio', 'Medio'),
        ('alto', 'Alto'),
        ('muy_alto', 'Muy Alto'),
    ]
    
    # Información básica
    nombre = models.CharField('Nombre', max_length=200)
    empresa = models.CharField('Empresa', max_length=200, blank=True)
    cargo = models.CharField('Cargo', max_length=100, blank=True)
    correo = models.EmailField('Correo Electrónico')
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    sector_actividad = models.CharField('Sector de Actividad', max_length=100, choices=Cliente.SECTOR_ACTIVIDAD_CHOICES, blank=True)
    
    # Información de seguimiento
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='nuevo')
    fuente = models.CharField('Fuente', max_length=20, choices=FUENTE_CHOICES, default='web')
    nivel_interes = models.CharField('Nivel de Interés', max_length=20, choices=INTERES_CHOICES, default='medio')
    
    # Información adicional
    necesidad = models.TextField('Necesidad/Problema', blank=True)
    presupuesto_estimado = models.DecimalField('Presupuesto Estimado', max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_contacto_inicial = models.DateField('Fecha de Contacto Inicial', default=fecha_actual)
    fecha_ultima_interaccion = models.DateField('Última Interacción', default=fecha_actual)
    
    # Asignación y seguimiento
    responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads_asignados')
    convertido_a_cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads_origen')
    convertido_a_trato = models.ForeignKey(Trato, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads_origen')
    
    # Notas y observaciones
    notas = models.TextField('Notas', blank=True)
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Última Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='leads_creados')
    
    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        empresa_info = f" ({self.empresa})" if self.empresa else ""
        return f"{self.nombre}{empresa_info}"
    
    def get_estado_class(self):
        """Retorna la clase CSS correspondiente al estado del lead."""
        estado_classes = {
            'nuevo': 'bg-primary text-white',
            'contactado': 'bg-info text-white',
            'calificado': 'bg-warning text-dark',
            'propuesta': 'bg-secondary text-white',
            'negociacion': 'bg-warning text-dark',
            'convertido': 'bg-success text-white',
            'perdido': 'bg-danger text-white',
            'descalificado': 'bg-dark text-white',
        }
        return estado_classes.get(self.estado, 'bg-secondary text-white')
    
    def get_interes_class(self):
        """Retorna la clase CSS correspondiente al nivel de interés."""
        interes_classes = {
            'bajo': 'bg-light text-dark',
            'medio': 'bg-info text-white',
            'alto': 'bg-warning text-dark',
            'muy_alto': 'bg-danger text-white',
        }
        return interes_classes.get(self.nivel_interes, 'bg-secondary text-white')
    
    @property
    def esta_convertido(self):
        """Retorna True si el lead ya fue convertido."""
        return self.convertido_a_cliente is not None or self.convertido_a_trato is not None
    
    def puede_convertir(self):
        """Retorna True si el lead puede ser convertido."""
        return not self.esta_convertido and self.estado not in ['perdido', 'descalificado']