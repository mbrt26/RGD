from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    Equipo, HojaVidaEquipo, RutinaMantenimiento, ContratoMantenimiento,
    ActividadMantenimiento, InformeMantenimiento, AdjuntoInformeMantenimiento,
    InformeMantenimientoUnidadPaquete, InformeMantenimientoColeccionPolvo
)
from crm.models import Cliente


class MantenimientoDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'mantenimiento/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        hoy = timezone.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_mes = hoy.replace(day=1)
        
        # Contadores principales
        context.update({
            'total_equipos': Equipo.objects.filter(activo=True).count(),
            'hojas_vida_activas': HojaVidaEquipo.objects.filter(activo=True).count(),
            'contratos_activos': ContratoMantenimiento.objects.filter(estado='activo').count(),
            'actividades_pendientes': ActividadMantenimiento.objects.filter(
                estado__in=['programada', 'asignada']
            ).count(),
        })
        
        # Actividades próximas (próximos 7 días)
        fecha_limite = hoy + timedelta(days=7)
        context['actividades_proximas'] = ActividadMantenimiento.objects.filter(
            fecha_programada__date__range=[hoy, fecha_limite],
            estado__in=['programada', 'asignada']
        ).select_related('hoja_vida_equipo', 'hoja_vida_equipo__cliente')[:10]
        
        # Actividades atrasadas
        context['actividades_atrasadas'] = ActividadMantenimiento.objects.filter(
            fecha_programada__date__lt=hoy,
            estado__in=['programada', 'asignada']
        ).select_related('hoja_vida_equipo', 'hoja_vida_equipo__cliente')[:10]
        
        # Contratos próximos a vencer (próximos 30 días)
        fecha_vencimiento = hoy + timedelta(days=30)
        context['contratos_por_vencer'] = ContratoMantenimiento.objects.filter(
            fecha_fin__range=[hoy, fecha_vencimiento],
            estado='activo'
        ).select_related('cliente')[:5]
        
        # Estadísticas por categoría de equipo
        context['estadisticas_categorias'] = Equipo.objects.values('categoria').annotate(
            total_equipos=Count('id'),
            hojas_vida_activas=Count('hojas_vida', filter=Q(hojas_vida__activo=True))
        ).order_by('-total_equipos')[:5]
        
        return context


# CRUD para Equipos (Base de datos de equipos)
class EquipoListView(LoginRequiredMixin, ListView):
    model = Equipo
    template_name = 'mantenimiento/equipo/list.html'
    context_object_name = 'equipos'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('creado_por')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(marca__icontains=search) |
                Q(modelo__icontains=search) |
                Q(descripcion__icontains=search)
            )
        
        # Filtro por categoría
        categoria = self.request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
            
        # Filtro por marca
        marca = self.request.GET.get('marca')
        if marca:
            queryset = queryset.filter(marca=marca)
            
        return queryset.order_by('categoria', 'marca', 'modelo')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Equipo.CATEGORIA_CHOICES
        context['marcas'] = Equipo.objects.values_list('marca', flat=True).distinct().order_by('marca')
        return context


class EquipoCreateView(LoginRequiredMixin, CreateView):
    model = Equipo
    template_name = 'mantenimiento/equipo/form.html'
    fields = [
        'nombre', 'descripcion', 'categoria', 'marca', 'modelo',
        'capacidad_btu', 'voltaje', 'amperaje', 'refrigerante', 'peso_kg',
        'fabricante', 'pais_origen', 'vida_util_anos', 'activo'
    ]
    success_url = reverse_lazy('mantenimiento:equipo_list')
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Equipo registrado exitosamente.')
        return super().form_valid(form)


class EquipoDetailView(LoginRequiredMixin, DetailView):
    model = Equipo
    template_name = 'mantenimiento/equipo/detail.html'
    context_object_name = 'equipo'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        equipo = self.get_object()
        
        # Hojas de vida de este equipo
        context['hojas_vida'] = equipo.hojas_vida.select_related('cliente').order_by('-fecha_instalacion')
        
        return context


class EquipoUpdateView(LoginRequiredMixin, UpdateView):
    model = Equipo
    template_name = 'mantenimiento/equipo/form.html'
    fields = [
        'nombre', 'descripcion', 'categoria', 'marca', 'modelo',
        'capacidad_btu', 'voltaje', 'amperaje', 'refrigerante', 'peso_kg',
        'fabricante', 'pais_origen', 'vida_util_anos', 'activo'
    ]
    success_url = reverse_lazy('mantenimiento:equipo_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Equipo actualizado exitosamente.')
        return super().form_valid(form)


# CRUD para Hojas de Vida de Equipos
class HojaVidaEquipoListView(LoginRequiredMixin, ListView):
    model = HojaVidaEquipo
    template_name = 'mantenimiento/hoja_vida/list.html'
    context_object_name = 'hojas_vida'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('equipo', 'cliente', 'creado_por')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(codigo_interno__icontains=search) |
                Q(numero_serie__icontains=search) |
                Q(tag_cliente__icontains=search) |
                Q(equipo__nombre__icontains=search) |
                Q(cliente__nombre__icontains=search)
            )
        
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
            
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        return queryset.order_by('cliente__nombre', 'codigo_interno')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        context['estados'] = HojaVidaEquipo.ESTADO_CHOICES
        return context


class HojaVidaEquipoCreateView(LoginRequiredMixin, CreateView):
    model = HojaVidaEquipo
    template_name = 'mantenimiento/hoja_vida/form.html'
    fields = [
        'equipo', 'cliente', 'codigo_interno', 'numero_serie', 'tag_cliente',
        'fecha_instalacion', 'fecha_compra', 'fecha_garantia_fin', 'proveedor',
        'valor_compra', 'ubicacion_detallada', 'direccion_instalacion',
        'coordenadas_gps', 'estado', 'observaciones', 'condiciones_ambientales', 'activo'
    ]
    success_url = reverse_lazy('mantenimiento:hoja_vida_list')
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Hoja de vida creada exitosamente.')
        return super().form_valid(form)


class HojaVidaEquipoDetailView(LoginRequiredMixin, DetailView):
    model = HojaVidaEquipo
    template_name = 'mantenimiento/hoja_vida/detail.html'
    context_object_name = 'hoja_vida'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoja_vida = self.get_object()
        
        # Rutinas de mantenimiento
        context['rutinas'] = hoja_vida.rutinas_mantenimiento.filter(activa=True)
        
        # Actividades de mantenimiento
        context['actividades'] = hoja_vida.actividades_mantenimiento.select_related(
            'tecnico_asignado'
        ).order_by('-fecha_programada')[:10]
        
        # Contratos que incluyen este equipo
        context['contratos'] = hoja_vida.contratos.filter(estado='activo')
        
        return context


class HojaVidaEquipoUpdateView(LoginRequiredMixin, UpdateView):
    model = HojaVidaEquipo
    template_name = 'mantenimiento/hoja_vida/form.html'
    fields = [
        'equipo', 'cliente', 'codigo_interno', 'numero_serie', 'tag_cliente',
        'fecha_instalacion', 'fecha_compra', 'fecha_garantia_fin', 'proveedor',
        'valor_compra', 'ubicacion_detallada', 'direccion_instalacion',
        'coordenadas_gps', 'estado', 'fecha_ultimo_servicio', 'observaciones',
        'condiciones_ambientales', 'activo'
    ]
    success_url = reverse_lazy('mantenimiento:hoja_vida_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Hoja de vida actualizada exitosamente.')
        return super().form_valid(form)


# CRUD para Contratos de Mantenimiento
class ContratoMantenimientoListView(LoginRequiredMixin, ListView):
    model = ContratoMantenimiento
    template_name = 'mantenimiento/contrato/list.html'
    context_object_name = 'contratos'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente', 'contacto_cliente', 'responsable_tecnico')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(numero_contrato__icontains=search) |
                Q(nombre_contrato__icontains=search) |
                Q(cliente__nombre__icontains=search)
            )
        
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
            
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        # Filtro por tipo
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_contrato=tipo)
            
        return queryset.order_by('-fecha_inicio')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        context['estados'] = ContratoMantenimiento.ESTADO_CHOICES
        context['tipos'] = ContratoMantenimiento.TIPO_CONTRATO_CHOICES
        return context


class ContratoMantenimientoCreateView(LoginRequiredMixin, CreateView):
    model = ContratoMantenimiento
    template_name = 'mantenimiento/contrato/form.html'
    fields = [
        'trato_origen', 'cotizacion_aprobada', 'cliente', 'nombre_contrato',
        'tipo_contrato', 'fecha_inicio', 'fecha_fin', 'meses_duracion',
        'renovacion_automatica', 'valor_mensual', 'valor_total_contrato',
        'incluye_materiales', 'incluye_repuestos', 'valor_hora_adicional',
        'tiempo_respuesta_horas', 'horas_incluidas_mes', 'disponibilidad_24_7',
        'contacto_cliente', 'responsable_tecnico', 'condiciones_especiales',
        'observaciones', 'clausulas_adicionales'
    ]
    success_url = reverse_lazy('mantenimiento:contrato_list')
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Contrato creado exitosamente.')
        return super().form_valid(form)


class ContratoMantenimientoDetailView(LoginRequiredMixin, DetailView):
    model = ContratoMantenimiento
    template_name = 'mantenimiento/contrato/detail.html'
    context_object_name = 'contrato'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contrato = self.get_object()
        
        # Equipos incluidos
        context['equipos_incluidos'] = contrato.equipos_incluidos.all()
        
        # Actividades del contrato
        context['actividades'] = contrato.actividades.select_related(
            'hoja_vida_equipo', 'tecnico_asignado'
        ).order_by('-fecha_programada')[:10]
        
        return context


class ContratoMantenimientoUpdateView(LoginRequiredMixin, UpdateView):
    model = ContratoMantenimiento
    template_name = 'mantenimiento/contrato/form.html'
    fields = [
        'trato_origen', 'cotizacion_aprobada', 'cliente', 'nombre_contrato',
        'tipo_contrato', 'fecha_inicio', 'fecha_fin', 'meses_duracion',
        'renovacion_automatica', 'valor_mensual', 'valor_total_contrato',
        'incluye_materiales', 'incluye_repuestos', 'valor_hora_adicional',
        'tiempo_respuesta_horas', 'horas_incluidas_mes', 'disponibilidad_24_7',
        'contacto_cliente', 'responsable_tecnico', 'estado', 'condiciones_especiales',
        'observaciones', 'clausulas_adicionales'
    ]
    success_url = reverse_lazy('mantenimiento:contrato_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Contrato actualizado exitosamente.')
        return super().form_valid(form)


# Vista consolidada de Actividades de Mantenimiento
class ActividadMantenimientoListView(LoginRequiredMixin, ListView):
    model = ActividadMantenimiento
    template_name = 'mantenimiento/actividad/list.html'
    context_object_name = 'actividades'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'contrato', 'hoja_vida_equipo', 'hoja_vida_equipo__cliente',
            'hoja_vida_equipo__equipo', 'tecnico_asignado', 'rutina_origen'
        )
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(codigo_actividad__icontains=search) |
                Q(titulo__icontains=search) |
                Q(hoja_vida_equipo__codigo_interno__icontains=search) |
                Q(hoja_vida_equipo__cliente__nombre__icontains=search)
            )
        
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(hoja_vida_equipo__cliente_id=cliente_id)
            
        # Filtro por equipo
        equipo_id = self.request.GET.get('equipo')
        if equipo_id:
            queryset = queryset.filter(hoja_vida_equipo_id=equipo_id)
            
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        # Filtro por tipo de actividad
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_actividad=tipo)
            
        # Filtro por técnico
        tecnico_id = self.request.GET.get('tecnico')
        if tecnico_id:
            queryset = queryset.filter(tecnico_asignado_id=tecnico_id)
            
        # Filtro por fechas
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_desde and fecha_hasta:
            queryset = queryset.filter(
                fecha_programada__date__range=[fecha_desde, fecha_hasta]
            )
        elif fecha_desde:
            queryset = queryset.filter(fecha_programada__date__gte=fecha_desde)
        elif fecha_hasta:
            queryset = queryset.filter(fecha_programada__date__lte=fecha_hasta)
            
        # Filtro por actividades atrasadas
        if self.request.GET.get('atrasadas') == '1':
            queryset = queryset.filter(
                fecha_programada__lt=timezone.now(),
                estado__in=['programada', 'asignada']
            )
            
        # Filtro por actividades pendientes
        if self.request.GET.get('pendientes') == '1':
            queryset = queryset.filter(estado__in=['programada', 'asignada'])
            
        # Filtro por actividades ejecutadas
        if self.request.GET.get('ejecutadas') == '1':
            queryset = queryset.filter(estado='completada')
            
        return queryset.order_by('fecha_programada')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        context['estados'] = ActividadMantenimiento.ESTADO_CHOICES
        context['tipos'] = ActividadMantenimiento.TIPO_ACTIVIDAD_CHOICES
        context['prioridades'] = ActividadMantenimiento.PRIORIDAD_CHOICES
        
        # Importar aquí para evitar dependencias circulares
        try:
            from servicios.models import Tecnico
            context['tecnicos'] = Tecnico.objects.filter(activo=True)
        except ImportError:
            context['tecnicos'] = []
        
        return context


class ActividadMantenimientoCreateView(LoginRequiredMixin, CreateView):
    model = ActividadMantenimiento
    template_name = 'mantenimiento/actividad/form.html'
    fields = [
        'contrato', 'hoja_vida_equipo', 'rutina_origen', 'tipo_actividad',
        'titulo', 'descripcion', 'fecha_programada', 'fecha_limite',
        'duracion_estimada_horas', 'prioridad', 'tecnico_asignado',
        'observaciones'
    ]
    success_url = reverse_lazy('mantenimiento:actividad_list')
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Actividad de mantenimiento creada exitosamente.')
        return super().form_valid(form)


class ActividadMantenimientoDetailView(LoginRequiredMixin, DetailView):
    model = ActividadMantenimiento
    template_name = 'mantenimiento/actividad/detail.html'
    context_object_name = 'actividad'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad = self.get_object()
        
        # Verificar si ya tiene informe
        try:
            context['informe'] = actividad.informe
        except InformeMantenimiento.DoesNotExist:
            context['informe'] = None
            
        return context


class ActividadMantenimientoUpdateView(LoginRequiredMixin, UpdateView):
    model = ActividadMantenimiento
    template_name = 'mantenimiento/actividad/form.html'
    fields = [
        'contrato', 'hoja_vida_equipo', 'rutina_origen', 'tipo_actividad',
        'titulo', 'descripcion', 'fecha_programada', 'fecha_limite',
        'duracion_estimada_horas', 'prioridad', 'tecnico_asignado', 'estado',
        'fecha_inicio_real', 'fecha_fin_real', 'observaciones',
        'motivo_reprogramacion', 'requiere_seguimiento'
    ]
    success_url = reverse_lazy('mantenimiento:actividad_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Actividad de mantenimiento actualizada exitosamente.')
        return super().form_valid(form)


# CRUD para Informes de Mantenimiento
class InformeMantenimientoCreateView(LoginRequiredMixin, CreateView):
    model = InformeMantenimiento
    template_name = 'mantenimiento/informe/form.html'
    fields = [
        'actividad', 'tecnico_ejecutor', 'fecha_ejecucion', 'hora_inicio', 'hora_fin',
        'resultado', 'trabajos_realizados', 'problemas_encontrados', 'soluciones_aplicadas',
        'estado_equipo_antes', 'estado_equipo_despues', 'funcionamiento_optimo',
        'checklist_realizado', 'materiales_utilizados', 'repuestos_cambiados', 
        'costo_materiales', 'costo_repuestos', 'recomendaciones', 'proxima_revision', 
        'trabajos_pendientes', 'requiere_repuestos', 'repuestos_requeridos', 
        'cliente_presente', 'nombre_cliente_receptor', 'cargo_cliente_receptor', 
        'satisfaccion_cliente', 'observaciones_cliente', 'foto_antes_1', 'foto_antes_2',
        'foto_despues_1', 'foto_despues_2', 'firma_tecnico', 'firma_cliente',
        'observaciones_tecnicas', 'observaciones_adicionales'
    ]
    success_url = reverse_lazy('mantenimiento:actividad_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Verificar si hay una actividad específica en la URL
        actividad_id = self.request.GET.get('actividad')
        
        if actividad_id:
            # Si hay una actividad específica, solo mostrar esa
            try:
                actividad = ActividadMantenimiento.objects.get(id=actividad_id)
                form.fields['actividad'].queryset = ActividadMantenimiento.objects.filter(id=actividad_id)
                form.fields['actividad'].initial = actividad
            except ActividadMantenimiento.DoesNotExist:
                # Si no existe la actividad, mostrar todas las disponibles
                actividades_sin_informe = ActividadMantenimiento.objects.filter(
                    informe__isnull=True, estado__in=['en_proceso', 'completada']
                ).select_related('hoja_vida_equipo').order_by('-fecha_programada')
                form.fields['actividad'].queryset = actividades_sin_informe
                form.fields['actividad'].empty_label = "--- Seleccione una actividad ---"
        else:
            # Solo mostrar actividades que no tienen informe
            actividades_sin_informe = ActividadMantenimiento.objects.filter(
                informe__isnull=True, estado__in=['en_proceso', 'completada']
            ).select_related('hoja_vida_equipo').order_by('-fecha_programada')
            form.fields['actividad'].queryset = actividades_sin_informe
            form.fields['actividad'].empty_label = "--- Seleccione una actividad ---"
            
        return form
    
    def form_valid(self, form):
        # Marcar la actividad como completada si no lo está
        if form.instance.actividad.estado != 'completada':
            form.instance.actividad.estado = 'completada'
            form.instance.actividad.fecha_fin_real = timezone.now()
            form.instance.actividad.save()
        
        messages.success(self.request, 'Informe de mantenimiento creado exitosamente.')
        return super().form_valid(form)


class InformeMantenimientoDetailView(LoginRequiredMixin, DetailView):
    model = InformeMantenimiento
    template_name = 'mantenimiento/informe/detail.html'
    context_object_name = 'informe'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['adjuntos'] = self.get_object().adjuntos.all()
        return context


class InformeMantenimientoUpdateView(LoginRequiredMixin, UpdateView):
    model = InformeMantenimiento
    template_name = 'mantenimiento/informe/form.html'
    fields = [
        'tecnico_ejecutor', 'fecha_ejecucion', 'hora_inicio', 'hora_fin',
        'resultado', 'trabajos_realizados', 'problemas_encontrados', 'soluciones_aplicadas',
        'estado_equipo_antes', 'estado_equipo_despues', 'funcionamiento_optimo',
        'checklist_realizado', 'materiales_utilizados', 'repuestos_cambiados',
        'costo_materiales', 'costo_repuestos', 'recomendaciones', 'proxima_revision',
        'trabajos_pendientes', 'requiere_repuestos', 'repuestos_requeridos',
        'cliente_presente', 'nombre_cliente_receptor', 'cargo_cliente_receptor',
        'satisfaccion_cliente', 'observaciones_cliente', 'firma_tecnico', 'firma_cliente',
        'foto_antes_1', 'foto_antes_2', 'foto_despues_1', 'foto_despues_2',
        'observaciones_tecnicas', 'observaciones_adicionales'
    ]
    success_url = reverse_lazy('mantenimiento:actividad_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Informe de mantenimiento actualizado exitosamente.')
        return super().form_valid(form)


# API Views para AJAX
@require_http_methods(["GET"])
def get_equipos_cliente(request, cliente_id):
    """API para obtener hojas de vida de equipos de un cliente específico"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        hojas_vida = HojaVidaEquipo.objects.filter(
            cliente_id=cliente_id, activo=True
        ).select_related('equipo').values(
            'id', 'codigo_interno', 'equipo__nombre', 'equipo__marca', 'equipo__modelo'
        )
        return JsonResponse(list(hojas_vida), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_rutinas_equipo(request, hoja_vida_id):
    """API para obtener rutinas de mantenimiento de un equipo específico"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        rutinas = RutinaMantenimiento.objects.filter(
            hoja_vida_equipo_id=hoja_vida_id, activa=True
        ).values('id', 'nombre_rutina', 'tipo_rutina', 'descripcion', 'duracion_estimada_horas')
        return JsonResponse(list(rutinas), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# Vista para seleccionar tipo de informe específico
class InformeEspecificoSeleccionView(LoginRequiredMixin, TemplateView):
    template_name = 'mantenimiento/informe/seleccionar_tipo.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad_id = self.kwargs.get('actividad_id')
        
        try:
            actividad = ActividadMantenimiento.objects.get(id=actividad_id)
            context['actividad'] = actividad
            context['tipos_informe'] = ActividadMantenimiento.TIPO_INFORME_CHOICES
        except ActividadMantenimiento.DoesNotExist:
            context['error'] = 'Actividad no encontrada'
            
        return context


# CRUD para Informe Mantenimiento Unidad Paquete
class InformeUnidadPaqueteCreateView(LoginRequiredMixin, CreateView):
    model = InformeMantenimientoUnidadPaquete
    template_name = 'mantenimiento/informe/unidad_paquete_form.html'
    fields = [
        'fecha', 'marca', 'sistema_modelo', 'equipo_serie', 'usuario',
        'tipo_mantenimiento', 'voltaje_l1_l2', 'voltaje_l2_l3', 'voltaje_l1_l3',
        'observaciones_previas',
        # Evaporador
        'evap_lavado', 'evap_desincrustante', 'evap_limpieza_bandeja', 'evap_limpieza_drenaje',
        'evap_motor_limpieza_rotores', 'evap_motor_lubricacion', 'evap_motor_rpm', 
        'evap_motor_amperaje', 'evap_motor_limpieza_ejes',
        'evap_nivel_aceite', 'evap_cambio_aceite', 'evap_ajuste_control_capacidad',
        'evap_amperaje_rla', 'evap_presion_succion', 'evap_presion_descarga',
        'evap_limpieza', 'evap_presostato_alta', 'evap_presostato_baja',
        # Condensador 1
        'comp1_modelo', 'comp1_revision_placas_bornes', 'comp1_nivel_aceite',
        'comp1_cambio_aceite', 'comp1_ajuste_control_capacidad',
        'cond1_limpieza_rotores', 'cond1_lubricacion', 'cond1_rpm',
        'cond1_amperaje_motor', 'cond1_limpieza_ejes',
        'cond1_nivel_aceite', 'cond1_cambio_aceite', 'cond1_ajuste_control_capacidad',
        'cond1_amperaje_rla', 'cond1_presion_succion', 'cond1_presion_descarga',
        'cond1_limpieza', 'cond1_presostato_alta', 'cond1_presostato_baja',
        # Condensador 2
        'comp2_modelo', 'comp2_revision_placas_bornes', 'comp2_nivel_aceite',
        'comp2_cambio_aceite', 'comp2_ajuste_control_capacidad',
        'cond2_limpieza_rotores', 'cond2_lubricacion', 'cond2_rpm',
        'cond2_amperaje_motor', 'cond2_limpieza_ejes',
        'cond2_nivel_aceite', 'cond2_cambio_aceite', 'cond2_ajuste_control_capacidad',
        'cond2_amperaje_rla', 'cond2_presion_succion', 'cond2_presion_descarga',
        'cond2_limpieza', 'cond2_presostato_alta', 'cond2_presostato_baja',
        # Refrigeración
        'refrig_carga_refrigerante', 'refrig_valvulas_solenoide', 'refrig_aislamiento',
        'refrig_pruebas_escapes', 'refrig_filtro_secador', 'refrig_valvula_expansion',
        'refrig_chequear_humedad',
        # Sistema Eléctrico
        'elect_limpieza_tablero', 'elect_limpieza_contactor', 'elect_operacion_timer',
        'elect_operacion_relevos', 'elect_revision_alambrado', 'elect_operacion_termostato',
        # Observaciones y firmas
        'observaciones_posteriores', 'prioridad',
        'ejecutado_por_nombre', 'ejecutado_por_fecha', 'ejecutado_por_firma',
        'supervisado_por_nombre', 'supervisado_por_fecha', 'supervisado_por_firma',
        'recibido_por_nombre', 'recibido_por_fecha', 'recibido_por_firma'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad_id = self.kwargs.get('actividad_id')
        
        try:
            actividad = ActividadMantenimiento.objects.get(id=actividad_id)
            context['actividad'] = actividad
            
            # Pre-llenar algunos campos con datos del equipo/actividad
            if not self.object:
                hoja_vida = actividad.hoja_vida_equipo
                equipo = hoja_vida.equipo
                context['initial_data'] = {
                    'fecha': timezone.now().date(),
                    'marca': equipo.marca,
                    'sistema_modelo': equipo.modelo,
                    'equipo_serie': hoja_vida.numero_serie,
                    'usuario': actividad.hoja_vida_equipo.cliente.nombre,
                    'ejecutado_por_fecha': timezone.now().date(),
                    'supervisado_por_fecha': timezone.now().date(),
                    'recibido_por_fecha': timezone.now().date(),
                }
        except ActividadMantenimiento.DoesNotExist:
            context['error'] = 'Actividad no encontrada'
            
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        actividad_id = self.kwargs.get('actividad_id')
        
        try:
            actividad = ActividadMantenimiento.objects.get(id=actividad_id)
            hoja_vida = actividad.hoja_vida_equipo
            equipo = hoja_vida.equipo
            
            initial.update({
                'fecha': timezone.now().date(),
                'marca': equipo.marca,
                'sistema_modelo': equipo.modelo,
                'equipo_serie': hoja_vida.numero_serie,
                'usuario': actividad.hoja_vida_equipo.cliente.nombre,
                'ejecutado_por_fecha': timezone.now().date(),
                'supervisado_por_fecha': timezone.now().date(),
                'recibido_por_fecha': timezone.now().date(),
            })
        except ActividadMantenimiento.DoesNotExist:
            pass
            
        return initial
    
    def form_valid(self, form):
        actividad_id = self.kwargs.get('actividad_id')
        
        try:
            actividad = ActividadMantenimiento.objects.get(id=actividad_id)
            form.instance.actividad = actividad
            form.instance.creado_por = self.request.user
            
            # Marcar la actividad como completada si no lo está
            if actividad.estado != 'completada':
                actividad.estado = 'completada'
                actividad.fecha_fin_real = timezone.now()
                actividad.save()
            
            messages.success(self.request, 'Informe de unidad paquete creado exitosamente.')
            return super().form_valid(form)
            
        except ActividadMantenimiento.DoesNotExist:
            messages.error(self.request, 'Actividad no encontrada.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('mantenimiento:actividad_detail', kwargs={'pk': self.object.actividad.pk})


class InformeUnidadPaqueteDetailView(LoginRequiredMixin, DetailView):
    model = InformeMantenimientoUnidadPaquete
    template_name = 'mantenimiento/informe/unidad_paquete_detail.html'
    context_object_name = 'informe'


class InformeUnidadPaqueteUpdateView(LoginRequiredMixin, UpdateView):
    model = InformeMantenimientoUnidadPaquete
    template_name = 'mantenimiento/informe/unidad_paquete_form.html'
    fields = [
        'fecha', 'marca', 'sistema_modelo', 'equipo_serie', 'usuario',
        'tipo_mantenimiento', 'voltaje_l1_l2', 'voltaje_l2_l3', 'voltaje_l1_l3',
        'observaciones_previas',
        # Evaporador
        'evap_lavado', 'evap_desincrustante', 'evap_limpieza_bandeja', 'evap_limpieza_drenaje',
        'evap_motor_limpieza_rotores', 'evap_motor_lubricacion', 'evap_motor_rpm', 
        'evap_motor_amperaje', 'evap_motor_limpieza_ejes',
        'evap_nivel_aceite', 'evap_cambio_aceite', 'evap_ajuste_control_capacidad',
        'evap_amperaje_rla', 'evap_presion_succion', 'evap_presion_descarga',
        'evap_limpieza', 'evap_presostato_alta', 'evap_presostato_baja',
        # Condensador 1
        'comp1_modelo', 'comp1_revision_placas_bornes', 'comp1_nivel_aceite',
        'comp1_cambio_aceite', 'comp1_ajuste_control_capacidad',
        'cond1_limpieza_rotores', 'cond1_lubricacion', 'cond1_rpm',
        'cond1_amperaje_motor', 'cond1_limpieza_ejes',
        'cond1_nivel_aceite', 'cond1_cambio_aceite', 'cond1_ajuste_control_capacidad',
        'cond1_amperaje_rla', 'cond1_presion_succion', 'cond1_presion_descarga',
        'cond1_limpieza', 'cond1_presostato_alta', 'cond1_presostato_baja',
        # Condensador 2
        'comp2_modelo', 'comp2_revision_placas_bornes', 'comp2_nivel_aceite',
        'comp2_cambio_aceite', 'comp2_ajuste_control_capacidad',
        'cond2_limpieza_rotores', 'cond2_lubricacion', 'cond2_rpm',
        'cond2_amperaje_motor', 'cond2_limpieza_ejes',
        'cond2_nivel_aceite', 'cond2_cambio_aceite', 'cond2_ajuste_control_capacidad',
        'cond2_amperaje_rla', 'cond2_presion_succion', 'cond2_presion_descarga',
        'cond2_limpieza', 'cond2_presostato_alta', 'cond2_presostato_baja',
        # Refrigeración
        'refrig_carga_refrigerante', 'refrig_valvulas_solenoide', 'refrig_aislamiento',
        'refrig_pruebas_escapes', 'refrig_filtro_secador', 'refrig_valvula_expansion',
        'refrig_chequear_humedad',
        # Sistema Eléctrico
        'elect_limpieza_tablero', 'elect_limpieza_contactor', 'elect_operacion_timer',
        'elect_operacion_relevos', 'elect_revision_alambrado', 'elect_operacion_termostato',
        # Observaciones y firmas
        'observaciones_posteriores', 'prioridad',
        'ejecutado_por_nombre', 'ejecutado_por_fecha', 'ejecutado_por_firma',
        'supervisado_por_nombre', 'supervisado_por_fecha', 'supervisado_por_firma',
        'recibido_por_nombre', 'recibido_por_fecha', 'recibido_por_firma'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actividad'] = self.object.actividad
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Informe de unidad paquete actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('mantenimiento:actividad_detail', kwargs={'pk': self.object.actividad.pk})


# CRUD para Informe Mantenimiento Colección de Polvo
class InformeColeccionPolvoCreateView(LoginRequiredMixin, CreateView):
    model = InformeMantenimientoColeccionPolvo
    template_name = 'mantenimiento/informe/coleccion_polvo_form.html'
    fields = [
        'fecha', 'marca', 'modelo', 'serie', 'cliente', 'ubicacion',
        'tipo_mantenimiento', 'voltaje_l1_l2', 'voltaje_l2_l3', 'voltaje_l1_l3',
        'observaciones_previas',
        # Conjunto Motor - Inspección Visual
        'motor_inspeccion_bobinado', 'motor_inspeccion_ventilador', 'motor_inspeccion_transmision',
        'motor_inspeccion_carcasa', 'motor_inspeccion_bornera',
        # Conjunto Motor - Actividades
        'motor_lubricacion_rodamientos', 'motor_limpieza_ventilador', 'motor_limpieza_carcasa',
        'motor_ajuste_transmision', 'motor_medicion_vibraciones', 'motor_medicion_temperatura',
        # Conjunto Motor - Mediciones
        'motor_amperaje', 'motor_voltaje', 'motor_rpm', 'motor_temperatura',
        'motor_vibracion_horizontal', 'motor_vibracion_vertical', 'motor_vibracion_axial',
        # Colectores de Polvo 1 - Actividades
        'colector1_limpieza_tolvas', 'colector1_revision_compuertas', 'colector1_revision_ductos',
        'colector1_revision_estructural', 'colector1_limpieza_estructura',
        # Colectores de Polvo 1 - Sistema de Filtros
        'colector1_revision_filtros', 'colector1_cambio_filtros', 'colector1_limpieza_camara',
        'colector1_revision_sellos',
        # Colectores de Polvo 1 - Sistema de Limpieza
        'colector1_revision_valvulas_pulso', 'colector1_prueba_secuencia', 
        'colector1_revision_compresor_aire', 'colector1_revision_tanque_aire',
        # Colectores de Polvo 1 - Mediciones
        'colector1_presion_diferencial', 'colector1_presion_aire', 'colector1_caudal_aire',
        # Sistema Eléctrico
        'elect_revision_tablero_principal', 'elect_limpieza_tablero', 'elect_revision_contactores',
        'elect_revision_relevos', 'elect_revision_fusibles', 'elect_revision_alambrado',
        'elect_prueba_funcionamiento', 'elect_medicion_resistencia',
        # Varios - Instrumentación
        'varios_revision_manometros', 'varios_calibracion_transmisores', 
        'varios_revision_termometros', 'varios_prueba_alarmas',
        # Varios - Sistema Control
        'varios_revision_plc', 'varios_revision_hmi', 'varios_backup_programa', 
        'varios_actualizacion_parametros',
        # Varios - Seguridad
        'varios_revision_paros_emergencia', 'varios_revision_guardas', 'varios_revision_señalizacion',
        # Observaciones y firmas
        'observaciones_posteriores', 'prioridad',
        'ejecutado_por_nombre', 'ejecutado_por_fecha', 'ejecutado_por_firma',
        'supervisado_por_nombre', 'supervisado_por_fecha', 'supervisado_por_firma',
        'recibido_por_nombre', 'recibido_por_fecha', 'recibido_por_firma'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        actividad_id = self.kwargs.get('actividad_id')
        
        try:
            actividad = ActividadMantenimiento.objects.get(id=actividad_id)
            context['actividad'] = actividad
            
            # Pre-llenar algunos campos con datos del equipo/actividad
            if not self.object:
                hoja_vida = actividad.hoja_vida_equipo
                equipo = hoja_vida.equipo
                context['initial_data'] = {
                    'fecha': timezone.now().date(),
                    'marca': equipo.marca,
                    'modelo': equipo.modelo,
                    'serie': hoja_vida.numero_serie,
                    'cliente': actividad.hoja_vida_equipo.cliente.nombre,
                    'ubicacion': hoja_vida.ubicacion_detallada,
                    'ejecutado_por_fecha': timezone.now().date(),
                    'supervisado_por_fecha': timezone.now().date(),
                    'recibido_por_fecha': timezone.now().date(),
                }
        except ActividadMantenimiento.DoesNotExist:
            context['error'] = 'Actividad no encontrada'
            
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        actividad_id = self.kwargs.get('actividad_id')
        
        try:
            actividad = ActividadMantenimiento.objects.get(id=actividad_id)
            hoja_vida = actividad.hoja_vida_equipo
            equipo = hoja_vida.equipo
            
            initial.update({
                'fecha': timezone.now().date(),
                'marca': equipo.marca,
                'modelo': equipo.modelo,
                'serie': hoja_vida.numero_serie,
                'cliente': actividad.hoja_vida_equipo.cliente.nombre,
                'ubicacion': hoja_vida.ubicacion_detallada,
                'ejecutado_por_fecha': timezone.now().date(),
                'supervisado_por_fecha': timezone.now().date(),
                'recibido_por_fecha': timezone.now().date(),
            })
        except ActividadMantenimiento.DoesNotExist:
            pass
            
        return initial
    
    def form_valid(self, form):
        actividad_id = self.kwargs.get('actividad_id')
        
        try:
            actividad = ActividadMantenimiento.objects.get(id=actividad_id)
            form.instance.actividad = actividad
            form.instance.creado_por = self.request.user
            
            # Marcar la actividad como completada si no lo está
            if actividad.estado != 'completada':
                actividad.estado = 'completada'
                actividad.fecha_fin_real = timezone.now()
                actividad.save()
            
            messages.success(self.request, 'Informe de colección de polvo creado exitosamente.')
            return super().form_valid(form)
            
        except ActividadMantenimiento.DoesNotExist:
            messages.error(self.request, 'Actividad no encontrada.')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('mantenimiento:actividad_detail', kwargs={'pk': self.object.actividad.pk})


class InformeColeccionPolvoDetailView(LoginRequiredMixin, DetailView):
    model = InformeMantenimientoColeccionPolvo
    template_name = 'mantenimiento/informe/coleccion_polvo_detail.html'
    context_object_name = 'informe'


class InformeColeccionPolvoUpdateView(LoginRequiredMixin, UpdateView):
    model = InformeMantenimientoColeccionPolvo
    template_name = 'mantenimiento/informe/coleccion_polvo_form.html'
    fields = [
        'fecha', 'marca', 'modelo', 'serie', 'cliente', 'ubicacion',
        'tipo_mantenimiento', 'voltaje_l1_l2', 'voltaje_l2_l3', 'voltaje_l1_l3',
        'observaciones_previas',
        # Conjunto Motor - Inspección Visual
        'motor_inspeccion_bobinado', 'motor_inspeccion_ventilador', 'motor_inspeccion_transmision',
        'motor_inspeccion_carcasa', 'motor_inspeccion_bornera',
        # Conjunto Motor - Actividades
        'motor_lubricacion_rodamientos', 'motor_limpieza_ventilador', 'motor_limpieza_carcasa',
        'motor_ajuste_transmision', 'motor_medicion_vibraciones', 'motor_medicion_temperatura',
        # Conjunto Motor - Mediciones
        'motor_amperaje', 'motor_voltaje', 'motor_rpm', 'motor_temperatura',
        'motor_vibracion_horizontal', 'motor_vibracion_vertical', 'motor_vibracion_axial',
        # Colectores de Polvo 1 - Actividades
        'colector1_limpieza_tolvas', 'colector1_revision_compuertas', 'colector1_revision_ductos',
        'colector1_revision_estructural', 'colector1_limpieza_estructura',
        # Colectores de Polvo 1 - Sistema de Filtros
        'colector1_revision_filtros', 'colector1_cambio_filtros', 'colector1_limpieza_camara',
        'colector1_revision_sellos',
        # Colectores de Polvo 1 - Sistema de Limpieza
        'colector1_revision_valvulas_pulso', 'colector1_prueba_secuencia', 
        'colector1_revision_compresor_aire', 'colector1_revision_tanque_aire',
        # Colectores de Polvo 1 - Mediciones
        'colector1_presion_diferencial', 'colector1_presion_aire', 'colector1_caudal_aire',
        # Sistema Eléctrico
        'elect_revision_tablero_principal', 'elect_limpieza_tablero', 'elect_revision_contactores',
        'elect_revision_relevos', 'elect_revision_fusibles', 'elect_revision_alambrado',
        'elect_prueba_funcionamiento', 'elect_medicion_resistencia',
        # Varios - Instrumentación
        'varios_revision_manometros', 'varios_calibracion_transmisores', 
        'varios_revision_termometros', 'varios_prueba_alarmas',
        # Varios - Sistema Control
        'varios_revision_plc', 'varios_revision_hmi', 'varios_backup_programa', 
        'varios_actualizacion_parametros',
        # Varios - Seguridad
        'varios_revision_paros_emergencia', 'varios_revision_guardas', 'varios_revision_señalizacion',
        # Observaciones y firmas
        'observaciones_posteriores', 'prioridad',
        'ejecutado_por_nombre', 'ejecutado_por_fecha', 'ejecutado_por_firma',
        'supervisado_por_nombre', 'supervisado_por_fecha', 'supervisado_por_firma',
        'recibido_por_nombre', 'recibido_por_fecha', 'recibido_por_firma'
    ]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['actividad'] = self.object.actividad
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'Informe de colección de polvo actualizado exitosamente.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('mantenimiento:actividad_detail', kwargs={'pk': self.object.actividad.pk})