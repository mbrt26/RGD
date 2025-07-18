#!/usr/bin/env python3
"""
Script para crear datos de prueba: 1 proyecto, 1 servicio y 1 comité
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
sys.path.append('/Users/miguelrodriguez/code/RGDAire')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rgd_aire.settings')
django.setup()

from users.models import User
from proyectos.models import Proyecto, Colaborador, ComiteProyecto, SeguimientoProyectoComite
from servicios.models import SolicitudServicio, Tecnico
from crm.models import Cliente, Contacto, Trato, RepresentanteVentas

def create_test_data():
    print("🚀 Creando datos de prueba...")
    
    # 1. Crear usuario admin si no existe
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@rgdaire.com',
            'first_name': 'Admin',
            'last_name': 'RGD',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print("✅ Usuario admin creado")
    else:
        print("✅ Usuario admin ya existe")

    # 2. Crear colaboradores
    colaborador_director, created = Colaborador.objects.get_or_create(
        nombre='Juan Carlos Pérez',
        defaults={
            'cargo': 'Director de Proyectos',
            'email': 'juan.perez@rgdaire.com',
            'telefono': '+57 300 123 4567'
        }
    )
    if created:
        print("✅ Colaborador Director creado")

    colaborador_ingeniero, created = Colaborador.objects.get_or_create(
        nombre='María Fernanda López',
        defaults={
            'cargo': 'Ingeniera Residente',
            'email': 'maria.lopez@rgdaire.com',
            'telefono': '+57 300 987 6543'
        }
    )
    if created:
        print("✅ Colaborador Ingeniero creado")

    # 3. Crear usuario para representante de ventas
    user_representante, created = User.objects.get_or_create(
        username='carlos.martinez',
        defaults={
            'email': 'carlos.martinez@rgdaire.com',
            'first_name': 'Carlos',
            'last_name': 'Martínez',
            'is_staff': False,
            'is_active': True
        }
    )
    if created:
        user_representante.set_password('carlos123')
        user_representante.save()

    # 4. Crear representante CRM
    representante, created = RepresentanteVentas.objects.get_or_create(
        usuario=user_representante,
        defaults={
            'telefono': '+57 301 555 0123',
            'meta_ventas': Decimal('200000000.00')  # Meta de $200M
        }
    )
    if created:
        print("✅ Representante CRM creado")

    # 5. Crear cliente CRM
    cliente, created = Cliente.objects.get_or_create(
        nombre='Empresa Industrial S.A.S.',
        defaults={
            'nit': '900123456-7',
            'direccion': 'Cra 50 # 25-30, Bogotá',
            'telefono': '+57 1 234 5678',
            'correo': 'contacto@empresaindustrial.com',
            'ciudad': 'Bogotá',
            'sector_actividad': 'industrial'
        }
    )
    if created:
        print("✅ Cliente CRM creado")

    # 6. Crear contacto CRM
    contacto, created = Contacto.objects.get_or_create(
        nombre='Ana Sofía García',
        defaults={
            'cargo': 'Gerente de Operaciones',
            'correo': 'ana.garcia@empresaindustrial.com',
            'telefono': '+57 300 456 7890',
            'cliente': cliente
        }
    )
    if created:
        print("✅ Contacto CRM creado")

    # 7. Crear trato CRM
    trato, created = Trato.objects.get_or_create(
        nombre='Mantenimiento Sistema HVAC 2024',
        defaults={
            'cliente': cliente,
            'contacto': contacto,
            'responsable': user_representante,
            'valor': Decimal('45000000.00'),  # $45,000,000
            'estado': 'envio_negociacion',
            'probabilidad': 75,
            'fecha_cierre': datetime.now().date() + timedelta(days=30),
            'descripcion': 'Contrato anual de mantenimiento preventivo y correctivo para sistema HVAC',
            'tipo_negociacion': 'mantenimiento',
            'centro_costos': 'CC-HVAC-001',
            'nombre_proyecto': 'Mantenimiento HVAC 2024'
        }
    )
    if created:
        print("✅ Trato CRM creado")

    # 8. Crear proyecto
    proyecto, created = Proyecto.objects.get_or_create(
        nombre_proyecto='Modernización Sistema HVAC - Planta Norte',
        defaults={
            'cliente': 'Empresa Industrial S.A.S.',
            'descripcion': 'Modernización completa del sistema HVAC de la planta norte incluyendo reemplazo de equipos, actualización de controles y optimización energética.',
            'fecha_inicio': datetime.now().date(),
            'fecha_fin': datetime.now().date() + timedelta(days=120),
            'estado': 'en_ejecucion',
            'avance': 35.5,
            'avance_planeado': 40.0,
            'presupuesto': Decimal('120000000.00'),  # $120,000,000
            'gasto_real': Decimal('38000000.00'),    # $38,000,000
            'director_proyecto': colaborador_director,
            'prioridad': 'alta',
            'centro_costo': 'CC-001-HVAC',
            'activo': True
        }
    )
    if created:
        print("✅ Proyecto creado")

    # 9. Crear usuario para técnico
    user_tecnico, created = User.objects.get_or_create(
        username='luis.rodriguez',
        defaults={
            'email': 'luis.rodriguez@rgdaire.com',
            'first_name': 'Luis Alberto',
            'last_name': 'Rodríguez',
            'is_staff': False,
            'is_active': True
        }
    )
    if created:
        user_tecnico.set_password('luis123')
        user_tecnico.save()

    # 10. Crear técnico
    tecnico, created = Tecnico.objects.get_or_create(
        codigo_tecnico='TEC001',
        defaults={
            'usuario': user_tecnico,
            'especialidades': 'HVAC - Sistemas de climatización y ventilación',
            'telefono': '+57 300 111 2233',
            'activo': True
        }
    )
    if created:
        print("✅ Técnico creado")

    # 11. Crear servicio
    servicio, created = SolicitudServicio.objects.get_or_create(
        numero_orden='FS202400001',
        defaults={
            'tipo_servicio': 'correctivo',
            'cliente_crm': cliente,
            'contacto_crm': contacto,
            'trato_origen': trato,
            'direccion_servicio': 'Cra 50 # 25-30, Planta Norte, Bogotá',
            'centro_costo': 'CC-001-SERV',
            'nombre_proyecto': 'Reparación Urgente Chiller Principal',
            'orden_contrato': 'OC-2024-0045',
            'dias_prometidos': 3,
            'fecha_programada': datetime.now().date() + timedelta(days=2),
            'duracion_estimada': timedelta(hours=8),
            'tecnico_asignado': tecnico,
            'director_proyecto': colaborador_director,
            'ingeniero_residente': colaborador_ingeniero,
            'observaciones_internas': 'Falla reportada en compresor principal. Requiere atención urgente para evitar parada de producción.',
            'estado': 'en_ejecucion',
            'prioridad': 'urgente'
        }
    )
    if created:
        print("✅ Servicio creado")

    # 12. Crear comité
    comite, created = ComiteProyecto.objects.get_or_create(
        nombre='Comité de Seguimiento Mensual - Enero 2024',
        defaults={
            'fecha_comite': datetime.now() + timedelta(days=7),
            'tipo_comite': 'seguimiento',
            'lugar': 'Sala de Juntas Principal - Oficina Central',
            'coordinador': colaborador_director,
            'duracion_estimada': 120,  # 2 horas
            'agenda': '''1. Revisión de avance de proyectos activos
2. Análisis de servicios críticos
3. Evaluación de recursos y cronogramas
4. Identificación de riesgos y oportunidades
5. Definición de acciones correctivas
6. Próximos pasos y fechas clave''',
            'observaciones': 'Comité de seguimiento mensual para evaluar el estado de proyectos y servicios activos.',
            'estado': 'programado',
            'creado_por': admin_user
        }
    )
    if created:
        print("✅ Comité creado")

    # 13. Crear seguimiento del proyecto en el comité
    seguimiento, created = SeguimientoProyectoComite.objects.get_or_create(
        comite=comite,
        proyecto=proyecto,
        defaults={
            'avance_reportado': 35.5,
            'avance_anterior': 28.0,
            'estado_seguimiento': 'amarillo',  # Ligeramente atrasado
            'logros_periodo': '''- Completada instalación de nuevos ductos principales (Zona A)
- Finalizada actualización de tableros de control
- Iniciadas pruebas de integración con sistema existente
- Capacitación técnica al personal de mantenimiento''',
            'obstaculos_identificados': '''- Retraso en entrega de componentes especializados (5 días)
- Necesidad de coordinación adicional con producción para paradas programadas
- Requerimiento de certificación adicional para nuevos controles''',
            'acciones_requeridas': '''- Acelerar gestión de importación de componentes faltantes
- Programar reunión con gerencia de producción para definir ventanas de trabajo
- Contactar certificadora para agilizar proceso de homologación''',
            'fecha_proximo_hito': datetime.now().date() + timedelta(days=14),
            'responsable_reporte': colaborador_director,
            'orden_presentacion': 1,
            'tiempo_asignado': 15,  # 15 minutos
            'presupuesto_ejecutado': Decimal('38000000.00'),
            'requiere_decision': True,
            'observaciones': 'Proyecto requiere atención especial por demoras en importaciones. Se recomienda evaluar proveedores alternativos.'
        }
    )
    if created:
        print("✅ Seguimiento de proyecto en comité creado")

    print("\n🎉 ¡Datos de prueba creados exitosamente!")
    print("\n📊 Resumen de datos creados:")
    print(f"👤 Usuario: {admin_user.username}")
    print(f"👥 Colaboradores: {Colaborador.objects.count()}")
    print(f"🏢 Cliente: {cliente.nombre}")
    print(f"📞 Contacto: {contacto.nombre}")
    print(f"🤝 Trato: {trato.nombre}")
    print(f"📋 Proyecto: {proyecto.nombre_proyecto}")
    print(f"🔧 Servicio: {servicio.numero_orden}")
    print(f"👨‍🔧 Técnico: {tecnico.nombre}")
    print(f"📅 Comité: {comite.nombre}")
    print(f"📈 Seguimiento: Proyecto incluido en comité")
    
    print(f"\n🌐 URLs para probar:")
    print(f"- Comité: http://localhost:8080/proyectos/comite/{comite.pk}/")
    print(f"- Proyecto: http://localhost:8080/proyectos/proyecto/{proyecto.pk}/")
    print(f"- Servicio: http://localhost:8080/servicios/solicitudes/{servicio.pk}/")
    print(f"- Admin: http://localhost:8080/admin/")

if __name__ == '__main__':
    create_test_data()