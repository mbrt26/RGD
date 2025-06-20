from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from proyectos.models import ComiteProyecto, ParticipanteComite, SeguimientoProyectoComite, Colaborador


class ComiteProyectoForm(forms.ModelForm):
    """Formulario para crear y editar comités de proyectos"""
    
    class Meta:
        model = ComiteProyecto
        fields = [
            'nombre', 'fecha_comite', 'tipo_comite', 'lugar', 'coordinador',
            'agenda', 'observaciones', 'estado'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Comité Semanal - Semana 25/2024'
            }),
            'fecha_comite': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'tipo_comite': forms.Select(attrs={
                'class': 'form-select'
            }),
            'lugar': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Sala de Juntas Principal, Microsoft Teams'
            }),
            'coordinador': forms.Select(attrs={
                'class': 'form-select'
            }),
            'agenda': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detalle la agenda del comité...'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones generales...'
            }),
            'estado': forms.Select(attrs={
                'class': 'form-select'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de coordinadores activos
        self.fields['coordinador'].queryset = Colaborador.objects.all().order_by('nombre')
        self.fields['coordinador'].empty_label = "Seleccionar coordinador..."
        
        # Si es un nuevo comité, ocultar el campo estado
        if not self.instance.pk:
            self.fields.pop('estado', None)
        
        # Configurar campos requeridos
        self.fields['nombre'].required = True
        self.fields['fecha_comite'].required = True
        
        # Configurar valores por defecto
        if not self.instance.pk:
            # Para nuevos comités, establecer fecha por defecto al próximo lunes
            from datetime import datetime, timedelta
            now = datetime.now()
            next_monday = now + timedelta(days=(7 - now.weekday()) % 7)
            next_monday = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
            self.fields['fecha_comite'].initial = next_monday
    
    def clean_fecha_comite(self):
        fecha_comite = self.cleaned_data.get('fecha_comite')
        
        if fecha_comite:
            # Solo validar fechas futuras para nuevos comités
            if not self.instance.pk and fecha_comite < timezone.now():
                raise ValidationError('La fecha del comité no puede ser en el pasado.')
        
        return fecha_comite
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        
        if nombre:
            # Validar que el nombre no esté duplicado
            query = ComiteProyecto.objects.filter(nombre__iexact=nombre)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            
            if query.exists():
                raise ValidationError('Ya existe un comité con este nombre.')
        
        return nombre


class ParticipanteComiteForm(forms.ModelForm):
    """Formulario para agregar participantes a un comité"""
    
    class Meta:
        model = ParticipanteComite
        fields = [
            'colaborador', 'tipo_participacion', 'rol_en_comite', 
            'estado_asistencia', 'observaciones'
        ]
        widgets = {
            'colaborador': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tipo_participacion': forms.Select(attrs={
                'class': 'form-select'
            }),
            'rol_en_comite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Presentador, Revisor, Observador'
            }),
            'estado_asistencia': forms.Select(attrs={
                'class': 'form-select'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones sobre la participación...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        comite = kwargs.pop('comite', None)
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de colaboradores
        self.fields['colaborador'].queryset = Colaborador.objects.all().order_by('nombre')
        self.fields['colaborador'].empty_label = "Seleccionar colaborador..."
        
        # Si hay un comité, excluir colaboradores ya participantes
        if comite:
            colaboradores_existentes = ParticipanteComite.objects.filter(
                comite=comite
            ).values_list('colaborador_id', flat=True)
            
            self.fields['colaborador'].queryset = self.fields['colaborador'].queryset.exclude(
                id__in=colaboradores_existentes
            )


class SeguimientoProyectoComiteForm(forms.ModelForm):
    """Formulario para editar el seguimiento de un proyecto en el comité"""
    
    class Meta:
        model = SeguimientoProyectoComite
        fields = [
            'estado_seguimiento', 'avance_reportado', 'logros_periodo',
            'dificultades', 'acciones_requeridas', 'responsable_reporte',
            'fecha_proximo_hito', 'presupuesto_ejecutado', 'observaciones',
            'orden_presentacion', 'tiempo_asignado', 'requiere_decision',
            'decision_tomada'
        ]
        widgets = {
            'estado_seguimiento': forms.Select(attrs={
                'class': 'form-select'
            }),
            'avance_reportado': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.01
            }),
            'logros_periodo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa los principales logros y avances desde el último comité...'
            }),
            'dificultades': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa los problemas, obstáculos o riesgos identificados...'
            }),
            'acciones_requeridas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Especifique las acciones concretas a tomar...'
            }),
            'responsable_reporte': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fecha_proximo_hito': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'presupuesto_ejecutado': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': 0.01
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observaciones adicionales...'
            }),
            'orden_presentacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'tiempo_asignado': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 5,
                'max': 60,
                'value': 10
            }),
            'requiere_decision': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'decision_tomada': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describa la decisión tomada por el comité...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de responsables
        self.fields['responsable_reporte'].queryset = Colaborador.objects.all().order_by('nombre')
        self.fields['responsable_reporte'].empty_label = "Seleccionar responsable..."
        
        # Configurar campos requeridos
        self.fields['estado_seguimiento'].required = True
        self.fields['avance_reportado'].required = True
        self.fields['logros_periodo'].required = True
        
        # Configurar valores por defecto si no existen
        if not self.instance.pk:
            self.fields['tiempo_asignado'].initial = 10
            self.fields['orden_presentacion'].initial = 1
    
    def clean_avance_reportado(self):
        avance = self.cleaned_data.get('avance_reportado')
        
        if avance is not None:
            if avance < 0 or avance > 100:
                raise ValidationError('El avance debe estar entre 0 y 100%.')
        
        return avance
    
    def clean_tiempo_asignado(self):
        tiempo = self.cleaned_data.get('tiempo_asignado')
        
        if tiempo is not None:
            if tiempo < 5 or tiempo > 60:
                raise ValidationError('El tiempo asignado debe estar entre 5 y 60 minutos.')
        
        return tiempo
    
    def clean_presupuesto_ejecutado(self):
        presupuesto = self.cleaned_data.get('presupuesto_ejecutado')
        
        if presupuesto is not None and presupuesto < 0:
            raise ValidationError('El presupuesto ejecutado no puede ser negativo.')
        
        return presupuesto
    
    def clean(self):
        cleaned_data = super().clean()
        requiere_decision = cleaned_data.get('requiere_decision')
        decision_tomada = cleaned_data.get('decision_tomada')
        
        # Si requiere decisión, validar que se haya especificado la decisión
        if requiere_decision and not decision_tomada:
            # No es error crítico, pero mostrar advertencia
            self.add_error('decision_tomada', 
                'Si el proyecto requiere decisión, especifique cuál fue tomada.')
        
        return cleaned_data


class BusquedaComiteForm(forms.Form):
    """Formulario para filtrar comités"""
    
    q = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, coordinador, lugar...'
        }),
        label='Buscar'
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + ComiteProyecto.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    tipo_comite = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + ComiteProyecto.TIPO_COMITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Comité'
    )
    
    coordinador = forms.ModelChoiceField(
        queryset=Colaborador.objects.all().order_by('nombre'),
        required=False,
        empty_label='Todos los coordinadores',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Coordinador'
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError('La fecha "desde" no puede ser posterior a la fecha "hasta".')
        
        return cleaned_data


class ImportarParticipantesForm(forms.Form):
    """Formulario para importar participantes masivamente"""
    
    archivo_excel = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        }),
        label='Archivo Excel',
        help_text='Suba un archivo Excel con las columnas: Nombre, Cargo, Email, Tipo Participación, Rol'
    )
    
    sobrescribir = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Sobrescribir participantes existentes',
        help_text='Si está marcado, reemplazará los participantes existentes'
    )
    
    def clean_archivo_excel(self):
        archivo = self.cleaned_data.get('archivo_excel')
        
        if archivo:
            if not archivo.name.endswith(('.xlsx', '.xls')):
                raise ValidationError('El archivo debe ser formato Excel (.xlsx o .xls)')
            
            if archivo.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError('El archivo no puede ser mayor a 5MB')
        
        return archivo