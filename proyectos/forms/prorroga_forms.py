from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from proyectos.models import ProrrogaProyecto, Proyecto


class ProrrogaProyectoForm(forms.ModelForm):
    """Formulario para solicitar prórrogas de proyecto"""
    
    class Meta:
        model = ProrrogaProyecto
        fields = [
            'fecha_fin_propuesta', 'tipo_prorroga', 'dias_extension', 'justificacion', 
            'documento_soporte'
        ]
        widgets = {
            'fecha_fin_propuesta': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                    'min': timezone.now().date().isoformat()
                }
            ),
            'tipo_prorroga': forms.Select(attrs={'class': 'form-select'}),
            'dias_extension': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '1',
                    'max': '365',
                    'placeholder': 'Número de días'
                }
            ),
            'justificacion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Describa detalladamente las razones que justifican la solicitud de prórroga...'
                }
            ),
            'documento_soporte': forms.FileInput(
                attrs={
                    'class': 'form-control',
                    'accept': '.pdf,.doc,.docx,.jpg,.png'
                }
            )
        }
        labels = {
            'fecha_fin_propuesta': 'Nueva Fecha de Finalización',
            'tipo_prorroga': 'Tipo de Prórroga',
            'dias_extension': 'Días de Extensión',
            'justificacion': 'Justificación Detallada',
            'documento_soporte': 'Documento de Soporte (Opcional)'
        }
        help_texts = {
            'fecha_fin_propuesta': 'Fecha propuesta para la nueva finalización del proyecto',
            'tipo_prorroga': 'Seleccione la razón principal de la solicitud de prórroga',
            'dias_extension': 'Número de días que se extenderá el proyecto (máximo 365 días)',
            'justificacion': 'Explique detalladamente las circunstancias que requieren la extensión del plazo',
            'documento_soporte': 'Adjunte documentos que respalden la solicitud (cartas, cotizaciones, etc.)'
        }
    
    def __init__(self, *args, **kwargs):
        self.proyecto = kwargs.pop('proyecto', None)
        super().__init__(*args, **kwargs)
        
        # Make fecha_fin_propuesta optional since we can calculate it from dias_extension
        self.fields['fecha_fin_propuesta'].required = False
        
        if self.proyecto:
            # Establecer la fecha fin original automáticamente
            self.initial['fecha_fin_original'] = self.proyecto.fecha_fin
            
            # Configurar fecha mínima como la fecha fin actual del proyecto
            self.fields['fecha_fin_propuesta'].widget.attrs['min'] = self.proyecto.fecha_fin.isoformat()
            
            # Personalizar el help text con información del proyecto
            fecha_actual = self.proyecto.fecha_fin.strftime('%d/%m/%Y')
            self.fields['fecha_fin_propuesta'].help_text = (
                f'Fecha actual de finalización: {fecha_actual}. '
                f'La nueva fecha debe ser posterior a esta.'
            )
    
    def clean_fecha_fin_propuesta(self):
        fecha_propuesta = self.cleaned_data.get('fecha_fin_propuesta')
        
        # Only validate if fecha_propuesta is provided (since it's optional now)
        if not fecha_propuesta:
            return fecha_propuesta
        
        if self.proyecto:
            # Validar que la nueva fecha sea posterior a la fecha fin actual
            if fecha_propuesta <= self.proyecto.fecha_fin:
                raise ValidationError(
                    f'La nueva fecha debe ser posterior a la fecha actual de finalización '
                    f'({self.proyecto.fecha_fin.strftime("%d/%m/%Y")})'
                )
            
            # Validar que la extensión no sea excesiva (máximo 1 año)
            diferencia = fecha_propuesta - self.proyecto.fecha_fin
            if diferencia.days > 365:
                raise ValidationError(
                    'La extensión no puede ser mayor a 365 días. '
                    f'Días solicitados: {diferencia.days}'
                )
            
            # Validar que la extensión sea razonable (mínimo 1 día)
            if diferencia.days < 1:
                raise ValidationError('La extensión debe ser de al menos 1 día.')
        
        return fecha_propuesta
    
    def clean_justificacion(self):
        justificacion = self.cleaned_data.get('justificacion', '').strip()
        
        if not justificacion:
            raise ValidationError('La justificación es obligatoria.')
        
        if len(justificacion) < 50:
            raise ValidationError(
                'La justificación debe tener al menos 50 caracteres. '
                f'Actual: {len(justificacion)} caracteres.'
            )
        
        return justificacion
    
    def clean_dias_extension(self):
        dias = self.cleaned_data.get('dias_extension')
        
        if dias is not None:
            if dias < 1:
                raise ValidationError('Los días de extensión deben ser al menos 1.')
            if dias > 365:
                raise ValidationError('Los días de extensión no pueden exceder 365 días.')
        
        return dias
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_propuesta = cleaned_data.get('fecha_fin_propuesta')
        dias_extension = cleaned_data.get('dias_extension')
        
        # Validar que se proporcione al menos uno de los dos campos
        if not fecha_propuesta and not dias_extension:
            raise ValidationError(
                'Debe proporcionar la nueva fecha de finalización o el número de días de extensión.'
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        prorroga = super().save(commit=False)
        
        if self.proyecto:
            prorroga.proyecto = self.proyecto
            prorroga.fecha_fin_original = self.proyecto.fecha_fin
            
            # Si se proporcionó fecha_fin_propuesta, calcular días de extensión
            if prorroga.fecha_fin_propuesta and prorroga.fecha_fin_original:
                delta = prorroga.fecha_fin_propuesta - prorroga.fecha_fin_original
                prorroga.dias_extension = delta.days
            # Si se proporcionaron días de extensión pero no fecha, calcular la fecha
            elif prorroga.dias_extension and prorroga.fecha_fin_original and not prorroga.fecha_fin_propuesta:
                from datetime import timedelta
                prorroga.fecha_fin_propuesta = prorroga.fecha_fin_original + timedelta(days=prorroga.dias_extension)
        
        if commit:
            prorroga.save()
        
        return prorroga


class ProrrogaAprobacionForm(forms.ModelForm):
    """Formulario para aprobar o rechazar prórrogas"""
    
    DECISION_CHOICES = [
        ('', '--- Seleccione una decisión ---'),
        ('aprobada', 'Aprobar Prórroga'),
        ('rechazada', 'Rechazar Prórroga')
    ]
    
    decision = forms.ChoiceField(
        choices=[('aprobada', 'Aprobar Prórroga'), ('rechazada', 'Rechazar Prórroga')],
        widget=forms.RadioSelect(),
        label='Decisión'
    )
    
    class Meta:
        model = ProrrogaProyecto
        fields = ['aprobada_por', 'observaciones_aprobacion']
        widgets = {
            'aprobada_por': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre del responsable que aprueba/rechaza'
                }
            ),
            'observaciones_aprobacion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Observaciones sobre la decisión tomada...'
                }
            )
        }
        labels = {
            'aprobada_por': 'Aprobada/Rechazada por',
            'observaciones_aprobacion': 'Observaciones'
        }
    
    def clean_aprobada_por(self):
        aprobada_por = self.cleaned_data.get('aprobada_por', '').strip()
        
        if not aprobada_por:
            raise ValidationError('Debe especificar quién toma la decisión.')
        
        return aprobada_por
    
    def clean_decision(self):
        decision = self.cleaned_data.get('decision')
        
        if not decision:
            raise ValidationError('Debe seleccionar una decisión.')
        
        return decision
    
    def save(self, commit=True):
        prorroga = super().save(commit=False)
        
        # Establecer el estado basado en la decisión
        decision = self.cleaned_data.get('decision')
        if decision:
            prorroga.estado = decision
            prorroga.fecha_aprobacion = timezone.now()
        
        if commit:
            prorroga.save()
        
        return prorroga


class FiltroProrrogasForm(forms.Form):
    """Formulario para filtrar prórrogas"""
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.all(),
        required=False,
        empty_label="--- Todos los proyectos ---",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    estado = forms.ChoiceField(
        choices=[('', '--- Todos los estados ---')] + ProrrogaProyecto.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tipo_prorroga = forms.ChoiceField(
        choices=[('', '--- Todos los tipos ---')] + ProrrogaProyecto.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        ),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        ),
        label='Hasta'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError('La fecha "desde" no puede ser posterior a la fecha "hasta".')
        
        return cleaned_data