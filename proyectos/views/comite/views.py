from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Avg
from decimal import Decimal

from proyectos.models import (
    ComiteProyecto, ParticipanteComite, SeguimientoProyectoComite,
    Proyecto, Colaborador
)
from proyectos.forms.comite_forms import (
    ComiteProyectoForm, SeguimientoProyectoComiteForm
)


class ComiteListView(LoginRequiredMixin, ListView):
    """Vista para listar todos los comités de proyectos"""
    model = ComiteProyecto
    template_name = 'proyectos/comite/list.html'
    context_object_name = 'comites'
    paginate_by = 15
    ordering = ['-fecha_comite']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros de búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(coordinador__nombre__icontains=search) |
                Q(lugar__icontains=search)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado', '')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        # Filtro por tipo
        tipo = self.request.GET.get('tipo', '')
        if tipo:
            queryset = queryset.filter(tipo_comite=tipo)
        
        return queryset.select_related('coordinador').prefetch_related(
            'participantes', 'seguimientos'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Comités de Proyectos'
        context['estados'] = ComiteProyecto.ESTADO_CHOICES
        context['tipos'] = ComiteProyecto.TIPO_COMITE_CHOICES
        context['search_query'] = self.request.GET.get('q', '')
        
        # Estadísticas rápidas
        total_comites = ComiteProyecto.objects.count()
        comites_activos = ComiteProyecto.objects.filter(
            estado__in=['programado', 'en_curso']
        ).count()
        
        context['estadisticas'] = {
            'total_comites': total_comites,
            'comites_activos': comites_activos,
            'comites_finalizados': ComiteProyecto.objects.filter(estado='finalizado').count(),
        }
        
        return context


class ComiteCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear un nuevo comité de proyectos"""
    model = ComiteProyecto
    form_class = ComiteProyectoForm
    template_name = 'proyectos/comite/form.html'
    success_url = reverse_lazy('proyectos:comite_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Comité de Proyectos'
        context['form_title'] = 'Crear Comité'
        
        # Datos para auto-completado
        context['colaboradores'] = Colaborador.objects.all().order_by('nombre')
        context['proyectos_activos'] = Proyecto.objects.filter(
            estado__in=['pendiente', 'en_ejecucion']
        ).count()
        
        return context

    def form_valid(self, form):
        """Guardar el comité y auto-desplegar proyectos activos"""
        form.instance.creado_por = self.request.user
        
        with transaction.atomic():
            # Guardar el comité
            response = super().form_valid(form)
            
            # Auto-desplegar proyectos activos
            proyectos_activos = Proyecto.objects.filter(
                estado__in=['pendiente', 'en_ejecucion']
            ).order_by('fecha_fin', 'nombre_proyecto')
            
            orden = 1
            proyectos_agregados = 0
            
            for proyecto in proyectos_activos:
                # Buscar el último comité para obtener el avance anterior
                ultimo_seguimiento = SeguimientoProyectoComite.objects.filter(
                    proyecto=proyecto
                ).order_by('-comite__fecha_comite').first()
                
                avance_anterior = None
                if ultimo_seguimiento:
                    avance_anterior = ultimo_seguimiento.avance_reportado
                
                # Crear seguimiento automático
                SeguimientoProyectoComite.objects.create(
                    comite=self.object,
                    proyecto=proyecto,
                    avance_reportado=proyecto.avance,
                    avance_anterior=avance_anterior,
                    estado_seguimiento=self._determinar_estado_inicial(proyecto),
                    logros_periodo='Pendiente de actualización',
                    responsable_reporte=proyecto.director_proyecto,
                    orden_presentacion=orden,
                    presupuesto_ejecutado=proyecto.gasto_real
                )
                
                orden += 1
                proyectos_agregados += 1
            
            messages.success(
                self.request,
                f'Comité creado exitosamente. Se agregaron automáticamente {proyectos_agregados} proyectos activos.'
            )
            
            return response

    def _determinar_estado_inicial(self, proyecto):
        """Determina el estado inicial del seguimiento basado en el proyecto"""
        if proyecto.esta_atrasado:
            return 'rojo'
        elif proyecto.avance < proyecto.avance_planeado:
            return 'amarillo'
        else:
            return 'verde'


class ComiteDetailView(LoginRequiredMixin, DetailView):
    """Vista detallada de un comité de proyectos"""
    model = ComiteProyecto
    template_name = 'proyectos/comite/detail.html'
    context_object_name = 'comite'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comite = self.get_object()
        
        # Seguimientos de proyectos ordenados
        seguimientos = comite.seguimientos.select_related(
            'proyecto', 'responsable_reporte'
        ).order_by('orden_presentacion')
        
        context['seguimientos'] = seguimientos
        
        # Participantes del comité
        participantes = ParticipanteComite.objects.filter(
            comite=comite
        ).select_related('colaborador').order_by('tipo_participacion', 'colaborador__nombre')
        
        context['participantes'] = participantes
        
        # Estadísticas del comité
        total_proyectos = seguimientos.count()
        proyectos_criticos = seguimientos.filter(estado_seguimiento='rojo').count()
        proyectos_atencion = seguimientos.filter(estado_seguimiento='amarillo').count()
        proyectos_normales = seguimientos.filter(estado_seguimiento='verde').count()
        
        if total_proyectos > 0:
            avance_promedio = seguimientos.aggregate(
                promedio=Avg('avance_reportado')
            )['promedio'] or 0
        else:
            avance_promedio = 0
        
        context['estadisticas_comite'] = {
            'total_proyectos': total_proyectos,
            'proyectos_criticos': proyectos_criticos,
            'proyectos_atencion': proyectos_atencion,
            'proyectos_normales': proyectos_normales,
            'avance_promedio': round(float(avance_promedio), 2),
            'participantes_confirmados': participantes.filter(
                estado_asistencia='confirmado'
            ).count(),
        }
        
        return context


class ComiteUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar un comité de proyectos"""
    model = ComiteProyecto
    form_class = ComiteProyectoForm
    template_name = 'proyectos/comite/form.html'
    success_url = reverse_lazy('proyectos:comite_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Editar Comité'
        context['form_title'] = 'Actualizar Comité'
        context['colaboradores'] = Colaborador.objects.all().order_by('nombre')
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Comité actualizado exitosamente.')
        return super().form_valid(form)


class SeguimientoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar el seguimiento de un proyecto en el comité"""
    model = SeguimientoProyectoComite
    form_class = SeguimientoProyectoComiteForm
    template_name = 'proyectos/comite/seguimiento_form.html'

    def get_success_url(self):
        return reverse_lazy('proyectos:comite_detail', kwargs={'pk': self.object.comite.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seguimiento = self.get_object()
        context['title'] = f'Actualizar Seguimiento - {seguimiento.proyecto.nombre_proyecto}'
        context['comite'] = seguimiento.comite
        context['proyecto'] = seguimiento.proyecto
        context['colaboradores'] = Colaborador.objects.all().order_by('nombre')
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Seguimiento actualizado para {self.object.proyecto.nombre_proyecto}'
        )
        return super().form_valid(form)


def gestionar_participantes_comite(request, comite_id):
    """Vista para gestionar participantes de un comité"""
    comite = get_object_or_404(ComiteProyecto, pk=comite_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        colaborador_id = request.POST.get('colaborador_id')
        
        if accion == 'agregar' and colaborador_id:
            colaborador = get_object_or_404(Colaborador, pk=colaborador_id)
            
            participante, created = ParticipanteComite.objects.get_or_create(
                comite=comite,
                colaborador=colaborador,
                defaults={
                    'tipo_participacion': request.POST.get('tipo_participacion', 'obligatorio'),
                    'rol_en_comite': request.POST.get('rol_en_comite', ''),
                }
            )
            
            if created:
                messages.success(
                    request,
                    f'{colaborador.nombre} agregado al comité exitosamente.'
                )
            else:
                messages.warning(
                    request,
                    f'{colaborador.nombre} ya es participante de este comité.'
                )
        
        elif accion == 'eliminar' and colaborador_id:
            try:
                participante = ParticipanteComite.objects.get(
                    comite=comite,
                    colaborador_id=colaborador_id
                )
                nombre = participante.colaborador.nombre
                participante.delete()
                messages.success(request, f'{nombre} eliminado del comité.')
            except ParticipanteComite.DoesNotExist:
                messages.error(request, 'Participante no encontrado.')
        
        elif accion == 'confirmar' and colaborador_id:
            try:
                participante = ParticipanteComite.objects.get(
                    comite=comite,
                    colaborador_id=colaborador_id
                )
                participante.estado_asistencia = 'confirmado'
                participante.fecha_confirmacion = timezone.now()
                participante.save()
                messages.success(
                    request,
                    f'Asistencia confirmada para {participante.colaborador.nombre}.'
                )
            except ParticipanteComite.DoesNotExist:
                messages.error(request, 'Participante no encontrado.')
    
    return redirect('proyectos:comite_detail', pk=comite_id)


def duplicar_comite(request, comite_id):
    """Vista para duplicar un comité existente"""
    comite_original = get_object_or_404(ComiteProyecto, pk=comite_id)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Crear nuevo comité basado en el original
            nuevo_comite = ComiteProyecto.objects.create(
                nombre=f"Copia de {comite_original.nombre}",
                fecha_comite=timezone.now() + timezone.timedelta(days=7),  # Una semana después
                tipo_comite=comite_original.tipo_comite,
                lugar=comite_original.lugar,
                coordinador=comite_original.coordinador,
                agenda=comite_original.agenda,
                creado_por=request.user,
                estado='programado'
            )
            
            # Copiar participantes
            participantes_copiados = 0
            for participante in comite_original.participantes.all():
                ParticipanteComite.objects.create(
                    comite=nuevo_comite,
                    colaborador=participante,
                    tipo_participacion='obligatorio',  # Reset a obligatorio
                    estado_asistencia='pendiente'
                )
                participantes_copiados += 1
            
            # Copiar seguimientos de proyectos activos
            proyectos_copiados = 0
            orden = 1
            
            for seguimiento in comite_original.seguimientos.all():
                # Solo copiar si el proyecto sigue activo
                if seguimiento.proyecto.estado in ['pendiente', 'en_ejecucion']:
                    SeguimientoProyectoComite.objects.create(
                        comite=nuevo_comite,
                        proyecto=seguimiento.proyecto,
                        avance_reportado=seguimiento.proyecto.avance,  # Avance actual
                        avance_anterior=seguimiento.avance_reportado,  # El anterior es el del comité original
                        estado_seguimiento='verde',  # Reset inicial
                        logros_periodo='Pendiente de actualización',
                        responsable_reporte=seguimiento.responsable_reporte,
                        orden_presentacion=orden,
                        tiempo_asignado=seguimiento.tiempo_asignado,
                        presupuesto_ejecutado=seguimiento.proyecto.gasto_real
                    )
                    orden += 1
                    proyectos_copiados += 1
            
            messages.success(
                request,
                f'Comité duplicado exitosamente. Se copiaron {participantes_copiados} participantes y {proyectos_copiados} proyectos activos.'
            )
            
            return redirect('proyectos:comite_detail', pk=nuevo_comite.pk)
    
    return redirect('proyectos:comite_detail', pk=comite_id)


def ajax_buscar_colaboradores(request):
    """Vista AJAX para buscar colaboradores"""
    query = request.GET.get('q', '')
    colaboradores = []
    
    if query and len(query) >= 2:
        colaboradores_qs = Colaborador.objects.filter(
            Q(nombre__icontains=query) | Q(cargo__icontains=query)
        )[:10]
        
        colaboradores = [
            {
                'id': c.id,
                'nombre': c.nombre,
                'cargo': c.cargo,
                'email': c.email
            }
            for c in colaboradores_qs
        ]
    
    return JsonResponse({'colaboradores': colaboradores})