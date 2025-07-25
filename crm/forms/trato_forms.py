from django import forms
from django.core.exceptions import ValidationError
from crm.models import Trato, Cliente, Contacto, RepresentanteVentas
from django.contrib.auth import get_user_model

User = get_user_model()

class TratoForm(forms.ModelForm):
    """
    Form for creating and editing Trato (Deal) instances.
    Handles manual offer number entry with validation.
    """
    
    class Meta:
        model = Trato
        fields = [
            'numero_oferta', 'nombre', 'cliente', 'contacto', 'correo', 'telefono', 
            'descripcion', 'valor', 'probabilidad', 'estado', 'fuente', 
            'fecha_creacion', 'fecha_cierre', 'fecha_envio_cotizacion', 
            'dias_prometidos', 'responsable', 'notas', 'centro_costos', 
            'nombre_proyecto', 'orden_contrato', 'tipo_negociacion', 'subclasificacion_comercial'
        ]
        widgets = {
            'fecha_creacion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_cierre': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'fecha_envio_cotizacion': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configure numero_oferta field as read-only
        self.fields['numero_oferta'].required = False
        self.fields['numero_oferta'].help_text = 'Se asigna automáticamente al guardar'
        self.fields['numero_oferta'].widget.attrs['readonly'] = True
        self.fields['numero_oferta'].widget.attrs['class'] = 'form-control-plaintext'
        self.fields['numero_oferta'].widget.attrs['tabindex'] = '-1'
        
        # Configure date input formats
        self.fields['fecha_creacion'].input_formats = ['%Y-%m-%d']
        
        # Set up querysets for related fields
        self.fields['cliente'].queryset = Cliente.objects.all()
        self.fields['contacto'].queryset = Contacto.objects.all()
        # Usar representantes de ventas para el campo responsable
        self.fields['responsable'].queryset = User.objects.filter(
            representanteventas__isnull=False
        ).distinct()
        self.fields['responsable'].empty_label = "--- Seleccione un representante ---"
    
    def clean_numero_oferta(self):
        """
        Ensure numero_oferta is not manually modified.
        For new instances, it will be auto-assigned.
        For existing instances, preserve the current value.
        """
        if self.instance.pk:
            # For existing instances, always use the current value
            return self.instance.numero_oferta
        else:
            # For new instances, return None to trigger auto-assignment
            return None