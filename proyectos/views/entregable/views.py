from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from proyectos.models import EntregaDocumental, Proyecto, EntregableProyecto


class EntregaDocumentalListView(LoginRequiredMixin, ListView):
    model = EntregaDocumental
    template_name = 'proyectos/entregable/list.html'
    context_object_name = 'entregables'
    ordering = ['-fecha_entrega']
    title = 'Entregables'
    add_url = 'proyectos:entregable_create'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['view'] = {'add_url': self.add_url}
        return context


class EntregaDocumentalCreateView(LoginRequiredMixin, CreateView):
    model = EntregaDocumental
    template_name = 'proyectos/entregable/form.html'
    fields = ['nombre', 'proyecto', 'descripcion', 'fecha_entrega', 'estado', 'archivo']
    success_url = reverse_lazy('proyectos:entregable_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Entregable'
        return context


class EntregaDocumentalDetailView(LoginRequiredMixin, DetailView):
    model = EntregaDocumental
    template_name = 'proyectos/entregable/detail.html'
    context_object_name = 'entregable'


class EntregaDocumentalUpdateView(LoginRequiredMixin, UpdateView):
    model = EntregaDocumental
    template_name = 'proyectos/entregable/form.html'
    fields = ['nombre', 'proyecto', 'descripcion', 'fecha_entrega', 'estado', 'archivo']
    success_url = reverse_lazy('proyectos:entregable_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Entregable: {self.object}'
        return context


class GestionEntregablesView(LoginRequiredMixin, TemplateView):
    """Vista principal para gestionar los entregables de un proyecto"""
    template_name = 'proyectos/entregables/gestion.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyectos'] = Proyecto.objects.all().order_by('-fecha_creacion')
        
        # Si se seleccionó un proyecto
        proyecto_id = self.request.GET.get('proyecto')
        if proyecto_id:
            try:
                proyecto = Proyecto.objects.get(id=proyecto_id)
                context['proyecto_seleccionado'] = proyecto
                
                # Cargar entregables desde JSON si no existen
                if not proyecto.entregables_proyecto.exists():
                    EntregableProyecto.cargar_entregables_desde_json(proyecto)
                
                # Obtener entregables agrupados por fase
                entregables = proyecto.entregables_proyecto.all()
                context['entregables_por_fase'] = {
                    'Definición': entregables.filter(fase='Definición'),
                    'Planeación': entregables.filter(fase='Planeación'),
                    'Ejecución': entregables.filter(fase='Ejecución'),
                    'Entrega': entregables.filter(fase='Entrega'),
                }
                
            except Proyecto.DoesNotExist:
                messages.error(self.request, 'Proyecto no encontrado.')
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Procesar la actualización de entregables seleccionados"""
        proyecto_id = request.POST.get('proyecto_id')
        if not proyecto_id:
            messages.error(request, 'Debe seleccionar un proyecto.')
            return redirect('proyectos:gestion_entregables')
        
        try:
            proyecto = Proyecto.objects.get(id=proyecto_id)
            
            # Actualizar selección de entregables
            entregables_seleccionados = request.POST.getlist('entregables')
            
            # Primero, deseleccionar todos los no obligatorios
            proyecto.entregables_proyecto.filter(obligatorio=False).update(seleccionado=False)
            
            # Luego, seleccionar los marcados
            for entregable_id in entregables_seleccionados:
                try:
                    entregable = proyecto.entregables_proyecto.get(id=entregable_id)
                    entregable.seleccionado = True
                    entregable.save()
                except EntregableProyecto.DoesNotExist:
                    continue
            
            messages.success(request, f'Entregables actualizados para el proyecto {proyecto.nombre_proyecto}')
            return redirect(f'{reverse_lazy("proyectos:gestion_entregables")}?proyecto={proyecto_id}')
            
        except Proyecto.DoesNotExist:
            messages.error(request, 'Proyecto no encontrado.')
            return redirect('proyectos:gestion_entregables')


class EntregableProyectoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar un entregable específico del proyecto"""
    model = EntregableProyecto
    template_name = 'proyectos/entregables/entregable_form.html'
    fields = ['estado', 'archivo', 'fecha_entrega', 'observaciones']
    
    def get_success_url(self):
        return f'{reverse_lazy("proyectos:gestion_entregables")}?proyecto={self.object.proyecto.id}'
    
    def form_valid(self, form):
        messages.success(self.request, f'Entregable {self.object.codigo} actualizado correctamente.')
        return super().form_valid(form)


def cargar_entregables_proyecto(request, proyecto_id):
    """Vista AJAX para cargar entregables de un proyecto"""
    try:
        proyecto = Proyecto.objects.get(id=proyecto_id)
        
        # Cargar entregables desde JSON si no existen
        if not proyecto.entregables_proyecto.exists():
            EntregableProyecto.cargar_entregables_desde_json(proyecto)
        
        entregables_data = []
        for entregable in proyecto.entregables_proyecto.all():
            entregables_data.append({
                'id': entregable.id,
                'codigo': entregable.codigo,
                'nombre': entregable.nombre,
                'fase': entregable.fase,
                'obligatorio': entregable.obligatorio,
                'seleccionado': entregable.seleccionado,
                'estado': entregable.estado,
                'creador': entregable.creador,
                'consolidador': entregable.consolidador,
            })
        
        return JsonResponse({
            'success': True,
            'entregables': entregables_data,
            'proyecto': {
                'id': proyecto.id,
                'nombre': proyecto.nombre_proyecto,
                'cliente': proyecto.cliente
            }
        })
        
    except Proyecto.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Proyecto no encontrado'
        }, status=404)
