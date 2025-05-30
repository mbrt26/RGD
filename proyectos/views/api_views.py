from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from proyectos.models import Proyecto

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def proyecto_detail_api(request, proyecto_id):
    """API endpoint para obtener detalles de un proyecto, incluyendo el centro de costos."""
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    
    # Devolver los datos relevantes del proyecto
    data = {
        'id': proyecto.id,
        'nombre_proyecto': proyecto.nombre_proyecto,
        'cliente': proyecto.cliente,
        'centro_costos': proyecto.centro_costos,
        'estado': proyecto.estado,
    }
    
    return JsonResponse(data)
