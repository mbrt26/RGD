from django import forms
from django.core.exceptions import ValidationError
from ..models import EntregableProyecto, Proyecto

class EntregableProyectoForm(forms.ModelForm):
    """Formulario para editar entregables del proyecto"""
    
    class Meta:
        model = EntregableProyecto
        fields = ['estado', 'fecha_entrega', 'archivo', 'observaciones']
        widgets = {
            'estado': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_estado'
            }),
            'fecha_entrega': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_fecha_entrega'
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'id_archivo',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip,.rar'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ingrese observaciones sobre el entregable...',
                'id': 'id_observaciones'
            }),
        }
        labels = {
            'estado': 'Estado del Entregable',
            'fecha_entrega': 'Fecha de Entrega',
            'archivo': 'Archivo del Entregable',
            'observaciones': 'Observaciones',
        }
        help_texts = {
            'estado': 'Seleccione el estado actual del entregable',
            'fecha_entrega': 'Fecha en que se entregó o entregará el documento',
            'archivo': 'Suba el archivo correspondiente al entregable (máximo 10MB)',
            'observaciones': 'Comentarios adicionales sobre el entregable',
        }

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar tamaño (10MB máximo)
            if archivo.size > 10 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar extensión
            extensiones_permitidas = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                '.ppt', '.pptx', '.zip', '.rar', '.txt'
            ]
            nombre_archivo = archivo.name.lower()
            if not any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
                raise ValidationError(
                    'Tipo de archivo no permitido. '
                    'Extensiones permitidas: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ZIP, RAR, TXT'
                )
        return archivo

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        archivo = cleaned_data.get('archivo')
        
        # Si el estado es completado, debe haber un archivo
        if estado == 'completado':
            if not archivo and not self.instance.archivo:
                raise ValidationError({
                    'archivo': 'Para marcar como completado, debe subir un archivo.'
                })
        
        return cleaned_data


class ConfiguracionMasivaForm(forms.Form):
    """Formulario para configuración masiva de entregables"""
    
    ACCION_CHOICES = [
        ('', 'Seleccione una acción'),
        ('cambiar_estado', 'Cambiar Estado'),
        ('asignar_fecha', 'Asignar Fecha de Entrega'),
        ('marcar_seleccionados', 'Marcar como Seleccionados'),
        ('desmarcar_seleccionados', 'Desmarcar como Seleccionados'),
        ('cambiar_obligatorio', 'Cambiar Tipo (Obligatorio/Opcional)'),
    ]
    
    proyectos = forms.ModelMultipleChoiceField(
        queryset=Proyecto.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Proyectos'
    )
    
    fases = forms.MultipleChoiceField(
        choices=EntregableProyecto.PHASE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Fases'
    )
    
    entregables_especificos = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Códigos de entregables separados por comas (ej: 1.0, 2.1, 3.4)'
        }),
        required=False,
        label='Entregables Específicos (Códigos)',
        help_text='Opcional: especifique códigos de entregables separados por comas'
    )
    
    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Acción a Realizar'
    )
    
    # Campos condicionales según la acción
    nuevo_estado = forms.ChoiceField(
        choices=[('', 'Seleccione un estado')] + EntregableProyecto.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Nuevo Estado'
    )
    
    fecha_entrega = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Fecha de Entrega'
    )
    
    obligatorio = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        label='Marcar como Obligatorio'
    )

    def clean(self):
        cleaned_data = super().clean()
        accion = cleaned_data.get('accion')
        
        # Validar que al menos se seleccione un criterio de filtrado
        proyectos = cleaned_data.get('proyectos')
        fases = cleaned_data.get('fases')
        entregables_especificos = cleaned_data.get('entregables_especificos')
        
        if not proyectos and not fases and not entregables_especificos:
            raise ValidationError(
                'Debe seleccionar al menos un criterio: proyectos, fases o entregables específicos.'
            )
        
        # Validaciones específicas por acción
        if accion == 'cambiar_estado':
            if not cleaned_data.get('nuevo_estado'):
                raise ValidationError({'nuevo_estado': 'Debe seleccionar un nuevo estado.'})
        
        elif accion == 'asignar_fecha':
            if not cleaned_data.get('fecha_entrega'):
                raise ValidationError({'fecha_entrega': 'Debe especificar una fecha de entrega.'})
        
        return cleaned_data


class FiltroEntregablesForm(forms.Form):
    """Formulario para filtrar entregables en reportes y vistas"""
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label='Todos los proyectos',
        label='Proyecto'
    )
    
    fase = forms.ChoiceField(
        choices=[('', 'Todas las fases')] + EntregableProyecto.PHASE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Fase'
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + EntregableProyecto.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Estado'
    )
    
    obligatorio = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Obligatorios'),
            ('false', 'Opcionales')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Tipo'
    )
    
    con_archivo = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Con archivo'),
            ('false', 'Sin archivo')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label='Archivo'
    )
    
    fecha_desde = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Fecha Desde'
    )
    
    fecha_hasta = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Fecha Hasta'
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValidationError({
                'fecha_hasta': 'La fecha hasta debe ser posterior a la fecha desde.'
            })
        
        return cleaned_data