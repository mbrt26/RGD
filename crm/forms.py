from django import forms
from .models import Cotizacion, VersionCotizacion

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'trato', 'monto', 'estado', 'notas']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class VersionCotizacionForm(forms.ModelForm):
    class Meta:
        model = VersionCotizacion
        fields = ['archivo', 'razon_cambio', 'valor']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        # El campo archivo no debe tener la clase form-control
        self.fields['archivo'].widget.attrs.update({'class': 'form-control-file'})

class CotizacionConVersionForm(forms.ModelForm):
    archivo = forms.FileField(label='Archivo de cotización', required=True)
    razon_cambio = forms.CharField(widget=forms.Textarea, label='Razón del cambio', required=True)
    
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'trato', 'monto', 'estado', 'notas']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['archivo'].widget.attrs.update({'class': 'form-control-file'})