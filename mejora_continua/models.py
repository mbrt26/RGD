from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class SolicitudMejora(models.Model):
    """Modelo para las solicitudes de mejora continua."""
    
    PRIORIDAD_CHOICES = [
        ('baja', _('Baja')),
        ('media', _('Media')),
        ('alta', _('Alta')),
        ('critica', _('Crítica')),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', _('Pendiente')),
        ('en_revision', _('En Revisión')),
        ('aprobada', _('Aprobada')),
        ('en_desarrollo', _('En Desarrollo')),
        ('completada', _('Completada')),
        ('rechazada', _('Rechazada')),
        ('cancelada', _('Cancelada')),
    ]
    
    MODULO_CHOICES = [
        ('crm', _('CRM')),
        ('proyectos', _('Proyectos')),
        ('servicios', _('Servicios')),
        ('mantenimiento', _('Mantenimiento')),
        ('insumos', _('Insumos')),
        ('users', _('Usuarios')),
        ('general', _('General')),
    ]
    
    TIPO_CHOICES = [
        ('modificacion', _('Modificación')),
        ('nueva_funcionalidad', _('Nueva Funcionalidad')),
        ('problema', _('Problema/Error')),
        ('mejora', _('Mejora de Rendimiento')),
        ('otro', _('Otro')),
    ]
    
    titulo = models.CharField(_('título'), max_length=200)
    descripcion = models.TextField(_('descripción'))
    tipo_solicitud = models.CharField(_('tipo de solicitud'), max_length=20, 
                                    choices=TIPO_CHOICES)
    modulo_afectado = models.CharField(_('módulo afectado'), max_length=20, 
                                     choices=MODULO_CHOICES)
    prioridad = models.CharField(_('prioridad'), max_length=10, 
                               choices=PRIORIDAD_CHOICES, default='media')
    estado = models.CharField(_('estado'), max_length=15, 
                            choices=ESTADO_CHOICES, default='pendiente')
    
    # Información del solicitante
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, 
                                  related_name='solicitudes_creadas',
                                  verbose_name=_('solicitante'))
    fecha_solicitud = models.DateTimeField(_('fecha de solicitud'), auto_now_add=True)
    
    # Información de seguimiento
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                 null=True, blank=True,
                                 related_name='solicitudes_asignadas',
                                 verbose_name=_('asignado a'))
    fecha_asignacion = models.DateTimeField(_('fecha de asignación'), null=True, blank=True)
    fecha_estimada_completado = models.DateField(_('fecha estimada completado'), 
                                               null=True, blank=True)
    fecha_completado = models.DateTimeField(_('fecha completado'), null=True, blank=True)
    
    # Información adicional
    pasos_reproducir = models.TextField(_('pasos para reproducir'), blank=True,
                                      help_text=_('Para problemas/errores, describe los pasos para reproducir el issue'))
    impacto_negocio = models.TextField(_('impacto en el negocio'), blank=True,
                                     help_text=_('Describe cómo afecta esta solicitud al negocio'))
    solucion_propuesta = models.TextField(_('solución propuesta'), blank=True,
                                        help_text=_('Si tienes una idea de solución, compártela'))
    
    # Metadatos
    fecha_actualizacion = models.DateTimeField(_('fecha actualización'), auto_now=True)
    numero_solicitud = models.CharField(_('número de solicitud'), max_length=20, 
                                      unique=True, blank=True)
    
    class Meta:
        verbose_name = _('Solicitud de Mejora')
        verbose_name_plural = _('Solicitudes de Mejora')
        ordering = ['-fecha_solicitud']
        permissions = [
            ('can_assign_requests', _('Puede asignar solicitudes')),
            ('can_change_status', _('Puede cambiar estado')),
            ('can_view_all_requests', _('Puede ver todas las solicitudes')),
        ]
    
    def __str__(self):
        return f"{self.numero_solicitud} - {self.titulo}"
    
    def save(self, *args, **kwargs):
        if not self.numero_solicitud:
            # Generar número de solicitud automático
            last_request = SolicitudMejora.objects.order_by('-id').first()
            if last_request and last_request.numero_solicitud:
                try:
                    last_number = int(last_request.numero_solicitud.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.numero_solicitud = f"MC-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    def get_estado_color(self):
        """Retorna el color bootstrap para el estado."""
        colors = {
            'pendiente': 'secondary',
            'en_revision': 'info',
            'aprobada': 'primary',
            'en_desarrollo': 'warning',
            'completada': 'success',
            'rechazada': 'danger',
            'cancelada': 'dark',
        }
        return colors.get(self.estado, 'secondary')
    
    def get_prioridad_color(self):
        """Retorna el color bootstrap para la prioridad."""
        colors = {
            'baja': 'success',
            'media': 'warning',
            'alta': 'danger',
            'critica': 'dark',
        }
        return colors.get(self.prioridad, 'secondary')

class ComentarioSolicitud(models.Model):
    """Comentarios y seguimiento de las solicitudes."""
    
    solicitud = models.ForeignKey(SolicitudMejora, on_delete=models.CASCADE,
                                related_name='comentarios',
                                verbose_name=_('solicitud'))
    autor = models.ForeignKey(User, on_delete=models.CASCADE,
                            verbose_name=_('autor'))
    comentario = models.TextField(_('comentario'))
    fecha_comentario = models.DateTimeField(_('fecha comentario'), auto_now_add=True)
    es_interno = models.BooleanField(_('comentario interno'), default=False,
                                   help_text=_('Los comentarios internos solo son visibles para administradores'))
    
    class Meta:
        verbose_name = _('Comentario')
        verbose_name_plural = _('Comentarios')
        ordering = ['fecha_comentario']
    
    def __str__(self):
        return f"Comentario de {self.autor} - {self.solicitud.numero_solicitud}"

def upload_to_solicitud(instance, filename):
    """Genera la ruta de subida para archivos de solicitud."""
    import os
    from django.utils.text import slugify
    
    # Obtener extensión del archivo
    name, ext = os.path.splitext(filename)
    
    # Crear nombre de archivo único
    safe_name = slugify(name)[:50]  # Limitar longitud
    timestamp = instance.solicitud.fecha_solicitud.strftime('%Y%m%d')
    
    return f'mejora_continua/{instance.solicitud.numero_solicitud}/{timestamp}_{safe_name}{ext}'

class AdjuntoSolicitud(models.Model):
    """Archivos adjuntos a las solicitudes."""
    
    TIPO_ARCHIVO_CHOICES = [
        ('imagen', _('Imagen')),
        ('documento', _('Documento')),
        ('video', _('Video')),
        ('audio', _('Audio')),
        ('otro', _('Otro')),
    ]
    
    solicitud = models.ForeignKey(SolicitudMejora, on_delete=models.CASCADE,
                                related_name='adjuntos',
                                verbose_name=_('solicitud'))
    archivo = models.FileField(_('archivo'), upload_to=upload_to_solicitud)
    descripcion = models.CharField(_('descripción'), max_length=200, blank=True)
    tipo_archivo = models.CharField(_('tipo de archivo'), max_length=20, 
                                  choices=TIPO_ARCHIVO_CHOICES, default='documento')
    tamaño_archivo = models.BigIntegerField(_('tamaño del archivo'), null=True, blank=True)
    nombre_original = models.CharField(_('nombre original'), max_length=255, blank=True)
    subido_por = models.ForeignKey(User, on_delete=models.CASCADE,
                                 verbose_name=_('subido por'))
    fecha_subida = models.DateTimeField(_('fecha subida'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Adjunto')
        verbose_name_plural = _('Adjuntos')
        ordering = ['fecha_subida']
    
    def __str__(self):
        return f"Adjunto - {self.solicitud.numero_solicitud} - {self.nombre_original or self.archivo.name}"
    
    def save(self, *args, **kwargs):
        if self.archivo:
            # Guardar nombre original
            if not self.nombre_original:
                self.nombre_original = self.archivo.name
            
            # Guardar tamaño del archivo
            if not self.tamaño_archivo:
                self.tamaño_archivo = self.archivo.size
            
            # Detectar tipo de archivo automáticamente
            if not self.tipo_archivo or self.tipo_archivo == 'documento':
                self.tipo_archivo = self._detectar_tipo_archivo()
        
        super().save(*args, **kwargs)
    
    def _detectar_tipo_archivo(self):
        """Detecta el tipo de archivo basado en la extensión."""
        import os
        if not self.archivo:
            return 'otro'
        
        nombre = self.archivo.name.lower()
        extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        extensiones_video = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        extensiones_audio = ['.mp3', '.wav', '.flac', '.aac', '.ogg']
        
        nombre_lower, ext = os.path.splitext(nombre)
        
        if ext in extensiones_imagen:
            return 'imagen'
        elif ext in extensiones_video:
            return 'video'
        elif ext in extensiones_audio:
            return 'audio'
        else:
            return 'documento'
    
    def es_imagen(self):
        """Verifica si el archivo es una imagen."""
        return self.tipo_archivo == 'imagen'
    
    def es_video(self):
        """Verifica si el archivo es un video."""
        return self.tipo_archivo == 'video'
    
    def obtener_icono(self):
        """Retorna el icono FontAwesome apropiado para el tipo de archivo."""
        iconos = {
            'imagen': 'fas fa-image',
            'documento': 'fas fa-file-alt',
            'video': 'fas fa-video',
            'audio': 'fas fa-music',
            'otro': 'fas fa-file'
        }
        return iconos.get(self.tipo_archivo, 'fas fa-file')
    
    def obtener_tamaño_legible(self):
        """Retorna el tamaño del archivo en formato legible."""
        if not self.tamaño_archivo:
            return 'Desconocido'
        
        for unidad in ['B', 'KB', 'MB', 'GB']:
            if self.tamaño_archivo < 1024.0:
                return f"{self.tamaño_archivo:.1f} {unidad}"
            self.tamaño_archivo /= 1024.0
        return f"{self.tamaño_archivo:.1f} TB"
