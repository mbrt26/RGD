"""
Comando para probar la creación automática de solicitudes de servicio
cuando un Trato se marca como ganado.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from crm.models import Trato, Cliente
from servicios.models import SolicitudServicio
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Prueba la creación automática de solicitudes de servicio'

    def add_arguments(self, parser):
        parser.add_argument('trato_id', type=int, help='ID del Trato a marcar como ganado')
        parser.add_argument('--dry-run', action='store_true', help='Solo mostrar lo que se haría sin ejecutar')

    def handle(self, *args, **options):
        trato_id = options['trato_id']
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(f"{'[DRY RUN] ' if dry_run else ''}Probando signal para Trato ID: {trato_id}")
        
        try:
            # Obtener el trato
            trato = Trato.objects.get(id=trato_id)
            
            # Mostrar información actual
            self.stdout.write(f"\nInformación del Trato:")
            self.stdout.write(f"  - Número oferta: {trato.numero_oferta}")
            self.stdout.write(f"  - Estado actual: {trato.estado}")
            self.stdout.write(f"  - Tipo negociación: {trato.tipo_negociacion}")
            self.stdout.write(f"  - Centro costos: {trato.centro_costos or 'NO ASIGNADO'}")
            self.stdout.write(f"  - Cliente: {trato.cliente.nombre if trato.cliente else 'NO ASIGNADO'}")
            
            # Verificar requisitos
            if not trato.centro_costos:
                self.stdout.write(self.style.ERROR("\n❌ ERROR: El Trato no tiene centro de costos asignado"))
                self.stdout.write("El centro de costos es obligatorio para marcar como ganado")
                return
            
            if trato.estado == 'ganado':
                self.stdout.write(self.style.WARNING("\n⚠️  El Trato ya está marcado como ganado"))
                
                # Verificar si existe solicitud
                solicitudes = SolicitudServicio.objects.filter(
                    numero_orden__icontains=str(trato.numero_oferta)
                )
                if solicitudes.exists():
                    self.stdout.write(f"\nSolicitudes de servicio existentes:")
                    for sol in solicitudes:
                        self.stdout.write(f"  - {sol.numero_orden} (ID: {sol.id})")
                else:
                    self.stdout.write("\nNo hay solicitudes de servicio asociadas")
                return
            
            # Verificar tipo de negociación
            if trato.tipo_negociacion not in ['control', 'servicios']:
                self.stdout.write(self.style.WARNING(
                    f"\n⚠️  El tipo de negociación '{trato.tipo_negociacion}' no genera solicitud de servicio"
                ))
                self.stdout.write("Solo 'control' y 'servicios' generan solicitudes")
                return
            
            if dry_run:
                self.stdout.write(self.style.SUCCESS("\n✅ [DRY RUN] Todo listo para marcar como ganado"))
                self.stdout.write("Se crearía una solicitud de servicio")
                return
            
            # Marcar como ganado
            self.stdout.write(f"\nMarcando Trato como ganado...")
            estado_anterior = trato.estado
            trato.estado = 'ganado'
            trato.save()
            
            self.stdout.write(self.style.SUCCESS(f"✅ Trato marcado como ganado"))
            
            # Verificar si se creó la solicitud
            self.stdout.write("\nVerificando creación de solicitud...")
            solicitudes = SolicitudServicio.objects.filter(
                numero_orden__icontains=str(trato.numero_oferta),
                created__gte=timezone.now() - timezone.timedelta(minutes=1)
            )
            
            if solicitudes.exists():
                solicitud = solicitudes.first()
                self.stdout.write(self.style.SUCCESS(f"\n✅ Solicitud de servicio creada exitosamente:"))
                self.stdout.write(f"  - Número orden: {solicitud.numero_orden}")
                self.stdout.write(f"  - ID: {solicitud.id}")
                self.stdout.write(f"  - Tipo servicio: {solicitud.get_tipo_servicio_display()}")
                self.stdout.write(f"  - Estado: {solicitud.estado}")
            else:
                self.stdout.write(self.style.ERROR("\n❌ No se creó ninguna solicitud de servicio"))
                self.stdout.write("Revisa los logs para más detalles")
                
                # Buscar logs recientes
                self.stdout.write("\nConsejo: Ejecuta estos comandos para ver los logs:")
                self.stdout.write("  - Ver logs del signal: grep '[SIGNAL]' logs/django.log | tail -20")
                self.stdout.write("  - Ver logs de servicio: grep '[SERVICIO]' logs/django.log | tail -20")
                
        except Trato.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ No se encontró el Trato con ID: {trato_id}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error inesperado: {str(e)}"))
            logger.error(f"Error en test_servicio_signal: {str(e)}", exc_info=True)