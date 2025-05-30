from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField
from datetime import timedelta
import openpyxl
from openpyxl.styles import Font, PatternFill
import io
from proyectos.models import EntregaDocumental, Proyecto, EntregableProyecto
from proyectos.forms.entregable_forms import (
    EntregableProyectoForm, ConfiguracionMasivaForm, FiltroEntregablesForm
)


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


class EntregablesDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard principal con estadísticas de entregables"""
    template_name = 'proyectos/entregables/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['stats'] = {
            'proyectos_con_entregables': Proyecto.objects.filter(
                entregables_proyecto__isnull=False
            ).distinct().count(),
            'entregables_pendientes': EntregableProyecto.objects.filter(
                estado='pendiente', seleccionado=True
            ).count(),
            'entregables_completados': EntregableProyecto.objects.filter(
                estado='completado'
            ).count(),
            'entregables_vencidos': EntregableProyecto.objects.filter(
                fecha_entrega__lt=timezone.now().date(),
                estado__in=['pendiente', 'en_proceso']
            ).count()
        }
        
        # Entregables próximos a vencer (próximos 7 días)
        fecha_limite = timezone.now().date() + timedelta(days=7)
        context['entregables_proximos'] = EntregableProyecto.objects.filter(
            fecha_entrega__lte=fecha_limite,
            fecha_entrega__gte=timezone.now().date(),
            estado__in=['pendiente', 'en_proceso'],
            seleccionado=True
        ).select_related('proyecto')[:10]
        
        # Proyectos sin entregables configurados
        context['proyectos_sin_entregables'] = Proyecto.objects.filter(
            entregables_proyecto__isnull=True,
            estado__in=['en_progreso', 'iniciado']
        )[:5]
        
        return context


class ConfiguracionMasivaEntregablesView(LoginRequiredMixin, TemplateView):
    """Vista para configurar entregables en múltiples proyectos"""
    template_name = 'proyectos/entregables/configuracion_masiva.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyectos'] = Proyecto.objects.filter(
            estado__in=['en_progreso', 'iniciado']
        ).order_by('-fecha_creacion')
        return context
    
    def post(self, request, *args, **kwargs):
        proyectos_ids = request.POST.getlist('proyectos')
        accion = request.POST.get('accion')
        
        if accion == 'cargar_entregables':
            for proyecto_id in proyectos_ids:
                try:
                    proyecto = Proyecto.objects.get(id=proyecto_id)
                    if not proyecto.entregables_proyecto.exists():
                        EntregableProyecto.cargar_entregables_desde_json(proyecto)
                except Proyecto.DoesNotExist:
                    continue
                    
            messages.success(request, f'Entregables cargados para {len(proyectos_ids)} proyectos.')
        
        return redirect('proyectos:configuracion_masiva_entregables')


class EntregablesFiltradosView(LoginRequiredMixin, ListView):
    """Vista con filtros avanzados para entregables"""
    model = EntregableProyecto
    template_name = 'proyectos/entregables/filtrados.html'
    context_object_name = 'entregables'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = EntregableProyecto.objects.select_related('proyecto')
        
        # Filtros
        fase = self.request.GET.get('fase')
        estado = self.request.GET.get('estado')
        proyecto_id = self.request.GET.get('proyecto')
        obligatorio = self.request.GET.get('obligatorio')
        vencidos = self.request.GET.get('vencidos')
        
        if fase:
            queryset = queryset.filter(fase=fase)
        if estado:
            queryset = queryset.filter(estado=estado)
        if proyecto_id:
            queryset = queryset.filter(proyecto_id=proyecto_id)
        if obligatorio:
            queryset = queryset.filter(obligatorio=obligatorio == 'true')
        if vencidos == 'true':
            queryset = queryset.filter(
                fecha_entrega__lt=timezone.now().date(),
                estado__in=['pendiente', 'en_proceso']
            )
            
        return queryset.order_by('-fecha_actualizacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyectos'] = Proyecto.objects.all().order_by('nombre_proyecto')
        context['fases'] = EntregableProyecto.PHASE_CHOICES
        context['estados'] = EntregableProyecto.ESTADO_CHOICES
        
        # Fechas para comparación en template
        context['today'] = timezone.now().date()
        context['fecha_limite'] = timezone.now().date() + timedelta(days=7)
        
        # Mantener filtros seleccionados
        context['filtros'] = {
            'fase': self.request.GET.get('fase', ''),
            'estado': self.request.GET.get('estado', ''),
            'proyecto': self.request.GET.get('proyecto', ''),
            'obligatorio': self.request.GET.get('obligatorio', ''),
            'vencidos': self.request.GET.get('vencidos', ''),
        }
        
        return context


class ReporteEntregablesView(LoginRequiredMixin, TemplateView):
    """Genera reportes de entregables en Excel"""
    
    def get(self, request, *args, **kwargs):
        # Crear workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte Entregables"
        
        # Headers
        headers = [
            'Proyecto', 'Cliente', 'Código', 'Nombre', 'Fase', 'Estado',
            'Obligatorio', 'Seleccionado', 'Fecha Entrega', 'Creador',
            'Consolidador', 'Archivo'
        ]
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Datos
        entregables = EntregableProyecto.objects.select_related('proyecto').all()
        for row, entregable in enumerate(entregables, 2):
            ws.cell(row=row, column=1, value=entregable.proyecto.nombre_proyecto)
            ws.cell(row=row, column=2, value=entregable.proyecto.cliente)
            ws.cell(row=row, column=3, value=entregable.codigo)
            ws.cell(row=row, column=4, value=entregable.nombre)
            ws.cell(row=row, column=5, value=entregable.fase)
            ws.cell(row=row, column=6, value=entregable.get_estado_display())
            ws.cell(row=row, column=7, value='Sí' if entregable.obligatorio else 'No')
            ws.cell(row=row, column=8, value='Sí' if entregable.seleccionado else 'No')
            ws.cell(row=row, column=9, value=entregable.fecha_entrega)
            ws.cell(row=row, column=10, value=entregable.creador)
            ws.cell(row=row, column=11, value=entregable.consolidador)
            ws.cell(row=row, column=12, value='Sí' if entregable.archivo else 'No')
        
        # Respuesta
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=reporte_entregables.xlsx'
        
        # Guardar en memoria
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        response.write(buffer.getvalue())
        
        return response
