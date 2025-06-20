from django import forms
from django.forms import ValidationError
from ..models import Cotizacion, VersionCotizacion, Cliente, Trato

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = ['cliente', 'trato', 'notas']


class VersionCotizacionForm(forms.ModelForm):
    class Meta:
        model = VersionCotizacion
        fields = ['version', 'archivo', 'razon_cambio', 'valor']


class CotizacionConVersionForm(forms.ModelForm):
    razon_cambio = forms.CharField(widget=forms.Textarea, label='Razón del Cambio', required=True)
    valor = forms.DecimalField(max_digits=12, decimal_places=2, label='Valor')

    class Meta:
        model = Cotizacion
        fields = ['cliente', 'trato', 'notas']

    def __init__(self, *args, **kwargs):
        # Extraer parámetros adicionales antes de llamar super()
        initial_cliente = kwargs.pop('initial_cliente', None)
        initial_trato = kwargs.pop('initial_trato', None)
        
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Si hay un cliente inicial, filtrar los tratos por ese cliente
        if initial_cliente:
            self.fields['trato'].queryset = Trato.objects.filter(cliente=initial_cliente).order_by('-fecha_creacion')
            # Si hay un trato inicial, establecerlo como seleccionado
            if initial_trato:
                self.fields['trato'].initial = initial_trato
        
        # Si estamos editando una cotización existente, filtrar por el cliente de la cotización
        elif self.instance and self.instance.pk and self.instance.cliente:
            self.fields['trato'].queryset = Trato.objects.filter(cliente=self.instance.cliente).order_by('-fecha_creacion')
        
        # Try to set trato queryset based on selected cliente
        elif 'cliente' in self.data:
            try:
                cliente_id = int(self.data.get('cliente'))
                self.fields['trato'].queryset = Trato.objects.filter(cliente_id=cliente_id).order_by('-fecha_creacion')
            except (ValueError, TypeError):
                self.fields['trato'].queryset = Trato.objects.none()
        else:
            self.fields['trato'].queryset = Trato.objects.all().order_by('-fecha_creacion')

    def clean(self):
        cleaned_data = super().clean()
        # La validación de archivos se maneja en la vista ya que necesitamos acceso a request.FILES
        return cleaned_data
