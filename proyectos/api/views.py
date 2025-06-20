from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from ..models import Actividad
from crm.models import Trato, VersionCotizacion
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

@require_http_methods(["GET"])
@csrf_exempt
def cotizaciones_trato_api(request, trato_id):
    """API endpoint to get quotations for a specific trato"""
    try:
        trato = get_object_or_404(Trato, pk=trato_id)
        
        # Obtener todas las versiones de cotización para este trato
        cotizaciones = VersionCotizacion.objects.filter(
            cotizacion__trato=trato
        ).select_related('cotizacion').order_by('-version')
        
        data = []
        for cotizacion in cotizaciones:
            data.append({
                'id': cotizacion.id,
                'version': cotizacion.version,
                'valor': str(cotizacion.valor),
                'razon_cambio': cotizacion.razon_cambio,
                'fecha_creacion': cotizacion.fecha_creacion.strftime('%d/%m/%Y'),
                'archivo_url': cotizacion.archivo.url if cotizacion.archivo else None,
                'creado_por': cotizacion.creado_por.username if cotizacion.creado_por else 'Sistema'
            })
        
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
