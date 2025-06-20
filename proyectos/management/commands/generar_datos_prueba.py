from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
from datetime import datetime, timedelta

from proyectos.models import (
    Proyecto, Actividad, Bitacora, Colaborador, ProrrogaProyecto,
    EntregableProyecto, BitacoraArchivo
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera datos de prueba completos para validar funcionalidades de Sesiones 3 y 4'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Limpia datos existentes antes de generar nuevos',
        )
        parser.add_argument(
            '--proyectos',
            type=int,
            default=10,
            help='Número de proyectos a crear (default: 10)',
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write('🧹 Limpiando datos existentes...')
            Bitacora.objects.all().delete()
            ProrrogaProyecto.objects.all().delete()
            Actividad.objects.all().delete()
            Proyecto.objects.all().delete()
            self.stdout.write('✅ Datos limpiados')

        self.crear_colaboradores()
        self.crear_proyectos(options['proyectos'])
        self.crear_actividades()
        self.crear_bitacoras()
        self.crear_prorrogas()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Datos de prueba generados exitosamente!\n'
                f'   📊 {Proyecto.objects.count()} Proyectos\n'
                f'   📋 {Actividad.objects.count()} Actividades\n'
                f'   📝 {Bitacora.objects.count()} Bitácoras\n'
                f'   ⏰ {ProrrogaProyecto.objects.count()} Prórrogas\n'
                f'   👥 {Colaborador.objects.count()} Colaboradores'
            )
        )

    def crear_colaboradores(self):
        """Crear colaboradores de prueba"""
        self.stdout.write('👥 Creando colaboradores...')
        
        colaboradores_data = [
            {'nombre': 'Carlos Rodríguez', 'cargo': 'Director de Proyectos', 'email': 'carlos.rodriguez@rgdaire.com'},
            {'nombre': 'Ana García', 'cargo': 'Ingeniera Residente', 'email': 'ana.garcia@rgdaire.com'},
            {'nombre': 'Miguel Fernández', 'cargo': 'Técnico Especialista', 'email': 'miguel.fernandez@rgdaire.com'},
            {'nombre': 'Laura Martínez', 'cargo': 'Coordinadora HSEQ', 'email': 'laura.martinez@rgdaire.com'},
            {'nombre': 'Roberto Silva', 'cargo': 'Técnico de Campo', 'email': 'roberto.silva@rgdaire.com'},
            {'nombre': 'Patricia López', 'cargo': 'Ingeniera de Diseño', 'email': 'patricia.lopez@rgdaire.com'},
            {'nombre': 'David Herrera', 'cargo': 'Supervisor de Instalación', 'email': 'david.herrera@rgdaire.com'},
            {'nombre': 'Carmen Jiménez', 'cargo': 'Técnica de Mantenimiento', 'email': 'carmen.jimenez@rgdaire.com'},
            {'nombre': 'Luis Torres', 'cargo': 'Especialista en Ventilación', 'email': 'luis.torres@rgdaire.com'},
            {'nombre': 'Mónica Vargas', 'cargo': 'Coordinadora de Calidad', 'email': 'monica.vargas@rgdaire.com'},
        ]
        
        for data in colaboradores_data:
            colaborador, created = Colaborador.objects.get_or_create(
                email=data['email'],
                defaults={
                    'nombre': data['nombre'],
                    'cargo': data['cargo'],
                    'telefono': f'+57 31{random.randint(0, 9)} {random.randint(100, 999)}-{random.randint(1000, 9999)}'
                }
            )
            if created:
                self.stdout.write(f'  ✅ {colaborador.nombre} - {colaborador.cargo}')

    def crear_proyectos(self, num_proyectos):
        """Crear proyectos con datos realistas"""
        self.stdout.write(f'📊 Creando {num_proyectos} proyectos...')
        
        # Obtener colaboradores para asignar como director e ingeniero
        colaboradores = list(Colaborador.objects.all())
        directores = [c for c in colaboradores if 'Director' in c.cargo or 'Coordinador' in c.cargo]
        ingenieros = [c for c in colaboradores if 'Ingenier' in c.cargo]
        
        # Obtener usuario para created_by
        user = User.objects.first()
        
        proyectos_data = [
            {
                'nombre': 'Sistema de Ventilación Industrial - Planta Cervecería',
                'cliente': 'Cervecería Nacional S.A.',
                'centro_costos': 'CERV-2024-001',
                'presupuesto': Decimal('285000000'),
                'dias_prometidos': 45,
                'tipo': 'industrial'
            },
            {
                'nombre': 'Extracción de Vapores - Laboratorio Farmacéutico',
                'cliente': 'Laboratorios Pharma Colombia',
                'centro_costos': 'PHAR-2024-002',
                'presupuesto': Decimal('156000000'),
                'dias_prometidos': 30,
                'tipo': 'laboratorio'
            },
            {
                'nombre': 'Campana de Extracción - Restaurante Gourmet',
                'cliente': 'Restaurantes Premium Ltda.',
                'centro_costos': 'REST-2024-003',
                'presupuesto': Decimal('75000000'),
                'dias_prometidos': 20,
                'tipo': 'comercial'
            },
            {
                'nombre': 'Sistema HVAC Completo - Hospital Regional',
                'cliente': 'Hospital Regional del Norte',
                'centro_costos': 'HOSP-2024-004',
                'presupuesto': Decimal('450000000'),
                'dias_prometidos': 90,
                'tipo': 'hospital'
            },
            {
                'nombre': 'Ventilación de Parqueadero - Centro Comercial',
                'cliente': 'Centros Comerciales Unidos',
                'centro_costos': 'MALL-2024-005',
                'presupuesto': Decimal('320000000'),
                'dias_prometidos': 60,
                'tipo': 'comercial'
            },
            {
                'nombre': 'Extracción Industrial - Planta Química',
                'cliente': 'Química Industrial S.A.S.',
                'centro_costos': 'QUIM-2024-006',
                'presupuesto': Decimal('580000000'),
                'dias_prometidos': 120,
                'tipo': 'industrial'
            },
            {
                'nombre': 'Sistema de Aire Acondicionado - Oficinas Corporativas',
                'cliente': 'Torre Empresarial del Sur',
                'centro_costos': 'CORP-2024-007',
                'presupuesto': Decimal('190000000'),
                'dias_prometidos': 35,
                'tipo': 'oficinas'
            },
            {
                'nombre': 'Ventilación Especializada - Planta de Alimentos',
                'cliente': 'Alimentos Procesados Colombia',
                'centro_costos': 'ALIM-2024-008',
                'presupuesto': Decimal('275000000'),
                'dias_prometidos': 50,
                'tipo': 'industrial'
            },
            {
                'nombre': 'Sistema de Extracción - Taller Automotriz',
                'cliente': 'Talleres Automotrices del Caribe',
                'centro_costos': 'AUTO-2024-009',
                'presupuesto': Decimal('85000000'),
                'dias_prometidos': 25,
                'tipo': 'taller'
            },
            {
                'nombre': 'HVAC Data Center - Empresa de Tecnología',
                'cliente': 'TechSolutions Colombia',
                'centro_costos': 'TECH-2024-010',
                'presupuesto': Decimal('380000000'),
                'dias_prometidos': 70,
                'tipo': 'datacenter'
            }
        ]
        
        for i in range(num_proyectos):
            data = proyectos_data[i % len(proyectos_data)]
            
            # Calcular fechas
            fecha_inicio = timezone.now().date() - timedelta(days=random.randint(10, 90))
            fecha_fin = fecha_inicio + timedelta(days=data['dias_prometidos'])
            
            # Generar datos financieros realistas
            presupuesto = data['presupuesto'] + Decimal(random.randint(-20000000, 20000000))
            presupuesto_gasto = presupuesto * Decimal(random.uniform(0.6, 0.8))
            gasto_real = presupuesto * Decimal(random.uniform(0.1, 0.7))
            gasto_operativo_real = presupuesto_gasto * Decimal(random.uniform(0.2, 0.6))
            reserva_contingencia = presupuesto * Decimal('0.1')
            
            # Estados realistas
            estados = ['pendiente', 'en_ejecucion', 'finalizado']
            estado = random.choice(estados)
            
            # Avances realistas
            avance_planeado = Decimal(random.randint(30, 85))
            if estado == 'pendiente':
                avance = Decimal(random.randint(0, 15))
            elif estado == 'en_ejecucion':
                avance = Decimal(random.randint(20, 80))
            else:  # finalizado
                avance = Decimal(100)
                fecha_fin_real = fecha_fin + timedelta(days=random.randint(-5, 15))
            
            proyecto = Proyecto.objects.create(
                nombre_proyecto=f"{data['nombre']} - Lote {i+1}",
                cliente=data['cliente'],
                centro_costos=f"{data['centro_costos']}-{i+1:02d}",
                orden_contrato=f"OC-{data['centro_costos']}-{i+1:02d}",
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                fecha_fin_real=fecha_fin_real if estado == 'finalizado' else None,
                dias_prometidos=data['dias_prometidos'],
                avance=avance,
                avance_planeado=avance_planeado,
                estado=estado,
                presupuesto=presupuesto,
                presupuesto_gasto=presupuesto_gasto,
                gasto_real=gasto_real,
                gasto_operativo_real=gasto_operativo_real,
                reserva_contingencia=reserva_contingencia,
                fecha_ultimo_gasto=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                observaciones=f"Proyecto de {data['tipo']} con especificaciones técnicas avanzadas.",
                director_proyecto=random.choice(directores) if directores else None,
                ingeniero_residente=random.choice(ingenieros) if ingenieros else None,
                creado_por=user
            )
            
            self.stdout.write(f'  ✅ {proyecto.nombre_proyecto} - {proyecto.estado} - {proyecto.avance}% avance')

    def crear_actividades(self):
        """Crear actividades para cada proyecto"""
        self.stdout.write('📋 Creando actividades...')
        
        colaboradores = list(Colaborador.objects.all())
        
        actividades_base = [
            {'nombre': 'Diseño y Cálculos Técnicos', 'duracion': 7, 'tipo': 'diseno'},
            {'nombre': 'Procura de Materiales', 'duracion': 10, 'tipo': 'procura'},
            {'nombre': 'Fabricación de Ductos', 'duracion': 15, 'tipo': 'fabricacion'},
            {'nombre': 'Instalación de Estructura', 'duracion': 8, 'tipo': 'instalacion'},
            {'nombre': 'Montaje de Equipos', 'duracion': 12, 'tipo': 'montaje'},
            {'nombre': 'Conexiones Eléctricas', 'duracion': 5, 'tipo': 'electrico'},
            {'nombre': 'Pruebas y Comisionamiento', 'duracion': 6, 'tipo': 'pruebas'},
            {'nombre': 'Entrega y Capacitación', 'duracion': 3, 'tipo': 'entrega'},
        ]
        
        for proyecto in Proyecto.objects.all():
            fecha_actual = proyecto.fecha_inicio
            
            for i, act_data in enumerate(actividades_base):
                inicio = fecha_actual
                fin = inicio + timedelta(days=act_data['duracion'])
                
                # Estados realistas basados en el proyecto
                if proyecto.estado == 'pendiente':
                    estado = 'no_iniciado' if i > 1 else random.choice(['no_iniciado', 'en_proceso'])
                    avance = random.randint(0, 20) if estado == 'en_proceso' else 0
                elif proyecto.estado == 'en_ejecucion':
                    if i < 3:
                        estado = 'finalizado'
                        avance = 100
                    elif i < 6:
                        estado = random.choice(['en_proceso', 'finalizado'])
                        avance = 100 if estado == 'finalizado' else random.randint(30, 90)
                    else:
                        estado = 'no_iniciado'
                        avance = 0
                else:  # finalizado
                    estado = 'finalizado'
                    avance = 100
                
                actividad = Actividad.objects.create(
                    proyecto=proyecto,
                    actividad=act_data['nombre'],
                    inicio=inicio,
                    fin=fin,
                    duracion=Decimal(act_data['duracion']),
                    avance=Decimal(avance),
                    estado=estado,
                    predecesoras=f"Actividad {i}" if i > 0 else "",
                    observaciones=f"Actividad de {act_data['tipo']} para el proyecto {proyecto.nombre_proyecto}",
                    responsable_asignado=random.choice(colaboradores) if colaboradores else None,
                    responsable_ejecucion=random.choice(['rgd', 'cliente', 'externo'])
                )
                
                fecha_actual = fin + timedelta(days=1)
                
        self.stdout.write(f'  ✅ {Actividad.objects.count()} actividades creadas')

    def crear_bitacoras(self):
        """Crear bitácoras con funcionalidades de Sesión 4"""
        self.stdout.write('📝 Creando bitácoras con funcionalidades Sesión 4...')
        
        colaboradores = list(Colaborador.objects.all())
        actividades = list(Actividad.objects.all())
        
        tipos_bitacora = [
            {'sub': 'Instalación de ductos principales', 'desc': 'Instalación y fijación de ductos de ventilación principal', 'horas': 8},
            {'sub': 'Conexión de sistemas eléctricos', 'desc': 'Cableado y conexión de motores y controles', 'horas': 6},
            {'sub': 'Pruebas de funcionamiento', 'desc': 'Verificación de operación y parámetros técnicos', 'horas': 4},
            {'sub': 'Ajustes y calibración', 'desc': 'Ajuste fino de equipos y calibración de controles', 'horas': 5},
            {'sub': 'Inspección de calidad', 'desc': 'Revisión de estándares de calidad y normativas', 'horas': 3},
            {'sub': 'Capacitación al personal', 'desc': 'Entrenamiento en operación y mantenimiento', 'horas': 4},
            {'sub': 'Documentación técnica', 'desc': 'Elaboración de manuales y planos as-built', 'horas': 6},
            {'sub': 'Limpieza y organización', 'desc': 'Limpieza de área de trabajo y organización de herramientas', 'horas': 2},
        ]
        
        for actividad in random.sample(actividades, min(len(actividades), 40)):
            # Crear 2-4 bitácoras por actividad seleccionada
            num_bitacoras = random.randint(2, 4)
            
            for i in range(num_bitacoras):
                tipo = random.choice(tipos_bitacora)
                
                # Fechas realistas
                fecha_planificada = actividad.inicio + timedelta(days=random.randint(0, int(actividad.duracion)))
                
                # Estados realistas con funcionalidades Sesión 4
                estados = ['planeada', 'en_proceso', 'completada', 'cancelada']
                estado = random.choice(estados)
                
                # Fecha real basada en estado
                if estado in ['completada', 'cancelada']:
                    # Algunas atrasadas, otras a tiempo
                    if random.random() < 0.3:  # 30% atrasadas
                        fecha_real = fecha_planificada + timedelta(days=random.randint(1, 10))
                    else:
                        fecha_real = fecha_planificada + timedelta(days=random.randint(-2, 2))
                else:
                    fecha_real = None
                
                # Estados de validación realistas
                if estado == 'completada':
                    estados_validacion = ['pendiente', 'validada_director', 'validada_ingeniero', 'validada_completa']
                    estado_validacion = random.choice(estados_validacion)
                else:
                    estado_validacion = 'pendiente'
                
                # Asignar equipo
                responsable = random.choice(colaboradores)
                lider_trabajo = random.choice(colaboradores)
                equipo = random.sample(colaboradores, random.randint(1, 4))
                
                bitacora = Bitacora.objects.create(
                    proyecto=actividad.proyecto,
                    actividad=actividad,
                    subactividad=f"{tipo['sub']} - Fase {i+1}",
                    responsable=responsable,
                    lider_trabajo=lider_trabajo,
                    fecha_planificada=fecha_planificada,
                    fecha_ejecucion_real=fecha_real,
                    estado=estado,
                    estado_validacion=estado_validacion,
                    descripcion=f"{tipo['desc']}. Trabajo realizado según especificaciones técnicas del proyecto {actividad.proyecto.nombre_proyecto}.",
                    duracion_horas=Decimal(tipo['horas']) + Decimal(random.uniform(-1, 2)),
                    observaciones=f"Observaciones técnicas para {tipo['sub'].lower()}. {random.choice(['Sin novedades.', 'Trabajo completado satisfactoriamente.', 'Se requiere seguimiento adicional.', 'Cumple con estándares de calidad.'])}"
                )
                
                # Agregar equipo
                bitacora.equipo.set(equipo)
                
                # Agregar firmas digitales para bitácoras completadas con validación
                if estado_validacion in ['validada_director', 'validada_completa']:
                    bitacora.firma_director = f"FIRMA_DIGITAL_DIR_{bitacora.id}_{timezone.now().timestamp()}"
                    bitacora.fecha_firma_director = timezone.now() - timedelta(days=random.randint(0, 5))
                    bitacora.ip_firma_director = f"192.168.1.{random.randint(100, 200)}"
                    bitacora.dispositivo_firma_director = random.choice([
                        "Windows 10 - Chrome 120.0.0.0",
                        "Android 13 - Chrome Mobile",
                        "iOS 17.1 - Safari",
                        "Windows 11 - Edge 120.0.0.0"
                    ])
                
                if estado_validacion in ['validada_ingeniero', 'validada_completa']:
                    bitacora.firma_ingeniero = f"FIRMA_DIGITAL_ING_{bitacora.id}_{timezone.now().timestamp()}"
                    bitacora.fecha_firma_ingeniero = timezone.now() - timedelta(days=random.randint(0, 3))
                    bitacora.ip_firma_ingeniero = f"192.168.1.{random.randint(100, 200)}"
                    bitacora.dispositivo_firma_ingeniero = random.choice([
                        "Windows 10 - Chrome 120.0.0.0",
                        "iPad OS 17 - Safari",
                        "Android 14 - Chrome Mobile",
                        "macOS Sonoma - Safari"
                    ])
                
                bitacora.save()
        
        self.stdout.write(f'  ✅ {Bitacora.objects.count()} bitácoras creadas con funcionalidades Sesión 4')

    def crear_prorrogas(self):
        """Crear prórrogas para validar funcionalidad Sesión 3"""
        self.stdout.write('⏰ Creando prórrogas...')
        
        # Seleccionar algunos proyectos para crear prórrogas
        proyectos_con_prorrogas = random.sample(
            list(Proyecto.objects.all()), 
            min(Proyecto.objects.count(), 6)
        )
        
        tipos_prorroga = [
            {'tipo': 'cliente', 'justificacion': 'El cliente solicitó cambios en las especificaciones técnicas que requieren tiempo adicional para implementar.'},
            {'tipo': 'tecnica', 'justificacion': 'Se encontraron dificultades técnicas imprevistas que requieren soluciones especializadas.'},
            {'tipo': 'clima', 'justificacion': 'Las condiciones climáticas adversas han impedido el trabajo en exteriores.'},
            {'tipo': 'recursos', 'justificacion': 'Retraso en la disponibilidad de materiales especializados por parte del proveedor.'},
            {'tipo': 'fuerza_mayor', 'justificacion': 'Situaciones de fuerza mayor han impedido el desarrollo normal de las actividades.'},
        ]
        
        for proyecto in proyectos_con_prorrogas:
            # 1-2 prórrogas por proyecto
            num_prorrogas = random.randint(1, 2)
            
            fecha_fin_actual = proyecto.fecha_fin
            
            for i in range(num_prorrogas):
                tipo_data = random.choice(tipos_prorroga)
                dias_extension = random.randint(7, 30)
                nueva_fecha_fin = fecha_fin_actual + timedelta(days=dias_extension)
                
                # Estados realistas
                estados = ['solicitada', 'aprobada', 'rechazada', 'aplicada']
                estado = random.choice(estados)
                
                prorroga = ProrrogaProyecto.objects.create(
                    proyecto=proyecto,
                    fecha_fin_original=fecha_fin_actual,
                    fecha_fin_propuesta=nueva_fecha_fin,
                    dias_extension=dias_extension,
                    tipo_prorroga=tipo_data['tipo'],
                    justificacion=f"{tipo_data['justificacion']} Se requiere una extensión de {dias_extension} días para completar el proyecto satisfactoriamente.",
                    estado=estado,
                    aprobada_por=f"Gerencia de Proyectos - {random.choice(['Carlos Rodríguez', 'Ana García'])}" if estado in ['aprobada', 'aplicada'] else "",
                    fecha_aprobacion=timezone.now() - timedelta(days=random.randint(1, 10)) if estado in ['aprobada', 'aplicada'] else None,
                    observaciones_aprobacion=f"Prórroga aprobada considerando las circunstancias especiales del proyecto." if estado in ['aprobada', 'aplicada'] else ""
                )
                
                # Si fue aplicada, actualizar fecha fin del proyecto
                if estado == 'aplicada':
                    proyecto.fecha_fin = nueva_fecha_fin
                    proyecto.save()
                    fecha_fin_actual = nueva_fecha_fin
        
        self.stdout.write(f'  ✅ {ProrrogaProyecto.objects.count()} prórrogas creadas')

    def mostrar_resumen_estadisticas(self):
        """Mostrar estadísticas de los datos generados"""
        self.stdout.write('\n📊 ESTADÍSTICAS DE DATOS GENERADOS:')
        
        # Proyectos por estado
        for estado, nombre in Proyecto.ESTADO_CHOICES:
            count = Proyecto.objects.filter(estado=estado).count()
            self.stdout.write(f'   📊 Proyectos {nombre}: {count}')
        
        # Bitácoras por estado
        for estado, nombre in Bitacora.ESTADO_CHOICES:
            count = Bitacora.objects.filter(estado=estado).count()
            self.stdout.write(f'   📝 Bitácoras {nombre}: {count}')
        
        # Alertas de retraso
        proyectos_atrasados = Proyecto.objects.filter(
            fecha_fin__lt=timezone.now().date(),
            estado__in=['pendiente', 'en_ejecucion']
        ).count()
        self.stdout.write(f'   🔴 Proyectos atrasados: {proyectos_atrasados}')
        
        # Bitácoras urgentes
        bitacoras_urgentes = sum(1 for b in Bitacora.objects.filter(estado='planeada') if b.requiere_registro_urgente)
        self.stdout.write(f'   🚨 Bitácoras urgentes: {bitacoras_urgentes}')
        
        # Prórrogas por estado
        for estado, nombre in ProrrogaProyecto.ESTADO_CHOICES:
            count = ProrrogaProyecto.objects.filter(estado=estado).count()
            self.stdout.write(f'   ⏰ Prórrogas {nombre}: {count}')