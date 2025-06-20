from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import random

from proyectos.models import (
    ComiteProyecto, ParticipanteComite, SeguimientoProyectoComite,
    Proyecto, Colaborador
)
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos de prueba para el módulo de comités de proyectos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--comites',
            type=int,
            default=8,
            help='Número de comités a crear (default: 8)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Eliminar datos existentes de comités antes de crear nuevos'
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('Eliminando datos existentes de comités...')
            ComiteProyecto.objects.all().delete()
            self.stdout.write(self.style.WARNING('Datos de comités eliminados.'))

        # Verificar que existan proyectos y colaboradores
        proyectos = Proyecto.objects.all()
        colaboradores = Colaborador.objects.all()
        users = User.objects.all()

        if not proyectos.exists():
            self.stdout.write(
                self.style.ERROR('No hay proyectos disponibles. Ejecute primero create_test_projects.')
            )
            return

        if not colaboradores.exists():
            self.stdout.write(
                self.style.ERROR('No hay colaboradores disponibles. Debe crear colaboradores primero.')
            )
            return

        self.stdout.write(f'Creando {options["comites"]} comités de prueba...')
        
        with transaction.atomic():
            comites_creados = self.create_comites(options['comites'], proyectos, colaboradores, users)
            
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon exitosamente {comites_creados} comités con sus seguimientos.')
        )
        
        # Mostrar resumen
        self.mostrar_resumen()

    def create_comites(self, num_comites, proyectos, colaboradores, users):
        """Crear comités de prueba"""
        comites_creados = 0
        
        # Tipos de comités y nombres base
        tipos_comites = ['semanal', 'mensual', 'extraordinario', 'revision']
        lugares = [
            'Sala de Juntas Principal',
            'Sala de Conferencias',
            'Microsoft Teams',
            'Google Meet',
            'Sala de Reuniones Norte',
            'Zoom - Virtual',
            'Sala Ejecutiva',
            'Centro de Conferencias'
        ]
        
        # Estados de comités
        estados_comites = ['programado', 'en_curso', 'finalizado', 'cancelado']
        
        # Crear comités desde hace 3 meses hasta 1 mes en el futuro
        fecha_inicio = timezone.now() - timedelta(days=90)
        fecha_fin = timezone.now() + timedelta(days=30)
        
        for i in range(num_comites):
            # Calcular fecha del comité
            dias_desde_inicio = (fecha_fin - fecha_inicio).days
            fecha_comite = fecha_inicio + timedelta(
                days=random.randint(0, dias_desde_inicio),
                hours=random.choice([9, 10, 14, 15, 16]),
                minutes=random.choice([0, 30])
            )
            
            # Determinar estado basado en la fecha
            ahora = timezone.now()
            if fecha_comite > ahora + timedelta(days=1):
                estado = 'programado'
            elif fecha_comite > ahora - timedelta(hours=2) and fecha_comite < ahora + timedelta(hours=2):
                estado = 'en_curso'
            elif fecha_comite < ahora - timedelta(days=7):
                estado = 'finalizado' if random.random() < 0.9 else 'cancelado'
            else:
                estado = 'finalizado' if random.random() < 0.8 else 'programado'
            
            # Tipo de comité
            tipo_comite = random.choice(tipos_comites)
            
            # Generar nombre del comité
            if tipo_comite == 'semanal':
                semana = fecha_comite.isocalendar()[1]
                nombre = f"Comité Semanal - Semana {semana}/{fecha_comite.year}"
            elif tipo_comite == 'mensual':
                nombre = f"Comité Mensual - {fecha_comite.strftime('%B %Y').title()}"
            elif tipo_comite == 'extraordinario':
                nombre = f"Comité Extraordinario - {fecha_comite.strftime('%d/%m/%Y')}"
            else:
                nombre = f"Comité de Revisión - {fecha_comite.strftime('%d/%m/%Y')}"
            
            # Seleccionar coordinador
            coordinador = random.choice(colaboradores) if colaboradores.exists() else None
            
            # Generar agenda
            agenda = self.generar_agenda(tipo_comite)
            
            # Crear comité
            comite = ComiteProyecto.objects.create(
                nombre=nombre,
                fecha_comite=fecha_comite,
                tipo_comite=tipo_comite,
                lugar=random.choice(lugares),
                coordinador=coordinador,
                agenda=agenda,
                observaciones=self.generar_observaciones(estado),
                estado=estado,
                creado_por=random.choice(users) if users.exists() else None
            )
            
            # Crear participantes
            self.crear_participantes(comite, colaboradores)
            
            # Crear seguimientos de proyectos
            self.crear_seguimientos(comite, proyectos, colaboradores)
            
            comites_creados += 1
            
            self.stdout.write(f'  ✓ {nombre} ({estado})')
        
        return comites_creados

    def crear_participantes(self, comite, colaboradores):
        """Crear participantes para un comité"""
        if not colaboradores.exists():
            return
            
        # Seleccionar entre 3 y 8 participantes
        num_participantes = random.randint(3, min(8, colaboradores.count()))
        participantes_seleccionados = random.sample(list(colaboradores), num_participantes)
        
        tipos_participacion = ['obligatorio', 'opcional', 'invitado']
        estados_asistencia = ['pendiente', 'confirmado', 'ausente', 'presente']
        roles = [
            'Coordinador', 'Presentador', 'Revisor', 'Observador', 
            'Director de Proyecto', 'Ingeniero Residente', 'Analista',
            'Supervisor', 'Gerente'
        ]
        
        for i, colaborador in enumerate(participantes_seleccionados):
            # El coordinador siempre es obligatorio
            if colaborador == comite.coordinador:
                tipo_participacion = 'obligatorio'
                estado_asistencia = 'presente' if comite.estado == 'finalizado' else 'confirmado'
                rol = 'Coordinador'
            else:
                tipo_participacion = random.choice(tipos_participacion)
                
                # Estado de asistencia basado en el estado del comité
                if comite.estado == 'finalizado':
                    estado_asistencia = 'presente' if random.random() < 0.85 else 'ausente'
                elif comite.estado == 'en_curso':
                    estado_asistencia = 'presente' if random.random() < 0.7 else 'confirmado'
                elif comite.estado == 'cancelado':
                    estado_asistencia = 'ausente'
                else:
                    estado_asistencia = 'confirmado' if random.random() < 0.7 else 'pendiente'
                
                rol = random.choice(roles)
            
            # Fecha de confirmación si está confirmado
            fecha_confirmacion = None
            if estado_asistencia in ['confirmado', 'presente']:
                fecha_confirmacion = comite.fecha_comite - timedelta(
                    days=random.randint(1, 7),
                    hours=random.randint(0, 23)
                )
            
            ParticipanteComite.objects.create(
                comite=comite,
                colaborador=colaborador,
                tipo_participacion=tipo_participacion,
                estado_asistencia=estado_asistencia,
                rol_en_comite=rol,
                fecha_confirmacion=fecha_confirmacion,
                observaciones=self.generar_observaciones_participante(estado_asistencia)
            )

    def crear_seguimientos(self, comite, proyectos, colaboradores):
        """Crear seguimientos de proyectos para un comité"""
        # Seleccionar proyectos activos o recientemente finalizados
        proyectos_candidatos = proyectos.filter(
            estado__in=['pendiente', 'en_ejecucion', 'finalizado']
        )
        
        if not proyectos_candidatos.exists():
            return
        
        # Seleccionar entre 2 y 6 proyectos para el seguimiento
        num_proyectos = random.randint(2, min(6, proyectos_candidatos.count()))
        proyectos_seleccionados = random.sample(list(proyectos_candidatos), num_proyectos)
        
        estados_seguimiento = ['verde', 'amarillo', 'rojo', 'azul']
        
        for i, proyecto in enumerate(proyectos_seleccionados):
            # Determinar estado de seguimiento basado en el estado del proyecto
            if proyecto.estado == 'finalizado':
                estado_seguimiento = 'verde' if random.random() < 0.8 else 'azul'
            elif proyecto.esta_atrasado:
                estado_seguimiento = 'amarillo' if random.random() < 0.6 else 'rojo'
            else:
                estado_seguimiento = 'verde' if random.random() < 0.7 else 'amarillo'
            
            # Avance reportado (puede ser diferente al avance real del proyecto)
            avance_base = float(proyecto.avance)
            variacion = random.uniform(-5, 5)  # Variación de ±5%
            avance_reportado = max(0, min(100, avance_base + variacion))
            
            # Avance anterior (del comité anterior)
            avance_anterior = None
            if random.choice([True, False]):  # 50% de posibilidades de tener avance anterior
                avance_anterior = max(0, avance_reportado - random.uniform(0, 15))
            
            # Responsable del reporte
            responsable_reporte = None
            if colaboradores.exists():
                # Preferir director o ingeniero del proyecto
                if proyecto.director_proyecto:
                    responsable_reporte = proyecto.director_proyecto
                elif proyecto.ingeniero_residente:
                    responsable_reporte = proyecto.ingeniero_residente
                else:
                    responsable_reporte = random.choice(colaboradores)
            
            # Fecha próximo hito
            fecha_proximo_hito = None
            if random.choice([True, False]):  # 50% de posibilidades
                fecha_proximo_hito = comite.fecha_comite.date() + timedelta(
                    days=random.randint(7, 30)
                )
            
            # Presupuesto ejecutado
            presupuesto_ejecutado = None
            if proyecto.presupuesto > 0:
                presupuesto_ejecutado = float(proyecto.gasto_real) + random.uniform(-10000, 50000)
                presupuesto_ejecutado = max(0, presupuesto_ejecutado)
            
            # Requiere decisión
            requiere_decision = random.random() < 0.2
            decision_tomada = ""
            if requiere_decision:
                decision_tomada = self.generar_decision()
            
            SeguimientoProyectoComite.objects.create(
                comite=comite,
                proyecto=proyecto,
                estado_seguimiento=estado_seguimiento,
                avance_reportado=avance_reportado,
                avance_anterior=avance_anterior,
                logros_periodo=self.generar_logros(proyecto, estado_seguimiento),
                dificultades=self.generar_dificultades(estado_seguimiento),
                acciones_requeridas=self.generar_acciones(estado_seguimiento),
                responsable_reporte=responsable_reporte,
                fecha_proximo_hito=fecha_proximo_hito,
                presupuesto_ejecutado=presupuesto_ejecutado,
                observaciones=self.generar_observaciones_seguimiento(estado_seguimiento),
                orden_presentacion=i + 1,
                tiempo_asignado=random.randint(5, 20),
                requiere_decision=requiere_decision,
                decision_tomada=decision_tomada
            )

    def generar_agenda(self, tipo_comite):
        """Generar agenda según el tipo de comité"""
        agendas = {
            'semanal': """1. Apertura y verificación de quórum
2. Revisión de acuerdos del comité anterior
3. Seguimiento de proyectos en ejecución
4. Alertas y proyectos críticos
5. Nuevos proyectos y asignaciones
6. Temas varios
7. Cierre y próxima reunión""",
            
            'mensual': """1. Apertura del comité mensual
2. Revisión ejecutiva de indicadores
3. Estado general de la cartera de proyectos
4. Análisis financiero y presupuestario
5. Revisión de cronogramas y entregas
6. Decisiones estratégicas
7. Planificación del próximo mes
8. Cierre""",
            
            'extraordinario': """1. Apertura del comité extraordinario
2. Presentación del caso crítico
3. Análisis de alternativas
4. Toma de decisiones
5. Definición de acciones inmediatas
6. Responsables y fechas límite
7. Cierre y seguimiento""",
            
            'revision': """1. Apertura del comité de revisión
2. Metodología de revisión
3. Revisión detallada por proyecto
4. Identificación de lecciones aprendidas
5. Recomendaciones de mejora
6. Plan de implementación
7. Cierre y documentación"""
        }
        
        return agendas.get(tipo_comite, agendas['semanal'])

    def generar_observaciones(self, estado):
        """Generar observaciones según el estado del comité"""
        observaciones = {
            'programado': [
                "Comité programado según cronograma establecido.",
                "Se enviará la agenda 24 horas antes de la reunión.",
                "Confirmar asistencia con el coordinador.",
                "Revisar documentos previos en la carpeta compartida."
            ],
            'en_curso': [
                "Comité actualmente en desarrollo.",
                "Sesión en progreso según agenda establecida.",
                "Participación activa de todos los miembros."
            ],
            'finalizado': [
                "Comité finalizado exitosamente con todos los objetivos cumplidos.",
                "Se generó acta con decisiones y compromisos.",
                "Próximo seguimiento programado para la siguiente semana.",
                "Excelente participación de todos los miembros del equipo.",
                "Se lograron acuerdos importantes para el avance de los proyectos."
            ],
            'cancelado': [
                "Comité cancelado por falta de quórum.",
                "Reagendado por conflictos de agenda de participantes clave.",
                "Cancelado por situación de fuerza mayor.",
                "Aplazado por falta de información crítica."
            ]
        }
        
        return random.choice(observaciones.get(estado, [""]))

    def generar_observaciones_participante(self, estado_asistencia):
        """Generar observaciones para participantes"""
        if estado_asistencia == 'ausente':
            return random.choice([
                "Conflicto de agenda reportado con anticipación.",
                "Viaje de trabajo programado.",
                "Situación personal justificada.",
                "Representado por su suplente."
            ])
        return ""

    def generar_logros(self, proyecto, estado_seguimiento):
        """Generar logros según el proyecto y estado"""
        logros_base = [
            f"Avance significativo en {proyecto.nombre_proyecto}",
            f"Completadas actividades críticas del cronograma",
            f"Resolución de obstáculos técnicos importantes",
            f"Aprobación de entregables por parte del cliente",
            f"Optimización de procesos en {proyecto.cliente}",
            f"Cumplimiento de hitos establecidos",
            f"Mejora en indicadores de calidad",
            f"Reducción de tiempos en procesos críticos"
        ]
        
        if estado_seguimiento == 'verde':
            logros_adicionales = [
                "Proyecto avanza según lo planificado sin contratiempos.",
                "Excelente coordinación con el cliente y equipo de trabajo.",
                "Anticipación en algunas actividades del cronograma."
            ]
        elif estado_seguimiento == 'amarillo':
            logros_adicionales = [
                "A pesar de algunos obstáculos, se mantiene el rumbo general.",
                "Implementación de medidas correctivas exitosas.",
                "Recuperación gradual del cronograma."
            ]
        elif estado_seguimiento == 'rojo':
            logros_adicionales = [
                "Identificación temprana de problemas críticos.",
                "Movilización de recursos adicionales para recuperación.",
                "Comunicación transparente con stakeholders."
            ]
        else:  # azul
            logros_adicionales = [
                "Pausa planificada según cronograma acordado.",
                "Preparación de documentación durante pausa.",
                "Mantenimiento de equipo y recursos."
            ]
        
        return random.choice(logros_base + logros_adicionales)

    def generar_dificultades(self, estado_seguimiento):
        """Generar dificultades según el estado"""
        if estado_seguimiento == 'verde':
            return random.choice([
                "",
                "Ninguna dificultad significativa reportada.",
                "Pequeños ajustes menores en coordinación de equipos."
            ])
        elif estado_seguimiento == 'amarillo':
            return random.choice([
                "Retrasos menores en entrega de materiales por parte del proveedor.",
                "Coordinación con horarios del cliente requiere ajustes.",
                "Condiciones climáticas han afectado algunas actividades externas.",
                "Disponibilidad de personal especializado limitada en algunas fechas."
            ])
        elif estado_seguimiento == 'rojo':
            return random.choice([
                "Retrasos significativos en aprobaciones del cliente.",
                "Problemas técnicos complejos requieren soluciones especializadas.",
                "Cambios en alcance solicitados por el cliente afectan cronograma.",
                "Disponibilidad de recursos críticos comprometida.",
                "Condiciones de sitio diferentes a las especificaciones originales."
            ])
        else:  # azul
            return random.choice([
                "Proyecto en pausa por decisiones del cliente.",
                "Esperando aprobaciones regulatorias necesarias.",
                "Pausa técnica para reevaluación de especificaciones.",
                "Suspensión temporal por factores externos."
            ])

    def generar_acciones(self, estado_seguimiento):
        """Generar acciones requeridas según el estado"""
        if estado_seguimiento == 'verde':
            return random.choice([
                "Continuar con el plan establecido según cronograma.",
                "Mantener comunicación regular con todas las partes.",
                "Preparar siguiente fase del proyecto."
            ])
        elif estado_seguimiento == 'amarillo':
            return random.choice([
                "Intensificar seguimiento semanal a proveedores críticos.",
                "Reunión de coordinación adicional con cliente próxima semana.",
                "Evaluar recursos adicionales para actividades críticas.",
                "Implementar plan de contingencia para condiciones climáticas."
            ])
        elif estado_seguimiento == 'rojo':
            return random.choice([
                "Reunión urgente con cliente para resolver aprobaciones pendientes.",
                "Traer consultor especializado para resolver problemas técnicos.",
                "Revisar y actualizar cronograma con nuevos alcances.",
                "Asegurar disponibilidad de recursos críticos con anticipación.",
                "Evaluación técnica completa de condiciones de sitio."
            ])
        else:  # azul
            return random.choice([
                "Dar seguimiento semanal al estado de aprobaciones.",
                "Mantener equipo en standby para reactivación rápida.",
                "Continuar con actividades de preparación y documentación.",
                "Coordinar reactivación una vez resueltos factores externos."
            ])

    def generar_decision(self):
        """Generar decisión tomada por el comité"""
        decisiones = [
            "Aprobada extensión de cronograma por 2 semanas adicionales.",
            "Autorizada contratación de recursos especializados externos.",
            "Aprobado cambio en especificaciones técnicas solicitado por cliente.",
            "Decidido implementar plan de contingencia tipo B.",
            "Autorizado presupuesto adicional para materiales especiales.",
            "Aprobada pausa técnica hasta resolución de aprobaciones regulatorias.",
            "Decidido acelerar cronograma con recursos adicionales.",
            "Autorizada reunión extraordinaria con directivos del cliente."
        ]
        
        return random.choice(decisiones)

    def generar_observaciones_seguimiento(self, estado_seguimiento):
        """Generar observaciones específicas del seguimiento"""
        if estado_seguimiento == 'verde':
            return random.choice([
                "Proyecto modelo en términos de ejecución y coordinación.",
                "Excelente desempeño del equipo de trabajo.",
                "Cliente muy satisfecho con el progreso reportado."
            ])
        elif estado_seguimiento == 'amarillo':
            return random.choice([
                "Se requiere monitoreo cercano para evitar escalamiento.",
                "Situación controlable con las medidas implementadas.",
                "Importante mantener comunicación fluida con stakeholders."
            ])
        elif estado_seguimiento == 'rojo':
            return random.choice([
                "Requiere atención prioritaria de la dirección del proyecto.",
                "Situación crítica que puede afectar otros proyectos.",
                "Necesario escalamiento a nivel gerencial para resolución."
            ])
        else:  # azul
            return random.choice([
                "Pausa planificada dentro de parámetros normales.",
                "Se mantiene preparación para reactivación inmediata.",
                "Situación temporal que no afecta viabilidad del proyecto."
            ])

    def mostrar_resumen(self):
        """Mostrar resumen de los datos creados"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("RESUMEN DE DATOS CREADOS"))
        self.stdout.write("="*50)
        
        # Estadísticas de comités
        total_comites = ComiteProyecto.objects.count()
        comites_por_estado = {}
        for estado, _ in ComiteProyecto.ESTADO_CHOICES:
            count = ComiteProyecto.objects.filter(estado=estado).count()
            comites_por_estado[estado] = count
        
        self.stdout.write(f"\n📊 COMITÉS CREADOS: {total_comites}")
        for estado, count in comites_por_estado.items():
            if count > 0:
                self.stdout.write(f"  • {estado.title()}: {count}")
        
        # Estadísticas de participantes
        total_participantes = ParticipanteComite.objects.count()
        self.stdout.write(f"\n👥 PARTICIPANTES: {total_participantes}")
        
        # Estadísticas de seguimientos
        total_seguimientos = SeguimientoProyectoComite.objects.count()
        seguimientos_por_estado = {}
        for estado, _ in SeguimientoProyectoComite.ESTADO_SEGUIMIENTO_CHOICES:
            count = SeguimientoProyectoComite.objects.filter(estado_seguimiento=estado).count()
            seguimientos_por_estado[estado] = count
        
        self.stdout.write(f"\n📈 SEGUIMIENTOS DE PROYECTOS: {total_seguimientos}")
        for estado, count in seguimientos_por_estado.items():
            if count > 0:
                self.stdout.write(f"  • {estado.title()}: {count}")
        
        # Comités con más proyectos
        self.stdout.write(f"\n🔝 COMITÉS CON MÁS PROYECTOS:")
        comites_top = ComiteProyecto.objects.all()[:3]
        for comite in comites_top:
            num_proyectos = comite.seguimientos.count()
            self.stdout.write(f"  • {comite.nombre}: {num_proyectos} proyectos")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("✅ Datos de prueba creados exitosamente"))
        self.stdout.write("="*50)