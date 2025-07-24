from django import forms
from django.forms import DateInput, Select
from proyectos.models import Actividad, Proyecto
from colaboradores.models import Colaborador

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
            'responsable_asignado', 'responsable_ejecucion',
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
            'responsable_asignado': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_responsable_asignado'
            }),
            'responsable_ejecucion': forms.Select(attrs={
                'class': 'form-control',
                'id': 'id_responsable_ejecucion'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar el queryset para responsable_asignado
        self.fields['responsable_asignado'].queryset = Colaborador.objects.all().order_by('nombre')
        self.fields['responsable_asignado'].empty_label = "--- Seleccione un colaborador ---"
        
        # Agregar help text
        self.fields['responsable_asignado'].help_text = 'Colaborador de RGD Aire responsable de esta actividad'
        self.fields['responsable_ejecucion'].help_text = 'Indica quién ejecutará la actividad'
