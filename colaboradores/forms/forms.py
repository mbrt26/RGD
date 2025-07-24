from django import forms
from colaboradores.models import Colaborador

class ColaboradorImportForm(forms.Form):
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Seleccione el archivo Excel con los datos de colaboradores',
        widget=forms.FileInput(attrs={'accept': '.xlsx,.xls'})
    )
    
    def clean_archivo_excel(self):
        archivo = self.cleaned_data['archivo_excel']
        
        if archivo:
            extension = archivo.name.split('.')[-1].lower()
            if extension not in ['xlsx', 'xls']:
                raise forms.ValidationError('Solo se permiten archivos Excel (.xlsx o .xls)')
            
            # Verificar tamaño del archivo (máximo 5MB)
            if archivo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo no debe superar los 5MB')
        
        return archivo