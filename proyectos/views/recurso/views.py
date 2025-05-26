from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from proyectos.models import Recurso

class RecursoListView(LoginRequiredMixin, ListView):
    model = Recurso
    template_name = 'proyectos/recurso/list.html'
    context_object_name = 'recursos'
    title = 'Lista de Recursos'
    add_url = 'proyectos:recurso_create'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['view'] = {'add_url': self.add_url}
        return context

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