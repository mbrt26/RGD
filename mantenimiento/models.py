from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()


class Equipo(models.Model):
    """Base de datos de equipos - Catálogo general de equipos disponibles"""
    
    CATEGORIA_CHOICES = [
        ('aire_acondicionado', 'Aire Acondicionado'),
        ('ventilacion', 'Ventilación'),
        ('calefaccion', 'Calefacción'),
        ('refrigeracion', 'Refrigeración'),
        ('humidificacion', 'Humidificación'),
        ('filtracion', 'Filtración'),
        ('otro', 'Otro'),
    ]
    
    # Información básica del equipo
    nombre = models.CharField('Nombre del Equipo', max_length=200, default='Equipo HVAC')
    descripcion = models.TextField('Descripción', help_text='Descripción técnica del equipo', default='')
    categoria = models.CharField('Categoría', max_length=50, choices=CATEGORIA_CHOICES, default='aire_acondicionado')
    marca = models.CharField('Marca', max_length=100, default='Sin especificar')
    modelo = models.CharField('Modelo', max_length=100, default='Sin especificar')
    
    # Especificaciones técnicas
    capacidad_btu = models.DecimalField('Capacidad BTU/h', max_digits=10, decimal_places=2, null=True, blank=True)
    voltaje = models.CharField('Voltaje', max_length=50, blank=True)
    amperaje = models.CharField('Amperaje', max_length=50, blank=True)
    refrigerante = models.CharField('Tipo de Refrigerante', max_length=50, blank=True)
    peso_kg = models.DecimalField('Peso (kg)', max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Información del fabricante
    fabricante = models.CharField('Fabricante', max_length=200, blank=True)
    pais_origen = models.CharField('País de Origen', max_length=100, blank=True)
    vida_util_anos = models.PositiveIntegerField('Vida Útil (años)', null=True, blank=True)
    
    # Estado y configuración
    activo = models.BooleanField('Activo', default=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='equipos_creados')
    
    class Meta:
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'
        ordering = ['categoria', 'marca', 'modelo']
    
    def __str__(self):
        return f"{self.marca} {self.modelo} - {self.nombre}"


class HojaVidaEquipo(models.Model):
    """Hoja de vida de equipos instalados en clientes - Instancia específica de un equipo"""
    
    ESTADO_CHOICES = [
        ('operativo', 'Operativo'),
        ('fuera_servicio', 'Fuera de Servicio'),
        ('mantenimiento', 'En Mantenimiento'),
        ('garantia', 'En Garantía'),
        ('reemplazo_pendiente', 'Pendiente de Reemplazo'),
        ('dado_baja', 'Dado de Baja'),
    ]
    
    # Relaciones principales
    equipo = models.ForeignKey(Equipo, on_delete=models.PROTECT, related_name='hojas_vida', verbose_name='Equipo')
    cliente = models.ForeignKey('crm.Cliente', on_delete=models.CASCADE, related_name='equipos_mantenimiento', verbose_name='Cliente')
    
    # Identificación única de la instancia
    codigo_interno = models.CharField('Código Interno', max_length=50, unique=True, help_text='Código único para este equipo específico')
    numero_serie = models.CharField('Número de Serie', max_length=100, unique=True)
    tag_cliente = models.CharField('Tag del Cliente', max_length=100, blank=True, help_text='Etiqueta o código que usa el cliente')
    
    # Información de instalación
    fecha_instalacion = models.DateField('Fecha de Instalación')
    fecha_compra = models.DateField('Fecha de Compra', null=True, blank=True)
    fecha_garantia_fin = models.DateField('Fin de Garantía', null=True, blank=True)
    proveedor = models.CharField('Proveedor', max_length=200, blank=True)
    valor_compra = models.DecimalField('Valor de Compra', max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Ubicación específica
    ubicacion_detallada = models.CharField('Ubicación Detallada', max_length=300, help_text='Ubicación específica en las instalaciones del cliente')
    direccion_instalacion = models.TextField('Dirección de Instalación', help_text='Dirección completa donde está instalado')
    coordenadas_gps = models.CharField('Coordenadas GPS', max_length=100, blank=True, help_text='Latitud, Longitud')
    
    # Estado actual
    estado = models.CharField('Estado', max_length=30, choices=ESTADO_CHOICES, default='operativo')
    fecha_ultimo_servicio = models.DateField('Último Servicio', null=True, blank=True)
    
    # Información adicional
    observaciones = models.TextField('Observaciones', blank=True)
    condiciones_ambientales = models.TextField('Condiciones Ambientales', blank=True, help_text='Temperatura, humedad, etc.')
    
    # Metadatos
    activo = models.BooleanField('Activo', default=True)
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hojas_vida_creadas')
    
    class Meta:
        verbose_name = 'Hoja de Vida de Equipo'
        verbose_name_plural = 'Hojas de Vida de Equipos'
        ordering = ['cliente__nombre', 'codigo_interno']
    
    def __str__(self):
        return f"{self.codigo_interno} - {self.equipo.marca} {self.equipo.modelo} ({self.cliente.nombre})"
    
    @property
    def edad_anos(self):
        """Calcula la edad del equipo en años"""
        if self.fecha_instalacion:
            delta = timezone.now().date() - self.fecha_instalacion
            return delta.days // 365
        return 0
    
    @property
    def en_garantia(self):
        """Verifica si el equipo está en garantía"""
        if self.fecha_garantia_fin:
            return timezone.now().date() <= self.fecha_garantia_fin
        return False


class RutinaMantenimiento(models.Model):
    """Rutina de mantenimiento definida para cada equipo específico del cliente"""
    
    TIPO_RUTINA_CHOICES = [
        ('preventivo', 'Mantenimiento Preventivo'),
        ('limpieza', 'Limpieza General'),
        ('inspeccion', 'Inspección Técnica'),
        ('calibracion', 'Calibración'),
        ('lubricacion', 'Lubricación'),
        ('cambio_filtros', 'Cambio de Filtros'),
        ('revision_general', 'Revisión General'),
    ]
    
    FRECUENCIA_CHOICES = [
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('semestral', 'Semestral'),
        ('anual', 'Anual'),
        ('personalizada', 'Personalizada'),
    ]
    
    # Relación con la hoja de vida del equipo
    hoja_vida_equipo = models.ForeignKey(HojaVidaEquipo, on_delete=models.CASCADE, related_name='rutinas_mantenimiento', verbose_name='Equipo')
    
    # Información de la rutina
    nombre_rutina = models.CharField('Nombre de la Rutina', max_length=200)
    tipo_rutina = models.CharField('Tipo de Rutina', max_length=30, choices=TIPO_RUTINA_CHOICES)
    descripcion = models.TextField('Descripción', help_text='Descripción detallada de la rutina')
    
    # Frecuencia y programación
    frecuencia = models.CharField('Frecuencia', max_length=20, choices=FRECUENCIA_CHOICES)
    dias_intervalo = models.PositiveIntegerField('Días de Intervalo', null=True, blank=True, help_text='Para frecuencia personalizada')
    
    # Configuración de ejecución
    duracion_estimada_horas = models.DecimalField('Duración Estimada (horas)', max_digits=4, decimal_places=2, default=1.0)
    requiere_parada_equipo = models.BooleanField('Requiere Parada del Equipo', default=False)
    requiere_tecnico_especializado = models.BooleanField('Requiere Técnico Especializado', default=False)
    
    # Materiales y herramientas
    materiales_necesarios = models.TextField('Materiales Necesarios', blank=True, help_text='Lista de materiales requeridos')
    herramientas_necesarias = models.TextField('Herramientas Necesarias', blank=True, help_text='Lista de herramientas requeridas')
    
    # Checklist de actividades
    checklist_actividades = models.JSONField('Checklist de Actividades', default=list, blank=True, help_text='Lista de actividades a realizar')
    
    # Estado y configuración
    activa = models.BooleanField('Activa', default=True)
    prioridad = models.CharField('Prioridad', max_length=20, choices=[
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ], default='media')
    
    # Observaciones
    observaciones = models.TextField('Observaciones', blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='rutinas_creadas')
    
    class Meta:
        verbose_name = 'Rutina de Mantenimiento'
        verbose_name_plural = 'Rutinas de Mantenimiento'
        ordering = ['hoja_vida_equipo', 'prioridad', 'nombre_rutina']
    
    def __str__(self):
        return f"{self.nombre_rutina} - {self.hoja_vida_equipo.codigo_interno}"
    
    def get_dias_intervalo(self):
        """Obtiene los días de intervalo según la frecuencia"""
        intervalos = {
            'semanal': 7,
            'quincenal': 15,
            'mensual': 30,
            'bimestral': 60,
            'trimestral': 90,
            'semestral': 180,
            'anual': 365,
        }
        return intervalos.get(self.frecuencia, self.dias_intervalo or 30)


class ContratoMantenimiento(models.Model):
    """Contrato de mantenimiento que agrupa hojas de vida de equipos con integración CRM"""
    
    TIPO_CONTRATO_CHOICES = [
        ('preventivo', 'Mantenimiento Preventivo'),
        ('correctivo', 'Mantenimiento Correctivo'),
        ('integral', 'Mantenimiento Integral'),
        ('emergencia', 'Solo Emergencias'),
        ('personalizado', 'Personalizado'),
    ]
    
    ESTADO_CHOICES = [
        ('borrador', 'Borrador'),
        ('activo', 'Activo'),
        ('suspendido', 'Suspendido'),
        ('vencido', 'Vencido'),
        ('cancelado', 'Cancelado'),
        ('renovado', 'Renovado'),
    ]
    
    # Integración con CRM
    trato_origen = models.ForeignKey(
        'crm.Trato',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Trato de Origen',
        help_text='Trato del CRM que originó este contrato'
    )
    cotizacion_aprobada = models.ForeignKey(
        'crm.VersionCotizacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Cotización Aprobada',
        help_text='Cotización aprobada asociada al contrato'
    )
    
    # Información básica del contrato
    numero_contrato = models.CharField('Número de Contrato', max_length=50, unique=True)
    cliente = models.ForeignKey('crm.Cliente', on_delete=models.CASCADE, related_name='contratos_mantenimiento', verbose_name='Cliente')
    nombre_contrato = models.CharField('Nombre del Contrato', max_length=200, default='Contrato de Mantenimiento')
    tipo_contrato = models.CharField('Tipo de Contrato', max_length=30, choices=TIPO_CONTRATO_CHOICES, default='preventivo')
    
    # Vigencia
    fecha_inicio = models.DateField('Fecha de Inicio')
    fecha_fin = models.DateField('Fecha de Fin')
    renovacion_automatica = models.BooleanField('Renovación Automática', default=False)
    meses_duracion = models.PositiveIntegerField('Duración (meses)', default=12)
    
    # Términos económicos
    valor_mensual = models.DecimalField('Valor Mensual', max_digits=12, decimal_places=2, default=0)
    valor_total_contrato = models.DecimalField('Valor Total del Contrato', max_digits=12, decimal_places=2, default=0)
    incluye_materiales = models.BooleanField('Incluye Materiales', default=False)
    incluye_repuestos = models.BooleanField('Incluye Repuestos', default=False)
    valor_hora_adicional = models.DecimalField('Valor Hora Adicional', max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Equipos incluidos en el contrato
    equipos_incluidos = models.ManyToManyField(HojaVidaEquipo, related_name='contratos', verbose_name='Equipos Incluidos', blank=True)
    
    # Condiciones de servicio
    tiempo_respuesta_horas = models.PositiveIntegerField('Tiempo de Respuesta (horas)', default=24)
    horas_incluidas_mes = models.PositiveIntegerField('Horas Incluidas por Mes', default=0)
    disponibilidad_24_7 = models.BooleanField('Disponibilidad 24/7', default=False)
    
    # Estado del contrato
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='borrador')
    
    # Contactos y responsables
    contacto_cliente = models.ForeignKey('crm.Contacto', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Contacto del Cliente')
    responsable_tecnico = models.ForeignKey('servicios.Tecnico', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Responsable Técnico')
    
    # Información adicional
    condiciones_especiales = models.TextField('Condiciones Especiales', blank=True)
    observaciones = models.TextField('Observaciones', blank=True)
    clausulas_adicionales = models.TextField('Cláusulas Adicionales', blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='contratos_creados')
    
    class Meta:
        verbose_name = 'Contrato de Mantenimiento'
        verbose_name_plural = 'Contratos de Mantenimiento'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.numero_contrato} - {self.cliente.nombre}"
    
    def save(self, *args, **kwargs):
        if not self.numero_contrato:
            # Generar número de contrato automático
            ultimo_numero = ContratoMantenimiento.objects.filter(
                numero_contrato__startswith=f"CM{timezone.now().year}"
            ).order_by('-numero_contrato').first()
            
            if ultimo_numero:
                try:
                    ultimo_num = int(ultimo_numero.numero_contrato[-4:])
                    nuevo_num = ultimo_num + 1
                except:
                    nuevo_num = 1
            else:
                nuevo_num = 1
            
            self.numero_contrato = f"CM{timezone.now().year}{nuevo_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def vigente(self):
        """Verifica si el contrato está vigente"""
        hoy = timezone.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin and self.estado == 'activo'
    
    @property
    def dias_para_vencer(self):
        """Calcula días para el vencimiento"""
        if self.fecha_fin:
            delta = self.fecha_fin - timezone.now().date()
            return delta.days
        return None
    
    def get_equipos_count(self):
        """Cuenta equipos incluidos en el contrato"""
        return self.equipos_incluidos.count()


class ActividadMantenimiento(models.Model):
    """Tabla consolidada de todas las actividades de mantenimiento programadas y ejecutadas"""
    
    TIPO_ACTIVIDAD_CHOICES = [
        ('preventivo', 'Mantenimiento Preventivo'),
        ('correctivo', 'Mantenimiento Correctivo'),
        ('limpieza', 'Limpieza'),
        ('inspeccion', 'Inspección'),
        ('calibracion', 'Calibración'),
        ('emergencia', 'Emergencia'),
        ('garantia', 'Garantía'),
    ]
    
    ESTADO_CHOICES = [
        ('programada', 'Programada'),
        ('asignada', 'Asignada'),
        ('en_proceso', 'En Proceso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('reprogramada', 'Reprogramada'),
        ('pendiente', 'Pendiente'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
        ('emergencia', 'Emergencia'),
    ]
    
    TIPO_INFORME_CHOICES = [
        ('unidades_paquetes_condensados', 'Mantenimiento Unidades Paquetes Condensados por Aire'),
        ('coleccion_polvo', 'Informe de Mantenimiento Colección de Polvo'),
        ('unidades_enfriador_agua', 'Informe de Mantenimiento Unidades Enfriador de Agua'),
        ('unidad_manejadora', 'Informe de Mantenimiento Unidad Manejadora'),
        ('unidades_fancoil', 'Mantenimiento Unidades Fancoil'),
        ('unidades_condensadoras', 'Mantenimiento Unidades Condensadoras'),
        ('ventilador_extraccion', 'Informe de Mantenimiento Ventilador de Extracción'),
        ('unidades_ventilacion', 'Informe de Mantenimiento Unidades de Ventilación'),
    ]
    
    # Código único de la actividad
    codigo_actividad = models.CharField('Código de Actividad', max_length=50, unique=True, editable=False)
    
    # Relaciones principales
    contrato = models.ForeignKey(ContratoMantenimiento, on_delete=models.CASCADE, related_name='actividades', verbose_name='Contrato')
    hoja_vida_equipo = models.ForeignKey(HojaVidaEquipo, on_delete=models.CASCADE, related_name='actividades_mantenimiento', verbose_name='Equipo')
    rutina_origen = models.ForeignKey(RutinaMantenimiento, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Rutina de Origen')
    
    # Información de la actividad
    tipo_actividad = models.CharField('Tipo de Actividad', max_length=30, choices=TIPO_ACTIVIDAD_CHOICES)
    titulo = models.CharField('Título', max_length=200, default='Actividad de Mantenimiento')
    descripcion = models.TextField('Descripción', default='')
    tipo_informe = models.CharField('Tipo de Informe', max_length=50, choices=TIPO_INFORME_CHOICES, null=True, blank=True)
    
    # Programación
    fecha_programada = models.DateTimeField('Fecha Programada')
    fecha_limite = models.DateTimeField('Fecha Límite', null=True, blank=True)
    duracion_estimada_horas = models.DecimalField('Duración Estimada (horas)', max_digits=4, decimal_places=2, default=1.0)
    
    # Asignación
    tecnico_asignado = models.ForeignKey('servicios.Tecnico', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Técnico Asignado')
    fecha_asignacion = models.DateTimeField('Fecha de Asignación', null=True, blank=True)
    
    # Estado y prioridad
    estado = models.CharField('Estado', max_length=20, choices=ESTADO_CHOICES, default='programada')
    prioridad = models.CharField('Prioridad', max_length=20, choices=PRIORIDAD_CHOICES, default='media')
    
    # Información de ejecución
    fecha_inicio_real = models.DateTimeField('Fecha de Inicio Real', null=True, blank=True)
    fecha_fin_real = models.DateTimeField('Fecha de Fin Real', null=True, blank=True)
    
    # Observaciones y seguimiento
    observaciones = models.TextField('Observaciones', blank=True)
    motivo_reprogramacion = models.TextField('Motivo de Reprogramación', blank=True)
    requiere_seguimiento = models.BooleanField('Requiere Seguimiento', default=False)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actividades_creadas')
    
    class Meta:
        verbose_name = 'Actividad de Mantenimiento'
        verbose_name_plural = 'Actividades de Mantenimiento'
        ordering = ['fecha_programada']
    
    def __str__(self):
        return f"{self.codigo_actividad} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        if not self.codigo_actividad:
            # Generar código único
            fecha_str = self.fecha_programada.strftime('%Y%m%d')
            tipo_inicial = self.tipo_actividad[0].upper()
            numero_secuencial = ActividadMantenimiento.objects.filter(
                fecha_programada__date=self.fecha_programada.date()
            ).count() + 1
            self.codigo_actividad = f"AM{fecha_str}{tipo_inicial}{numero_secuencial:03d}"
        
        super().save(*args, **kwargs)
    
    @property
    def atrasada(self):
        """Verifica si la actividad está atrasada"""
        return (
            self.estado in ['programada', 'asignada'] and 
            self.fecha_programada < timezone.now()
        )
    
    @property
    def dias_atraso(self):
        """Calcula días de atraso"""
        if self.atrasada:
            delta = timezone.now() - self.fecha_programada
            return delta.days
        return 0
    
    @property
    def duracion_real_horas(self):
        """Calcula la duración real en horas"""
        if self.fecha_inicio_real and self.fecha_fin_real:
            delta = self.fecha_fin_real - self.fecha_inicio_real
            return round(delta.total_seconds() / 3600, 2)
        return 0


class InformeMantenimiento(models.Model):
    """Informe de mantenimiento que documenta el técnico después de completar una actividad"""
    
    RESULTADO_CHOICES = [
        ('exitoso', 'Exitoso'),
        ('parcial', 'Parcial con Observaciones'),
        ('fallido', 'Fallido'),
        ('requiere_seguimiento', 'Requiere Seguimiento'),
        ('equipo_fuera_servicio', 'Equipo Fuera de Servicio'),
    ]
    
    # Relación con la actividad
    actividad = models.OneToOneField(ActividadMantenimiento, on_delete=models.CASCADE, related_name='informe', verbose_name='Actividad')
    
    # Información de ejecución
    tecnico_ejecutor = models.ForeignKey('servicios.Tecnico', on_delete=models.SET_NULL, null=True, verbose_name='Técnico Ejecutor')
    fecha_ejecucion = models.DateTimeField('Fecha de Ejecución')
    hora_inicio = models.TimeField('Hora de Inicio')
    hora_fin = models.TimeField('Hora de Fin')
    
    # Resultados del mantenimiento
    resultado = models.CharField('Resultado', max_length=30, choices=RESULTADO_CHOICES, default='exitoso')
    trabajos_realizados = models.TextField('Trabajos Realizados', help_text='Descripción detallada de los trabajos realizados', default='')
    problemas_encontrados = models.TextField('Problemas Encontrados', blank=True)
    soluciones_aplicadas = models.TextField('Soluciones Aplicadas', blank=True)
    
    # Estado del equipo después del mantenimiento
    estado_equipo_antes = models.CharField('Estado del Equipo Antes', max_length=200, blank=True)
    estado_equipo_despues = models.CharField('Estado del Equipo Después', max_length=200, blank=True)
    funcionamiento_optimo = models.BooleanField('Funcionamiento Óptimo', default=True)
    
    # Checklist realizado
    checklist_realizado = models.JSONField('Checklist Realizado', default=list, blank=True, help_text='Checklist de actividades completadas')
    
    # Materiales y repuestos utilizados
    materiales_utilizados = models.TextField('Materiales Utilizados', blank=True, help_text='Lista de materiales utilizados')
    repuestos_cambiados = models.TextField('Repuestos Cambiados', blank=True, help_text='Lista de repuestos cambiados')
    costo_materiales = models.DecimalField('Costo de Materiales', max_digits=10, decimal_places=2, default=0)
    costo_repuestos = models.DecimalField('Costo de Repuestos', max_digits=10, decimal_places=2, default=0)
    
    # Recomendaciones y seguimiento
    recomendaciones = models.TextField('Recomendaciones', blank=True)
    proxima_revision = models.DateField('Próxima Revisión', null=True, blank=True)
    trabajos_pendientes = models.TextField('Trabajos Pendientes', blank=True)
    requiere_repuestos = models.BooleanField('Requiere Repuestos', default=False)
    repuestos_requeridos = models.TextField('Repuestos Requeridos', blank=True)
    
    # Satisfacción del cliente
    cliente_presente = models.BooleanField('Cliente Presente', default=False)
    nombre_cliente_receptor = models.CharField('Nombre de quien Recibe', max_length=200, blank=True)
    cargo_cliente_receptor = models.CharField('Cargo de quien Recibe', max_length=100, blank=True)
    satisfaccion_cliente = models.CharField('Satisfacción del Cliente', max_length=20, choices=[
        ('muy_satisfecho', 'Muy Satisfecho'),
        ('satisfecho', 'Satisfecho'),
        ('insatisfecho', 'Insatisfecho'),
        ('muy_insatisfecho', 'Muy Insatisfecho'),
    ], blank=True)
    observaciones_cliente = models.TextField('Observaciones del Cliente', blank=True)
    
    # Firmas digitales
    firma_tecnico = models.ImageField('Firma del Técnico', upload_to='mantenimiento/firmas/tecnicos/', blank=True)
    firma_cliente = models.ImageField('Firma del Cliente', upload_to='mantenimiento/firmas/clientes/', blank=True)
    
    # Evidencias fotográficas
    foto_antes_1 = models.ImageField('Foto Antes 1', upload_to='mantenimiento/evidencias/antes/', blank=True)
    foto_antes_2 = models.ImageField('Foto Antes 2', upload_to='mantenimiento/evidencias/antes/', blank=True)
    foto_despues_1 = models.ImageField('Foto Después 1', upload_to='mantenimiento/evidencias/despues/', blank=True)
    foto_despues_2 = models.ImageField('Foto Después 2', upload_to='mantenimiento/evidencias/despues/', blank=True)
    
    # Observaciones finales
    observaciones_tecnicas = models.TextField('Observaciones Técnicas', blank=True)
    observaciones_adicionales = models.TextField('Observaciones Adicionales', blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Informe de Mantenimiento'
        verbose_name_plural = 'Informes de Mantenimiento'
        ordering = ['-fecha_ejecucion']
    
    def __str__(self):
        return f"Informe {self.actividad.codigo_actividad} - {self.fecha_ejecucion.strftime('%d/%m/%Y')}"
    
    @property
    def duracion_horas(self):
        """Calcula la duración del trabajo en horas"""
        if self.hora_inicio and self.hora_fin:
            from datetime import datetime, timedelta
            inicio = datetime.combine(datetime.today(), self.hora_inicio)
            fin = datetime.combine(datetime.today(), self.hora_fin)
            if fin < inicio:  # Cruzó medianoche
                fin += timedelta(days=1)
            delta = fin - inicio
            return round(delta.total_seconds() / 3600, 2)
        return 0
    
    @property
    def costo_total(self):
        """Calcula el costo total del mantenimiento"""
        return self.costo_materiales + self.costo_repuestos


class AdjuntoInformeMantenimiento(models.Model):
    """Adjuntos adicionales para los informes de mantenimiento"""
    
    TIPO_ADJUNTO_CHOICES = [
        ('imagen', 'Imagen'),
        ('documento', 'Documento'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('plano', 'Plano'),
        ('manual', 'Manual'),
        ('factura', 'Factura'),
        ('otro', 'Otro'),
    ]
    
    informe = models.ForeignKey(InformeMantenimiento, on_delete=models.CASCADE, related_name='adjuntos', verbose_name='Informe')
    archivo = models.FileField('Archivo', upload_to='mantenimiento/adjuntos/%Y/%m/')
    nombre_original = models.CharField('Nombre Original', max_length=255)
    tipo_adjunto = models.CharField('Tipo de Adjunto', max_length=20, choices=TIPO_ADJUNTO_CHOICES)
    descripcion = models.CharField('Descripción', max_length=500, blank=True)
    tamaño_archivo = models.PositiveIntegerField('Tamaño (bytes)', null=True, blank=True)
    fecha_subida = models.DateTimeField('Fecha de Subida', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Adjunto de Informe'
        verbose_name_plural = 'Adjuntos de Informe'
        ordering = ['-fecha_subida']
    
    def __str__(self):
        return f"{self.informe.actividad.codigo_actividad} - {self.nombre_original}"
    
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


class InformeMantenimientoUnidadPaquete(models.Model):
    """Informe específico para Mantenimiento de Unidades Paquetes Condensados por Aire"""
    
    TIPO_MANTENIMIENTO_CHOICES = [
        ('preventivo', 'Mantenimiento Preventivo'),
        ('correctivo', 'Mantenimiento Correctivo'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('alta', 'ALTA'),
        ('baja', 'BAJA'),
    ]
    
    # Relación con actividad
    actividad = models.OneToOneField(
        ActividadMantenimiento, 
        on_delete=models.CASCADE, 
        related_name='informe_unidad_paquete',
        verbose_name='Actividad'
    )
    
    # 1. Información General del Equipo
    fecha = models.DateField('Fecha', default=timezone.now)
    marca = models.CharField('Marca', max_length=100)
    sistema_modelo = models.CharField('Sistema Modelo', max_length=100)
    equipo_serie = models.CharField('Equipo Serie', max_length=100)
    consecutivo = models.PositiveIntegerField('Consecutivo')
    usuario = models.CharField('Usuario', max_length=100)
    
    # 2. Tipo de Mantenimiento
    tipo_mantenimiento = models.CharField(
        'Tipo de Mantenimiento', 
        max_length=20, 
        choices=TIPO_MANTENIMIENTO_CHOICES
    )
    
    # 3. Voltaje en Tableros Eléctricos
    voltaje_l1_l2 = models.DecimalField('L1 y L2 (voltios)', max_digits=6, decimal_places=2, null=True, blank=True)
    voltaje_l2_l3 = models.DecimalField('L2 y L3 (voltios)', max_digits=6, decimal_places=2, null=True, blank=True)
    voltaje_l1_l3 = models.DecimalField('L1 y L3 (voltios)', max_digits=6, decimal_places=2, null=True, blank=True)
    
    # 4. Observaciones Previas al Mantenimiento
    observaciones_previas = models.TextField('Observaciones Previas al Mantenimiento', blank=True)
    
    # 5. Sección Evaporador - Actividades de Mantenimiento
    evap_lavado = models.BooleanField('Lavado', default=False)
    evap_desincrustante = models.BooleanField('Desincrustante', default=False)
    evap_limpieza_bandeja = models.BooleanField('Limpieza bandeja', default=False)
    evap_limpieza_drenaje = models.BooleanField('Limpieza drenaje', default=False)
    
    # Conjunto Motor Ventilador Evaporador
    evap_motor_limpieza_rotores = models.BooleanField('Limpieza rotores', default=False)
    evap_motor_lubricacion = models.BooleanField('Lubricación', default=False)
    evap_motor_rpm = models.BooleanField('R.P.M.', default=False)
    evap_motor_amperaje = models.BooleanField('Amperaje motor', default=False)
    evap_motor_limpieza_ejes = models.BooleanField('Limpieza ejes', default=False)
    
    # Campos numéricos Evaporador - Rangos Permitidos
    evap_nivel_aceite = models.DecimalField('Nivel Aceite', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_cambio_aceite = models.DecimalField('Cambio de Aceite', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_ajuste_control_capacidad = models.DecimalField('Ajuste control capacidad', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_amperaje_rla = models.DecimalField('Amperaje RLA', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_presion_succion = models.DecimalField('Presión Succión', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_presion_descarga = models.DecimalField('Presión descarga', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_limpieza = models.DecimalField('Limpieza', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_presostato_alta = models.DecimalField('Presostato de alta', max_digits=8, decimal_places=2, null=True, blank=True)
    evap_presostato_baja = models.DecimalField('Presostato de baja', max_digits=8, decimal_places=2, null=True, blank=True)
    
    # 6. Sección Condensador - Compresor No.1
    comp1_modelo = models.CharField('Compresor 1 - Modelo', max_length=100, blank=True)
    comp1_revision_placas_bornes = models.BooleanField('Revisión placas bornes', default=False)
    comp1_nivel_aceite = models.BooleanField('Nivel Aceite', default=False)
    comp1_cambio_aceite = models.BooleanField('Cambio de Aceite', default=False)
    comp1_ajuste_control_capacidad = models.BooleanField('Ajuste control capacidad', default=False)
    
    # Conjunto Motor Ventilador Condensador 1
    cond1_limpieza_rotores = models.BooleanField('Cond 1 - Limpieza rotores', default=False)
    cond1_lubricacion = models.BooleanField('Cond 1 - Lubricación', default=False)
    cond1_rpm = models.BooleanField('Cond 1 - R.P.M.', default=False)
    cond1_amperaje_motor = models.BooleanField('Cond 1 - Amperaje motor', default=False)
    cond1_limpieza_ejes = models.BooleanField('Cond 1 - Limpieza ejes', default=False)
    
    # Rangos permitidos Condensador 1
    cond1_nivel_aceite = models.DecimalField('Cond 1 - Nivel Aceite', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_cambio_aceite = models.DecimalField('Cond 1 - Cambio de Aceite', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_ajuste_control_capacidad = models.DecimalField('Cond 1 - Ajuste control capacidad', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_amperaje_rla = models.DecimalField('Cond 1 - Amperaje RLA', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_presion_succion = models.DecimalField('Cond 1 - Presión Succión', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_presion_descarga = models.DecimalField('Cond 1 - Presión descarga', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_limpieza = models.DecimalField('Cond 1 - Limpieza', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_presostato_alta = models.DecimalField('Cond 1 - Presostato de alta', max_digits=8, decimal_places=2, null=True, blank=True)
    cond1_presostato_baja = models.DecimalField('Cond 1 - Presostato de baja', max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Compresor No.2
    comp2_modelo = models.CharField('Compresor 2 - Modelo', max_length=100, blank=True)
    comp2_revision_placas_bornes = models.BooleanField('Comp 2 - Revisión placas bornes', default=False)
    comp2_nivel_aceite = models.BooleanField('Comp 2 - Nivel Aceite', default=False)
    comp2_cambio_aceite = models.BooleanField('Comp 2 - Cambio de Aceite', default=False)
    comp2_ajuste_control_capacidad = models.BooleanField('Comp 2 - Ajuste control capacidad', default=False)
    
    # Conjunto Motor Ventilador Condensador 2
    cond2_limpieza_rotores = models.BooleanField('Cond 2 - Limpieza rotores', default=False)
    cond2_lubricacion = models.BooleanField('Cond 2 - Lubricación', default=False)
    cond2_rpm = models.BooleanField('Cond 2 - R.P.M.', default=False)
    cond2_amperaje_motor = models.BooleanField('Cond 2 - Amperaje motor', default=False)
    cond2_limpieza_ejes = models.BooleanField('Cond 2 - Limpieza ejes', default=False)
    
    # Rangos permitidos Condensador 2
    cond2_nivel_aceite = models.DecimalField('Cond 2 - Nivel Aceite', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_cambio_aceite = models.DecimalField('Cond 2 - Cambio de Aceite', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_ajuste_control_capacidad = models.DecimalField('Cond 2 - Ajuste control capacidad', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_amperaje_rla = models.DecimalField('Cond 2 - Amperaje RLA', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_presion_succion = models.DecimalField('Cond 2 - Presión Succión', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_presion_descarga = models.DecimalField('Cond 2 - Presión descarga', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_limpieza = models.DecimalField('Cond 2 - Limpieza', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_presostato_alta = models.DecimalField('Cond 2 - Presostato de alta', max_digits=8, decimal_places=2, null=True, blank=True)
    cond2_presostato_baja = models.DecimalField('Cond 2 - Presostato de baja', max_digits=8, decimal_places=2, null=True, blank=True)
    
    # 7. Circuito de Refrigeración
    refrig_carga_refrigerante = models.BooleanField('Carga refrigerante', default=False)
    refrig_valvulas_solenoide = models.BooleanField('Válvulas Solenoide', default=False)
    refrig_aislamiento = models.BooleanField('Aislamiento', default=False)
    refrig_pruebas_escapes = models.BooleanField('Pruebas escapes', default=False)
    refrig_filtro_secador = models.BooleanField('Filtro Secador', default=False)
    refrig_valvula_expansion = models.BooleanField('Válvula de expansión', default=False)
    refrig_chequear_humedad = models.BooleanField('Chequear humedad', default=False)
    
    # 8. Sistema Eléctrico
    elect_limpieza_tablero = models.BooleanField('Limpieza tablero', default=False)
    elect_limpieza_contactor = models.BooleanField('Limpieza contactor', default=False)
    elect_operacion_timer = models.BooleanField('Operación Timer', default=False)
    elect_operacion_relevos = models.BooleanField('Operación Relevos', default=False)
    elect_revision_alambrado = models.BooleanField('Revisión alambrado', default=False)
    elect_operacion_termostato = models.BooleanField('Operación termostato', default=False)
    
    # 9. Observaciones Posteriores al Mantenimiento
    observaciones_posteriores = models.TextField('Observaciones Posteriores al Mantenimiento', blank=True)
    prioridad = models.CharField('Prioridad', max_length=10, choices=PRIORIDAD_CHOICES, default='baja')
    
    # 10. Firmas y Responsables
    ejecutado_por_nombre = models.CharField('Ejecutado por - Nombre', max_length=100, blank=True)
    ejecutado_por_fecha = models.DateField('Ejecutado por - Fecha', null=True, blank=True)
    ejecutado_por_firma = models.TextField('Ejecutado por - Firma', blank=True)
    
    supervisado_por_nombre = models.CharField('Supervisado por - Nombre', max_length=100, blank=True)
    supervisado_por_fecha = models.DateField('Supervisado por - Fecha', null=True, blank=True)
    supervisado_por_firma = models.TextField('Supervisado por - Firma', blank=True)
    
    recibido_por_nombre = models.CharField('Recibido por - Nombre', max_length=100, blank=True)
    recibido_por_fecha = models.DateField('Recibido por - Fecha', null=True, blank=True)
    recibido_por_firma = models.TextField('Recibido por - Firma', blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='informes_unidad_paquete_creados')
    
    class Meta:
        verbose_name = 'Informe Mantenimiento Unidad Paquete'
        verbose_name_plural = 'Informes Mantenimiento Unidades Paquete'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Informe Unidad Paquete - {self.actividad.codigo_actividad} - {self.fecha}"
    
    def save(self, *args, **kwargs):
        if not self.consecutivo:
            # Generar consecutivo automático
            ultimo_consecutivo = InformeMantenimientoUnidadPaquete.objects.filter(
                fecha__year=self.fecha.year
            ).order_by('-consecutivo').first()
            
            if ultimo_consecutivo:
                self.consecutivo = ultimo_consecutivo.consecutivo + 1
            else:
                self.consecutivo = 1
        
        super().save(*args, **kwargs)


class InformeMantenimientoColeccionPolvo(models.Model):
    """Informe específico para Mantenimiento de Colección de Polvo"""
    
    TIPO_MANTENIMIENTO_CHOICES = [
        ('preventivo', 'Mantenimiento Preventivo'),
        ('correctivo', 'Mantenimiento Correctivo'),
    ]
    
    PRIORIDAD_CHOICES = [
        ('alta', 'ALTA'),
        ('baja', 'BAJA'),
    ]
    
    # Relación con actividad
    actividad = models.OneToOneField(
        ActividadMantenimiento, 
        on_delete=models.CASCADE, 
        related_name='informe_coleccion_polvo',
        verbose_name='Actividad'
    )
    
    # 1. Header
    fecha = models.DateField('Fecha', default=timezone.now)
    marca = models.CharField('Marca', max_length=100)
    modelo = models.CharField('Modelo', max_length=100)
    serie = models.CharField('Serie', max_length=100)
    consecutivo = models.PositiveIntegerField('Consecutivo')
    cliente = models.CharField('Cliente', max_length=200)
    ubicacion = models.CharField('Ubicación', max_length=200)
    
    # 2. Tipo Mantenimiento
    tipo_mantenimiento = models.CharField('Tipo de Mantenimiento', max_length=20, choices=TIPO_MANTENIMIENTO_CHOICES)
    
    # 3. Voltaje Tableros
    voltaje_l1_l2 = models.DecimalField('Voltaje L1-L2', max_digits=6, decimal_places=2, null=True, blank=True)
    voltaje_l2_l3 = models.DecimalField('Voltaje L2-L3', max_digits=6, decimal_places=2, null=True, blank=True)
    voltaje_l1_l3 = models.DecimalField('Voltaje L1-L3', max_digits=6, decimal_places=2, null=True, blank=True)
    
    # 4. Observaciones Previas
    observaciones_previas = models.TextField('Observaciones Previas al Mantenimiento', blank=True)
    
    # 5. Conjunto Motor - Inspección Visual
    motor_inspeccion_bobinado = models.BooleanField('Inspección visual bobinado', default=False)
    motor_inspeccion_ventilador = models.BooleanField('Inspección visual ventilador', default=False)
    motor_inspeccion_transmision = models.BooleanField('Inspección visual transmisión', default=False)
    motor_inspeccion_carcasa = models.BooleanField('Inspección visual carcasa', default=False)
    motor_inspeccion_bornera = models.BooleanField('Inspección visual bornera', default=False)
    
    # 5. Conjunto Motor - Actividades
    motor_lubricacion_rodamientos = models.BooleanField('Lubricación rodamientos', default=False)
    motor_limpieza_ventilador = models.BooleanField('Limpieza ventilador', default=False)
    motor_limpieza_carcasa = models.BooleanField('Limpieza carcasa', default=False)
    motor_ajuste_transmision = models.BooleanField('Ajuste transmisión', default=False)
    motor_medicion_vibraciones = models.BooleanField('Medición vibraciones', default=False)
    motor_medicion_temperatura = models.BooleanField('Medición temperatura', default=False)
    
    # 5. Conjunto Motor - Mediciones
    motor_amperaje = models.DecimalField('Amperaje (A)', max_digits=6, decimal_places=2, null=True, blank=True)
    motor_voltaje = models.DecimalField('Voltaje (V)', max_digits=6, decimal_places=2, null=True, blank=True)
    motor_rpm = models.IntegerField('RPM', null=True, blank=True)
    motor_temperatura = models.DecimalField('Temperatura (°C)', max_digits=5, decimal_places=1, null=True, blank=True)
    motor_vibracion_horizontal = models.DecimalField('Vibración Horizontal (mm/s)', max_digits=5, decimal_places=2, null=True, blank=True)
    motor_vibracion_vertical = models.DecimalField('Vibración Vertical (mm/s)', max_digits=5, decimal_places=2, null=True, blank=True)
    motor_vibracion_axial = models.DecimalField('Vibración Axial (mm/s)', max_digits=5, decimal_places=2, null=True, blank=True)
    
    # 6. Colectores de Polvo 1 - Actividades
    colector1_limpieza_tolvas = models.BooleanField('Limpieza tolvas', default=False)
    colector1_revision_compuertas = models.BooleanField('Revisión compuertas', default=False)
    colector1_revision_ductos = models.BooleanField('Revisión ductos', default=False)
    colector1_revision_estructural = models.BooleanField('Revisión estructural', default=False)
    colector1_limpieza_estructura = models.BooleanField('Limpieza estructura', default=False)
    
    # 6. Colectores de Polvo 1 - Sistema de Filtros
    colector1_revision_filtros = models.BooleanField('Revisión filtros', default=False)
    colector1_cambio_filtros = models.BooleanField('Cambio filtros', default=False)
    colector1_limpieza_camara = models.BooleanField('Limpieza cámara filtros', default=False)
    colector1_revision_sellos = models.BooleanField('Revisión sellos', default=False)
    
    # 6. Colectores de Polvo 1 - Sistema de Limpieza
    colector1_revision_valvulas_pulso = models.BooleanField('Revisión válvulas pulso', default=False)
    colector1_prueba_secuencia = models.BooleanField('Prueba secuencia limpieza', default=False)
    colector1_revision_compresor_aire = models.BooleanField('Revisión compresor aire', default=False)
    colector1_revision_tanque_aire = models.BooleanField('Revisión tanque aire', default=False)
    
    # 6. Colectores de Polvo 1 - Mediciones
    colector1_presion_diferencial = models.DecimalField('Presión Diferencial (Pa)', max_digits=6, decimal_places=2, null=True, blank=True)
    colector1_presion_aire = models.DecimalField('Presión Aire (bar)', max_digits=5, decimal_places=2, null=True, blank=True)
    colector1_caudal_aire = models.DecimalField('Caudal Aire (m³/h)', max_digits=8, decimal_places=2, null=True, blank=True)
    
    # 7. Sistema Eléctrico
    elect_revision_tablero_principal = models.BooleanField('Revisión tablero principal', default=False)
    elect_limpieza_tablero = models.BooleanField('Limpieza tablero', default=False)
    elect_revision_contactores = models.BooleanField('Revisión contactores', default=False)
    elect_revision_relevos = models.BooleanField('Revisión relevos', default=False)
    elect_revision_fusibles = models.BooleanField('Revisión fusibles', default=False)
    elect_revision_alambrado = models.BooleanField('Revisión alambrado', default=False)
    elect_prueba_funcionamiento = models.BooleanField('Prueba funcionamiento', default=False)
    elect_medicion_resistencia = models.BooleanField('Medición resistencia aislamiento', default=False)
    
    # 8. Varios - Instrumentación
    varios_revision_manometros = models.BooleanField('Revisión manómetros', default=False)
    varios_calibracion_transmisores = models.BooleanField('Calibración transmisores', default=False)
    varios_revision_termometros = models.BooleanField('Revisión termómetros', default=False)
    varios_prueba_alarmas = models.BooleanField('Prueba alarmas', default=False)
    
    # 8. Varios - Sistema Control
    varios_revision_plc = models.BooleanField('Revisión PLC', default=False)
    varios_revision_hmi = models.BooleanField('Revisión HMI', default=False)
    varios_backup_programa = models.BooleanField('Backup programa', default=False)
    varios_actualizacion_parametros = models.BooleanField('Actualización parámetros', default=False)
    
    # 8. Varios - Seguridad
    varios_revision_paros_emergencia = models.BooleanField('Revisión paros emergencia', default=False)
    varios_revision_guardas = models.BooleanField('Revisión guardas', default=False)
    varios_revision_señalizacion = models.BooleanField('Revisión señalización', default=False)
    
    # 9. Observaciones Posteriores + Prioridad
    observaciones_posteriores = models.TextField('Observaciones Posteriores al Mantenimiento', blank=True)
    prioridad = models.CharField('Prioridad', max_length=10, choices=PRIORIDAD_CHOICES, default='baja')
    
    # 10. Firmas
    ejecutado_por_nombre = models.CharField('Ejecutado por - Nombre', max_length=100, blank=True)
    ejecutado_por_fecha = models.DateField('Ejecutado por - Fecha', null=True, blank=True)
    ejecutado_por_firma = models.TextField('Ejecutado por - Firma', blank=True)
    
    supervisado_por_nombre = models.CharField('Supervisado por - Nombre', max_length=100, blank=True)
    supervisado_por_fecha = models.DateField('Supervisado por - Fecha', null=True, blank=True)
    supervisado_por_firma = models.TextField('Supervisado por - Firma', blank=True)
    
    recibido_por_nombre = models.CharField('Recibido por - Nombre', max_length=100, blank=True)
    recibido_por_fecha = models.DateField('Recibido por - Fecha', null=True, blank=True)
    recibido_por_firma = models.TextField('Recibido por - Firma', blank=True)
    
    # Metadatos
    fecha_creacion = models.DateTimeField('Fecha de Creación', auto_now_add=True)
    fecha_actualizacion = models.DateTimeField('Fecha de Actualización', auto_now=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='informes_coleccion_polvo_creados')
    
    class Meta:
        verbose_name = 'Informe Mantenimiento Colección de Polvo'
        verbose_name_plural = 'Informes Mantenimiento Colección de Polvo'
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Informe Colección Polvo - {self.actividad.codigo_actividad} - {self.fecha}"
    
    def save(self, *args, **kwargs):
        if not self.consecutivo:
            # Generar consecutivo automático
            ultimo_consecutivo = InformeMantenimientoColeccionPolvo.objects.filter(
                fecha__year=self.fecha.year
            ).order_by('-consecutivo').first()
            
            if ultimo_consecutivo:
                self.consecutivo = ultimo_consecutivo.consecutivo + 1
            else:
                self.consecutivo = 1
        
        super().save(*args, **kwargs)