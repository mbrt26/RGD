from django.urls import path
from . import views

app_name = 'insumos'

urlpatterns = [
    # Dashboard principal
    path('', views.InsumosDashboardView.as_view(), name='dashboard'),
    
    # Gestión de productos
    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    
    # Gestión de cotizaciones
    path('cotizaciones/', views.CotizacionListView.as_view(), name='cotizacion_list'),
    path('cotizaciones/nueva/', views.CotizacionCreateView.as_view(), name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', views.CotizacionDetailView.as_view(), name='cotizacion_detail'),
    
    # Gestión de pedidos
    path('pedidos/', views.PedidoListView.as_view(), name='pedido_list'),
    path('pedidos/<int:pk>/', views.PedidoDetailView.as_view(), name='pedido_detail'),
    
    # Gestión de recomendaciones
    path('recomendaciones/', views.RecomendacionListView.as_view(), name='recomendacion_list'),
    
    # Gestión de kits de mantenimiento
    path('kits/', views.KitMantenimientoListView.as_view(), name='kit_list'),
    path('kits/<int:pk>/', views.KitMantenimientoDetailView.as_view(), name='kit_detail'),
    
    # APIs para funcionalidad AJAX
    path('api/productos/buscar/', views.buscar_productos_api, name='api_buscar_productos'),
    path('api/clientes/<int:cliente_id>/contactos/', views.obtener_contactos_cliente_api, name='api_contactos_cliente'),
    path('api/productos/<int:producto_id>/precio/', views.obtener_precio_producto_api, name='api_precio_producto'),
    path('api/recomendaciones/<int:recomendacion_id>/generar-cotizacion/', views.generar_cotizacion_desde_recomendacion_api, name='api_generar_cotizacion'),
]