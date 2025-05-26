from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import json
import os

# Use string reference to avoid circular import
# Trato model will be referenced as 'crm.Trato'


def validate_fecha_futura(value):
    if value < timezone.now().date():
        raise ValidationError('La fecha no puede ser en el pasado.')


def validate_porcentaje(value):
    if value < 0 or value > 100:
        raise ValidationError('El porcentaje debe estar entre 0 y 100')

class Colaborador(models.Model):
    nombre = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    email = models.EmailField('Correo electrónico', blank=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Colaborador'
        verbose_name_plural = 'Colaboradores'

    def __str__(self):
        return f"{self.nombre} - {self.cargo}"

class Proyecto(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('en_revision', 'En Revisión'),
        ('completado', 'Completado'),
        ('suspendido', 'Suspendido'),
        ('cancelado', 'Cancelado')
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critico', 'Crítico')
    ]
    
    # Información básica
    trato = models.OneToOneField('crm.Trato', on_delete=models.SET_NULL, null=True, blank=True, related_name='proyecto')
    cliente = models.CharField(max_length=200)
    centro_costos = models.CharField('Centro de Costos', max_length=100)
    nombre_proyecto = models.CharField('Nombre Proyecto', max_length=200)
    orden_contrato = models.CharField('Orden o Contrato', max_length=100, unique=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True, default=timezone.now)
    
    # Fechas y plazos
    fecha_inicio = models.DateField('Fecha Inicio', validators=[validate_fecha_futura])
    fecha_fin = models.DateField('Fecha Fin')
    fecha_fin_real = models.DateField('Fecha de Finalización Real', null=True, blank=True)
    dias_prometidos = models.PositiveIntegerField('Promesa de Días')
    
    # Seguimiento
    avance = models.DecimalField(
        '% Avance', 
        max_digits=5, 
        decimal_places=2, 
        validators=[validate_porcentaje],
        default=0
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente'
    )
    prioridad = models.CharField(
        max_length=10, 
        choices=PRIORIDAD_CHOICES, 
        default='media'
    )
    
    # Presupuesto
    presupuesto = models.DecimalField(
        'Presupuesto Total', 
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    gasto_real = models.DecimalField(
        'Gasto Real', 
        max_digits=12, 
        decimal_places=2,
        default=0
    )
    
    # Documentos y archivos
    observaciones = models.TextField(blank=True)
    adjunto = models.FileField(upload_to='proyectos/adjuntos/', blank=True)
    
    # Auditoría
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, 
        null=True,
        related_name='proyectos_creados'
    )
    
    class Meta:
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
        ordering = ['-fecha_creacion']
        permissions = [
            ('can_view_all_projects', 'Puede ver todos los proyectos'),
            ('can_export_projects', 'Puede exportar proyectos'),
        ]
    
    def clean(self):
        from decimal import Decimal
        
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError('La fecha de inicio no puede ser posterior a la fecha de fin.')
        
        # Convertir el factor 1.1 a Decimal para la comparación
        if self.gasto_real and self.presupuesto:
            limite_presupuesto = self.presupuesto * Decimal('1.1')  # Permite un 10% de sobrecosto
            if self.gasto_real > limite_presupuesto:
                raise ValidationError('El gasto real supera el presupuesto por más del 10% permitido.')
    
    def save(self, *args, **kwargs):
        self.clean()
        
        # Si el proyecto se marca como completado, establecer la fecha de finalización real
        if self.estado == 'completado' and not self.fecha_fin_real:
            self.fecha_fin_real = timezone.now().date()
            
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.nombre_proyecto} - {self.cliente}"
        
    @property
    def dias_restantes(self):
        """Calcula los días restantes para la fecha de fin del proyecto."""
        if self.estado == 'completado' and self.fecha_fin_real:
            return 0
        hoy = timezone.now().date()
        return (self.fecha_fin - hoy).days if self.fecha_fin > hoy else 0
        
    @property
    def sobrecosto(self):
        """Calcula el porcentaje de sobrecosto del proyecto."""
        if self.presupuesto == 0:
            return 0
        return ((self.gasto_real - self.presupuesto) / self.presupuesto) * 100

    # Documentos de Legalización
    cotizacion = models.FileField('1.0) Oferta', upload_to='proyectos/legalizacion/', blank=True)
    orden_compra = models.FileField('1.1) Orden de Compra', upload_to='proyectos/legalizacion/', blank=True)
    contrato = models.FileField('1.2) Contrato', upload_to='proyectos/legalizacion/', blank=True)
    polizas = models.FileField('1.3) Pólizas', upload_to='proyectos/legalizacion/', blank=True)
    correo_formalizacion = models.TextField('1.4) Correo o Formalización', blank=True)
    acta_socializacion = models.FileField('1.5) Acta de Socialización', upload_to='proyectos/legalizacion/', blank=True)

    # Documentos de Planeación
    cronograma = models.FileField('2.0) Cronograma', upload_to='proyectos/planeacion/', blank=True)
    acta_inicio = models.FileField('2.1) Acta de Inicio', upload_to='proyectos/planeacion/', blank=True)
    inspeccion_hseq = models.FileField('2.2) Inspección Condiciones HSEQ', upload_to='proyectos/planeacion/', blank=True)
    inspeccion_propiedad_cliente = models.FileField('2.3) Inspección Propiedad del Cliente', upload_to='proyectos/planeacion/', blank=True)

    # Documentos de Ejecución
    control_cambios = models.FileField('3.0) Control de Cambios', upload_to='proyectos/ejecucion/', blank=True)
    acta_avance_obras = models.FileField('3.1) Acta de avance de obras', upload_to='proyectos/ejecucion/', blank=True)
    informes_trabajo = models.FileField('3.2) Informes de Trabajo', upload_to='proyectos/ejecucion/', blank=True)
    informes_control = models.FileField('3.2.1) Informes de Control', upload_to='proyectos/ejecucion/', blank=True)
    informes_mantenimiento = models.FileField('3.2.2) Informes de Mantenimiento', upload_to='proyectos/ejecucion/', blank=True)
    informes_externos = models.FileField('3.3) Informes Externos', upload_to='proyectos/ejecucion/', blank=True)
    informe_tecnico = models.FileField('3.4) Informe Técnico', upload_to='proyectos/ejecucion/', blank=True)
    comunicaciones_cliente = models.FileField('3.5) Correos - Comunicaciones con el Cliente', upload_to='proyectos/ejecucion/', blank=True)
    ficha_diseno = models.FileField('3.6) Ficha de Diseño', upload_to='proyectos/ejecucion/', blank=True)

    # Documentos de Entrega Administrativa
    remision = models.FileField('4.0) Remisión', upload_to='proyectos/entrega/', blank=True)
    factura = models.FileField('4.1) Factura', upload_to='proyectos/entrega/', blank=True)
    acta_entrega = models.FileField('4.2) Acta de Entrega', upload_to='proyectos/entrega/', blank=True)
    acta_liquidacion = models.FileField('4.3) Acta de Liquidación Final', upload_to='proyectos/entrega/', blank=True)
    acta_cierre = models.FileField('4.4) Acta de Cierre', upload_to='proyectos/entrega/', blank=True)
    archivos_generales = models.FileField(upload_to='proyectos/general/', blank=True)

    def __str__(self):
        return self.nombre_proyecto

class Actividad(models.Model):
    ESTADOS_CHOICES = [
        ('no_iniciado', 'No Iniciado'),
        ('en_proceso', 'En Proceso'),
        ('finalizado', 'Finalizado')
    ]

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='actividades')
    actividad = models.CharField(max_length=200)
    inicio = models.DateField()
    fin = models.DateField()
    duracion = models.DecimalField(max_digits=5, decimal_places=0)
    avance = models.DecimalField('% Avance', max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='no_iniciado')
    predecesoras = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    adjuntos = models.FileField(upload_to='actividades/adjuntos/', blank=True)

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        return f"{self.actividad} - {self.proyecto}"

class Recurso(models.Model):
    material_herramienta = models.CharField('Material o Herramienta', max_length=200)
    unidad = models.CharField(max_length=50)
    proyecto = models.CharField(max_length=200)
    actividad = models.CharField(max_length=200)

    def __str__(self):
        return self.material_herramienta

class Bitacora(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='bitacoras')
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='bitacoras')
    subactividad = models.CharField(max_length=200)
    responsable = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name='bitacoras_responsable')
    equipo = models.ManyToManyField(Colaborador, related_name='bitacoras_equipo')
    descripcion = models.TextField('Descripción de la Actividad')
    duracion_horas = models.DecimalField('Duración (Horas)', max_digits=5, decimal_places=2)
    observaciones = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='bitacora/imagenes/', blank=True)
    archivo = models.FileField(upload_to='bitacora/archivos/', blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.proyecto} - {self.actividad} - {self.fecha_registro}"

class BitacoraRecurso(models.Model):
    bitacora = models.ForeignKey(Bitacora, on_delete=models.CASCADE, related_name='recursos')
    recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.recurso} - {self.cantidad}"

class EntregaDocumental(models.Model):
    ESTADOS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_revision', 'En Revisión'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('entregado', 'Entregado')
    ]
    
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='entregables')
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    archivo = models.FileField(upload_to='entregables/', blank=True)
    fecha_entrega = models.DateField()
    estado = models.CharField(max_length=50, choices=ESTADOS_CHOICES, default='pendiente')

    def __str__(self):
        return f"{self.nombre} - {self.proyecto}"

class EntregableProyecto(models.Model):
    """Modelo para gestionar los entregables específicos de cada proyecto"""
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
        ('no_aplica', 'No Aplica')
    ]
    
    PHASE_CHOICES = [
        ('Definición', 'Definición'),
        ('Planeación', 'Planeación'),
        ('Ejecución', 'Ejecución'),
        ('Entrega', 'Entrega')
    ]
    
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='entregables_proyecto')
    codigo = models.CharField(max_length=20)
    nombre = models.CharField(max_length=300)
    fase = models.CharField(max_length=50, choices=PHASE_CHOICES)
    creador = models.CharField(max_length=200)
    consolidador = models.CharField(max_length=200)
    medio = models.CharField(max_length=50)
    dossier_cliente = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones = models.TextField(blank=True)
    obligatorio = models.BooleanField(default=True)
    seleccionado = models.BooleanField(default=False)
    archivo = models.FileField(upload_to='entregables/', blank=True, null=True)
    fecha_entrega = models.DateField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Entregable del Proyecto'
        verbose_name_plural = 'Entregables del Proyecto'
        unique_together = ['proyecto', 'codigo']
        ordering = ['codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre} ({self.proyecto.nombre_proyecto})"
    
    @classmethod
    def cargar_entregables_desde_json(cls, proyecto):
        """Carga los entregables desde el archivo JSON para un proyecto específico"""
        json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'proyectos', 'Entregables.json')
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                entregables_data = json.load(f)
            
            for item in entregables_data:
                # Determinar si es obligatorio según las reglas de negocio
                obligatorio = cls._determinar_obligatorio(item['phase'])
                
                # Solo crear si no existe ya
                entregable, created = cls.objects.get_or_create(
                    proyecto=proyecto,
                    codigo=item['code'],
                    defaults={
                        'nombre': item['name'],
                        'fase': item['phase'],
                        'creador': item['support']['creator'],
                        'consolidador': item['support']['consolidator'],
                        'medio': item['medium'],
                        'dossier_cliente': item['client_dossier'],
                        'observaciones': item['observations'],
                        'obligatorio': obligatorio,
                        'seleccionado': obligatorio,  # Por defecto seleccionados los obligatorios
                    }
                )
                
            return True
        except Exception as e:
            print(f"Error al cargar entregables: {e}")
            return False
    
    @staticmethod
    def _determinar_obligatorio(fase):
        """Determina si un entregable es obligatorio según las reglas de negocio"""
        reglas_obligatorios = {
            'Definición': True,  # Legalización - todos obligatorios
            'Planeación': True,  # Planeación - todos obligatorios
            'Ejecución': False,  # Ejecución - seleccionar por usuario
            'Entrega': False     # Entrega administrativa - seleccionar por usuario
        }
        return reglas_obligatorios.get(fase, False)
