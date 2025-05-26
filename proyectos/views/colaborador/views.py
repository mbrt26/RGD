from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from proyectos.models import Colaborador, Bitacora

class ColaboradorListView(LoginRequiredMixin, ListView):
    model = Colaborador
    template_name = 'proyectos/colaborador/list.html'
    context_object_name = 'colaboradores'
    paginate_by = 10
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Colaboradores'
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        print(f"DEBUG - Total colaboradores en la base de datos: {queryset.count()}")
        for c in queryset:
            print(f"DEBUG - Colaborador ID: {c.id}, Nombre: {c.nombre}")
        return queryset.order_by('nombre')

class ColaboradorCreateView(LoginRequiredMixin, CreateView):
    model = Colaborador
    template_name = 'proyectos/colaborador/form.html'
    fields = '__all__'
    success_url = reverse_lazy('proyectos:colaborador_list')

class ColaboradorDetailView(LoginRequiredMixin, DetailView):
    model = Colaborador
    template_name = 'proyectos/colaborador/detail.html'
    context_object_name = 'colaborador'
    pk_url_kwarg = 'id'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        print(f"DEBUG - Colaborador encontrado: {obj.id} - {obj.nombre}")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        colaborador = self.get_object()
        
        # Debug information
        print(f"DEBUG - Context data for colaborador: {colaborador.id} - {colaborador.nombre}")
        print(f"DEBUG - Email: {colaborador.email}, Teléfono: {colaborador.telefono}")
        
        # Get related bitacoras
        bitacoras = Bitacora.objects.filter(responsable=colaborador)
        print(f"DEBUG - Bitácoras encontradas: {bitacoras.count()}")
        
        context['bitacoras'] = bitacoras
        context['debug_info'] = {
            'colaborador_id': colaborador.id,
            'bitacoras_count': bitacoras.count(),
            'all_fields': {field.name: getattr(colaborador, field.name) for field in colaborador._meta.fields}
        }
        return context

class ColaboradorUpdateView(LoginRequiredMixin, UpdateView):
    model = Colaborador
    template_name = 'proyectos/colaborador/form.html'
    fields = '__all__'
    pk_url_kwarg = 'id'
    success_url = reverse_lazy('proyectos:colaborador_list')