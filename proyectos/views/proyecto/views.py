# Python imports
import json

# Django imports
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Count, Sum, Case, When, IntegerField
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, TemplateView
)

# Project imports
from proyectos.models import Proyecto, Actividad, Bitacora, EntregaDocumental


class ProyectoListView(LoginRequiredMixin, ListView):
    model = Proyecto
    template_name = 'proyectos/proyecto/list.html'
    context_object_name = 'proyectos'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(nombre_proyecto__icontains=search) |
                Q(cliente__icontains=search) |
                Q(orden_contrato__icontains=search)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado', '')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        # Filtro por prioridad
        prioridad = self.request.GET.get('prioridad', '')
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
            
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add status and priority choices for filters
        context['estados'] = dict(Proyecto.ESTADO_CHOICES)
        context['prioridades'] = dict(Proyecto.PRIORIDAD_CHOICES)
        
        # Add pagination context
        page_obj = context.get('page_obj')
        if page_obj:
            context['is_paginated'] = page_obj.has_other_pages()
            
        # Add search query to context
        context['search_query'] = self.request.GET.get('q', '')
        
        # Add counts for dashboard stats
        if self.request.user.has_perm('proyectos.view_all_projects'):
            context['total_projects'] = Proyecto.objects.count()
            context['active_projects'] = Proyecto.objects.filter(
                estado__in=['pendiente', 'en_progreso', 'en_revision']
            ).count()
            context['completed_projects'] = Proyecto.objects.filter(
                estado='completado'
            ).count()
        else:
            context['total_projects'] = Proyecto.objects.filter(
                creado_por=self.request.user
            ).count()
            context['active_projects'] = Proyecto.objects.filter(
                creado_por=self.request.user,
                estado__in=['pendiente', 'en_progreso', 'en_revision']
            ).count()
            context['completed_projects'] = Proyecto.objects.filter(
                creado_por=self.request.user,
                estado='completado'
            ).count()
            
        return context


class ProyectoCreateView(LoginRequiredMixin, CreateView):
    model = Proyecto
    template_name = 'proyectos/proyecto/form.html'
    fields = [
        'trato', 'cliente', 'centro_costos', 'nombre_proyecto', 
        'orden_contrato', 'dias_prometidos', 'fecha_inicio', 'fecha_fin',
        'presupuesto', 'estado', 'prioridad', 'observaciones', 'adjunto'
    ]
    success_url = reverse_lazy('proyectos:proyecto_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Importar el modelo Trato desde crm
        from crm.models import Trato
        
        # Filtrar solo los tratos ganados
        tratos_ganados = Trato.objects.filter(estado='ganado').select_related('cliente')
        form.fields['trato'].queryset = tratos_ganados
        
        # Obtener lista única de clientes de los tratos ganados
        clientes_unicos = []
        clientes_vistos = set()
        
        for trato in tratos_ganados:
            cliente_nombre = str(trato.cliente)
            if cliente_nombre not in clientes_vistos:
                clientes_unicos.append((cliente_nombre, cliente_nombre))
                clientes_vistos.add(cliente_nombre)
        
        # Ordenar alfabéticamente
        clientes_unicos.sort(key=lambda x: x[1])
        
        # Convertir el campo cliente en un select con las opciones de los clientes
        form.fields['cliente'] = forms.ChoiceField(
            choices=[('', '--- Seleccione un cliente ---')] + clientes_unicos,
            required=True,
            label='Cliente',
            widget=forms.Select(attrs={'class': 'form-control'})
        )

        # Agregar widgets de calendario para las fechas
        form.fields['fecha_inicio'].widget = forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'min': timezone.now().date().isoformat()
            }
        )
        form.fields['fecha_fin'].widget = forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'min': timezone.now().date().isoformat()
            }
        )
        
        # Mejorar el widget del campo trato
        form.fields['trato'].widget.attrs.update({'class': 'form-control'})
        form.fields['trato'].empty_label = "--- Seleccione un trato ---"
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Importar el modelo Trato desde crm
        from crm.models import Trato
        
        form = context['form']
        # Agregar datos de tratos para el autocompletado
        tratos_data = []
        tratos_ganados = Trato.objects.filter(estado='ganado').select_related('cliente')
        
        for trato in tratos_ganados:
            try:
                trato_dict = {
                    'id': trato.id,
                    'numero_oferta': str(trato.numero_oferta) if trato.numero_oferta else '',
                    'nombre': str(trato.nombre) if trato.nombre else '',
                    'cliente': str(trato.cliente),
                    'centro_costos': str(trato.centro_costos) if trato.centro_costos else '',
                    'nombre_proyecto': str(trato.nombre_proyecto) if trato.nombre_proyecto else '',
                    'orden_contrato': str(trato.orden_contrato) if trato.orden_contrato else '',
                    'dias_prometidos': str(trato.dias_prometidos) if trato.dias_prometidos else '',
                    'valor': float(trato.valor) if trato.valor else 0
                }
                tratos_data.append(trato_dict)
            except Exception as e:
                print(f'Error al procesar trato {trato.id}: {str(e)}')
                continue
        
        context['tratos_json'] = json.dumps(tratos_data)
        return context
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Proyecto creado exitosamente.')
        return super().form_valid(form)


class ProyectoDetailView(LoginRequiredMixin, DetailView):
    model = Proyecto
    template_name = 'proyectos/proyecto/detail.html'
    context_object_name = 'proyecto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proyecto = self.get_object()
        
        # Obtener estadísticas de actividades
        actividades = proyecto.actividades.all()
        context['total_actividades'] = actividades.count()
        context['actividades_completadas'] = actividades.filter(estado='completada').count()
        
        # Obtener bitácoras recientes
        context['bitacoras_recientes'] = proyecto.bitacoras.all()[:5]
        
        # Obtener documentos pendientes de entrega
        context['documentos_pendientes'] = proyecto.entregables.filter(
            estado__in=['pendiente', 'en_proceso']
        )
        
        return context


class ProyectoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Proyecto
    template_name = 'proyectos/proyecto/form.html'
    fields = [
        'trato', 'cliente', 'centro_costos', 'nombre_proyecto', 
        'orden_contrato', 'dias_prometidos', 'fecha_inicio', 'fecha_fin',
        'fecha_fin_real', 'presupuesto', 'gasto_real', 'avance', 
        'estado', 'prioridad', 'observaciones', 'adjunto'
    ]
    success_url = reverse_lazy('proyectos:proyecto_list')
    
    def test_func(self):
        proyecto = self.get_object()
        return self.request.user.has_perm('proyectos.change_proyecto') or \
               proyecto.creado_por == self.request.user
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permiso para editar este proyecto.')
        return redirect('proyectos:proyecto_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Proyecto actualizado exitosamente.')
        return super().form_valid(form)


class ProyectoDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'proyectos/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Obtener proyectos basados en permisos
        if user.has_perm('proyectos.view_all_projects'):
            proyectos = Proyecto.objects.all()
        else:
            proyectos = Proyecto.objects.filter(creado_por=user)
        
        # Estadísticas generales
        context['total_proyectos'] = proyectos.count()
        context['proyectos_activos'] = proyectos.filter(
            estado__in=['pendiente', 'en_progreso', 'en_revision']
        ).count()
        context['proyectos_completados'] = proyectos.filter(estado='completado').count()
        
        # Calcular avance promedio
        avance_agregado = proyectos.aggregate(Sum('avance'))['avance__sum']
        context['avance_promedio'] = (
            avance_agregado / context['total_proyectos'] if context['total_proyectos'] > 0 else 0
        )
        
        # Contar actividades pendientes
        context['actividades_pendientes'] = Actividad.objects.filter(
            proyecto__in=proyectos,
            estado='pendiente'
        ).count()
        
        # Últimos proyectos para la tabla
        context['ultimos_proyectos'] = proyectos.order_by('-fecha_creacion')[:5]
        
        # Datos para el gráfico de distribución de actividades por estado
        context['actividades_por_estado'] = {
            'no_iniciado': 0,
            'en_proceso': 0,
            'finalizado': 0
        }
        
        actividades_estados = Actividad.objects.filter(
            proyecto__in=proyectos
        ).values('estado').annotate(total=Count('id'))
        
        for estado_data in actividades_estados:
            if estado_data['estado'] in ['pendiente', 'no_iniciado']:
                context['actividades_por_estado']['no_iniciado'] += estado_data['total']
            elif estado_data['estado'] in ['en_progreso', 'en_revision']:
                context['actividades_por_estado']['en_proceso'] += estado_data['total']
            elif estado_data['estado'] == 'completado':
                context['actividades_por_estado']['finalizado'] += estado_data['total']
        
        # Proyectos en riesgo (con menos de 10 días para terminar y avance < 90%)
        hoy = timezone.now().date()
        context['proyectos_riesgo'] = proyectos.filter(
            fecha_fin__lte=hoy + timezone.timedelta(days=10),
            avance__lt=90,
            estado__in=['pendiente', 'en_progreso', 'en_revision']
        ).order_by('fecha_fin')[:5]
        
        # Presupuesto vs Gasto
        if proyectos.exists():
            presupuesto = proyectos.aggregate(Sum('presupuesto'))['presupuesto__sum'] or 0
            gasto = proyectos.aggregate(Sum('gasto_real'))['gasto_real__sum'] or 0
            context['presupuesto_total'] = presupuesto
            context['gasto_total'] = gasto
            context['porcentaje_gasto'] = (gasto / presupuesto * 100) if presupuesto > 0 else 0
        else:
            context['presupuesto_total'] = 0
            context['gasto_total'] = 0
            context['porcentaje_gasto'] = 0
        
        # Obtener las últimas entradas de bitácora
        context['ultimas_bitacoras'] = Bitacora.objects.select_related(
            'proyecto', 'responsable'
        ).order_by('-fecha_registro')[:5]
        
        # Añadir diccionarios de opciones para los filtros
        context['estados'] = dict(Proyecto.ESTADO_CHOICES)
        context['prioridades'] = dict(Proyecto.PRIORIDAD_CHOICES)
        
        return context
