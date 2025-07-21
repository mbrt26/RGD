from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import json
import os

# Use string reference to avoid circular import
# Trato model will be referenced as 'crm.Trato'


def validate_fecha_futura_solo_nuevos(value):
    """Validador que solo aplica a proyectos nuevos, no a ediciones"""
    # Este validador será removido dinámicamente en el form de edición
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
        ('en_ejecucion', 'En Ejecución'),
        ('finalizado', 'Finalizado')
    ]
    
    
    # Información básica
    trato = models.OneToOneField('crm.Trato', on_delete=models.SET_NULL, null=True, blank=True, related_name='proyecto')
    cliente = models.CharField(max_length=200)
    centro_costos = models.CharField('Centro de Costos', max_length=100)
    nombre_proyecto = models.CharField('Nombre Proyecto', max_length=200)
    orden_contrato = models.CharField('Orden o Contrato', max_length=100, unique=True)
    
    # Fechas y plazos
    fecha_inicio = models.DateField('Fecha Inicio', validators=[validate_fecha_futura_solo_nuevos])
    fecha_fin = models.DateField('Fecha Fin')
    fecha_fin_real = models.DateField('Fecha de Finalización Real', null=True, blank=True)
    dias_prometidos = models.PositiveIntegerField('Promesa de Días')
    
    # Seguimiento
    avance = models.DecimalField(
        '% Avance Real', 
        max_digits=5, 
        decimal_places=2, 
        validators=[validate_porcentaje],
        default=0
    )
    avance_planeado = models.DecimalField(
        '% Avance Planeado', 
        max_digits=5, 
        decimal_places=2, 
        validators=[validate_porcentaje],
        default=0,
        help_text='Porcentaje de avance esperado según el cronograma'
    )
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente'
    )
    
    # Presupuesto y Control Financiero
    presupuesto = models.DecimalField(
        'Presupuesto Total', 
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='Presupuesto total aprobado para el proyecto'
    )
    presupuesto_gasto = models.DecimalField(
        'Presupuesto de Gasto Operativo',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='Presupuesto específico para gastos operativos del proyecto'
    )
    gasto_real = models.DecimalField(
        'Gasto Real Acumulado', 
        max_digits=12, 
        decimal_places=2,
        default=0,
        help_text='Total de gastos reales ejecutados'
    )
    gasto_operativo_real = models.DecimalField(
        'Gasto Operativo Real',
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Gastos operativos reales (materiales, mano de obra, etc.)'
    )
    reserva_contingencia = models.DecimalField(
        'Reserva de Contingencia',
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Reserva para imprevistos (% del presupuesto total)'
    )
    fecha_ultimo_gasto = models.DateField(
        'Fecha Último Gasto Registrado',
        null=True,
        blank=True,
        help_text='Fecha del último gasto registrado en el proyecto'
    )
    
    # Documentos y archivos
    observaciones = models.TextField(blank=True)
    adjunto = models.FileField(upload_to='proyectos/adjuntos/', blank=True)
    cotizacion_aprobada = models.ForeignKey(
        'crm.VersionCotizacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Cotización Aprobada',
        help_text='Cotización aprobada asociada al proyecto'
    )
    
    # Equipo del proyecto
    director_proyecto = models.ForeignKey(
        'Colaborador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyectos_dirigidos',
        verbose_name='Director de Proyecto',
        help_text='Colaborador responsable de dirigir el proyecto'
    )
    ingeniero_residente = models.ForeignKey(
        'Colaborador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyectos_residencia',
        verbose_name='Ingeniero Residente',
        help_text='Colaborador responsable de la residencia del proyecto'
    )
    
    # Auditoría
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
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
        
        # Si el proyecto se marca como finalizado, establecer la fecha de finalización real
        if self.estado == 'finalizado' and not self.fecha_fin_real:
            self.fecha_fin_real = timezone.now().date()
            
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.nombre_proyecto} - {self.cliente}"
        
    @property
    def dias_restantes(self):
        """Calcula los días restantes para la fecha de fin del proyecto."""
        if self.estado == 'finalizado' and self.fecha_fin_real:
            return 0
        hoy = timezone.now().date()
        return (self.fecha_fin - hoy).days if self.fecha_fin > hoy else 0
    
    @property
    def dias_retraso(self):
        """Calcula los días de retraso del proyecto."""
        if self.estado == 'finalizado':
            # Para proyectos finalizados, comparar fecha real vs fecha planificada
            if self.fecha_fin_real and self.fecha_fin_real > self.fecha_fin:
                return (self.fecha_fin_real - self.fecha_fin).days
            return 0
        else:
            # Para proyectos activos, comparar fecha actual vs fecha planificada
            hoy = timezone.now().date()
            if hoy > self.fecha_fin:
                return (hoy - self.fecha_fin).days
            return 0
    
    @property
    def esta_atrasado(self):
        """Determina si el proyecto está atrasado."""
        return self.dias_retraso > 0
    
    @property
    def nivel_retraso(self):
        """Determina el nivel de retraso del proyecto."""
        dias = self.dias_retraso
        if dias == 0:
            return 'sin_retraso'
        elif dias <= 7:
            return 'leve'  # 1-7 días
        elif dias <= 15:
            return 'moderado'  # 8-15 días
        elif dias <= 30:
            return 'severo'  # 16-30 días
        else:
            return 'critico'  # +30 días
    
    @property
    def porcentaje_tiempo_transcurrido(self):
        """Calcula el porcentaje de tiempo transcurrido del proyecto."""
        if not self.fecha_inicio or not self.fecha_fin:
            return 0
        
        hoy = timezone.now().date()
        
        # Si el proyecto no ha iniciado
        if hoy < self.fecha_inicio:
            return 0
        
        # Duración total del proyecto
        duracion_total = (self.fecha_fin - self.fecha_inicio).days
        if duracion_total <= 0:
            return 100
        
        # Tiempo transcurrido
        if self.estado == 'finalizado' and self.fecha_fin_real:
            tiempo_transcurrido = (self.fecha_fin_real - self.fecha_inicio).days
        else:
            tiempo_transcurrido = (hoy - self.fecha_inicio).days
        
        porcentaje = (tiempo_transcurrido / duracion_total) * 100
        return min(max(porcentaje, 0), 200)  # Limitar entre 0% y 200%
    
    @property
    def desviacion_cronograma(self):
        """Calcula la desviación entre avance real y avance esperado."""
        tiempo_transcurrido = self.porcentaje_tiempo_transcurrido
        
        # Avance esperado basándose en el tiempo transcurrido
        avance_esperado = min(tiempo_transcurrido, 100)
        
        # Desviación (positivo = adelantado, negativo = atrasado)
        return float(self.avance) - avance_esperado
    
    @property
    def estado_cronograma(self):
        """Determina el estado del cronograma del proyecto."""
        desviacion = self.desviacion_cronograma
        
        if desviacion >= 10:
            return 'adelantado'
        elif desviacion >= -5:
            return 'en_tiempo'
        elif desviacion >= -15:
            return 'ligeramente_atrasado'
        else:
            return 'muy_atrasado'
    
    @property
    def dias_proyecto_total(self):
        """Calcula la duración total del proyecto en días."""
        if not self.fecha_inicio or not self.fecha_fin:
            return 0
        return (self.fecha_fin - self.fecha_inicio).days
    
    def calcular_avance_real(self):
        """Calcula el % avance real basado en días de duración de actividades.
        
        Regla de negocio:
        - 100% = Sumatoria de días de duración planeada de todas las actividades
        - Actividades completadas (finalizado) = 100% de su duración
        - Actividades no completadas = duración × (avance_actividad / 100)
        """
        actividades = self.actividades.all()
        
        if not actividades.exists():
            return Decimal('0.00')
        
        total_dias_planeados = Decimal('0.00')
        dias_completados = Decimal('0.00')
        
        for actividad in actividades:
            duracion = actividad.duracion or Decimal('0.00')
            
            # Sumar a total de días planeados
            total_dias_planeados += duracion
            
            # Calcular contribución según estado
            if actividad.estado == 'finalizado':
                # Actividad completada: contribuye el 100% de su duración
                dias_completados += duracion
            else:
                # Actividad no completada: contribuye duración × (avance / 100)
                avance_decimal = (actividad.avance or Decimal('0.00')) / Decimal('100.00')
                dias_completados += duracion * avance_decimal
        
        # Calcular porcentaje final
        if total_dias_planeados == 0:
            return Decimal('0.00')
        
        porcentaje_avance = (dias_completados / total_dias_planeados) * Decimal('100.00')
        
        # Redondear a 2 decimales y limitar entre 0 y 100
        return min(max(porcentaje_avance.quantize(Decimal('0.01')), Decimal('0.00')), Decimal('100.00'))
    
    def actualizar_avance_real(self):
        """Actualiza el campo avance con el cálculo basado en actividades."""
        nuevo_avance = self.calcular_avance_real()
        if self.avance != nuevo_avance:
            self.avance = nuevo_avance
            self.save(update_fields=['avance'])
        return nuevo_avance
    
    @property
    def eficiencia_tiempo(self):
        """Calcula la eficiencia de tiempo del proyecto (días planificados vs días utilizados)."""
        if self.estado != 'finalizado' or not self.fecha_fin_real:
            return None
        
        dias_planificados = self.dias_proyecto_total
        dias_utilizados = (self.fecha_fin_real - self.fecha_inicio).days
        
        if dias_utilizados <= 0:
            return 100
        
        return (dias_planificados / dias_utilizados) * 100
        
    @property
    def sobrecosto(self):
        """Calcula el porcentaje de sobrecosto del proyecto."""
        if self.presupuesto == 0:
            return 0
        return ((self.gasto_real - self.presupuesto) / self.presupuesto) * 100
    
    def get_alertas_retraso(self):
        """Obtiene alertas relacionadas con retrasos del proyecto."""
        alertas = []
        
        # Alerta por días de retraso
        if self.dias_retraso > 0:
            nivel = self.nivel_retraso
            alertas.append({
                'tipo': 'retraso_fecha',
                'nivel': nivel,
                'mensaje': f'Proyecto atrasado {self.dias_retraso} días',
                'dias': self.dias_retraso
            })
        
        # Alerta por desviación de cronograma
        desviacion = self.desviacion_cronograma
        if desviacion < -10:
            alertas.append({
                'tipo': 'desviacion_cronograma',
                'nivel': 'moderado' if desviacion > -20 else 'severo',
                'mensaje': f'Avance real {abs(desviacion):.1f}% por debajo de lo esperado',
                'desviacion': desviacion
            })
        
        # Alerta por proximidad a fecha límite
        dias_restantes = self.dias_restantes
        if dias_restantes <= 7 and dias_restantes > 0 and self.estado != 'finalizado':
            alertas.append({
                'tipo': 'proximidad_fecha',
                'nivel': 'leve' if dias_restantes > 3 else 'moderado',
                'mensaje': f'Quedan {dias_restantes} días para la fecha límite',
                'dias_restantes': dias_restantes
            })
        
        return alertas
    
    @property
    def porcentaje_ejecucion_presupuesto(self):
        """Calcula el porcentaje de ejecución del presupuesto total."""
        if self.presupuesto == 0:
            return 0
        return float((self.gasto_real / self.presupuesto) * 100)
    
    @property
    def porcentaje_ejecucion_gasto_operativo(self):
        """Calcula el porcentaje de ejecución del presupuesto de gasto operativo."""
        if self.presupuesto_gasto == 0:
            return 0
        return float((self.gasto_operativo_real / self.presupuesto_gasto) * 100)
    
    @property
    def presupuesto_disponible(self):
        """Calcula el presupuesto disponible restante."""
        return float(max(0, self.presupuesto - self.gasto_real))
    
    @property
    def presupuesto_gasto_disponible(self):
        """Calcula el presupuesto de gasto operativo disponible."""
        return float(max(0, self.presupuesto_gasto - self.gasto_operativo_real))
    
    @property
    def estado_presupuesto(self):
        """Determina el estado del presupuesto del proyecto."""
        porcentaje = float(self.porcentaje_ejecucion_presupuesto)
        avance = float(self.avance)
        
        # Comparar ejecución presupuestaria con avance físico
        diferencia = porcentaje - avance
        
        if diferencia > 20:
            return 'sobreejecucion_critica'  # Gastando mucho más rápido que avanzando
        elif diferencia > 10:
            return 'sobreejecucion_moderada'
        elif diferencia > -5:
            return 'normal'
        elif diferencia > -15:
            return 'subejecucion_leve'  # Gastando menos de lo esperado
        else:
            return 'subejecucion_alta'
    
    @property
    def eficiencia_presupuestaria(self):
        """Calcula la eficiencia presupuestaria (avance vs gasto)."""
        porcentaje_ejecucion = float(self.porcentaje_ejecucion_presupuesto)
        if porcentaje_ejecucion == 0:
            return float('inf') if float(self.avance) > 0 else 0
        
        return float(self.avance) / porcentaje_ejecucion
    
    @property
    def proyeccion_costo_final(self):
        """Proyecta el costo final del proyecto basado en el avance actual."""
        avance = float(self.avance)
        if avance == 0:
            return float(self.gasto_real)
        
        return float((self.gasto_real / avance) * 100)
    
    @property
    def riesgo_sobrecosto(self):
        """Evalua el riesgo de sobrecosto del proyecto."""
        proyeccion = self.proyeccion_costo_final
        
        if self.presupuesto == 0:
            return 'sin_presupuesto'
        
        porcentaje_sobrecosto_proyectado = float(((proyeccion - float(self.presupuesto)) / float(self.presupuesto)) * 100)
        
        if porcentaje_sobrecosto_proyectado > 20:
            return 'alto'
        elif porcentaje_sobrecosto_proyectado > 10:
            return 'moderado'
        elif porcentaje_sobrecosto_proyectado > 0:
            return 'bajo'
        else:
            return 'dentro_presupuesto'
    
    def get_alertas_presupuesto(self):
        """Obtiene alertas relacionadas con el presupuesto del proyecto."""
        alertas = []
        
        # Alerta por sobrecosto actual
        sobrecosto = self.sobrecosto
        if sobrecosto > 10:
            nivel = 'critico' if sobrecosto > 20 else 'moderado'
            alertas.append({
                'tipo': 'sobrecosto_actual',
                'nivel': nivel,
                'mensaje': f'Sobrecosto actual del {sobrecosto:.1f}%',
                'valor': sobrecosto
            })
        
        # Alerta por riesgo de sobrecosto
        riesgo = self.riesgo_sobrecosto
        if riesgo in ['alto', 'moderado']:
            proyeccion = self.proyeccion_costo_final
            sobrecosto_proyectado = ((proyeccion - float(self.presupuesto)) / float(self.presupuesto)) * 100 if self.presupuesto > 0 else 0
            alertas.append({
                'tipo': 'riesgo_sobrecosto',
                'nivel': 'moderado' if riesgo == 'moderado' else 'severo',
                'mensaje': f'Proyección de sobrecosto del {sobrecosto_proyectado:.1f}%',
                'proyeccion': proyeccion
            })
        
        # Alerta por estado presupuestario
        estado = self.estado_presupuesto
        if estado.startswith('sobreejecucion'):
            alertas.append({
                'tipo': 'sobreejecucion_presupuesto',
                'nivel': 'severo' if 'critica' in estado else 'moderado',
                'mensaje': 'Ejecución presupuestaria superior al avance físico',
                'diferencia': self.porcentaje_ejecucion_presupuesto - float(self.avance)
            })
        
        # Alerta por presupuesto agotado
        if self.presupuesto_disponible < (float(self.presupuesto) * 0.1):  # Menos del 10% disponible
            alertas.append({
                'tipo': 'presupuesto_agotandose',
                'nivel': 'moderado',
                'mensaje': f'Presupuesto disponible: ${self.presupuesto_disponible:,.0f}',
                'disponible': self.presupuesto_disponible
            })
        
        return alertas
    
    def get_alertas_completas(self):
        """Obtiene todas las alertas del proyecto (retrasos + presupuesto)."""
        alertas_retraso = self.get_alertas_retraso()
        alertas_presupuesto = self.get_alertas_presupuesto()
        
        return {
            'retraso': alertas_retraso,
            'presupuesto': alertas_presupuesto,
            'total': len(alertas_retraso) + len(alertas_presupuesto)
        }

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
    
    RESPONSABLE_EJECUCION_CHOICES = [
        ('rgd', 'RGD Aire'),
        ('cliente', 'Cliente'),
        ('externo', 'Tercero/Externo')
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
    
    # Nuevos campos
    responsable_asignado = models.ForeignKey(
        'Colaborador',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades_asignadas',
        verbose_name='Responsable Asignado',
        help_text='Colaborador responsable de ejecutar esta actividad'
    )
    responsable_ejecucion = models.CharField(
        'Responsable de Ejecución',
        max_length=10,
        choices=RESPONSABLE_EJECUCION_CHOICES,
        default='rgd',
        help_text='Indica quién ejecuta la actividad: RGD Aire, Cliente o Tercero'
    )

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        return f"{self.actividad} - {self.proyecto}"
        
    @property
    def centro_costo(self):
        """Returns the centro_costos of the associated project"""
        if self.proyecto:
            return self.proyecto.centro_costos
        return None

class Recurso(models.Model):
    material_herramienta = models.CharField('Material o Herramienta', max_length=200)
    unidad = models.CharField(max_length=50)
    proyecto = models.CharField(max_length=200)
    actividad = models.CharField(max_length=200)

    def __str__(self):
        return self.material_herramienta

class Bitacora(models.Model):
    ESTADO_CHOICES = [
        ('planeada', 'Planeada'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada')
    ]
    
    ESTADO_VALIDACION_CHOICES = [
        ('pendiente', 'Pendiente de Validación'),
        ('validada_director', 'Validada por Director'),
        ('validada_ingeniero', 'Validada por Ingeniero'),
        ('validada_completa', 'Validación Completa'),
        ('rechazada', 'Rechazada')
    ]
    
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='bitacoras')
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE, related_name='bitacoras')
    subactividad = models.CharField(max_length=200)
    
    # Responsables y Equipo Ampliado
    responsable = models.ForeignKey(Colaborador, on_delete=models.CASCADE, related_name='bitacoras_responsable')
    lider_trabajo = models.ForeignKey(
        Colaborador, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='bitacoras_lider',
        verbose_name='Líder de Trabajo',
        help_text='Persona responsable de liderar el equipo en esta actividad'
    )
    equipo = models.ManyToManyField(Colaborador, related_name='bitacoras_equipo', blank=True)
    
    # Fechas y Planificación
    fecha_planificada = models.DateField(
        'Fecha de Ejecución Planeada',
        default=timezone.now,
        help_text='Fecha en que se planificó ejecutar esta actividad'
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_ejecucion_real = models.DateField(
        'Fecha de Ejecución Real',
        null=True,
        blank=True,
        help_text='Fecha en que realmente se ejecutó la actividad'
    )
    
    # Estado y Control
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='planeada',
        help_text='Estado actual de la actividad'
    )
    estado_validacion = models.CharField(
        max_length=20,
        choices=ESTADO_VALIDACION_CHOICES,
        default='pendiente',
        help_text='Estado de validación por director e ingeniero'
    )
    
    # Contenido
    descripcion = models.TextField('Descripción de la Actividad')
    duracion_horas = models.DecimalField('Duración (Horas)', max_digits=5, decimal_places=2)
    observaciones = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='bitacora/imagenes/', blank=True)
    archivo = models.FileField(upload_to='bitacora/archivos/', blank=True)
    
    # Firmas Digitales
    firma_director = models.TextField(
        'Firma Digital Director',
        blank=True,
        help_text='Firma digital del director del proyecto'
    )
    fecha_firma_director = models.DateTimeField(
        'Fecha Firma Director',
        null=True,
        blank=True
    )
    firma_ingeniero = models.TextField(
        'Firma Digital Ingeniero',
        blank=True,
        help_text='Firma digital del ingeniero residente'
    )
    fecha_firma_ingeniero = models.DateTimeField(
        'Fecha Firma Ingeniero',
        null=True,
        blank=True
    )
    ip_firma_director = models.GenericIPAddressField(
        'IP Firma Director',
        null=True,
        blank=True,
        help_text='Dirección IP desde donde se firmó'
    )
    ip_firma_ingeniero = models.GenericIPAddressField(
        'IP Firma Ingeniero',
        null=True,
        blank=True,
        help_text='Dirección IP desde donde se firmó'
    )
    dispositivo_firma_director = models.CharField(
        'Dispositivo Firma Director',
        max_length=200,
        blank=True,
        help_text='Información del dispositivo usado para firmar'
    )
    dispositivo_firma_ingeniero = models.CharField(
        'Dispositivo Firma Ingeniero',
        max_length=200,
        blank=True,
        help_text='Información del dispositivo usado para firmar'
    )

    class Meta:
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.proyecto} - {self.actividad} - {self.fecha_registro}"
    
    def save(self, *args, **kwargs):
        # Establecer fecha de ejecución real cuando se completa
        if self.estado == 'completada' and not self.fecha_ejecucion_real:
            self.fecha_ejecucion_real = timezone.now().date()
        
        super().save(*args, **kwargs)
    
    @property
    def dias_retraso_ejecucion(self):
        """Calcula los días de retraso en la ejecución."""
        if not self.fecha_planificada:
            return 0
        
        fecha_comparacion = self.fecha_ejecucion_real or timezone.now().date()
        
        if fecha_comparacion > self.fecha_planificada:
            return (fecha_comparacion - self.fecha_planificada).days
        return 0
    
    @property
    def esta_atrasada(self):
        """Determina si la bitácora está atrasada."""
        return self.dias_retraso_ejecucion > 0
    
    @property
    def requiere_registro_urgente(self):
        """Determina si la bitácora planeada requiere registro urgente."""
        if self.estado != 'planeada':
            return False
        
        hoy = timezone.now().date()
        return hoy > self.fecha_planificada
    
    @property
    def estado_validacion_completo(self):
        """Verifica si la validación está completa."""
        return (self.firma_director and self.firma_ingeniero and 
                self.estado_validacion == 'validada_completa')
    
    @property
    def nivel_urgencia(self):
        """Determina el nivel de urgencia para registro."""
        if self.estado != 'planeada':
            return 'sin_urgencia'
        
        dias_retraso = self.dias_retraso_ejecucion
        
        if dias_retraso == 0:
            return 'normal'
        elif dias_retraso <= 2:
            return 'leve'
        elif dias_retraso <= 5:
            return 'moderado'
        else:
            return 'critico'
    
    @property
    def equipo_nombres(self):
        """Retorna los nombres del equipo como string."""
        return ', '.join([colaborador.nombre for colaborador in self.equipo.all()])
    
    def firmar_director(self, firma_data, ip_address, device_info):
        """Registra la firma digital del director."""
        self.firma_director = firma_data
        self.fecha_firma_director = timezone.now()
        self.ip_firma_director = ip_address
        self.dispositivo_firma_director = device_info
        
        # Actualizar estado de validación
        if self.firma_ingeniero:
            self.estado_validacion = 'validada_completa'
        else:
            self.estado_validacion = 'validada_director'
        
        self.save()
    
    def firmar_ingeniero(self, firma_data, ip_address, device_info):
        """Registra la firma digital del ingeniero."""
        self.firma_ingeniero = firma_data
        self.fecha_firma_ingeniero = timezone.now()
        self.ip_firma_ingeniero = ip_address
        self.dispositivo_firma_ingeniero = device_info
        
        # Actualizar estado de validación
        if self.firma_director:
            self.estado_validacion = 'validada_completa'
        else:
            self.estado_validacion = 'validada_ingeniero'
        
        self.save()
    
    def get_alertas_bitacora(self):
        """Obtiene alertas relacionadas con la bitácora."""
        alertas = []
        
        # Alerta por registro atrasado
        if self.requiere_registro_urgente:
            nivel = self.nivel_urgencia
            alertas.append({
                'tipo': 'registro_atrasado',
                'nivel': nivel,
                'mensaje': f'Registro atrasado {self.dias_retraso_ejecucion} días',
                'dias_retraso': self.dias_retraso_ejecucion
            })
        
        # Alerta por validación pendiente
        if self.estado == 'completada' and not self.estado_validacion_completo:
            alertas.append({
                'tipo': 'validacion_pendiente',
                'nivel': 'moderado',
                'mensaje': 'Validación digital pendiente',
                'firmas_faltantes': [
                    'Director' if not self.firma_director else None,
                    'Ingeniero' if not self.firma_ingeniero else None
                ]
            })
        
        return alertas

class BitacoraArchivo(models.Model):
    """Modelo para manejar múltiples archivos adjuntos en una bitácora"""
    bitacora = models.ForeignKey(Bitacora, on_delete=models.CASCADE, related_name='archivos_adjuntos')
    archivo = models.FileField('Archivo', upload_to='bitacora/adjuntos/')
    nombre_original = models.CharField('Nombre del archivo', max_length=255)
    fecha_subida = models.DateTimeField('Fecha de subida', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Archivo de Bitácora'
        verbose_name_plural = 'Archivos de Bitácora'
        ordering = ['fecha_subida']
    
    def __str__(self):
        return f"{self.nombre_original} - {self.bitacora}"
    
    @property
    def extension(self):
        """Retorna la extensión del archivo"""
        return self.nombre_original.split('.')[-1].lower() if '.' in self.nombre_original else ''
    
    @property 
    def es_imagen(self):
        """Verifica si el archivo es una imagen"""
        extensiones_imagen = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return self.extension in extensiones_imagen
    
    @property
    def tamano_legible(self):
        """Retorna el tamaño del archivo en formato legible"""
        try:
            size = self.archivo.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
        except:
            return "Desconocido"

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

class ProrrogaProyecto(models.Model):
    """Modelo para gestionar prórrogas de proyectos"""
    TIPO_CHOICES = [
        ('cliente', 'Solicitud del Cliente'),
        ('tecnica', 'Razón Técnica'),
        ('clima', 'Condiciones Climáticas'),
        ('recursos', 'Disponibilidad de Recursos'),
        ('fuerza_mayor', 'Fuerza Mayor'),
        ('otra', 'Otra Razón')
    ]
    
    ESTADO_CHOICES = [
        ('solicitada', 'Solicitada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('aplicada', 'Aplicada')
    ]
    
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='prorrogas')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_fin_original = models.DateField('Fecha Fin Original')
    fecha_fin_propuesta = models.DateField('Nueva Fecha Fin Propuesta')
    dias_extension = models.PositiveIntegerField('Días de Extensión')
    tipo_prorroga = models.CharField('Tipo de Prórroga', max_length=20, choices=TIPO_CHOICES)
    justificacion = models.TextField('Justificación de la Prórroga')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='solicitada')
    
    # Aprobación
    aprobada_por = models.CharField('Aprobada por', max_length=200, blank=True)
    fecha_aprobacion = models.DateTimeField('Fecha de Aprobación', null=True, blank=True)
    observaciones_aprobacion = models.TextField('Observaciones de Aprobación', blank=True)
    
    # Archivos de soporte
    documento_soporte = models.FileField('Documento de Soporte', upload_to='prorrogas/', blank=True)
    
    class Meta:
        verbose_name = 'Prórroga de Proyecto'
        verbose_name_plural = 'Prórrogas de Proyecto'
        ordering = ['-fecha_solicitud']
    
    def save(self, *args, **kwargs):
        # Calcular días de extensión automáticamente
        if self.fecha_fin_original and self.fecha_fin_propuesta:
            delta = self.fecha_fin_propuesta - self.fecha_fin_original
            self.dias_extension = delta.days
        
        # Si se aprueba la prórroga, actualizar fecha fin del proyecto
        if self.estado == 'aprobada' and self.pk:
            old_instance = ProrrogaProyecto.objects.get(pk=self.pk)
            if old_instance.estado != 'aprobada':
                self.proyecto.fecha_fin = self.fecha_fin_propuesta
                self.proyecto.save(update_fields=['fecha_fin'])
                self.estado = 'aplicada'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Prórroga {self.proyecto.nombre_proyecto} - {self.dias_extension} días"
    
    @property
    def es_aprobable(self):
        """Verifica si la prórroga puede ser aprobada"""
        return self.estado == 'solicitada'
    
    @property
    def impacto_presupuesto(self):
        """Calcula el impacto estimado en el presupuesto por día adicional"""
        if self.proyecto.presupuesto and self.proyecto.dias_prometidos:
            costo_por_dia = self.proyecto.presupuesto / self.proyecto.dias_prometidos
            return costo_por_dia * self.dias_extension
        return 0


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


# ============================================================================
# SESIÓN 5: MÓDULO DE COMITÉ DE PROYECTOS
# ============================================================================

class ComiteProyecto(models.Model):
    """
    Modelo para registrar las reuniones de comité de proyectos.
    Permite hacer seguimiento y trazabilidad de decisiones.
    """
    
    TIPO_COMITE_CHOICES = [
        ('semanal', 'Comité Semanal'),
        ('mensual', 'Comité Mensual'),
        ('extraordinario', 'Comité Extraordinario'),
        ('revision', 'Comité de Revisión'),
    ]
    
    # Información básica del comité
    nombre = models.CharField('Nombre del Comité', max_length=200)
    fecha_comite = models.DateTimeField('Fecha y Hora del Comité')
    tipo_comite = models.CharField(
        'Tipo de Comité',
        max_length=20,
        choices=TIPO_COMITE_CHOICES,
        default='semanal'
    )
    lugar = models.CharField('Lugar de Reunión', max_length=200, blank=True)
    
    # Organización del comité
    coordinador = models.ForeignKey(
        Colaborador,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comites_coordinados',
        verbose_name='Coordinador del Comité'
    )
    
    # Participantes del comité
    participantes = models.ManyToManyField(
        Colaborador,
        through='ParticipanteComite',
        related_name='comites_participados',
        verbose_name='Participantes'
    )
    
    # Información adicional
    agenda = models.TextField('Agenda del Comité', blank=True)
    observaciones = models.TextField('Observaciones Generales', blank=True)
    acta_reunion = models.FileField(
        'Acta de Reunión',
        upload_to='comites/actas/',
        blank=True
    )
    
    # Control de registro
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comites_creados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Estado del comité
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('en_curso', 'En Curso'),
        ('finalizado', 'Finalizado'),
        ('cancelado', 'Cancelado'),
    ]
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='programado'
    )
    
    class Meta:
        verbose_name = 'Comité de Proyecto'
        verbose_name_plural = 'Comités de Proyectos'
        ordering = ['-fecha_comite']
    
    def __str__(self):
        return f"{self.nombre} - {self.fecha_comite.strftime('%d/%m/%Y')}"
    
    @property
    def numero_participantes(self):
        """Retorna el número de participantes confirmados"""
        return self.participantes.count()
    
    @property
    def proyectos_revisados(self):
        """Retorna la cantidad de proyectos revisados en este comité"""
        return self.seguimientos.count()
    
    @property
    def duracion_estimada(self):
        """Calcula duración estimada basada en proyectos y participantes"""
        base_minutos = 30  # 30 min base
        minutos_por_proyecto = 10  # 10 min por proyecto
        return base_minutos + (self.proyectos_revisados * minutos_por_proyecto)


class ParticipanteComite(models.Model):
    """
    Modelo intermedio para gestionar participantes del comité con información adicional.
    """
    
    TIPO_PARTICIPACION_CHOICES = [
        ('obligatorio', 'Obligatorio'),
        ('opcional', 'Opcional'),
        ('invitado', 'Invitado'),
    ]
    
    ESTADO_ASISTENCIA_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('ausente', 'Ausente'),
        ('presente', 'Presente'),
    ]
    
    comite = models.ForeignKey(ComiteProyecto, on_delete=models.CASCADE)
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    
    tipo_participacion = models.CharField(
        'Tipo de Participación',
        max_length=20,
        choices=TIPO_PARTICIPACION_CHOICES,
        default='obligatorio'
    )
    
    estado_asistencia = models.CharField(
        'Estado de Asistencia',
        max_length=20,
        choices=ESTADO_ASISTENCIA_CHOICES,
        default='pendiente'
    )
    
    rol_en_comite = models.CharField(
        'Rol en el Comité',
        max_length=100,
        blank=True,
        help_text='Ej: Presentador, Revisor, Observador'
    )
    
    observaciones = models.TextField('Observaciones', blank=True)
    fecha_confirmacion = models.DateTimeField('Fecha de Confirmación', null=True, blank=True)
    
    class Meta:
        unique_together = ['comite', 'colaborador']
        verbose_name = 'Participante de Comité'
        verbose_name_plural = 'Participantes de Comité'
    
    def __str__(self):
        return f"{self.colaborador.nombre} - {self.comite.nombre}"


class SeguimientoProyectoComite(models.Model):
    """
    Modelo para registrar el seguimiento específico de cada proyecto en un comité.
    Auto-despliega proyectos activos al crear el comité.
    """
    
    ESTADO_SEGUIMIENTO_CHOICES = [
        ('verde', 'Verde - Sin problemas'),
        ('amarillo', 'Amarillo - Requiere atención'),
        ('rojo', 'Rojo - Crítico'),
        ('azul', 'Azul - En pausa'),
    ]
    
    comite = models.ForeignKey(
        ComiteProyecto,
        on_delete=models.CASCADE,
        related_name='seguimientos'
    )
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='seguimientos_comite'
    )
    
    # Información específica del proyecto en este comité
    estado_seguimiento = models.CharField(
        'Estado de Seguimiento',
        max_length=20,
        choices=ESTADO_SEGUIMIENTO_CHOICES,
        default='verde'
    )
    
    avance_reportado = models.DecimalField(
        'Avance Reportado (%)',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Avance reportado en este comité'
    )
    
    avance_anterior = models.DecimalField(
        'Avance Anterior (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Avance del comité anterior para comparación'
    )
    
    # Información detallada
    logros_periodo = models.TextField(
        'Logros del Período',
        help_text='Principales logros desde el último comité'
    )
    
    dificultades = models.TextField(
        'Dificultades Encontradas',
        blank=True,
        help_text='Problemas o obstáculos identificados'
    )
    
    acciones_requeridas = models.TextField(
        'Acciones Requeridas',
        blank=True,
        help_text='Acciones específicas definidas en el comité'
    )
    
    responsable_reporte = models.ForeignKey(
        Colaborador,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reportes_comite',
        verbose_name='Responsable del Reporte'
    )
    
    fecha_proximo_hito = models.DateField(
        'Fecha Próximo Hito',
        null=True,
        blank=True,
        help_text='Fecha del próximo hito importante'
    )
    
    # Control de presupuesto específico para el comité
    presupuesto_ejecutado = models.DecimalField(
        'Presupuesto Ejecutado',
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Presupuesto ejecutado reportado en este comité'
    )
    
    observaciones = models.TextField('Observaciones Específicas', blank=True)
    
    # Metadata
    orden_presentacion = models.PositiveIntegerField(
        'Orden de Presentación',
        default=1,
        help_text='Orden en que se presenta el proyecto en el comité'
    )
    
    tiempo_asignado = models.PositiveIntegerField(
        'Tiempo Asignado (minutos)',
        default=10,
        help_text='Tiempo asignado para la presentación del proyecto'
    )
    
    requiere_decision = models.BooleanField(
        'Requiere Decisión',
        default=False,
        help_text='Marca si el proyecto requiere una decisión del comité'
    )
    
    decision_tomada = models.TextField(
        'Decisión Tomada',
        blank=True,
        help_text='Decisión específica tomada por el comité para este proyecto'
    )
    
    # Relación con tareas generadas
    tareas_generadas = models.ManyToManyField(
        'tasks.Task',
        blank=True,
        related_name='seguimientos_comite',
        verbose_name='Tareas Generadas',
        help_text='Tareas creadas desde este seguimiento de comité'
    )
    
    class Meta:
        unique_together = ['comite', 'proyecto']
        verbose_name = 'Seguimiento de Proyecto en Comité'
        verbose_name_plural = 'Seguimientos de Proyectos en Comités'
        ordering = ['orden_presentacion', 'proyecto__nombre_proyecto']
    
    def __str__(self):
        return f"{self.proyecto.nombre_proyecto} - {self.comite.nombre}"
    
    @property
    def variacion_avance(self):
        """Calcula la variación de avance respecto al período anterior"""
        if self.avance_anterior is not None:
            return self.avance_reportado - self.avance_anterior
        return None
    
    @property
    def color_seguimiento(self):
        """Retorna el color CSS basado en el estado de seguimiento"""
        colores = {
            'verde': '#28a745',
            'amarillo': '#ffc107', 
            'rojo': '#dc3545',
            'azul': '#007bff'
        }
        return colores.get(self.estado_seguimiento, '#6c757d')
    
    @property
    def icono_seguimiento(self):
        """Retorna el icono FontAwesome basado en el estado"""
        iconos = {
            'verde': 'fas fa-check-circle',
            'amarillo': 'fas fa-exclamation-triangle',
            'rojo': 'fas fa-exclamation-circle',
            'azul': 'fas fa-pause-circle'
        }
        return iconos.get(self.estado_seguimiento, 'fas fa-circle')


class SeguimientoServicioComite(models.Model):
    """
    Modelo para registrar el seguimiento específico de cada servicio en un comité.
    """
    
    ESTADO_SEGUIMIENTO_CHOICES = [
        ('verde', 'Verde - Sin problemas'),
        ('amarillo', 'Amarillo - Requiere atención'),
        ('rojo', 'Rojo - Crítico'),
        ('azul', 'Azul - En pausa'),
    ]
    
    comite = models.ForeignKey(
        ComiteProyecto,
        on_delete=models.CASCADE,
        related_name='seguimientos_servicios'
    )
    servicio = models.ForeignKey(
        'servicios.SolicitudServicio',
        on_delete=models.CASCADE,
        related_name='seguimientos_comite'
    )
    
    # Información específica del servicio en este comité
    estado_seguimiento = models.CharField(
        'Estado de Seguimiento',
        max_length=20,
        choices=ESTADO_SEGUIMIENTO_CHOICES,
        default='verde'
    )
    
    avance_reportado = models.DecimalField(
        'Avance Reportado (%)',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Avance reportado en este comité',
        default=0
    )
    
    # Información detallada
    logros_periodo = models.TextField(
        'Logros del Período',
        help_text='Principales logros desde el último comité',
        blank=True
    )
    
    dificultades = models.TextField(
        'Dificultades Encontradas',
        blank=True,
        help_text='Problemas o obstáculos identificados'
    )
    
    acciones_requeridas = models.TextField(
        'Acciones Requeridas',
        blank=True,
        help_text='Acciones específicas definidas en el comité'
    )
    
    responsable_reporte = models.ForeignKey(
        Colaborador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportes_servicio_comite',
        verbose_name='Responsable del Reporte'
    )
    
    fecha_proximo_hito = models.DateField(
        'Fecha Próximo Hito',
        null=True,
        blank=True,
        help_text='Fecha del próximo hito importante'
    )
    
    requiere_decision = models.BooleanField(
        'Requiere Decisión',
        default=False,
        help_text='Marca si este servicio requiere una decisión del comité'
    )
    
    decision_tomada = models.TextField(
        'Decisión Tomada',
        blank=True,
        help_text='Decisión específica tomada por el comité para este servicio'
    )
    
    orden_presentacion = models.PositiveIntegerField(
        'Orden de Presentación',
        default=1,
        help_text='Orden en que se presenta en el comité'
    )
    
    # Relación con tareas generadas
    tareas = models.ManyToManyField(
        'tasks.Task',
        blank=True,
        related_name='seguimientos_servicio_comite',
        verbose_name='Tareas Generadas',
        help_text='Tareas creadas desde este seguimiento de servicio en comité'
    )
    
    # Metadatos
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    actualizado_por = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='seguimientos_servicio_actualizados'
    )
    
    class Meta:
        verbose_name = 'Seguimiento de Servicio en Comité'
        verbose_name_plural = 'Seguimientos de Servicios en Comités'
        unique_together = ['comite', 'servicio']
        ordering = ['orden_presentacion', 'servicio__numero_orden']
    
    def __str__(self):
        return f"{self.servicio.numero_orden} - {self.comite.nombre}"
    
    @property
    def color_seguimiento(self):
        """Retorna el color CSS basado en el estado de seguimiento"""
        colores = {
            'verde': '#28a745',
            'amarillo': '#ffc107', 
            'rojo': '#dc3545',
            'azul': '#007bff'
        }
        return colores.get(self.estado_seguimiento, '#6c757d')
    
    @property
    def icono_seguimiento(self):
        """Retorna el icono FontAwesome basado en el estado"""
        iconos = {
            'verde': 'fas fa-check-circle',
            'amarillo': 'fas fa-exclamation-triangle',
            'rojo': 'fas fa-exclamation-circle',
            'azul': 'fas fa-pause-circle'
        }
        return iconos.get(self.estado_seguimiento, 'fas fa-question-circle')


class ElementoExternoComite(models.Model):
    """
    Modelo para elementos externos (proyectos/servicios) que no están en el sistema
    pero se quieren incluir en el seguimiento del comité.
    """
    
    TIPO_ELEMENTO_CHOICES = [
        ('proyecto', 'Proyecto'),
        ('servicio', 'Servicio'),
        ('otros', 'Otros'),
    ]
    
    ESTADO_SEGUIMIENTO_CHOICES = [
        ('verde', 'Verde - Sin problemas'),
        ('amarillo', 'Amarillo - Requiere atención'),
        ('rojo', 'Rojo - Crítico'),
        ('azul', 'Azul - En pausa'),
    ]
    
    comite = models.ForeignKey(
        ComiteProyecto,
        on_delete=models.CASCADE,
        related_name='elementos_externos'
    )
    
    # Información básica del elemento
    tipo_elemento = models.CharField(
        'Tipo de Elemento',
        max_length=20,
        choices=TIPO_ELEMENTO_CHOICES,
        default='proyecto'
    )
    
    cliente = models.CharField(
        'Cliente',
        max_length=200,
        help_text='Nombre del cliente'
    )
    
    centro_costos = models.CharField(
        'Centro de Costos',
        max_length=100,
        blank=True,
        help_text='Centro de costos al que pertenece'
    )
    
    nombre_proyecto = models.CharField(
        'Nombre del Proyecto/Servicio',
        max_length=200,
        help_text='Nombre descriptivo del proyecto o servicio'
    )
    
    # Información de seguimiento
    estado_seguimiento = models.CharField(
        'Estado de Seguimiento',
        max_length=20,
        choices=ESTADO_SEGUIMIENTO_CHOICES,
        default='verde'
    )
    
    avance_reportado = models.DecimalField(
        'Avance Reportado (%)',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Avance reportado en este comité',
        default=0
    )
    
    logros_periodo = models.TextField(
        'Logros del Período',
        blank=True,
        help_text='Principales logros y avances desde el último comité'
    )
    
    dificultades = models.TextField(
        'Dificultades',
        blank=True,
        help_text='Problemas, obstáculos o riesgos identificados'
    )
    
    acciones_requeridas = models.TextField(
        'Acciones Requeridas',
        blank=True,
        help_text='Acciones específicas a tomar para resolver dificultades'
    )
    
    responsable_reporte = models.ForeignKey(
        Colaborador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportes_externos_comite',
        verbose_name='Responsable del Reporte'
    )
    
    observaciones = models.TextField(
        'Observaciones',
        blank=True,
        help_text='Información adicional sobre el elemento'
    )
    
    decision_tomada = models.TextField(
        'Decisión Tomada',
        blank=True,
        help_text='Decisiones tomadas o pendientes de tomar'
    )
    
    # Relación con tareas generadas
    tareas_generadas = models.ManyToManyField(
        'tasks.Task',
        blank=True,
        related_name='elementos_externos_comite',
        verbose_name='Tareas Generadas',
        help_text='Tareas creadas desde este elemento externo'
    )
    
    # Campo temporal para compatibilidad
    orden_presentacion = models.PositiveIntegerField(
        'Orden de Presentación',
        default=999,
        help_text='Orden en que se presenta en el comité'
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='elementos_externos_creados'
    )
    actualizado_por = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='elementos_externos_actualizados'
    )
    
    class Meta:
        verbose_name = 'Elemento Externo de Comité'
        verbose_name_plural = 'Elementos Externos de Comités'
        ordering = ['comite', 'nombre_proyecto']
    
    def __str__(self):
        return f"{self.get_tipo_elemento_display()}: {self.nombre_proyecto} - {self.comite.nombre}"
    
    @property
    def color_seguimiento(self):
        """Retorna el color CSS basado en el estado de seguimiento"""
        colores = {
            'verde': '#28a745',
            'amarillo': '#ffc107', 
            'rojo': '#dc3545',
            'azul': '#007bff'
        }
        return colores.get(self.estado_seguimiento, '#6c757d')
    
    @property
    def icono_seguimiento(self):
        """Retorna el icono FontAwesome basado en el estado"""
        iconos = {
            'verde': 'fas fa-check-circle',
            'amarillo': 'fas fa-exclamation-triangle',
            'rojo': 'fas fa-exclamation-circle',
            'azul': 'fas fa-pause-circle'
        }
        return iconos.get(self.estado_seguimiento, 'fas fa-question-circle')
