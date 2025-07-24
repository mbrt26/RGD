from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.forms import inlineformset_factory
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
import base64
import io
from PIL import Image

from .models import SolicitudServicio, InformeTrabajo, MaterialConsumible, MaterialRequerido, AdjuntoInforme, UbicacionTecnico
from crm.models import Cliente, Contacto
from colaboradores.models import Colaborador

# Crear formset para materiales requeridos
MaterialRequeridoFormSet = inlineformset_factory(
    InformeTrabajo, 
    MaterialRequerido,
    fields=['descripcion', 'marca', 'referencia', 'unidad_medida', 'cantidad'],
    extra=1,
    min_num=0,
    validate_min=False,
    can_delete=True
)

# Crear formset para adjuntos de informe
AdjuntoInformeFormSet = inlineformset_factory(
    InformeTrabajo,
    AdjuntoInforme,
    fields=['archivo', 'descripcion'],
    extra=1,
    min_num=0,
    validate_min=False,
    can_delete=True
)

def process_signature(signature_data, field_name):
    """Procesa datos de firma digital y retorna un archivo de imagen"""
    if signature_data and signature_data.startswith('data:image'):
        try:
            # Remover el prefijo 'data:image/png;base64,'
            format, imgstr = signature_data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Decodificar base64
            img_data = base64.b64decode(imgstr)
            
            # Crear archivo
            filename = f"{field_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            return ContentFile(img_data, name=filename)
        except Exception as e:
            print(f"Error procesando firma {field_name}: {e}")
            return None
    return None


class ServiciosDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'servicios/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        hoy = timezone.now().date()
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_mes = hoy.replace(day=1)
        
        context.update({
            # 'total_tecnicos': Tecnico.objects.filter(activo=True).count(),
            'solicitudes_pendientes': SolicitudServicio.objects.filter(estado='planeada').count(),
            'servicios_hoy': SolicitudServicio.objects.filter(fecha_programada__date=hoy).count(),
            'informes_pendientes': SolicitudServicio.objects.filter(estado='en_proceso').count(),
            
            # Solicitudes por estado
            'solicitudes_por_estado': dict(
                SolicitudServicio.objects.values('estado').annotate(
                    count=Count('id')
                ).values_list('estado', 'count')
            ),
            
            # Servicios de la semana
            'servicios_semana': SolicitudServicio.objects.filter(
                fecha_programada__date__gte=inicio_semana
            ).order_by('fecha_programada')[:10],
            
            # Técnicos más activos
            # 'tecnicos_activos': Tecnico.objects.annotate(
            #     servicios_mes=Count('servicios_asignados', 
            #                       filter=Q(servicios_asignados__fecha_programada__gte=inicio_mes))
            # ).filter(activo=True).order_by('-servicios_mes')[:5],
        })
        
        return context


# class TecnicoListView(LoginRequiredMixin, ListView):
#     model = Tecnico
#     template_name = 'servicios/tecnico/list.html'
#     context_object_name = 'tecnicos'
#     paginate_by = 15
#     
#     def get_queryset(self):
#         queryset = super().get_queryset().select_related('usuario')
#         
#         # Filtro por búsqueda
#         search = self.request.GET.get('q', '')
#         if search:
#             queryset = queryset.filter(
#                 Q(codigo_tecnico__icontains=search) |
#                 Q(usuario__first_name__icontains=search) |
#                 Q(usuario__last_name__icontains=search) |
#                 Q(especialidades__icontains=search)
#             )
#         
#         # Filtro por estado
#         if self.request.GET.get('activo') == '1':
#             queryset = queryset.filter(activo=True)
#         elif self.request.GET.get('activo') == '0':
#             queryset = queryset.filter(activo=False)
#             
#         return queryset.order_by('codigo_tecnico')


# class TecnicoCreateView(LoginRequiredMixin, CreateView):
#     model = Tecnico
#     template_name = 'servicios/tecnico/form.html'
#     fields = ['usuario', 'codigo_tecnico', 'telefono', 'especialidades', 'activo']
#     success_url = reverse_lazy('servicios:tecnico_list')
#     
#     def form_valid(self, form):
#         messages.success(self.request, 'Técnico creado exitosamente.')
#         return super().form_valid(form)


# class TecnicoDetailView(LoginRequiredMixin, DetailView):
#     model = Tecnico
#     template_name = 'servicios/tecnico/detail.html'
#     context_object_name = 'tecnico'
#     
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         tecnico = self.get_object()
#         
#         # Servicios recientes
#         context['servicios_recientes'] = tecnico.servicios_asignados.select_related(
#             'cliente_crm'
#         ).order_by('-fecha_programada')[:10]
#         
#         # Estadísticas del técnico
#         hoy = timezone.now().date()
#         inicio_mes = hoy.replace(day=1)
#         
#         context['estadisticas'] = {
#             'servicios_mes': tecnico.servicios_asignados.filter(
#                 fecha_programada__gte=inicio_mes
#             ).count(),
#             'servicios_completados': tecnico.servicios_asignados.filter(
#                 estado='ejecutada'
#             ).count(),
#             'promedio_satisfaccion': tecnico.servicios_asignados.filter(
#                 informe__satisfaccion_cliente__isnull=False
#             ).aggregate(
#                 promedio=Avg('informe__satisfaccion_cliente')
#             )['promedio'] or 0
#         }
#         
#         return context


# class TecnicoUpdateView(LoginRequiredMixin, UpdateView):
#     model = Tecnico
#     template_name = 'servicios/tecnico/form.html'
#     fields = ['usuario', 'codigo_tecnico', 'telefono', 'especialidades', 'activo']
#     success_url = reverse_lazy('servicios:tecnico_list')
#     
#     def form_valid(self, form):
#         messages.success(self.request, 'Técnico actualizado exitosamente.')
#         return super().form_valid(form)


class SolicitudServicioListView(LoginRequiredMixin, ListView):
    model = SolicitudServicio
    template_name = 'servicios/solicitud/list.html'
    context_object_name = 'solicitudes'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'cliente_crm', 'tecnico_asignado',
            'trato_origen', 'cotizacion_aprobada__cotizacion__trato'
        )
        
        # Filtros
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(numero_orden__icontains=search) |
                Q(cliente_crm__nombre__icontains=search) |
                Q(direccion_servicio__icontains=search)
            )
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo_servicio=tipo)
            
        tecnico = self.request.GET.get('tecnico')
        if tecnico:
            queryset = queryset.filter(tecnico_asignado_id=tecnico)
            
        centro_costo = self.request.GET.get('centro_costo')
        if centro_costo:
            queryset = queryset.filter(centro_costo__icontains=centro_costo)
            
        return queryset.order_by('-fecha_programada')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = SolicitudServicio.ESTADO_CHOICES
        context['tipos'] = SolicitudServicio.TIPO_SERVICIO_CHOICES
        # context['tecnicos'] = Tecnico.objects.filter(activo=True)
        # Obtener centros de costos únicos
        context['centros_costos'] = SolicitudServicio.objects.exclude(
            centro_costo__isnull=True
        ).exclude(
            centro_costo__exact=''
        ).values_list('centro_costo', flat=True).distinct().order_by('centro_costo')
        return context


class SolicitudServicioCreateView(LoginRequiredMixin, CreateView):
    model = SolicitudServicio
    template_name = 'servicios/solicitud/form.html'
    fields = ['tipo_servicio', 'cliente_crm', 'contacto_crm', 'trato_origen', 'cotizacion_aprobada',
             'direccion_servicio', 'centro_costo', 'nombre_proyecto', 'orden_contrato', 'dias_prometidos',
             'fecha_contractual', 'fecha_programada', 'duracion_estimada', 'tecnico_asignado', 'director_proyecto', 
             'ingeniero_residente', 'cronograma', 'observaciones_internas']
    success_url = reverse_lazy('servicios:solicitud_list')
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Solicitud de servicio creada exitosamente.')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Usar colaboradores como técnicos
        form.fields['tecnico_asignado'].queryset = Colaborador.objects.all().order_by('nombre')
        
        # Importar y configurar colaboradores
        from colaboradores.models import Colaborador
        colaboradores = Colaborador.objects.all().order_by('nombre')
        form.fields['director_proyecto'].queryset = colaboradores
        form.fields['ingeniero_residente'].queryset = colaboradores
        form.fields['director_proyecto'].empty_label = "--- Seleccione un director ---"
        form.fields['ingeniero_residente'].empty_label = "--- Seleccione un ingeniero ---"
        
        # Configurar tratos disponibles
        from crm.models import Trato
        tratos = Trato.objects.select_related('cliente').order_by('-fecha_creacion')
        form.fields['trato_origen'].queryset = tratos
        form.fields['trato_origen'].empty_label = "--- Seleccione un trato ---"
        
        # Configurar cotizaciones disponibles - mostrar todas para creación
        from crm.models import VersionCotizacion
        cotizaciones = VersionCotizacion.objects.select_related('cotizacion__trato').order_by('-fecha_creacion')
        form.fields['cotizacion_aprobada'].queryset = cotizaciones
        form.fields['cotizacion_aprobada'].empty_label = "--- Seleccione una cotización ---"
        
        # Configurar widget de fecha con calendario
        from django import forms
        form.fields['fecha_programada'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_programada'].input_formats = ['%Y-%m-%dT%H:%M']
        
        return form


class SolicitudServicioDetailView(LoginRequiredMixin, DetailView):
    model = SolicitudServicio
    template_name = 'servicios/solicitud/detail.html'
    context_object_name = 'solicitud'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.get_object()
        
        # Verificar si ya tiene informe
        try:
            context['informe'] = solicitud.informe
        except InformeTrabajo.DoesNotExist:
            context['informe'] = None
            
        # Ubicaciones del técnico para esta solicitud
        context['ubicaciones'] = solicitud.ubicaciones_tecnico.order_by('-timestamp')[:5]
        
        return context


class SolicitudServicioUpdateView(LoginRequiredMixin, UpdateView):
    model = SolicitudServicio
    template_name = 'servicios/solicitud/form.html'
    fields = ['estado', 'tipo_servicio', 'cliente_crm', 'contacto_crm', 'trato_origen', 'cotizacion_aprobada',
             'direccion_servicio', 'centro_costo', 'nombre_proyecto', 'orden_contrato', 'dias_prometidos',
             'fecha_contractual', 'fecha_programada', 'duracion_estimada', 'tecnico_asignado', 'director_proyecto', 
             'ingeniero_residente', 'cronograma', 'observaciones_internas']
    success_url = reverse_lazy('servicios:solicitud_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Solicitud de servicio actualizada exitosamente.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Usar colaboradores como técnicos
        form.fields['tecnico_asignado'].queryset = Colaborador.objects.all().order_by('nombre')
        
        # Importar y configurar colaboradores
        from colaboradores.models import Colaborador
        colaboradores = Colaborador.objects.all().order_by('nombre')
        form.fields['director_proyecto'].queryset = colaboradores
        form.fields['ingeniero_residente'].queryset = colaboradores
        form.fields['director_proyecto'].empty_label = "--- Seleccione un director ---"
        form.fields['ingeniero_residente'].empty_label = "--- Seleccione un ingeniero ---"
        
        # Configurar tratos disponibles
        from crm.models import Trato
        tratos = Trato.objects.select_related('cliente').order_by('-fecha_creacion')
        form.fields['trato_origen'].queryset = tratos
        form.fields['trato_origen'].empty_label = "--- Seleccione un trato ---"
        
        # Configurar cotizaciones disponibles - filtrar por trato específico si existe
        from crm.models import VersionCotizacion
        if self.object and self.object.trato_origen:
            # Si estamos editando una solicitud existente con trato de origen, filtrar por ese trato específico
            cotizaciones = VersionCotizacion.objects.select_related('cotizacion__trato').filter(
                cotizacion__trato=self.object.trato_origen
            ).order_by('-fecha_creacion')
        elif self.object and self.object.cliente_crm:
            # Si no hay trato específico, filtrar por cliente como fallback
            cotizaciones = VersionCotizacion.objects.select_related('cotizacion__trato').filter(
                cotizacion__cliente=self.object.cliente_crm
            ).order_by('-fecha_creacion')
        else:
            # Si es una nueva solicitud, mostrar todas las cotizaciones
            cotizaciones = VersionCotizacion.objects.select_related('cotizacion__trato').order_by('-fecha_creacion')
        
        form.fields['cotizacion_aprobada'].queryset = cotizaciones
        form.fields['cotizacion_aprobada'].empty_label = "--- Seleccione una cotización ---"
        
        # Configurar widget de fecha con calendario
        from django import forms
        form.fields['fecha_programada'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_programada'].input_formats = ['%Y-%m-%dT%H:%M']
        
        return form


class InformeTrabajoListView(LoginRequiredMixin, ListView):
    model = InformeTrabajo
    template_name = 'servicios/informe/list.html'
    context_object_name = 'informes'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'solicitud_servicio__cliente_crm', 
            'solicitud_servicio__tecnico_asignado'
        )
        
        # Filtros
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(solicitud_servicio__numero_orden__icontains=search) |
                Q(solicitud_servicio__cliente_crm__nombre__icontains=search) |
                Q(descripcion_problema__icontains=search)
            )
        
        completado = self.request.GET.get('completado')
        if completado == '1':
            queryset = queryset.filter(completado=True)
        elif completado == '0':
            queryset = queryset.filter(completado=False)
            
        return queryset.order_by('-fecha_servicio')


class InformeTrabajoCreateView(LoginRequiredMixin, CreateView):
    model = InformeTrabajo
    template_name = 'servicios/informe/form.html'
    fields = ['solicitud_servicio', 'fecha_servicio', 'hora_ingreso', 'hora_salida', 'descripcion_problema', 
             'diagnostico_preliminar', 'detalle_trabajos', 'causas_problema', 'descripcion_trabajo', 
             'satisfaccion_cliente', 'observaciones_encuesta', 'recomendaciones']
    success_url = reverse_lazy('servicios:informe_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Configurar campo de causas_problema como checkboxes múltiples
        from django import forms
        form.fields['causas_problema'].widget = forms.CheckboxSelectMultiple(
            choices=InformeTrabajo.CAUSA_PROBLEMA_CHOICES
        )
        form.fields['causas_problema'].help_text = "Seleccione una o más causas del problema"
        
        # Configurar campo de descripcion_trabajo como checkboxes múltiples
        form.fields['descripcion_trabajo'].widget = forms.CheckboxSelectMultiple(
            choices=InformeTrabajo.DESCRIPCION_TRABAJO_CHOICES
        )
        form.fields['descripcion_trabajo'].help_text = "Seleccione uno o más tipos de trabajo"
        
        # Configurar campo de satisfacción del cliente
        form.fields['satisfaccion_cliente'].help_text = "Califique la experiencia del servicio de RGD Aire Acondicionado"
        form.fields['satisfaccion_cliente'].empty_label = "--- Seleccione una opción ---"
        
        # Configurar campos de hora con widget datetime
        form.fields['hora_ingreso'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'step': '60'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['hora_ingreso'].input_formats = ['%Y-%m-%dT%H:%M']
        form.fields['hora_ingreso'].help_text = "Hora de llegada al sitio de trabajo"
        
        form.fields['hora_salida'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control',
                'step': '60'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['hora_salida'].input_formats = ['%Y-%m-%dT%H:%M']
        form.fields['hora_salida'].help_text = "Hora de finalización del trabajo"
        
        # Verificar si hay una solicitud específica en la URL
        solicitud_id = self.request.GET.get('solicitud')
        
        if solicitud_id:
            # Si hay una solicitud específica, solo mostrar esa
            try:
                solicitud = SolicitudServicio.objects.get(id=solicitud_id)
                form.fields['solicitud_servicio'].queryset = SolicitudServicio.objects.filter(id=solicitud_id)
                form.fields['solicitud_servicio'].initial = solicitud
            except SolicitudServicio.DoesNotExist:
                # Si no existe la solicitud, mostrar todas las disponibles
                solicitudes_sin_informe = SolicitudServicio.objects.filter(
                    informe__isnull=True
                ).select_related('cliente_crm').order_by('-fecha_programada')
                form.fields['solicitud_servicio'].queryset = solicitudes_sin_informe
                form.fields['solicitud_servicio'].empty_label = "--- Seleccione una solicitud de servicio ---"
        else:
            # Solo mostrar solicitudes que no tienen informe
            solicitudes_sin_informe = SolicitudServicio.objects.filter(
                informe__isnull=True
            ).select_related('cliente_crm').order_by('-fecha_programada')
            form.fields['solicitud_servicio'].queryset = solicitudes_sin_informe
            form.fields['solicitud_servicio'].empty_label = "--- Seleccione una solicitud de servicio ---"
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['materiales_formset'] = MaterialRequeridoFormSet(
                self.request.POST, instance=self.object
            )
            context['adjuntos_formset'] = AdjuntoInformeFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['materiales_formset'] = MaterialRequeridoFormSet(instance=self.object)
            context['adjuntos_formset'] = AdjuntoInformeFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        materiales_formset = context['materiales_formset']
        adjuntos_formset = context['adjuntos_formset']
        
        # Validar si es visita de inspección y si necesita materiales
        solicitud = form.instance.solicitud_servicio or form.cleaned_data.get('solicitud_servicio')
        es_inspeccion = solicitud and solicitud.tipo_servicio == 'inspeccion'
        
        # Validar formsets
        if materiales_formset.is_valid() and adjuntos_formset.is_valid():
            # Si es inspección, validar que tenga al menos un material
            if es_inspeccion:
                materiales_validos = [
                    f for f in materiales_formset.forms 
                    if f.cleaned_data and not f.cleaned_data.get('DELETE', False) and f.cleaned_data.get('descripcion')
                ]
                if not materiales_validos:
                    messages.error(self.request, 'Para visitas de inspección es obligatorio especificar al menos un material requerido.')
                    return self.form_invalid(form)
            
            self.object = form.save()
            materiales_formset.instance = self.object
            materiales_formset.save()
            
            # Procesar adjuntos
            for adjunto_form in adjuntos_formset.forms:
                if adjunto_form.cleaned_data and not adjunto_form.cleaned_data.get('DELETE', False):
                    if adjunto_form.cleaned_data.get('archivo'):
                        adjunto = adjunto_form.save(commit=False)
                        adjunto.informe = self.object
                        
                        # Obtener información del archivo
                        archivo = adjunto_form.cleaned_data['archivo']
                        adjunto.nombre_original = archivo.name
                        adjunto.tamaño_archivo = archivo.size
                        
                        # Determinar tipo de adjunto basado en la extensión
                        extension = archivo.name.lower().split('.')[-1] if '.' in archivo.name else ''
                        if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
                            adjunto.tipo_adjunto = 'imagen'
                        elif extension in ['pdf', 'doc', 'docx', 'txt']:
                            adjunto.tipo_adjunto = 'documento'
                        elif extension in ['mp4', 'avi', 'mov', 'wmv']:
                            adjunto.tipo_adjunto = 'video'
                        elif extension in ['mp3', 'wav', 'm4a']:
                            adjunto.tipo_adjunto = 'audio'
                        else:
                            adjunto.tipo_adjunto = 'otro'
                        
                        adjunto.save()
            
            messages.success(self.request, 'Informe de trabajo creado exitosamente.')
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class InformeTrabajoDetailView(LoginRequiredMixin, DetailView):
    model = InformeTrabajo
    template_name = 'servicios/informe/detail.html'
    context_object_name = 'informe'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['materiales'] = self.get_object().materiales.all()
        context['materiales_requeridos'] = self.get_object().materiales_requeridos.all()
        context['adjuntos'] = self.get_object().adjuntos.all()
        return context


class InformeTrabajoUpdateView(LoginRequiredMixin, UpdateView):
    model = InformeTrabajo
    template_name = 'servicios/informe/form.html'
    fields = ['fecha_servicio', 'hora_ingreso', 'hora_salida', 'descripcion_problema', 
             'diagnostico_preliminar', 'detalle_trabajos', 'causas_problema', 'descripcion_trabajo', 'tipos_falla',
             'tecnico_nombre', 'tecnico_cargo', 'tecnico_fecha_firma', 'tecnico_firma',
             'cliente_nombre', 'cliente_cargo', 'cliente_fecha_firma', 'cliente_firma',
             'entregado_por_nombre', 'entregado_por_cargo', 'entregado_por_fecha', 'entregado_por_firma',
             'entregado_cliente_nombre', 'entregado_cliente_cargo', 'entregado_cliente_fecha', 'entregado_cliente_firma',
             'satisfaccion_cliente', 'observaciones_encuesta', 'recomendaciones', 'observaciones_adicionales']
    success_url = reverse_lazy('servicios:informe_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Configurar campo de causas_problema como checkboxes múltiples
        from django import forms
        form.fields['causas_problema'].widget = forms.CheckboxSelectMultiple(
            choices=InformeTrabajo.CAUSA_PROBLEMA_CHOICES
        )
        form.fields['causas_problema'].help_text = "Seleccione una o más causas del problema"
        
        # Configurar campo de descripcion_trabajo como checkboxes múltiples
        form.fields['descripcion_trabajo'].widget = forms.CheckboxSelectMultiple(
            choices=InformeTrabajo.DESCRIPCION_TRABAJO_CHOICES
        )
        form.fields['descripcion_trabajo'].help_text = "Seleccione uno o más tipos de trabajo"
        
        # Configurar campo de tipos_falla como checkboxes múltiples
        form.fields['tipos_falla'].widget = forms.CheckboxSelectMultiple(
            choices=InformeTrabajo.TIPO_FALLA_CHOICES
        )
        form.fields['tipos_falla'].help_text = "Seleccione uno o más tipos de falla"
        
        # Configurar campo de satisfacción del cliente
        form.fields['satisfaccion_cliente'].help_text = "Califique la experiencia del servicio de RGD Aire Acondicionado"
        form.fields['satisfaccion_cliente'].empty_label = "--- Seleccione una opción ---"
        
        # Configurar widgets de fecha para los campos de entrega
        fecha_fields = ['entregado_por_fecha', 'entregado_cliente_fecha']
        for field_name in fecha_fields:
            if field_name in form.fields:
                form.fields[field_name].widget = forms.DateInput(
                    attrs={
                        'type': 'date',
                        'class': 'form-control'
                    }
                )
        
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['materiales_formset'] = MaterialRequeridoFormSet(
                self.request.POST, instance=self.object
            )
            context['adjuntos_formset'] = AdjuntoInformeFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['materiales_formset'] = MaterialRequeridoFormSet(instance=self.object)
            context['adjuntos_formset'] = AdjuntoInformeFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        materiales_formset = context['materiales_formset']
        adjuntos_formset = context['adjuntos_formset']
        
        # Validar si es visita de inspección y si necesita materiales
        es_inspeccion = self.object.solicitud_servicio.tipo_servicio == 'inspeccion'
        
        # Validar formsets
        if materiales_formset.is_valid() and adjuntos_formset.is_valid():
            # Si es inspección, validar que tenga al menos un material
            if es_inspeccion:
                materiales_validos = [
                    f for f in materiales_formset.forms 
                    if f.cleaned_data and not f.cleaned_data.get('DELETE', False) and f.cleaned_data.get('descripcion')
                ]
                if not materiales_validos:
                    messages.error(self.request, 'Para visitas de inspección es obligatorio especificar al menos un material requerido.')
                    return self.form_invalid(form)
            
            # Procesar firmas digitales
            signature_fields = [
                ('tecnico_firma_data', 'tecnico_firma'),
                ('cliente_firma_data', 'cliente_firma'),
                ('entregado_por_firma_data', 'entregado_por_firma'),
                ('entregado_cliente_firma_data', 'entregado_cliente_firma')
            ]
            
            for signature_field, model_field in signature_fields:
                signature_data = self.request.POST.get(signature_field)
                if signature_data:
                    signature_file = process_signature(signature_data, model_field)
                    if signature_file:
                        setattr(form.instance, model_field, signature_file)
            
            self.object = form.save()
            materiales_formset.instance = self.object
            materiales_formset.save()
            
            # Procesar adjuntos
            for adjunto_form in adjuntos_formset.forms:
                if adjunto_form.cleaned_data and not adjunto_form.cleaned_data.get('DELETE', False):
                    if adjunto_form.cleaned_data.get('archivo'):
                        adjunto = adjunto_form.save(commit=False)
                        adjunto.informe = self.object
                        
                        # Obtener información del archivo
                        archivo = adjunto_form.cleaned_data['archivo']
                        adjunto.nombre_original = archivo.name
                        adjunto.tamaño_archivo = archivo.size
                        
                        # Determinar tipo de adjunto basado en la extensión
                        extension = archivo.name.lower().split('.')[-1] if '.' in archivo.name else ''
                        if extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp']:
                            adjunto.tipo_adjunto = 'imagen'
                        elif extension in ['pdf', 'doc', 'docx', 'txt']:
                            adjunto.tipo_adjunto = 'documento'
                        elif extension in ['mp4', 'avi', 'mov', 'wmv']:
                            adjunto.tipo_adjunto = 'video'
                        elif extension in ['mp3', 'wav', 'm4a']:
                            adjunto.tipo_adjunto = 'audio'
                        else:
                            adjunto.tipo_adjunto = 'otro'
                        
                        adjunto.save()
            
            messages.success(self.request, 'Informe de trabajo actualizado exitosamente.')
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


# API Views
@require_http_methods(["GET"])
def get_contactos_cliente(request, cliente_id):
    """API para obtener contactos de un cliente específico"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        contactos = Contacto.objects.filter(cliente_id=cliente_id).values('id', 'nombre', 'correo')
        return JsonResponse(list(contactos), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_contactos_trato(request, trato_id):
    """API para obtener contactos de un trato específico (incluye contacto del trato + contactos del cliente)"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        from crm.models import Trato
        trato = Trato.objects.select_related('cliente', 'contacto').get(id=trato_id)
        
        contactos_data = []
        
        # Agregar el contacto específico del trato si existe
        if trato.contacto:
            contactos_data.append({
                'id': trato.contacto.id,
                'nombre': trato.contacto.nombre,
                'correo': trato.contacto.correo,
                'es_contacto_trato': True
            })
        
        # Agregar otros contactos del cliente (excluyendo el ya agregado si existe)
        contactos_cliente = Contacto.objects.filter(cliente=trato.cliente)
        if trato.contacto:
            contactos_cliente = contactos_cliente.exclude(id=trato.contacto.id)
        
        for contacto in contactos_cliente:
            contactos_data.append({
                'id': contacto.id,
                'nombre': contacto.nombre,
                'correo': contacto.correo,
                'es_contacto_trato': False
            })
        
        return JsonResponse(contactos_data, safe=False)
    except Trato.DoesNotExist:
        return JsonResponse({'error': 'Trato no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_cotizaciones_cliente(request, cliente_id):
    """API para obtener cotizaciones de un cliente específico"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        from crm.models import VersionCotizacion
        cotizaciones = VersionCotizacion.objects.select_related('cotizacion__trato').filter(
            cotizacion__cliente_id=cliente_id
        ).order_by('-fecha_creacion')
        
        cotizaciones_data = []
        for cotizacion in cotizaciones:
            display_name = f"#{cotizacion.cotizacion.trato.numero_oferta} - V{cotizacion.version}" if cotizacion.cotizacion.trato else f"COT-{cotizacion.cotizacion.id} - V{cotizacion.version}"
            cotizaciones_data.append({
                'id': cotizacion.id,
                'display_name': display_name,
                'version': cotizacion.version,
                'valor': float(cotizacion.valor),
                'fecha_creacion': cotizacion.fecha_creacion.strftime('%d/%m/%Y')
            })
        
        return JsonResponse(cotizaciones_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_cotizaciones_trato(request, trato_id):
    """API para obtener cotizaciones de un trato específico"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        from crm.models import VersionCotizacion
        cotizaciones = VersionCotizacion.objects.select_related('cotizacion__trato').filter(
            cotizacion__trato_id=trato_id
        ).order_by('-fecha_creacion')
        
        cotizaciones_data = []
        for cotizacion in cotizaciones:
            display_name = f"#{cotizacion.cotizacion.trato.numero_oferta} - V{cotizacion.version}"
            cotizaciones_data.append({
                'id': cotizacion.id,
                'display_name': display_name,
                'version': cotizacion.version,
                'valor': float(cotizacion.valor),
                'fecha_creacion': cotizacion.fecha_creacion.strftime('%d/%m/%Y')
            })
        
        return JsonResponse(cotizaciones_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_solicitudes_tecnico(request, tecnico_id):
    """API para obtener solicitudes asignadas a un técnico"""
    try:
        solicitudes = SolicitudServicio.objects.filter(
            tecnico_asignado_id=tecnico_id
        ).values('id', 'numero_orden', 'cliente_crm__nombre', 'fecha_programada', 'estado')
        return JsonResponse(list(solicitudes), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["GET"])
def get_solicitud_tipo(request, solicitud_id):
    """API para obtener el tipo de servicio de una solicitud"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        solicitud = SolicitudServicio.objects.get(id=solicitud_id)
        return JsonResponse({
            'tipo_servicio': solicitud.tipo_servicio,
            'tipo_servicio_display': solicitud.get_tipo_servicio_display()
        })
    except SolicitudServicio.DoesNotExist:
        return JsonResponse({'error': 'Solicitud no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


class SolicitudServicioDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Vista para eliminar una solicitud de servicio con confirmación robusta"""
    model = SolicitudServicio
    template_name = 'servicios/solicitud/confirm_delete.html'
    success_url = reverse_lazy('servicios:solicitud_list')
    context_object_name = 'solicitud'
    
    def test_func(self):
        """Solo usuarios staff pueden eliminar solicitudes"""
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solicitud = self.get_object()
        
        # Obtener información relacionada para mostrar advertencias
        informes_count = InformeTrabajo.objects.filter(solicitud_servicio=solicitud).count()
        
        context.update({
            'title': f'Eliminar Solicitud: {solicitud.numero_orden}',
            'informes_count': informes_count,
            'tiene_datos_relacionados': informes_count > 0,
        })
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """Sobrescribir para agregar mensaje de confirmación"""
        solicitud = self.get_object()
        numero_orden = solicitud.numero_orden
        cliente = solicitud.cliente_crm.nombre if solicitud.cliente_crm else 'Cliente no especificado'
        
        # Verificar que el usuario confirmó explícitamente
        confirmacion = request.POST.get('confirmacion')
        if confirmacion != 'ELIMINAR':
            messages.error(
                request, 
                'Debe escribir "ELIMINAR" exactamente para confirmar la eliminación.'
            )
            return redirect('servicios:solicitud_delete', pk=solicitud.pk)
        
        # Mensaje de éxito antes de eliminar
        messages.success(
            request,
            f'Solicitud de servicio "{numero_orden}" del cliente "{cliente}" ha sido eliminada permanentemente.'
        )
        
        return super().delete(request, *args, **kwargs)
    
    def handle_no_permission(self):
        """Mensaje personalizado cuando no tiene permisos"""
        messages.error(
            self.request,
            'No tiene permisos para eliminar solicitudes. Solo los administradores pueden realizar esta acción.'
        )
        return redirect('servicios:solicitud_list')
