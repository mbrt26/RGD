from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta, date

from crm.models import (
    ConfiguracionOferta, Cliente, Contacto, RepresentanteVentas, 
    Trato, Cotizacion, VersionCotizacion, TareaVenta, Lead
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera datos de prueba completos para el módulo CRM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina todos los datos existentes antes de generar nuevos',
        )
        parser.add_argument(
            '--clientes',
            type=int,
            default=20,
            help='Número de clientes a crear (default: 20)',
        )
        parser.add_argument(
            '--leads',
            type=int,
            default=15,
            help='Número de leads a crear (default: 15)',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('🗑️ Eliminando datos existentes...')
            self.reset_data()

        self.stdout.write('🚀 Iniciando generación de datos de prueba para CRM...')
        
        # 1. Configurar numeración de ofertas
        self.crear_configuracion_oferta()
        
        # 2. Crear usuarios y representantes de ventas
        usuarios = self.crear_usuarios_vendedores()
        
        # 3. Crear clientes con contactos
        clientes = self.crear_clientes_con_contactos(options['clientes'])
        
        # 4. Crear leads
        leads = self.crear_leads(options['leads'], usuarios)
        
        # 5. Crear tratos con cotizaciones
        tratos = self.crear_tratos_con_cotizaciones(clientes, usuarios)
        
        # 6. Crear tareas de venta
        self.crear_tareas_venta(clientes, tratos, usuarios)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Datos de prueba generados exitosamente!\n'
                f'   📊 {len(clientes)} clientes creados\n'
                f'   🎯 {len(leads)} leads creados\n'
                f'   💼 {len(tratos)} tratos creados\n'
                f'   👥 {len(usuarios)} vendedores creados'
            )
        )

    def reset_data(self):
        """Elimina todos los datos del CRM"""
        TareaVenta.objects.all().delete()
        VersionCotizacion.objects.all().delete()
        Cotizacion.objects.all().delete()
        Trato.objects.all().delete()
        Lead.objects.all().delete()
        Contacto.objects.all().delete()
        Cliente.objects.all().delete()
        RepresentanteVentas.objects.all().delete()
        ConfiguracionOferta.objects.all().delete()
        self.stdout.write('✅ Datos eliminados')

    def crear_configuracion_oferta(self):
        """Crea o actualiza la configuración de ofertas"""
        config, created = ConfiguracionOferta.objects.get_or_create(
            defaults={'siguiente_numero': 1001}
        )
        if created:
            self.stdout.write('✅ Configuración de ofertas creada')
        return config

    def crear_usuarios_vendedores(self):
        """Crea usuarios vendedores y sus representantes"""
        vendedores_data = [
            {'username': 'carlos_lopez', 'first_name': 'Carlos', 'last_name': 'López', 'email': 'carlos.lopez@rgd.com'},
            {'username': 'maria_garcia', 'first_name': 'María', 'last_name': 'García', 'email': 'maria.garcia@rgd.com'},
            {'username': 'juan_perez', 'first_name': 'Juan', 'last_name': 'Pérez', 'email': 'juan.perez@rgd.com'},
            {'username': 'ana_rodriguez', 'first_name': 'Ana', 'last_name': 'Rodríguez', 'email': 'ana.rodriguez@rgd.com'},
            {'username': 'diego_martinez', 'first_name': 'Diego', 'last_name': 'Martínez', 'email': 'diego.martinez@rgd.com'},
        ]
        
        usuarios = []
        for data in vendedores_data:
            usuario, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'email': data['email'],
                    'is_staff': True,
                }
            )
            if created:
                usuario.set_password('vendedor123')
                usuario.save()
            
            # Crear representante de ventas
            rep_ventas, created = RepresentanteVentas.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'telefono': f'+57 300 {random.randint(1000000, 9999999)}',
                    'meta_ventas': Decimal(str(random.randint(500000000, 2000000000)))
                }
            )
            usuarios.append(usuario)
        
        self.stdout.write(f'✅ {len(usuarios)} vendedores creados')
        return usuarios

    def crear_clientes_con_contactos(self, num_clientes):
        """Crea clientes con sus contactos"""
        empresas_data = [
            # Sector Alimentos
            {'nombre': 'Alimentos del Valle S.A.S', 'sector': 'alimentos', 'nit': '900123456-1'},
            {'nombre': 'Procesadora de Carnes Premium', 'sector': 'alimentos', 'nit': '800234567-2'},
            {'nombre': 'Lácteos Frescos Colombia', 'sector': 'alimentos', 'nit': '900345678-3'},
            {'nombre': 'Panadería Industrial El Trigal', 'sector': 'alimentos', 'nit': '800456789-4'},
            {'nombre': 'Bebidas Naturales Andinas', 'sector': 'alimentos', 'nit': '900567890-5'},
            
            # Sector Farmacéutico
            {'nombre': 'Laboratorios Farma Colombia', 'sector': 'farmaceutico', 'nit': '900678901-6'},
            {'nombre': 'Medicamentos Genéricos S.A.', 'sector': 'farmaceutico', 'nit': '800789012-7'},
            {'nombre': 'Biotecnología Médica Ltda.', 'sector': 'farmaceutico', 'nit': '900890123-8'},
            
            # Sector Industrial
            {'nombre': 'Manufacturas Industriales del Norte', 'sector': 'industrial', 'nit': '800901234-9'},
            {'nombre': 'Química Industrial Colombiana', 'sector': 'industrial', 'nit': '900012345-0'},
            {'nombre': 'Metalmecánica Bogotá S.A.S', 'sector': 'industrial', 'nit': '800123450-1'},
            {'nombre': 'Textiles y Confecciones Modernas', 'sector': 'industrial', 'nit': '900234561-2'},
            
            # Sector Construcción
            {'nombre': 'Constructora Edificar S.A.', 'sector': 'construccion', 'nit': '800345672-3'},
            {'nombre': 'Ingeniería y Obras Civiles', 'sector': 'construccion', 'nit': '900456783-4'},
            {'nombre': 'Materiales de Construcción del Sur', 'sector': 'construccion', 'nit': '800567894-5'},
            
            # Sector Salud
            {'nombre': 'Hospital Regional San José', 'sector': 'salud', 'nit': '900678905-6'},
            {'nombre': 'Clínica Especializada del Corazón', 'sector': 'salud', 'nit': '800789016-7'},
            {'nombre': 'Centro Médico Integral', 'sector': 'salud', 'nit': '900890127-8'},
            
            # Sector Cosméticos
            {'nombre': 'Cosméticos Naturales Bella', 'sector': 'cosmeticos', 'nit': '800901238-9'},
            {'nombre': 'Productos de Belleza Premium', 'sector': 'cosmeticos', 'nit': '900012349-0'},
            
            # Sector Educación
            {'nombre': 'Universidad Tecnológica del Futuro', 'sector': 'educacion', 'nit': '800123461-1'},
            {'nombre': 'Instituto de Formación Técnica', 'sector': 'educacion', 'nit': '900234572-2'},
            
            # Sector Comercio
            {'nombre': 'Distribuidora Comercial Mayorista', 'sector': 'comercio', 'nit': '800345683-3'},
            {'nombre': 'Supermercados Económicos S.A.S', 'sector': 'comercio', 'nit': '900456794-4'},
        ]
        
        ciudades = ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena', 'Bucaramanga', 'Pereira', 'Manizales']
        departamentos = ['Cundinamarca', 'Antioquia', 'Valle del Cauca', 'Atlántico', 'Bolívar', 'Santander', 'Risaralda', 'Caldas']
        
        clientes = []
        for i in range(min(num_clientes, len(empresas_data))):
            empresa = empresas_data[i]
            ciudad = random.choice(ciudades)
            departamento = random.choice(departamentos)
            
            cliente = Cliente.objects.create(
                nombre=empresa['nombre'],
                sector_actividad=empresa['sector'],
                nit=empresa['nit'],
                correo=f"contacto@{empresa['nombre'].lower().replace(' ', '').replace('.', '')[:20]}.com",
                telefono=f'+57 {random.choice([1, 4, 5, 6])} {random.randint(200, 999)}{random.randint(1000, 9999)}',
                direccion=f'Calle {random.randint(10, 200)} # {random.randint(10, 99)}-{random.randint(10, 99)}',
                ciudad=ciudad,
                estado=departamento,
                notas=f'Cliente del sector {empresa["sector"]} con sede principal en {ciudad}.'
            )
            
            # Crear 2-4 contactos por cliente
            contactos_nombres = [
                ['Carlos', 'Fernández', 'Gerente General'],
                ['María', 'Rodríguez', 'Directora de Compras'],
                ['Juan', 'González', 'Jefe de Producción'],
                ['Ana', 'López', 'Coordinadora de Calidad'],
                ['Diego', 'Martínez', 'Supervisor de Mantenimiento'],
                ['Laura', 'Sánchez', 'Asistente Administrativa'],
            ]
            
            num_contactos = random.randint(2, 4)
            contactos_seleccionados = random.sample(contactos_nombres, num_contactos)
            
            for nombre, apellido, cargo in contactos_seleccionados:
                Contacto.objects.create(
                    cliente=cliente,
                    nombre=f'{nombre} {apellido}',
                    cargo=cargo,
                    correo=f'{nombre.lower()}.{apellido.lower()}@{empresa["nombre"].lower().replace(" ", "").replace(".", "")[:15]}.com',
                    telefono=f'+57 300 {random.randint(1000000, 9999999)}',
                    notas=f'Contacto principal para temas de {cargo.lower()}'
                )
            
            clientes.append(cliente)
        
        self.stdout.write(f'✅ {len(clientes)} clientes con contactos creados')
        return clientes

    def crear_leads(self, num_leads, usuarios):
        """Crea leads potenciales"""
        leads_data = [
            {'nombre': 'Patricia Vásquez', 'empresa': 'Textiles Modernos S.A.', 'sector': 'industrial'},
            {'nombre': 'Roberto Silva', 'empresa': 'Farmacia Central', 'sector': 'farmaceutico'},
            {'nombre': 'Claudia Moreno', 'empresa': 'Alimentos Orgánicos', 'sector': 'alimentos'},
            {'nombre': 'Fernando Ruiz', 'empresa': 'Construcciones del Pacífico', 'sector': 'construccion'},
            {'nombre': 'Gabriela Torres', 'empresa': 'Centro de Salud Integral', 'sector': 'salud'},
            {'nombre': 'Andrés Herrera', 'empresa': 'Cosméticos Naturales Ltda.', 'sector': 'cosmeticos'},
            {'nombre': 'Isabel Ramírez', 'empresa': 'Colegio Técnico Industrial', 'sector': 'educacion'},
            {'nombre': 'Miguel Castillo', 'empresa': 'Distribuidora del Caribe', 'sector': 'comercio'},
            {'nombre': 'Natalia Jiménez', 'empresa': 'Productos Fitoterapéuticos', 'sector': 'fitoterapeuta'},
            {'nombre': 'Sebastián Vargas', 'empresa': 'Obras de Infraestructura', 'sector': 'infraestructura'},
            {'nombre': 'Carolina Mejía', 'empresa': 'Banco Regional del Sur', 'sector': 'servicios_financieros'},
            {'nombre': 'Alejandro Cruz', 'empresa': 'Procesadora de Frutas', 'sector': 'alimentos'},
            {'nombre': 'Valentina Ortiz', 'empresa': 'Laboratorio de Análisis', 'sector': 'farmaceutico'},
            {'nombre': 'Daniel Guerrero', 'empresa': 'Metales y Aleaciones', 'sector': 'industrial'},
            {'nombre': 'Sofía Ramos', 'empresa': 'Hospital Infantil', 'sector': 'salud'},
        ]
        
        estados = ['nuevo', 'contactado', 'calificado', 'propuesta', 'negociacion']
        fuentes = ['web', 'referido', 'publicidad', 'evento', 'llamada_fria', 'email', 'redes_sociales']
        niveles_interes = ['bajo', 'medio', 'alto', 'muy_alto']
        
        necesidades = [
            'Sistema de tratamiento de aguas residuales para cumplir normativas ambientales',
            'Control de calidad del aire en áreas de producción',
            'Filtración de agua para procesos industriales',
            'Monitoreo continuo de emisiones atmosféricas',
            'Tratamiento de efluentes líquidos industriales',
            'Sistema de purificación de agua potable',
            'Control de olores en procesos productivos',
            'Gestión integral de residuos líquidos',
            'Análisis y control de contaminantes',
            'Sistema de recirculación de agua industrial'
        ]
        
        leads = []
        for i in range(min(num_leads, len(leads_data))):
            lead_data = leads_data[i]
            
            lead = Lead.objects.create(
                nombre=lead_data['nombre'],
                empresa=lead_data['empresa'],
                cargo=random.choice(['Gerente', 'Director', 'Coordinador', 'Jefe', 'Supervisor']),
                correo=f"{lead_data['nombre'].lower().replace(' ', '.')}@{lead_data['empresa'].lower().replace(' ', '').replace('.', '')[:15]}.com",
                telefono=f'+57 300 {random.randint(1000000, 9999999)}',
                sector_actividad=lead_data['sector'],
                estado=random.choice(estados),
                fuente=random.choice(fuentes),
                nivel_interes=random.choice(niveles_interes),
                necesidad=random.choice(necesidades),
                presupuesto_estimado=Decimal(str(random.randint(50000000, 500000000))),
                fecha_contacto_inicial=timezone.now().date() - timedelta(days=random.randint(1, 90)),
                fecha_ultima_interaccion=timezone.now().date() - timedelta(days=random.randint(0, 30)),
                responsable=random.choice(usuarios),
                notas=f'Lead generado desde {random.choice(fuentes)} con interés en soluciones ambientales.'
            )
            leads.append(lead)
        
        self.stdout.write(f'✅ {len(leads)} leads creados')
        return leads

    def crear_tratos_con_cotizaciones(self, clientes, usuarios):
        """Crea tratos con sus cotizaciones"""
        descripciones = [
            'Sistema de tratamiento de aguas residuales industriales con capacidad de 500 m³/día',
            'Implementación de planta de filtración de agua potable para 1000 personas',
            'Control y monitoreo de emisiones atmosféricas en chimenea industrial',
            'Diseño e instalación de sistema de recirculación de agua en proceso productivo',
            'Tratamiento biológico de efluentes líquidos con carga orgánica alta',
            'Sistema de purificación de agua para uso en laboratorio farmacéutico',
            'Control de olores mediante torres de lavado con carbón activado',
            'Planta de tratamiento de lixiviados en relleno sanitario',
            'Sistema de filtración multimedia para agua de proceso industrial',
            'Monitoreo continuo de calidad del aire en zona urbana',
            'Tratamiento físico-químico de aguas de lavado industrial',
            'Sistema de osmosis inversa para agua de alta pureza',
            'Control de pH y neutralización de efluentes ácidos',
            'Planta compacta de tratamiento de aguas grises',
            'Sistema de aireación y oxigenación para tratamiento biológico'
        ]
        
        estados = ['revision_tecnica', 'elaboracion_oferta', 'envio_negociacion', 'formalizacion', 'ganado', 'perdido']
        tipos = ['contrato', 'control', 'diseno', 'filtros', 'mantenimiento', 'servicios']
        fuentes = ['visita', 'informe_tecnico', 'email', 'telefono', 'whatsapp']
        
        tratos = []
        for i, cliente in enumerate(clientes[:len(descripciones)]):
            contacto = cliente.contactos.first()
            
            # Generar fechas realistas
            fecha_creacion = timezone.now().date() - timedelta(days=random.randint(10, 180))
            fecha_cierre = fecha_creacion + timedelta(days=random.randint(30, 90))
            
            trato = Trato.objects.create(
                nombre=f'Proyecto {i+1} - {cliente.nombre}',
                cliente=cliente,
                contacto=contacto,
                correo=contacto.correo if contacto else '',
                telefono=contacto.telefono if contacto else '',
                descripcion=descripciones[i],
                valor=Decimal(str(random.randint(80000000, 800000000))),
                probabilidad=random.randint(20, 95),
                estado=random.choice(estados),
                tipo_negociacion=random.choice(tipos),
                centro_costos=f'CC-{random.randint(1000, 9999)}',
                nombre_proyecto=f'PROYECTO-{cliente.nombre.split()[0].upper()}-{random.randint(100, 999)}',
                orden_contrato=f'OC-{random.randint(10000, 99999)}',
                dias_prometidos=random.randint(30, 180),
                fuente=random.choice(fuentes),
                fecha_creacion=fecha_creacion,
                fecha_cierre=fecha_cierre,
                responsable=random.choice(usuarios),
                notas=f'Trato generado para {cliente.sector_actividad} con alta probabilidad de cierre.'
            )
            
            # Crear cotización para algunos tratos
            if random.choice([True, False]):
                cotizacion = Cotizacion.objects.create(
                    cliente=cliente,
                    trato=trato,
                    monto=trato.valor,
                    estado=random.choice(['borrador', 'enviada', 'aceptada']),
                    notas=f'Cotización para {trato.descripcion[:50]}...'
                )
                
                # Crear versiones de cotización
                num_versiones = random.randint(1, 3)
                for v in range(1, num_versiones + 1):
                    VersionCotizacion.objects.create(
                        cotizacion=cotizacion,
                        version=v,
                        razon_cambio=f'Versión {v} - {"Ajuste inicial" if v == 1 else "Modificación por solicitud del cliente"}',
                        valor=cotizacion.monto + Decimal(str(random.randint(-10000000, 10000000))),
                        creado_por=random.choice(usuarios)
                    )
            
            tratos.append(trato)
        
        self.stdout.write(f'✅ {len(tratos)} tratos con cotizaciones creados')
        return tratos

    def crear_tareas_venta(self, clientes, tratos, usuarios):
        """Crea tareas de venta"""
        tipos_tarea = ['llamada', 'reunion', 'email', 'seguimiento', 'modificacion']
        estados = ['pendiente', 'en_progreso', 'completada']
        
        titulos_tarea = [
            'Llamada de seguimiento semanal',
            'Reunión técnica con equipo de ingeniería',
            'Envío de propuesta comercial actualizada',
            'Seguimiento post-visita técnica',
            'Revisión de especificaciones técnicas',
            'Presentación de solución técnica',
            'Negociación de condiciones comerciales',
            'Visita a instalaciones del cliente',
            'Entrega de documentación técnica',
            'Coordinación de pruebas piloto'
        ]
        
        descripciones = [
            'Realizar seguimiento del estado actual del proyecto y resolver dudas técnicas pendientes',
            'Coordinar reunión con el equipo técnico para revisar especificaciones del sistema',
            'Enviar propuesta comercial actualizada con modificaciones solicitadas por el cliente',
            'Hacer seguimiento a la visita técnica realizada la semana pasada',
            'Revisar y validar las especificaciones técnicas del proyecto con el cliente',
            'Presentar la solución técnica propuesta al comité de decisión',
            'Negociar términos comerciales y condiciones de pago del contrato',
            'Realizar visita técnica a las instalaciones para validar condiciones',
            'Entregar documentación técnica completa del sistema propuesto',
            'Coordinar y supervisar las pruebas piloto del sistema'
        ]
        
        tareas_creadas = 0
        
        # Crear tareas para algunos tratos
        for trato in random.sample(tratos, min(len(tratos), 15)):
            num_tareas = random.randint(1, 3)
            for i in range(num_tareas):
                fecha_vencimiento = timezone.now().date() + timedelta(days=random.randint(-10, 30))
                
                TareaVenta.objects.create(
                    titulo=random.choice(titulos_tarea),
                    cliente=trato.cliente,
                    trato=trato,
                    tipo=random.choice(tipos_tarea),
                    descripcion=random.choice(descripciones),
                    fecha_vencimiento=fecha_vencimiento,
                    estado=random.choice(estados),
                    responsable=random.choice(usuarios),
                    notas=f'Tarea generada para el trato #{trato.numero_oferta}'
                )
                tareas_creadas += 1
        
        # Crear algunas tareas sin trato asociado
        for cliente in random.sample(clientes, min(len(clientes), 10)):
            TareaVenta.objects.create(
                titulo='Seguimiento comercial general',
                cliente=cliente,
                tipo='seguimiento',
                descripcion='Mantener contacto comercial con el cliente para futuras oportunidades',
                fecha_vencimiento=timezone.now().date() + timedelta(days=random.randint(7, 21)),
                estado=random.choice(estados),
                responsable=random.choice(usuarios),
                notas='Tarea de mantenimiento de relación comercial'
            )
            tareas_creadas += 1
        
        self.stdout.write(f'✅ {tareas_creadas} tareas de venta creadas')