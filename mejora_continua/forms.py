from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field, HTML
from django.contrib.auth import get_user_model
from .models import SolicitudMejora, ComentarioSolicitud, AdjuntoSolicitud

class MultipleFileField(forms.FileField):
    """Campo personalizado para subir múltiples archivos."""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", forms.FileInput(attrs={'multiple': True}))
        super().__init__(*args, **kwargs)
    
    def clean(self, data, initial=None):
        # Si data es una lista (múltiples archivos), validar cada uno
        if isinstance(data, list):
            result = []
            for item in data:
                result.append(super().clean(item, initial))
            return result
        # Si es un solo archivo, usar validación normal
        return super().clean(data, initial)

User = get_user_model()

class SolicitudMejoraForm(forms.ModelForm):
    """Formulario para crear/editar solicitudes de mejora."""
    
    class Meta:
        model = SolicitudMejora
        fields = [
            'titulo', 'descripcion', 'tipo_solicitud', 'modulo_afectado',
            'prioridad', 'pasos_reproducir', 'impacto_negocio', 'solucion_propuesta'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'pasos_reproducir': forms.Textarea(attrs={'rows': 3}),
            'impacto_negocio': forms.Textarea(attrs={'rows': 3}),
            'solucion_propuesta': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configuración Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('titulo', css_class='form-group col-md-8 mb-0'),
                Column('tipo_solicitud', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('modulo_afectado', css_class='form-group col-md-6 mb-0'),
                Column('prioridad', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Field('descripcion'),
            HTML('<hr>'),
            HTML('<h6>Información Adicional <small class="text-muted">(Opcional)</small></h6>'),
            Field('pasos_reproducir'),
            Field('impacto_negocio'),
            Field('solucion_propuesta'),
            Submit('submit', 'Crear Solicitud', css_class='btn btn-primary')
        )
        
        # Si es edición, cambiar el texto del botón
        if self.instance.pk:
            self.helper.layout[-1] = Submit('submit', 'Actualizar Solicitud', css_class='btn btn-primary')

class SolicitudMejoraUpdateForm(forms.ModelForm):
    """Formulario para que los administradores actualicen el estado y asignación."""
    
    class Meta:
        model = SolicitudMejora
        fields = [
            'estado', 'asignado_a', 'fecha_estimada_completado', 'prioridad'
        ]
        widgets = {
            'fecha_estimada_completado': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Solo mostrar usuarios staff para asignación
        self.fields['asignado_a'].queryset = User.objects.filter(is_staff=True)
        
        # Configuración Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('estado', css_class='form-group col-md-6 mb-0'),
                Column('prioridad', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('asignado_a', css_class='form-group col-md-8 mb-0'),
                Column('fecha_estimada_completado', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Actualizar', css_class='btn btn-success')
        )

class ComentarioSolicitudForm(forms.ModelForm):
    """Formulario para agregar comentarios a las solicitudes."""
    
    class Meta:
        model = ComentarioSolicitud
        fields = ['comentario', 'es_interno']
        widgets = {
            'comentario': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Escribe tu comentario aquí...'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Solo usuarios staff pueden hacer comentarios internos
        if not user or not user.is_staff:
            self.fields.pop('es_interno')
        
        # Configuración Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('comentario'),
            Field('es_interno') if 'es_interno' in self.fields else None,
            Submit('submit', 'Agregar Comentario', css_class='btn btn-primary btn-sm')
        )

class AdjuntoSolicitudForm(forms.ModelForm):
    """Formulario para subir archivos adjuntos."""
    
    class Meta:
        model = AdjuntoSolicitud
        fields = ['archivo', 'descripcion']
        widgets = {
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,video/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar'
            }),
            'descripcion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descripción del archivo (opcional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuración Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            Field('archivo'),
            Field('descripcion'),
            Submit('submit', 'Subir Archivo', css_class='btn btn-secondary btn-sm')
        )

class SolicitudMejoraConAdjuntosForm(forms.ModelForm):
    """Formulario para crear solicitud con archivos adjuntos."""
    
    archivos = forms.FileField(
        label='Archivos adjuntos (opcional)',
        help_text='Archivo adjunto. Tamaño máximo: 10MB.',
        required=False
    )
    
    class Meta:
        model = SolicitudMejora
        fields = [
            'titulo', 'descripcion', 'tipo_solicitud', 'modulo_afectado',
            'prioridad', 'pasos_reproducir', 'impacto_negocio', 'solucion_propuesta'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'pasos_reproducir': forms.Textarea(attrs={'rows': 3}),
            'impacto_negocio': forms.Textarea(attrs={'rows': 3}),
            'solucion_propuesta': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configuración Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('<h4><i class="fas fa-edit me-2"></i>Información de la Solicitud</h4><hr>'),
            Row(
                Column('titulo', css_class='form-group col-md-8 mb-0'),
                Column('tipo_solicitud', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('modulo_afectado', css_class='form-group col-md-6 mb-0'),
                Column('prioridad', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Field('descripcion'),
            HTML('<h5 class="mt-4"><i class="fas fa-info-circle me-2"></i>Información Adicional <small class="text-muted">(Opcional)</small></h5>'),
            Field('pasos_reproducir'),
            Field('impacto_negocio'),
            Field('solucion_propuesta'),
            HTML('<h5 class="mt-4"><i class="fas fa-paperclip me-2"></i>Archivos Adjuntos <small class="text-muted">(Opcional)</small></h5>'),
            HTML('''
                <div class="upload-preview-area border rounded p-3 mb-3" style="background-color: #f8f9fa;">
                    <div class="d-flex align-items-center mb-2">
                        <i class="fas fa-cloud-upload-alt me-2 text-muted"></i>
                        <span class="text-muted">Selecciona archivos para adjuntar a tu solicitud</span>
                    </div>
                    <div id="archivos-preview" class="mt-2"></div>
                </div>
            '''),
            Field('archivos'),
            Submit('submit', 'Crear Solicitud', css_class='btn btn-primary btn-lg')
        )
    
    def clean_archivos(self):
        archivos = self.files.getlist('archivos')
        
        if not archivos:
            return []
        
        # Validar cada archivo
        max_size = 10 * 1024 * 1024  # 10MB
        allowed_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',  # Imágenes
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',  # Videos
            '.mp3', '.wav', '.flac', '.aac', '.ogg',  # Audio
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt',  # Documentos
            '.zip', '.rar'  # Comprimidos
        ]
        
        for archivo in archivos:
            # Validar tamaño
            if archivo.size > max_size:
                raise forms.ValidationError(
                    f'El archivo "{archivo.name}" es demasiado grande. '
                    f'Tamaño máximo permitido: 10MB'
                )
            
            # Validar extensión
            import os
            _, ext = os.path.splitext(archivo.name.lower())
            if ext not in allowed_extensions:
                raise forms.ValidationError(
                    f'Tipo de archivo no permitido: "{archivo.name}". '
                    f'Extensiones permitidas: {", ".join(allowed_extensions)}'
                )
        
        return archivos

class FiltroSolicitudesForm(forms.Form):
    """Formulario para filtrar solicitudes en la lista."""
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + SolicitudMejora.ESTADO_CHOICES,
        required=False
    )
    tipo_solicitud = forms.ChoiceField(
        choices=[('', 'Todos los tipos')] + SolicitudMejora.TIPO_CHOICES,
        required=False
    )
    modulo_afectado = forms.ChoiceField(
        choices=[('', 'Todos los módulos')] + SolicitudMejora.MODULO_CHOICES,
        required=False
    )
    prioridad = forms.ChoiceField(
        choices=[('', 'Todas las prioridades')] + SolicitudMejora.PRIORIDAD_CHOICES,
        required=False
    )
    asignado_a = forms.ModelChoiceField(
        queryset=User.objects.filter(is_staff=True),
        required=False,
        empty_label="Todos los asignados"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuración Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('estado', css_class='form-group col-md-2 mb-0'),
                Column('tipo_solicitud', css_class='form-group col-md-3 mb-0'),
                Column('modulo_afectado', css_class='form-group col-md-2 mb-0'),
                Column('prioridad', css_class='form-group col-md-2 mb-0'),
                Column('asignado_a', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Filtrar', css_class='btn btn-outline-primary btn-sm')
        )