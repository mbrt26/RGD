from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'crm'

urlpatterns = [
    # Dashboard
    path('', login_required(views.CRMDashboardView.as_view()), name='dashboard'),
    
    # Configuración inicial (sin login requerido para setup inicial)
    path('setup/', views.setup_initial_config, name='setup_initial'),
    
    # Clientes
    path('clientes/', login_required(views.ClienteListView.as_view()), name='cliente_list'),
    path('clientes/nuevo/', login_required(views.ClienteCreateView.as_view()), name='cliente_create'),
    path('clientes/importar/', login_required(views.ClienteImportView.as_view()), name='cliente_import'),
    path('clientes/plantilla-excel/', login_required(views.ClientePlantillaExcelView.as_view()), name='cliente_plantilla_excel'),
    path('clientes/<int:pk>/', login_required(views.ClienteDetailView.as_view()), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', login_required(views.ClienteUpdateView.as_view()), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', login_required(views.ClienteDeleteView.as_view()), name='cliente_delete'),
    
    # Contactos
    path('clientes/<int:cliente_id>/contactos/nuevo/', login_required(views.ContactoCreateView.as_view()), name='contacto_create'),
    
    # Representantes
    path('representantes/', login_required(views.RepresentanteListView.as_view()), name='representante_list'),
    path('representantes/nuevo/', login_required(views.RepresentanteCreateView.as_view()), name='representante_create'),
    path('representantes/<int:pk>/', login_required(views.RepresentanteDetailView.as_view()), name='representante_detail'),
    path('representantes/<int:pk>/editar/', login_required(views.RepresentanteUpdateView.as_view()), name='representante_update'),
    
    # Cotizaciones
    path('oferta/', login_required(views.CotizacionListView.as_view()), name='cotizacion_list'),
    path('oferta/nueva/', login_required(views.CotizacionCreateView.as_view()), name='cotizacion_create'),
    path('oferta/<int:pk>/', login_required(views.CotizacionDetailView.as_view()), name='cotizacion_detail'),
    path('oferta/<int:pk>/editar/', login_required(views.CotizacionUpdateView.as_view()), name='cotizacion_update'),
    path('oferta/<int:pk>/eliminar/', login_required(views.CotizacionDeleteView.as_view()), name='cotizacion_delete'),
    
    # Tareas
    path('tareas/', login_required(views.TareaVentaListView.as_view()), name='tarea_list'),
    path('tareas/nueva/', login_required(views.TareaVentaCreateView.as_view()), name='tarea_create'),
    path('tareas/<int:pk>/', login_required(views.TareaVentaDetailView.as_view()), name='tarea_detail'),
    path('tareas/<int:pk>/editar/', login_required(views.TareaVentaUpdateView.as_view()), name='tarea_update'),
    
    # Tratos
    path('tratos/', login_required(views.TratoListView.as_view()), name='trato_list'),
    path('tratos/nuevo/', login_required(views.TratoCreateView.as_view()), name='trato_create'),
    path('tratos/importar/', login_required(views.TratoImportView.as_view()), name='trato_import'),
    path('tratos/plantilla-excel/', login_required(views.TratoPlantillaExcelView.as_view()), name='trato_plantilla_excel'),
    path('tratos/<int:pk>/', login_required(views.TratoDetailView.as_view()), name='trato_detail'),
    path('tratos/<int:pk>/editar/', login_required(views.TratoUpdateView.as_view()), name='trato_update'),
]