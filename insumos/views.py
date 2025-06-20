from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count, F, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    # Catálogo
    Producto, CategoriaProducto, Marca, Proveedor, Inventario,
    # Cotizaciones y Pedidos
    Cotizacion, ItemCotizacion, Pedido, ItemPedido,
    # Recomendaciones
    RecomendacionProducto, KitMantenimiento
)
from crm.models import Cliente, Contacto

class InsumosDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'insumos/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Estadísticas generales
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        
        # Contadores principales
        context.update({
            'total_productos': Producto.objects.filter(activo=True).count(),
            'productos_stock_bajo': Inventario.objects.filter(
                producto__activo=True
            ).filter(
                stock_actual__lte=F('stock_minimo')
            ).count(),
            'cotizaciones_pendientes': Cotizacion.objects.filter(
                estado__in=['borrador', 'enviada', 'en_negociacion']
            ).count(),
            'pedidos_pendientes': Pedido.objects.filter(
                estado__in=['pendiente', 'confirmado', 'en_preparacion']
            ).count(),
            'recomendaciones_pendientes': RecomendacionProducto.objects.filter(
                procesada=False
            ).count(),
        })
        
        # Productos con stock crítico
        context['productos_criticos'] = Inventario.objects.filter(
            producto__activo=True,
            stock_actual__lte=F('stock_minimo')
        ).select_related('producto', 'almacen').order_by('stock_actual')[:10]
        
        # Cotizaciones recientes
        context['cotizaciones_recientes'] = Cotizacion.objects.filter(
            fecha_creacion__gte=inicio_mes
        ).select_related('cliente').order_by('-fecha_creacion')[:10]
        
        # Pedidos próximos a entregar
        fecha_limite = hoy + timedelta(days=7)
        context['pedidos_proximos'] = Pedido.objects.filter(
            fecha_entrega_solicitada__range=[hoy, fecha_limite],
            estado__in=['confirmado', 'en_preparacion', 'listo_despacho']
        ).select_related('cliente').order_by('fecha_entrega_solicitada')[:10]
        
        # Estadísticas de ventas del mes
        ventas_mes = Cotizacion.objects.filter(
            fecha_creacion__gte=inicio_mes,
            estado='aprobada'
        ).aggregate(
            total_ventas=Sum('total_general'),
            cantidad_cotizaciones=Count('id')
        )
        context['ventas_mes'] = ventas_mes
        
        # Top productos más cotizados
        context['productos_populares'] = ItemCotizacion.objects.filter(
            cotizacion__fecha_creacion__gte=inicio_mes
        ).values(
            'producto__codigo_interno',
            'producto__nombre'
        ).annotate(
            total_cantidad=Sum('cantidad'),
            total_cotizaciones=Count('cotizacion', distinct=True)
        ).order_by('-total_cantidad')[:10]
        
        # Recomendaciones sin procesar por prioridad
        context['recomendaciones_por_prioridad'] = RecomendacionProducto.objects.filter(
            procesada=False
        ).values('prioridad').annotate(
            cantidad=Count('id')
        ).order_by('prioridad')
        
        return context

class ProductoListView(LoginRequiredMixin, ListView):
    model = Producto
    template_name = 'insumos/producto/list.html'
    context_object_name = 'productos'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'categoria', 'marca', 'unidad_medida', 'proveedor_principal'
        ).prefetch_related('inventarios')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(codigo_interno__icontains=search) |
                Q(codigo_fabricante__icontains=search) |
                Q(nombre__icontains=search) |
                Q(descripcion_corta__icontains=search)
            )
        
        # Filtro por categoría
        categoria_id = self.request.GET.get('categoria')
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
            
        # Filtro por marca
        marca_id = self.request.GET.get('marca')
        if marca_id:
            queryset = queryset.filter(marca_id=marca_id)
            
        # Filtro por estado
        activo = self.request.GET.get('activo')
        if activo:
            queryset = queryset.filter(activo=activo == 'true')
            
        # Filtro por productos con stock bajo
        if self.request.GET.get('stock_bajo') == '1':
            productos_stock_bajo = Inventario.objects.filter(
                stock_actual__lte=F('stock_minimo')
            ).values_list('producto_id', flat=True)
            queryset = queryset.filter(id__in=productos_stock_bajo)
            
        return queryset.filter(activo=True).order_by('categoria__nombre', 'nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaProducto.objects.filter(activa=True).order_by('nombre')
        context['marcas'] = Marca.objects.filter(activa=True).order_by('nombre')
        
        # Agregar información de stock a cada producto
        for producto in context['productos']:
            inventarios = producto.inventarios.all()
            producto.stock_total = sum(inv.stock_actual for inv in inventarios)
            producto.requiere_reorden = any(inv.requiere_reorden for inv in inventarios)
        
        return context

class ProductoDetailView(LoginRequiredMixin, DetailView):
    model = Producto
    template_name = 'insumos/producto/detail.html'
    context_object_name = 'producto'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto = self.get_object()
        
        # Inventarios del producto
        context['inventarios'] = producto.inventarios.select_related('almacen').all()
        
        # Especificaciones técnicas
        context['especificaciones'] = producto.especificaciones.order_by('orden')
        
        # Imágenes adicionales
        context['imagenes'] = producto.imagenes.order_by('orden')
        
        # Productos equivalentes
        context['equivalentes'] = producto.equivalentes.select_related('producto_equivalente')
        
        # Compatibilidades con equipos
        context['compatibilidades'] = producto.compatibilidades.all()
        
        # Precios especiales activos
        context['precios_especiales'] = producto.precios_especiales.filter(
            lista_precio__activa=True
        ).select_related('lista_precio__segmento')
        
        # Descuentos por volumen activos
        hoy = timezone.now().date()
        context['descuentos_volumen'] = producto.descuentos_volumen.filter(
            activo=True,
            fecha_inicio__lte=hoy
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
        ).order_by('cantidad_minima')
        
        # Historial de cotizaciones recientes
        context['cotizaciones_recientes'] = ItemCotizacion.objects.filter(
            producto=producto
        ).select_related('cotizacion').order_by('-cotizacion__fecha_creacion')[:10]
        
        return context

class CotizacionListView(LoginRequiredMixin, ListView):
    model = Cotizacion
    template_name = 'insumos/cotizacion/list.html'
    context_object_name = 'cotizaciones'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente', 'contacto', 'creado_por')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(numero_cotizacion__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(contacto__nombre__icontains=search)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
            
        # Filtro por fecha
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__gte=fecha_desde)
            
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__lte=fecha_hasta)
            
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Cotizacion.ESTADO_CHOICES
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        return context

class CotizacionCreateView(LoginRequiredMixin, CreateView):
    model = Cotizacion
    template_name = 'insumos/cotizacion/form.html'
    fields = [
        'cliente', 'contacto', 'trato_crm', 'orden_mantenimiento', 'equipo_referencia',
        'fecha_validez', 'descuento_general', 'incremento_flete', 'observaciones',
        'terminos_condiciones'
    ]
    success_url = reverse_lazy('insumos:cotizacion_list')
    
    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        form.instance.actualizado_por = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Cotización creada exitosamente.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Nueva Cotización'
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        return context

class CotizacionDetailView(LoginRequiredMixin, DetailView):
    model = Cotizacion
    template_name = 'insumos/cotizacion/detail.html'
    context_object_name = 'cotizacion'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cotizacion = self.get_object()
        
        # Items de la cotización
        context['items'] = cotizacion.items.select_related('producto').order_by('id')
        
        # Pedidos generados desde esta cotización
        context['pedidos'] = cotizacion.pedidos.all().order_by('-fecha_pedido')
        
        return context

class PedidoListView(LoginRequiredMixin, ListView):
    model = Pedido
    template_name = 'insumos/pedido/list.html'
    context_object_name = 'pedidos'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente', 'contacto', 'cotizacion')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(numero_pedido__icontains=search) |
                Q(cliente__nombre__icontains=search) |
                Q(orden_compra_cliente__icontains=search)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
            
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
            
        return queryset.order_by('-fecha_pedido')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['estados'] = Pedido.ESTADO_CHOICES
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        return context

class PedidoDetailView(LoginRequiredMixin, DetailView):
    model = Pedido
    template_name = 'insumos/pedido/detail.html'
    context_object_name = 'pedido'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pedido = self.get_object()
        
        # Items del pedido
        context['items'] = pedido.items.select_related('producto', 'almacen_origen').order_by('id')
        
        # Entregas del pedido
        context['entregas'] = pedido.entregas.order_by('-fecha_entrega')
        
        return context

class RecomendacionListView(LoginRequiredMixin, ListView):
    model = RecomendacionProducto
    template_name = 'insumos/recomendacion/list.html'
    context_object_name = 'recomendaciones'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cliente', 'producto')
        
        # Filtro por estado
        procesada = self.request.GET.get('procesada')
        if procesada is not None:
            queryset = queryset.filter(procesada=procesada == 'true')
        else:
            # Por defecto mostrar solo las no procesadas
            queryset = queryset.filter(procesada=False)
            
        # Filtro por origen
        origen = self.request.GET.get('origen')
        if origen:
            queryset = queryset.filter(origen_recomendacion=origen)
            
        # Filtro por prioridad
        prioridad = self.request.GET.get('prioridad')
        if prioridad:
            queryset = queryset.filter(prioridad=prioridad)
            
        # Filtro por cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            queryset = queryset.filter(cliente_id=cliente_id)
            
        return queryset.order_by('-fecha_creacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['origenes'] = RecomendacionProducto.ORIGEN_CHOICES
        context['prioridades'] = [
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
            ('urgente', 'Urgente'),
        ]
        context['clientes'] = Cliente.objects.all().order_by('nombre')
        return context

class KitMantenimientoListView(LoginRequiredMixin, ListView):
    model = KitMantenimiento
    template_name = 'insumos/kit/list.html'
    context_object_name = 'kits'
    paginate_by = 15
    
    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('items__producto')
        
        # Filtro por búsqueda
        search = self.request.GET.get('q', '')
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(tipo_equipo__icontains=search)
            )
        
        # Filtro por tipo de equipo
        tipo_equipo = self.request.GET.get('tipo_equipo')
        if tipo_equipo:
            queryset = queryset.filter(tipo_equipo=tipo_equipo)
            
        # Filtro por estado
        activo = self.request.GET.get('activo')
        if activo:
            queryset = queryset.filter(activo=activo == 'true')
            
        return queryset.filter(activo=True).order_by('nombre')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Tipos de equipo únicos
        context['tipos_equipo'] = KitMantenimiento.objects.filter(
            activo=True
        ).values_list('tipo_equipo', flat=True).distinct().order_by('tipo_equipo')
        
        return context

class KitMantenimientoDetailView(LoginRequiredMixin, DetailView):
    model = KitMantenimiento
    template_name = 'insumos/kit/detail.html'
    context_object_name = 'kit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kit = self.get_object()
        
        # Items del kit
        context['items'] = kit.items.select_related('producto').order_by('orden')
        
        # Calcular precios
        context['precio_individual'] = kit.calcular_precio_individual()
        context['ahorro'] = kit.ahorro_kit
        context['porcentaje_ahorro'] = (context['ahorro'] / context['precio_individual']) * 100 if context['precio_individual'] > 0 else 0
        
        return context

# ============================================================================
# API VIEWS PARA BÚSQUEDAS AJAX
# ============================================================================

def buscar_productos_api(request):
    """API para búsqueda de productos en tiempo real"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'productos': []})
    
    productos = Producto.objects.filter(
        Q(codigo_interno__icontains=query) |
        Q(nombre__icontains=query) |
        Q(codigo_fabricante__icontains=query),
        activo=True
    ).select_related('categoria', 'marca', 'unidad_medida')[:20]
    
    data = []
    for producto in productos:
        # Calcular stock total
        stock_total = sum(inv.stock_actual for inv in producto.inventarios.all())
        
        data.append({
            'id': producto.id,
            'codigo_interno': producto.codigo_interno,
            'nombre': producto.nombre,
            'categoria': producto.categoria.nombre,
            'marca': producto.marca.nombre,
            'precio_venta_base': float(producto.precio_venta_base),
            'precio_con_iva': float(producto.precio_con_iva),
            'unidad_medida': producto.unidad_medida.simbolo,
            'stock_total': float(stock_total),
            'imagen_url': producto.imagen_principal.url if producto.imagen_principal else None,
        })
    
    return JsonResponse({'productos': data})

def obtener_contactos_cliente_api(request, cliente_id):
    """API para obtener contactos de un cliente específico"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        contactos = Contacto.objects.filter(cliente_id=cliente_id).values(
            'id', 'nombre', 'cargo', 'correo', 'telefono'
        )
        return JsonResponse(list(contactos), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def obtener_precio_producto_api(request, producto_id):
    """API para obtener precio de producto según cliente y cantidad"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        cliente_id = request.GET.get('cliente_id')
        cantidad = request.GET.get('cantidad', 1)
        
        # Precio base
        precio = producto.precio_venta_base
        
        # TODO: Implementar lógica de precios especiales por cliente y descuentos por volumen
        
        data = {
            'precio_unitario': float(precio),
            'precio_con_iva': float(producto.precio_con_iva),
            'iva_porcentaje': float(producto.iva),
            'descuento_aplicable': 0,  # Implementar lógica de descuentos
            'stock_disponible': sum(inv.stock_disponible for inv in producto.inventarios.all())
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def generar_cotizacion_desde_recomendacion_api(request, recomendacion_id):
    """API para generar cotización automática desde recomendación"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        recomendacion = get_object_or_404(RecomendacionProducto, id=recomendacion_id)
        
        # Crear cotización automática
        cotizacion = Cotizacion.objects.create(
            cliente=recomendacion.cliente,
            fecha_validez=timezone.now().date() + timedelta(days=30),
            creado_por=request.user,
            actualizado_por=request.user,
            observaciones=f"Cotización generada automáticamente desde recomendación: {recomendacion.motivo}"
        )
        
        # Crear item de cotización
        ItemCotizacion.objects.create(
            cotizacion=cotizacion,
            producto=recomendacion.producto,
            cantidad=recomendacion.cantidad_sugerida,
            precio_unitario=recomendacion.producto.precio_venta_base,
            observaciones=recomendacion.motivo
        )
        
        # Marcar recomendación como procesada
        recomendacion.procesada = True
        recomendacion.cotizacion_generada = cotizacion
        recomendacion.fecha_procesamiento = timezone.now()
        recomendacion.save()
        
        return JsonResponse({
            'success': True,
            'cotizacion_id': cotizacion.id,
            'numero_cotizacion': cotizacion.numero_cotizacion,
            'mensaje': 'Cotización generada exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)