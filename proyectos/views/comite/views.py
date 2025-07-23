from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_http_methods
from decimal import Decimal

from proyectos.models import (
    ComiteProyecto, ParticipanteComite, SeguimientoProyectoComite, SeguimientoServicioComite, ElementoExternoComite,
    Proyecto, Colaborador
)
from servicios.models import SolicitudServicio
from proyectos.forms.comite_forms import (
    ComiteProyectoForm, SeguimientoProyectoComiteForm, SeguimientoServicioComiteForm, ElementoExternoComiteForm
)
from proyectos.forms.task_forms import TareasComiteFormSet
from tasks.models import Task


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
        
        # Seguimientos de servicios ordenados
        seguimientos_servicios = comite.seguimientos_servicios.select_related(
            'servicio', 'responsable_reporte'
        ).order_by('orden_presentacion')
        
        # Elementos externos ordenados
        elementos_externos = comite.elementos_externos.select_related(
            'responsable_reporte'
        ).order_by('orden_presentacion')
        
        # Servicios activos que no tienen seguimiento en este comité
        servicios_con_seguimiento = seguimientos_servicios.values_list('servicio_id', flat=True)
        servicios_activos = SolicitudServicio.objects.filter(
            estado__in=['pendiente', 'en_ejecucion', 'atrasado']
        ).exclude(
            id__in=servicios_con_seguimiento
        ).select_related(
            'cliente_crm', 'director_proyecto', 'ingeniero_residente', 'tecnico_asignado'
        ).order_by('fecha_contractual', 'numero_orden')
        
        context['seguimientos'] = seguimientos
        context['seguimientos_servicios'] = seguimientos_servicios
        context['elementos_externos'] = elementos_externos
        context['servicios_activos'] = servicios_activos
        
        # Participantes del comité
        participantes = ParticipanteComite.objects.filter(
            comite=comite
        ).select_related('colaborador').order_by('tipo_participacion', 'colaborador__nombre')
        
        context['participantes'] = participantes
        
        # Estadísticas del comité (proyectos + servicios + elementos externos)
        total_proyectos = seguimientos.count()
        total_servicios = seguimientos_servicios.count()
        total_externos = elementos_externos.count()
        total_items = total_proyectos + total_servicios + total_externos
        
        proyectos_criticos = seguimientos.filter(estado_seguimiento='rojo').count()
        servicios_criticos = seguimientos_servicios.filter(estado_seguimiento='rojo').count()
        externos_criticos = elementos_externos.filter(estado_seguimiento='rojo').count()
        total_criticos = proyectos_criticos + servicios_criticos + externos_criticos
        
        proyectos_atencion = seguimientos.filter(estado_seguimiento='amarillo').count()
        servicios_atencion = seguimientos_servicios.filter(estado_seguimiento='amarillo').count()
        externos_atencion = elementos_externos.filter(estado_seguimiento='amarillo').count()
        total_atencion = proyectos_atencion + servicios_atencion + externos_atencion
        
        proyectos_normales = seguimientos.filter(estado_seguimiento='verde').count()
        servicios_normales = seguimientos_servicios.filter(estado_seguimiento='verde').count()
        externos_normales = elementos_externos.filter(estado_seguimiento='verde').count()
        total_normales = proyectos_normales + servicios_normales + externos_normales
        
        if total_items > 0:
            # Calcular avance promedio combinado
            avance_proyectos = seguimientos.aggregate(promedio=Avg('avance_reportado'))['promedio'] or 0
            avance_servicios = seguimientos_servicios.aggregate(promedio=Avg('avance_reportado'))['promedio'] or 0
            avance_externos = elementos_externos.aggregate(promedio=Avg('avance_reportado'))['promedio'] or 0
            
            # Calcular promedio ponderado
            total_avance = (avance_proyectos * total_proyectos + 
                           avance_servicios * total_servicios + 
                           avance_externos * total_externos)
            avance_promedio = total_avance / total_items if total_items > 0 else 0
        else:
            avance_promedio = 0
        
        context['estadisticas_comite'] = {
            'total_proyectos': total_items,  # Total combinado
            'proyectos_criticos': total_criticos,
            'proyectos_atencion': total_atencion,
            'proyectos_normales': total_normales,
            'avance_promedio': round(float(avance_promedio), 2),
            'participantes_confirmados': participantes.filter(
                estado_asistencia='confirmado'
            ).count(),
            # Estadísticas separadas para información adicional
            'total_proyectos_solo': total_proyectos,
            'total_servicios': total_servicios,
            'total_externos': total_externos,
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
        
        # Agregar formulario de tareas
        context['tareas_formset'] = TareasComiteFormSet(prefix='tareas')
        
        # Agregar tareas existentes
        context['tareas_existentes'] = seguimiento.tareas_generadas.all().select_related(
            'assigned_to', 'created_by'
        ).order_by('-created_at')
        
        # Usuarios disponibles para asignar tareas
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['usuarios_disponibles'] = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
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
        response = super().form_valid(form)
        
        # Procesar las tareas si se enviaron
        tareas_formset = TareasComiteFormSet(self.request.POST, prefix='tareas')
        
        if tareas_formset.is_valid() and tareas_formset.cleaned_data.get('tareas_json'):
            try:
                tareas_creadas = tareas_formset.save(
                    seguimiento=self.object,
                    usuario_creador=self.request.user
                )
                
                if tareas_creadas:
                    messages.success(
                        self.request,
                        f'Se crearon {len(tareas_creadas)} tareas para el proyecto {self.object.proyecto.nombre_proyecto}'
                    )
            except Exception as e:
                messages.error(
                    self.request,
                    f'Error al crear las tareas: {str(e)}'
                )
        
        messages.success(
            self.request,
            f'Seguimiento actualizado para {self.object.proyecto.nombre_proyecto}'
        )
        
        return response


class SeguimientoServicioUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para actualizar el seguimiento de un servicio en el comité"""
    model = SeguimientoServicioComite
    form_class = SeguimientoServicioComiteForm
    template_name = 'proyectos/comite/seguimiento_servicio_form.html'

    def get_success_url(self):
        return reverse_lazy('proyectos:comite_detail', kwargs={'pk': self.object.comite.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seguimiento = self.get_object()
        context['title'] = f'Actualizar Seguimiento Servicio - {seguimiento.servicio.numero_orden}'
        context['comite'] = seguimiento.comite
        context['servicio'] = seguimiento.servicio
        context['colaboradores'] = Colaborador.objects.all().order_by('nombre')
        
        # Agregar formulario de tareas
        context['tareas_formset'] = TareasComiteFormSet(prefix='tareas')
        
        # Agregar tareas existentes
        context['tareas_existentes'] = seguimiento.tareas.all().select_related(
            'assigned_to', 'created_by'
        ).order_by('-created_at')
        
        # Usuarios disponibles para asignar tareas
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['usuarios_disponibles'] = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        return context

    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user
        
        # Procesar tareas a eliminar
        tareas_a_eliminar_json = self.request.POST.get('tareas_a_eliminar', '[]')
        if tareas_a_eliminar_json:
            try:
                import json
                tareas_ids = json.loads(tareas_a_eliminar_json)
                if tareas_ids:
                    # Eliminar las tareas marcadas
                    Task.objects.filter(
                        id__in=tareas_ids
                    ).filter(
                        id__in=form.instance.tareas.values_list('id', flat=True)
                    ).delete()
                    messages.info(self.request, f'{len(tareas_ids)} tarea(s) eliminada(s).')
            except json.JSONDecodeError:
                pass
        
        # Procesar las tareas ANTES de guardar el formulario principal
        tareas_formset = TareasComiteFormSet(self.request.POST, prefix='tareas')
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"POST data: {self.request.POST}")
        logger.info(f"Tareas formset valid: {tareas_formset.is_valid()}")
        if not tareas_formset.is_valid():
            logger.error(f"Tareas formset errors: {tareas_formset.errors}")
        
        if tareas_formset.is_valid():
            tareas_json = tareas_formset.cleaned_data.get('tareas_json', [])
            logger.info(f"Tareas JSON data: {tareas_json}")
            if tareas_json:
                logger.info(f"Procesando {len(tareas_json)} tareas para servicio {self.object.servicio.numero_orden}")
                try:
                    # Modificar el save para servicios
                    tareas_creadas = []
                    
                    # Obtener o crear categoría para servicios
                    from tasks.models import TaskCategory
                    categoria, _ = TaskCategory.objects.get_or_create(
                        name='Comité - Servicios',
                        module='servicios',
                        defaults={
                            'description': 'Tareas generadas desde seguimiento de servicio en comité',
                            'color': '#28a745'
                        }
                    )
                    
                    for tarea_data in tareas_json:
                        # Crear la tarea
                        tarea = Task.objects.create(
                            title=tarea_data['titulo'],
                            description=tarea_data.get('descripcion', ''),
                            assigned_to_id=tarea_data['responsable'],
                            created_by=self.request.user,
                            due_date=tarea_data['fecha_vencimiento'],
                            priority=tarea_data.get('prioridad', 'medium'),
                            category=categoria,
                            solicitud_servicio=self.object.servicio,
                            centro_costos=self.object.servicio.centro_costo,
                            task_type='task',
                            status='pending'
                        )
                        
                        tareas_creadas.append(tarea)
                        
                    # NO guardamos aquí, lo haremos después con super().form_valid()
                    logger.info(f"Tareas creadas en memoria: {len(tareas_creadas)}")
                    
                    # Guardamos las tareas creadas para asociarlas después
                    self._tareas_creadas = tareas_creadas
                    
                    if tareas_creadas:
                        messages.success(
                            self.request,
                            f'Se crearon {len(tareas_creadas)} tareas para el servicio {self.object.servicio.numero_orden}'
                        )
                except Exception as e:
                    logger.error(f"Error al crear las tareas: {str(e)}", exc_info=True)
                    messages.error(
                        self.request,
                        f'Error al crear las tareas: {str(e)}'
                    )
        
        # Ahora sí guardamos el formulario principal
        response = super().form_valid(form)
        
        # Después de guardar, asociamos las tareas si las hay
        if hasattr(self, '_tareas_creadas') and self._tareas_creadas:
            self.object.tareas.add(*self._tareas_creadas)
            logger.info(f"Tareas asociadas al seguimiento {self.object.id}: {len(self._tareas_creadas)} tareas")
        
        messages.success(
            self.request,
            f'Seguimiento actualizado para servicio {self.object.servicio.numero_orden}'
        )
        return response


@require_http_methods(["POST"])
def agregar_servicio_seguimiento(request, comite_id):
    """Vista AJAX para agregar un servicio al seguimiento del comité"""
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        comite = get_object_or_404(ComiteProyecto, pk=comite_id)
        data = json.loads(request.body)
        servicio_id = data.get('servicio_id')
        
        logger.info(f"Intentando agregar servicio {servicio_id} al comité {comite_id}")
        
        if not servicio_id:
            return JsonResponse({'success': False, 'message': 'ID de servicio requerido'})
        
        servicio = get_object_or_404(SolicitudServicio, pk=servicio_id)
        
        # Verificar si ya existe seguimiento para este servicio
        if SeguimientoServicioComite.objects.filter(comite=comite, servicio=servicio).exists():
            return JsonResponse({'success': False, 'message': 'El servicio ya tiene seguimiento en este comité'})
        
        # Obtener el siguiente número de orden
        from django.db.models import Max
        ultimo_orden = SeguimientoServicioComite.objects.filter(comite=comite).aggregate(
            max_orden=Max('orden_presentacion')
        )['max_orden'] or 0
        
        # Crear el seguimiento
        seguimiento = SeguimientoServicioComite.objects.create(
            comite=comite,
            servicio=servicio,
            estado_seguimiento='verde',
            avance_reportado=0,
            logros_periodo='Servicio agregado al seguimiento del comité.',
            orden_presentacion=ultimo_orden + 1,
            actualizado_por=request.user
        )
        
        logger.info(f"Seguimiento creado exitosamente: {seguimiento.id}")
        
        return JsonResponse({
            'success': True, 
            'message': f'Servicio {servicio.numero_orden} agregado al seguimiento'
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Datos JSON inválidos'})
    except Exception as e:
        logger.error(f"Error al agregar servicio al seguimiento: {str(e)}", exc_info=True)
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


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
        
        # Obtener seguimientos de proyectos ordenados
        context['seguimientos'] = comite.seguimientos.select_related('proyecto', 'proyecto__director_proyecto').order_by('orden_presentacion', 'proyecto__nombre_proyecto')
        
        # Obtener seguimientos de servicios ordenados
        context['seguimientos_servicios'] = comite.seguimientos_servicios.select_related('servicio').order_by('orden_presentacion', 'servicio__numero_orden')
        
        # Obtener elementos externos ordenados
        context['elementos_externos'] = comite.elementos_externos.select_related('responsable_reporte').order_by('orden_presentacion')
        
        # Obtener participantes con asistencia confirmada
        context['participantes_asistieron'] = comite.participantecomite_set.filter(
            estado_asistencia='asistio'
        ).select_related('colaborador').order_by('colaborador__nombre')
        
        # Calcular estadísticas combinadas (proyectos + servicios + elementos externos)
        total_proyectos = context['seguimientos'].count()
        total_servicios = context['seguimientos_servicios'].count()
        total_externos = context['elementos_externos'].count()
        total_items = total_proyectos + total_servicios + total_externos
        
        proyectos_verdes = context['seguimientos'].filter(estado_seguimiento='verde').count()
        servicios_verdes = context['seguimientos_servicios'].filter(estado_seguimiento='verde').count()
        externos_verdes = context['elementos_externos'].filter(estado_seguimiento='verde').count()
        total_verdes = proyectos_verdes + servicios_verdes + externos_verdes
        
        proyectos_rojos = context['seguimientos'].filter(estado_seguimiento='rojo').count()
        servicios_rojos = context['seguimientos_servicios'].filter(estado_seguimiento='rojo').count()
        externos_rojos = context['elementos_externos'].filter(estado_seguimiento='rojo').count()
        total_rojos = proyectos_rojos + servicios_rojos + externos_rojos
        
        proyectos_amarillos = context['seguimientos'].filter(estado_seguimiento='amarillo').count()
        servicios_amarillos = context['seguimientos_servicios'].filter(estado_seguimiento='amarillo').count()
        externos_amarillos = context['elementos_externos'].filter(estado_seguimiento='amarillo').count()
        total_amarillos = proyectos_amarillos + servicios_amarillos + externos_amarillos
        
        # Obtener todas las tareas relacionadas
        from tasks.models import Task
        tareas_proyectos = []
        tareas_servicios = []
        tareas_elementos = []
        
        # Tareas de seguimientos de proyectos
        for seguimiento in context['seguimientos']:
            tareas = seguimiento.tareas_generadas.all().select_related(
                'assigned_to', 'created_by'
            ).order_by('-created_at')
            if tareas.exists():
                tareas_proyectos.append({
                    'proyecto': seguimiento.proyecto.nombre_proyecto,
                    'cliente': seguimiento.proyecto.cliente,
                    'centro_costos': seguimiento.proyecto.centro_costos,
                    'descripcion': seguimiento.proyecto.observaciones or '',
                    'tipo': 'proyecto',
                    'tareas': tareas
                })
        
        # Tareas de seguimientos de servicios
        for seguimiento_servicio in context['seguimientos_servicios']:
            tareas = seguimiento_servicio.tareas.all().select_related(
                'assigned_to', 'created_by'
            ).order_by('-created_at')
            if tareas.exists():
                servicio = seguimiento_servicio.servicio
                descripcion_servicio = ''
                if servicio.trato_origen and servicio.trato_origen.descripcion:
                    descripcion_servicio = servicio.trato_origen.descripcion
                
                tareas_servicios.append({
                    'proyecto': f"Servicio {servicio.numero_orden}",
                    'cliente': servicio.cliente_crm.nombre if servicio.cliente_crm else 'Sin cliente',
                    'centro_costos': servicio.centro_costo or 'Sin CC',
                    'descripcion': descripcion_servicio,
                    'tipo': 'servicio',
                    'tareas': tareas
                })
        
        # Tareas de elementos externos
        for elemento in context['elementos_externos']:
            tareas = elemento.tareas_generadas.all().select_related(
                'assigned_to', 'created_by'
            ).order_by('-created_at')
            if tareas.exists():
                tareas_elementos.append({
                    'proyecto': elemento.nombre_proyecto,
                    'cliente': elemento.cliente,
                    'centro_costos': elemento.centro_costos or 'Sin CC',
                    'descripcion': elemento.descripcion,
                    'tipo': 'elemento_externo',
                    'tareas': tareas
                })
        
        context.update({
            'title': f'Acta - {comite.nombre}',
            'total_proyectos': total_proyectos,
            'total_servicios': total_servicios,
            'total_externos': total_externos,
            'total_items': total_items,
            'proyectos_verdes': total_verdes,
            'proyectos_rojos': total_rojos,
            'proyectos_amarillos': total_amarillos,
            'tareas_proyectos': tareas_proyectos,
            'tareas_servicios': tareas_servicios,
            'tareas_elementos': tareas_elementos,
            'tiene_tareas': bool(tareas_proyectos or tareas_servicios or tareas_elementos),
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
            'Tipo', 'Proyecto/Servicio', 'Cliente/Información', 'Responsable', 'Estado Avance', 
            'Porcentaje Avance', 'Semáforo', 'Decisiones Requeridas', 'Observaciones'
        ])
        
        # Datos de seguimientos de proyectos
        for seguimiento in comite.seguimientos.select_related('proyecto').order_by('orden_presentacion'):
            writer.writerow([
                'Proyecto',
                seguimiento.proyecto.nombre_proyecto,
                seguimiento.proyecto.cliente or '',
                seguimiento.responsable_reporte.nombre if seguimiento.responsable_reporte else 'Sin asignar',
                seguimiento.get_estado_seguimiento_display(),
                f"{seguimiento.avance_reportado}%",
                seguimiento.get_estado_seguimiento_display(),
                'Sí' if seguimiento.requiere_decision else 'No',
                seguimiento.logros_periodo or ''
            ])
        
        # Datos de seguimientos de servicios
        for seguimiento in comite.seguimientos_servicios.select_related('servicio').order_by('orden_presentacion'):
            writer.writerow([
                'Servicio',
                seguimiento.servicio.numero_orden,
                seguimiento.servicio.cliente_crm.nombre if seguimiento.servicio.cliente_crm else '',
                seguimiento.responsable_reporte.nombre if seguimiento.responsable_reporte else 'Sin asignar',
                seguimiento.get_estado_seguimiento_display(),
                f"{seguimiento.avance_reportado}%",
                seguimiento.get_estado_seguimiento_display(),
                'Sí' if seguimiento.requiere_decision else 'No',
                seguimiento.logros_periodo or ''
            ])
        
        # Datos de elementos externos
        for elemento in comite.elementos_externos.select_related('responsable_reporte').order_by('orden_presentacion'):
            writer.writerow([
                'Externo',
                elemento.nombre_proyecto,
                elemento.centro_costos,
                elemento.responsable_reporte.nombre if elemento.responsable_reporte else 'Sin asignar',
                elemento.get_estado_seguimiento_display(),
                f"{elemento.avance_reportado}%",
                elemento.get_estado_seguimiento_display(),
                'Sí' if elemento.requiere_decision else 'No',
                elemento.observaciones or ''
            ])
        
        return response


class ElementoExternoCreateView(LoginRequiredMixin, CreateView):
    """Vista para crear elementos externos (proyectos/servicios que no están en el sistema)"""
    model = ElementoExternoComite
    form_class = ElementoExternoComiteForm
    template_name = 'proyectos/comite/elemento_externo_form.html'
    
    def get_success_url(self):
        return reverse_lazy('proyectos:comite_detail', kwargs={'pk': self.kwargs['comite_id']})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comite = get_object_or_404(ComiteProyecto, pk=self.kwargs['comite_id'])
        context['comite'] = comite
        context['title'] = f'Agregar Elemento Externo - {comite.nombre}'
        context['form_title'] = 'Agregar Proyecto/Servicio Externo'
        context['colaboradores'] = Colaborador.objects.all().order_by('nombre')
        
        # Agregar formulario de tareas
        context['tareas_formset'] = TareasComiteFormSet(prefix='tareas')
        
        # Usuarios disponibles para asignar tareas
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['usuarios_disponibles'] = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        comite = get_object_or_404(ComiteProyecto, pk=self.kwargs['comite_id'])
        kwargs['comite'] = comite
        return kwargs
    
    def form_valid(self, form):
        comite = get_object_or_404(ComiteProyecto, pk=self.kwargs['comite_id'])
        form.instance.comite = comite
        form.instance.creado_por = self.request.user
        form.instance.actualizado_por = self.request.user
        
        # Asignar orden de presentación automáticamente
        from django.db.models import Max
        ultimo_orden = ElementoExternoComite.objects.filter(
            comite=comite
        ).aggregate(max_orden=Max('orden_presentacion'))['max_orden'] or 0
        form.instance.orden_presentacion = ultimo_orden + 1
        
        response = super().form_valid(form)
        
        # Procesar las tareas si se enviaron
        tareas_formset = TareasComiteFormSet(self.request.POST, prefix='tareas')
        
        if tareas_formset.is_valid() and tareas_formset.cleaned_data.get('tareas_json'):
            try:
                # Crear objeto mock para compatibilidad con el método save
                class ElementoExternoMock:
                    def __init__(self, elemento):
                        self.proyecto = None
                        self.centro_costos = elemento.centro_costos
                        self.tareas_generadas = elemento.tareas_generadas
                
                mock_seguimiento = ElementoExternoMock(self.object)
                
                tareas_creadas = tareas_formset.save(
                    seguimiento=mock_seguimiento,
                    usuario_creador=self.request.user
                )
                
                if tareas_creadas:
                    messages.success(
                        self.request,
                        f'Se crearon {len(tareas_creadas)} tareas para el elemento externo {self.object.nombre_proyecto}'
                    )
            except Exception as e:
                messages.error(
                    self.request,
                    f'Error al crear tareas: {str(e)}'
                )
        
        messages.success(
            self.request,
            f'Elemento externo "{form.instance.nombre_proyecto}" agregado exitosamente al comité.'
        )
        return response


class ElementoExternoUpdateView(LoginRequiredMixin, UpdateView):
    """Vista para editar elementos externos del comité"""
    model = ElementoExternoComite
    form_class = ElementoExternoComiteForm
    template_name = 'proyectos/comite/elemento_externo_form.html'
    
    def get_success_url(self):
        return reverse_lazy('proyectos:comite_detail', kwargs={'pk': self.object.comite.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        elemento = self.get_object()
        context['comite'] = elemento.comite
        context['title'] = f'Editar Elemento Externo - {elemento.nombre_proyecto}'
        context['form_title'] = 'Editar Proyecto/Servicio Externo'
        context['colaboradores'] = Colaborador.objects.all().order_by('nombre')
        
        # Agregar formulario de tareas
        context['tareas_formset'] = TareasComiteFormSet(prefix='tareas')
        
        # Agregar tareas existentes
        context['tareas_existentes'] = elemento.tareas_generadas.all().select_related(
            'assigned_to', 'created_by'
        ).order_by('-created_at')
        
        # Usuarios disponibles para asignar tareas
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['usuarios_disponibles'] = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['comite'] = self.object.comite
        return kwargs
    
    def form_valid(self, form):
        form.instance.actualizado_por = self.request.user
        
        # Procesar tareas a eliminar
        tareas_a_eliminar_json = self.request.POST.get('tareas_a_eliminar', '[]')
        if tareas_a_eliminar_json:
            try:
                import json
                tareas_ids = json.loads(tareas_a_eliminar_json)
                if tareas_ids:
                    # Eliminar las tareas marcadas
                    Task.objects.filter(
                        id__in=tareas_ids
                    ).filter(
                        id__in=form.instance.tareas_generadas.values_list('id', flat=True)
                    ).delete()
                    messages.info(self.request, f'{len(tareas_ids)} tarea(s) eliminada(s).')
            except json.JSONDecodeError:
                pass
        
        # Procesar nuevas tareas
        tareas_formset = TareasComiteFormSet(self.request.POST, prefix='tareas')
        if tareas_formset.is_valid() and tareas_formset.cleaned_data.get('tareas_json'):
            try:
                # Crear objeto mock para compatibilidad con el método save
                class ElementoExternoMock:
                    def __init__(self, elemento):
                        self.proyecto = None
                        self.centro_costos = elemento.centro_costos
                        self.tareas_generadas = elemento.tareas_generadas
                
                mock_seguimiento = ElementoExternoMock(form.instance)
                
                tareas_creadas = tareas_formset.save(
                    seguimiento=mock_seguimiento,
                    usuario_creador=self.request.user
                )
                
                if tareas_creadas:
                    messages.info(self.request, f'{len(tareas_creadas)} nueva(s) tarea(s) creada(s).')
            except Exception as e:
                messages.error(self.request, f'Error al crear tareas: {str(e)}')
        
        messages.success(
            self.request,
            f'Elemento externo "{form.instance.nombre_proyecto}" actualizado exitosamente.'
        )
        return super().form_valid(form)


class ElementoExternoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar elementos externos"""
    model = ElementoExternoComite
    template_name = 'proyectos/comite/elemento_externo_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('proyectos:comite_detail', kwargs={'pk': self.object.comite.pk})
    
    def delete(self, request, *args, **kwargs):
        elemento = self.get_object()
        comite = elemento.comite
        messages.success(request, f'Elemento externo "{elemento.nombre_proyecto}" eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


class SeguimientoDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar seguimiento de proyecto del comité"""
    model = SeguimientoProyectoComite
    template_name = 'proyectos/comite/seguimiento_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('proyectos:comite_detail', kwargs={'pk': self.object.comite.pk})
    
    def delete(self, request, *args, **kwargs):
        seguimiento = self.get_object()
        proyecto_nombre = seguimiento.proyecto.nombre_proyecto
        comite = seguimiento.comite
        messages.success(request, f'Seguimiento del proyecto "{proyecto_nombre}" eliminado del comité.')
        return super().delete(request, *args, **kwargs)


class SeguimientoServicioDeleteView(LoginRequiredMixin, DeleteView):
    """Vista para eliminar seguimiento de servicio del comité"""
    model = SeguimientoServicioComite
    template_name = 'proyectos/comite/seguimiento_servicio_confirm_delete.html'
    
    def get_success_url(self):
        return reverse_lazy('proyectos:comite_detail', kwargs={'pk': self.object.comite.pk})
    
    def delete(self, request, *args, **kwargs):
        seguimiento = self.get_object()
        servicio_numero = seguimiento.servicio.numero_orden
        comite = seguimiento.comite
        messages.success(request, f'Seguimiento del servicio "{servicio_numero}" eliminado del comité.')
        return super().delete(request, *args, **kwargs)


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