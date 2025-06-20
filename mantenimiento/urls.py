from django.urls import path
from . import views

app_name = 'mantenimiento'

urlpatterns = [
    # Dashboard
    path('', views.MantenimientoDashboardView.as_view(), name='dashboard'),
    
    # Equipos (Base de datos de equipos)
    path('equipos/', views.EquipoListView.as_view(), name='equipo_list'),
    path('equipos/nuevo/', views.EquipoCreateView.as_view(), name='equipo_create'),
    path('equipos/<int:pk>/', views.EquipoDetailView.as_view(), name='equipo_detail'),
    path('equipos/<int:pk>/editar/', views.EquipoUpdateView.as_view(), name='equipo_update'),
    
    # Hojas de Vida de Equipos
    path('hojas-vida/', views.HojaVidaEquipoListView.as_view(), name='hoja_vida_list'),
    path('hojas-vida/nueva/', views.HojaVidaEquipoCreateView.as_view(), name='hoja_vida_create'),
    path('hojas-vida/<int:pk>/', views.HojaVidaEquipoDetailView.as_view(), name='hoja_vida_detail'),
    path('hojas-vida/<int:pk>/editar/', views.HojaVidaEquipoUpdateView.as_view(), name='hoja_vida_update'),
    
    # Contratos de Mantenimiento
    path('contratos/', views.ContratoMantenimientoListView.as_view(), name='contrato_list'),
    path('contratos/nuevo/', views.ContratoMantenimientoCreateView.as_view(), name='contrato_create'),
    path('contratos/<int:pk>/', views.ContratoMantenimientoDetailView.as_view(), name='contrato_detail'),
    path('contratos/<int:pk>/editar/', views.ContratoMantenimientoUpdateView.as_view(), name='contrato_update'),
    
    # Actividades de Mantenimiento (Tabla consolidada)
    path('actividades/', views.ActividadMantenimientoListView.as_view(), name='actividad_list'),
    path('actividades/nueva/', views.ActividadMantenimientoCreateView.as_view(), name='actividad_create'),
    path('actividades/<int:pk>/', views.ActividadMantenimientoDetailView.as_view(), name='actividad_detail'),
    path('actividades/<int:pk>/editar/', views.ActividadMantenimientoUpdateView.as_view(), name='actividad_update'),
    
    # Informes de Mantenimiento
    path('informes/nuevo/', views.InformeMantenimientoCreateView.as_view(), name='informe_create'),
    path('informes/<int:pk>/', views.InformeMantenimientoDetailView.as_view(), name='informe_detail'),
    path('informes/<int:pk>/editar/', views.InformeMantenimientoUpdateView.as_view(), name='informe_update'),
    
    # Informes Específicos
    path('actividades/<int:actividad_id>/informe/seleccionar/', views.InformeEspecificoSeleccionView.as_view(), name='informe_seleccionar_tipo'),
    path('actividades/<int:actividad_id>/informe/unidad-paquete/nuevo/', views.InformeUnidadPaqueteCreateView.as_view(), name='informe_unidad_paquete_create'),
    path('informes/unidad-paquete/<int:pk>/', views.InformeUnidadPaqueteDetailView.as_view(), name='informe_unidad_paquete_detail'),
    path('informes/unidad-paquete/<int:pk>/editar/', views.InformeUnidadPaqueteUpdateView.as_view(), name='informe_unidad_paquete_update'),
    path('actividades/<int:actividad_id>/informe/coleccion-polvo/nuevo/', views.InformeColeccionPolvoCreateView.as_view(), name='informe_coleccion_polvo_create'),
    path('informes/coleccion-polvo/<int:pk>/', views.InformeColeccionPolvoDetailView.as_view(), name='informe_coleccion_polvo_detail'),
    path('informes/coleccion-polvo/<int:pk>/editar/', views.InformeColeccionPolvoUpdateView.as_view(), name='informe_coleccion_polvo_update'),
    
    # APIs
    path('api/equipos-cliente/<int:cliente_id>/', views.get_equipos_cliente, name='api_equipos_cliente'),
    path('api/rutinas-equipo/<int:hoja_vida_id>/', views.get_rutinas_equipo, name='api_rutinas_equipo'),
]