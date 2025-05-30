from django import forms
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Count, F, ProtectedError
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.db import transaction
import pandas as pd
import io
from .models import (
    Cliente, Contacto, Cotizacion, TareaVenta, Trato, 
    RepresentanteVentas, DocumentoCliente, VersionCotizacion
)
from .forms import (
    CotizacionForm, VersionCotizacionForm, CotizacionConVersionForm,
    ClienteImportForm, TratoImportForm
)

class CRMDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/dashboard.html'

    def get_queryset_filters(self, request):
        """Aplica los filtros al queryset de tratos"""
        today = timezone.now()
        
        # Obtener parámetros de filtro
        cliente_id = request.GET.get('cliente')
        comercial_id = request.GET.get('comercial')
        tipo_negociacion = request.GET.get('tipo_negociacion')
        periodo = request.GET.get('periodo', 'mes')  # mes o trimestre
        trimestre = request.GET.get('trimestre')  # 1, 2, 3, 4

        # Base queryset para tratos
        tratos_qs = Trato.objects.all()  # Cambiado para incluir todos los tratos, no solo los ganados

        # Aplicar filtros
        if cliente_id:
            tratos_qs = tratos_qs.filter(cliente_id=cliente_id)
        if comercial_id:
            tratos_qs = tratos_qs.filter(responsable_id=comercial_id)
        if tipo_negociacion:
            tratos_qs = tratos_qs.filter(tipo_negociacion=tipo_negociacion)

        # Filtrar por período
        if periodo == 'mes':
            primer_dia_mes = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            tratos_qs = tratos_qs.filter(fecha_cierre__gte=primer_dia_mes)
        elif periodo == 'trimestre' and trimestre:
            año_actual = today.year
            trimestres = {
                '1': (1, 3),   # Enero - Marzo
                '2': (4, 6),   # Abril - Junio
                '3': (7, 9),   # Julio - Septiembre
                '4': (10, 12), # Octubre - Diciembre
            }
            if trimestre in trimestres:
                mes_inicio, mes_fin = trimestres[trimestre]
                fecha_inicio = today.replace(month=mes_inicio, day=1, hour=0, minute=0, second=0, microsecond=0)
                if mes_fin == 12:
                    fecha_fin = today.replace(month=mes_fin, day=31, hour=23, minute=59, second=59, microsecond=999999)
                else:
                    fecha_fin = today.replace(month=mes_fin + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                tratos_qs = tratos_qs.filter(fecha_cierre__range=(fecha_inicio, fecha_fin))
        
        return tratos_qs

    def get_dashboard_data(self, request):
        """Obtiene los datos del dashboard según los filtros aplicados"""
        tratos_qs = self.get_queryset_filters(request)
        tratos_ganados_qs = tratos_qs.filter(estado='ganado')
        today = timezone.now()
        
        # Calcular métricas
        total_ganado = tratos_ganados_qs.aggregate(total=Sum('valor'))['total'] or 0
        total_clientes = Cliente.objects.count()
        total_tratos = tratos_qs.count()
        tratos_abiertos = tratos_qs.exclude(estado__in=['ganado', 'perdido', 'cancelado']).count()
        valor_total_tratos = tratos_qs.aggregate(total=Sum('valor'))['total'] or 0
        
        # Tratos por estado
        tratos_por_estado = {
            'nuevo': tratos_qs.filter(estado='nuevo').count(),
            'cotizacion': tratos_qs.filter(estado='cotizacion').count(),
            'negociacion': tratos_qs.filter(estado='negociacion').count(),
            'ganado': tratos_qs.filter(estado='ganado').count(),
            'perdido': tratos_qs.filter(estado='perdido').count(),
        }
        
        # Tratos por fuente
        tratos_por_fuente = dict(Trato.FUENTE_CHOICES)
        fuentes_data = {}
        for fuente in tratos_por_fuente:
            fuentes_data[tratos_por_fuente[fuente]] = tratos_qs.filter(fuente=fuente).count()
        
        # Últimos tratos
        ultimos_tratos = []
        for trato in tratos_qs.order_by('-fecha_creacion')[:5]:
            ultimos_tratos.append({
                'id': trato.id,
                'nombre': trato.nombre,
                'cliente': trato.cliente.nombre,
                'valor': float(trato.valor) if trato.valor else 0,
                'estado': trato.get_estado_display(),
                'fecha_creacion': trato.fecha_creacion.strftime('%d/%m/%Y')
            })
        
        # Tareas atrasadas
        tareas_atrasadas = TareaVenta.objects.filter(
            estado='pendiente',
            fecha_vencimiento__lt=today.date()
        ).count()
        
        return {
            'total_ganado': float(total_ganado),
            'total_clientes': total_clientes,
            'total_tratos': total_tratos,
            'tratos_abiertos': tratos_abiertos,
            'valor_total_tratos': float(valor_total_tratos),
            'tratos_por_estado': tratos_por_estado,
            'tratos_por_fuente': fuentes_data,
            'ultimos_tratos': ultimos_tratos,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        
        # Obtener datos del dashboard
        dashboard_data = self.get_dashboard_data(request)
        
        # Agregar datos del dashboard al contexto
        context.update(dashboard_data)
        
        # Agregar opciones para los filtros
        context['clientes'] = list(Cliente.objects.values('id', 'nombre'))
        context['comerciales'] = list(get_user_model().objects.filter(
            tratos__isnull=False
        ).distinct().values('id', 'first_name', 'last_name'))
        context['tipos_negociacion'] = [{'id': k, 'nombre': v} for k, v in Trato.TIPO_CHOICES]
        
        # Mantener filtros seleccionados en el contexto
        context['filtros'] = {
            'cliente': request.GET.get('cliente', ''),
            'comercial': request.GET.get('comercial', ''),
            'tipo_negociacion': request.GET.get('tipo_negociacion', ''),
            'periodo': request.GET.get('periodo', 'mes'),
            'trimestre': request.GET.get('trimestre', '')
        }
        
        # Asegurarse de que los datos de los gráficos estén en el formato correcto
        if 'tratos_por_estado' not in context:
            context['tratos_por_estado'] = {
                'nuevo': 0,
                'cotizacion': 0,
                'negociacion': 0,
                'ganado': 0,
                'perdido': 0
            }
            
        if 'tratos_por_fuente' not in context:
            context['tratos_por_fuente'] = {}
            
        if 'ultimos_tratos' not in context:
            context['ultimos_tratos'] = []
        
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Si es una petición AJAX, devolver los datos en formato JSON
            return JsonResponse(context, safe=False, json_dumps_params={'ensure_ascii': False})
        return self.render_to_response(context)

# Vistas para Cliente
class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'crm/cliente/list.html'
    context_object_name = 'clientes'

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    template_name = 'crm/cliente/form.html'
    fields = ['nombre', 'sector_actividad', 'correo', 'telefono', 'direccion_linea1', 'direccion_linea2', 
              'ciudad', 'estado', 'pais', 'codigo_postal', 'rut', 'notas']
    success_url = reverse_lazy('crm:cliente_list')

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        files = request.FILES.getlist('documentos')
        
        if form.is_valid():
            cliente = form.save()
            for f in files:
                DocumentoCliente.objects.create(
                    cliente=cliente,
                    archivo=f,
                    nombre=f.name
                )
            return redirect(self.success_url)
        
        return self.form_invalid(form)

class ClienteDetailView(LoginRequiredMixin, DetailView):
    model = Cliente
    template_name = 'crm/cliente/detail.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Usar el objeto cliente directamente en lugar de su nombre
        context['tratos'] = Trato.objects.filter(cliente=self.object)
        context['cotizaciones'] = Cotizacion.objects.filter(cliente=self.object)
        return context

class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    template_name = 'crm/cliente/form.html'
    fields = ['nombre', 'sector_actividad', 'correo', 'telefono', 'direccion_linea1', 'direccion_linea2', 
              'ciudad', 'estado', 'pais', 'codigo_postal', 'rut', 'notas']
    success_url = reverse_lazy('crm:cliente_list')

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        files = request.FILES.getlist('documentos')
        
        if form.is_valid():
            cliente = form.save()
            for f in files:
                DocumentoCliente.objects.create(
                    cliente=cliente,
                    archivo=f,
                    nombre=f.name
                )
            return redirect(self.success_url)
        
        return self.form_invalid(form)

class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'crm/cliente/confirm_delete.html'
    success_url = reverse_lazy('crm:cliente_list')

class ClienteImportView(LoginRequiredMixin, FormView):
    template_name = 'crm/cliente/import.html'
    form_class = ClienteImportForm
    success_url = reverse_lazy('crm:cliente_list')
    
    def form_valid(self, form):
        try:
            archivo_excel = form.cleaned_data['archivo_excel']
            
            # Leer el archivo Excel
            df = pd.read_excel(archivo_excel)
            
            # Validar las columnas requeridas
            required_columns = ['nombre', 'sector_actividad', 'correo', 'telefono', 'rut']
            if not all(col in df.columns for col in required_columns):
                messages.error(self.request, 'El archivo Excel debe contener las columnas: ' + ', '.join(required_columns))
                return self.form_invalid(form)
            
            # Procesar cada fila
            clientes_creados = 0
            for _, row in df.iterrows():
                try:
                    Cliente.objects.create(
                        nombre=row['nombre'],
                        sector_actividad=row.get('sector_actividad', ''),
                        correo=row.get('correo', ''),
                        telefono=row.get('telefono', ''),
                        direccion_linea1=row.get('direccion_linea1', ''),
                        direccion_linea2=row.get('direccion_linea2', ''),
                        ciudad=row.get('ciudad', ''),
                        estado=row.get('estado', ''),
                        pais=row.get('pais', ''),
                        codigo_postal=row.get('codigo_postal', ''),
                        rut=row.get('rut', ''),
                        notas=row.get('notas', '')
                    )
                    clientes_creados += 1
                except Exception as e:
                    messages.warning(self.request, f'Error al importar cliente {row.get("nombre", "desconocido")}: {str(e)}')
            
            messages.success(self.request, f'Se importaron {clientes_creados} clientes exitosamente.')
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo Excel: {str(e)}')
            return self.form_invalid(form)

# Vistas para RepresentanteVentas
class RepresentanteListView(LoginRequiredMixin, ListView):
    model = RepresentanteVentas
    template_name = 'crm/representante/list.html'
    context_object_name = 'representantes'
    title = 'Lista de Representantes'
    add_url = 'crm:representante_create'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('usuario')
        print("Número de representantes en la consulta:", queryset.count())
        # Instead of using values_list on nombre (which is a property),
        # we'll get the full objects and let the template use the property
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['view'] = {'add_url': self.add_url}
        context['add_url'] = self.add_url
        return context

class RepresentanteCreateView(LoginRequiredMixin, CreateView):
    model = RepresentanteVentas
    template_name = 'crm/representante/form.html'
    fields = '__all__'
    success_url = reverse_lazy('crm:representante_list')

class RepresentanteDetailView(LoginRequiredMixin, DetailView):
    model = RepresentanteVentas
    template_name = 'crm/representante/detail.html'
    context_object_name = 'representante'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tratos'] = Trato.objects.filter(representante=self.object)
        return context

class RepresentanteUpdateView(LoginRequiredMixin, UpdateView):
    model = RepresentanteVentas
    template_name = 'crm/representante/form.html'
    fields = '__all__'
    success_url = reverse_lazy('crm:representante_list')

# Vistas para Cotizacion
class CotizacionListView(LoginRequiredMixin, ListView):
    model = Cotizacion
    template_name = 'crm/oferta/list.html'
    context_object_name = 'cotizacion_list'
    title = 'Lista de Ofertas'
    add_url = 'crm:cotizacion_create'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related('cliente')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        # Asegurar que add_url esté disponible tanto directamente como dentro de view
        context['view'] = {'add_url': self.add_url}
        context['add_url'] = self.add_url
        return context

class CotizacionCreateView(LoginRequiredMixin, CreateView):
    model = Cotizacion
    template_name = 'crm/oferta/form.html'
    form_class = CotizacionConVersionForm
    success_url = reverse_lazy('crm:cotizacion_list')

    def form_valid(self, form):
        with transaction.atomic():
            # Guardar la cotización
            cotizacion = form.save()
            
            # Crear la primera versión
            VersionCotizacion.objects.create(
                cotizacion=cotizacion,
                version=1,
                archivo=self.request.FILES['archivo'],
                razon_cambio=form.cleaned_data['razon_cambio'],
                valor=cotizacion.monto,
                creado_por=self.request.user
            )
            
            messages.success(self.request, 'Cotización creada exitosamente.')
            return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)

class CotizacionDetailView(LoginRequiredMixin, DetailView):
    model = Cotizacion
    template_name = 'crm/oferta/detail.html'
    context_object_name = 'cotizacion'

class CotizacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Cotizacion
    template_name = 'crm/oferta/form.html'
    form_class = CotizacionConVersionForm
    success_url = reverse_lazy('crm:cotizacion_list')

    def form_valid(self, form):
        with transaction.atomic():
            cotizacion = form.save()
            if 'archivo' in self.request.FILES:
                # Obtener la última versión
                ultima_version = VersionCotizacion.objects.filter(
                    cotizacion=cotizacion
                ).order_by('-version').first()
                
                nuevo_numero_version = 1 if not ultima_version else ultima_version.version + 1
                
                # Crear nueva versión
                VersionCotizacion.objects.create(
                    cotizacion=cotizacion,
                    version=nuevo_numero_version,
                    archivo=self.request.FILES['archivo'],
                    razon_cambio=form.cleaned_data['razon_cambio'],
                    valor=cotizacion.monto,
                    creado_por=self.request.user
                )
            
            messages.success(self.request, 'Cotización actualizada exitosamente.')
            return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor corrija los errores en el formulario.')
        return super().form_invalid(form)

class CotizacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Cotizacion
    success_url = reverse_lazy('crm:cotizacion_list')

    def delete(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'No se puede eliminar esta cotización porque tiene elementos relacionados.')
            return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

# Vistas para TareaVenta
class TareaVentaListView(LoginRequiredMixin, ListView):
    model = TareaVenta
    template_name = 'crm/tarea/list.html'
    context_object_name = 'tareas'
    title = 'Lista de Tareas de Venta'
    add_url = 'crm:tarea_create'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente', 'responsable', 'trato')
        
        # Filtros
        cliente_id = self.request.GET.get('cliente')
        trato_id = self.request.GET.get('trato')
        responsable_id = self.request.GET.get('responsable')
        numero_oferta = self.request.GET.get('numero_oferta')
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if trato_id:
            queryset = queryset.filter(trato_id=trato_id)
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)
        if numero_oferta:
            queryset = queryset.filter(trato__numero_oferta__icontains=numero_oferta)
            
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['view'] = {'add_url': self.add_url}
        context['add_url'] = self.add_url
        
        # Agregar opciones de filtrado al contexto
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        context['tratos'] = Trato.objects.all().order_by('-fecha_creacion')
        context['responsables'] = get_user_model().objects.filter(
            tareas_asignadas__isnull=False
        ).distinct().order_by('username')
        
        # Mantener los filtros seleccionados
        context['selected_cliente'] = self.request.GET.get('cliente')
        context['selected_trato'] = self.request.GET.get('trato')
        context['selected_responsable'] = self.request.GET.get('responsable')
        context['selected_numero_oferta'] = self.request.GET.get('numero_oferta')
        
        return context

class TareaVentaCreateView(LoginRequiredMixin, CreateView):
    model = TareaVenta
    template_name = 'crm/tarea/form.html'
    fields = ['titulo', 'cliente', 'trato', 'tipo', 'descripcion', 'fecha_vencimiento', 
              'estado', 'prioridad', 'responsable', 'notas', 'fecha_ejecucion']
    success_url = reverse_lazy('crm:tarea_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['fecha_vencimiento'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_ejecucion'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
        return form

class TareaVentaDetailView(LoginRequiredMixin, DetailView):
    model = TareaVenta
    template_name = 'crm/tarea/detail.html'
    context_object_name = 'tarea'

class TareaVentaUpdateView(LoginRequiredMixin, UpdateView):
    model = TareaVenta
    template_name = 'crm/tarea/form.html'
    fields = ['titulo', 'cliente', 'trato', 'tipo', 'descripcion', 'fecha_vencimiento', 
              'estado', 'prioridad', 'responsable', 'notas', 'fecha_ejecucion']
    success_url = reverse_lazy('crm:tarea_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['fecha_vencimiento'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_ejecucion'].widget = forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
        return form

# Vistas para Trato
class TratoListView(LoginRequiredMixin, ListView):
    model = Trato
    template_name = 'crm/trato/list.html'
    context_object_name = 'tratos'
    title = 'Lista de Tratos'
    add_url = 'crm:trato_create'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('responsable').order_by('-numero_oferta')
        
        # Filtro de búsqueda
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(numero_oferta__icontains=search_query) |
                Q(cliente__icontains=search_query) |
                Q(descripcion__icontains=search_query) |
                Q(responsable__username__icontains=search_query) |
                Q(nombre__icontains=search_query)
            )
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['add_url'] = reverse_lazy(self.add_url)
        return context

class TratoCreateView(LoginRequiredMixin, CreateView):
    model = Trato
    template_name = 'crm/trato/form.html'
    fields = ['nombre', 'cliente', 'contacto', 'correo', 'telefono', 'descripcion', 
              'valor', 'probabilidad', 'estado', 'fuente', 'fecha_cierre', 'responsable', 'notas',
              'centro_costos', 'nombre_proyecto', 'orden_contrato', 'dias_prometidos', 'tipo_negociacion']
    success_url = reverse_lazy('crm:trato_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['fecha_cierre'].widget = forms.DateInput(attrs={'type': 'date'})
        return form
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context['title'] = 'Nuevo Trato'
        context['clientes'] = Cliente.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        return context

class TratoDetailView(LoginRequiredMixin, DetailView):
    model = Trato
    template_name = 'crm/trato/detail.html'
    context_object_name = 'trato'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cotizaciones'] = Cotizacion.objects.filter(trato=self.object).order_by('-fecha_creacion')
        context['tareas'] = TareaVenta.objects.filter(trato=self.object).order_by('-fecha_vencimiento')
        return context

class TratoUpdateView(LoginRequiredMixin, UpdateView):
    model = Trato
    template_name = 'crm/trato/form.html'
    fields = ['nombre', 'cliente', 'contacto', 'correo', 'telefono', 'descripcion', 
              'valor', 'probabilidad', 'estado', 'fuente', 'fecha_cierre', 'responsable', 'notas',
              'centro_costos', 'nombre_proyecto', 'orden_contrato', 'dias_prometidos', 'tipo_negociacion']
    success_url = reverse_lazy('crm:trato_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['fecha_cierre'].widget = forms.DateInput(attrs={'type': 'date'})
        return form
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context['title'] = f'Editar Trato: {self.object.nombre}'
        context['clientes'] = Cliente.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        context['tareas'] = TareaVenta.objects.filter(trato=self.object).order_by('-fecha_vencimiento')
        return context

class TratoImportView(LoginRequiredMixin, FormView):
    template_name = 'crm/trato/import.html'
    form_class = TratoImportForm
    success_url = reverse_lazy('crm:trato_list')
    
    def form_valid(self, form):
        try:
            archivo_excel = form.cleaned_data['archivo_excel']
            
            # Leer el archivo Excel
            df = pd.read_excel(archivo_excel)
            
            # Validar las columnas requeridas
            required_columns = ['nombre', 'cliente', 'valor', 'estado', 'fecha_cierre']
            if not all(col in df.columns for col in required_columns):
                messages.error(self.request, 'El archivo Excel debe contener las columnas: ' + ', '.join(required_columns))
                return self.form_invalid(form)
            
            # Procesar cada fila
            tratos_creados = 0
            for _, row in df.iterrows():
                try:
                    # Buscar o crear el cliente
                    cliente = Cliente.objects.filter(nombre=row['cliente']).first()
                    if not cliente:
                        messages.warning(self.request, f'Cliente no encontrado: {row["cliente"]}. Se omitirá este trato.')
                        continue

                    Trato.objects.create(
                        nombre=row['nombre'],
                        cliente=cliente,
                        correo=row.get('correo', ''),
                        telefono=row.get('telefono', ''),
                        descripcion=row.get('descripcion', ''),
                        valor=row['valor'],
                        probabilidad=row.get('probabilidad', 50),
                        estado=row['estado'],
                        fuente=row.get('fuente', ''),
                        fecha_cierre=row['fecha_cierre'],
                        responsable=self.request.user,
                        notas=row.get('notas', ''),
                        centro_costos=row.get('centro_costos', ''),
                        nombre_proyecto=row.get('nombre_proyecto', ''),
                        orden_contrato=row.get('orden_contrato', ''),
                        dias_prometidos=row.get('dias_prometidos', 0),
                        tipo_negociacion=row.get('tipo_negociacion', ''),
                        creado_por=self.request.user
                    )
                    tratos_creados += 1
                except Exception as e:
                    messages.warning(self.request, f'Error al importar trato {row.get("nombre", "desconocido")}: {str(e)}')
            
            messages.success(self.request, f'Se importaron {tratos_creados} tratos exitosamente.')
            return super().form_valid(form)
            
        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo Excel: {str(e)}')
            return self.form_invalid(form)

class ContactoCreateView(LoginRequiredMixin, CreateView):
    model = Contacto
    fields = ['nombre', 'cargo', 'correo', 'telefono', 'notas']
    
    def form_valid(self, form):
        cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_id'])
        form.instance.cliente = cliente
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('crm:cliente_detail', kwargs={'pk': self.kwargs['cliente_id']})

# Vistas para descargar plantillas de Excel
class ClientePlantillaExcelView(LoginRequiredMixin, TemplateView):
    """Vista para generar y descargar plantilla de Excel para clientes"""
    
    def get(self, request, *args, **kwargs):
        # Crear un DataFrame con las columnas y datos de ejemplo
        datos_ejemplo = {
            'nombre': ['Ejemplo Empresa ABC', 'Cliente Muestra XYZ'],
            'sector_actividad': ['Tecnología', 'Comercio'],
            'correo': ['contacto@empresa.com', 'info@cliente.com'],
            'telefono': ['+56912345678', '+56987654321'],
            'rut': ['12345678-9', '98765432-1'],
            'direccion_linea1': ['Av. Principal 123', 'Calle Secundaria 456'],
            'direccion_linea2': ['Oficina 201', ''],
            'ciudad': ['Santiago', 'Valparaíso'],
            'estado': ['Región Metropolitana', 'Valparaíso'],
            'pais': ['Chile', 'Chile'],
            'codigo_postal': ['7500000', '2340000'],
            'notas': ['Cliente potencial importante', 'Referido por socio comercial']
        }
        
        df = pd.DataFrame(datos_ejemplo)
        
        # Crear archivo Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Clientes')
            
            # Obtener la hoja de trabajo para formatear
            worksheet = writer.sheets['Clientes']
            
            # Ajustar el ancho de las columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        buffer.seek(0)
        
        # Crear respuesta HTTP con el archivo
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_clientes.xlsx"'
        
        return response

class TratoPlantillaExcelView(LoginRequiredMixin, TemplateView):
    """Vista para generar y descargar plantilla de Excel para tratos"""
    
    def get(self, request, *args, **kwargs):
        # Crear un DataFrame con las columnas y datos de ejemplo
        datos_ejemplo = {
            'nombre': ['Proyecto Implementación ERP', 'Desarrollo App Móvil'],
            'cliente': ['Ejemplo Empresa ABC', 'Cliente Muestra XYZ'],
            'valor': [150000, 85000],
            'estado': ['nuevo', 'cotizacion'],
            'fecha_cierre': ['2025-08-15', '2025-07-30'],
            'correo': ['proyecto@empresa.com', 'desarrollo@cliente.com'],
            'telefono': ['+56912345678', '+56987654321'],
            'descripcion': ['Implementación completa de sistema ERP', 'Desarrollo de aplicación móvil nativa'],
            'probabilidad': [75, 60],
            'fuente': ['referido', 'web'],
            'notas': ['Cliente con presupuesto aprobado', 'Proyecto urgente para Q3'],
            'centro_costos': ['CC001', 'CC002'],
            'nombre_proyecto': ['ERP-2025-001', 'APP-MOV-2025-002'],
            'orden_contrato': ['OC-2025-001', 'OC-2025-002'],
            'dias_prometidos': [90, 60],
            'tipo_negociacion': ['licitacion', 'cotizacion_directa']
        }
        
        df = pd.DataFrame(datos_ejemplo)
        
        # Crear archivo Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Tratos')
            
            # Obtener la hoja de trabajo para formatear
            worksheet = writer.sheets['Tratos']
            
            # Ajustar el ancho de las columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
                
            # Agregar una segunda hoja con información sobre los valores válidos
            info_data = {
                'Campo': ['estado', 'fuente', 'tipo_negociacion'],
                'Valores_Válidos': [
                    'nuevo, cotizacion, negociacion, ganado, perdido, cancelado',
                    'web, referido, telefono, email, redes_sociales, evento, otro',
                    'licitacion, cotizacion_directa, negociacion_abierta'
                ]
            }
            df_info = pd.DataFrame(info_data)
            df_info.to_excel(writer, index=False, sheet_name='Valores_Válidos')
        
        buffer.seek(0)
        
        # Crear respuesta HTTP con el archivo
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="plantilla_tratos.xlsx"'
        
        return response
