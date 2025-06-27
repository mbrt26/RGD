from django import forms
from django.core.exceptions import ValidationError
from crm.models import Trato, Cliente, Contacto
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
            'nombre_proyecto', 'orden_contrato', 'tipo_negociacion'
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
        
        # Configure numero_oferta field
        self.fields['numero_oferta'].required = False
        self.fields['numero_oferta'].help_text = 'Deje vacío para asignar automáticamente'
        
        # Configure date input formats
        self.fields['fecha_creacion'].input_formats = ['%Y-%m-%d']
        
        # Set up querysets for related fields
        self.fields['cliente'].queryset = Cliente.objects.all()
        self.fields['contacto'].queryset = Contacto.objects.all()
        self.fields['responsable'].queryset = User.objects.filter(is_active=True)
    
    def clean_numero_oferta(self):
        """
        Validate that manual offer numbers don't conflict with existing ones.
        """
        numero_oferta = self.cleaned_data.get('numero_oferta')
        
        if numero_oferta:
            # Check if this number already exists (excluding current instance for updates)
            existing_query = Trato.objects.filter(numero_oferta=numero_oferta)
            if self.instance.pk:
                existing_query = existing_query.exclude(pk=self.instance.pk)
            
            if existing_query.exists():
                raise ValidationError(
                    f'El número de oferta {numero_oferta} ya existe. '
                    f'Use un número diferente o deje el campo vacío para asignar automáticamente.'
                )
        
        return numero_oferta