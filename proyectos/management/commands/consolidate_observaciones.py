from django.core.management.base import BaseCommand
from django.db import transaction
from proyectos.models import SeguimientoProyectoComite, SeguimientoServicioComite, ElementoExternoComite


class Command(BaseCommand):
    help = 'Consolida los campos de logros, dificultades, acciones y observaciones en el campo observaciones'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando consolidación de campos de observaciones...')
        
        # Consolidar SeguimientoProyectoComite
        self.consolidate_seguimiento_proyectos()
        
        # Consolidar SeguimientoServicioComite
        self.consolidate_seguimiento_servicios()
        
        # Consolidar ElementoExternoComite
        self.consolidate_elementos_externos()
        
        self.stdout.write(self.style.SUCCESS('Consolidación completada exitosamente'))
    
    @transaction.atomic
    def consolidate_seguimiento_proyectos(self):
        seguimientos = SeguimientoProyectoComite.objects.all()
        count = 0
        
        for seg in seguimientos:
            # Solo procesar si el campo observaciones está vacío pero hay datos en otros campos
            if not seg.observaciones and any([seg.logros_periodo, seg.dificultades, seg.acciones_requeridas]):
                observaciones_partes = []
                
                if seg.logros_periodo:
                    observaciones_partes.append(f"**Logros del Período:**\n{seg.logros_periodo}")
                
                if seg.dificultades:
                    observaciones_partes.append(f"**Dificultades Encontradas:**\n{seg.dificultades}")
                
                if seg.acciones_requeridas:
                    observaciones_partes.append(f"**Acciones Requeridas:**\n{seg.acciones_requeridas}")
                
                seg.observaciones = '\n\n'.join(observaciones_partes)
                seg.save(update_fields=['observaciones'])
                count += 1
        
        self.stdout.write(f'Consolidados {count} seguimientos de proyectos')
    
    @transaction.atomic
    def consolidate_seguimiento_servicios(self):
        seguimientos = SeguimientoServicioComite.objects.all()
        count = 0
        
        for seg in seguimientos:
            # Solo procesar si el campo observaciones está vacío pero hay datos en otros campos
            if not seg.observaciones and any([seg.logros_periodo, seg.dificultades, seg.acciones_requeridas]):
                observaciones_partes = []
                
                if seg.logros_periodo:
                    observaciones_partes.append(f"**Logros del Período:**\n{seg.logros_periodo}")
                
                if seg.dificultades:
                    observaciones_partes.append(f"**Dificultades Encontradas:**\n{seg.dificultades}")
                
                if seg.acciones_requeridas:
                    observaciones_partes.append(f"**Acciones Requeridas:**\n{seg.acciones_requeridas}")
                
                seg.observaciones = '\n\n'.join(observaciones_partes)
                seg.save(update_fields=['observaciones'])
                count += 1
        
        self.stdout.write(f'Consolidados {count} seguimientos de servicios')
    
    @transaction.atomic
    def consolidate_elementos_externos(self):
        elementos = ElementoExternoComite.objects.all()
        count = 0
        
        for elem in elementos:
            # Solo procesar si el campo observaciones está vacío pero hay datos en otros campos
            if not elem.observaciones and any([elem.logros_periodo, elem.dificultades, elem.acciones_requeridas]):
                observaciones_partes = []
                
                if elem.logros_periodo:
                    observaciones_partes.append(f"**Logros del Período:**\n{elem.logros_periodo}")
                
                if elem.dificultades:
                    observaciones_partes.append(f"**Dificultades Encontradas:**\n{elem.dificultades}")
                
                if elem.acciones_requeridas:
                    observaciones_partes.append(f"**Acciones Requeridas:**\n{elem.acciones_requeridas}")
                
                elem.observaciones = '\n\n'.join(observaciones_partes)
                elem.save(update_fields=['observaciones'])
                count += 1
        
        self.stdout.write(f'Consolidados {count} elementos externos')