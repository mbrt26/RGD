from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views
from .views import (
    ProyectoListView, ProyectoCreateView, ProyectoDetailView, ProyectoUpdateView,
    ProyectoDashboardView, ColaboradorListView, ColaboradorCreateView, 
    ColaboradorDetailView, ColaboradorUpdateView
)
from .views.debug_views import debug_template_loading
from .views.actividad.views import (
    ActividadListView, ActividadCreateView, ActividadDetailView, ActividadUpdateView,
    actividades_por_proyecto
)
from .views.recurso.views import (
    RecursoListView, RecursoCreateView, RecursoDetailView, RecursoUpdateView
)
from .views.bitacora.views import (
    BitacoraListView, BitacoraCreateView, BitacoraDetailView, BitacoraUpdateView,
    get_actividades_por_proyecto
)
from .views.entregable.views import (
    EntregaDocumentalListView, EntregaDocumentalCreateView,
    EntregaDocumentalDetailView, EntregaDocumentalUpdateView,
    GestionEntregablesView, EntregableProyectoUpdateView, cargar_entregables_proyecto
)

app_name = 'proyectos'

urlpatterns = [
    # Debug URL
    path('debug/template/', debug_template_loading, name='debug_template'),
    
    # Dashboard
    path('', login_required(ProyectoDashboardView.as_view()), name='dashboard'),
    
    # Projects
    path('proyectos/', include([
        path('', login_required(ProyectoListView.as_view()), name='proyecto_list'),
        path('nuevo/', login_required(ProyectoCreateView.as_view()), name='proyecto_create'),
        path('<int:pk>/', include([
            path('', login_required(ProyectoDetailView.as_view()), name='proyecto_detail'),
            path('editar/', login_required(ProyectoUpdateView.as_view()), name='proyecto_update'),
        ])),
    ])),
    
    # Colaboradores
    path('colaboradores/', include([
        path('', login_required(ColaboradorListView.as_view()), name='colaborador_list'),
        path('nuevo/', login_required(ColaboradorCreateView.as_view()), name='colaborador_create'),
        path('<int:id>/', login_required(ColaboradorDetailView.as_view()), name='colaborador_detail'),
        path('<int:id>/editar/', login_required(ColaboradorUpdateView.as_view()), name='colaborador_update'),
    ])),

    # Actividades
    path('actividades/', include([
        path('', login_required(ActividadListView.as_view()), name='actividad_list'),
        path('nueva/', login_required(ActividadCreateView.as_view()), name='actividad_create'),
        path('por-proyecto/<int:proyecto_id>/', login_required(actividades_por_proyecto), name='actividades_por_proyecto'),
        path('<int:pk>/editar/', login_required(ActividadUpdateView.as_view()), name='actividad_update'),
        path('<int:pk>/', login_required(ActividadDetailView.as_view()), name='actividad_detail'),
    ])),

    # Recursos
    path('recursos/', include([
        path('', login_required(RecursoListView.as_view()), name='recurso_list'),
        path('nuevo/', login_required(RecursoCreateView.as_view()), name='recurso_create'),
        path('<int:pk>/', login_required(RecursoDetailView.as_view()), name='recurso_detail'),
        path('<int:pk>/editar/', login_required(RecursoUpdateView.as_view()), name='recurso_update'),
    ])),

    # Bitácora 
    path('bitacora/', include([
        path('', login_required(BitacoraListView.as_view()), name='bitacora_list'),
        path('nueva/', login_required(BitacoraCreateView.as_view()), name='bitacora_create'),
        path('<int:pk>/', login_required(BitacoraDetailView.as_view()), name='bitacora_detail'),
        path('<int:pk>/editar/', login_required(BitacoraUpdateView.as_view()), name='bitacora_update'),
        path('api/actividades/<int:proyecto_id>/', login_required(get_actividades_por_proyecto), name='get_actividades_por_proyecto'),
    ])),

    # Entregables
    path('entregables/', include([
        path('', login_required(EntregaDocumentalListView.as_view()), name='entregable_list'),
        path('nuevo/', login_required(EntregaDocumentalCreateView.as_view()), name='entregable_create'),
        path('<int:pk>/', login_required(EntregaDocumentalDetailView.as_view()), name='entregable_detail'),
        path('<int:pk>/editar/', login_required(EntregaDocumentalUpdateView.as_view()), name='entregable_update'),
        # Nuevas rutas para gestión de entregables del proyecto
        path('gestion/', login_required(GestionEntregablesView.as_view()), name='gestion_entregables'),
        path('proyecto/<int:proyecto_id>/cargar/', login_required(cargar_entregables_proyecto), name='cargar_entregables_proyecto'),
        path('proyecto-entregable/<int:pk>/editar/', login_required(EntregableProyectoUpdateView.as_view()), name='entregable_proyecto_update'),
    ])),
]