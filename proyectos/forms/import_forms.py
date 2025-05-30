from django import forms

class ActividadImportForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Seleccione un archivo Excel (.xlsx)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx'
        })
    )
    proyecto = forms.ModelChoiceField(
        queryset=None,
        label='Proyecto',
        help_text='Seleccione el proyecto para las actividades importadas',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        proyecto_queryset = kwargs.pop('proyecto_queryset', None)
        super().__init__(*args, **kwargs)
        if proyecto_queryset is not None:
            self.fields['proyecto'].queryset = proyecto_queryset
