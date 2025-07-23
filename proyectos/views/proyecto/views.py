# Python imports
import json

# Django imports
from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Count, Sum, Case, When, IntegerField
from users.mixins import ModulePermissionMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, TemplateView, DeleteView
)

# Project imports
from proyectos.models import Proyecto, Actividad, Bitacora, EntregaDocumental


class ProyectoListView(LoginRequiredMixin, ModulePermissionMixin, ListView):
    module_name = 'proyectos'
    permission_action = 'view'
    model = Proyecto
    template_name = 'proyectos/proyecto/list.html'
    context_object_name = 'proyectos'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por búsqueda general
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(nombre_proyecto__icontains=search) |
                Q(cliente__icontains=search) |
                Q(orden_contrato__icontains=search) |
                Q(centro_costos__icontains=search)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado', '')
        if estado:
            queryset = queryset.filter(estado=estado)
            
            
        # Filtro por cliente específico
        cliente = self.request.GET.get('cliente', '')
        if cliente:
            queryset = queryset.filter(cliente__icontains=cliente)
            
        # Filtro por centro de costos
        centro_costos = self.request.GET.get('centro_costos', '')
        if centro_costos:
            queryset = queryset.filter(centro_costos__icontains=centro_costos)
            
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add status and priority choices for filters
        context['estados'] = dict(Proyecto.ESTADO_CHOICES)
        
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
                estado__in=['pendiente', 'en_ejecucion', 'atrasado']
            ).count()
            context['completed_projects'] = Proyecto.objects.filter(
                estado='finalizado'
            ).count()
        else:
            context['total_projects'] = Proyecto.objects.filter(
                creado_por=self.request.user
            ).count()
            context['active_projects'] = Proyecto.objects.filter(
                creado_por=self.request.user,
                estado__in=['pendiente', 'en_ejecucion', 'atrasado']
            ).count()
            context['completed_projects'] = Proyecto.objects.filter(
                creado_por=self.request.user,
                estado='finalizado'
            ).count()
            
        return context


class ProyectoCreateView(LoginRequiredMixin, CreateView):
    model = Proyecto
    template_name = 'proyectos/proyecto/form.html'
    fields = [
        'trato', 'cliente', 'centro_costos', 'nombre_proyecto', 
        'orden_contrato', 'dias_prometidos', 'fecha_inicio', 'fecha_fin',
        'fecha_fin_real', 'avance_planeado', 'avance', 'presupuesto', 
        'gasto_real', 'estado', 'director_proyecto', 
        'ingeniero_residente', 'cotizacion_aprobada', 'observaciones', 'adjunto'
    ]
    success_url = reverse_lazy('proyectos:proyecto_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Importar modelos desde crm y proyectos
        from crm.models import Trato
        from proyectos.models import Colaborador
        
        # Filtrar solo los tratos ganados
        tratos_ganados = Trato.objects.filter(estado='ganado').select_related('cliente')
        form.fields['trato'].queryset = tratos_ganados
        
        # Configurar campos de colaboradores
        colaboradores = Colaborador.objects.all().order_by('nombre')
        form.fields['director_proyecto'].queryset = colaboradores
        form.fields['director_proyecto'].empty_label = "--- Seleccione un director ---"
        form.fields['ingeniero_residente'].queryset = colaboradores
        form.fields['ingeniero_residente'].empty_label = "--- Seleccione un ingeniero ---"
        
        # Configurar campo de cotización aprobada
        from crm.models import VersionCotizacion
        form.fields['cotizacion_aprobada'].queryset = VersionCotizacion.objects.none()
        form.fields['cotizacion_aprobada'].empty_label = "--- Seleccione una cotización ---"
        form.fields['cotizacion_aprobada'].required = False
        
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
        # Para crear proyectos, aplicar validación de fecha futura
        min_date = timezone.now().date().isoformat()
        form.fields['fecha_inicio'].widget = forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'min': min_date
            },
            format='%Y-%m-%d'
        )
        form.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        
        form.fields['fecha_fin'].widget = forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'min': min_date
            },
            format='%Y-%m-%d'
        )
        form.fields['fecha_fin'].input_formats = ['%Y-%m-%d']
        
        # Widget para fecha_fin_real (solo en edición)
        if 'fecha_fin_real' in form.fields:
            form.fields['fecha_fin_real'].widget = forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                },
                format='%Y-%m-%d'
            )
            form.fields['fecha_fin_real'].input_formats = ['%Y-%m-%d']
        
        # Mejorar el widget del campo trato
        form.fields['trato'].widget.attrs.update({'class': 'form-control'})
        form.fields['trato'].empty_label = "--- Seleccione un trato ---"
        
        # Agregar ayuda y labels mejorados
        form.fields['centro_costos'].help_text = 'Centro de costos asignado al proyecto'
        form.fields['dias_prometidos'].help_text = 'Número de días prometidos para completar el proyecto'
        form.fields['presupuesto'].help_text = 'Presupuesto total asignado al proyecto'
        
        # Configurar campos adicionales para creación
        if 'gasto_real' in form.fields:
            form.fields['gasto_real'].help_text = 'Gasto real del proyecto hasta la fecha'
            form.fields['gasto_real'].required = False
            form.fields['gasto_real'].initial = 0
        
        if 'avance' in form.fields:
            form.fields['avance'].help_text = 'Porcentaje de avance real del proyecto (0-100)'
            form.fields['avance'].required = False
            form.fields['avance'].initial = 0
            
        if 'avance_planeado' in form.fields:
            form.fields['avance_planeado'].help_text = 'Porcentaje de avance esperado según cronograma (0-100)'
            form.fields['avance_planeado'].required = False
            form.fields['avance_planeado'].initial = 0
        
        # Configurar campos de equipo del proyecto
        if 'director_proyecto' in form.fields:
            form.fields['director_proyecto'].help_text = 'Colaborador responsable de dirigir el proyecto'
            form.fields['director_proyecto'].required = False
        if 'ingeniero_residente' in form.fields:
            form.fields['ingeniero_residente'].help_text = 'Colaborador responsable de la residencia del proyecto'
            form.fields['ingeniero_residente'].required = False
        
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
        
        # Obtener actividades del proyecto
        actividades = proyecto.actividades.all().order_by('inicio')
        context['actividades'] = actividades
        context['total_actividades'] = actividades.count()
        context['actividades_completadas'] = actividades.filter(estado='finalizado').count()
        
        # Obtener bitácoras recientes
        bitacoras = proyecto.bitacoras.all().order_by('-fecha_registro')[:5]
        context['bitacoras'] = bitacoras
        context['bitacoras_recientes'] = bitacoras
        
        # Obtener entregables del proyecto
        entregables = proyecto.entregables.all()
        context['entregables'] = entregables
        context['documentos_pendientes'] = entregables.filter(
            estado__in=['pendiente', 'en_proceso']
        )
        
        # Obtener prórrogas del proyecto
        prorrogas = proyecto.prorrogas.all().order_by('-fecha_solicitud')
        context['prorrogas'] = prorrogas
        context['total_prorrogas'] = prorrogas.count()
        context['prorrogas_pendientes'] = prorrogas.filter(estado='solicitada').count()
        context['prorrogas_aprobadas'] = prorrogas.filter(estado='aprobada').count()
        context['prorrogas_rechazadas'] = prorrogas.filter(estado='rechazada').count()
        
        # Calcular total de días de extensión aprobados
        dias_extension_total = sum([
            p.dias_extension for p in prorrogas.filter(estado='aprobada')
        ])
        context['dias_extension_total'] = dias_extension_total
        
        # Obtener la última prórroga aprobada para mostrar la fecha fin actual
        ultima_prorroga_aprobada = prorrogas.filter(estado='aprobada').first()
        if ultima_prorroga_aprobada:
            context['fecha_fin_actual'] = ultima_prorroga_aprobada.fecha_fin_propuesta
        else:
            context['fecha_fin_actual'] = proyecto.fecha_fin
        
        return context


class ProyectoUpdateForm(forms.ModelForm):
    class Meta:
        model = Proyecto
        fields = [
            'trato', 'cliente', 'centro_costos', 'nombre_proyecto', 
            'orden_contrato', 'dias_prometidos', 'fecha_inicio', 'fecha_fin',
            'fecha_fin_real', 'avance_planeado', 'avance', 'presupuesto', 
            'gasto_real', 'estado', 'director_proyecto', 
            'ingeniero_residente', 'cotizacion_aprobada', 'observaciones', 'adjunto'
        ]
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
            'fecha_fin_real': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}, format='%Y-%m-%d'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Importar modelos necesarios
        from crm.models import Trato
        from proyectos.models import Colaborador
        
        # Remover validators de fecha_inicio para permitir fechas pasadas en edición
        if 'fecha_inicio' in self.fields:
            self.fields['fecha_inicio'].validators = []
            self.fields['fecha_inicio'].input_formats = ['%Y-%m-%d']
        
        # Configurar formato para otros campos de fecha también
        if 'fecha_fin' in self.fields:
            self.fields['fecha_fin'].input_formats = ['%Y-%m-%d']
        if 'fecha_fin_real' in self.fields:
            self.fields['fecha_fin_real'].input_formats = ['%Y-%m-%d']
        
        # Configurar campo cliente como ChoiceField
        tratos_ganados = Trato.objects.filter(estado='ganado').select_related('cliente')
        clientes_unicos = []
        clientes_vistos = set()
        
        for trato in tratos_ganados:
            cliente_nombre = str(trato.cliente)
            if cliente_nombre not in clientes_vistos:
                clientes_unicos.append((cliente_nombre, cliente_nombre))
                clientes_vistos.add(cliente_nombre)
        
        clientes_unicos.sort(key=lambda x: x[1])
        
        self.fields['cliente'] = forms.ChoiceField(
            choices=[('', '--- Seleccione un cliente ---')] + clientes_unicos,
            required=True,
            label='Cliente',
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        
        # Configurar campos de colaboradores
        colaboradores = Colaborador.objects.all().order_by('nombre')
        self.fields['director_proyecto'].queryset = colaboradores
        self.fields['director_proyecto'].empty_label = "--- Seleccione un director ---"
        self.fields['ingeniero_residente'].queryset = colaboradores
        self.fields['ingeniero_residente'].empty_label = "--- Seleccione un ingeniero ---"
        
        # Configurar campo de cotización aprobada
        from crm.models import VersionCotizacion
        if self.instance and self.instance.trato:
            # Si hay un trato asociado, mostrar sus cotizaciones
            self.fields['cotizacion_aprobada'].queryset = VersionCotizacion.objects.filter(
                cotizacion__trato=self.instance.trato
            ).order_by('-version')
        else:
            self.fields['cotizacion_aprobada'].queryset = VersionCotizacion.objects.none()
        self.fields['cotizacion_aprobada'].empty_label = "--- Seleccione una cotización ---"
        self.fields['cotizacion_aprobada'].required = False
    
    def clean_fecha_inicio(self):
        """Override clean method for fecha_inicio to skip future date validation on edit"""
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        # Para edición, no validar fecha futura - permitir cualquier fecha
        return fecha_inicio
    
    def full_clean(self):
        """Override full_clean to prevent model field validation for fecha_inicio"""
        # Call the parent's full_clean
        super().full_clean()
        
        # If fecha_inicio had an error related to past dates, clear it
        if 'fecha_inicio' in self._errors:
            error_messages = self._errors['fecha_inicio']
            # Check if the error is related to future date validation
            future_date_error = any('pasado' in str(msg) for msg in error_messages)
            if future_date_error:
                # Remove the error - the field should already have the correct value
                del self._errors['fecha_inicio']

class ProyectoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Proyecto
    form_class = ProyectoUpdateForm
    template_name = 'proyectos/proyecto/form.html'
    success_url = reverse_lazy('proyectos:proyecto_list')
    
    def test_func(self):
        proyecto = self.get_object()
        return self.request.user.has_perm('proyectos.change_proyecto') or \
               proyecto.creado_por == self.request.user
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permiso para editar este proyecto.')
        return redirect('proyectos:proyecto_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Importar modelos desde crm
        from crm.models import Trato
        
        # Filtrar solo los tratos ganados para el campo trato
        tratos_ganados = Trato.objects.filter(estado='ganado').select_related('cliente')
        form.fields['trato'].queryset = tratos_ganados
        form.fields['trato'].widget.attrs.update({'class': 'form-control'})
        form.fields['trato'].empty_label = "--- Seleccione un trato ---"
        
        # Agregar ayuda y labels mejorados
        form.fields['centro_costos'].help_text = 'Centro de costos asignado al proyecto'
        form.fields['dias_prometidos'].help_text = 'Número de días prometidos para completar el proyecto'
        form.fields['presupuesto'].help_text = 'Presupuesto total asignado al proyecto'
        form.fields['gasto_real'].help_text = 'Gasto real del proyecto hasta la fecha'
        form.fields['avance'].help_text = 'Porcentaje de avance real del proyecto (0-100)'
        form.fields['avance_planeado'].help_text = 'Porcentaje de avance esperado según cronograma (0-100)'
        form.fields['director_proyecto'].help_text = 'Colaborador responsable de dirigir el proyecto'
        form.fields['ingeniero_residente'].help_text = 'Colaborador responsable de la residencia del proyecto'
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Importar el modelo Trato desde crm
        from crm.models import Trato
        
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
        messages.success(self.request, 'Proyecto actualizado exitosamente.')
        return super().form_valid(form)


class ProyectoDeleteView(LoginRequiredMixin, DeleteView):
    model = Proyecto
    template_name = 'proyectos/proyecto/confirm_delete.html'
    success_url = reverse_lazy('proyectos:proyecto_list')
    context_object_name = 'proyecto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Eliminar Proyecto {self.object.nombre_proyecto}'
        return context


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
        total_proyectos = proyectos.count()
        proyectos_activos = proyectos.filter(
            estado__in=['pendiente', 'en_ejecucion']
        ).count()
        context['total_proyectos'] = total_proyectos
        context['proyectos_activos'] = proyectos_activos
        context['proyectos_completados'] = proyectos.filter(estado='finalizado').count()
        
        # Calcular porcentajes para las barras de progreso
        context['porcentaje_activos'] = round(float(proyectos_activos / total_proyectos * 100), 2) if total_proyectos > 0 else 0
        
        # Nuevas métricas de control
        hoy = timezone.now().date()
        
        # Proyectos con retraso en avance (avance real < avance planeado)
        proyectos_retraso_avance = 0
        # Proyectos con sobreejecución presupuestaria
        proyectos_sobre_presupuesto = 0
        # Proyectos atrasados en fechas
        proyectos_atrasados_fecha = 0
        
        for proyecto in proyectos:
            # Retraso en avance
            if proyecto.avance < proyecto.avance_planeado:
                proyectos_retraso_avance += 1
            
            # Sobreejecución presupuestaria (% ejecución > avance real)
            if proyecto.porcentaje_ejecucion_presupuesto > float(proyecto.avance):
                proyectos_sobre_presupuesto += 1
            
            # Atrasados en fecha
            if proyecto.esta_atrasado:
                proyectos_atrasados_fecha += 1
        
        context['proyectos_retraso_avance'] = proyectos_retraso_avance
        context['proyectos_sobre_presupuesto'] = proyectos_sobre_presupuesto
        context['proyectos_atrasados_fecha'] = proyectos_atrasados_fecha
        
        # Calcular avances promedio
        avance_real_agregado = proyectos.aggregate(Sum('avance'))['avance__sum'] or 0
        avance_planeado_agregado = proyectos.aggregate(Sum('avance_planeado'))['avance_planeado__sum'] or 0
        
        avance_promedio = float(avance_real_agregado / total_proyectos) if total_proyectos > 0 else 0
        avance_planeado_promedio = float(avance_planeado_agregado / total_proyectos) if total_proyectos > 0 else 0
        
        context['avance_promedio'] = round(avance_promedio, 2)
        context['avance_planeado_promedio'] = round(avance_planeado_promedio, 2)
        
        # Calcular desviación del avance (real vs planeado)
        context['desviacion_avance'] = round(avance_promedio - avance_planeado_promedio, 2)
        
        # Bitácoras urgentes (planeadas que requieren registro urgente)
        bitacoras_urgentes = 0
        for bitacora in Bitacora.objects.filter(proyecto__in=proyectos, estado='planeada'):
            if hasattr(bitacora, 'requiere_registro_urgente') and bitacora.requiere_registro_urgente:
                bitacoras_urgentes += 1
        context['bitacoras_urgentes'] = bitacoras_urgentes
        
        # Actividades por estado (corregido para usar estados reales)
        actividades_estados = Actividad.objects.filter(
            proyecto__in=proyectos
        ).values('estado').annotate(total=Count('id'))
        
        context['actividades_por_estado'] = {
            'no_iniciado': 0,
            'en_proceso': 0,
            'finalizado': 0
        }
        
        for estado_data in actividades_estados:
            estado = estado_data['estado']
            total = estado_data['total']
            if estado in ['no_iniciado', 'pendiente']:
                context['actividades_por_estado']['no_iniciado'] += total
            elif estado in ['en_proceso', 'en_revision']:
                context['actividades_por_estado']['en_proceso'] += total
            elif estado == 'finalizado':
                context['actividades_por_estado']['finalizado'] += total
        
        # Últimos proyectos para la tabla (con más datos)
        context['ultimos_proyectos'] = proyectos.select_related(
            'director_proyecto', 'ingeniero_residente'
        ).order_by('-fecha_creacion')[:8]
        
        # Proyectos críticos (múltiples alertas)
        proyectos_criticos = []
        for proyecto in proyectos:
            alertas = 0
            alertas_desc = []
            
            if proyecto.avance < proyecto.avance_planeado:
                alertas += 1
                alertas_desc.append("Retraso en avance")
            
            if proyecto.porcentaje_ejecucion_presupuesto > float(proyecto.avance):
                alertas += 1
                alertas_desc.append("Sobreejecución presupuestaria")
            
            if proyecto.esta_atrasado:
                alertas += 1
                alertas_desc.append("Atraso en fechas")
            
            if alertas >= 2:  # Crítico si tiene 2 o más alertas
                proyectos_criticos.append({
                    'proyecto': proyecto,
                    'alertas_count': alertas,
                    'alertas_desc': alertas_desc
                })
        
        context['proyectos_criticos'] = sorted(
            proyectos_criticos, 
            key=lambda x: x['alertas_count'], 
            reverse=True
        )[:5]
        
        # Presupuesto vs Gasto con más detalle
        if proyectos.exists():
            presupuesto = proyectos.aggregate(Sum('presupuesto'))['presupuesto__sum'] or 0
            gasto = proyectos.aggregate(Sum('gasto_real'))['gasto_real__sum'] or 0
            presupuesto_gasto = proyectos.aggregate(Sum('presupuesto_gasto'))['presupuesto_gasto__sum'] or 0
            gasto_operativo = proyectos.aggregate(Sum('gasto_operativo_real'))['gasto_operativo_real__sum'] or 0
            
            context['presupuesto_total'] = presupuesto
            context['gasto_total'] = gasto
            context['presupuesto_gasto_total'] = presupuesto_gasto
            context['gasto_operativo_total'] = gasto_operativo
            context['porcentaje_gasto'] = round(float(gasto / presupuesto * 100), 2) if presupuesto > 0 else 0
            context['disponible_total'] = presupuesto - gasto
            context['porcentaje_disponible'] = round(float((presupuesto - gasto) / presupuesto * 100), 2) if presupuesto > 0 else 0
        else:
            context['presupuesto_total'] = 0
            context['gasto_total'] = 0
            context['presupuesto_gasto_total'] = 0
            context['gasto_operativo_total'] = 0
            context['porcentaje_gasto'] = 0
            context['disponible_total'] = 0
            context['porcentaje_disponible'] = 0
        
        # Obtener bitácoras recientes con más información
        context['ultimas_bitacoras'] = Bitacora.objects.select_related(
            'proyecto', 'responsable', 'lider_trabajo'
        ).filter(proyecto__in=proyectos).order_by('-fecha_registro')[:6]
        
        # Distribución de proyectos por estado
        context['proyectos_por_estado'] = {
            'pendiente': proyectos.filter(estado='pendiente').count(),
            'en_ejecucion': proyectos.filter(estado='en_ejecucion').count(),
            'finalizado': proyectos.filter(estado='finalizado').count(),
        }
        
        # Próximas fechas límite
        context['proximas_fechas'] = proyectos.filter(
            fecha_fin__gte=hoy,
            fecha_fin__lte=hoy + timezone.timedelta(days=30),
            estado__in=['pendiente', 'en_ejecucion']
        ).order_by('fecha_fin')[:5]
        
        return context


class ProyectoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vista para eliminar un proyecto con confirmación robusta"""
    model = Proyecto
    template_name = 'proyectos/proyecto/confirm_delete.html'
    success_url = reverse_lazy('proyectos:proyecto_list')
    context_object_name = 'proyecto'
    
    def test_func(self):
        """Solo usuarios staff pueden eliminar proyectos"""
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proyecto = self.get_object()
        
        # Obtener información relacionada para mostrar advertencias
        actividades_count = Actividad.objects.filter(proyecto=proyecto).count()
        bitacoras_count = Bitacora.objects.filter(proyecto=proyecto).count()
        entregables_count = EntregaDocumental.objects.filter(proyecto=proyecto).count()
        
        # Calcular datos financieros
        presupuesto_ejecutado = proyecto.gasto_real or 0
        porcentaje_ejecucion = (presupuesto_ejecutado / proyecto.presupuesto * 100) if proyecto.presupuesto > 0 else 0
        
        context.update({
            'title': f'Eliminar Proyecto: {proyecto.nombre_proyecto}',
            'actividades_count': actividades_count,
            'bitacoras_count': bitacoras_count,
            'entregables_count': entregables_count,
            'presupuesto_ejecutado': presupuesto_ejecutado,
            'porcentaje_ejecucion': round(porcentaje_ejecucion, 2),
            'tiene_datos_relacionados': any([actividades_count, bitacoras_count, entregables_count]),
            'avance_proyecto': proyecto.avance or 0,
        })
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """Sobrescribir para agregar mensaje de confirmación"""
        proyecto = self.get_object()
        nombre_proyecto = proyecto.nombre_proyecto
        cliente = proyecto.cliente
        
        # Verificar que el usuario confirmó explícitamente
        confirmacion = request.POST.get('confirmacion')
        if confirmacion != 'ELIMINAR':
            messages.error(
                request, 
                'Debe escribir "ELIMINAR" exactamente para confirmar la eliminación.'
            )
            return redirect('proyectos:proyecto_delete', pk=proyecto.pk)
        
        # Mensaje de éxito antes de eliminar
        messages.success(
            request,
            f'Proyecto "{nombre_proyecto}" del cliente "{cliente}" ha sido eliminado permanentemente.'
        )
        
        return super().delete(request, *args, **kwargs)
    
    def handle_no_permission(self):
        """Mensaje personalizado cuando no tiene permisos"""
        messages.error(
            self.request,
            'No tiene permisos para eliminar proyectos. Solo los administradores pueden realizar esta acción.'
        )
        return redirect('proyectos:proyecto_list')
