from django.core.management.base import BaseCommand
from django.utils import timezone
from proyectos.models import Proyecto
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Calcula y actualiza automáticamente los retrasos de todos los proyectos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecuta el comando sin hacer cambios reales',
        )
        parser.add_argument(
            '--proyecto-id',
            type=int,
            help='Calcular retrasos solo para un proyecto específico',
        )
        parser.add_argument(
            '--solo-activos',
            action='store_true',
            help='Calcular solo para proyectos activos (no finalizados)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        proyecto_id = options.get('proyecto_id')
        solo_activos = options['solo_activos']

        self.stdout.write(
            self.style.SUCCESS('Iniciando cálculo de retrasos de proyectos...')
        )

        # Filtrar proyectos
        if proyecto_id:
            proyectos = Proyecto.objects.filter(id=proyecto_id)
            if not proyectos.exists():
                self.stdout.write(
                    self.style.ERROR(f'No se encontró el proyecto con ID {proyecto_id}')
                )
                return
        elif solo_activos:
            proyectos = Proyecto.objects.exclude(estado='finalizado')
        else:
            proyectos = Proyecto.objects.all()

        total_proyectos = proyectos.count()
        proyectos_atrasados = 0
        retraso_total_dias = 0

        self.stdout.write(f'Analizando {total_proyectos} proyectos...\n')

        for i, proyecto in enumerate(proyectos, 1):
            # Calcular métricas de retraso
            dias_retraso = proyecto.dias_retraso
            nivel_retraso = proyecto.nivel_retraso
            alertas = proyecto.get_alertas_retraso()
            
            # Estadísticas
            if dias_retraso > 0:
                proyectos_atrasados += 1
                retraso_total_dias += dias_retraso

            # Mostrar información del proyecto
            estado_color = self.get_color_by_status(proyecto.estado)
            self.stdout.write(
                f'[{i:3d}/{total_proyectos}] {proyecto.nombre_proyecto[:50]:<50} '
                f'({estado_color(proyecto.get_estado_display())})'
            )

            # Mostrar información de fechas
            hoy = timezone.now().date()
            self.stdout.write(f'           Inicio: {proyecto.fecha_inicio} | Fin: {proyecto.fecha_fin}')
            
            if proyecto.fecha_fin_real:
                self.stdout.write(f'           Fin Real: {proyecto.fecha_fin_real}')

            # Mostrar retrasos
            if dias_retraso > 0:
                nivel_color = self.get_color_by_delay_level(nivel_retraso)
                self.stdout.write(
                    f'           🔴 RETRASO: {nivel_color(f"{dias_retraso} días ({nivel_retraso})")}'
                )
            else:
                self.stdout.write('           ✅ Al día')

            # Mostrar alertas
            if alertas:
                for alerta in alertas:
                    alerta_color = self.get_color_by_alert_level(alerta['nivel'])
                    self.stdout.write(
                        f'           ⚠️  {alerta_color(alerta["mensaje"])}'
                    )

            # Mostrar avance vs tiempo
            tiempo_transcurrido = proyecto.porcentaje_tiempo_transcurrido
            avance_real = float(proyecto.avance)
            desviacion = proyecto.desviacion_cronograma
            
            if abs(desviacion) > 5:
                desv_color = self.style.ERROR if desviacion < -10 else self.style.WARNING
                self.stdout.write(
                    f'           📊 Avance: {avance_real:.1f}% | Tiempo: {tiempo_transcurrido:.1f}% | '
                    f'Desviación: {desv_color(f"{desviacion:+.1f}%")}'
                )
            else:
                self.stdout.write(
                    f'           📊 Avance: {avance_real:.1f}% | Tiempo: {tiempo_transcurrido:.1f}% | ✅ En tiempo'
                )

            self.stdout.write('')  # Línea en blanco

        # Resumen final
        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN DE RETRASOS ==='))
        self.stdout.write(f'Total de proyectos analizados: {total_proyectos}')
        self.stdout.write(f'Proyectos atrasados: {proyectos_atrasados}')
        self.stdout.write(f'Porcentaje de proyectos atrasados: {(proyectos_atrasados/total_proyectos*100):.1f}%')
        self.stdout.write(f'Total de días de retraso acumulados: {retraso_total_dias}')
        
        if proyectos_atrasados > 0:
            promedio_retraso = retraso_total_dias / proyectos_atrasados
            self.stdout.write(f'Promedio de días de retraso: {promedio_retraso:.1f}')

        # Proyectos más atrasados
        proyectos_criticos = [p for p in proyectos if p.nivel_retraso in ['severo', 'critico']]
        if proyectos_criticos:
            self.stdout.write(f'\n🚨 Proyectos críticos ({len(proyectos_criticos)}):')
            for proyecto in sorted(proyectos_criticos, key=lambda p: p.dias_retraso, reverse=True):
                self.stdout.write(
                    f'   • {proyecto.nombre_proyecto} - {proyecto.dias_retraso} días '
                    f'({proyecto.nivel_retraso})'
                )

        # Próximas fechas límite
        proximas_fechas = proyectos.filter(
            fecha_fin__gte=timezone.now().date(),
            fecha_fin__lte=timezone.now().date() + timedelta(days=7),
            estado__in=['pendiente', 'en_ejecucion']
        )
        
        if proximas_fechas.exists():
            self.stdout.write(f'\n📅 Proyectos con fecha límite próxima (7 días):')
            for proyecto in proximas_fechas.order_by('fecha_fin'):
                dias_restantes = (proyecto.fecha_fin - timezone.now().date()).days
                self.stdout.write(
                    f'   • {proyecto.nombre_proyecto} - {dias_restantes} días restantes '
                    f'(Fin: {proyecto.fecha_fin})'
                )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('\n[DRY RUN] No se realizaron cambios reales.')
            )

        self.stdout.write(self.style.SUCCESS('\n✅ Cálculo de retrasos completado.'))

    def get_color_by_status(self, estado):
        """Retorna el color apropiado según el estado del proyecto"""
        colores = {
            'pendiente': self.style.WARNING,
            'en_ejecucion': self.style.HTTP_INFO,
            'finalizado': self.style.SUCCESS,
        }
        return colores.get(estado, self.style.NOTICE)

    def get_color_by_delay_level(self, nivel):
        """Retorna el color apropiado según el nivel de retraso"""
        colores = {
            'leve': self.style.WARNING,
            'moderado': self.style.WARNING,
            'severo': self.style.ERROR,
            'critico': self.style.ERROR,
        }
        return colores.get(nivel, self.style.NOTICE)

    def get_color_by_alert_level(self, nivel):
        """Retorna el color apropiado según el nivel de alerta"""
        colores = {
            'leve': self.style.WARNING,
            'moderado': self.style.WARNING,
            'severo': self.style.ERROR,
            'critico': self.style.ERROR,
        }
        return colores.get(nivel, self.style.NOTICE)