from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer fecha_entrega obligatoria
        self.fields['fecha_entrega'].required = True
        
        # Mejorar widget de fecha si no tiene fecha asignada
        if not self.instance.fecha_entrega:
            self.fields['fecha_entrega'].widget.attrs.update({
                'min': timezone.now().date().strftime('%Y-%m-%d')
            })

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get('estado')
        archivo = cleaned_data.get('archivo')
        fecha_entrega = cleaned_data.get('fecha_entrega')
        
        # Fecha de entrega es obligatoria
        if not fecha_entrega:
            raise ValidationError({
                'fecha_entrega': 'La fecha de entrega es obligatoria.'
            })
        
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


class EntregablePersonalizadoForm(forms.ModelForm):
    """Formulario para crear entregables personalizados adicionales"""
    
    class Meta:
        model = EntregableProyecto
        fields = ['codigo', 'nombre', 'fase', 'creador', 'consolidador', 'medio', 'dossier_cliente', 'observaciones', 'fecha_entrega']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 5.0, A.1, CUSTOM-1',
                'pattern': r'^[A-Za-z0-9\.\-_]+$',
                'title': 'Solo letras, números, puntos, guiones y guiones bajos'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del entregable personalizado',
                'maxlength': 300
            }),
            'fase': forms.Select(attrs={
                'class': 'form-select'
            }),
            'creador': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Responsable de crear el entregable',
                'maxlength': 200
            }),
            'consolidador': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Responsable de consolidar el entregable',
                'maxlength': 200
            }),
            'medio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Digital, Físico, Digital/Físico',
                'maxlength': 50
            }),
            'dossier_cliente': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Observaciones adicionales sobre este entregable...'
            }),
            'fecha_entrega': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            })
        }
        labels = {
            'codigo': 'Código del Entregable *',
            'nombre': 'Nombre del Entregable *',
            'fase': 'Fase del Proyecto *',
            'creador': 'Responsable de Creación *',
            'consolidador': 'Responsable de Consolidación *',
            'medio': 'Medio de Entrega',
            'dossier_cliente': 'Incluir en Dossier del Cliente',
            'observaciones': 'Observaciones',
            'fecha_entrega': 'Fecha de Entrega Estimada *'
        }
        help_texts = {
            'codigo': 'Código único para identificar este entregable (no debe existir en el proyecto)',
            'nombre': 'Descripción clara del entregable personalizado',
            'fase': 'Seleccione en qué fase del proyecto se entregará',
            'creador': 'Persona o área responsable de crear este entregable',
            'consolidador': 'Persona o área responsable de la versión final',
            'medio': 'Forma de entrega: Digital, Físico, etc.',
            'dossier_cliente': 'Marque si este entregable debe incluirse en el dossier final del cliente',
            'fecha_entrega': 'Fecha estimada de entrega del entregable'
        }

    def __init__(self, *args, proyecto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proyecto = proyecto
        
        # Hacer campos obligatorios
        self.fields['codigo'].required = True
        self.fields['nombre'].required = True
        self.fields['fase'].required = True
        self.fields['creador'].required = True
        self.fields['consolidador'].required = True
        self.fields['fecha_entrega'].required = True

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo and self.proyecto:
            # Verificar que el código no exista ya en el proyecto
            if EntregableProyecto.objects.filter(
                proyecto=self.proyecto, 
                codigo__iexact=codigo
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(
                    f'Ya existe un entregable con el código "{codigo}" en este proyecto.'
                )
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre and self.proyecto:
            # Verificar que el nombre no sea muy similar a uno existente
            if EntregableProyecto.objects.filter(
                proyecto=self.proyecto, 
                nombre__iexact=nombre
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError(
                    f'Ya existe un entregable con el nombre "{nombre}" en este proyecto.'
                )
        return nombre

    def save(self, commit=True):
        entregable = super().save(commit=False)
        if self.proyecto:
            entregable.proyecto = self.proyecto
        
        # Los entregables personalizados por defecto son opcionales
        entregable.obligatorio = False
        entregable.seleccionado = True  # Se seleccionan automáticamente al crear
        entregable.estado = 'pendiente'
        
        if commit:
            entregable.save()
        return entregable


class EntregableImportForm(forms.Form):
    """Formulario para importar entregables desde Excel"""
    
    proyecto = forms.ModelChoiceField(
        queryset=Proyecto.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Proyecto *',
        help_text='Seleccione el proyecto al que se agregarán los entregables'
    )
    
    archivo_excel = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls',
            'required': True
        }),
        label='Archivo Excel *',
        help_text='Archivo Excel con la estructura de entregables. Máximo 5MB.'
    )
    
    reemplazar_existentes = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Reemplazar entregables existentes',
        help_text='Si se marca, se actualizarán los entregables con códigos duplicados'
    )

    def clean_archivo_excel(self):
        archivo = self.cleaned_data.get('archivo_excel')
        if archivo:
            # Validar tamaño (5MB máximo)
            if archivo.size > 5 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 5MB.')
            
            # Validar extensión
            nombre_archivo = archivo.name.lower()
            if not (nombre_archivo.endswith('.xlsx') or nombre_archivo.endswith('.xls')):
                raise ValidationError('Solo se permiten archivos Excel (.xlsx, .xls)')
        
        return archivo