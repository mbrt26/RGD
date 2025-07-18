from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()

class Tecnico(models.Model):
    """Modelo para gestionar técnicos de servicios"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tecnico_profile')
    codigo_tecnico = models.CharField('Código Técnico', max_length=20, unique=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)
    especialidades = models.TextField('Especialidades', help_text='Especialidades técnicas separadas por comas', blank=True)
    activo = models.BooleanField('Activo', default=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Técnico'
        verbose_name_plural = 'Técnicos'
        ordering = ['usuario__first_name', 'usuario__last_name']
    
    def __str__(self):
        return f"{self.codigo_tecnico} - {self.usuario.get_full_name() or self.usuario.username}"
    
    @property
    def nombre_completo(self):
        return self.usuario.get_full_name() or self.usuario.username

class SolicitudServicio(models.Model):
    """Modelo para gestionar solicitudes de servicio"""
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_ejecucion', 'En Ejecución'),
        ('atrasado', 'Atrasado'),
        ('finalizado', 'Finalizado'),
    ]
    
    TIPO_SERVICIO_CHOICES = [
        ('inspeccion', 'Visita de Inspección'),
        ('correctivo', 'Mantenimiento Correctivo'),
        ('visita_servicio', 'Visita de Servicio'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    # Información básica
    numero_orden = models.CharField('Número de Orden', max_length=20, unique=True, blank=True)
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    tipo_servicio = models.CharField('Tipo de Servicio', max_length=20, choices=TIPO_SERVICIO_CHOICES)
    prioridad = models.CharField('Prioridad', max_length=10, choices=PRIORIDAD_CHOICES, default='media')
    
    # Información del cliente (integración con CRM)
    cliente_crm = models.ForeignKey('crm.Cliente', on_delete=models.CASCADE, related_name='servicios_field')
    contacto_crm = models.ForeignKey('crm.Contacto', on_delete=models.SET_NULL, null=True, blank=True, related_name='servicios_field')
    trato_origen = models.ForeignKey(
        'crm.Trato',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Trato de Origen',
        help_text='Trato del CRM que originó esta solicitud de servicio'
    )
    cotizacion_aprobada = models.ForeignKey(
        'crm.VersionCotizacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Cotización Aprobada',
        help_text='Cotización aprobada asociada al servicio'
    )
    
    # Información adicional del cliente para el servicio
    direccion_servicio = models.TextField('Dirección de Servicio', help_text='Dirección específica donde se realizará el servicio')
    centro_costo = models.CharField('Centro de Costo', max_length=100, blank=True)
    nombre_proyecto = models.CharField('Nombre del Proyecto', max_length=200, blank=True, help_text='Nombre del proyecto asociado al servicio')
    orden_contrato = models.CharField('Orden o Contrato', max_length=100, blank=True, help_text='Orden o contrato proveniente del CRM')
    dias_prometidos = models.PositiveIntegerField('Promesa de Días', null=True, blank=True, help_text='Días prometidos del trato original')
    fecha_contractual = models.DateField('Fecha Contractual', null=True, blank=True, help_text='Fecha de creación + días prometidos')
    
    # Programación
    fecha_programada = models.DateTimeField('Fecha Programada')
    duracion_estimada = models.PositiveIntegerField('Duración Estimada (minutos)', default=120)
    tecnico_asignado = models.ForeignKey(Tecnico, on_delete=models.SET_NULL, null=True, blank=True, related_name='servicios_asignados')
    
    # Equipo del proyecto
    director_proyecto = models.ForeignKey(
        'proyectos.Colaborador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='servicios_dirigidos',
        verbose_name='Director de Proyecto',
        help_text='Colaborador responsable de dirigir el proyecto'
    )
    ingeniero_residente = models.ForeignKey(
        'proyectos.Colaborador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='servicios_residencia',
        verbose_name='Ingeniero Residente',
        help_text='Colaborador responsable de la residencia del proyecto'
    )
    
    # Documentos del proyecto
    cronograma = models.FileField(
        'Cronograma',
        upload_to='servicios/cronogramas/',
        blank=True,
        null=True,
        help_text='Archivo del cronograma del proyecto'
    )
    
    # Geolocalización
    latitud = models.DecimalField('Latitud', max_digits=10, decimal_places=8, null=True, blank=True)
    longitud = models.DecimalField('Longitud', max_digits=11, decimal_places=8, null=True, blank=True)
    direccion_gps = models.TextField('Dirección GPS', blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='servicios_creados')
    observaciones_internas = models.TextField('Observaciones Internas', blank=True)
    
    class Meta:
        verbose_name = 'Solicitud de Servicio'
        verbose_name_plural = 'Solicitudes de Servicio'
        ordering = ['-fecha_programada']
    
    def __str__(self):
        return f"{self.numero_orden} - {self.cliente_crm.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.numero_orden:
            # Generar número de orden automático
            ultimo_numero = SolicitudServicio.objects.filter(
                numero_orden__startswith=f"FS{timezone.now().year}"
            ).order_by('-numero_orden').first()
            
            if ultimo_numero:
                try:
                    ultimo_num = int(ultimo_numero.numero_orden[-4:])
                    nuevo_num = ultimo_num + 1
                except:
                    nuevo_num = 1
            else:
                nuevo_num = 1
            
            self.numero_orden = f"FS{timezone.now().year}{nuevo_num:04d}"
        
        # Calcular fecha_contractual si hay dias_prometidos
        if self.dias_prometidos and self.dias_prometidos > 0:
            if not self.pk:  # Es una nueva instancia
                self.fecha_contractual = timezone.now().date() + timezone.timedelta(days=self.dias_prometidos)
            elif not self.fecha_contractual:  # Ya existe pero no tiene fecha_contractual
                # Usar fecha_creacion si ya existe
                self.fecha_contractual = self.fecha_creacion.date() + timezone.timedelta(days=self.dias_prometidos)
        
        super().save(*args, **kwargs)

class InformeTrabajo(models.Model):
    """Modelo principal para el informe de trabajo de servicios"""
    
    CAUSA_PROBLEMA_CHOICES = [
        ('vida_util', 'Vida Útil'),
        ('mal_manejo', 'Mal Manejo'),
        ('materiales', 'Materiales'),
        ('lubricacion', 'Lubricación'),
        ('ambiente', 'Ambiente'),
        ('otros', 'Otros'),
    ]
    
    TIPO_FALLA_CHOICES = [
        ('electrico', 'Eléctrico'),
        ('mecanico', 'Mecánico'),
        ('electronico', 'Electrónico'),
        ('hidraulico', 'Hidráulico'),
        ('neumatico', 'Neumático'),
        ('lubricacion', 'Lubricación'),
        ('otros', 'Otros'),
    ]
    
    DESCRIPCION_TRABAJO_CHOICES = [
        ('electrico', 'Eléctrico'),
        ('mecanico', 'Mecánico'),
        ('electronico', 'Electrónico'),
        ('neumatico', 'Neumático'),
        ('hidraulico', 'Hidráulico'),
        ('otro', 'Otro'),
    ]
    
    SATISFACCION_CHOICES = [
        ('muy_insatisfecho', 'Muy Insatisfecho'),
        ('insatisfecho', 'Insatisfecho'),
        ('satisfecho', 'Satisfecho'),
        ('muy_satisfecho', 'Muy Satisfecho'),
    ]
    
    # Relación con solicitud de servicio
    solicitud_servicio = models.OneToOneField(SolicitudServicio, on_delete=models.CASCADE, related_name='informe')
    
    # Información general (se carga desde la solicitud y CRM)
    fecha_servicio = models.DateField('Fecha de Servicio', default=timezone.now)
    
    # Control de tiempo
    hora_ingreso = models.DateTimeField('Hora de Ingreso', null=True, blank=True)
    hora_salida = models.DateTimeField('Hora de Salida', null=True, blank=True)
    tiempo_total_minutos = models.PositiveIntegerField('Tiempo Total (minutos)', null=True, blank=True)
    
    # Diagnóstico y descripción
    descripcion_problema = models.TextField('Descripción del Problema', blank=True)
    diagnostico_preliminar = models.TextField('Diagnóstico Preliminar', blank=True)
    detalle_trabajos = models.TextField('Detalle de Trabajos Realizados', blank=True)
    
    # Causa y tipo de falla (campos múltiples)
    causas_problema = models.JSONField('Causas del Problema', default=list, blank=True)
    tipos_falla = models.JSONField('Tipos de Falla', default=list, blank=True)
    descripcion_trabajo = models.JSONField('Descripción del Trabajo', default=list, blank=True, help_text='Tipo de trabajo realizado')
    
    # Firmas y responsables
    tecnico_nombre = models.CharField('Nombre del Técnico', max_length=200, blank=True)
    tecnico_cargo = models.CharField('Cargo del Técnico', max_length=100, blank=True)
    tecnico_fecha_firma = models.DateField('Fecha Firma Técnico', null=True, blank=True)
    tecnico_firma = models.ImageField('Firma del Técnico', upload_to='firmas/tecnicos/', blank=True)
    
    cliente_nombre = models.CharField('Nombre del Cliente', max_length=200, blank=True)
    cliente_cargo = models.CharField('Cargo del Cliente', max_length=100, blank=True)
    cliente_fecha_firma = models.DateField('Fecha Firma Cliente', null=True, blank=True)
    cliente_firma = models.ImageField('Firma del Cliente', upload_to='firmas/clientes/', blank=True)
    
    # Información de entrega
    entregado_por_nombre = models.CharField('Nombre de quien Entrega', max_length=200, blank=True)
    entregado_por_cargo = models.CharField('Cargo de quien Entrega', max_length=100, blank=True)
    entregado_por_fecha = models.DateField('Fecha de Entrega', null=True, blank=True)
    entregado_por_firma = models.ImageField('Firma de quien Entrega', upload_to='firmas/entrega/', blank=True)
    
    entregado_cliente_nombre = models.CharField('Nombre de quien Recibe (Cliente)', max_length=200, blank=True)
    entregado_cliente_cargo = models.CharField('Cargo de quien Recibe (Cliente)', max_length=100, blank=True)
    entregado_cliente_fecha = models.DateField('Fecha de Recepción', null=True, blank=True)
    entregado_cliente_firma = models.ImageField('Firma de quien Recibe (Cliente)', upload_to='firmas/recepcion/', blank=True)
    
    # Encuesta de satisfacción
    satisfaccion_cliente = models.CharField('Satisfacción del Cliente', max_length=20, choices=SATISFACCION_CHOICES, blank=True)
    observaciones_encuesta = models.TextField('Observaciones de la Encuesta', blank=True, help_text='Comentarios adicionales del cliente sobre el servicio')
    
    # Observaciones finales
    recomendaciones = models.TextField('Recomendaciones y Observaciones', blank=True)
    observaciones_adicionales = models.TextField('Observaciones Adicionales', blank=True)
    
    # Geolocalización del servicio
    latitud_servicio = models.DecimalField('Latitud del Servicio', max_digits=10, decimal_places=8, null=True, blank=True)
    longitud_servicio = models.DecimalField('Longitud del Servicio', max_digits=11, decimal_places=8, null=True, blank=True)
    ubicacion_verificada = models.BooleanField('Ubicación Verificada', default=False)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    completado = models.BooleanField('Completado', default=False)
    
    class Meta:
        verbose_name = 'Informe de Trabajo'
        verbose_name_plural = 'Informes de Trabajo'
        ordering = ['-fecha_servicio']
    
    def __str__(self):
        return f"Informe {self.solicitud_servicio.numero_orden} - {self.solicitud_servicio.cliente_crm.nombre}"
    
    def save(self, *args, **kwargs):
        # Calcular tiempo total automáticamente
        if self.hora_ingreso and self.hora_salida:
            delta = self.hora_salida - self.hora_ingreso
            self.tiempo_total_minutos = int(delta.total_seconds() / 60)
        
        # Marcar como completado si tiene firmas
        if self.tecnico_firma and self.cliente_firma:
            self.completado = True
            if self.solicitud_servicio.estado != 'ejecutada':
                self.solicitud_servicio.estado = 'ejecutada'
                self.solicitud_servicio.save()
        
        super().save(*args, **kwargs)
    
    @property
    def tiempo_total_horas(self):
        if self.tiempo_total_minutos:
            horas = self.tiempo_total_minutos // 60
            minutos = self.tiempo_total_minutos % 60
            return f"{horas}h {minutos}m"
        return "0h 0m"

class MaterialRequerido(models.Model):
    """Modelo para materiales requeridos en visitas de inspección"""
    
    informe = models.ForeignKey(InformeTrabajo, on_delete=models.CASCADE, related_name='materiales_requeridos')
    descripcion = models.CharField('Descripción', max_length=200)
    marca = models.CharField('Marca', max_length=100, blank=True)
    referencia = models.CharField('Referencia', max_length=100, blank=True)
    unidad_medida = models.CharField('Unidad de Medida', max_length=50, default='Unidad')
    cantidad = models.DecimalField('Cantidad', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Material Requerido'
        verbose_name_plural = 'Materiales Requeridos'
        ordering = ['descripcion']
    
    def __str__(self):
        return f"{self.descripcion} - {self.cantidad} {self.unidad_medida}"

class MaterialConsumible(models.Model):
    """Modelo para materiales y consumibles utilizados en el servicio"""
    
    SUMINISTRADO_POR_CHOICES = [
        ('cliente', 'Cliente'),
        ('empresa', 'Empresa'),
    ]
    
    informe = models.ForeignKey(InformeTrabajo, on_delete=models.CASCADE, related_name='materiales')
    descripcion = models.CharField('Descripción', max_length=200)
    marca = models.CharField('Marca', max_length=100, blank=True)
    referencia = models.CharField('Referencia', max_length=100, blank=True)
    unidad_medida = models.CharField('Unidad de Medida', max_length=50, default='Unidad')
    cantidad = models.DecimalField('Cantidad', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    suministrado_por = models.CharField('Suministrado por', max_length=20, choices=SUMINISTRADO_POR_CHOICES)
    costo_unitario = models.DecimalField('Costo Unitario', max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Material/Consumible'
        verbose_name_plural = 'Materiales/Consumibles'
        ordering = ['descripcion']
    
    def __str__(self):
        return f"{self.descripcion} - {self.cantidad} {self.unidad_medida}"
    
    @property
    def costo_total(self):
        return self.cantidad * self.costo_unitario

class AdjuntoInforme(models.Model):
    """Modelo para adjuntos de informes (imágenes y archivos)"""
    
    TIPO_ADJUNTO_CHOICES = [
        ('imagen', 'Imagen'),
        ('documento', 'Documento'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('otro', 'Otro'),
    ]
    
    informe = models.ForeignKey(InformeTrabajo, on_delete=models.CASCADE, related_name='adjuntos')
    archivo = models.FileField('Archivo', upload_to='informes/adjuntos/%Y/%m/')
    nombre_original = models.CharField('Nombre Original', max_length=255)
    tipo_adjunto = models.CharField('Tipo de Adjunto', max_length=20, choices=TIPO_ADJUNTO_CHOICES)
    descripcion = models.CharField('Descripción', max_length=500, blank=True, help_text='Descripción opcional del adjunto')
    tamaño_archivo = models.PositiveIntegerField('Tamaño (bytes)', null=True, blank=True)
    fecha_creacion = models.DateTimeField('Fecha de Subida', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Adjunto de Informe'
        verbose_name_plural = 'Adjuntos de Informe'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.informe.solicitud_servicio.numero_orden} - {self.nombre_original}"
    
    @property
    def tamaño_legible(self):
        """Convierte el tamaño en bytes a formato legible"""
        if not self.tamaño_archivo:
            return "Desconocido"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamaño_archivo < 1024.0:
                return f"{self.tamaño_archivo:.1f} {unit}"
            self.tamaño_archivo /= 1024.0
        return f"{self.tamaño_archivo:.1f} TB"
    
    @property
    def es_imagen(self):
        """Verifica si el adjunto es una imagen"""
        extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp']
        return any(self.archivo.name.lower().endswith(ext) for ext in extensiones_imagen)
    
    @property
    def icono_tipo(self):
        """Retorna el icono FontAwesome según el tipo de archivo"""
        if self.es_imagen:
            return 'fas fa-image'
        elif self.archivo.name.lower().endswith(('.pdf',)):
            return 'fas fa-file-pdf'
        elif self.archivo.name.lower().endswith(('.doc', '.docx')):
            return 'fas fa-file-word'
        elif self.archivo.name.lower().endswith(('.xls', '.xlsx')):
            return 'fas fa-file-excel'
        elif self.archivo.name.lower().endswith(('.mp4', '.avi', '.mov')):
            return 'fas fa-file-video'
        elif self.archivo.name.lower().endswith(('.mp3', '.wav', '.m4a')):
            return 'fas fa-file-audio'
        else:
            return 'fas fa-file'

class UbicacionTecnico(models.Model):
    """Modelo para tracking de ubicación de técnicos"""
    tecnico = models.ForeignKey(Tecnico, on_delete=models.CASCADE, related_name='ubicaciones')
    solicitud_servicio = models.ForeignKey(SolicitudServicio, on_delete=models.CASCADE, related_name='ubicaciones_tecnico', null=True, blank=True)
    latitud = models.DecimalField('Latitud', max_digits=10, decimal_places=8)
    longitud = models.DecimalField('Longitud', max_digits=11, decimal_places=8)
    precision = models.PositiveIntegerField('Precisión (metros)', null=True, blank=True)
    timestamp = models.DateTimeField('Timestamp', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ubicación del Técnico'
        verbose_name_plural = 'Ubicaciones del Técnico'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.tecnico.nombre_completo} - {self.timestamp}"
