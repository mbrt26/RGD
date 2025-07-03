from django.urls import path
from .views import (
    MejoraContinuaDashboardView,
    SolicitudMejoraListView,
    SolicitudMejoraDetailView,
    SolicitudMejoraCreateView,
    SolicitudMejoraUpdateView,
    SolicitudMejoraDeleteView,
    ComentarioCreateView,
    AdjuntoCreateView,
    MisSolicitudesView,
    SolicitudesAsignadasView,
    # MultipleFileUploadView,  # Temporarily disabled
    EliminarAdjuntoView,
)

app_name = 'mejora_continua'

urlpatterns = [
    # Dashboard
    path('', MejoraContinuaDashboardView.as_view(), name='dashboard'),
    
    # Solicitudes
    path('solicitudes/', SolicitudMejoraListView.as_view(), name='solicitud_list'),
    path('solicitudes/nueva/', SolicitudMejoraCreateView.as_view(), name='solicitud_create'),
    path('solicitudes/<int:pk>/', SolicitudMejoraDetailView.as_view(), name='solicitud_detail'),
    path('solicitudes/<int:pk>/editar/', SolicitudMejoraUpdateView.as_view(), name='solicitud_update'),
    path('solicitudes/<int:pk>/eliminar/', SolicitudMejoraDeleteView.as_view(), name='solicitud_delete'),
    
    # Comentarios y adjuntos
    path('solicitudes/<int:solicitud_pk>/comentarios/nuevo/', ComentarioCreateView.as_view(), name='comentario_create'),
    path('solicitudes/<int:solicitud_pk>/adjuntos/nuevo/', AdjuntoCreateView.as_view(), name='adjunto_create'),
    # path('solicitudes/<int:solicitud_pk>/adjuntos/multiples/', MultipleFileUploadView.as_view(), name='multiple_upload'),  # Temporarily disabled
    path('adjuntos/<int:pk>/eliminar/', EliminarAdjuntoView.as_view(), name='adjunto_delete'),
    
    # Vistas específicas
    path('mis-solicitudes/', MisSolicitudesView.as_view(), name='mis_solicitudes'),
    path('solicitudes-asignadas/', SolicitudesAsignadasView.as_view(), name='solicitudes_asignadas'),
]