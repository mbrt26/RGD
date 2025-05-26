from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.db.models import Q, Count, Case, When, IntegerField, F, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.forms import DateInput

from proyectos.models import Actividad, Proyecto, Bitacora
from proyectos.forms.actividad_forms import ActividadForm


class ActividadListView(LoginRequiredMixin, ListView):
    model = Actividad
    template_name = 'proyectos/actividad/list.html'
    context_object_name = 'actividades'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('proyecto')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(actividad__icontains=search) |
                Q(proyecto__nombre_proyecto__icontains=search) |
                Q(proyecto__cliente__icontains=search)
            )
        
        # Filtro por proyecto
        proyecto_id = self.request.GET.get('proyecto_id')
        if proyecto_id:
            queryset = queryset.filter(proyecto_id=proyecto_id)
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Anotar con información adicional
        return queryset.annotate(
            dias_restantes=Case(
                When(fin__lt=timezone.now().date(), then=Value(0)),
                default=F('fin') - timezone.now().date(),
                output_field=IntegerField()
            ),
            total_horas=Coalesce(Count('bitacoras'), 0)
        ).order_by('inicio', 'fin')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = dict(Actividad.ESTADOS_CHOICES)
        
        # Si se está filtrando por proyecto, agregar el proyecto al contexto
        proyecto_id = self.request.GET.get('proyecto_id')
        if proyecto_id:
            context['proyecto'] = get_object_or_404(Proyecto, pk=proyecto_id)
        
        return context


class ActividadCreateView(LoginRequiredMixin, CreateView):
    model = Actividad
    template_name = 'proyectos/actividad/form.html'
    form_class = ActividadForm
    
    def get_success_url(self):
        return reverse('proyectos:actividad_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Actividad creada exitosamente.')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filtrar proyectos activos en el formulario
        form.fields['proyecto'].queryset = Proyecto.objects.filter(estado__in=['pendiente', 'en_progreso'])
        
        # Establecer la fecha mínima para los selectores de fecha
        today = timezone.now().strftime('%Y-%m-%d')
        form.fields['inicio'].widget.attrs['min'] = today
        form.fields['fin'].widget.attrs['min'] = today
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nueva Actividad'
        return context


class ActividadDetailView(LoginRequiredMixin, DetailView):
    model = Actividad
    template_name = 'proyectos/actividad/detail.html'
    context_object_name = 'actividad'
    
    def get_queryset(self):
        return super().get_queryset().select_related('proyecto')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad = self.get_object()
        
        # Obtener bitácoras relacionadas
        context['bitacoras'] = actividad.bitacoras.select_related(
            'responsable'
        ).order_by('-fecha_registro')
        
        return context


class ActividadUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Actividad
    template_name = 'proyectos/actividad/form.html'
    form_class = ActividadForm
    
    def test_func(self):
        actividad = self.get_object()
        return self.request.user.has_perm('proyectos.change_actividad') or \
               self.request.user == actividad.proyecto.lider
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permiso para editar esta actividad.')
        return redirect('proyectos:actividad_list')
    
    def get_success_url(self):
        return reverse('proyectos:actividad_detail', kwargs={'pk': self.object.pk})
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Establecer la fecha mínima para los selectores de fecha
        today = timezone.now().strftime('%Y-%m-%d')
        form.fields['inicio'].widget.attrs['min'] = today
        form.fields['fin'].widget.attrs['min'] = today
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Editar Actividad'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Actividad actualizada exitosamente.')
        return super().form_valid(form)


# Vista para API que devuelve actividades de un proyecto (usada en formularios AJAX)
@require_http_methods(["GET"])
def actividades_por_proyecto(request, proyecto_id):
    """Devuelve las actividades de un proyecto en formato JSON para su uso en AJAX."""
    actividades = Actividad.objects.filter(
        proyecto_id=proyecto_id
    ).values('id', 'actividad')
    return JsonResponse(list(actividades), safe=False)
