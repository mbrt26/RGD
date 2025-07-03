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
    path('clientes/importar/progreso/<str:import_id>/', login_required(views.ClienteImportProgressView.as_view()), name='cliente_import_progress'),
    path('clientes/importar/proceso/<str:import_id>/', login_required(views.ClienteImportProcessView.as_view()), name='cliente_import_process'),
    path('clientes/importar/estado/<str:import_id>/', login_required(views.ClienteImportStatusView.as_view()), name='cliente_import_status'),
    path('clientes/plantilla-excel/', login_required(views.ClientePlantillaExcelView.as_view()), name='cliente_plantilla_excel'),
    path('clientes/<int:pk>/', login_required(views.ClienteDetailView.as_view()), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', login_required(views.ClienteUpdateView.as_view()), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', login_required(views.ClienteDeleteView.as_view()), name='cliente_delete'),
    
    # Contactos
    path('contactos/', login_required(views.ContactoListView.as_view()), name='contacto_list'),
    path('contactos/nuevo/', login_required(views.ContactoCreateView.as_view()), name='contacto_create'),
    path('contactos/importar/', login_required(views.ContactoImportView.as_view()), name='contacto_import'),
    path('contactos/importar/progreso/<str:import_id>/', login_required(views.ContactoImportProgressView.as_view()), name='contacto_import_progress'),
    path('contactos/importar/proceso/<str:import_id>/', login_required(views.ContactoImportProcessView.as_view()), name='contacto_import_process'),
    path('contactos/importar/estado/<str:import_id>/', login_required(views.ContactoImportStatusView.as_view()), name='contacto_import_status'),
    path('contactos/plantilla-excel/', login_required(views.ContactoPlantillaExcelView.as_view()), name='contacto_plantilla_excel'),
    path('contactos/<int:pk>/', login_required(views.ContactoDetailView.as_view()), name='contacto_detail'),
    path('contactos/<int:pk>/editar/', login_required(views.ContactoUpdateView.as_view()), name='contacto_update'),
    path('clientes/<int:cliente_id>/contactos/nuevo/', login_required(views.ContactoCreateFromClientView.as_view()), name='contacto_create_from_client'),
    path('api/clientes/<int:cliente_id>/contactos/', login_required(views.ContactosPorClienteView.as_view()), name='contactos_por_cliente'),
    
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
    
    # ProyectosCRM
    path('proyectoscrm/', login_required(views.TratoListView.as_view()), name='trato_list'),
    path('proyectoscrm/nuevo/', login_required(views.TratoCreateView.as_view()), name='trato_create'),
    path('proyectoscrm/rapido/', login_required(views.TratoQuickCreateView.as_view()), name='trato_quick_create'),
    path('proyectoscrm/importar/', login_required(views.TratoImportView.as_view()), name='trato_import'),
    path('proyectoscrm/plantilla-excel/', login_required(views.TratoPlantillaExcelView.as_view()), name='trato_plantilla_excel'),
    path('proyectoscrm/eliminar-masivo/', login_required(views.TratoBulkDeleteView.as_view()), name='trato_bulk_delete'),
    path('proyectoscrm/<int:pk>/', login_required(views.TratoDetailView.as_view()), name='trato_detail'),
    path('proyectoscrm/<int:pk>/editar/', login_required(views.TratoUpdateView.as_view()), name='trato_update'),
    
    # Leads
    path('leads/', login_required(views.LeadListView.as_view()), name='lead_list'),
    path('leads/nuevo/', login_required(views.LeadCreateView.as_view()), name='lead_create'),
    path('leads/<int:pk>/', login_required(views.LeadDetailView.as_view()), name='lead_detail'),
    path('leads/<int:pk>/editar/', login_required(views.LeadUpdateView.as_view()), name='lead_update'),
    path('leads/<int:pk>/eliminar/', login_required(views.LeadDeleteView.as_view()), name='lead_delete'),
    path('leads/<int:pk>/convertir/', login_required(views.LeadConvertView.as_view()), name='lead_convert'),
    
    # Configuración
    path('configuracion/ofertas/', login_required(views.ConfiguracionOfertaView.as_view()), name='configuracion_oferta'),
]