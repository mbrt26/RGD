from django.urls import path
from colaboradores.views import (
    ColaboradorListView,
    ColaboradorCreateView,
    ColaboradorDetailView,
    ColaboradorUpdateView,
    ColaboradorDeleteView,
    ColaboradorImportView,
    ColaboradorPlantillaExcelView
)

app_name = 'colaboradores'

urlpatterns = [
    # Colaboradores
    path('', ColaboradorListView.as_view(), name='list'),
    path('nuevo/', ColaboradorCreateView.as_view(), name='create'),
    path('importar/', ColaboradorImportView.as_view(), name='import'),
    path('plantilla-excel/', ColaboradorPlantillaExcelView.as_view(), name='plantilla_excel'),
    path('<int:id>/', ColaboradorDetailView.as_view(), name='detail'),
    path('<int:id>/editar/', ColaboradorUpdateView.as_view(), name='update'),
    path('<int:id>/eliminar/', ColaboradorDeleteView.as_view(), name='delete'),
]