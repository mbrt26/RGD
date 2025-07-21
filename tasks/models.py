from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()

class TaskCategory(models.Model):
    """Categorías para organizar las tareas por módulo o tipo."""
    
    MODULE_CHOICES = [
        ('proyectos', _('Proyectos')),
        ('servicios', _('Servicios')),
        ('mantenimiento', _('Mantenimiento')),
        ('insumos', _('Insumos')),
        ('users', _('Usuarios')),
        ('general', _('General')),
    ]
    
    name = models.CharField(_('nombre'), max_length=100)
    module = models.CharField(_('módulo'), max_length=20, choices=MODULE_CHOICES)
    description = models.TextField(_('descripción'), blank=True)
    color = models.CharField(_('color'), max_length=7, default='#007bff', 
                           help_text=_('Color en formato hexadecimal (ej: #007bff)'))
    is_active = models.BooleanField(_('activo'), default=True)
    created_at = models.DateTimeField(_('fecha creación'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Categoría de Tarea')
        verbose_name_plural = _('Categorías de Tareas')
        ordering = ['module', 'name']
        unique_together = ['name', 'module']
    
    def __str__(self):
        return f"{self.get_module_display()} - {self.name}"

class Task(models.Model):
    """Modelo principal para tareas del sistema."""
    
    STATUS_CHOICES = [
        ('pending', _('Pendiente')),
        ('in_progress', _('En Progreso')),
        ('completed', _('Completada')),
        ('cancelled', _('Cancelada')),
        ('on_hold', _('En Espera')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Baja')),
        ('medium', _('Media')),
        ('high', _('Alta')),
        ('urgent', _('Urgente')),
    ]
    
    TYPE_CHOICES = [
        ('task', _('Tarea')),
        ('reminder', _('Recordatorio')),
        ('follow_up', _('Seguimiento')),
        ('review', _('Revisión')),
        ('meeting', _('Reunión')),
        ('call', _('Llamada')),
        ('email', _('Email')),
        ('other', _('Otro')),
    ]
    
    # Campos básicos
    title = models.CharField(_('título'), max_length=200)
    description = models.TextField(_('descripción'), blank=True)
    
    # Asignación y responsabilidad
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, 
                                  related_name='assigned_tasks', 
                                  verbose_name=_('asignado a'))
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, 
                                 related_name='created_tasks',
                                 verbose_name=_('creado por'))
    
    # Categorización
    category = models.ForeignKey(TaskCategory, on_delete=models.SET_NULL, 
                               null=True, blank=True,
                               verbose_name=_('categoría'))
    
    # Estado y prioridad
    status = models.CharField(_('estado'), max_length=20, 
                            choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(_('prioridad'), max_length=10, 
                              choices=PRIORITY_CHOICES, default='medium')
    task_type = models.CharField(_('tipo'), max_length=20, 
                               choices=TYPE_CHOICES, default='task')
    
    # Fechas
    due_date = models.DateTimeField(_('fecha vencimiento'), null=True, blank=True)
    start_date = models.DateTimeField(_('fecha inicio'), null=True, blank=True)
    completed_date = models.DateTimeField(_('fecha completado'), null=True, blank=True)
    created_at = models.DateTimeField(_('fecha creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha actualización'), auto_now=True)
    
    # Relación genérica para vincular con cualquier objeto
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                   null=True, blank=True,
                                   verbose_name=_('tipo de contenido'))
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')
    
    # Campos para asociar con centro de costos y proyectos específicos
    centro_costos = models.CharField(_('centro de costos'), max_length=100, blank=True,
                                   help_text=_('Centro de costos asociado a la tarea'))
    
    # Relaciones específicas con módulos
    proyecto_relacionado = models.ForeignKey('proyectos.Proyecto', on_delete=models.SET_NULL,
                                           null=True, blank=True,
                                           verbose_name=_('proyecto relacionado'),
                                           help_text=_('Proyecto específico al que pertenece la tarea'))
    
    solicitud_servicio = models.ForeignKey('servicios.SolicitudServicio', on_delete=models.SET_NULL,
                                         null=True, blank=True,
                                         verbose_name=_('solicitud de servicio'),
                                         help_text=_('Solicitud de servicio relacionada'))
    
    contrato_mantenimiento = models.ForeignKey('mantenimiento.ContratoMantenimiento', on_delete=models.SET_NULL,
                                             null=True, blank=True,
                                             verbose_name=_('contrato de mantenimiento'),
                                             help_text=_('Contrato de mantenimiento relacionado'))
    
    # Configuraciones adicionales
    is_recurring = models.BooleanField(_('recurrente'), default=False)
    recurrence_pattern = models.CharField(_('patrón recurrencia'), max_length=50, blank=True,
                                        help_text=_('ej: daily, weekly, monthly'))
    estimated_hours = models.DecimalField(_('horas estimadas'), max_digits=5, decimal_places=2, 
                                        null=True, blank=True)
    actual_hours = models.DecimalField(_('horas reales'), max_digits=5, decimal_places=2, 
                                     null=True, blank=True)
    
    # Notificaciones
    reminder_sent = models.BooleanField(_('recordatorio enviado'), default=False)
    reminder_date = models.DateTimeField(_('fecha recordatorio'), null=True, blank=True)
    
    # Progreso
    progress_percentage = models.PositiveIntegerField(_('porcentaje progreso'), default=0,
                                                    help_text=_('0-100'))
    
    class Meta:
        verbose_name = _('Tarea')
        verbose_name_plural = _('Tareas')
        ordering = ['-priority', 'due_date', '-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['centro_costos']),
            models.Index(fields=['proyecto_relacionado', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"
    
    def clean(self):
        """Validaciones personalizadas."""
        if self.progress_percentage < 0 or self.progress_percentage > 100:
            raise ValidationError(_('El porcentaje de progreso debe estar entre 0 y 100.'))
        
        if self.start_date and self.due_date and self.start_date > self.due_date:
            raise ValidationError(_('La fecha de inicio no puede ser posterior a la fecha de vencimiento.'))
        
        if self.estimated_hours and self.estimated_hours < 0:
            raise ValidationError(_('Las horas estimadas no pueden ser negativas.'))
        
        if self.actual_hours and self.actual_hours < 0:
            raise ValidationError(_('Las horas reales no pueden ser negativas.'))
    
    def save(self, *args, **kwargs):
        self.clean()
        
        # Auto-completar la fecha de completado
        if self.status == 'completed' and not self.completed_date:
            self.completed_date = timezone.now()
        elif self.status != 'completed' and self.completed_date:
            self.completed_date = None
        
        # Auto-actualizar progreso basado en estado
        if self.status == 'completed':
            self.progress_percentage = 100
        elif self.status == 'pending' and self.progress_percentage == 0:
            pass  # Mantener en 0
        elif self.status == 'in_progress' and self.progress_percentage == 0:
            self.progress_percentage = 10  # Mínimo cuando está en progreso
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Verifica si la tarea está vencida."""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        """Calcula días hasta el vencimiento."""
        if self.due_date:
            delta = self.due_date.date() - timezone.now().date()
            return delta.days
        return None
    
    @property
    def priority_weight(self):
        """Peso numérico para ordenamiento por prioridad."""
        weights = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4}
        return weights.get(self.priority, 2)
    
    def get_related_object_display(self):
        """Retorna representación string del objeto relacionado."""
        if self.related_object:
            return str(self.related_object)
        return None
    
    def get_centro_costos_display(self):
        """Retorna el centro de costos desde el objeto relacionado o el campo directo."""
        if self.centro_costos:
            return self.centro_costos
        elif self.proyecto_relacionado:
            return self.proyecto_relacionado.centro_costos
        return None
    
    def get_modulo_origen(self):
        """Retorna el módulo de origen de la tarea."""
        if self.proyecto_relacionado:
            return 'proyectos'
        elif self.solicitud_servicio:
            return 'servicios'
        elif self.contrato_mantenimiento:
            return 'mantenimiento'
        elif self.category:
            return self.category.module
        return 'general'
    
    def can_be_edited_by(self, user):
        """Verifica si un usuario puede editar la tarea."""
        return (user == self.assigned_to or 
                user == self.created_by or 
                user.is_superuser or
                user.has_module_permission('tasks', 'change'))
    
    def get_priority_color(self):
        """Retorna el color CSS para el badge de prioridad."""
        colors = {
            'low': 'secondary',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'secondary')
    
    def get_status_color(self):
        """Retorna el color CSS para el badge de estado."""
        colors = {
            'pending': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'cancelled': 'dark',
            'on_hold': 'warning'
        }
        return colors.get(self.status, 'secondary')
    
    def can_be_viewed_by(self, user):
        """Verifica si un usuario puede ver la tarea."""
        return (user == self.assigned_to or 
                user == self.created_by or 
                user.is_superuser or
                user.has_module_permission('tasks', 'view'))

class TaskComment(models.Model):
    """Comentarios y notas en las tareas."""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, 
                           related_name='comments',
                           verbose_name=_('tarea'))
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name=_('autor'))
    content = models.TextField(_('contenido'))
    is_internal = models.BooleanField(_('interno'), default=False,
                                    help_text=_('Solo visible para el equipo interno'))
    created_at = models.DateTimeField(_('fecha creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('Comentario de Tarea')
        verbose_name_plural = _('Comentarios de Tareas')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comentario de {self.author.username} en {self.task.title}"

class TaskAttachment(models.Model):
    """Archivos adjuntos a las tareas."""
    
    FILE_TYPE_CHOICES = [
        ('document', _('Documento')),
        ('image', _('Imagen')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('archive', _('Archivo comprimido')),
        ('other', _('Otro')),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                           related_name='attachments',
                           verbose_name=_('tarea'))
    file = models.FileField(_('archivo'), upload_to='tasks/attachments/%Y/%m/')
    original_name = models.CharField(_('nombre original'), max_length=255)
    file_type = models.CharField(_('tipo de archivo'), max_length=20, 
                               choices=FILE_TYPE_CHOICES, default='other')
    description = models.CharField(_('descripción'), max_length=500, blank=True,
                                 help_text=_('Descripción opcional del archivo'))
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                  verbose_name=_('subido por'))
    uploaded_at = models.DateTimeField(_('fecha subida'), auto_now_add=True)
    file_size = models.PositiveIntegerField(_('tamaño archivo'), null=True, blank=True)
    mime_type = models.CharField(_('tipo MIME'), max_length=100, blank=True)
    is_public = models.BooleanField(_('público'), default=False,
                                  help_text=_('Si está marcado, el archivo es visible para todos'))
    group = models.ForeignKey('TaskAttachmentGroup', on_delete=models.SET_NULL,
                            null=True, blank=True,
                            related_name='grouped_attachments',
                            verbose_name=_('grupo'),
                            help_text=_('Grupo al que pertenece este archivo'))
    
    class Meta:
        verbose_name = _('Archivo Adjunto')
        verbose_name_plural = _('Archivos Adjuntos')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['task', 'file_type']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.original_name} - {self.task.title}"
    
    def save(self, *args, **kwargs):
        if self.file:
            if not self.original_name:
                self.original_name = self.file.name
            if not self.file_size:
                self.file_size = self.file.size
            
            # Detectar tipo de archivo automáticamente
            if not self.file_type or self.file_type == 'other':
                self.file_type = self.detect_file_type()
            
            # Detectar MIME type
            if not self.mime_type:
                self.mime_type = self.detect_mime_type()
                
        super().save(*args, **kwargs)
    
    def detect_file_type(self):
        """Detecta el tipo de archivo basado en la extensión."""
        if not self.file:
            return 'other'
        
        extension = self.get_file_extension().lower()
        
        # Imágenes
        if extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff']:
            return 'image'
        
        # Documentos
        elif extension in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt', '.ods']:
            return 'document'
        
        # Videos
        elif extension in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']:
            return 'video'
        
        # Audio
        elif extension in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
            return 'audio'
        
        # Archivos comprimidos
        elif extension in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']:
            return 'archive'
        
        return 'other'
    
    def detect_mime_type(self):
        """Detecta el tipo MIME basado en la extensión."""
        if not self.file:
            return ''
        
        import mimetypes
        mime_type, _ = mimetypes.guess_type(self.file.name)
        return mime_type or ''
    
    def get_file_extension(self):
        """Obtiene la extensión del archivo."""
        if self.file and self.file.name:
            import os
            return os.path.splitext(self.file.name)[1]
        return ''
    
    @property
    def is_image(self):
        """Verifica si el archivo es una imagen."""
        return self.file_type == 'image'
    
    @property
    def is_document(self):
        """Verifica si el archivo es un documento."""
        return self.file_type == 'document'
    
    @property
    def can_preview(self):
        """Verifica si el archivo se puede previsualizar."""
        return self.is_image or self.file_type in ['document'] and self.get_file_extension().lower() == '.pdf'
    
    @property
    def file_size_formatted(self):
        """Retorna el tamaño del archivo en formato legible."""
        if not self.file_size:
            return _('Desconocido')
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    @property
    def icon_class(self):
        """Retorna la clase CSS del icono FontAwesome según el tipo de archivo."""
        icons = {
            'image': 'fas fa-image text-primary',
            'document': 'fas fa-file-alt text-info',
            'video': 'fas fa-video text-warning',
            'audio': 'fas fa-music text-success',
            'archive': 'fas fa-file-archive text-secondary',
            'other': 'fas fa-file text-muted'
        }
        return icons.get(self.file_type, 'fas fa-file text-muted')

class TaskHistory(models.Model):
    """Historial de cambios en las tareas."""
    
    ACTION_CHOICES = [
        ('created', _('Creada')),
        ('updated', _('Actualizada')),
        ('status_changed', _('Estado Cambiado')),
        ('assigned', _('Asignada')),
        ('commented', _('Comentario Agregado')),
        ('completed', _('Completada')),
        ('cancelled', _('Cancelada')),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                           related_name='history',
                           verbose_name=_('tarea'))
    action = models.CharField(_('acción'), max_length=20, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                           verbose_name=_('usuario'))
    description = models.TextField(_('descripción'), blank=True)
    old_value = models.TextField(_('valor anterior'), blank=True)
    new_value = models.TextField(_('valor nuevo'), blank=True)
    created_at = models.DateTimeField(_('fecha'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Historial de Tarea')
        verbose_name_plural = _('Historiales de Tareas')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.task.title} por {self.user.username}"

class TaskImage(models.Model):
    """Imágenes específicas adjuntas a las tareas."""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                           related_name='images',
                           verbose_name=_('tarea'))
    image = models.ImageField(_('imagen'), upload_to='tasks/images/%Y/%m/',
                            help_text=_('Formatos soportados: JPG, PNG, GIF, WebP'))
    title = models.CharField(_('título'), max_length=200, blank=True,
                           help_text=_('Título descriptivo de la imagen'))
    description = models.TextField(_('descripción'), blank=True,
                                 help_text=_('Descripción detallada de la imagen'))
    taken_at = models.DateTimeField(_('fecha de captura'), null=True, blank=True,
                                  help_text=_('Fecha en que se tomó la imagen'))
    location = models.CharField(_('ubicación'), max_length=500, blank=True,
                              help_text=_('Ubicación donde se tomó la imagen'))
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                  verbose_name=_('subido por'))
    uploaded_at = models.DateTimeField(_('fecha subida'), auto_now_add=True)
    width = models.PositiveIntegerField(_('ancho'), null=True, blank=True)
    height = models.PositiveIntegerField(_('alto'), null=True, blank=True)
    file_size = models.PositiveIntegerField(_('tamaño archivo'), null=True, blank=True)
    is_primary = models.BooleanField(_('imagen principal'), default=False,
                                   help_text=_('Marcar como imagen principal de la tarea'))
    is_public = models.BooleanField(_('pública'), default=False,
                                  help_text=_('Si está marcada, la imagen es visible para todos'))
    
    class Meta:
        verbose_name = _('Imagen de Tarea')
        verbose_name_plural = _('Imágenes de Tareas')
        ordering = ['-is_primary', '-uploaded_at']
        indexes = [
            models.Index(fields=['task', 'is_primary']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Imagen'} - {self.task.title}"
    
    def save(self, *args, **kwargs):
        # Si se marca como principal, desmarcar otras imágenes principales
        if self.is_primary:
            TaskImage.objects.filter(task=self.task, is_primary=True).update(is_primary=False)
        
        # Obtener dimensiones y tamaño del archivo
        if self.image:
            if not self.file_size:
                self.file_size = self.image.size
            
            # Obtener dimensiones de la imagen
            if not self.width or not self.height:
                try:
                    from PIL import Image
                    with Image.open(self.image) as img:
                        self.width, self.height = img.size
                except Exception:
                    pass
        
        super().save(*args, **kwargs)
    
    @property
    def file_size_formatted(self):
        """Retorna el tamaño del archivo en formato legible."""
        if not self.file_size:
            return _('Desconocido')
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    @property
    def dimensions(self):
        """Retorna las dimensiones de la imagen."""
        if self.width and self.height:
            return f"{self.width}x{self.height}"
        return _('Desconocido')
    
    @property
    def aspect_ratio(self):
        """Calcula la relación de aspecto de la imagen."""
        if self.width and self.height and self.height > 0:
            return self.width / self.height
        return 1
    
    @property
    def is_landscape(self):
        """Verifica si la imagen es horizontal."""
        return self.aspect_ratio > 1
    
    @property
    def is_portrait(self):
        """Verifica si la imagen es vertical."""
        return self.aspect_ratio < 1
    
    @property
    def thumbnail_url(self):
        """Retorna la URL para thumbnail (se puede implementar con sorl-thumbnail)."""
        return self.image.url if self.image else None

class TaskAttachmentGroup(models.Model):
    """Grupos para organizar archivos adjuntos."""
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                           related_name='attachment_groups',
                           verbose_name=_('tarea'))
    name = models.CharField(_('nombre'), max_length=200)
    description = models.TextField(_('descripción'), blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                 verbose_name=_('creado por'))
    created_at = models.DateTimeField(_('fecha creación'), auto_now_add=True)
    order = models.PositiveIntegerField(_('orden'), default=0)
    
    class Meta:
        verbose_name = _('Grupo de Archivos')
        verbose_name_plural = _('Grupos de Archivos')
        ordering = ['order', 'name']
        unique_together = ['task', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.task.title}"
    
    @property
    def attachment_count(self):
        """Cuenta los archivos en este grupo."""
        return self.grouped_attachments.count()
    
    @property
    def total_size(self):
        """Calcula el tamaño total de archivos en el grupo."""
        return sum(att.file_size or 0 for att in self.grouped_attachments.all())
    
    @property
    def total_size_formatted(self):
        """Retorna el tamaño total en formato legible."""
        size = self.total_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
