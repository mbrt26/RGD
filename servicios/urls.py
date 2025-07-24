from django.urls import path
from . import views

app_name = 'servicios'

urlpatterns = [
    # Dashboard
    path('', views.ServiciosDashboardView.as_view(), name='dashboard'),
    
    # Técnicos (deshabilitado - ahora se usan colaboradores)
    # path('tecnicos/', views.TecnicoListView.as_view(), name='tecnico_list'),
    # path('tecnicos/nuevo/', views.TecnicoCreateView.as_view(), name='tecnico_create'),
    # path('tecnicos/<int:pk>/', views.TecnicoDetailView.as_view(), name='tecnico_detail'),
    # path('tecnicos/<int:pk>/editar/', views.TecnicoUpdateView.as_view(), name='tecnico_update'),
    
    # Solicitudes de Servicio
    path('solicitudes/', views.SolicitudServicioListView.as_view(), name='solicitud_list'),
    path('solicitudes/nueva/', views.SolicitudServicioCreateView.as_view(), name='solicitud_create'),
    path('solicitudes/<int:pk>/', views.SolicitudServicioDetailView.as_view(), name='solicitud_detail'),
    path('solicitudes/<int:pk>/editar/', views.SolicitudServicioUpdateView.as_view(), name='solicitud_update'),
    path('solicitudes/<int:pk>/eliminar/', views.SolicitudServicioDeleteView.as_view(), name='solicitud_delete'),
    
    # Informes de Trabajo
    path('informes/', views.InformeTrabajoListView.as_view(), name='informe_list'),
    path('informes/nuevo/', views.InformeTrabajoCreateView.as_view(), name='informe_create'),
    path('informes/<int:pk>/', views.InformeTrabajoDetailView.as_view(), name='informe_detail'),
    path('informes/<int:pk>/editar/', views.InformeTrabajoUpdateView.as_view(), name='informe_update'),
    
    # APIs AJAX
    path('api/contactos-cliente/<int:cliente_id>/', views.get_contactos_cliente, name='api_contactos_cliente'),
    path('api/contactos-trato/<int:trato_id>/', views.get_contactos_trato, name='api_contactos_trato'),
    path('api/cotizaciones-cliente/<int:cliente_id>/', views.get_cotizaciones_cliente, name='api_cotizaciones_cliente'),
    path('api/cotizaciones-trato/<int:trato_id>/', views.get_cotizaciones_trato, name='api_cotizaciones_trato'),
    path('api/solicitudes-tecnico/<int:tecnico_id>/', views.get_solicitudes_tecnico, name='api_solicitudes_tecnico'),
    path('api/solicitud-tipo/<int:solicitud_id>/', views.get_solicitud_tipo, name='api_solicitud_tipo'),
]