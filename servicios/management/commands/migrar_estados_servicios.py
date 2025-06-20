from django.core.management.base import BaseCommand
from servicios.models import SolicitudServicio


class Command(BaseCommand):
    help = 'Migra estados antiguos de solicitudes de servicio a los nuevos valores'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando migración de estados de solicitudes de servicio...\n')
        
        # Mapeo de estados antiguos a nuevos
        mapeo_estados = {
            'planeada': 'pendiente',
            'en_proceso': 'en_ejecucion',
            'ejecutada': 'finalizado',
            'cancelada': 'pendiente',  # Las canceladas las ponemos como pendientes
        }
        
        # Obtener todos los estados actuales
        estados_actuales = SolicitudServicio.objects.values_list('estado', flat=True).distinct()
        self.stdout.write(f'Estados encontrados en la BD: {list(estados_actuales)}')
        
        total_actualizadas = 0
        
        for estado_antiguo, estado_nuevo in mapeo_estados.items():
            solicitudes = SolicitudServicio.objects.filter(estado=estado_antiguo)
            count = solicitudes.count()
            
            if count > 0:
                solicitudes.update(estado=estado_nuevo)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Actualizadas {count} solicitudes de "{estado_antiguo}" a "{estado_nuevo}"'
                    )
                )
                total_actualizadas += count
            else:
                self.stdout.write(f'- No se encontraron solicitudes con estado "{estado_antiguo}"')
        
        # Verificar si hay estados que no están en el mapeo
        estados_nuevos_validos = ['pendiente', 'en_ejecucion', 'atrasado', 'finalizado']
        estados_finales = SolicitudServicio.objects.values_list('estado', flat=True).distinct()
        
        for estado in estados_finales:
            if estado not in estados_nuevos_validos:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Estado no reconocido encontrado: "{estado}"')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Migración completada. Total de solicitudes actualizadas: {total_actualizadas}')
        )
        
        # Mostrar resumen final
        self.stdout.write('\nResumen de estados después de la migración:')
        estados_resumen = SolicitudServicio.objects.values_list('estado', flat=True).distinct()
        for estado in estados_resumen:
            count = SolicitudServicio.objects.filter(estado=estado).count()
            self.stdout.write(f'- {estado}: {count} solicitudes')