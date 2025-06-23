from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from mejora_continua.models import SolicitudMejora, ComentarioSolicitud

User = get_user_model()

class Command(BaseCommand):
    help = 'Genera datos de ejemplo para el módulo de mejora continua'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=15,
            help='Cantidad de solicitudes a crear'
        )

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        
        # Obtener usuarios existentes
        usuarios = list(User.objects.all())
        if not usuarios:
            self.stdout.write(
                self.style.ERROR('No hay usuarios en el sistema. Crea al menos un usuario primero.')
            )
            return

        # Datos de ejemplo para solicitudes
        solicitudes_ejemplo = [
            {
                'titulo': 'Mejorar velocidad de carga del dashboard CRM',
                'descripcion': 'El dashboard del CRM tarda mucho en cargar cuando hay muchos tratos. Sería necesario optimizar las consultas a la base de datos.',
                'tipo_solicitud': 'mejora',
                'modulo_afectado': 'crm',
                'prioridad': 'alta',
                'pasos_reproducir': '1. Ir al dashboard CRM\n2. Observar el tiempo de carga\n3. El tiempo supera los 5 segundos',
                'impacto_negocio': 'Los usuarios comerciales pierden tiempo esperando que cargue la información, reduciendo su productividad.',
                'solucion_propuesta': 'Implementar paginación en las tablas y optimizar las consultas con select_related.'
            },
            {
                'titulo': 'Agregar filtros avanzados en lista de proyectos',
                'descripcion': 'Los usuarios necesitan filtrar proyectos por múltiples criterios como estado, director, fecha de inicio, etc.',
                'tipo_solicitud': 'nueva_funcionalidad',
                'modulo_afectado': 'proyectos',
                'prioridad': 'media',
                'impacto_negocio': 'Facilitaría la gestión de proyectos y ahorraría tiempo en la búsqueda de información específica.',
                'solucion_propuesta': 'Crear un formulario de filtros con campos múltiples y aplicar filtros dinámicos.'
            },
            {
                'titulo': 'Error al generar reporte de mantenimiento',
                'descripcion': 'Al intentar generar el reporte mensual de mantenimiento, la aplicación muestra un error 500.',
                'tipo_solicitud': 'problema',
                'modulo_afectado': 'mantenimiento',
                'prioridad': 'critica',
                'pasos_reproducir': '1. Ir a Mantenimiento > Reportes\n2. Seleccionar mes actual\n3. Hacer clic en "Generar Reporte"\n4. Aparece error 500',
                'impacto_negocio': 'No se pueden generar reportes mensuales requeridos para la gestión.',
            },
            {
                'titulo': 'Notificaciones por email para tareas vencidas',
                'descripcion': 'Implementar un sistema de notificaciones automáticas que envíe emails cuando las tareas estén próximas a vencer.',
                'tipo_solicitud': 'nueva_funcionalidad',
                'modulo_afectado': 'tasks',
                'prioridad': 'media',
                'impacto_negocio': 'Mejorará el seguimiento de tareas y reducirá los olvidos.',
                'solucion_propuesta': 'Crear comando de Django que se ejecute diariamente y envíe emails a usuarios con tareas vencidas.'
            },
            {
                'titulo': 'Optimizar exportación de datos de servicios',
                'descripcion': 'La exportación de datos de servicios a Excel es muy lenta cuando hay muchos registros.',
                'tipo_solicitud': 'mejora',
                'modulo_afectado': 'servicios',
                'prioridad': 'baja',
                'impacto_negocio': 'Los usuarios deben esperar mucho tiempo para obtener reportes.',
                'solucion_propuesta': 'Implementar procesamiento en background con Celery.'
            },
            {
                'titulo': 'Agregar campo "Urgente" en solicitudes de servicio',
                'descripcion': 'Necesitamos un campo para marcar solicitudes de servicio como urgentes y priorizarlas.',
                'tipo_solicitud': 'modificacion',
                'modulo_afectado': 'servicios',
                'prioridad': 'media',
                'impacto_negocio': 'Permitirá mejor gestión de emergencias y servicios críticos.'
            },
            {
                'titulo': 'Error en cálculo de presupuesto de proyectos',
                'descripcion': 'Los cálculos automáticos de presupuesto no incluyen correctamente los costos indirectos.',
                'tipo_solicitud': 'problema',
                'modulo_afectado': 'proyectos',
                'prioridad': 'alta',
                'pasos_reproducir': '1. Crear nuevo proyecto\n2. Agregar actividades con costos\n3. El total no incluye costos indirectos del 15%',
                'impacto_negocio': 'Presupuestos incorrectos pueden causar pérdidas económicas.'
            },
            {
                'titulo': 'Dashboard para gestión de inventario de insumos',
                'descripcion': 'Crear un dashboard que muestre el estado actual del inventario, productos con stock bajo, etc.',
                'tipo_solicitud': 'nueva_funcionalidad',
                'modulo_afectado': 'insumos',
                'prioridad': 'media',
                'impacto_negocio': 'Mejorará la gestión de inventario y evitará faltantes.'
            },
            {
                'titulo': 'Mejorar interfaz de usuario en móviles',
                'descripcion': 'La aplicación no es completamente responsive en dispositivos móviles, especialmente en tablets.',
                'tipo_solicitud': 'mejora',
                'modulo_afectado': 'general',
                'prioridad': 'media',
                'impacto_negocio': 'Los usuarios móviles tienen dificultades para usar la aplicación.'
            },
            {
                'titulo': 'Integración con sistema de contabilidad',
                'descripcion': 'Necesitamos integrar la aplicación con el sistema de contabilidad para sincronizar facturas y pagos.',
                'tipo_solicitud': 'nueva_funcionalidad',
                'modulo_afectado': 'general',
                'prioridad': 'alta',
                'impacto_negocio': 'Eliminaría la doble captura de datos y reduciría errores.'
            },
            {
                'titulo': 'Error al subir archivos grandes',
                'descripcion': 'No se pueden subir archivos de más de 10MB en ningún módulo de la aplicación.',
                'tipo_solicitud': 'problema',
                'modulo_afectado': 'general',
                'prioridad': 'media',
                'pasos_reproducir': '1. Intentar subir archivo > 10MB\n2. La carga se interrumpe\n3. Muestra error de timeout',
                'impacto_negocio': 'Limita el tipo de documentos que se pueden gestionar.'
            },
            {
                'titulo': 'Tema oscuro para la aplicación',
                'descripcion': 'Implementar un tema oscuro opcional para mejorar la experiencia de usuario.',
                'tipo_solicitud': 'nueva_funcionalidad',
                'modulo_afectado': 'general',
                'prioridad': 'baja',
                'impacto_negocio': 'Mejorará la comodidad de usuarios que trabajan en horarios nocturnos.'
            },
            {
                'titulo': 'Backup automático de base de datos',
                'descripcion': 'Implementar sistema de backups automáticos diarios de la base de datos.',
                'tipo_solicitud': 'nueva_funcionalidad',
                'modulo_afectado': 'general',
                'prioridad': 'critica',
                'impacto_negocio': 'Asegurará la continuidad del negocio en caso de fallas.'
            },
            {
                'titulo': 'Búsqueda global en toda la aplicación',
                'descripcion': 'Agregar una barra de búsqueda global que permita buscar en todos los módulos.',
                'tipo_solicitud': 'nueva_funcionalidad',
                'modulo_afectado': 'general',
                'prioridad': 'media',
                'impacto_negocio': 'Facilitará encontrar información rápidamente.'
            },
            {
                'titulo': 'Corrección en permisos de usuarios',
                'descripcion': 'Algunos usuarios pueden acceder a módulos para los que no tienen permisos.',
                'tipo_solicitud': 'problema',
                'modulo_afectado': 'users',
                'prioridad': 'alta',
                'impacto_negocio': 'Problema de seguridad que debe resolverse pronto.'
            }
        ]

        # Comentarios de ejemplo
        comentarios_ejemplo = [
            "Solicitud recibida, revisando factibilidad técnica.",
            "Necesitamos más detalles sobre los requerimientos específicos.",
            "Solicitud aprobada, asignando a equipo de desarrollo.",
            "Iniciando desarrollo, tiempo estimado: 2 semanas.",
            "Primera versión lista para pruebas.",
            "Pruebas completadas satisfactoriamente.",
            "Implementación completada y en producción.",
            "Solicitud requiere análisis adicional de costos.",
            "Consultando con el equipo de infraestructura.",
            "Prioridad ajustada debido a impacto en negocio.",
        ]

        self.stdout.write('Generando datos de ejemplo...')

        # Crear solicitudes
        solicitudes_creadas = 0
        
        for i in range(cantidad):
            # Seleccionar datos aleatorios
            if i < len(solicitudes_ejemplo):
                datos = solicitudes_ejemplo[i]
            else:
                # Generar datos aleatorios para solicitudes adicionales
                datos = {
                    'titulo': f'Solicitud de mejora #{i+1}',
                    'descripcion': f'Descripción detallada de la solicitud número {i+1}',
                    'tipo_solicitud': random.choice(['modificacion', 'nueva_funcionalidad', 'problema', 'mejora', 'otro']),
                    'modulo_afectado': random.choice(['crm', 'proyectos', 'servicios', 'mantenimiento', 'insumos', 'users', 'general']),
                    'prioridad': random.choice(['baja', 'media', 'alta', 'critica']),
                    'impacto_negocio': 'Impacto general en las operaciones del negocio.'
                }
            
            # Seleccionar usuario aleatorio
            solicitante = random.choice(usuarios)
            
            # Crear solicitud
            solicitud = SolicitudMejora.objects.create(
                titulo=datos['titulo'],
                descripcion=datos['descripcion'],
                tipo_solicitud=datos['tipo_solicitud'],
                modulo_afectado=datos['modulo_afectado'],
                prioridad=datos['prioridad'],
                solicitante=solicitante,
                pasos_reproducir=datos.get('pasos_reproducir', ''),
                impacto_negocio=datos.get('impacto_negocio', ''),
                solucion_propuesta=datos.get('solucion_propuesta', ''),
            )
            
            # Asignar estado aleatorio y fechas
            estados_posibles = ['pendiente', 'en_revision', 'aprobada', 'en_desarrollo', 'completada', 'rechazada']
            nuevo_estado = random.choice(estados_posibles)
            solicitud.estado = nuevo_estado
            
            # Si no está pendiente, asignar a un usuario staff
            if nuevo_estado != 'pendiente':
                staff_users = [u for u in usuarios if u.is_staff]
                if staff_users:
                    solicitud.asignado_a = random.choice(staff_users)
                    solicitud.fecha_asignacion = timezone.now() - timedelta(days=random.randint(1, 30))
            
            # Si está completada, agregar fecha de completado
            if nuevo_estado == 'completada':
                solicitud.fecha_completado = timezone.now() - timedelta(days=random.randint(1, 10))
            elif nuevo_estado in ['en_desarrollo', 'aprobada']:
                solicitud.fecha_estimada_completado = timezone.now() + timedelta(days=random.randint(5, 30))
            
            # Ajustar fecha de solicitud
            solicitud.fecha_solicitud = timezone.now() - timedelta(days=random.randint(1, 60))
            solicitud.save()
            
            # Agregar comentarios aleatorios
            num_comentarios = random.randint(0, 3)
            for _ in range(num_comentarios):
                ComentarioSolicitud.objects.create(
                    solicitud=solicitud,
                    autor=random.choice(usuarios),
                    comentario=random.choice(comentarios_ejemplo),
                    es_interno=random.choice([True, False]) if random.choice(usuarios).is_staff else False,
                    fecha_comentario=solicitud.fecha_solicitud + timedelta(days=random.randint(1, 30))
                )
            
            solicitudes_creadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Se crearon {solicitudes_creadas} solicitudes de mejora con comentarios.'
            )
        )
        
        # Mostrar estadísticas
        total_solicitudes = SolicitudMejora.objects.count()
        por_estado = {}
        for estado, _ in SolicitudMejora.ESTADO_CHOICES:
            count = SolicitudMejora.objects.filter(estado=estado).count()
            if count > 0:
                por_estado[estado] = count
        
        self.stdout.write('\n📊 Estadísticas:')
        self.stdout.write(f'   Total de solicitudes: {total_solicitudes}')
        for estado, count in por_estado.items():
            self.stdout.write(f'   {estado.title()}: {count}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 Datos de ejemplo generados exitosamente para el módulo de mejora continua!'
            )
        )