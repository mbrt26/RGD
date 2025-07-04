from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
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
        
        # Auto-popular el progreso desde el proyecto si no se ha reportado aún
        if seguimiento.avance_reportado == 0 and seguimiento.proyecto.avance:
            context['avance_sugerido'] = seguimiento.proyecto.avance
            context['avance_desde_proyecto'] = True
        
        return context
    
    def get_initial(self):
        """Auto-popular el avance reportado con el avance del proyecto"""
        initial = super().get_initial()
        seguimiento = self.get_object()
        
        # Si no se ha reportado avance aún, usar el del proyecto
        if seguimiento.avance_reportado == 0 and seguimiento.proyecto.avance:
            initial['avance_reportado'] = seguimiento.proyecto.avance
            
        return initial

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
        
        # Después de procesar POST, redirigir a la misma página
        return redirect('proyectos:gestionar_participantes_comite', comite_id=comite_id)
    
    # GET request - mostrar la interfaz de gestión
    participantes_actuales = comite.participantecomite_set.select_related('colaborador').order_by('colaborador__nombre')
    
    # Colaboradores que NO están en el comité
    participantes_ids = participantes_actuales.values_list('colaborador_id', flat=True)
    colaboradores_disponibles = Colaborador.objects.exclude(
        id__in=participantes_ids
    ).order_by('nombre')
    
    context = {
        'comite': comite,
        'participantes_actuales': participantes_actuales,
        'colaboradores_disponibles': colaboradores_disponibles,
        'title': f'Gestionar Participantes - {comite.nombre}',
    }
    
    return render(request, 'proyectos/comite/gestionar_participantes.html', context)


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


class ComiteActaView(LoginRequiredMixin, DetailView):
    """Vista para mostrar el acta de un comité"""
    model = ComiteProyecto
    template_name = 'proyectos/comite/acta.html'
    context_object_name = 'comite'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comite = self.get_object()
        
        # Obtener seguimientos ordenados
        context['seguimientos'] = comite.seguimientos.select_related('proyecto').order_by('orden_presentacion', 'proyecto__nombre_proyecto')
        
        # Obtener participantes con asistencia confirmada
        context['participantes_asistieron'] = comite.participantecomite_set.filter(
            estado_asistencia='asistio'
        ).select_related('colaborador').order_by('colaborador__nombre')
        
        # Calcular estadísticas
        total_proyectos = context['seguimientos'].count()
        proyectos_verdes = context['seguimientos'].filter(estado_seguimiento='verde').count()
        proyectos_rojos = context['seguimientos'].filter(estado_seguimiento='rojo').count()
        
        context.update({
            'title': f'Acta - {comite.nombre}',
            'total_proyectos': total_proyectos,
            'proyectos_verdes': proyectos_verdes,
            'proyectos_rojos': proyectos_rojos,
        })
        
        return context


class ComiteExportView(LoginRequiredMixin, DetailView):
    """Vista para exportar información de un comité"""
    model = ComiteProyecto
    
    def get(self, request, *args, **kwargs):
        from django.http import HttpResponse
        import csv
        
        comite = self.get_object()
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="comite_{comite.pk}_{comite.fecha_comite.strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        # Headers
        writer.writerow([
            'Proyecto', 'Responsable', 'Estado Avance', 'Porcentaje Avance',
            'Semáforo', 'Decisiones Requeridas', 'Observaciones'
        ])
        
        # Datos de seguimientos
        for seguimiento in comite.seguimientos.select_related('proyecto').order_by('orden_presentacion'):
            writer.writerow([
                seguimiento.proyecto.nombre_proyecto,
                seguimiento.proyecto.responsable.nombre if seguimiento.proyecto.responsable else 'Sin asignar',
                seguimiento.get_estado_seguimiento_display(),
                f"{seguimiento.avance_reportado}%",
                seguimiento.get_estado_seguimiento_display(),
                'Sí' if seguimiento.requiere_decision else 'No',
                seguimiento.observaciones or ''
            ])
        
        return response


class ComiteIniciarView(LoginRequiredMixin, DetailView):
    """Vista para iniciar un comité (cambiar estado a 'en_curso')"""
    model = ComiteProyecto
    
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import logging
        
        logger = logging.getLogger(__name__)
        comite = self.get_object()
        
        logger.info(f"Intentando iniciar comité {comite.pk}: {comite.nombre}, estado actual: {comite.estado}")
        
        # Verificar que el comité esté en estado 'programado'
        if comite.estado != 'programado':
            logger.warning(f"Comité {comite.pk} no está en estado 'programado', estado actual: {comite.estado}")
            return JsonResponse({
                'success': False, 
                'message': f'Solo se pueden iniciar comités programados. Estado actual: {comite.get_estado_display()}'
            })
        
        # Verificar que tenga participantes
        if not comite.participantecomite_set.exists():
            return JsonResponse({
                'success': False, 
                'message': 'No se puede iniciar un comité sin participantes.'
            })
        
        # Verificar que tenga proyectos para revisar
        if not comite.seguimientos.exists():
            return JsonResponse({
                'success': False, 
                'message': 'No se puede iniciar un comité sin proyectos para revisar.'
            })
        
        # Cambiar estado a 'en_curso'
        comite.estado = 'en_curso'
        comite.save()
        
        # Marcar asistencia de participantes confirmados
        comite.participantecomite_set.filter(
            estado_asistencia='confirmado'
        ).update(estado_asistencia='asistio')
        
        return JsonResponse({
            'success': True,
            'message': f'Comité "{comite.nombre}" iniciado exitosamente.'
        })
    
    def get(self, request, *args, **kwargs):
        # Redirigir GET requests al detalle del comité
        return redirect('proyectos:comite_detail', pk=self.kwargs['pk'])


class ComiteFinalizarView(LoginRequiredMixin, DetailView):
    """Vista para finalizar un comité (cambiar estado a 'finalizado')"""
    model = ComiteProyecto
    
    def post(self, request, *args, **kwargs):
        from django.http import JsonResponse
        import logging
        
        logger = logging.getLogger(__name__)
        comite = self.get_object()
        
        logger.info(f"Intentando finalizar comité {comite.pk}: {comite.nombre}, estado actual: {comite.estado}")
        
        # Verificar que el comité esté en estado 'en_curso'
        if comite.estado != 'en_curso':
            logger.warning(f"Comité {comite.pk} no está en estado 'en_curso', estado actual: {comite.estado}")
            return JsonResponse({
                'success': False, 
                'message': f'Solo se pueden finalizar comités en curso. Estado actual: {comite.get_estado_display()}'
            })
        
        # Cambiar estado a 'finalizado'
        comite.estado = 'finalizado'
        comite.save()
        
        logger.info(f"Comité {comite.pk} finalizado exitosamente")
        
        return JsonResponse({
            'success': True,
            'message': f'Comité "{comite.nombre}" finalizado exitosamente.'
        })
    
    def get(self, request, *args, **kwargs):
        # Redirigir GET requests al detalle del comité
        return redirect('proyectos:comite_detail', pk=self.kwargs['pk'])


class ComiteDeleteView(LoginRequiredMixin, DetailView):
    """Vista para eliminar un comité"""
    model = ComiteProyecto
    
    def post(self, request, *args, **kwargs):
        comite = self.get_object()
        
        try:
            nombre = comite.nombre
            comite.delete()
            messages.success(request, f'El comité "{nombre}" ha sido eliminado exitosamente.')
            return redirect('proyectos:comite_list')
        except Exception as e:
            messages.error(request, f'Error al eliminar el comité: {str(e)}')
            return redirect('proyectos:comite_detail', pk=comite.pk)
    
    def get(self, request, *args, **kwargs):
        # Redirigir GET requests al detalle del comité
        return redirect('proyectos:comite_detail', pk=self.kwargs['pk'])