from django.core.management.base import BaseCommand
from proyectos.models import Proyecto


class Command(BaseCommand):
    help = 'Actualiza el % avance real de todos los proyectos basado en días de actividades'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué cambios se harían sin aplicarlos',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write('🔍 MODO PRUEBA - No se aplicarán cambios')
        
        self.stdout.write('📊 Actualizando avances de proyectos...')
        
        proyectos = Proyecto.objects.all()
        total_proyectos = proyectos.count()
        proyectos_actualizados = 0
        
        for proyecto in proyectos:
            avance_anterior = proyecto.avance
            nuevo_avance = proyecto.calcular_avance_real()
            
            if avance_anterior != nuevo_avance:
                if not dry_run:
                    proyecto.avance = nuevo_avance
                    proyecto.save(update_fields=['avance'])
                
                proyectos_actualizados += 1
                
                self.stdout.write(
                    f'  ✅ {proyecto.nombre_proyecto[:50]}... '
                    f'({avance_anterior}% → {nuevo_avance}%)'
                )
            else:
                self.stdout.write(
                    f'  ⏭️  {proyecto.nombre_proyecto[:50]}... '
                    f'(sin cambios: {avance_anterior}%)'
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n📋 RESUMEN (MODO PRUEBA):\n'
                    f'   📊 Total proyectos: {total_proyectos}\n'
                    f'   🔄 Proyectos que cambiarían: {proyectos_actualizados}\n'
                    f'   ⏭️  Proyectos sin cambios: {total_proyectos - proyectos_actualizados}\n'
                    f'\n💡 Ejecuta sin --dry-run para aplicar los cambios'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 ACTUALIZACIÓN COMPLETADA:\n'
                    f'   📊 Total proyectos: {total_proyectos}\n'
                    f'   ✅ Proyectos actualizados: {proyectos_actualizados}\n'
                    f'   ⏭️  Proyectos sin cambios: {total_proyectos - proyectos_actualizados}'
                )
            )