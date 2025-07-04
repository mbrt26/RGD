from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from . import views
from .views import (
    ProyectoListView, ProyectoCreateView, ProyectoDetailView, ProyectoUpdateView,
    ProyectoDashboardView, ColaboradorListView, ColaboradorCreateView, 
    ColaboradorDetailView, ColaboradorUpdateView
)
from .views.colaborador.views import ColaboradorDeleteView
from .views.colaborador.views import ColaboradorImportView, ColaboradorPlantillaExcelView
from .views.debug_views import debug_template_loading
from .views.actividad.views import (
    ActividadListView, ActividadCreateView, ActividadDetailView, ActividadUpdateView,
    ActividadImportView, ActividadPlantillaExcelView, actividades_por_proyecto,
    actividad_bulk_delete
)
from .views.api_views import proyecto_detail_api
from .api.views import actividad_detail_api, cotizaciones_trato_api
from .views.recurso.views import (
    RecursoListView, RecursoCreateView, RecursoDetailView, RecursoUpdateView
)
from .views.bitacora.views import (
    BitacoraListView, BitacoraCreateView, BitacoraDetailView, BitacoraUpdateView,
    get_actividades_por_proyecto, eliminar_archivo_bitacora
)
from .views.entregable.views import (
    EntregaDocumentalListView, EntregaDocumentalCreateView,
    EntregaDocumentalDetailView, EntregaDocumentalUpdateView,
    GestionEntregablesView, EntregableProyectoUpdateView, cargar_entregables_proyecto,
    EntregablesDashboardView, ConfiguracionMasivaEntregablesView, 
    EntregablesFiltradosView, ReporteEntregablesView, EntregablePersonalizadoCreateView,
    CambiarTipoEntregableView, EntregablesChecklistView, EntregableImportView,
    EntregablePlantillaExcelView, entregable_proyecto_update_inline
)
from .views.comite.views import (
    ComiteListView, ComiteCreateView, ComiteDetailView, ComiteUpdateView,
    ComiteDeleteView, ComiteActaView, ComiteExportView, ComiteIniciarView, 
    ComiteFinalizarView, SeguimientoUpdateView, gestionar_participantes_comite, 
    duplicar_comite, ajax_buscar_colaboradores
)
from .views.prorroga.views import (
    ProrrogaListView, ProrrogaCreateView, ProrrogaDetailView, ProrrogaAprobacionView,
    ProrrogaDashboardView, prorroga_quick_approve, proyecto_tiene_prorrogas_pendientes
)

app_name = 'proyectos'

urlpatterns = [
    # Debug URL
    path('debug/template/', debug_template_loading, name='debug_template'),
    
    # API Endpoints
    path('api/proyectos/<int:proyecto_id>/', login_required(proyecto_detail_api), name='proyecto_detail_api'),
    path('api/actividades/<int:pk>/', login_required(actividad_detail_api), name='actividad_detail_api'),
    path('api/cotizaciones-trato/<int:trato_id>/', login_required(cotizaciones_trato_api), name='cotizaciones_trato_api'),
    
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
        path('importar/', login_required(ColaboradorImportView.as_view()), name='colaborador_import'),
        path('plantilla-excel/', login_required(ColaboradorPlantillaExcelView.as_view()), name='colaborador_plantilla_excel'),
        path('<int:id>/', login_required(ColaboradorDetailView.as_view()), name='colaborador_detail'),
        path('<int:id>/editar/', login_required(ColaboradorUpdateView.as_view()), name='colaborador_update'),
        path('<int:id>/eliminar/', login_required(ColaboradorDeleteView.as_view()), name='colaborador_delete'),
    ])),

    # Actividades
    path('actividades/', include([
        path('', login_required(ActividadListView.as_view()), name='actividad_list'),
        path('nueva/', login_required(ActividadCreateView.as_view()), name='actividad_create'),
        path('importar/', login_required(ActividadImportView.as_view()), name='actividad_import'),
        path('plantilla-excel/', login_required(ActividadPlantillaExcelView.as_view()), name='actividad_plantilla_excel'),
        path('por-proyecto/<int:proyecto_id>/', login_required(actividades_por_proyecto), name='actividades_por_proyecto'),
        path('eliminar-multiples/', login_required(actividad_bulk_delete), name='actividad_bulk_delete'),
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
        path('archivo/<int:archivo_id>/eliminar/', login_required(eliminar_archivo_bitacora), name='eliminar_archivo_bitacora'),
        path('api/actividades/<int:proyecto_id>/', login_required(get_actividades_por_proyecto), name='get_actividades_por_proyecto'),
    ])),

    # Entregables
    path('entregables/', include([
        # Vista principal - Gestión de entregables del proyecto
        path('', login_required(GestionEntregablesView.as_view()), name='entregable_list'),
        path('gestion/', login_required(GestionEntregablesView.as_view()), name='gestion_entregables'),
        
        # Dashboard y vistas adicionales
        path('dashboard/', login_required(EntregablesDashboardView.as_view()), name='entregables_dashboard'),
        path('filtrados/', login_required(EntregablesFiltradosView.as_view()), name='entregables_filtrados'),
        path('configuracion-masiva/', login_required(ConfiguracionMasivaEntregablesView.as_view()), name='configuracion_masiva_entregables'),
        path('reporte/', login_required(ReporteEntregablesView.as_view()), name='reporte_entregables'),
        path('importar/', login_required(EntregableImportView.as_view()), name='entregable_import'),
        path('plantilla-excel/', login_required(EntregablePlantillaExcelView.as_view()), name='entregable_plantilla_excel'),
        
        # Operaciones específicas de entregables
        path('proyecto/<int:proyecto_id>/cargar/', login_required(cargar_entregables_proyecto), name='cargar_entregables_proyecto'),
        path('proyecto/<int:proyecto_id>/personalizado/nuevo/', login_required(EntregablePersonalizadoCreateView.as_view()), name='entregable_personalizado_create'),
        path('proyecto/<int:proyecto_id>/cambiar-tipo/', login_required(CambiarTipoEntregableView.as_view()), name='cambiar_tipo_entregable'),
        path('proyecto/<int:proyecto_id>/checklist/', login_required(EntregablesChecklistView.as_view()), name='entregables_checklist'),
        path('proyecto-entregable/<int:pk>/editar/', login_required(EntregableProyectoUpdateView.as_view()), name='entregable_proyecto_update'),
        path('proyecto-entregable/<int:pk>/update-inline/', login_required(entregable_proyecto_update_inline), name='entregable_proyecto_update_inline'),
        
        # Entregables documentales (legacy) - movidos a subcarpeta
        path('documentales/', login_required(EntregaDocumentalListView.as_view()), name='entregable_documental_list'),
        path('documentales/nuevo/', login_required(EntregaDocumentalCreateView.as_view()), name='entregable_create'),
        path('documentales/<int:pk>/', login_required(EntregaDocumentalDetailView.as_view()), name='entregable_detail'),
        path('documentales/<int:pk>/editar/', login_required(EntregaDocumentalUpdateView.as_view()), name='entregable_update'),
    ])),
    
    # Comités de Proyectos
    path('comite/', include([
        path('', login_required(ComiteListView.as_view()), name='comite_list'),
        path('nuevo/', login_required(ComiteCreateView.as_view()), name='comite_create'),
        path('<int:pk>/', login_required(ComiteDetailView.as_view()), name='comite_detail'),
        path('<int:pk>/editar/', login_required(ComiteUpdateView.as_view()), name='comite_update'),
        path('<int:pk>/acta/', login_required(ComiteActaView.as_view()), name='comite_acta'),
        path('<int:pk>/exportar/', login_required(ComiteExportView.as_view()), name='comite_export'),
        path('<int:pk>/iniciar/', login_required(ComiteIniciarView.as_view()), name='comite_iniciar'),
        path('<int:pk>/finalizar/', login_required(ComiteFinalizarView.as_view()), name='comite_finalizar'),
        path('<int:pk>/eliminar/', login_required(ComiteDeleteView.as_view()), name='comite_delete'),
        path('<int:comite_id>/participantes/', login_required(gestionar_participantes_comite), name='gestionar_participantes_comite'),
        path('<int:comite_id>/duplicar/', login_required(duplicar_comite), name='duplicar_comite'),
        path('seguimiento/<int:pk>/editar/', login_required(SeguimientoUpdateView.as_view()), name='seguimiento_update'),
        path('ajax/buscar-colaboradores/', login_required(ajax_buscar_colaboradores), name='ajax_buscar_colaboradores'),
    ])),
    
    # Prórrogas de Proyectos
    path('prorrogas/', include([
        path('', login_required(ProrrogaListView.as_view()), name='prorroga_list'),
        path('dashboard/', login_required(ProrrogaDashboardView.as_view()), name='prorroga_dashboard'),
        path('proyecto/<int:proyecto_id>/nueva/', login_required(ProrrogaCreateView.as_view()), name='prorroga_create'),
        path('<int:pk>/', login_required(ProrrogaDetailView.as_view()), name='prorroga_detail'),
        path('<int:pk>/aprobar/', login_required(ProrrogaAprobacionView.as_view()), name='prorroga_approve'),
        path('<int:pk>/quick-approve/', login_required(prorroga_quick_approve), name='prorroga_quick_approve'),
        path('api/proyecto/<int:proyecto_id>/pendientes/', login_required(proyecto_tiene_prorrogas_pendientes), name='proyecto_prorrogas_pendientes'),
    ])),
]