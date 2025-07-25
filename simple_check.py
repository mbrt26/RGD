import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings_cloudrun')
django.setup()

from crm.models import Trato
from servicios.models import SolicitudServicio

# Buscar trato 6981
try:
    trato = Trato.objects.get(numero_oferta='6981')
    print(f"TRATO ENCONTRADO: #{trato.numero_oferta}")
    print(f"Estado: {trato.estado}")
    print(f"Tipo: {trato.tipo_negociacion}")
    print(f"Cliente: {trato.cliente.nombre if trato.cliente else 'Sin cliente'}")
    print(f"Centro costos: '{trato.centro_costos}'")
    
    # Verificar solicitudes
    sols = SolicitudServicio.objects.filter(trato_origen=trato)
    print(f"Solicitudes: {sols.count()}")
    
    if trato.estado == 'ganado' and trato.tipo_negociacion in ['servicios', 'control'] and not sols.exists():
        from crm.signals import crear_solicitud_servicio_desde_trato
        success, msg, sol = crear_solicitud_servicio_desde_trato(trato)
        print(f"Creación: {'ÉXITO' if success else 'ERROR'}")
        print(msg)
        
except Trato.DoesNotExist:
    print("TRATO 6981 NO ENCONTRADO")
    # Mostrar algunos recientes
    recientes = Trato.objects.all().order_by('-id')[:5]
    for t in recientes:
        print(f"  #{t.numero_oferta} - {t.estado}")