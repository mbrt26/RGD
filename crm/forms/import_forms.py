from django import forms

class ClienteImportForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Seleccione un archivo Excel (.xlsx)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx'
        })
    )

class TratoImportForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Seleccione un archivo Excel (.xlsx)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx'
        })
    )

class ContactoImportForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Seleccione un archivo Excel (.xlsx)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx'
        })
    )
