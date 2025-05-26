from .proyecto.views import (
    ProyectoListView, ProyectoCreateView, ProyectoDetailView, 
    ProyectoUpdateView, ProyectoDashboardView
)
from .colaborador.views import (
    ColaboradorListView, ColaboradorCreateView, 
    ColaboradorDetailView, ColaboradorUpdateView
)
from .recurso.views import (
    RecursoListView, RecursoCreateView, RecursoDetailView, RecursoUpdateView
)
from .bitacora.views import (
    BitacoraListView, BitacoraCreateView, BitacoraDetailView, BitacoraUpdateView
)
from .entregable.views import (
    EntregaDocumentalListView, EntregaDocumentalCreateView,
    EntregaDocumentalDetailView, EntregaDocumentalUpdateView
)

__all__ = [
    'ProyectoListView', 'ProyectoCreateView', 'ProyectoDetailView',
    'ProyectoUpdateView', 'ProyectoDashboardView',
    'ColaboradorListView', 'ColaboradorCreateView',
    'ColaboradorDetailView', 'ColaboradorUpdateView',
    'RecursoListView', 'RecursoCreateView', 'RecursoDetailView', 'RecursoUpdateView',
    'BitacoraListView', 'BitacoraCreateView', 'BitacoraDetailView', 'BitacoraUpdateView',
    'EntregaDocumentalListView', 'EntregaDocumentalCreateView',
    'EntregaDocumentalDetailView', 'EntregaDocumentalUpdateView'
]