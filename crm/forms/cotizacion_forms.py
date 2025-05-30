from django import forms
from ..models import Cotizacion, VersionCotizacion

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'trato', 'estado', 'notas']


class VersionCotizacionForm(forms.ModelForm):
    class Meta:
        model = VersionCotizacion
        fields = ['version', 'archivo', 'razon_cambio', 'valor']

class CotizacionConVersionForm(forms.Form):
    # Campos de Cotizacion
    cliente = forms.ModelChoiceField(queryset=None, label='Cliente')
    trato = forms.ModelChoiceField(queryset=None, required=False, label='Trato')
    estado = forms.ChoiceField(choices=Cotizacion.ESTADO_CHOICES, initial='borrador', label='Estado')
    notas = forms.CharField(widget=forms.Textarea, required=False, label='Notas')
    
    # Campos de VersionCotizacion
    version = forms.IntegerField(min_value=1, initial=1, label='Número de Versión')
    archivo = forms.FileField(label='Archivo')
    razon_cambio = forms.CharField(widget=forms.Textarea, label='Razón del Cambio')
    valor = forms.DecimalField(max_digits=12, decimal_places=2, label='Valor')

    def __init__(self, *args, **kwargs):
        from ..models import Cliente, Trato
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.all()
        if 'cliente' in self.data:
            try:
                cliente_id = int(self.data.get('cliente'))
                self.fields['trato'].queryset = Trato.objects.filter(cliente_id=cliente_id)
            except (ValueError, TypeError):
                pass
