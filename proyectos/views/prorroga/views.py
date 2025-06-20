from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

from proyectos.models import ProrrogaProyecto, Proyecto
from proyectos.forms.prorroga_forms import (
    ProrrogaProyectoForm, ProrrogaAprobacionForm, FiltroProrrogasForm
)


class ProrrogaListView(LoginRequiredMixin, ListView):
    """Vista para listar todas las prórrogas"""
    model = ProrrogaProyecto
    template_name = 'proyectos/prorroga/list.html'
    context_object_name = 'prorrogas'
    paginate_by = 20
    ordering = ['-fecha_solicitud']
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('proyecto')
        
        # Aplicar filtros
        proyecto_id = self.request.GET.get('proyecto')
        estado = self.request.GET.get('estado')
        tipo_prorroga = self.request.GET.get('tipo_prorroga')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if proyecto_id:
            queryset = queryset.filter(proyecto_id=proyecto_id)
        
        if estado:
            queryset = queryset.filter(estado=estado)
        
        if tipo_prorroga:
            queryset = queryset.filter(tipo_prorroga=tipo_prorroga)
        
        if fecha_desde:
            queryset = queryset.filter(fecha_solicitud__gte=fecha_desde)
        
        if fecha_hasta:
            queryset = queryset.filter(fecha_solicitud__lte=fecha_hasta)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_filtros'] = FiltroProrrogasForm(self.request.GET)
        
        # Estadísticas
        context['stats'] = {
            'total': ProrrogaProyecto.objects.count(),
            'pendientes': ProrrogaProyecto.objects.filter(estado='solicitada').count(),
            'aprobadas': ProrrogaProyecto.objects.filter(estado='aprobada').count(),
            'rechazadas': ProrrogaProyecto.objects.filter(estado='rechazada').count(),
        }
        
        return context


class ProrrogaCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear nueva prórroga"""
    model = ProrrogaProyecto
    form_class = ProrrogaProyectoForm
    template_name = 'proyectos/prorroga/form.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.proyecto = get_object_or_404(Proyecto, id=kwargs['proyecto_id'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['proyecto'] = self.proyecto
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['proyecto'] = self.proyecto
        context['title'] = f'Solicitar Prórroga - {self.proyecto.nombre_proyecto}'
        
        # Prórrogas anteriores del proyecto
        context['prorrogas_anteriores'] = self.proyecto.prorrogas.order_by('-fecha_solicitud')
        
        return context
    
    def form_valid(self, form):
        messages.success(
            self.request, 
            f'Solicitud de prórroga creada correctamente para el proyecto {self.proyecto.nombre_proyecto}'
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyectos:prorroga_detail', kwargs={'pk': self.object.pk})


class ProrrogaDetailView(LoginRequiredMixin, DetailView):
    """Vista para ver detalles de una prórroga"""
    model = ProrrogaProyecto
    template_name = 'proyectos/prorroga/detail.html'
    context_object_name = 'prorroga'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Formulario de aprobación si la prórroga está pendiente
        if self.object.estado == 'solicitada':
            context['form_aprobacion'] = ProrrogaAprobacionForm()
        
        return context


class ProrrogaAprobacionView(LoginRequiredMixin, UpdateView):
    """Vista para aprobar o rechazar prórrogas"""
    model = ProrrogaProyecto
    form_class = ProrrogaAprobacionForm
    template_name = 'proyectos/prorroga/aprobar.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Verificar que la prórroga esté pendiente
        if self.object.estado != 'solicitada':
            messages.error(request, 'Esta prórroga ya ha sido procesada.')
            return redirect('proyectos:prorroga_detail', pk=self.object.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        decision = form.cleaned_data.get('decision')
        
        if decision == 'aprobada':
            messages.success(
                self.request, 
                f'Prórroga aprobada. El proyecto {self.object.proyecto.nombre_proyecto} '
                f'ahora tiene fecha fin: {self.object.fecha_fin_propuesta.strftime("%d/%m/%Y")}'
            )
        else:
            messages.warning(
                self.request, 
                f'Prórroga rechazada para el proyecto {self.object.proyecto.nombre_proyecto}'
            )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('proyectos:prorroga_detail', kwargs={'pk': self.object.pk})


def prorroga_quick_approve(request, pk):
    """Vista AJAX para aprobación rápida de prórrogas"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        prorroga = get_object_or_404(ProrrogaProyecto, pk=pk)
        
        if prorroga.estado != 'solicitada':
            return JsonResponse({
                'error': 'Esta prórroga ya ha sido procesada'
            }, status=400)
        
        # Aprobar la prórroga
        prorroga.estado = 'aprobada'
        prorroga.aprobada_por = request.user.get_full_name() or request.user.username
        prorroga.fecha_aprobacion = timezone.now()
        prorroga.observaciones_aprobacion = 'Aprobación rápida'
        prorroga.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Prórroga aprobada exitosamente',
            'nueva_fecha_fin': prorroga.fecha_fin_propuesta.strftime('%d/%m/%Y'),
            'estado': prorroga.get_estado_display()
        })
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al procesar la solicitud: {str(e)}'
        }, status=500)


class ProrrogaDashboardView(LoginRequiredMixin, ListView):
    """Dashboard de prórrogas con estadísticas"""
    model = ProrrogaProyecto
    template_name = 'proyectos/prorroga/dashboard.html'
    context_object_name = 'prorrogas_recientes'
    
    def get_queryset(self):
        # Últimas 10 prórrogas
        return ProrrogaProyecto.objects.select_related('proyecto').order_by('-fecha_solicitud')[:10]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        context['stats'] = {
            'total_prorrogas': ProrrogaProyecto.objects.count(),
            'pendientes_aprobacion': ProrrogaProyecto.objects.filter(estado='solicitada').count(),
            'aprobadas_mes': ProrrogaProyecto.objects.filter(
                estado='aprobada',
                fecha_aprobacion__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'dias_promedio_extension': ProrrogaProyecto.objects.filter(
                estado='aprobada'
            ).aggregate(promedio=Sum('dias_extension'))['promedio'] or 0
        }
        
        # Prórrogas por tipo
        context['prorrogas_por_tipo'] = []
        for tipo, nombre in ProrrogaProyecto.TIPO_CHOICES:
            count = ProrrogaProyecto.objects.filter(tipo_prorroga=tipo).count()
            if count > 0:
                context['prorrogas_por_tipo'].append({
                    'tipo': nombre,
                    'count': count
                })
        
        # Proyectos con más prórrogas
        context['proyectos_con_mas_prorrogas'] = Proyecto.objects.annotate(
            num_prorrogas=Count('prorrogas')
        ).filter(num_prorrogas__gt=0).order_by('-num_prorrogas')[:5]
        
        # Prórrogas pendientes urgentes
        context['prorrogas_urgentes'] = ProrrogaProyecto.objects.filter(
            estado='solicitada',
            fecha_solicitud__lte=timezone.now() - timedelta(days=7)
        ).select_related('proyecto')
        
        return context


def proyecto_tiene_prorrogas_pendientes(request, proyecto_id):
    """API para verificar si un proyecto tiene prórrogas pendientes"""
    try:
        proyecto = get_object_or_404(Proyecto, id=proyecto_id)
        tiene_pendientes = proyecto.prorrogas.filter(estado='solicitada').exists()
        
        return JsonResponse({
            'tiene_pendientes': tiene_pendientes,
            'count_pendientes': proyecto.prorrogas.filter(estado='solicitada').count(),
            'count_total': proyecto.prorrogas.count()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)