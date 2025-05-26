from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Avg
from .models import (
    Proyecto, Actividad, Recurso, 
    Bitacora, BitacoraRecurso, EntregaDocumental
)

class ProyectosDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'proyectos/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_proyectos'] = Proyecto.objects.count()
        context['proyectos_activos'] = Proyecto.objects.filter(avance__lt=100).count()
        context['avance_promedio'] = Proyecto.objects.aggregate(avg=Avg('avance'))['avg'] or 0
        context['actividades_pendientes'] = Actividad.objects.filter(estado='no_iniciado').count()
        return context

# Vistas para Proyecto
class ProyectoListView(LoginRequiredMixin, ListView):
    model = Proyecto
    template_name = 'proyectos/proyecto/list.html'
    context_object_name = 'proyectos'

class ProyectoCreateView(LoginRequiredMixin, CreateView):
    model = Proyecto
    template_name = 'proyectos/proyecto/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:proyecto_list')

class ProyectoDetailView(LoginRequiredMixin, DetailView):
    model = Proyecto
    template_name = 'proyectos/proyecto/detail.html'
    context_object_name = 'proyecto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actividades'] = self.object.actividades.all()
        context['bitacoras'] = self.object.bitacoras.all()
        context['entregables'] = self.object.entregables.all()
        return context

class ProyectoUpdateView(LoginRequiredMixin, UpdateView):
    model = Proyecto
    template_name = 'proyectos/proyecto/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:proyecto_list')

# Vistas para Actividad
class ActividadListView(LoginRequiredMixin, ListView):
    model = Actividad
    template_name = 'proyectos/actividad/list.html'
    context_object_name = 'actividades'

class ActividadCreateView(LoginRequiredMixin, CreateView):
    model = Actividad
    template_name = 'proyectos/actividad/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:actividad_list')

class ActividadDetailView(LoginRequiredMixin, DetailView):
    model = Actividad
    template_name = 'proyectos/actividad/detail.html'
    context_object_name = 'actividad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bitacoras'] = self.object.bitacoras.all()
        return context

class ActividadUpdateView(LoginRequiredMixin, UpdateView):
    model = Actividad
    template_name = 'proyectos/actividad/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:actividad_list')

# Vistas para Recurso
class RecursoListView(LoginRequiredMixin, ListView):
    model = Recurso
    template_name = 'proyectos/recurso/list.html'
    context_object_name = 'recursos'

class RecursoCreateView(LoginRequiredMixin, CreateView):
    model = Recurso
    template_name = 'proyectos/recurso/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:recurso_list')

class RecursoDetailView(LoginRequiredMixin, DetailView):
    model = Recurso
    template_name = 'proyectos/recurso/detail.html'
    context_object_name = 'recurso'

class RecursoUpdateView(LoginRequiredMixin, UpdateView):
    model = Recurso
    template_name = 'proyectos/recurso/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:recurso_list')

# Vistas para Bitácora
class BitacoraListView(LoginRequiredMixin, ListView):
    model = Bitacora 
    template_name = 'proyectos/bitacora/list.html'
    context_object_name = 'bitacoras'
    ordering = ['-fecha_registro']

class BitacoraCreateView(LoginRequiredMixin, CreateView):
    model = Bitacora
    template_name = 'proyectos/bitacora/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:bitacora_list')

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
    fields = '__all__'
    success_url = reverse_lazy('proyectos:bitacora_list')

# Vistas para EntregaDocumental 
class EntregaDocumentalListView(LoginRequiredMixin, ListView):
    model = EntregaDocumental
    template_name = 'proyectos/entregable/list.html'
    context_object_name = 'entregables'

class EntregaDocumentalCreateView(LoginRequiredMixin, CreateView):
    model = EntregaDocumental
    template_name = 'proyectos/entregable/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:entregable_list')

class EntregaDocumentalDetailView(LoginRequiredMixin, DetailView):
    model = EntregaDocumental 
    template_name = 'proyectos/entregable/detail.html'
    context_object_name = 'entregable'

class EntregaDocumentalUpdateView(LoginRequiredMixin, UpdateView):
    model = EntregaDocumental
    template_name = 'proyectos/entregable/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:entregable_list')
