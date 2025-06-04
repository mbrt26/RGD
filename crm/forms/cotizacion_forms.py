from django import forms
from django.forms import ValidationError
from ..models import Cotizacion, VersionCotizacion, Cliente, Trato

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'trato', 'estado', 'notas']


class VersionCotizacionForm(forms.ModelForm):
    class Meta:
        model = VersionCotizacion
        fields = ['version', 'archivo', 'razon_cambio', 'valor']


class CotizacionConVersionForm(forms.ModelForm):
    archivo = forms.FileField(label='Archivo', required=False)
    razon_cambio = forms.CharField(widget=forms.Textarea, label='Razón del Cambio', required=False)
    valor = forms.DecimalField(max_digits=12, decimal_places=2, label='Valor')

    class Meta:
        model = Cotizacion
        fields = ['cliente', 'trato', 'estado', 'notas', 'valor']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all()
        
        # Try to set trato queryset based on selected cliente
        if 'cliente' in self.data:
            try:
                cliente_id = int(self.data.get('cliente'))
                self.fields['trato'].queryset = Trato.objects.filter(cliente_id=cliente_id)
            except (ValueError, TypeError):
                self.fields['trato'].queryset = Trato.objects.none()
        elif self.instance.pk and hasattr(self.instance, 'cliente') and self.instance.cliente is not None:
            # Only try to filter tratos if we have a saved instance with a cliente
            self.fields['trato'].queryset = Trato.objects.filter(cliente=self.instance.cliente)
        else:
            self.fields['trato'].queryset = Trato.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and not cleaned_data.get('archivo'):
            raise ValidationError('El archivo es requerido para crear una nueva cotización')
        return cleaned_data
