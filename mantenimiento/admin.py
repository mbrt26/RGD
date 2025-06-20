from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Equipo, HojaVidaEquipo, RutinaMantenimiento, ContratoMantenimiento,
    ActividadMantenimiento, InformeMantenimiento, AdjuntoInformeMantenimiento,
    InformeMantenimientoUnidadPaquete, InformeMantenimientoColeccionPolvo
)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'marca', 'modelo', 'categoria', 'activo', 'hojas_vida_count', 'fecha_creacion']
    list_filter = ['categoria', 'activo', 'marca', 'fabricante']
    search_fields = ['nombre', 'descripcion', 'marca', 'modelo', 'fabricante']
    
    fieldsets = (
        ('Información General', {
            'fields': ('nombre', 'descripcion', 'categoria', 'marca', 'modelo', 'activo')
        }),
        ('Especificaciones Técnicas', {
            'fields': ('capacidad_btu', 'voltaje', 'amperaje', 'refrigerante', 'peso_kg')
        }),
        ('Información del Fabricante', {
            'fields': ('fabricante', 'pais_origen', 'vida_util_anos'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def hojas_vida_count(self, obj):
        count = obj.hojas_vida.count()
        if count > 0:
            url = reverse('admin:mantenimiento_hojavidaequipo_changelist') + f'?equipo__id__exact={obj.id}'
            return format_html('<a href="{}">{} instalaciones</a>', url, count)
        return '0 instalaciones'
    hojas_vida_count.short_description = 'Instalaciones'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Nuevo equipo
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


class RutinaMantenimientoInline(admin.TabularInline):
    model = RutinaMantenimiento
    extra = 0
    fields = ['nombre_rutina', 'tipo_rutina', 'frecuencia', 'prioridad', 'activa']
    readonly_fields = ['fecha_creacion']


@admin.register(HojaVidaEquipo)
class HojaVidaEquipoAdmin(admin.ModelAdmin):
    list_display = ['codigo_interno', 'equipo', 'cliente', 'estado', 'fecha_instalacion', 'edad_anos_display', 'en_garantia_display']
    list_filter = ['estado', 'activo', 'equipo__categoria', 'cliente']
    search_fields = ['codigo_interno', 'numero_serie', 'tag_cliente', 'equipo__nombre', 'cliente__nombre']
    date_hierarchy = 'fecha_instalacion'
    inlines = [RutinaMantenimientoInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('equipo', 'cliente', 'codigo_interno', 'numero_serie', 'tag_cliente', 'estado', 'activo')
        }),
        ('Información de Instalación', {
            'fields': ('fecha_instalacion', 'fecha_compra', 'fecha_garantia_fin', 'proveedor', 'valor_compra')
        }),
        ('Ubicación', {
            'fields': ('ubicacion_detallada', 'direccion_instalacion', 'coordenadas_gps')
        }),
        ('Estado y Observaciones', {
            'fields': ('fecha_ultimo_servicio', 'observaciones', 'condiciones_ambientales'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def edad_anos_display(self, obj):
        edad = obj.edad_anos
        if edad >= 10:
            return format_html('<span style="color: red; font-weight: bold;">{} años</span>', edad)
        elif edad >= 5:
            return format_html('<span style="color: orange;">{} años</span>', edad)
        return f"{edad} años"
    edad_anos_display.short_description = 'Edad'
    
    def en_garantia_display(self, obj):
        if obj.en_garantia:
            return format_html('<span style="color: green; font-weight: bold;">✓ Sí</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    en_garantia_display.short_description = 'En Garantía'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(RutinaMantenimiento)
class RutinaMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['nombre_rutina', 'hoja_vida_equipo', 'tipo_rutina', 'frecuencia', 'prioridad', 'activa', 'duracion_estimada_horas']
    list_filter = ['tipo_rutina', 'frecuencia', 'prioridad', 'activa', 'requiere_parada_equipo', 'requiere_tecnico_especializado']
    search_fields = ['nombre_rutina', 'descripcion', 'hoja_vida_equipo__codigo_interno', 'hoja_vida_equipo__cliente__nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('hoja_vida_equipo', 'nombre_rutina', 'tipo_rutina', 'descripcion', 'activa')
        }),
        ('Programación', {
            'fields': ('frecuencia', 'dias_intervalo', 'prioridad')
        }),
        ('Configuración de Ejecución', {
            'fields': ('duracion_estimada_horas', 'requiere_parada_equipo', 'requiere_tecnico_especializado')
        }),
        ('Recursos Necesarios', {
            'fields': ('materiales_necesarios', 'herramientas_necesarias'),
            'classes': ('collapse',)
        }),
        ('Checklist', {
            'fields': ('checklist_actividades',),
            'classes': ('collapse',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContratoMantenimiento)
class ContratoMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['numero_contrato', 'cliente', 'tipo_contrato', 'fecha_inicio', 'fecha_fin', 'estado', 'vigente_display', 'valor_mensual', 'equipos_count']
    list_filter = ['tipo_contrato', 'estado', 'renovacion_automatica', 'incluye_materiales', 'incluye_repuestos']
    search_fields = ['numero_contrato', 'nombre_contrato', 'cliente__nombre']
    date_hierarchy = 'fecha_inicio'
    filter_horizontal = ['equipos_incluidos']
    
    fieldsets = (
        ('Integración CRM', {
            'fields': ('trato_origen', 'cotizacion_aprobada'),
            'classes': ('collapse',)
        }),
        ('Información del Contrato', {
            'fields': ('numero_contrato', 'cliente', 'nombre_contrato', 'tipo_contrato', 'estado')
        }),
        ('Vigencia', {
            'fields': ('fecha_inicio', 'fecha_fin', 'meses_duracion', 'renovacion_automatica')
        }),
        ('Términos Económicos', {
            'fields': ('valor_mensual', 'valor_total_contrato', 'valor_hora_adicional', 'incluye_materiales', 'incluye_repuestos')
        }),
        ('Equipos y Cobertura', {
            'fields': ('equipos_incluidos', 'tiempo_respuesta_horas', 'horas_incluidas_mes', 'disponibilidad_24_7')
        }),
        ('Contactos y Responsables', {
            'fields': ('contacto_cliente', 'responsable_tecnico'),
            'classes': ('collapse',)
        }),
        ('Información Adicional', {
            'fields': ('condiciones_especiales', 'observaciones', 'clausulas_adicionales'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def vigente_display(self, obj):
        if obj.vigente:
            return format_html('<span style="color: green; font-weight: bold;">✓ Vigente</span>')
        elif obj.dias_para_vencer is not None and obj.dias_para_vencer <= 30:
            return format_html('<span style="color: orange;">⚠️ Próximo a vencer</span>')
        return format_html('<span style="color: red;">✗ No Vigente</span>')
    vigente_display.short_description = 'Vigencia'
    
    def equipos_count(self, obj):
        return obj.get_equipos_count()
    equipos_count.short_description = 'Equipos'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(ActividadMantenimiento)
class ActividadMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['codigo_actividad', 'titulo', 'hoja_vida_equipo', 'tipo_actividad', 'fecha_programada', 'estado', 'prioridad', 'tecnico_asignado', 'estado_display']
    list_filter = ['tipo_actividad', 'estado', 'prioridad', 'tecnico_asignado', 'contrato']
    search_fields = ['codigo_actividad', 'titulo', 'descripcion', 'hoja_vida_equipo__codigo_interno', 'hoja_vida_equipo__cliente__nombre']
    date_hierarchy = 'fecha_programada'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('contrato', 'hoja_vida_equipo', 'rutina_origen', 'tipo_actividad', 'titulo', 'descripcion')
        }),
        ('Programación', {
            'fields': ('fecha_programada', 'fecha_limite', 'duracion_estimada_horas', 'prioridad')
        }),
        ('Asignación', {
            'fields': ('tecnico_asignado', 'fecha_asignacion', 'estado')
        }),
        ('Ejecución', {
            'fields': ('fecha_inicio_real', 'fecha_fin_real'),
            'classes': ('collapse',)
        }),
        ('Observaciones y Seguimiento', {
            'fields': ('observaciones', 'motivo_reprogramacion', 'requiere_seguimiento'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['codigo_actividad', 'fecha_creacion', 'fecha_actualizacion']
    
    def estado_display(self, obj):
        if obj.atrasada:
            return format_html('<span style="color: red; font-weight: bold;">⚠️ Atrasada ({} días)</span>', obj.dias_atraso)
        elif obj.estado == 'completada':
            return format_html('<span style="color: green;">✓ Completada</span>')
        elif obj.estado == 'en_proceso':
            return format_html('<span style="color: blue;">🔄 En Proceso</span>')
        return obj.get_estado_display()
    estado_display.short_description = 'Estado Actual'
    
    actions = ['marcar_asignada', 'marcar_en_proceso', 'marcar_completada']
    
    def marcar_asignada(self, request, queryset):
        updated = queryset.filter(estado='programada').update(estado='asignada')
        self.message_user(request, f'{updated} actividades marcadas como asignadas.')
    marcar_asignada.short_description = 'Marcar como asignadas'
    
    def marcar_en_proceso(self, request, queryset):
        updated = queryset.filter(estado__in=['programada', 'asignada']).update(estado='en_proceso')
        self.message_user(request, f'{updated} actividades marcadas como en proceso.')
    marcar_en_proceso.short_description = 'Marcar como en proceso'
    
    def marcar_completada(self, request, queryset):
        updated = queryset.filter(estado__in=['programada', 'asignada', 'en_proceso']).update(estado='completada')
        self.message_user(request, f'{updated} actividades marcadas como completadas.')
    marcar_completada.short_description = 'Marcar como completadas'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


class AdjuntoInformeMantenimientoInline(admin.TabularInline):
    model = AdjuntoInformeMantenimiento
    extra = 0
    fields = ['archivo', 'tipo_adjunto', 'descripcion']
    readonly_fields = ['nombre_original', 'tamaño_archivo', 'fecha_subida']


@admin.register(InformeMantenimientoUnidadPaquete)
class InformeMantenimientoUnidadPaqueteAdmin(admin.ModelAdmin):
    list_display = ['consecutivo', 'actividad', 'fecha', 'marca', 'sistema_modelo', 'tipo_mantenimiento', 'prioridad', 'fecha_creacion']
    list_filter = ['tipo_mantenimiento', 'prioridad', 'fecha', 'marca']
    search_fields = ['consecutivo', 'actividad__codigo_actividad', 'marca', 'sistema_modelo', 'equipo_serie', 'usuario']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información de la Actividad', {
            'fields': ('actividad',)
        }),
        ('Información General del Equipo', {
            'fields': ('fecha', 'marca', 'sistema_modelo', 'equipo_serie', 'consecutivo', 'usuario')
        }),
        ('Tipo de Mantenimiento', {
            'fields': ('tipo_mantenimiento',)
        }),
        ('Voltaje en Tableros Eléctricos', {
            'fields': ('voltaje_l1_l2', 'voltaje_l2_l3', 'voltaje_l1_l3'),
            'classes': ('collapse',)
        }),
        ('Observaciones Previas', {
            'fields': ('observaciones_previas',),
            'classes': ('collapse',)
        }),
        ('Sección Evaporador - Actividades', {
            'fields': (
                'evap_lavado', 'evap_desincrustante', 'evap_limpieza_bandeja', 'evap_limpieza_drenaje',
                'evap_motor_limpieza_rotores', 'evap_motor_lubricacion', 'evap_motor_rpm', 
                'evap_motor_amperaje', 'evap_motor_limpieza_ejes'
            ),
            'classes': ('collapse',)
        }),
        ('Sección Evaporador - Rangos Permitidos', {
            'fields': (
                'evap_nivel_aceite', 'evap_cambio_aceite', 'evap_ajuste_control_capacidad',
                'evap_amperaje_rla', 'evap_presion_succion', 'evap_presion_descarga',
                'evap_limpieza', 'evap_presostato_alta', 'evap_presostato_baja'
            ),
            'classes': ('collapse',)
        }),
        ('Compresor No.1', {
            'fields': (
                'comp1_modelo', 'comp1_revision_placas_bornes', 'comp1_nivel_aceite',
                'comp1_cambio_aceite', 'comp1_ajuste_control_capacidad'
            ),
            'classes': ('collapse',)
        }),
        ('Condensador 1', {
            'fields': (
                'cond1_limpieza_rotores', 'cond1_lubricacion', 'cond1_rpm',
                'cond1_amperaje_motor', 'cond1_limpieza_ejes',
                'cond1_nivel_aceite', 'cond1_cambio_aceite', 'cond1_ajuste_control_capacidad',
                'cond1_amperaje_rla', 'cond1_presion_succion', 'cond1_presion_descarga',
                'cond1_limpieza', 'cond1_presostato_alta', 'cond1_presostato_baja'
            ),
            'classes': ('collapse',)
        }),
        ('Compresor No.2', {
            'fields': (
                'comp2_modelo', 'comp2_revision_placas_bornes', 'comp2_nivel_aceite',
                'comp2_cambio_aceite', 'comp2_ajuste_control_capacidad'
            ),
            'classes': ('collapse',)
        }),
        ('Condensador 2', {
            'fields': (
                'cond2_limpieza_rotores', 'cond2_lubricacion', 'cond2_rpm',
                'cond2_amperaje_motor', 'cond2_limpieza_ejes',
                'cond2_nivel_aceite', 'cond2_cambio_aceite', 'cond2_ajuste_control_capacidad',
                'cond2_amperaje_rla', 'cond2_presion_succion', 'cond2_presion_descarga',
                'cond2_limpieza', 'cond2_presostato_alta', 'cond2_presostato_baja'
            ),
            'classes': ('collapse',)
        }),
        ('Circuito de Refrigeración', {
            'fields': (
                'refrig_carga_refrigerante', 'refrig_valvulas_solenoide', 'refrig_aislamiento',
                'refrig_pruebas_escapes', 'refrig_filtro_secador', 'refrig_valvula_expansion',
                'refrig_chequear_humedad'
            ),
            'classes': ('collapse',)
        }),
        ('Sistema Eléctrico', {
            'fields': (
                'elect_limpieza_tablero', 'elect_limpieza_contactor', 'elect_operacion_timer',
                'elect_operacion_relevos', 'elect_revision_alambrado', 'elect_operacion_termostato'
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones Posteriores', {
            'fields': ('observaciones_posteriores', 'prioridad'),
            'classes': ('collapse',)
        }),
        ('Firmas y Responsables', {
            'fields': (
                'ejecutado_por_nombre', 'ejecutado_por_fecha', 'ejecutado_por_firma',
                'supervisado_por_nombre', 'supervisado_por_fecha', 'supervisado_por_firma',
                'recibido_por_nombre', 'recibido_por_fecha', 'recibido_por_firma'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['consecutivo', 'fecha_creacion', 'fecha_actualizacion']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(InformeMantenimiento)
class InformeMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['actividad', 'tecnico_ejecutor', 'fecha_ejecucion', 'resultado', 'duracion_horas_display', 'costo_total', 'satisfaccion_cliente']
    list_filter = ['resultado', 'tecnico_ejecutor', 'funcionamiento_optimo', 'cliente_presente', 'satisfaccion_cliente']
    search_fields = ['actividad__codigo_actividad', 'actividad__hoja_vida_equipo__codigo_interno', 'tecnico_ejecutor__usuario__first_name', 'tecnico_ejecutor__usuario__last_name']
    date_hierarchy = 'fecha_ejecucion'
    inlines = [AdjuntoInformeMantenimientoInline]
    
    fieldsets = (
        ('Información de la Actividad', {
            'fields': ('actividad', 'tecnico_ejecutor', 'fecha_ejecucion', 'hora_inicio', 'hora_fin')
        }),
        ('Resultados del Mantenimiento', {
            'fields': ('resultado', 'trabajos_realizados', 'problemas_encontrados', 'soluciones_aplicadas')
        }),
        ('Estado del Equipo', {
            'fields': ('estado_equipo_antes', 'estado_equipo_despues', 'funcionamiento_optimo'),
            'classes': ('collapse',)
        }),
        ('Checklist y Materiales', {
            'fields': ('checklist_realizado', 'materiales_utilizados', 'repuestos_cambiados', 'costo_materiales', 'costo_repuestos'),
            'classes': ('collapse',)
        }),
        ('Recomendaciones y Seguimiento', {
            'fields': ('recomendaciones', 'proxima_revision', 'trabajos_pendientes', 'requiere_repuestos', 'repuestos_requeridos'),
            'classes': ('collapse',)
        }),
        ('Satisfacción del Cliente', {
            'fields': ('cliente_presente', 'nombre_cliente_receptor', 'cargo_cliente_receptor', 'satisfaccion_cliente', 'observaciones_cliente'),
            'classes': ('collapse',)
        }),
        ('Evidencias', {
            'fields': ('foto_antes_1', 'foto_antes_2', 'foto_despues_1', 'foto_despues_2'),
            'classes': ('collapse',)
        }),
        ('Firmas', {
            'fields': ('firma_tecnico', 'firma_cliente'),
            'classes': ('collapse',)
        }),
        ('Observaciones Finales', {
            'fields': ('observaciones_tecnicas', 'observaciones_adicionales'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def duracion_horas_display(self, obj):
        return f"{obj.duracion_horas} hrs"
    duracion_horas_display.short_description = 'Duración'


@admin.register(AdjuntoInformeMantenimiento)
class AdjuntoInformeMantenimientoAdmin(admin.ModelAdmin):
    list_display = ['informe', 'nombre_original', 'tipo_adjunto', 'tamaño_legible', 'fecha_subida']
    list_filter = ['tipo_adjunto', 'fecha_subida']
    search_fields = ['nombre_original', 'descripcion', 'informe__actividad__codigo_actividad']
    
    fieldsets = (
        ('Información del Adjunto', {
            'fields': ('informe', 'archivo', 'tipo_adjunto', 'descripcion')
        }),
        ('Metadatos', {
            'fields': ('nombre_original', 'tamaño_archivo', 'fecha_subida'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['nombre_original', 'tamaño_archivo', 'fecha_subida']


@admin.register(InformeMantenimientoColeccionPolvo)
class InformeMantenimientoColeccionPolvoAdmin(admin.ModelAdmin):
    list_display = ['consecutivo', 'actividad', 'fecha', 'marca', 'modelo', 'tipo_mantenimiento', 'prioridad', 'fecha_creacion']
    list_filter = ['tipo_mantenimiento', 'prioridad', 'fecha', 'marca']
    search_fields = ['consecutivo', 'actividad__codigo_actividad', 'marca', 'modelo', 'serie', 'cliente']
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información de la Actividad', {
            'fields': ('actividad',)
        }),
        ('Header', {
            'fields': ('fecha', 'marca', 'modelo', 'serie', 'consecutivo', 'cliente', 'ubicacion')
        }),
        ('Tipo de Mantenimiento', {
            'fields': ('tipo_mantenimiento',)
        }),
        ('Voltaje Tableros', {
            'fields': ('voltaje_l1_l2', 'voltaje_l2_l3', 'voltaje_l1_l3'),
            'classes': ('collapse',)
        }),
        ('Observaciones Previas', {
            'fields': ('observaciones_previas',),
            'classes': ('collapse',)
        }),
        ('Conjunto Motor - Inspección Visual', {
            'fields': (
                'motor_inspeccion_bobinado', 'motor_inspeccion_ventilador', 
                'motor_inspeccion_transmision', 'motor_inspeccion_carcasa', 'motor_inspeccion_bornera'
            ),
            'classes': ('collapse',)
        }),
        ('Conjunto Motor - Actividades', {
            'fields': (
                'motor_lubricacion_rodamientos', 'motor_limpieza_ventilador', 'motor_limpieza_carcasa',
                'motor_ajuste_transmision', 'motor_medicion_vibraciones', 'motor_medicion_temperatura'
            ),
            'classes': ('collapse',)
        }),
        ('Conjunto Motor - Mediciones', {
            'fields': (
                'motor_amperaje', 'motor_voltaje', 'motor_rpm', 'motor_temperatura',
                'motor_vibracion_horizontal', 'motor_vibracion_vertical', 'motor_vibracion_axial'
            ),
            'classes': ('collapse',)
        }),
        ('Colectores de Polvo 1 - Actividades', {
            'fields': (
                'colector1_limpieza_tolvas', 'colector1_revision_compuertas', 'colector1_revision_ductos',
                'colector1_revision_estructural', 'colector1_limpieza_estructura'
            ),
            'classes': ('collapse',)
        }),
        ('Colectores de Polvo 1 - Sistema de Filtros', {
            'fields': (
                'colector1_revision_filtros', 'colector1_cambio_filtros', 'colector1_limpieza_camara',
                'colector1_revision_sellos'
            ),
            'classes': ('collapse',)
        }),
        ('Colectores de Polvo 1 - Sistema de Limpieza', {
            'fields': (
                'colector1_revision_valvulas_pulso', 'colector1_prueba_secuencia', 
                'colector1_revision_compresor_aire', 'colector1_revision_tanque_aire'
            ),
            'classes': ('collapse',)
        }),
        ('Colectores de Polvo 1 - Mediciones', {
            'fields': (
                'colector1_presion_diferencial', 'colector1_presion_aire', 'colector1_caudal_aire'
            ),
            'classes': ('collapse',)
        }),
        ('Sistema Eléctrico', {
            'fields': (
                'elect_revision_tablero_principal', 'elect_limpieza_tablero', 'elect_revision_contactores',
                'elect_revision_relevos', 'elect_revision_fusibles', 'elect_revision_alambrado',
                'elect_prueba_funcionamiento', 'elect_medicion_resistencia'
            ),
            'classes': ('collapse',)
        }),
        ('Varios - Instrumentación', {
            'fields': (
                'varios_revision_manometros', 'varios_calibracion_transmisores', 
                'varios_revision_termometros', 'varios_prueba_alarmas'
            ),
            'classes': ('collapse',)
        }),
        ('Varios - Sistema Control', {
            'fields': (
                'varios_revision_plc', 'varios_revision_hmi', 'varios_backup_programa', 
                'varios_actualizacion_parametros'
            ),
            'classes': ('collapse',)
        }),
        ('Varios - Seguridad', {
            'fields': (
                'varios_revision_paros_emergencia', 'varios_revision_guardas', 'varios_revision_señalizacion'
            ),
            'classes': ('collapse',)
        }),
        ('Observaciones Posteriores', {
            'fields': ('observaciones_posteriores', 'prioridad'),
            'classes': ('collapse',)
        }),
        ('Firmas y Responsables', {
            'fields': (
                'ejecutado_por_nombre', 'ejecutado_por_fecha', 'ejecutado_por_firma',
                'supervisado_por_nombre', 'supervisado_por_fecha', 'supervisado_por_firma',
                'recibido_por_nombre', 'recibido_por_fecha', 'recibido_por_firma'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['consecutivo', 'fecha_creacion', 'fecha_actualizacion']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)

