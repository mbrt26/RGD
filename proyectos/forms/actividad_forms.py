from django import forms
from django.forms import DateInput
from proyectos.models import Actividad

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            'proyecto', 'actividad', 'inicio', 'fin',
            'duracion', 'estado', 'avance', 'predecesoras',
            'observaciones', 'adjuntos'
        ]
        widgets = {
            'inicio': DateInput(attrs={
                'type': 'date', 
                'class': 'form-control datepicker',
                'id': 'id_inicio'
            }),
            'fin': DateInput(attrs={
                'type': 'date', 
                'class': 'form-control datepicker',
                'id': 'id_fin'
            }),
            'duracion': forms.NumberInput(attrs={
                'class': 'form-control',
                'id': 'id_duracion',
                'min': '1'
            }),
        }
