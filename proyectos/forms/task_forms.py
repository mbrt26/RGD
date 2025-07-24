from django import forms
from django.contrib.auth import get_user_model
from tasks.models import Task, TaskCategory
from colaboradores.models import Colaborador
import json

User = get_user_model()


class ComiteTareaForm(forms.Form):
    """Formulario para crear tareas desde el seguimiento de comité"""
    
    titulo = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título de la tarea...'
        })
    )
    
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Descripción de la tarea...'
        })
    )
    
    responsable = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    fecha_vencimiento = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    prioridad = forms.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar usuarios por nombre
        self.fields['responsable'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')


class TareasComiteFormSet(forms.Form):
    """Formulario para manejar múltiples tareas desde el comité"""
    
    tareas_json = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    def clean_tareas_json(self):
        tareas_json = self.cleaned_data.get('tareas_json', '[]')
        try:
            tareas = json.loads(tareas_json) if tareas_json else []
            
            # Validar cada tarea
            for i, tarea in enumerate(tareas):
                if not tarea.get('titulo'):
                    raise forms.ValidationError(f'La tarea {i+1} debe tener un título')
                if not tarea.get('responsable'):
                    raise forms.ValidationError(f'La tarea {i+1} debe tener un responsable')
                if not tarea.get('fecha_vencimiento'):
                    raise forms.ValidationError(f'La tarea {i+1} debe tener una fecha de vencimiento')
                    
            return tareas
            
        except json.JSONDecodeError:
            raise forms.ValidationError('Formato de datos inválido')
    
    def save(self, seguimiento, usuario_creador):
        """Crea las tareas y las asocia al seguimiento"""
        tareas = self.cleaned_data.get('tareas_json', [])
        tareas_creadas = []
        
        # Obtener o crear categoría para proyectos
        categoria, _ = TaskCategory.objects.get_or_create(
            name='Comité',
            module='proyectos',
            defaults={
                'description': 'Tareas generadas desde seguimiento de comité',
                'color': '#6c757d'
            }
        )
        
        for tarea_data in tareas:
            # Crear la tarea
            tarea = Task.objects.create(
                title=tarea_data['titulo'],
                description=tarea_data.get('descripcion', ''),
                assigned_to_id=tarea_data['responsable'],
                created_by=usuario_creador,
                due_date=tarea_data['fecha_vencimiento'],
                priority=tarea_data.get('prioridad', 'medium'),
                category=categoria,
                proyecto_relacionado=seguimiento.proyecto if hasattr(seguimiento, 'proyecto') else None,
                centro_costos=seguimiento.centro_costos if hasattr(seguimiento, 'centro_costos') else None,
                task_type='task',
                status='pending'
            )
            
            tareas_creadas.append(tarea)
            
        # Asociar las tareas al seguimiento
        if hasattr(seguimiento, 'tareas_generadas'):
            seguimiento.tareas_generadas.add(*tareas_creadas)
        elif hasattr(seguimiento, 'tareas'):
            seguimiento.tareas.add(*tareas_creadas)
        
        return tareas_creadas