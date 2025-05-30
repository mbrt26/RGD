from django import forms
from django.forms import DateInput, Select
from proyectos.models import Actividad, Proyecto

class ProyectoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Display both the project name and centro de costos in the dropdown
        return f"{obj.nombre_proyecto} - Centro de costo: {obj.centro_costos}"

class ActividadForm(forms.ModelForm):
    # Override the proyecto field to use our custom field
    proyecto = ProyectoChoiceField(
        queryset=Proyecto.objects.all(),
        label="Proyecto",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
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
