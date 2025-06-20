from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random

from mantenimiento.models import Equipo, HojaVidaEquipo, ContratoMantenimiento, ActividadMantenimiento
from crm.models import Cliente

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea datos de prueba para el módulo de mantenimiento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--equipos',
            type=int,
            default=10,
            help='Número de equipos a crear'
        )
        parser.add_argument(
            '--hojas-vida',
            type=int,
            default=15,
            help='Número de hojas de vida a crear'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de prueba para mantenimiento...'))
        
        # Obtener o crear usuario por defecto
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.create_user(
                    username='admin_mantenimiento',
                    email='admin@rgdaire.com',
                    password='admin123',
                    is_superuser=True,
                    is_staff=True
                )
        except Exception as e:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No hay usuarios en el sistema. Cree un usuario primero.'))
                return

        # Verificar que hay clientes
        clientes = list(Cliente.objects.all())
        if not clientes:
            self.stdout.write(self.style.ERROR('No hay clientes en el sistema. Cree clientes primero.'))
            return

        # Crear equipos si no existen
        equipos_existentes = Equipo.objects.count()
        if equipos_existentes == 0:
            self.stdout.write('Creando equipos...')
            
            # Datos de ejemplo para equipos
            equipos_data = [
                {
                    'nombre': 'Aire Acondicionado Split 12000 BTU',
                    'categoria': 'aire_acondicionado',
                    'marca': 'Carrier',
                    'modelo': '42QHC012DS',
                    'capacidad_btu': 12000,
                    'voltaje': '220V',
                    'amperaje': '5.8A',
                    'refrigerante': 'R-410A',
                    'peso_kg': 32.5,
                    'fabricante': 'Carrier Corporation',
                    'pais_origen': 'Estados Unidos',
                    'vida_util_anos': 15
                },
                {
                    'nombre': 'Aire Acondicionado Central 60000 BTU',
                    'categoria': 'aire_acondicionado',
                    'marca': 'York',
                    'modelo': 'YCD060S4ASA',
                    'capacidad_btu': 60000,
                    'voltaje': '380V',
                    'amperaje': '15.2A',
                    'refrigerante': 'R-410A',
                    'peso_kg': 125.0,
                    'fabricante': 'York International',
                    'pais_origen': 'Estados Unidos',
                    'vida_util_anos': 20
                },
                {
                    'nombre': 'Ventilador Industrial de Techo',
                    'categoria': 'ventilacion',
                    'marca': 'Hunter',
                    'modelo': 'HFC-72',
                    'voltaje': '110V',
                    'amperaje': '1.2A',
                    'peso_kg': 15.8,
                    'fabricante': 'Hunter Fan Company',
                    'pais_origen': 'Estados Unidos',
                    'vida_util_anos': 10
                },
                {
                    'nombre': 'Sistema de Ventilación Comercial',
                    'categoria': 'ventilacion',
                    'marca': 'Systemair',
                    'modelo': 'RVK-315L1',
                    'voltaje': '220V',
                    'amperaje': '2.8A',
                    'peso_kg': 45.2,
                    'fabricante': 'Systemair AB',
                    'pais_origen': 'Suecia',
                    'vida_util_anos': 15
                },
                {
                    'nombre': 'Chiller Enfriado por Agua',
                    'categoria': 'refrigeracion',
                    'marca': 'Trane',
                    'modelo': 'CGAM080',
                    'capacidad_btu': 80000,
                    'voltaje': '380V',
                    'amperaje': '25.5A',
                    'refrigerante': 'R-134A',
                    'peso_kg': 180.5,
                    'fabricante': 'Trane Technologies',
                    'pais_origen': 'Estados Unidos',
                    'vida_util_anos': 25
                },
                {
                    'nombre': 'Humidificador Ultrasónico',
                    'categoria': 'humidificacion',
                    'marca': 'Honeywell',
                    'modelo': 'HUL570B',
                    'voltaje': '110V',
                    'amperaje': '0.8A',
                    'peso_kg': 8.2,
                    'fabricante': 'Honeywell International',
                    'pais_origen': 'Estados Unidos',
                    'vida_util_anos': 8
                },
                {
                    'nombre': 'Sistema de Filtración HEPA',
                    'categoria': 'filtracion',
                    'marca': 'Camfil',
                    'modelo': 'Hi-Flo ES',
                    'voltaje': '220V',
                    'amperaje': '3.2A',
                    'peso_kg': 25.8,
                    'fabricante': 'Camfil Group',
                    'pais_origen': 'Suecia',
                    'vida_util_anos': 12
                },
                {
                    'nombre': 'Caldera de Calefacción',
                    'categoria': 'calefaccion',
                    'marca': 'Bosch',
                    'modelo': 'Greenstar 30CDi',
                    'voltaje': '220V',
                    'amperaje': '4.5A',
                    'peso_kg': 42.0,
                    'fabricante': 'Bosch Thermotechnology',
                    'pais_origen': 'Alemania',
                    'vida_util_anos': 18
                },
                {
                    'nombre': 'Aire Acondicionado Cassette',
                    'categoria': 'aire_acondicionado',
                    'marca': 'Daikin',
                    'modelo': 'FCQ100KAVEA',
                    'capacidad_btu': 36000,
                    'voltaje': '220V',
                    'amperaje': '8.5A',
                    'refrigerante': 'R-32',
                    'peso_kg': 28.5,
                    'fabricante': 'Daikin Industries',
                    'pais_origen': 'Japón',
                    'vida_util_anos': 16
                },
                {
                    'nombre': 'Extractor de Aire Industrial',
                    'categoria': 'ventilacion',
                    'marca': 'Soler & Palau',
                    'modelo': 'TD-800/200',
                    'voltaje': '380V',
                    'amperaje': '2.1A',
                    'peso_kg': 18.7,
                    'fabricante': 'Soler & Palau Ventilation Group',
                    'pais_origen': 'España',
                    'vida_util_anos': 12
                }
            ]

            created_equipos = []
            for data in equipos_data:
                equipo = Equipo.objects.create(
                    **data,
                    descripcion=f"Equipo HVAC {data['marca']} {data['modelo']} para {data['categoria']}",
                    creado_por=user
                )
                created_equipos.append(equipo)
                self.stdout.write(f'  ✓ Creado equipo: {equipo.marca} {equipo.modelo}')

        else:
            created_equipos = list(Equipo.objects.all())
            self.stdout.write(f'Usando {len(created_equipos)} equipos existentes')

        # Crear hojas de vida
        hojas_vida_existentes = HojaVidaEquipo.objects.count()
        if hojas_vida_existentes == 0:
            self.stdout.write('Creando hojas de vida...')
            
            num_hojas_vida = min(options['hojas_vida'], len(clientes) * 2)  # Máximo 2 equipos por cliente
            
            for i in range(num_hojas_vida):
                cliente = random.choice(clientes)
                equipo = random.choice(created_equipos)
                
                # Generar fechas aleatorias
                fecha_instalacion = timezone.now().date() - timedelta(days=random.randint(30, 1095))  # Entre 1 mes y 3 años
                fecha_compra = fecha_instalacion - timedelta(days=random.randint(1, 90))  # Entre 1 y 90 días antes
                
                # Generar código interno único
                codigo_base = f"{cliente.nombre[:3].upper()}-{equipo.categoria[:2].upper()}"
                codigo_interno = f"{codigo_base}-{i+1:03d}"
                
                # Verificar unicidad del código
                while HojaVidaEquipo.objects.filter(codigo_interno=codigo_interno).exists():
                    codigo_interno = f"{codigo_base}-{random.randint(100, 999)}"
                
                # Generar número de serie único
                numero_serie = f"{equipo.marca[:2].upper()}{equipo.modelo[:3].upper()}{random.randint(100000, 999999)}"
                while HojaVidaEquipo.objects.filter(numero_serie=numero_serie).exists():
                    numero_serie = f"{equipo.marca[:2].upper()}{equipo.modelo[:3].upper()}{random.randint(100000, 999999)}"

                hoja_vida = HojaVidaEquipo.objects.create(
                    equipo=equipo,
                    cliente=cliente,
                    codigo_interno=codigo_interno,
                    numero_serie=numero_serie,
                    tag_cliente=f"TAG-{i+1:03d}",
                    fecha_instalacion=fecha_instalacion,
                    fecha_compra=fecha_compra,
                    fecha_garantia_fin=fecha_instalacion + timedelta(days=365 * random.randint(1, 3)),  # 1-3 años
                    proveedor=random.choice(['Distribuidor HVAC SA', 'Equipos Industriales Ltda', 'Climatización Profesional', 'Aire y Ventilación SAS']),
                    valor_compra=random.randint(500000, 5000000),  # Entre 500k y 5M
                    ubicacion_detallada=random.choice([
                        'Sala de servidores - Planta 2',
                        'Oficina principal - Recepción',
                        'Área de producción - Zona A',
                        'Almacén - Sector Norte',
                        'Sala de juntas - Piso 3',
                        'Área administrativa - Planta 1',
                        'Laboratorio - Zona limpia',
                        'Taller de mantenimiento'
                    ]),
                    direccion_instalacion=cliente.direccion or 'Dirección no especificada',
                    coordenadas_gps=f"{random.uniform(4.5, 4.8):.6f}, {random.uniform(-74.2, -74.0):.6f}",
                    estado=random.choice(['operativo', 'operativo', 'operativo', 'mantenimiento', 'fuera_servicio']),  # Más operativos
                    observaciones=f"Equipo instalado por contrato #{random.randint(1000, 9999)}. Estado general bueno.",
                    condiciones_ambientales=f"Temperatura ambiente: {random.randint(18, 28)}°C, Humedad: {random.randint(40, 70)}%",
                    creado_por=user
                )
                
                self.stdout.write(f'  ✓ Creada hoja de vida: {hoja_vida.codigo_interno} - {cliente.nombre}')

        else:
            self.stdout.write(f'Ya existen {hojas_vida_existentes} hojas de vida')

        # Crear contratos de mantenimiento
        contratos_existentes = ContratoMantenimiento.objects.count()
        if contratos_existentes == 0:
            self.stdout.write('Creando contratos de mantenimiento...')
            
            hojas_vida = list(HojaVidaEquipo.objects.all())
            if hojas_vida:
                # Crear 5 contratos con diferentes clientes
                clientes_con_contratos = random.sample(clientes, min(5, len(clientes)))
                
                for i, cliente in enumerate(clientes_con_contratos):
                    # Obtener hojas de vida de este cliente
                    hojas_cliente = [hv for hv in hojas_vida if hv.cliente == cliente]
                    
                    if hojas_cliente:
                        fecha_inicio = timezone.now().date() - timedelta(days=random.randint(30, 365))
                        
                        contrato = ContratoMantenimiento.objects.create(
                            cliente=cliente,
                            nombre_contrato=f"Contrato de Mantenimiento {cliente.nombre[:20]}",
                            tipo_contrato=random.choice(['preventivo', 'integral', 'correctivo']),
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_inicio + timedelta(days=365),
                            meses_duracion=12,
                            valor_mensual=random.randint(500000, 2000000),
                            valor_total_contrato=random.randint(6000000, 24000000),
                            incluye_materiales=random.choice([True, False]),
                            incluye_repuestos=random.choice([True, False]),
                            tiempo_respuesta_horas=random.choice([24, 48, 72]),
                            horas_incluidas_mes=random.randint(8, 40),
                            estado='activo',
                            creado_por=user
                        )
                        
                        # Asignar hojas de vida al contrato
                        contrato.equipos_incluidos.set(hojas_cliente)
                        
                        self.stdout.write(f'  ✓ Creado contrato: {contrato.numero_contrato} - {cliente.nombre}')

        # Crear actividades de mantenimiento
        actividades_existentes = ActividadMantenimiento.objects.count()
        if actividades_existentes == 0:
            self.stdout.write('Creando actividades de mantenimiento...')
            
            contratos = list(ContratoMantenimiento.objects.filter(estado='activo'))
            if contratos:
                for contrato in contratos:
                    hojas_vida_contrato = list(contrato.equipos_incluidos.all())
                    
                    # Crear 2-4 actividades por contrato
                    num_actividades = random.randint(2, 4)
                    for i in range(num_actividades):
                        hoja_vida = random.choice(hojas_vida_contrato)
                        
                        # Fechas variadas (pasadas, presentes y futuras)
                        fecha_base = timezone.now()
                        if i == 0:
                            # Actividad completada (pasada)
                            fecha_programada = fecha_base - timedelta(days=random.randint(7, 30))
                            estado = 'completada'
                        elif i == 1:
                            # Actividad en proceso (reciente)
                            fecha_programada = fecha_base - timedelta(days=random.randint(1, 3))
                            estado = 'en_proceso'
                        else:
                            # Actividad futura
                            fecha_programada = fecha_base + timedelta(days=random.randint(7, 60))
                            estado = random.choice(['programada', 'asignada'])
                        
                        actividad = ActividadMantenimiento.objects.create(
                            contrato=contrato,
                            hoja_vida_equipo=hoja_vida,
                            tipo_actividad=random.choice(['preventivo', 'limpieza', 'inspeccion', 'correctivo']),
                            titulo=f"{random.choice(['Mantenimiento preventivo', 'Limpieza general', 'Inspección técnica', 'Revisión de filtros'])} - {hoja_vida.codigo_interno}",
                            descripcion=f"Actividad de mantenimiento programada para el equipo {hoja_vida.equipo.marca} {hoja_vida.equipo.modelo}",
                            fecha_programada=fecha_programada,
                            fecha_limite=fecha_programada + timedelta(hours=random.randint(4, 24)),
                            duracion_estimada_horas=random.choice([1.0, 1.5, 2.0, 3.0, 4.0]),
                            estado=estado,
                            prioridad=random.choice(['baja', 'media', 'media', 'alta']),  # Más medias
                            observaciones=f"Actividad generada automáticamente para el cliente {contrato.cliente.nombre}",
                            creado_por=user
                        )
                        
                        # Si está completada, agregar fechas reales
                        if estado == 'completada':
                            actividad.fecha_inicio_real = fecha_programada
                            actividad.fecha_fin_real = fecha_programada + timedelta(hours=float(actividad.duracion_estimada_horas))
                            actividad.save()
                        elif estado == 'en_proceso':
                            actividad.fecha_inicio_real = fecha_programada
                            actividad.save()
                        
                        self.stdout.write(f'  ✓ Creada actividad: {actividad.codigo_actividad} - {actividad.titulo[:50]}...')

        # Mostrar resumen
        total_equipos = Equipo.objects.count()
        total_hojas_vida = HojaVidaEquipo.objects.count()
        total_contratos = ContratoMantenimiento.objects.count()
        total_actividades = ActividadMantenimiento.objects.count()
        total_clientes = Cliente.objects.count()

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('RESUMEN DE DATOS CREADOS:'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'📦 Equipos en catálogo: {total_equipos}')
        self.stdout.write(f'📋 Hojas de vida: {total_hojas_vida}')
        self.stdout.write(f'📝 Contratos activos: {total_contratos}')
        self.stdout.write(f'⚡ Actividades de mantenimiento: {total_actividades}')
        self.stdout.write(f'🏢 Clientes disponibles: {total_clientes}')
        self.stdout.write(self.style.SUCCESS('\n✅ Datos de prueba creados exitosamente!'))
        self.stdout.write('\n🔗 Ahora puede:')
        self.stdout.write('   • Ver equipos: /mantenimiento/equipos/')
        self.stdout.write('   • Ver hojas de vida: /mantenimiento/hojas-vida/')
        self.stdout.write('   • Ver contratos: /mantenimiento/contratos/')
        self.stdout.write('   • Ver actividades: /mantenimiento/actividades/')
        self.stdout.write('   • Crear informes de mantenimiento')