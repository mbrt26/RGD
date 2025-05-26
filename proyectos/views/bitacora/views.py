from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
from proyectos.models import Bitacora, Proyecto, Actividad, Colaborador

@require_http_methods(["GET"])
def get_actividades_por_proyecto(request, proyecto_id):
    """Vista AJAX que devuelve las actividades de un proyecto específico"""
    try:
        actividades = Actividad.objects.filter(
            proyecto_id=proyecto_id,
            estado__in=['no_iniciado', 'en_proceso']  # Solo actividades no finalizadas
        ).values('id', 'actividad').order_by('actividad')
        return JsonResponse(list(actividades), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

class BitacoraListView(LoginRequiredMixin, ListView):
    model = Bitacora
    template_name = 'proyectos/bitacora/list.html'
    context_object_name = 'bitacoras'
    ordering = ['-fecha_registro']
    title = 'Bitácora de Actividades'
    add_url = 'proyectos:bitacora_create'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['view'] = {'add_url': self.add_url}
        return context

class BitacoraCreateView(LoginRequiredMixin, CreateView):
    model = Bitacora
    template_name = 'proyectos/bitacora/form.html'
    fields = ['proyecto', 'actividad', 'subactividad', 'descripcion', 'duracion_horas', 'equipo', 'observaciones', 'imagen', 'archivo']
    success_url = reverse_lazy('proyectos:bitacora_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nueva Entrada de Bitácora'
        return context
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Si hay un proyecto seleccionado, mostrar sus actividades
        if form.instance.proyecto_id:
            form.fields['actividad'].queryset = Actividad.objects.filter(
                proyecto_id=form.instance.proyecto_id,
                estado__in=['no_iniciado', 'en_proceso']
            )
        elif form.data.get('proyecto'):
            # Si el formulario fue enviado, mostrar las actividades del proyecto seleccionado
            form.fields['actividad'].queryset = Actividad.objects.filter(
                proyecto_id=form.data['proyecto'],
                estado__in=['no_iniciado', 'en_proceso']
            )
        else:
            # Si no hay proyecto seleccionado, mostrar queryset vacío
            form.fields['actividad'].queryset = Actividad.objects.none()
            
        return form

    def form_valid(self, form):
        user = self.request.user
        # Obtener o crear el Colaborador basado en el usuario actual
        colaborador, created = Colaborador.objects.get_or_create(
            email=user.email,
            defaults={
                'nombre': f"{user.first_name} {user.last_name}".strip() or user.username,
                'cargo': 'Usuario del Sistema',
                'telefono': ''
            }
        )
        
        form.instance.responsable = colaborador
        messages.success(self.request, 'Entrada de bitácora creada exitosamente.')
        return super().form_valid(form)

class BitacoraDetailView(LoginRequiredMixin, DetailView):
    model = Bitacora
    template_name = 'proyectos/bitacora/detail.html'
    context_object_name = 'bitacora'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recursos'] = self.object.recursos.all()
        return context

class BitacoraUpdateView(LoginRequiredMixin, UpdateView):
    model = Bitacora
    template_name = 'proyectos/bitacora/form.html'
    fields = ['proyecto', 'actividad', 'subactividad', 'descripcion', 'duracion_horas', 'equipo', 'observaciones', 'imagen', 'archivo']
    success_url = reverse_lazy('proyectos:bitacora_list')