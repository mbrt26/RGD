from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, HTML, Submit, Button
from crispy_forms.bootstrap import FormActions

from .models import (
    Equipo, HojaVidaEquipo, RutinaMantenimiento, ContratoMantenimiento,
    ActividadMantenimiento, InformeMantenimiento, AdjuntoInformeMantenimiento
)
from crm.models import Cliente, Contacto, Trato, VersionCotizacion

User = get_user_model()


class EquipoForm(forms.ModelForm):
    """Formulario para gestión de equipos (base de datos de equipos)"""
    
    class Meta:
        model = Equipo
        fields = [
            'nombre', 'descripcion', 'categoria', 'marca', 'modelo',
            'capacidad_btu', 'voltaje', 'amperaje', 'refrigerante', 'peso_kg',
            'fabricante', 'pais_origen', 'vida_util_anos', 'activo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'capacidad_btu': forms.NumberInput(attrs={'step': '0.01'}),
            'peso_kg': forms.NumberInput(attrs={'step': '0.01'}),
            'vida_util_anos': forms.NumberInput(attrs={'min': 1, 'max': 50}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Información General',
                Row(
                    Column('nombre', css_class='form-group col-md-6 mb-0'),
                    Column('categoria', css_class='form-group col-md-6 mb-0'),
                ),
                'descripcion',
                Row(
                    Column('marca', css_class='form-group col-md-6 mb-0'),
                    Column('modelo', css_class='form-group col-md-6 mb-0'),
                ),
                'activo'
            ),
            Fieldset(
                'Especificaciones Técnicas',
                Row(
                    Column('capacidad_btu', css_class='form-group col-md-4 mb-0'),
                    Column('voltaje', css_class='form-group col-md-4 mb-0'),
                    Column('amperaje', css_class='form-group col-md-4 mb-0'),
                ),
                Row(
                    Column('refrigerante', css_class='form-group col-md-6 mb-0'),
                    Column('peso_kg', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Información del Fabricante',
                Row(
                    Column('fabricante', css_class='form-group col-md-6 mb-0'),
                    Column('pais_origen', css_class='form-group col-md-6 mb-0'),
                ),
                'vida_util_anos'
            ),
            FormActions(
                Submit('submit', 'Guardar Equipo', css_class='btn btn-primary'),
                Button('cancel', 'Cancelar', css_class='btn btn-secondary', onclick='history.back()'),
            )
        )


class HojaVidaEquipoForm(forms.ModelForm):
    """Formulario para hojas de vida de equipos instalados en clientes"""
    
    class Meta:
        model = HojaVidaEquipo
        fields = [
            'equipo', 'cliente', 'codigo_interno', 'numero_serie', 'tag_cliente',
            'fecha_instalacion', 'fecha_compra', 'fecha_garantia_fin', 'proveedor',
            'valor_compra', 'ubicacion_detallada', 'direccion_instalacion',
            'coordenadas_gps', 'estado', 'observaciones', 'condiciones_ambientales', 'activo'
        ]
        widgets = {
            'fecha_instalacion': forms.DateInput(attrs={'type': 'date'}),
            'fecha_compra': forms.DateInput(attrs={'type': 'date'}),
            'fecha_garantia_fin': forms.DateInput(attrs={'type': 'date'}),
            'valor_compra': forms.NumberInput(attrs={'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'condiciones_ambientales': forms.Textarea(attrs={'rows': 3}),
            'coordenadas_gps': forms.TextInput(attrs={'placeholder': 'Latitud, Longitud'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nombre')
        self.fields['equipo'].queryset = Equipo.objects.filter(activo=True).order_by('categoria', 'marca', 'modelo')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Información Básica',
                Row(
                    Column('equipo', css_class='form-group col-md-6 mb-0'),
                    Column('cliente', css_class='form-group col-md-6 mb-0'),
                ),
                Row(
                    Column('codigo_interno', css_class='form-group col-md-4 mb-0'),
                    Column('numero_serie', css_class='form-group col-md-4 mb-0'),
                    Column('tag_cliente', css_class='form-group col-md-4 mb-0'),
                ),
                Row(
                    Column('estado', css_class='form-group col-md-6 mb-0'),
                    Column('activo', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Información de Instalación',
                Row(
                    Column('fecha_instalacion', css_class='form-group col-md-4 mb-0'),
                    Column('fecha_compra', css_class='form-group col-md-4 mb-0'),
                    Column('fecha_garantia_fin', css_class='form-group col-md-4 mb-0'),
                ),
                Row(
                    Column('proveedor', css_class='form-group col-md-6 mb-0'),
                    Column('valor_compra', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Ubicación',
                'ubicacion_detallada',
                'direccion_instalacion',
                'coordenadas_gps'
            ),
            Fieldset(
                'Observaciones',
                'observaciones',
                'condiciones_ambientales'
            ),
            FormActions(
                Submit('submit', 'Guardar Hoja de Vida', css_class='btn btn-primary'),
                Button('cancel', 'Cancelar', css_class='btn btn-secondary', onclick='history.back()'),
            )
        )


class RutinaMantenimientoForm(forms.ModelForm):
    """Formulario para rutinas de mantenimiento por equipo del cliente"""
    
    class Meta:
        model = RutinaMantenimiento
        fields = [
            'hoja_vida_equipo', 'nombre_rutina', 'tipo_rutina', 'descripcion',
            'frecuencia', 'dias_intervalo', 'duracion_estimada_horas',
            'requiere_parada_equipo', 'requiere_tecnico_especializado',
            'materiales_necesarios', 'herramientas_necesarias',
            'checklist_actividades', 'prioridad', 'observaciones', 'activa'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'duracion_estimada_horas': forms.NumberInput(attrs={'step': '0.1', 'min': 0.1}),
            'dias_intervalo': forms.NumberInput(attrs={'min': 1}),
            'materiales_necesarios': forms.Textarea(attrs={'rows': 3}),
            'herramientas_necesarias': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'checklist_actividades': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Ingrese cada actividad en una línea separada'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hoja_vida_equipo'].queryset = HojaVidaEquipo.objects.filter(activo=True).select_related('equipo', 'cliente').order_by('cliente__nombre', 'codigo_interno')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Información Básica',
                'hoja_vida_equipo',
                Row(
                    Column('nombre_rutina', css_class='form-group col-md-6 mb-0'),
                    Column('tipo_rutina', css_class='form-group col-md-6 mb-0'),
                ),
                'descripcion',
                Row(
                    Column('prioridad', css_class='form-group col-md-6 mb-0'),
                    Column('activa', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Programación',
                Row(
                    Column('frecuencia', css_class='form-group col-md-6 mb-0'),
                    Column('dias_intervalo', css_class='form-group col-md-6 mb-0'),
                ),
                HTML('<small class="text-muted">El campo "Días de Intervalo" solo se usa si selecciona frecuencia "Personalizada"</small><br><br>'),
                'duracion_estimada_horas'
            ),
            Fieldset(
                'Configuración de Ejecución',
                Row(
                    Column('requiere_parada_equipo', css_class='form-group col-md-6 mb-0'),
                    Column('requiere_tecnico_especializado', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Recursos Necesarios',
                'materiales_necesarios',
                'herramientas_necesarias'
            ),
            Fieldset(
                'Checklist de Actividades',
                'checklist_actividades'
            ),
            Fieldset(
                'Observaciones',
                'observaciones'
            ),
            FormActions(
                Submit('submit', 'Guardar Rutina', css_class='btn btn-primary'),
                Button('cancel', 'Cancelar', css_class='btn btn-secondary', onclick='history.back()'),
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        frecuencia = cleaned_data.get('frecuencia')
        dias_intervalo = cleaned_data.get('dias_intervalo')
        
        if frecuencia == 'personalizada' and not dias_intervalo:
            raise forms.ValidationError('Debe especificar los días de intervalo para frecuencia personalizada.')
        
        return cleaned_data


class ContratoMantenimientoForm(forms.ModelForm):
    """Formulario para contratos de mantenimiento con integración CRM"""
    
    class Meta:
        model = ContratoMantenimiento
        fields = [
            'trato_origen', 'cotizacion_aprobada', 'cliente', 'nombre_contrato',
            'tipo_contrato', 'fecha_inicio', 'fecha_fin', 'meses_duracion',
            'renovacion_automatica', 'valor_mensual', 'valor_total_contrato',
            'incluye_materiales', 'incluye_repuestos', 'valor_hora_adicional',
            'tiempo_respuesta_horas', 'horas_incluidas_mes', 'disponibilidad_24_7',
            'contacto_cliente', 'responsable_tecnico', 'equipos_incluidos',
            'condiciones_especiales', 'observaciones', 'clausulas_adicionales'
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'valor_mensual': forms.NumberInput(attrs={'step': '0.01'}),
            'valor_total_contrato': forms.NumberInput(attrs={'step': '0.01'}),
            'valor_hora_adicional': forms.NumberInput(attrs={'step': '0.01'}),
            'condiciones_especiales': forms.Textarea(attrs={'rows': 4}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'clausulas_adicionales': forms.Textarea(attrs={'rows': 4}),
            'equipos_incluidos': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nombre')
        self.fields['trato_origen'].queryset = Trato.objects.all().order_by('-fecha_creacion')
        self.fields['cotizacion_aprobada'].queryset = VersionCotizacion.objects.all().order_by('-fecha_creacion')
        self.fields['contacto_cliente'].queryset = Contacto.objects.all().order_by('nombre')
        
        # Filtrar equipos por cliente si está especificado
        if self.instance.pk and self.instance.cliente:
            self.fields['equipos_incluidos'].queryset = HojaVidaEquipo.objects.filter(
                cliente=self.instance.cliente, activo=True
            ).order_by('codigo_interno')
        else:
            self.fields['equipos_incluidos'].queryset = HojaVidaEquipo.objects.filter(activo=True).order_by('cliente__nombre', 'codigo_interno')
            
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Integración CRM',
                Row(
                    Column('trato_origen', css_class='form-group col-md-6 mb-0'),
                    Column('cotizacion_aprobada', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Información del Contrato',
                Row(
                    Column('cliente', css_class='form-group col-md-6 mb-0'),
                    Column('tipo_contrato', css_class='form-group col-md-6 mb-0'),
                ),
                'nombre_contrato'
            ),
            Fieldset(
                'Vigencia',
                Row(
                    Column('fecha_inicio', css_class='form-group col-md-4 mb-0'),
                    Column('fecha_fin', css_class='form-group col-md-4 mb-0'),
                    Column('meses_duracion', css_class='form-group col-md-4 mb-0'),
                ),
                'renovacion_automatica'
            ),
            Fieldset(
                'Términos Económicos',
                Row(
                    Column('valor_mensual', css_class='form-group col-md-6 mb-0'),
                    Column('valor_total_contrato', css_class='form-group col-md-6 mb-0'),
                ),
                Row(
                    Column('incluye_materiales', css_class='form-group col-md-4 mb-0'),
                    Column('incluye_repuestos', css_class='form-group col-md-4 mb-0'),
                    Column('valor_hora_adicional', css_class='form-group col-md-4 mb-0'),
                ),
            ),
            Fieldset(
                'Condiciones de Servicio',
                Row(
                    Column('tiempo_respuesta_horas', css_class='form-group col-md-4 mb-0'),
                    Column('horas_incluidas_mes', css_class='form-group col-md-4 mb-0'),
                    Column('disponibilidad_24_7', css_class='form-group col-md-4 mb-0'),
                ),
            ),
            Fieldset(
                'Contactos y Responsables',
                Row(
                    Column('contacto_cliente', css_class='form-group col-md-6 mb-0'),
                    Column('responsable_tecnico', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Equipos Incluidos',
                'equipos_incluidos'
            ),
            Fieldset(
                'Información Adicional',
                'condiciones_especiales',
                'observaciones',
                'clausulas_adicionales'
            ),
            FormActions(
                Submit('submit', 'Guardar Contrato', css_class='btn btn-primary'),
                Button('cancel', 'Cancelar', css_class='btn btn-secondary', onclick='history.back()'),
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            raise forms.ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        
        return cleaned_data


class ActividadMantenimientoForm(forms.ModelForm):
    """Formulario para actividades de mantenimiento (tabla consolidada)"""
    
    class Meta:
        model = ActividadMantenimiento
        fields = [
            'contrato', 'hoja_vida_equipo', 'rutina_origen', 'tipo_actividad',
            'titulo', 'descripcion', 'fecha_programada', 'fecha_limite',
            'duracion_estimada_horas', 'prioridad', 'tecnico_asignado',
            'observaciones'
        ]
        widgets = {
            'fecha_programada': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'fecha_limite': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duracion_estimada_horas': forms.NumberInput(attrs={'step': '0.1', 'min': 0.1}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contrato'].queryset = ContratoMantenimiento.objects.filter(estado='activo').order_by('cliente__nombre', 'nombre_contrato')
        self.fields['hoja_vida_equipo'].queryset = HojaVidaEquipo.objects.filter(activo=True).select_related('equipo', 'cliente').order_by('cliente__nombre', 'codigo_interno')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Información Básica',
                Row(
                    Column('contrato', css_class='form-group col-md-6 mb-0'),
                    Column('hoja_vida_equipo', css_class='form-group col-md-6 mb-0'),
                ),
                Row(
                    Column('rutina_origen', css_class='form-group col-md-6 mb-0'),
                    Column('tipo_actividad', css_class='form-group col-md-6 mb-0'),
                ),
                'titulo',
                'descripcion'
            ),
            Fieldset(
                'Programación',
                Row(
                    Column('fecha_programada', css_class='form-group col-md-6 mb-0'),
                    Column('fecha_limite', css_class='form-group col-md-6 mb-0'),
                ),
                Row(
                    Column('duracion_estimada_horas', css_class='form-group col-md-6 mb-0'),
                    Column('prioridad', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Asignación',
                'tecnico_asignado'
            ),
            Fieldset(
                'Observaciones',
                'observaciones'
            ),
            FormActions(
                Submit('submit', 'Guardar Actividad', css_class='btn btn-primary'),
                Button('cancel', 'Cancelar', css_class='btn btn-secondary', onclick='history.back()'),
            )
        )


class InformeMantenimientoForm(forms.ModelForm):
    """Formulario para informes de mantenimiento que documenta el técnico"""
    
    class Meta:
        model = InformeMantenimiento
        fields = [
            'actividad', 'tecnico_ejecutor', 'fecha_ejecucion', 'hora_inicio', 'hora_fin',
            'resultado', 'trabajos_realizados', 'problemas_encontrados', 'soluciones_aplicadas',
            'estado_equipo_antes', 'estado_equipo_despues', 'funcionamiento_optimo',
            'materiales_utilizados', 'repuestos_cambiados', 'costo_materiales', 'costo_repuestos',
            'recomendaciones', 'proxima_revision', 'trabajos_pendientes',
            'requiere_repuestos', 'repuestos_requeridos', 'cliente_presente',
            'nombre_cliente_receptor', 'cargo_cliente_receptor', 'satisfaccion_cliente',
            'observaciones_cliente', 'observaciones_tecnicas', 'observaciones_adicionales'
        ]
        widgets = {
            'fecha_ejecucion': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
            'proxima_revision': forms.DateInput(attrs={'type': 'date'}),
            'costo_materiales': forms.NumberInput(attrs={'step': '0.01'}),
            'costo_repuestos': forms.NumberInput(attrs={'step': '0.01'}),
            'trabajos_realizados': forms.Textarea(attrs={'rows': 4}),
            'problemas_encontrados': forms.Textarea(attrs={'rows': 3}),
            'soluciones_aplicadas': forms.Textarea(attrs={'rows': 3}),
            'materiales_utilizados': forms.Textarea(attrs={'rows': 3}),
            'repuestos_cambiados': forms.Textarea(attrs={'rows': 3}),
            'recomendaciones': forms.Textarea(attrs={'rows': 3}),
            'trabajos_pendientes': forms.Textarea(attrs={'rows': 3}),
            'repuestos_requeridos': forms.Textarea(attrs={'rows': 3}),
            'observaciones_cliente': forms.Textarea(attrs={'rows': 3}),
            'observaciones_tecnicas': forms.Textarea(attrs={'rows': 3}),
            'observaciones_adicionales': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo mostrar actividades que no tienen informe aún
        self.fields['actividad'].queryset = ActividadMantenimiento.objects.filter(
            informe__isnull=True,
            estado__in=['en_proceso', 'completada']
        ).select_related('hoja_vida_equipo', 'hoja_vida_equipo__cliente').order_by('-fecha_programada')
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Información de la Actividad',
                Row(
                    Column('actividad', css_class='form-group col-md-6 mb-0'),
                    Column('tecnico_ejecutor', css_class='form-group col-md-6 mb-0'),
                ),
                Row(
                    Column('fecha_ejecucion', css_class='form-group col-md-4 mb-0'),
                    Column('hora_inicio', css_class='form-group col-md-4 mb-0'),
                    Column('hora_fin', css_class='form-group col-md-4 mb-0'),
                ),
            ),
            Fieldset(
                'Resultados del Mantenimiento',
                'resultado',
                'trabajos_realizados',
                Row(
                    Column('problemas_encontrados', css_class='form-group col-md-6 mb-0'),
                    Column('soluciones_aplicadas', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Estado del Equipo',
                Row(
                    Column('estado_equipo_antes', css_class='form-group col-md-6 mb-0'),
                    Column('estado_equipo_despues', css_class='form-group col-md-6 mb-0'),
                ),
                'funcionamiento_optimo'
            ),
            Fieldset(
                'Materiales y Repuestos',
                Row(
                    Column('materiales_utilizados', css_class='form-group col-md-6 mb-0'),
                    Column('repuestos_cambiados', css_class='form-group col-md-6 mb-0'),
                ),
                Row(
                    Column('costo_materiales', css_class='form-group col-md-6 mb-0'),
                    Column('costo_repuestos', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Recomendaciones y Seguimiento',
                'recomendaciones',
                Row(
                    Column('proxima_revision', css_class='form-group col-md-6 mb-0'),
                    Column('requiere_repuestos', css_class='form-group col-md-6 mb-0'),
                ),
                'trabajos_pendientes',
                'repuestos_requeridos'
            ),
            Fieldset(
                'Satisfacción del Cliente',
                Row(
                    Column('cliente_presente', css_class='form-group col-md-4 mb-0'),
                    Column('nombre_cliente_receptor', css_class='form-group col-md-4 mb-0'),
                    Column('cargo_cliente_receptor', css_class='form-group col-md-4 mb-0'),
                ),
                Row(
                    Column('satisfaccion_cliente', css_class='form-group col-md-6 mb-0'),
                    Column('observaciones_cliente', css_class='form-group col-md-6 mb-0'),
                ),
            ),
            Fieldset(
                'Observaciones Finales',
                'observaciones_tecnicas',
                'observaciones_adicionales'
            ),
            FormActions(
                Submit('submit', 'Guardar Informe', css_class='btn btn-primary'),
                Button('cancel', 'Cancelar', css_class='btn btn-secondary', onclick='history.back()'),
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        if hora_inicio and hora_fin and hora_fin <= hora_inicio:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio.')
        
        return cleaned_data


class AdjuntoInformeMantenimientoForm(forms.ModelForm):
    """Formulario para adjuntos de informes de mantenimiento"""
    
    class Meta:
        model = AdjuntoInformeMantenimiento
        fields = ['archivo', 'tipo_adjunto', 'descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={'placeholder': 'Descripción del archivo (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['archivo'].required = True


# Formsets para relaciones inline
AdjuntoInformeFormSet = inlineformset_factory(
    InformeMantenimiento,
    AdjuntoInformeMantenimiento,
    form=AdjuntoInformeMantenimientoForm,
    extra=1,
    can_delete=True,
    max_num=10
)


class FiltroActividadesForm(forms.Form):
    """Formulario para filtrar actividades de mantenimiento en la tabla consolidada"""
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by('nombre'),
        required=False,
        empty_label="Todos los clientes"
    )
    
    equipo = forms.ModelChoiceField(
        queryset=HojaVidaEquipo.objects.filter(activo=True).select_related('equipo', 'cliente').order_by('cliente__nombre', 'codigo_interno'),
        required=False,
        empty_label="Todos los equipos"
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + ActividadMantenimiento.ESTADO_CHOICES,
        required=False
    )
    
    tipo_actividad = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + ActividadMantenimiento.TIPO_ACTIVIDAD_CHOICES,
        required=False
    )
    
    prioridad = forms.ChoiceField(
        choices=[('', 'Todas las prioridades')] + ActividadMantenimiento.PRIORIDAD_CHOICES,
        required=False
    )
    
    fecha_desde = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    
    fecha_hasta = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    
    solo_atrasadas = forms.BooleanField(
        required=False,
        label="Solo actividades atrasadas"
    )
    
    solo_pendientes = forms.BooleanField(
        required=False,
        label="Solo actividades pendientes"
    )
    
    solo_ejecutadas = forms.BooleanField(
        required=False,
        label="Solo actividades ejecutadas"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('cliente', css_class='form-group col-md-3 mb-0'),
                Column('equipo', css_class='form-group col-md-3 mb-0'),
                Column('estado', css_class='form-group col-md-3 mb-0'),
                Column('tipo_actividad', css_class='form-group col-md-3 mb-0'),
            ),
            Row(
                Column('prioridad', css_class='form-group col-md-3 mb-0'),
                Column('fecha_desde', css_class='form-group col-md-3 mb-0'),
                Column('fecha_hasta', css_class='form-group col-md-3 mb-0'),
                Column(
                    HTML('<div class="form-group"><label>&nbsp;</label><br>'),
                    'solo_atrasadas',
                    'solo_pendientes', 
                    'solo_ejecutadas',
                    HTML('</div>'),
                    css_class='col-md-3 mb-0'
                ),
            ),
            FormActions(
                Submit('filtrar', 'Filtrar', css_class='btn btn-primary'),
                Button('limpiar', 'Limpiar Filtros', css_class='btn btn-secondary', onclick='window.location.href = window.location.pathname'),
            )
        )