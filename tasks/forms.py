from django import forms
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Button, Div, HTML
from crispy_forms.bootstrap import FormActions, Alert
from .models import Task, TaskCategory, TaskComment, TaskAttachment, TaskHistory, TaskImage, TaskAttachmentGroup

User = get_user_model()

class TaskForm(forms.ModelForm):
    """Formulario principal para tareas."""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'category', 'task_type',
            'status', 'priority', 'start_date', 'due_date', 'estimated_hours',
            'progress_percentage', 'is_recurring', 'recurrence_pattern',
            'reminder_date', 'centro_costos', 'proyecto_relacionado',
            'solicitud_servicio', 'contrato_mantenimiento'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reminder_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'progress_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar usuarios activos
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Filtrar categorías activas
        self.fields['category'].queryset = TaskCategory.objects.filter(is_active=True)
        
        # Configurar campos de relaciones
        self.fields['proyecto_relacionado'].queryset = self.get_proyecto_queryset()
        self.fields['solicitud_servicio'].required = False
        self.fields['contrato_mantenimiento'].required = False
        
        # Si no es superusuario, limitar las opciones
        if self.user and not self.user.is_superuser:
            # Solo puede asignar a sí mismo o a usuarios de su mismo equipo
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(
                id=self.user.id
            )
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Alert(
                content=_('Completa la información de la tarea. Los campos marcados con * son obligatorios.'),
                css_class='alert-info'
            ),
            Row(
                Column('title', css_class='form-group col-md-8 mb-0'),
                Column('task_type', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'description',
            Row(
                Column('assigned_to', css_class='form-group col-md-6 mb-0'),
                Column('category', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            HTML('<h5 class="mt-3 mb-2"><i class="fas fa-link"></i> Relaciones del Proyecto</h5>'),
            'centro_costos',
            Row(
                Column('proyecto_relacionado', css_class='form-group col-md-4 mb-0'),
                Column('solicitud_servicio', css_class='form-group col-md-4 mb-0'),
                Column('contrato_mantenimiento', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('status', css_class='form-group col-md-4 mb-0'),
                Column('priority', css_class='form-group col-md-4 mb-0'),
                Column('progress_percentage', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            HTML('<h5 class="mt-3 mb-2"><i class="fas fa-calendar-alt"></i> Fechas y Tiempo</h5>'),
            Row(
                Column('start_date', css_class='form-group col-md-4 mb-0'),
                Column('due_date', css_class='form-group col-md-4 mb-0'),
                Column('estimated_hours', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            HTML('<h5 class="mt-3 mb-2"><i class="fas fa-repeat"></i> Recordatorios</h5>'),
            Row(
                Column('reminder_date', css_class='form-group col-md-6 mb-0'),
                Column('is_recurring', css_class='form-group col-md-3 mb-0'),
                Column('recurrence_pattern', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', _('Guardar Tarea'), css_class='btn btn-primary'),
                Button('cancel', _('Cancelar'), css_class='btn btn-secondary', 
                      onclick="window.history.back();")
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        due_date = cleaned_data.get('due_date')
        reminder_date = cleaned_data.get('reminder_date')
        
        # Validar fechas
        if start_date and due_date and start_date > due_date:
            raise forms.ValidationError(_('La fecha de inicio no puede ser posterior a la fecha de vencimiento.'))
        
        if reminder_date and due_date and reminder_date > due_date:
            raise forms.ValidationError(_('La fecha de recordatorio no puede ser posterior a la fecha de vencimiento.'))
        
        # Validar recurrencia
        is_recurring = cleaned_data.get('is_recurring')
        recurrence_pattern = cleaned_data.get('recurrence_pattern')
        
        if is_recurring and not recurrence_pattern:
            raise forms.ValidationError(_('Debe especificar un patrón de recurrencia para tareas recurrentes.'))
        
        return cleaned_data
    
    def get_proyecto_queryset(self):
        """Obtiene queryset de proyectos disponibles."""
        try:
            from proyectos.models import Proyecto
            return Proyecto.objects.filter(estado__in=['pendiente', 'en_ejecucion']).order_by('nombre_proyecto')
        except ImportError:
            return None

class TaskQuickCreateForm(forms.ModelForm):
    """Formulario rápido para crear tareas."""
    
    class Meta:
        model = Task
        fields = ['title', 'assigned_to', 'due_date', 'priority']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar usuarios activos
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['assigned_to'].initial = self.user
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'title',
            Row(
                Column('assigned_to', css_class='form-group col-md-6 mb-0'),
                Column('priority', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'due_date',
            FormActions(
                Submit('submit', _('Crear Tarea'), css_class='btn btn-primary'),
                Button('cancel', _('Cancelar'), css_class='btn btn-secondary', 
                      onclick="$('#quickTaskModal').modal('hide');")
            )
        )

class TaskUpdateForm(forms.ModelForm):
    """Formulario para actualizar tareas."""
    
    actual_hours = forms.DecimalField(
        label=_('Horas reales'),
        max_digits=5, 
        decimal_places=2, 
        required=False,
        help_text=_('Horas realmente trabajadas en esta tarea')
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 'category', 'task_type',
            'status', 'priority', 'start_date', 'due_date', 'estimated_hours',
            'actual_hours', 'progress_percentage', 'is_recurring', 
            'recurrence_pattern', 'reminder_date'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'reminder_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'progress_percentage': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar usuarios activos
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Filtrar categorías activas
        self.fields['category'].queryset = TaskCategory.objects.filter(is_active=True)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-8 mb-0'),
                Column('task_type', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'description',
            Row(
                Column('assigned_to', css_class='form-group col-md-6 mb-0'),
                Column('category', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('status', css_class='form-group col-md-4 mb-0'),
                Column('priority', css_class='form-group col-md-4 mb-0'),
                Column('progress_percentage', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            HTML('<h5 class="mt-3 mb-2"><i class="fas fa-clock"></i> Tiempo</h5>'),
            Row(
                Column('start_date', css_class='form-group col-md-4 mb-0'),
                Column('due_date', css_class='form-group col-md-4 mb-0'),
                Column('reminder_date', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('estimated_hours', css_class='form-group col-md-6 mb-0'),
                Column('actual_hours', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            HTML('<h5 class="mt-3 mb-2"><i class="fas fa-repeat"></i> Recurrencia</h5>'),
            Row(
                Column('is_recurring', css_class='form-group col-md-6 mb-0'),
                Column('recurrence_pattern', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            FormActions(
                Submit('submit', _('Actualizar Tarea'), css_class='btn btn-primary'),
                Button('cancel', _('Cancelar'), css_class='btn btn-secondary', 
                      onclick="window.history.back();")
            )
        )

class TaskCategoryForm(forms.ModelForm):
    """Formulario para categorías de tareas."""
    
    class Meta:
        model = TaskCategory
        fields = ['name', 'module', 'description', 'color', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-8 mb-0'),
                Column('is_active', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('module', css_class='form-group col-md-6 mb-0'),
                Column('color', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description',
            FormActions(
                Submit('submit', _('Guardar Categoría'), css_class='btn btn-primary'),
                Button('cancel', _('Cancelar'), css_class='btn btn-secondary', 
                      onclick="window.history.back();")
            )
        )

class TaskCommentForm(forms.ModelForm):
    """Formulario para comentarios de tareas."""
    
    class Meta:
        model = TaskComment
        fields = ['content', 'is_internal']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Escribe tu comentario...')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'content',
            'is_internal',
        )

class TaskAttachmentForm(forms.ModelForm):
    """Formulario para archivos adjuntos de tareas."""
    
    class Meta:
        model = TaskAttachment
        fields = ['file', 'description', 'group', 'is_public']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': _('Descripción opcional del archivo')}),
        }
    
    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop('task', None)
        super().__init__(*args, **kwargs)
        
        self.fields['file'].help_text = _('Archivos permitidos: PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, ZIP, Videos, Audio (máx. 50MB)')
        
        # Filtrar grupos por tarea
        if self.task:
            self.fields['group'].queryset = TaskAttachmentGroup.objects.filter(task=self.task)
        else:
            self.fields['group'].queryset = TaskAttachmentGroup.objects.none()
        
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'file',
            'description',
            Row(
                Column('group', css_class='form-group col-md-6 mb-0'),
                Column('is_public', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            )
        )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            # Validar tamaño (50MB máximo)
            if file.size > 50 * 1024 * 1024:
                raise forms.ValidationError(_('El archivo no puede ser mayor a 50MB.'))
            
            # Validar tipo de archivo
            allowed_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff',
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv',
                '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
                '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'
            ]
            file_extension = f".{file.name.lower().split('.')[-1]}"
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    _('Tipo de archivo no permitido. Consulta la lista de formatos soportados.')
                )
        
        return file

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class MultipleTaskAttachmentForm(forms.Form):
    """Formulario para subir múltiples archivos a la vez."""
    
    files = MultipleFileField(
        label=_('Archivos'),
        help_text=_('Selecciona múltiples archivos. Máximo 50MB por archivo.'),
        required=True
    )
    description = forms.CharField(
        label=_('Descripción general'),
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': _('Descripción opcional para todos los archivos')})
    )
    group = forms.ModelChoiceField(
        queryset=TaskAttachmentGroup.objects.none(),
        label=_('Grupo'),
        required=False,
        empty_label=_('Sin grupo')
    )
    is_public = forms.BooleanField(
        label=_('Archivos públicos'),
        required=False,
        help_text=_('Marcar si todos los archivos deben ser públicos')
    )
    
    def __init__(self, *args, **kwargs):
        self.task = kwargs.pop('task', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar grupos por tarea
        if self.task:
            self.fields['group'].queryset = TaskAttachmentGroup.objects.filter(task=self.task)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'files',
            'description',
            Row(
                Column('group', css_class='form-group col-md-6 mb-0'),
                Column('is_public', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            )
        )
    
    def clean_files(self):
        files = self.cleaned_data.get('files', [])
        
        if not isinstance(files, list):
            files = [files]
        
        # Validar cada archivo
        for file in files:
            if file:
                # Validar tamaño (50MB máximo por archivo)
                if file.size > 50 * 1024 * 1024:
                    raise forms.ValidationError(
                        _('El archivo "%(filename)s" excede el límite de 50MB.') % {'filename': file.name}
                    )
                
                # Validar tipo de archivo
                allowed_extensions = [
                    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf',
                    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff',
                    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv',
                    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',
                    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'
                ]
                file_extension = f".{file.name.lower().split('.')[-1]}"
                if file_extension not in allowed_extensions:
                    raise forms.ValidationError(
                        _('El archivo "%(filename)s" tiene un formato no permitido.') % {'filename': file.name}
                    )
        
        # Validar número total de archivos
        if len(files) > 10:
            raise forms.ValidationError(_('No puedes subir más de 10 archivos a la vez.'))
        
        return files

class TaskImageForm(forms.ModelForm):
    """Formulario para imágenes de tareas."""
    
    class Meta:
        model = TaskImage
        fields = ['image', 'title', 'description', 'taken_at', 'location', 'is_primary', 'is_public']
        widgets = {
            'taken_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'title': forms.TextInput(attrs={'placeholder': _('Título descriptivo de la imagen')}),
            'location': forms.TextInput(attrs={'placeholder': _('Ubicación donde se tomó la imagen')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['image'].help_text = _('Formatos soportados: JPG, PNG, GIF, WebP (máx. 20MB)')
        
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'image',
            'title',
            'description',
            Row(
                Column('taken_at', css_class='form-group col-md-6 mb-0'),
                Column('location', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('is_primary', css_class='form-group col-md-6 mb-0'),
                Column('is_public', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            )
        )
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        
        if image:
            # Validar tamaño (20MB máximo)
            if image.size > 20 * 1024 * 1024:
                raise forms.ValidationError(_('La imagen no puede ser mayor a 20MB.'))
            
            # Validar tipo de archivo
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
            file_extension = f".{image.name.lower().split('.')[-1]}"
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    _('Formato de imagen no permitido. Formatos soportados: JPG, PNG, GIF, WebP, BMP')
                )
        
        return image

class MultipleImageField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class MultipleTaskImageForm(forms.Form):
    """Formulario para subir múltiples imágenes a la vez."""
    
    images = MultipleImageField(
        label=_('Imágenes'),
        help_text=_('Selecciona múltiples imágenes. Máximo 20MB por imagen.'),
        required=True
    )
    title_prefix = forms.CharField(
        label=_('Prefijo de título'),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Ej: Inspección - ')})
    )
    description = forms.CharField(
        label=_('Descripción general'),
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': _('Descripción opcional para todas las imágenes')})
    )
    location = forms.CharField(
        label=_('Ubicación'),
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Ubicación donde se tomaron las imágenes')})
    )
    is_public = forms.BooleanField(
        label=_('Imágenes públicas'),
        required=False,
        help_text=_('Marcar si todas las imágenes deben ser públicas')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'images',
            Row(
                Column('title_prefix', css_class='form-group col-md-6 mb-0'),
                Column('location', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'description',
            'is_public'
        )
    
    def clean_images(self):
        images = self.cleaned_data.get('images', [])
        
        if not isinstance(images, list):
            images = [images]
        
        # Validar cada imagen
        for image in images:
            if image:
                # Validar tamaño (20MB máximo por imagen)
                if image.size > 20 * 1024 * 1024:
                    raise forms.ValidationError(
                        _('La imagen "%(filename)s" excede el límite de 20MB.') % {'filename': image.name}
                    )
                
                # Validar tipo de archivo
                allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
                file_extension = f".{image.name.lower().split('.')[-1]}"
                if file_extension not in allowed_extensions:
                    raise forms.ValidationError(
                        _('La imagen "%(filename)s" tiene un formato no permitido.') % {'filename': image.name}
                    )
        
        # Validar número total de imágenes
        if len(images) > 20:
            raise forms.ValidationError(_('No puedes subir más de 20 imágenes a la vez.'))
        
        return images

class TaskAttachmentGroupForm(forms.ModelForm):
    """Formulario para grupos de archivos adjuntos."""
    
    class Meta:
        model = TaskAttachmentGroup
        fields = ['name', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-8 mb-0'),
                Column('order', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'description'
        )

class TaskFilterForm(forms.Form):
    """Formulario para filtrar tareas."""
    
    STATUS_CHOICES = [('', _('Todos los estados'))] + Task.STATUS_CHOICES
    PRIORITY_CHOICES = [('', _('Todas las prioridades'))] + Task.PRIORITY_CHOICES
    TYPE_CHOICES = [('', _('Todos los tipos'))] + Task.TYPE_CHOICES
    
    search = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': _('Buscar en título o descripción...')})
    )
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    task_type = forms.ChoiceField(choices=TYPE_CHOICES, required=False)
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name', 'last_name'),
        required=False,
        empty_label=_('Todos los usuarios')
    )
    category = forms.ModelChoiceField(
        queryset=TaskCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('Todas las categorías')
    )
    due_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label=_('Vence desde')
    )
    due_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label=_('Vence hasta')
    )
    overdue_only = forms.BooleanField(required=False, label=_('Solo vencidas'))
    my_tasks_only = forms.BooleanField(required=False, label=_('Solo mis tareas'))
    centro_costos = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Filtrar por centro de costos...')}),
        label=_('Centro de Costos')
    )
    modulo = forms.ChoiceField(
        choices=[
            ('', _('Todos los módulos')),
            ('proyectos', _('Proyectos')),
            ('servicios', _('Servicios')),
            ('mantenimiento', _('Mantenimiento')),
            ('general', _('General'))
        ],
        required=False,
        label=_('Módulo')
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='form-group col-md-4 mb-0'),
                Column('status', css_class='form-group col-md-2 mb-0'),
                Column('priority', css_class='form-group col-md-2 mb-0'),
                Column('task_type', css_class='form-group col-md-2 mb-0'),
                Column(
                    Submit('submit', _('Filtrar'), css_class='btn btn-primary btn-sm mt-4'),
                    css_class='form-group col-md-2 mb-0'
                ),
                css_class='form-row'
            ),
            Row(
                Column('assigned_to', css_class='form-group col-md-3 mb-0'),
                Column('category', css_class='form-group col-md-3 mb-0'),
                Column('due_date_from', css_class='form-group col-md-2 mb-0'),
                Column('due_date_to', css_class='form-group col-md-2 mb-0'),
                Column('overdue_only', css_class='form-group col-md-1 mb-0'),
                Column('my_tasks_only', css_class='form-group col-md-1 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('centro_costos', css_class='form-group col-md-6 mb-0'),
                Column('modulo', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
        )