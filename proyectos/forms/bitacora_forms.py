from django import forms
from django.utils import timezone
from proyectos.models import Bitacora, Proyecto, Actividad, Colaborador


class BitacoraForm(forms.ModelForm):
    """Formulario para crear y editar bitácoras con todos los campos de Sesión 4"""
    
    class Meta:
        model = Bitacora
        fields = [
            'proyecto', 'actividad', 'subactividad', 'lider_trabajo', 'equipo',
            'fecha_planificada', 'fecha_ejecucion_real', 'estado', 'estado_validacion',
            'descripcion', 'duracion_horas', 'observaciones'
        ]
        
        widgets = {
            'fecha_planificada': forms.DateInput(
                attrs={
                    'type': 'date', 
                    'class': 'form-control',
                    'placeholder': 'Seleccionar fecha planificada'
                }
            ),
            'fecha_ejecucion_real': forms.DateInput(
                attrs={
                    'type': 'date', 
                    'class': 'form-control',
                    'placeholder': 'Seleccionar fecha real'
                }
            ),
            'subactividad': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre de la subactividad específica'
                }
            ),
            'descripcion': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Descripción detallada de la actividad realizada...'
                }
            ),
            'duracion_horas': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': '0.5',
                    'step': '0.5',
                    'placeholder': 'Ej: 8.0'
                }
            ),
            'observaciones': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Observaciones adicionales, notas importantes...'
                }
            ),
            'proyecto': forms.Select(attrs={'class': 'form-control'}),
            'actividad': forms.Select(attrs={'class': 'form-control'}),
            'lider_trabajo': forms.Select(attrs={'class': 'form-control'}),
            'equipo': forms.SelectMultiple(attrs={'class': 'form-control', 'size': 4}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'estado_validacion': forms.Select(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'proyecto': 'Proyecto',
            'actividad': 'Actividad Principal',
            'subactividad': 'Subactividad Específica',
            'lider_trabajo': 'Líder de Trabajo',
            'equipo': 'Equipo de Trabajo',
            'fecha_planificada': 'Fecha Planificada de Ejecución',
            'fecha_ejecucion_real': 'Fecha Real de Ejecución',
            'estado': 'Estado de la Actividad',
            'estado_validacion': 'Estado de Validación',
            'descripcion': 'Descripción de la Actividad',
            'duracion_horas': 'Duración (Horas)',
            'observaciones': 'Observaciones'
        }
        
        help_texts = {
            'fecha_planificada': 'Fecha en que se planificó ejecutar esta actividad',
            'fecha_ejecucion_real': 'Fecha en que realmente se ejecutó (dejar vacío si aún no se ejecuta)',
            'lider_trabajo': 'Persona responsable de liderar el equipo en esta actividad',
            'equipo': 'Seleccionar colaboradores que participan (mantener Ctrl para múltiple selección)',
            'estado': 'Estado actual de la actividad',
            'estado_validacion': 'Estado de validación por director e ingeniero',
            'duracion_horas': 'Tiempo estimado o real en horas (ej: 2.5)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar querysets iniciales
        self.fields['actividad'].queryset = Actividad.objects.none()
        
        # Si hay un proyecto seleccionado o en la instancia, cargar sus actividades
        if self.instance and self.instance.pk and self.instance.proyecto:
            self.fields['actividad'].queryset = Actividad.objects.filter(
                proyecto=self.instance.proyecto
            ).order_by('actividad')
        elif 'proyecto' in self.data:
            try:
                proyecto_id = int(self.data.get('proyecto'))
                self.fields['actividad'].queryset = Actividad.objects.filter(
                    proyecto_id=proyecto_id
                ).order_by('actividad')
            except (ValueError, TypeError):
                pass
        
        # Configurar valores por defecto para nuevas bitácoras
        if not self.instance.pk:
            self.fields['fecha_planificada'].initial = timezone.now().date()
            self.fields['estado'].initial = 'planeada'
            self.fields['estado_validacion'].initial = 'pendiente'

    def clean(self):
        cleaned_data = super().clean()
        fecha_planificada = cleaned_data.get('fecha_planificada')
        fecha_ejecucion_real = cleaned_data.get('fecha_ejecucion_real')
        estado = cleaned_data.get('estado')
        
        # Validaciones lógicas
        if fecha_ejecucion_real and fecha_planificada:
            if fecha_ejecucion_real < fecha_planificada:
                # Solo advertencia, no error
                pass
        
        # Si el estado es completada, debería tener fecha de ejecución real
        if estado == 'completada' and not fecha_ejecucion_real:
            cleaned_data['fecha_ejecucion_real'] = timezone.now().date()
        
        return cleaned_data


class BitacoraFirmaForm(forms.ModelForm):
    """Formulario especializado para firmas digitales"""
    
    firma_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Contraseña de Confirmación',
        help_text='Ingrese su contraseña para confirmar la firma digital'
    )
    
    comentarios_firma = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Comentarios de Validación',
        required=False,
        help_text='Comentarios opcionales sobre la validación'
    )
    
    class Meta:
        model = Bitacora
        fields = ['estado_validacion']
        
    def __init__(self, *args, user=None, rol=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.rol = rol  # 'director' o 'ingeniero'
        
        if rol == 'director':
            self.fields['estado_validacion'].choices = [
                ('validada_director', 'Validada por Director'),
                ('rechazada', 'Rechazada'),
            ]
        elif rol == 'ingeniero':
            self.fields['estado_validacion'].choices = [
                ('validada_ingeniero', 'Validada por Ingeniero'),
                ('rechazada', 'Rechazada'),
            ]

    def clean_firma_password(self):
        password = self.cleaned_data.get('firma_password')
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError('Contraseña incorrecta.')
        return password


class FiltroBitacorasForm(forms.Form):
    """Formulario para filtrar bitácoras"""
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.all(),
        required=False,
        empty_label="Todos los proyectos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + Bitacora.ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    estado_validacion = forms.ChoiceField(
        choices=[('', 'Todas las validaciones')] + Bitacora.ESTADO_VALIDACION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    urgencia = forms.ChoiceField(
        choices=[
            ('', 'Todas las urgencias'),
            ('urgente', 'Requiere registro urgente'),
            ('normal', 'Sin urgencia'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    responsable = forms.ModelChoiceField(
        queryset=Colaborador.objects.all(),
        required=False,
        empty_label="Todos los responsables",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )