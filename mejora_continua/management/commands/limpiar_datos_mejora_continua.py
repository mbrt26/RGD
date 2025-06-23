from django.core.management.base import BaseCommand
from mejora_continua.models import SolicitudMejora, ComentarioSolicitud, AdjuntoSolicitud

class Command(BaseCommand):
    help = 'Elimina todos los datos del módulo de mejora continua'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma que quieres eliminar todos los datos'
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Este comando eliminará TODOS los datos del módulo de mejora continua.'
                )
            )
            self.stdout.write(
                'Para confirmar, ejecuta: python manage.py limpiar_datos_mejora_continua --confirmar'
            )
            return

        # Contar datos antes de eliminar
        solicitudes_count = SolicitudMejora.objects.count()
        comentarios_count = ComentarioSolicitud.objects.count()
        adjuntos_count = AdjuntoSolicitud.objects.count()

        # Eliminar todos los datos
        AdjuntoSolicitud.objects.all().delete()
        ComentarioSolicitud.objects.all().delete()
        SolicitudMejora.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Datos eliminados exitosamente:'
            )
        )
        self.stdout.write(f'   - {solicitudes_count} solicitudes eliminadas')
        self.stdout.write(f'   - {comentarios_count} comentarios eliminados')
        self.stdout.write(f'   - {adjuntos_count} adjuntos eliminados')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🧹 Base de datos del módulo de mejora continua limpiada.'
            )
        )