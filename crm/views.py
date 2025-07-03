from django import forms
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView, FormView, View
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum, Count, F, ProtectedError
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.db import transaction
from django.core.exceptions import ValidationError
import pandas as pd
import io
import logging
from datetime import datetime, timedelta
from .models import (
    Cliente, Contacto, Cotizacion, TareaVenta, Trato, 
    RepresentanteVentas, DocumentoCliente, VersionCotizacion, Lead,
    ConfiguracionOferta
)
from .forms import (
    CotizacionForm, VersionCotizacionForm, CotizacionConVersionForm, TratoForm
)
from .forms.import_forms import ClienteImportForm, TratoImportForm, ContactoImportForm

class CRMDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/dashboard.html'

    def get_queryset_filters(self, request):
        """Aplica los filtros al queryset de tratos"""
        today = timezone.now()
        
        # Obtener parámetros de filtro
        cliente_id = request.GET.get('cliente')
        comercial_id = request.GET.get('comercial')
        tipo_negociacion = request.GET.get('tipo_negociacion')
        periodo = request.GET.get('periodo', 'mes')
        trimestre = request.GET.get('trimestre')

        # Base queryset para tratos
        tratos_qs = Trato.objects.all()

        # Aplicar filtros solo si tienen valor
        if cliente_id and cliente_id != '':
            tratos_qs = tratos_qs.filter(cliente_id=cliente_id)
        if comercial_id and comercial_id != '':
            tratos_qs = tratos_qs.filter(responsable_id=comercial_id)
        if tipo_negociacion and tipo_negociacion != '':
            tratos_qs = tratos_qs.filter(tipo_negociacion=tipo_negociacion)

        # Filtrar por período
        año_actual = today.year
        
        if periodo == 'mes':
            # Filtrar por el mes actual
            primer_dia_mes = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            tratos_qs = tratos_qs.filter(fecha_creacion__gte=primer_dia_mes)
        elif periodo == 'trimestre' and trimestre and trimestre != '':
            # Filtrar por el trimestre seleccionado del año actual
            trimestres = {
                '1': (1, 3),   # Enero - Marzo
                '2': (4, 6),   # Abril - Junio
                '3': (7, 9),   # Julio - Septiembre
                '4': (10, 12), # Octubre - Diciembre
            }
            if trimestre in trimestres:
                mes_inicio, mes_fin = trimestres[trimestre]
                fecha_inicio = today.replace(year=año_actual, month=mes_inicio, day=1, hour=0, minute=0, second=0, microsecond=0)
                if mes_fin == 12:
                    fecha_fin = today.replace(year=año_actual, month=mes_fin, day=31, hour=23, minute=59, second=59, microsecond=999999)
                else:
                    fecha_fin = today.replace(year=año_actual, month=mes_fin + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(microseconds=1)
                tratos_qs = tratos_qs.filter(fecha_creacion__range=(fecha_inicio, fecha_fin))
        elif periodo == 'anio':
            # Filtrar por el año actual, pero si se especifica un trimestre, filtramos por ese trimestre
            primer_dia_año = today.replace(year=año_actual, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            ultimo_dia_año = today.replace(year=año_actual, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            
            if trimestre and trimestre in ['1', '2', '3', '4']:
                # Si se especificó un trimestre aunque el periodo sea 'anio', también filtramos por ese trimestre
                trimestres = {
                    '1': (1, 3),   # Enero - Marzo
                    '2': (4, 6),   # Abril - Junio
                    '3': (7, 9),   # Julio - Septiembre
                    '4': (10, 12), # Octubre - Diciembre
                }
                mes_inicio, mes_fin = trimestres[trimestre]
                fecha_inicio = today.replace(year=año_actual, month=mes_inicio, day=1, hour=0, minute=0, second=0, microsecond=0)
                if mes_fin == 12:
                    fecha_fin = today.replace(year=año_actual, month=mes_fin, day=31, hour=23, minute=59, second=59, microsecond=999999)
                else:
                    fecha_fin = today.replace(year=año_actual, month=mes_fin + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(microseconds=1)
                
                # Aplicamos el filtro de trimestre
                tratos_qs = tratos_qs.filter(fecha_creacion__range=(fecha_inicio, fecha_fin))
            else:
                # Si no se especificó trimestre, filtramos por todo el año
                tratos_qs = tratos_qs.filter(fecha_creacion__range=(primer_dia_año, ultimo_dia_año))
        elif periodo == 'todo':
            # No aplicar filtro de fecha, mostrar todos los registros
            pass
        
        # Debug para ver cuantos tratos y qué valores hay
        print(f"Filtros aplicados: periodo={periodo}, trimestre={trimestre}")
        print(f"Total tratos en queryset: {tratos_qs.count()}")
        ganados = tratos_qs.filter(estado='ganado')
        print(f"Tratos ganados: {ganados.count()}, Valor total ganado: {ganados.aggregate(total=Sum('valor'))['total'] or 0}")
        
        return tratos_qs

    def get_dashboard_data(self, request):
        """Obtiene los datos del dashboard según los filtros aplicados"""
        tratos_qs = self.get_queryset_filters(request)
        today = timezone.now()
        
        # Debug
        print(f"Filtros aplicados. Total tratos en queryset: {tratos_qs.count()}")
        
        # Calcular métricas
        total_ganado = tratos_qs.filter(estado='ganado').aggregate(total=Sum('valor'))['total'] or 0
        total_clientes = Cliente.objects.count()
        total_tratos = tratos_qs.count()
        tratos_abiertos = tratos_qs.exclude(estado__in=['ganado', 'perdido', 'cancelado']).count()
        valor_total_tratos = tratos_qs.aggregate(total=Sum('valor'))['total'] or 0
        
        # Tratos por estado (ahora calculando la suma del valor, no solo contando)
        tratos_por_estado = {}
        tratos_por_estado_count = {}  # Mantener también el conteo para referencias
        for estado_code, estado_name in Trato.ESTADO_CHOICES:
            # Obtener suma del valor de tratos en este estado
            valor_sum = tratos_qs.filter(estado=estado_code).aggregate(total=Sum('valor'))['total'] or 0
            count = tratos_qs.filter(estado=estado_code).count()
            tratos_por_estado[estado_code] = float(valor_sum)
            tratos_por_estado_count[estado_code] = count
            # Debug
            print(f"Estado: {estado_name} ({estado_code}): {count} tratos, valor: ${valor_sum}")
        
        # Tratos por fuente
        tratos_por_fuente = {}
        for fuente_code, fuente_name in Trato.FUENTE_CHOICES:
            count = tratos_qs.filter(fuente=fuente_code).count()
            tratos_por_fuente[fuente_name] = count
            # Debug
            print(f"Fuente: {fuente_name} ({fuente_code}): {count} tratos")
        
        # Últimos tratos
        ultimos_tratos = []
        for trato in tratos_qs.order_by('-fecha_creacion')[:5]:
            ultimos_tratos.append({
                'id': trato.id,
                'cliente': str(trato.cliente),
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
            'tratos_por_estado_count': tratos_por_estado_count,  # Incluimos también el conteo
            'tratos_por_fuente': tratos_por_fuente,
            'ultimos_tratos': ultimos_tratos,
            'tareas_atrasadas': tareas_atrasadas,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        
        # Obtener datos del dashboard con los filtros aplicados
        dashboard_data = self.get_dashboard_data(request)
        context.update(dashboard_data)
        
        # Agregar opciones para los filtros
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        context['comerciales'] = get_user_model().objects.filter(
            tratos__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        context['tipos_negociacion'] = Trato.TIPO_CHOICES
        
        # Mantener filtros seleccionados en el contexto
        context['filtros'] = {
            'cliente': request.GET.get('cliente', ''),
            'comercial': request.GET.get('comercial', ''),
            'tipo_negociacion': request.GET.get('tipo_negociacion', ''),
            'periodo': request.GET.get('periodo', 'mes'),
            'trimestre': request.GET.get('trimestre', '')
        }
        
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Si es una petición AJAX, devolver solo los datos necesarios en formato JSON
            # Filtrar solo los datos que son serializables a JSON
            json_data = {
                'total_ganado': context.get('total_ganado', 0),
                'total_clientes': context.get('total_clientes', 0),
                'total_tratos': context.get('total_tratos', 0),
                'tratos_abiertos': context.get('tratos_abiertos', 0),
                'valor_total_tratos': context.get('valor_total_tratos', 0),
                'tratos_por_estado': context.get('tratos_por_estado', {}),
                'tratos_por_fuente': context.get('tratos_por_fuente', {}),
                'ultimos_tratos': context.get('ultimos_tratos', []),
                'tareas_atrasadas': context.get('tareas_atrasadas', 0),
            }
            return JsonResponse(json_data, json_dumps_params={'ensure_ascii': False})
        return self.render_to_response(context)

# Vistas para Cliente
class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'crm/cliente/list.html'
    context_object_name = 'clientes'

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    template_name = 'crm/cliente/form.html'
    fields = ['nombre', 'sector_actividad', 'nit', 'correo', 'telefono', 'direccion', 
              'ciudad', 'estado', 'rut', 'cedula', 'ef', 'camara', 'formulario_vinculacion', 'notas']
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
    fields = ['nombre', 'sector_actividad', 'nit', 'correo', 'telefono', 'direccion', 
              'ciudad', 'estado', 'rut', 'cedula', 'ef', 'camara', 'formulario_vinculacion', 'notas']
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
        archivo_excel = form.cleaned_data['archivo_excel']
        import_id = str(timezone.now().timestamp()).replace('.', '')
        
        try:
            # Leer el archivo Excel para validación inicial
            df = pd.read_excel(archivo_excel)
            
            # Validar columnas requeridas
            required_columns = ['nombre']
            if not all(col in df.columns for col in required_columns):
                messages.error(self.request, f'El archivo Excel debe contener al menos la columna: {", ".join(required_columns)}')
                return self.form_invalid(form)
            
            # Limpiar datos: reemplazar NaN con cadenas vacías
            df = df.fillna('')
            
            total_rows = len(df)
            
            # Convertir a diccionario y limpiar cualquier valor NaN restante
            data_records = df.to_dict('records')
            
            # Limpiar datos para evitar problemas de serialización JSON
            cleaned_records = []
            for record in data_records:
                cleaned_record = {}
                for key, value in record.items():
                    # Convertir NaN, None, y otros valores problemáticos a cadena vacía
                    if pd.isna(value) or value is None:
                        cleaned_record[key] = ''
                    else:
                        cleaned_record[key] = str(value).strip()
                cleaned_records.append(cleaned_record)
            
            # Guardar datos en sesión
            self.request.session[f'import_{import_id}'] = {
                'status': 'ready',
                'total': total_rows,
                'processed': 0,
                'created': 0,
                'errors': [],
                'data': cleaned_records  # Guardar datos limpios para procesamiento
            }
            
            # Redirigir a la página de progreso
            return redirect(reverse('crm:cliente_import_progress', kwargs={'import_id': import_id}) + f'?file={archivo_excel.name}')
            
        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo Excel: {str(e)}')
            return self.form_invalid(form)

class ClienteImportProgressView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/cliente/import_progress.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_id'] = kwargs['import_id']
        context['filename'] = self.request.GET.get('file', 'archivo.xlsx')
        return context

class ClienteImportProcessView(LoginRequiredMixin, TemplateView):
    """Vista AJAX para iniciar el procesamiento de la importación"""
    
    def post(self, request, import_id):
        import_data = request.session.get(f'import_{import_id}')
        if not import_data:
            return JsonResponse({'error': 'Importación no encontrada'}, status=404)
        
        if import_data['status'] != 'ready':
            return JsonResponse({'error': 'La importación ya está en proceso o completada'}, status=400)
        
        # Marcar como en proceso
        import_data['status'] = 'processing'
        request.session[f'import_{import_id}'] = import_data
        request.session.modified = True
        
        try:
            data_rows = import_data['data']
            total_rows = len(data_rows)
            clientes_creados = 0
            errores = []
            batch_size = 5  # Procesar en lotes más pequeños para evitar timeouts
            
            # Procesar cada fila con manejo mejorado de errores
            for index, row in enumerate(data_rows):
                try:
                    # Validar datos básicos antes de crear
                    nombre = str(row.get('nombre', '')).strip()
                    if not nombre or nombre.lower() in ['nan', 'none', 'null']:
                        error_msg = f'Fila {index + 2}: El nombre del cliente es requerido'
                        errores.append(error_msg)
                        continue
                    
                    # Verificar si el cliente ya existe para evitar duplicados
                    if Cliente.objects.filter(nombre=nombre).exists():
                        error_msg = f'Fila {index + 2}: Cliente "{nombre}" ya existe'
                        errores.append(error_msg)
                        continue
                    
                    # Función helper para limpiar campos
                    def clean_field(value):
                        if value is None or pd.isna(value):
                            return ''
                        value_str = str(value).strip()
                        return '' if value_str.lower() in ['nan', 'none', 'null'] else value_str
                    
                    # Crear cliente con validación de campos
                    with transaction.atomic():
                        Cliente.objects.create(
                            nombre=nombre,
                            sector_actividad=clean_field(row.get('sector_actividad', '')),
                            nit=clean_field(row.get('nit', '')),
                            correo=clean_field(row.get('correo', '')),
                            telefono=clean_field(row.get('telefono', '')),
                            direccion=clean_field(row.get('direccion', '')),
                            ciudad=clean_field(row.get('ciudad', '')),
                            estado=clean_field(row.get('estado', '')),
                            notas=clean_field(row.get('notas', ''))
                        )
                    clientes_creados += 1
                    
                except Exception as e:
                    error_msg = f'Fila {index + 2}: Error al importar cliente {row.get("nombre", "desconocido")}: {str(e)}'
                    errores.append(error_msg)
                
                # Actualizar progreso cada lote o al final
                if (index + 1) % batch_size == 0 or index == total_rows - 1:
                    import_data.update({
                        'processed': index + 1,
                        'created': clientes_creados,
                        'errors': errores
                    })
                    request.session[f'import_{import_id}'] = import_data
                    request.session.modified = True
                    
                    # Forzar guardado de la sesión
                    request.session.save()
            
            # Marcar como completado
            import_data.update({
                'status': 'completed',
                'processed': total_rows,
                'created': clientes_creados,
                'errors': errores
            })
            request.session[f'import_{import_id}'] = import_data
            request.session.modified = True
            request.session.save()
            
            return JsonResponse({
                'status': 'completed',
                'total': total_rows,
                'created': clientes_creados,
                'errors': len(errores)
            })
            
        except Exception as e:
            import_data.update({
                'status': 'error',
                'error': str(e)
            })
            request.session[f'import_{import_id}'] = import_data
            request.session.modified = True
            request.session.save()
            return JsonResponse({'error': str(e)}, status=500)

class ClienteImportStatusView(LoginRequiredMixin, TemplateView):
    """Vista AJAX para obtener el estado actual de la importación"""
    
    def get(self, request, import_id):
        import_data = request.session.get(f'import_{import_id}')
        if not import_data:
            return JsonResponse({'error': 'Importación no encontrada'}, status=404)
        
        return JsonResponse(import_data)

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
    model = VersionCotizacion
    template_name = 'crm/oferta/list.html'
    context_object_name = 'version_list'
    title = 'Lista de Ofertas'
    add_url = 'crm:cotizacion_create'
    
    def get_queryset(self):
        return VersionCotizacion.objects.select_related(
            'cotizacion__cliente', 
            'cotizacion__trato',
            'creado_por'
        ).order_by('-fecha_creacion')
        
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
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        trato_id = self.request.GET.get('trato')
        if trato_id:
            try:
                trato = Trato.objects.get(id=trato_id)
                kwargs['initial_cliente'] = trato.cliente
                kwargs['initial_trato'] = trato
            except Trato.DoesNotExist:
                pass
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        trato_id = self.request.GET.get('trato')
        if trato_id:
            try:
                trato = Trato.objects.get(id=trato_id)
                initial['trato'] = trato
                initial['cliente'] = trato.cliente
                initial['valor'] = trato.valor  # Pre-fill the value as well
            except Trato.DoesNotExist:
                pass
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trato_id = self.request.GET.get('trato')
        if trato_id:
            try:
                trato = Trato.objects.get(id=trato_id)
                context['trato_inicial'] = trato
                context['cliente_inicial'] = trato.cliente
            except Trato.DoesNotExist:
                pass
        return context

    def get_success_url(self):
        trato_id = self.request.GET.get('trato') or self.request.POST.get('trato_id')
        if trato_id:
            return reverse('crm:trato_detail', kwargs={'pk': trato_id})
        return self.success_url

    def form_valid(self, form):
        # Verificar que se haya proporcionado al menos un archivo
        archivos = self.request.FILES.getlist('archivos')
        
        if not archivos:
            form.add_error(None, 'Debe proporcionar al menos un archivo para la cotización.')
            return self.form_invalid(form)
        
        with transaction.atomic():
            # Asignar el valor del monto desde el campo valor del formulario
            cotizacion = form.save(commit=False)
            cotizacion.monto = form.cleaned_data['valor']
            cotizacion.save()
            
            # Obtener el número de la próxima versión basada en el trato
            if cotizacion.trato:
                # Buscar la última versión para este trato
                ultima_version = VersionCotizacion.objects.filter(
                    cotizacion__trato=cotizacion.trato
                ).order_by('-version').first()
                siguiente_version = 1 if not ultima_version else ultima_version.version + 1
            else:
                # Si no hay trato asociado, usar versiones de esta cotización
                siguiente_version = 1
            
            # Crear versiones para cada archivo subido
            for i, archivo in enumerate(archivos):
                VersionCotizacion.objects.create(
                    cotizacion=cotizacion,
                    version=siguiente_version + i,
                    archivo=archivo,
                    razon_cambio=form.cleaned_data['razon_cambio'],
                    valor=form.cleaned_data['valor'],
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

    def get_initial(self):
        initial = super().get_initial()
        if self.object:
            initial['valor'] = self.object.monto
        return initial

    def form_valid(self, form):
        with transaction.atomic():
            cotizacion = form.save(commit=False)
            cotizacion.monto = form.cleaned_data['valor']
            cotizacion.save()
            
            # Manejar archivos subidos (solo si hay archivos nuevos)
            archivos = self.request.FILES.getlist('archivos')
            
            if archivos:
                # Obtener el número de la próxima versión basada en el trato
                if cotizacion.trato:
                    # Buscar la última versión para este trato
                    ultima_version = VersionCotizacion.objects.filter(
                        cotizacion__trato=cotizacion.trato
                    ).order_by('-version').first()
                    siguiente_version = 1 if not ultima_version else ultima_version.version + 1
                else:
                    # Si no hay trato asociado, usar versiones de esta cotización
                    ultima_version = VersionCotizacion.objects.filter(
                        cotizacion=cotizacion
                    ).order_by('-version').first()
                    siguiente_version = 1 if not ultima_version else ultima_version.version + 1
                
                # Crear nuevas versiones para cada archivo
                for i, archivo in enumerate(archivos):
                    VersionCotizacion.objects.create(
                        cotizacion=cotizacion,
                        version=siguiente_version + i,
                        archivo=archivo,
                        razon_cambio=form.cleaned_data.get('razon_cambio', ''),
                        valor=form.cleaned_data['valor'],
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
        
        # Filtros existentes
        cliente_id = self.request.GET.get('cliente')
        trato_id = self.request.GET.get('trato')
        responsable_id = self.request.GET.get('responsable')
        numero_oferta = self.request.GET.get('numero_oferta')
        
        # Nuevos filtros
        tipo = self.request.GET.get('tipo')
        estado = self.request.GET.get('estado')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        if trato_id:
            queryset = queryset.filter(trato_id=trato_id)
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)
        if numero_oferta:
            queryset = queryset.filter(trato__numero_oferta__icontains=numero_oferta)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if estado:
            queryset = queryset.filter(estado=estado)
        if fecha_desde:
            queryset = queryset.filter(fecha_vencimiento__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha_vencimiento__lte=fecha_hasta)
            
        return queryset.order_by('-fecha_vencimiento')
        
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
        
        # Agregar opciones para los filtros
        context['tipos_tarea'] = TareaVenta.TIPO_CHOICES
        context['estados_tarea'] = TareaVenta.ESTADO_CHOICES
        
        # Mantener los filtros seleccionados (existentes)
        context['selected_cliente'] = self.request.GET.get('cliente')
        context['selected_trato'] = self.request.GET.get('trato')
        context['selected_responsable'] = self.request.GET.get('responsable')
        context['selected_numero_oferta'] = self.request.GET.get('numero_oferta')
        
        # Mantener los filtros seleccionados
        context['selected_tipo'] = self.request.GET.get('tipo')
        context['selected_estado'] = self.request.GET.get('estado')
        context['selected_fecha_desde'] = self.request.GET.get('fecha_desde')
        context['selected_fecha_hasta'] = self.request.GET.get('fecha_hasta')
        
        return context

class TareaVentaCreateView(LoginRequiredMixin, CreateView):
    model = TareaVenta
    template_name = 'crm/tarea/form.html'
    fields = ['titulo', 'cliente', 'trato', 'tipo', 'descripcion', 'fecha_vencimiento', 
              'estado', 'responsable', 'notas', 'fecha_ejecucion']
    success_url = reverse_lazy('crm:tarea_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Configurar campos de fecha con widgets mejorados
        form.fields['fecha_vencimiento'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_vencimiento'].input_formats = ['%Y-%m-%dT%H:%M']
        
        form.fields['fecha_ejecucion'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_ejecucion'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Configurar ayuda para los campos
        form.fields['titulo'].help_text = 'Título descriptivo para la tarea'
        form.fields['descripcion'].help_text = 'Descripción detallada de la tarea a realizar'
        form.fields['fecha_vencimiento'].help_text = 'Fecha y hora límite para completar la tarea'
        form.fields['fecha_ejecucion'].help_text = 'Fecha y hora real de ejecución (opcional)'
        form.fields['notas'].help_text = 'Notas adicionales o comentarios sobre la tarea'
        
        # Cambiar label del campo trato
        form.fields['trato'].label = 'Proyecto'
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Tarea creada exitosamente.')
        return super().form_valid(form)

class TareaVentaDetailView(LoginRequiredMixin, DetailView):
    model = TareaVenta
    template_name = 'crm/tarea/detail.html'
    context_object_name = 'tarea'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Si la tarea está asociada a un trato, verificar si hay un proyecto relacionado
        if self.object.trato:
            try:
                # Intentar importar el modelo Proyecto solo si está disponible
                from proyectos.models import Proyecto
                proyecto = Proyecto.objects.filter(trato=self.object.trato).first()
                context['proyecto_relacionado'] = proyecto
            except ImportError:
                # El módulo proyectos no está disponible
                pass
        
        return context

class TareaVentaUpdateView(LoginRequiredMixin, UpdateView):
    model = TareaVenta
    template_name = 'crm/tarea/form.html'
    fields = ['titulo', 'cliente', 'trato', 'tipo', 'descripcion', 'fecha_vencimiento', 
              'estado', 'responsable', 'notas', 'fecha_ejecucion']
    success_url = reverse_lazy('crm:tarea_list')
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Configurar campos de fecha con widgets mejorados
        form.fields['fecha_vencimiento'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_vencimiento'].input_formats = ['%Y-%m-%dT%H:%M']
        
        form.fields['fecha_ejecucion'].widget = forms.DateTimeInput(
            attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            },
            format='%Y-%m-%dT%H:%M'
        )
        form.fields['fecha_ejecucion'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Configurar ayuda para los campos
        form.fields['titulo'].help_text = 'Título descriptivo para la tarea'
        form.fields['descripcion'].help_text = 'Descripción detallada de la tarea a realizar'
        form.fields['fecha_vencimiento'].help_text = 'Fecha y hora límite para completar la tarea'
        form.fields['fecha_ejecucion'].help_text = 'Fecha y hora real de ejecución (opcional)'
        form.fields['notas'].help_text = 'Notas adicionales o comentarios sobre la tarea'
        
        # Cambiar label del campo trato
        form.fields['trato'].label = 'Proyecto'
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Tarea actualizada exitosamente.')
        return super().form_valid(form)

# Vistas para Trato
class TratoListView(LoginRequiredMixin, ListView):
    model = Trato
    template_name = 'crm/trato/list.html'
    context_object_name = 'tratos'
    title = 'Lista de ProyectosCRM'
    add_url = 'crm:trato_create'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('responsable', 'cliente').order_by('-numero_oferta')
        
        # Filtro de búsqueda general
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(numero_oferta__icontains=search_query) |
                Q(cliente__nombre__icontains=search_query) |
                Q(descripcion__icontains=search_query) |
                Q(responsable__username__icontains=search_query) |
                Q(responsable__first_name__icontains=search_query) |
                Q(responsable__last_name__icontains=search_query) |
                Q(nombre__icontains=search_query)
            )
        
        # Filtros específicos
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
        
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        responsable_id = self.request.GET.get('responsable')
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)
        
        fuente = self.request.GET.get('fuente')
        if fuente:
            queryset = queryset.filter(fuente=fuente)
        
        tipo_negociacion = self.request.GET.get('tipo_negociacion')
        if tipo_negociacion:
            queryset = queryset.filter(tipo_negociacion=tipo_negociacion)
        
        # Filtro por rango de probabilidad
        probabilidad_min = self.request.GET.get('probabilidad_min')
        if probabilidad_min:
            try:
                queryset = queryset.filter(probabilidad__gte=int(probabilidad_min))
            except ValueError:
                pass
        
        probabilidad_max = self.request.GET.get('probabilidad_max')
        if probabilidad_max:
            try:
                queryset = queryset.filter(probabilidad__lte=int(probabilidad_max))
            except ValueError:
                pass
        
        # Filtro por rango de valor
        valor_min = self.request.GET.get('valor_min')
        if valor_min:
            try:
                queryset = queryset.filter(valor__gte=float(valor_min))
            except ValueError:
                pass
        
        valor_max = self.request.GET.get('valor_max')
        if valor_max:
            try:
                queryset = queryset.filter(valor__lte=float(valor_max))
            except ValueError:
                pass
        
        # Filtro por fecha de cierre
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            try:
                queryset = queryset.filter(fecha_cierre__gte=fecha_desde)
            except ValueError:
                pass
        
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            try:
                queryset = queryset.filter(fecha_cierre__lte=fecha_hasta)
            except ValueError:
                pass
        
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['add_url'] = reverse_lazy(self.add_url)
        
        # Agregar contador de ofertas (usando el queryset filtrado)
        context['total_ofertas'] = self.get_queryset().count()
        
        # Agregar opciones para filtros
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        context['responsables'] = get_user_model().objects.filter(
            tratos__isnull=False
        ).distinct().order_by('first_name', 'last_name')
        context['estados'] = Trato.ESTADO_CHOICES
        context['fuentes'] = Trato.FUENTE_CHOICES
        context['tipos_negociacion'] = Trato.TIPO_CHOICES
        
        # Mantener filtros seleccionados
        context['filtros'] = {
            'q': self.request.GET.get('q', ''),
            'cliente': self.request.GET.get('cliente', ''),
            'estado': self.request.GET.get('estado', ''),
            'responsable': self.request.GET.get('responsable', ''),
            'fuente': self.request.GET.get('fuente', ''),
            'tipo_negociacion': self.request.GET.get('tipo_negociacion', ''),
            'probabilidad_min': self.request.GET.get('probabilidad_min', ''),
            'probabilidad_max': self.request.GET.get('probabilidad_max', ''),
            'valor_min': self.request.GET.get('valor_min', ''),
            'valor_max': self.request.GET.get('valor_max', ''),
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
        }
        
        return context

class TratoBulkDeleteView(LoginRequiredMixin, View):
    """Vista para eliminar múltiples tratos de forma masiva"""
    
    def post(self, request, *args, **kwargs):
        selected_ids = request.POST.getlist('selected_ids')
        
        if not selected_ids:
            messages.error(request, 'No se seleccionaron ofertas para eliminar.')
            return redirect('crm:trato_list')
        
        try:
            # Buscar los tratos que pertenecen al usuario o que el usuario puede ver
            tratos_to_delete = Trato.objects.filter(id__in=selected_ids)
            
            if not tratos_to_delete.exists():
                messages.error(request, 'No se encontraron ofertas válidas para eliminar.')
                return redirect('crm:trato_list')
            
            # Get info before deletion for logging
            tratos_info = []
            for trato in tratos_to_delete:
                tratos_info.append(f"#{trato.numero_oferta} - {trato.cliente}")
            
            deleted_count = tratos_to_delete.count()
            tratos_to_delete.delete()
            
            # Log the bulk deletion
            logger = logging.getLogger(__name__)
            logger.info(f"Eliminación masiva de tratos por usuario {request.user.username}. "
                       f"Cantidad: {deleted_count}. Tratos: {', '.join(tratos_info[:10])}")
            
            messages.success(
                request, 
                f'Se eliminaron exitosamente {deleted_count} oferta{"s" if deleted_count != 1 else ""}.'
            )
            
        except Exception as e:
            messages.error(request, f'Error al eliminar las ofertas: {str(e)}')
            logger = logging.getLogger(__name__)
            logger.error(f"Error en eliminación masiva de tratos: {str(e)}")
        
        return redirect('crm:trato_list')

class TratoCreateView(LoginRequiredMixin, CreateView):
    model = Trato
    form_class = TratoForm
    template_name = 'crm/trato/form.html'
    success_url = reverse_lazy('crm:trato_list')
    
    def form_valid(self, form):
        try:
            form.instance.creado_por = self.request.user
            response = super().form_valid(form)
            
            # Si se marca como ganado y se crea un proyecto, mostrar mensaje de éxito
            if form.instance.estado == 'ganado' and hasattr(form.instance, 'proyecto'):
                messages.success(
                    self.request, 
                    f'Trato creado como ganado exitosamente. '
                    f'Se ha creado automáticamente el proyecto: {form.instance.proyecto.nombre_proyecto}'
                )
            else:
                messages.success(self.request, 'Trato creado exitosamente.')
            
            return response
            
        except ValidationError as e:
            # Check if the error is about duplicate offer number
            error_message = str(e)
            if 'número de oferta' in error_message and 'ya existe' in error_message:
                form.add_error('numero_oferta', error_message)
                messages.error(self.request, error_message)
            else:
                # Handle other validation errors (like centro_costos)
                form.add_error('centro_costos', str(e))
                messages.error(
                    self.request, 
                    'No se puede crear el trato como "Ganado" sin especificar el Centro de Costos. '
                    'Este campo es obligatorio para crear el proyecto automáticamente.'
                )
            return self.form_invalid(form)
        except Exception as e:
            # Manejar otros errores inesperados
            messages.error(
                self.request, 
                f'Error al crear el trato: {str(e)}'
            )
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context['title'] = 'Nuevo ProyectoCRM'
        context['clientes'] = Cliente.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        return context

class TratoQuickCreateView(LoginRequiredMixin, CreateView):
    model = Trato
    template_name = 'crm/trato/quick_create.html'
    fields = ['cliente', 'descripcion', 'fuente', 'contacto']
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Hacer que descripción sea requerida
        form.fields['descripcion'].required = True
        form.fields['cliente'].required = True
        
        # Personalizar widgets
        form.fields['descripcion'].widget = forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Describe brevemente el proyecto o servicio...'
        })
        form.fields['cliente'].widget.attrs.update({'class': 'form-select'})
        form.fields['fuente'].widget.attrs.update({'class': 'form-select'})
        form.fields['contacto'].widget.attrs.update({'class': 'form-select'})
        
        return form
    
    def form_valid(self, form):
        # Establecer valores por defecto para campos requeridos
        form.instance.estado = 'revision_tecnica'  # Estado inicial
        form.instance.probabilidad = 50  # Probabilidad por defecto
        form.instance.valor = 0  # Valor inicial
        form.instance.responsable = self.request.user
        
        # Determinar la acción del botón presionado
        action = self.request.POST.get('action', 'quick')
        
        try:
            response = super().form_valid(form)
            
            if action == 'complete':
                # Redirigir al formulario completo para editar
                messages.success(
                    self.request,
                    'Trato creado exitosamente. Completa la información adicional.'
                )
                return redirect('crm:trato_update', pk=self.object.pk)
            else:
                # Creación rápida completada
                messages.success(
                    self.request,
                    f'Trato #{self.object.numero_oferta} creado exitosamente. '
                    f'Puedes completar la información adicional desde el detalle del trato.'
                )
                return redirect('crm:trato_detail', pk=self.object.pk)
                
        except Exception as e:
            messages.error(
                self.request,
                f'Error al crear el trato: {str(e)}'
            )
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('crm:trato_detail', kwargs={'pk': self.object.pk})

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
    form_class = TratoForm
    template_name = 'crm/trato/form.html'
    success_url = reverse_lazy('crm:trato_list')
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            
            # Si se marca como ganado y se crea un proyecto, mostrar mensaje de éxito
            if form.instance.estado == 'ganado' and hasattr(form.instance, 'proyecto'):
                messages.success(
                    self.request, 
                    f'Trato marcado como ganado exitosamente. '
                    f'Se ha creado automáticamente el proyecto: {form.instance.proyecto.nombre_proyecto}'
                )
            else:
                messages.success(self.request, 'Trato actualizado exitosamente.')
            
            return response
            
        except ValidationError as e:
            # Check if the error is about duplicate offer number
            error_message = str(e)
            if 'número de oferta' in error_message and 'ya existe' in error_message:
                form.add_error('numero_oferta', error_message)
                messages.error(self.request, error_message)
            else:
                # Handle other validation errors (like centro_costos)
                form.add_error('centro_costos', str(e))
                messages.error(
                    self.request, 
                    'No se puede marcar el trato como "Ganado" sin especificar el Centro de Costos. '
                    'Este campo es obligatorio para crear el proyecto automáticamente.'
                )
            return self.form_invalid(form)
        except Exception as e:
            # Manejar otros errores inesperados
            messages.error(
                self.request, 
                f'Error al actualizar el trato: {str(e)}'
            )
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context['title'] = f'Editar ProyectoCRM: {self.object.nombre}'
        context['clientes'] = Cliente.objects.all()
        context['users'] = User.objects.filter(is_active=True)
        context['tareas'] = TareaVenta.objects.filter(trato=self.object).order_by('-fecha_vencimiento')
        return context

class TratoImportView(LoginRequiredMixin, FormView):
    template_name = 'crm/trato/import.html'
    form_class = TratoImportForm
    success_url = reverse_lazy('crm:trato_list')
    
    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        
        # Initialize import statistics
        import_stats = {
            'total_rows': 0,
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }
        
        try:
            archivo_excel = form.cleaned_data['archivo_excel']
            logger.info(f"Iniciando procesamiento de archivo: {archivo_excel.name}")
            
            # Leer el archivo Excel con manejo de errores mejorado
            try:
                # Intentar con openpyxl primero
                df = pd.read_excel(archivo_excel, engine='openpyxl')
                import_stats['total_rows'] = len(df)
                logger.info(f"Archivo Excel leído exitosamente con openpyxl. Filas: {import_stats['total_rows']}")
            except Exception as excel_error:
                logger.warning(f"Error con openpyxl: {str(excel_error)}")
                try:
                    # Fallback a xlrd para archivos .xls antiguos
                    # Reset file pointer
                    archivo_excel.seek(0)
                    df = pd.read_excel(archivo_excel, engine=None)
                    import_stats['total_rows'] = len(df)
                    logger.info(f"Archivo Excel leído exitosamente con engine por defecto. Filas: {import_stats['total_rows']}")
                except Exception as final_error:
                    error_msg = f"Error al leer archivo Excel (intentado con múltiples engines): {str(final_error)}"
                    logger.error(error_msg)
                    messages.error(self.request, f"Error al leer archivo Excel. Asegúrese de que sea un archivo .xlsx válido. Error: {str(final_error)}")
                    return self.form_invalid(form)
            
            # Validar que el archivo no esté vacío
            if df.empty or len(df) == 0:
                error_msg = "El archivo Excel está vacío o no contiene datos válidos."
                logger.error(error_msg)
                messages.error(self.request, error_msg)
                return self.form_invalid(form)
            
            logger.info(f"Iniciando importación de tratos. Usuario: {self.request.user.username}, Archivo: {archivo_excel.name}, Total filas: {import_stats['total_rows']}")
            
            # Validar las columnas requeridas
            required_columns = ['nombre', 'cliente', 'valor', 'estado', 'fecha_cierre']
            df_columns = [col.lower().strip() for col in df.columns]
            missing_columns = []
            
            for req_col in required_columns:
                if req_col.lower() not in df_columns:
                    missing_columns.append(req_col)
            
            if missing_columns:
                error_msg = f'El archivo Excel debe contener las columnas: {", ".join(missing_columns)}. Columnas encontradas: {", ".join(df.columns)}'
                logger.error(f"Error de validación de columnas: {error_msg}")
                messages.error(self.request, error_msg)
                return self.form_invalid(form)
            
            # Limpiar datos: reemplazar NaN con valores por defecto
            df = df.fillna({
                'numero_oferta': '',
                'correo': '',
                'telefono': '',
                'descripcion': '',
                'probabilidad': 50,
                'fuente': 'visita',
                'notas': '',
                'centro_costos': '',
                'nombre_proyecto': '',
                'orden_contrato': '',
                'dias_prometidos': 0,
                'tipo_negociacion': 'contrato',
                'contacto': ''
            })
            
            # Limitar a 500 filas por proceso para evitar timeouts
            max_rows = min(len(df), 500)
            if len(df) > 500:
                logger.warning(f"Archivo tiene {len(df)} filas. Procesando solo las primeras 500 para evitar timeouts.")
                messages.warning(self.request, f"Archivo tiene {len(df)} filas. Procesando solo las primeras 500 por seguridad.")
            
            # BULK IMPORT OPTIMIZATION - Preload all clients once at the beginning
            logger.info("Preloading clients for bulk import optimization...")
            all_clientes = {cliente.nombre: cliente for cliente in Cliente.objects.all()}
            # Also create a case-insensitive lookup dictionary for fallback
            all_clientes_lower = {nombre.lower(): cliente for nombre, cliente in all_clientes.items()}
            logger.info(f"Preloaded {len(all_clientes)} clients for import")
            
            # Process all rows and prepare Trato objects (without saving)
            tratos_to_create = []
            batch_size = 50  # Process in batches to avoid memory issues
            
            # Helper functions for data cleaning (same as original)
            def clean_numeric_field(value, default=0):
                if pd.isna(value) or value is None or value == '':
                    return default
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    return default

            def clean_text_field(value, default=''):
                if pd.isna(value) or value is None:
                    return default
                return str(value).strip()

            def clean_date_field(value):
                if pd.isna(value) or value is None or value == '':
                    return None
                try:
                    if hasattr(value, 'date'):
                        return value.date()
                    if isinstance(value, str):
                        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
                        for fmt in date_formats:
                            try:
                                return datetime.strptime(value.strip(), fmt).date()
                            except ValueError:
                                continue
                    return None
                except Exception:
                    return None
            
            # Process each row and prepare objects for bulk creation
            for index, row in df.head(max_rows).iterrows():
                try:
                    logger.debug(f"Processing row {index + 1} for bulk creation")
                    
                    # Find client using preloaded data
                    cliente_nombre = str(row['cliente']).strip() if pd.notna(row['cliente']) else ''
                    if not cliente_nombre:
                        warning_msg = f'Nombre de cliente vacío en fila {index + 1}. Se omitirá este trato.'
                        import_stats['skipped'] += 1
                        import_stats['error_details'].append(warning_msg)
                        continue
                    
                    # Clean client name to avoid encoding issues
                    cliente_nombre = cliente_nombre.encode('utf-8', errors='ignore').decode('utf-8')
                    
                    # Find client using preloaded dictionary (much faster than DB queries)
                    cliente = all_clientes.get(cliente_nombre)
                    if not cliente:
                        # Try case-insensitive lookup as fallback
                        cliente = all_clientes_lower.get(cliente_nombre.lower())
                    
                    if not cliente:
                        warning_msg = f'Cliente no encontrado: "{cliente_nombre}". Se omitirá este trato.'
                        import_stats['skipped'] += 1
                        import_stats['error_details'].append(f"Fila {index + 1}: {warning_msg}")
                        continue
                    
                    # Validate required fields
                    nombre = clean_text_field(row['nombre'])
                    if not nombre:
                        error_msg = f'Fila {index + 1}: El campo "nombre" es requerido'
                        import_stats['errors'] += 1
                        import_stats['error_details'].append(error_msg)
                        continue
                    
                    # Handle fecha_cierre
                    fecha_cierre = clean_date_field(row.get('fecha_cierre'))
                    if not fecha_cierre:
                        fecha_cierre = (timezone.now() + timedelta(days=30)).date()
                    
                    # Handle numero_oferta
                    numero_oferta = clean_text_field(row.get('numero_oferta', ''))
                    
                    # Handle contacto field - temporarily disabled
                    contacto = None
                    
                    # Create Trato object (not saved yet)
                    trato = Trato(
                        nombre=nombre,
                        cliente=cliente,
                        contacto=contacto,
                        correo=clean_text_field(row.get('correo', '')),
                        telefono=clean_text_field(row.get('telefono', '')),
                        descripcion=clean_text_field(row.get('descripcion', '')),
                        valor=clean_numeric_field(row['valor'], 0),
                        probabilidad=clean_numeric_field(row.get('probabilidad', 50), 50),
                        estado=clean_text_field(row['estado'], 'revision_tecnica'),
                        fuente=clean_text_field(row.get('fuente', 'visita'), 'visita'),
                        fecha_cierre=fecha_cierre,
                        responsable=self.request.user,
                        notas=clean_text_field(row.get('notas', '')),
                        centro_costos=clean_text_field(row.get('centro_costos', '')),
                        nombre_proyecto=clean_text_field(row.get('nombre_proyecto', '')),
                        orden_contrato=clean_text_field(row.get('orden_contrato', '')),
                        dias_prometidos=clean_numeric_field(row.get('dias_prometidos', 0), 0),
                        tipo_negociacion=clean_text_field(row.get('tipo_negociacion', 'contrato'), 'contrato')
                    )
                    
                    # Only add numero_oferta if provided
                    if numero_oferta:
                        trato.numero_oferta = numero_oferta
                    
                    tratos_to_create.append(trato)
                    
                except Exception as e:
                    error_msg = f'Error al procesar trato en fila {index + 1}: {str(e)}'
                    logger.error(error_msg)
                    import_stats['errors'] += 1
                    import_stats['error_details'].append(error_msg)
                    continue
            
            # Bulk create all prepared tratos
            if tratos_to_create:
                logger.info(f"Creating {len(tratos_to_create)} tratos using bulk_create...")
                
                try:
                    with transaction.atomic():
                        # For tratos without numero_oferta, we need individual saves for auto-assignment
                        tratos_with_numero = [t for t in tratos_to_create if hasattr(t, 'numero_oferta') and t.numero_oferta]
                        tratos_without_numero = [t for t in tratos_to_create if not (hasattr(t, 'numero_oferta') and t.numero_oferta)]
                        
                        # Bulk create tratos with numero_oferta
                        if tratos_with_numero:
                            created_count = len(Trato.objects.bulk_create(tratos_with_numero, ignore_conflicts=True))
                            import_stats['created'] += created_count
                            logger.info(f"Bulk created {created_count} tratos with numero_oferta")
                        
                        # Individual create for tratos needing auto numero_oferta
                        for trato in tratos_without_numero:
                            try:
                                trato.save()
                                import_stats['created'] += 1
                            except Exception as e:
                                error_msg = f'Error creating trato {trato.nombre}: {str(e)}'
                                logger.error(error_msg)
                                import_stats['errors'] += 1
                                import_stats['error_details'].append(error_msg)
                        
                        logger.info(f"Bulk creation completed: {import_stats['created']} tratos created total")
                        
                except Exception as e:
                    error_msg = f'Error in bulk creation: {str(e)}'
                    logger.error(error_msg)
                    import_stats['errors'] += len(tratos_to_create)
                    import_stats['error_details'].append(error_msg)
            else:
                logger.warning("No valid tratos to create")            # Log final import statistics
            logger.info(f"Importación completada. Estadísticas: {import_stats}")
            
            # Create detailed success message
            success_message = f'Importación completada: {import_stats["created"]} tratos creados'
            if import_stats['skipped'] > 0:
                success_message += f', {import_stats["skipped"]} omitidos'
            if import_stats['errors'] > 0:
                success_message += f', {import_stats["errors"]} errores'
            success_message += f' de {import_stats["total_rows"]} filas procesadas.'
            
            messages.success(self.request, success_message)
            
            # Add detailed error information if there were any issues
            if import_stats['error_details']:
                error_summary = "Detalles de errores:\n" + "\n".join(import_stats['error_details'][:10])  # Show first 10 errors
                if len(import_stats['error_details']) > 10:
                    error_summary += f"\n... y {len(import_stats['error_details']) - 10} errores más."
                messages.info(self.request, error_summary)
            
            return super().form_valid(form)
            
        except Exception as e:
            error_msg = f'Error al procesar el archivo Excel: {str(e)}'
            logger.error(f"Error crítico en importación: {error_msg}")
            messages.error(self.request, error_msg)
            return self.form_invalid(form)

class ContactoListView(LoginRequiredMixin, ListView):
    model = Contacto
    template_name = 'crm/contacto/list.html'
    context_object_name = 'contactos'
    title = 'Lista de Contactos'
    add_url = 'crm:contacto_create'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente')
        
        # Filtro de búsqueda
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(cliente__nombre__icontains=search_query) |
                Q(correo__icontains=search_query) |
                Q(cargo__icontains=search_query)
            )
        
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
            
        return queryset.order_by('cliente__nombre', 'nombre')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        context['add_url'] = self.add_url
        
        # Agregar clientes para filtro
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        context['selected_cliente'] = self.request.GET.get('cliente')
        context['search_query'] = self.request.GET.get('q', '')
        
        return context

class ContactoCreateView(LoginRequiredMixin, CreateView):
    model = Contacto
    template_name = 'crm/contacto/form.html'
    fields = ['cliente', 'nombre', 'cargo', 'correo', 'telefono', 'notas']
    success_url = reverse_lazy('crm:contacto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nuevo Contacto'
        return context

class ContactoCreateFromClientView(LoginRequiredMixin, CreateView):
    model = Contacto
    fields = ['nombre', 'cargo', 'correo', 'telefono', 'notas']
    
    def form_valid(self, form):
        cliente = get_object_or_404(Cliente, pk=self.kwargs['cliente_id'])
        form.instance.cliente = cliente
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('crm:cliente_detail', kwargs={'pk': self.kwargs['cliente_id']})

class ContactoDetailView(LoginRequiredMixin, DetailView):
    model = Contacto
    template_name = 'crm/contacto/detail.html'
    context_object_name = 'contacto'

class ContactoUpdateView(LoginRequiredMixin, UpdateView):
    model = Contacto
    template_name = 'crm/contacto/form.html'
    fields = ['cliente', 'nombre', 'cargo', 'correo', 'telefono', 'notas']
    success_url = reverse_lazy('crm:contacto_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar Contacto: {self.object.nombre}'
        return context

class ContactoImportView(LoginRequiredMixin, FormView):
    template_name = 'crm/contacto/import.html'
    form_class = ContactoImportForm
    success_url = reverse_lazy('crm:contacto_list')
    
    def form_valid(self, form):
        archivo_excel = form.cleaned_data['archivo_excel']
        import_id = str(timezone.now().timestamp()).replace('.', '')
        
        try:
            # Leer el archivo Excel para validación inicial
            df = pd.read_excel(archivo_excel)
            
            # Validar columnas requeridas
            required_columns = ['nombre', 'cliente', 'cargo']
            if not all(col in df.columns for col in required_columns):
                messages.error(self.request, f'El archivo Excel debe contener al menos las columnas: {", ".join(required_columns)}')
                return self.form_invalid(form)
            
            # Limpiar datos: reemplazar NaN con cadenas vacías
            df = df.fillna('')
            
            total_rows = len(df)
            
            # Convertir a diccionario y limpiar cualquier valor NaN restante
            data_records = df.to_dict('records')
            
            # Limpiar datos para evitar problemas de serialización JSON
            cleaned_records = []
            for record in data_records:
                cleaned_record = {}
                for key, value in record.items():
                    # Convertir NaN, None, y otros valores problemáticos a cadena vacía
                    if pd.isna(value) or value is None:
                        cleaned_record[key] = ''
                    else:
                        cleaned_record[key] = str(value).strip()
                cleaned_records.append(cleaned_record)
            
            # Guardar datos en sesión
            self.request.session[f'import_contacto_{import_id}'] = {
                'status': 'ready',
                'total': total_rows,
                'processed': 0,
                'created': 0,
                'errors': [],
                'data': cleaned_records  # Guardar datos limpios para procesamiento
            }
            
            # Redirigir a la página de progreso
            return redirect(reverse('crm:contacto_import_progress', kwargs={'import_id': import_id}) + f'?file={archivo_excel.name}')
            
        except Exception as e:
            messages.error(self.request, f'Error al procesar el archivo Excel: {str(e)}')
            return self.form_invalid(form)

class ContactoImportProgressView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/contacto/import_progress.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_id'] = kwargs['import_id']
        context['filename'] = self.request.GET.get('file', 'archivo.xlsx')
        return context

class ContactoImportProcessView(LoginRequiredMixin, TemplateView):
    """Vista AJAX para iniciar el procesamiento de la importación de contactos"""
    
    def post(self, request, import_id):
        import_data = request.session.get(f'import_contacto_{import_id}')
        if not import_data:
            return JsonResponse({'error': 'Importación no encontrada'}, status=404)
        
        if import_data['status'] != 'ready':
            return JsonResponse({'error': 'La importación ya está en proceso o completada'}, status=400)
        
        # Marcar como en proceso
        import_data['status'] = 'processing'
        request.session[f'import_contacto_{import_id}'] = import_data
        request.session.modified = True
        
        try:
            data_rows = import_data['data']
            total_rows = len(data_rows)
            contactos_creados = 0
            errores = []
            
            # Procesar cada fila
            for index, row in enumerate(data_rows):
                try:
                    # Función helper para limpiar campos
                    def clean_field(value):
                        if value is None or pd.isna(value):
                            return ''
                        value_str = str(value).strip()
                        return '' if value_str.lower() in ['nan', 'none', 'null'] else value_str
                    
                    # Buscar el cliente por nombre
                    cliente_nombre = clean_field(row.get('cliente', ''))
                    if not cliente_nombre:
                        error_msg = f'Fila {index + 2}: El nombre del cliente es requerido'
                        errores.append(error_msg)
                        continue
                    
                    # Buscar el cliente existente
                    try:
                        cliente = Cliente.objects.get(nombre=cliente_nombre)
                    except Cliente.DoesNotExist:
                        error_msg = f'Fila {index + 2}: Cliente "{cliente_nombre}" no encontrado'
                        errores.append(error_msg)
                        continue
                    
                    # Validar nombre del contacto
                    nombre_contacto = clean_field(row.get('nombre', ''))
                    if not nombre_contacto:
                        error_msg = f'Fila {index + 2}: El nombre del contacto es requerido'
                        errores.append(error_msg)
                        continue
                    
                    # Crear contacto
                    Contacto.objects.create(
                        cliente=cliente,
                        nombre=nombre_contacto,
                        cargo=clean_field(row.get('cargo', '')),
                        correo=clean_field(row.get('correo', '')),
                        telefono=clean_field(row.get('telefono', '')),
                        notas=clean_field(row.get('notas', ''))
                    )
                    contactos_creados += 1
                except Exception as e:
                    error_msg = f'Fila {index + 2}: Error al importar contacto {row.get("nombre", "desconocido")}: {str(e)}'
                    errores.append(error_msg)
                
                # Actualizar progreso cada 10 registros o al final
                if (index + 1) % 10 == 0 or index == total_rows - 1:
                    import_data.update({
                        'processed': index + 1,
                        'created': contactos_creados,
                        'errors': errores
                    })
                    request.session[f'import_contacto_{import_id}'] = import_data
                    request.session.modified = True
            
            # Marcar como completado
            import_data.update({
                'status': 'completed',
                'processed': total_rows,
                'created': contactos_creados,
                'errors': errores
            })
            request.session[f'import_contacto_{import_id}'] = import_data
            request.session.modified = True
            
            return JsonResponse({
                'status': 'completed',
                'total': total_rows,
                'created': contactos_creados,
                'errors': len(errores)
            })
            
        except Exception as e:
            import_data.update({
                'status': 'error',
                'error': str(e)
            })
            request.session[f'import_contacto_{import_id}'] = import_data
            request.session.modified = True
            return JsonResponse({'error': str(e)}, status=500)

class ContactoImportStatusView(LoginRequiredMixin, TemplateView):
    """Vista AJAX para obtener el estado actual de la importación de contactos"""
    
    def get(self, request, import_id):
        import_data = request.session.get(f'import_contacto_{import_id}')
        if not import_data:
            return JsonResponse({'error': 'Importación no encontrada'}, status=404)
        
        return JsonResponse(import_data)

class ContactosPorClienteView(LoginRequiredMixin, TemplateView):
    """Vista AJAX para obtener contactos de un cliente"""
    
    def get(self, request, cliente_id):
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            contactos = Contacto.objects.filter(cliente=cliente).values(
                'id', 'nombre', 'cargo', 'correo', 'telefono'
            )
            return JsonResponse({
                'success': True,
                'contactos': list(contactos)
            })
        except Cliente.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Cliente no encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })

# Vistas para descargar plantillas de Excel
class ClientePlantillaExcelView(LoginRequiredMixin, TemplateView):
    """Vista para generar y descargar plantilla de Excel para clientes"""
    
    def get(self, request, *args, **kwargs):
        # Crear un DataFrame con las columnas y datos de ejemplo - CAMPOS ACTUALIZADOS
        datos_ejemplo = {
            'nombre': ['Ejemplo Empresa ABC', 'Cliente Muestra XYZ'],
            'sector_actividad': ['Tecnología', 'Comercio'],
            'nit': ['900123456-1', '800987654-2'],
            'correo': ['contacto@empresa.com', 'info@cliente.com'],
            'telefono': ['+56912345678', '+56987654321'],
            'direccion': ['Av. Principal 123, Oficina 201', 'Calle Secundaria 456'],
            'ciudad': ['Santiago', 'Valparaíso'],
            'estado': ['Región Metropolitana', 'Valparaíso'],
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
            'numero_oferta': ['0100', ''],  # Ejemplo: uno con número manual, otro automático
            'nombre': ['Proyecto Implementación ERP', 'Desarrollo App Móvil'],
            'cliente': ['Ejemplo Empresa ABC', 'Cliente Muestra XYZ'],
            'contacto': ['Juan Pérez', 'María González'],  # NUEVO CAMPO
            'valor': [150000, 85000],
            'estado': ['revision_tecnica', 'elaboracion_oferta'],
            'fecha_cierre': ['2025-08-15', '2025-07-30'],
            'correo': ['proyecto@empresa.com', 'desarrollo@cliente.com'],
            'telefono': ['+56912345678', '+56987654321'],
            'descripcion': ['Implementación completa de sistema ERP', 'Desarrollo de aplicación móvil nativa'],
            'probabilidad': [75, 60],
            'fuente': ['visita', 'informe_tecnico'],
            'notas': ['Cliente con presupuesto aprobado', 'Proyecto urgente para Q3'],
            'centro_costos': ['CC001', 'CC002'],
            'nombre_proyecto': ['ERP-2025-001', 'APP-MOV-2025-002'],
            'orden_contrato': ['OC-2025-001', 'OC-2025-002'],
            'dias_prometidos': [90, 60],
            'tipo_negociacion': ['contrato', 'servicios']
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
                'Campo': ['numero_oferta', 'contacto', 'estado', 'fuente', 'tipo_negociacion'],
                'Valores_Válidos': [
                    'OPCIONAL: Número de oferta manual (ej: 0100, 0201). Deje vacío para asignar automáticamente.',
                    'OPCIONAL: Nombre del contacto asociado al trato. Debe existir previamente en el sistema.',
                    'revision_tecnica, elaboracion_oferta, envio_negociacion, formalizacion, ganado, perdido, sin_informacion',
                    'visita, informe_tecnico, email, telefono, whatsapp, otro',
                    'contrato, control, diseno, filtros, mantenimiento, servicios'
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

class ContactoPlantillaExcelView(LoginRequiredMixin, TemplateView):
    """Vista para generar y descargar plantilla de Excel para contactos"""
    
    def get(self, request, *args, **kwargs):
        # Crear un DataFrame con las columnas y datos de ejemplo
        datos_ejemplo = {
            'nombre': ['Juan Pérez', 'María González'],
            'cliente': ['Ejemplo Empresa ABC', 'Cliente Muestra XYZ'],
            'cargo': ['Gerente de Proyectos', 'Directora de Tecnología'],
            'correo': ['juan.perez@empresa.com', 'maria.gonzalez@cliente.com'],
            'telefono': ['+56912345678', '+56987654321'],
            'notas': ['Contacto principal para proyectos', 'Decisor técnico final']
        }
        
        df = pd.DataFrame(datos_ejemplo)
        
        # Crear archivo Excel en memoria
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Contactos')
            
            # Obtener la hoja de trabajo para formatear
            worksheet = writer.sheets['Contactos']
            
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
        response['Content-Disposition'] = 'attachment; filename="plantilla_contactos.xlsx"'
        
        return response

from django.http import HttpResponse
from django.core.management import call_command
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
import io
import sys

@csrf_exempt
def setup_initial_config(request):
    """
    Vista para ejecutar la configuración inicial de RGD AIRE
    Solo disponible para configuración inicial
    """
    if request.method != 'POST' and 'setup_key' not in request.GET:
        return HttpResponse("""
        <html>
        <head><title>Configuración Inicial RGD AIRE</title></head>
        <body>
            <h1>🚀 Configuración Inicial RGD AIRE</h1>
            <p>Esta página ejecuta la configuración inicial de la aplicación.</p>
            <form method="post">
                <input type="hidden" name="setup_key" value="rgd_aire_initial_setup">
                <button type="submit" style="padding: 10px 20px; background: #007cba; color: white; border: none; border-radius: 5px;">
                    ▶️ Ejecutar Configuración Inicial
                </button>
            </form>
        </body>
        </html>
        """)
    
    # Capturar output
    output = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output
    
    try:
        print("🚀 Iniciando configuración de RGD AIRE...")
        
        # 1. Ejecutar migraciones
        print("📊 Ejecutando migraciones de base de datos...")
        call_command('migrate', verbosity=2, interactive=False)
        print("✅ Migraciones completadas exitosamente")
        
        # 2. Crear superadministrador
        print("👤 Configurando superadministrador...")
        try:
            call_command('create_secure_admin')
            print("✅ Superadministrador configurado")
        except Exception as e:
            print(f"⚠️  Error al crear superadministrador: {e}")
            print("💡 Puede que ya exista un administrador")
        
        # 3. Verificar configuración
        print("🔍 Verificando configuración del sistema...")
        call_command('check', deploy=True)
        print("✅ Sistema verificado correctamente")
        
        print("🎉 ¡Configuración inicial completada exitosamente!")
        print()
        print("📋 Información de acceso:")
        print("🌐 URL: https://rgd-aire-dot-appsindunnova.rj.r.appspot.com")
        print("🔐 Admin: https://rgd-aire-dot-appsindunnova.rj.r.appspot.com/admin/")
        print("👤 Usuario: rgd_admin")
        print("📧 Email: admin@rgdaire.com")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        sys.stdout = old_stdout
    
    output_text = output.getvalue()
    
    return HttpResponse(f"""
    <html>
    <head>
        <title>Configuración RGD AIRE - Completada</title>
        <style>
            body {{ font-family: monospace; margin: 20px; }}
            .output {{ background: #f5f5f5; padding: 15px; border-radius: 5px; white-space: pre-wrap; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>✅ Configuración RGD AIRE</h1>
        <div class="output">{output_text}</div>
        <p><a href="/">← Volver a la aplicación</a></p>
        <p><a href="/admin/">🔐 Ir al panel de administración</a></p>
    </body>
    </html>
    """)


# ============================================================================
# VISTAS PARA LEADS
# ============================================================================

class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'crm/lead/list.html'
    context_object_name = 'leads'
    paginate_by = 20

    def get_queryset(self):
        queryset = Lead.objects.all()
        
        # Filtros de búsqueda
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(nombre__icontains=search_query) |
                Q(empresa__icontains=search_query) |
                Q(correo__icontains=search_query) |
                Q(telefono__icontains=search_query)
            )
        
        # Filtros específicos
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        fuente = self.request.GET.get('fuente')
        if fuente:
            queryset = queryset.filter(fuente=fuente)
            
        nivel_interes = self.request.GET.get('nivel_interes')
        if nivel_interes:
            queryset = queryset.filter(nivel_interes=nivel_interes)
            
        responsable_id = self.request.GET.get('responsable')
        if responsable_id:
            queryset = queryset.filter(responsable_id=responsable_id)
            
        sector = self.request.GET.get('sector')
        if sector:
            queryset = queryset.filter(sector_actividad=sector)

        return queryset.order_by('-fecha_actualizacion')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar opciones para filtros
        context['estados_lead'] = Lead.ESTADO_CHOICES
        context['fuentes_lead'] = Lead.FUENTE_CHOICES
        context['niveles_interes'] = Lead.INTERES_CHOICES
        context['sectores'] = Cliente.SECTOR_ACTIVIDAD_CHOICES
        context['responsables'] = get_user_model().objects.filter(is_active=True).order_by('username')
        
        # Mantener filtros seleccionados
        context['selected_estado'] = self.request.GET.get('estado')
        context['selected_fuente'] = self.request.GET.get('fuente')
        context['selected_nivel_interes'] = self.request.GET.get('nivel_interes')
        context['selected_responsable'] = self.request.GET.get('responsable')
        context['selected_sector'] = self.request.GET.get('sector')
        context['search_query'] = self.request.GET.get('q', '')
        
        return context


class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    template_name = 'crm/lead/form.html'
    fields = ['nombre', 'empresa', 'cargo', 'correo', 'telefono', 'sector_actividad',
              'estado', 'fuente', 'nivel_interes', 'necesidad', 'presupuesto_estimado',
              'fecha_contacto_inicial', 'responsable', 'notas']
    success_url = reverse_lazy('crm:lead_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Personalizar widgets
        form.fields['fecha_contacto_inicial'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        form.fields['necesidad'].widget = forms.Textarea(
            attrs={'rows': 3, 'class': 'form-control'}
        )
        form.fields['notas'].widget = forms.Textarea(
            attrs={'rows': 3, 'class': 'form-control'}
        )
        
        # Aplicar clases CSS
        for field in form.fields.values():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            field.widget.attrs.update({'class': 'form-control'})
            
        return form

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        if not form.instance.responsable:
            form.instance.responsable = self.request.user
            
        messages.success(self.request, 'Lead creado exitosamente.')
        return super().form_valid(form)


class LeadDetailView(LoginRequiredMixin, DetailView):
    model = Lead
    template_name = 'crm/lead/detail.html'
    context_object_name = 'lead'


class LeadUpdateView(LoginRequiredMixin, UpdateView):
    model = Lead
    template_name = 'crm/lead/form.html'
    fields = ['nombre', 'empresa', 'cargo', 'correo', 'telefono', 'sector_actividad',
              'estado', 'fuente', 'nivel_interes', 'necesidad', 'presupuesto_estimado',
              'fecha_contacto_inicial', 'fecha_ultima_interaccion', 'responsable', 'notas']
    success_url = reverse_lazy('crm:lead_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Personalizar widgets
        form.fields['fecha_contacto_inicial'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        form.fields['fecha_ultima_interaccion'].widget = forms.DateInput(
            attrs={'type': 'date', 'class': 'form-control'}
        )
        form.fields['necesidad'].widget = forms.Textarea(
            attrs={'rows': 3, 'class': 'form-control'}
        )
        form.fields['notas'].widget = forms.Textarea(
            attrs={'rows': 3, 'class': 'form-control'}
        )
        
        # Aplicar clases CSS
        for field in form.fields.values():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            field.widget.attrs.update({'class': 'form-control'})
            
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Lead actualizado exitosamente.')
        return super().form_valid(form)


class LeadDeleteView(LoginRequiredMixin, DeleteView):
    model = Lead
    template_name = 'crm/lead/confirm_delete.html'
    success_url = reverse_lazy('crm:lead_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Lead eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)


class LeadConvertView(LoginRequiredMixin, TemplateView):
    template_name = 'crm/lead/convert.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lead'] = get_object_or_404(Lead, pk=self.kwargs['pk'])
        return context
    
    def post(self, request, *args, **kwargs):
        lead = get_object_or_404(Lead, pk=kwargs['pk'])
        
        print(f"DEBUG: Converting lead {lead.nombre}")
        print(f"DEBUG: POST data: {request.POST}")
        
        if not lead.puede_convertir():
            messages.error(request, 'Este lead no puede ser convertido.')
            return redirect('crm:lead_detail', pk=lead.pk)
        
        conversion_type = request.POST.get('conversion_type')
        print(f"DEBUG: Conversion type: {conversion_type}")
        
        try:
            with transaction.atomic():
                if conversion_type == 'cliente':
                    # Convertir a Cliente
                    cliente = Cliente.objects.create(
                        nombre=lead.empresa or lead.nombre,
                        sector_actividad=lead.sector_actividad,
                        correo=lead.correo,
                        telefono=lead.telefono,
                        notas=f"Convertido desde Lead: {lead.nombre}\n\n{lead.notas}"
                    )
                    
                    # Crear contacto asociado
                    Contacto.objects.create(
                        cliente=cliente,
                        nombre=lead.nombre,
                        cargo=lead.cargo,
                        correo=lead.correo,
                        telefono=lead.telefono,
                        notas=f"Contacto principal del lead convertido"
                    )
                    
                    # Actualizar lead
                    lead.convertido_a_cliente = cliente
                    lead.estado = 'convertido'
                    lead.save()
                    
                    messages.success(request, f'Lead convertido exitosamente a Cliente: {cliente.nombre}')
                    return redirect('crm:cliente_detail', pk=cliente.pk)
                
                elif conversion_type == 'trato':
                    # Crear o buscar cliente existente
                    cliente = None
                    if lead.empresa:
                        cliente, created = Cliente.objects.get_or_create(
                            nombre=lead.empresa,
                            defaults={
                                'sector_actividad': lead.sector_actividad,
                                'correo': lead.correo,
                                'telefono': lead.telefono,
                                'notas': f"Cliente creado desde Lead: {lead.nombre}"
                            }
                        )
                    
                    # Crear contacto si no existe
                    contacto = None
                    if cliente:
                        contacto, created = Contacto.objects.get_or_create(
                            cliente=cliente,
                            correo=lead.correo,
                            defaults={
                                'nombre': lead.nombre,
                                'cargo': lead.cargo,
                                'telefono': lead.telefono,
                                'notas': f"Contacto desde lead convertido"
                            }
                        )
                    
                    # Convertir a Trato
                    trato = Trato.objects.create(
                        nombre=lead.necesidad[:200] if lead.necesidad else f"Oportunidad de {lead.nombre}",
                        cliente=cliente,
                        contacto=contacto,
                        correo=lead.correo,
                        telefono=lead.telefono,
                        descripcion=lead.necesidad or f"Trato convertido desde lead: {lead.nombre}",
                        valor=lead.presupuesto_estimado or 0,
                        probabilidad=70,  # Alta probabilidad para leads convertidos
                        estado='revision_tecnica',
                        fuente=lead.fuente if lead.fuente in dict(Trato.FUENTE_CHOICES) else 'otro',
                        responsable=lead.responsable or request.user,
                        notas=f"Convertido desde Lead: {lead.nombre}\n\n{lead.notas}"
                    )
                    
                    # Actualizar lead
                    lead.convertido_a_cliente = cliente
                    lead.convertido_a_trato = trato
                    lead.estado = 'convertido'
                    lead.save()
                    
                    messages.success(request, f'Lead convertido exitosamente a ProyectoCRM #{trato.numero_oferta}')
                    return redirect('crm:trato_detail', pk=trato.pk)
                    
        except Exception as e:
            messages.error(request, f'Error al convertir el lead: {str(e)}')
            return redirect('crm:lead_detail', pk=lead.pk)
        
        messages.error(request, 'Tipo de conversión no válido.')
        return redirect('crm:lead_detail', pk=lead.pk)


class ConfiguracionOfertaForm(forms.Form):
    siguiente_numero = forms.IntegerField(
        label='Siguiente Número de Oferta',
        min_value=1,
        help_text='El próximo número que se asignará a una nueva oferta',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 200'
        })
    )


class ConfiguracionOfertaView(LoginRequiredMixin, FormView):
    template_name = 'crm/configuracion_oferta.html'
    form_class = ConfiguracionOfertaForm
    success_url = reverse_lazy('crm:configuracion_oferta')

    def dispatch(self, request, *args, **kwargs):
        # Solo permitir acceso a superusuarios o usuarios con permisos específicos
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a esta configuración.')
            return redirect('crm:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Cargar el valor actual de la configuración"""
        config = ConfiguracionOferta.obtener_configuracion()
        return {'siguiente_numero': config.siguiente_numero}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = ConfiguracionOferta.obtener_configuracion()
        
        # Obtener estadísticas útiles
        ultimo_trato = Trato.objects.exclude(numero_oferta='').order_by('-numero_oferta').first()
        total_ofertas = Trato.objects.exclude(numero_oferta='').count()
        
        context.update({
            'config': config,
            'ultimo_numero': ultimo_trato.numero_oferta if ultimo_trato else 'Ninguna',
            'total_ofertas': total_ofertas,
            'siguiente_formato': f"{config.siguiente_numero:04d}",
        })
        return context

    def form_valid(self, form):
        """Guardar la nueva configuración"""
        nuevo_numero = form.cleaned_data['siguiente_numero']
        
        try:
            # Obtener la configuración existente
            config = ConfiguracionOferta.obtener_configuracion()
            
            # Validar que el nuevo número no sea menor al último usado
            ultimo_trato = Trato.objects.exclude(numero_oferta='').order_by('-numero_oferta').first()
            if ultimo_trato and ultimo_trato.numero_oferta:
                try:
                    ultimo_numero = int(ultimo_trato.numero_oferta)
                    if nuevo_numero <= ultimo_numero:
                        messages.warning(
                            self.request, 
                            f'Advertencia: El número configurado ({nuevo_numero:04d}) es menor o igual '
                            f'al último número usado ({ultimo_numero:04d}). Esto podría causar conflictos.'
                        )
                except ValueError:
                    pass  # Si no se puede convertir, continuar
            
            # Actualizar la configuración
            config.siguiente_numero = nuevo_numero
            config.actualizado_por = self.request.user
            config.save()
            
            messages.success(
                self.request, 
                f'Configuración actualizada exitosamente. '
                f'Las próximas ofertas comenzarán desde #{nuevo_numero:04d}'
            )
            
        except Exception as e:
            messages.error(self.request, f'Error al actualizar la configuración: {str(e)}')
        
        return super().form_valid(form)
