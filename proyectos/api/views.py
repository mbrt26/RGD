from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from ..models import Actividad
import json

@require_http_methods(["GET"])
@csrf_exempt
def actividad_detail_api(request, pk):
    """API endpoint to get activity details"""
    try:
        actividad = get_object_or_404(Actividad, pk=pk)
        data = {
            'id': actividad.id,
            'actividad': actividad.actividad,
            'inicio': actividad.inicio.isoformat() if actividad.inicio else None,
            'fin': actividad.fin.isoformat() if actividad.fin else None,
            'duracion': actividad.duracion,
            'estado': actividad.estado,
            'avance': actividad.avance,
            'proyecto_id': actividad.proyecto_id,
            'proyecto_nombre': actividad.proyecto.nombre_proyecto if actividad.proyecto else '',
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
