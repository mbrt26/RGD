from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from tasks.models import Task, TaskCategory, TaskComment, TaskHistory
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea tareas de ejemplo para demostrar el funcionamiento del gestor'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Creando tareas de ejemplo...')
        )

        # Obtener usuarios y categorías
        try:
            users = list(User.objects.filter(is_active=True))
            categories = list(TaskCategory.objects.filter(is_active=True))
            
            if not users:
                self.stdout.write(
                    self.style.ERROR('No hay usuarios activos. Creando usuario de prueba...')
                )
                admin_user = User.objects.create_user(
                    username='admin_tasks',
                    email='admin@rgdaire.com',
                    password='admin123',
                    first_name='Administrador',
                    last_name='Tareas',
                    is_staff=True,
                    is_superuser=True
                )
                users = [admin_user]
                
            if not categories:
                self.stdout.write(
                    self.style.WARNING('No hay categorías. Ejecuta primero setup_task_permissions')
                )
                return

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al obtener datos: {e}')
            )
            return

        # Tareas de ejemplo
        sample_tasks = [
            {
                'title': 'Revisar propuesta técnica Cliente ABC',
                'description': 'Analizar los requerimientos técnicos del proyecto de ventilación industrial para Cliente ABC. Verificar especificaciones de equipos y dimensionamiento de ductos.',
                'priority': 'high',
                'task_type': 'review',
                'estimated_hours': 4.0,
                'days_offset': -2  # Vence en 2 días
            },
            {
                'title': 'Mantenimiento preventivo Equipo #001',
                'description': 'Realizar mantenimiento preventivo programado al sistema de extracción de la planta principal. Incluye limpieza de filtros y verificación de motores.',
                'priority': 'medium',
                'task_type': 'task',
                'estimated_hours': 6.0,
                'days_offset': 1  # Vence mañana
            },
            {
                'title': 'Seguimiento proyecto Industria XYZ',
                'description': 'Llamada de seguimiento con el cliente para revisar el avance del proyecto de instalación del sistema de ventilación.',
                'priority': 'medium',
                'task_type': 'call',
                'estimated_hours': 1.0,
                'days_offset': 0  # Vence hoy
            },
            {
                'title': 'Actualizar inventario filtros HEPA',
                'description': 'Revisar y actualizar el inventario de filtros HEPA. Verificar stock disponible y generar orden de compra si es necesario.',
                'priority': 'low',
                'task_type': 'task',
                'estimated_hours': 2.0,
                'days_offset': 7  # Vence en una semana
            },
            {
                'title': 'Reunión de planificación semanal',
                'description': 'Reunión del equipo técnico para revisar el avance de proyectos activos y planificar actividades de la próxima semana.',
                'priority': 'medium',
                'task_type': 'meeting',
                'estimated_hours': 2.0,
                'days_offset': 3,  # Vence en 3 días
                'is_recurring': True,
                'recurrence_pattern': 'weekly'
            },
            {
                'title': 'URGENTE: Reparación sistema Cliente Emergencia',
                'description': 'Atender emergencia en el sistema de ventilación del Cliente Emergencia. Falla en motor principal requiere atención inmediata.',
                'priority': 'urgent',
                'task_type': 'task',
                'estimated_hours': 8.0,
                'days_offset': -1  # Vencida (ayer)
            },
            {
                'title': 'Cotizar repuestos Motor Siemens',
                'description': 'Solicitar cotización para repuestos del motor Siemens modelo XYZ123. Cliente solicita presupuesto para mantenimiento preventivo.',
                'priority': 'medium',
                'task_type': 'other',
                'estimated_hours': 1.5,
                'days_offset': 5
            },
            {
                'title': 'Capacitación uso equipos nuevos',
                'description': 'Realizar capacitación al personal técnico sobre el uso y mantenimiento de los nuevos equipos de medición de calidad de aire.',
                'priority': 'medium',
                'task_type': 'other',
                'estimated_hours': 4.0,
                'days_offset': 10
            }
        ]

        created_tasks = []
        
        for i, task_data in enumerate(sample_tasks):
            try:
                # Seleccionar usuario y categoría aleatoriamente
                assigned_user = random.choice(users)
                created_user = random.choice(users)
                category = random.choice(categories)
                
                # Calcular fechas
                due_date = timezone.now() + timedelta(days=task_data['days_offset'])
                start_date = due_date - timedelta(days=random.randint(1, 5))
                
                # Determinar estado basado en si está vencida
                if task_data['days_offset'] < 0:
                    status = random.choice(['in_progress', 'pending'])
                    progress = random.randint(10, 70)
                elif task_data['days_offset'] == 0:
                    status = 'in_progress'
                    progress = random.randint(30, 90)
                else:
                    status = random.choice(['pending', 'in_progress'])
                    progress = random.randint(0, 50) if status == 'pending' else random.randint(10, 80)
                
                # Algunas tareas completadas
                if i % 5 == 0:  # Cada 5 tareas
                    status = 'completed'
                    progress = 100
                
                # Crear tarea
                task = Task.objects.create(
                    title=task_data['title'],
                    description=task_data['description'],
                    assigned_to=assigned_user,
                    created_by=created_user,
                    category=category,
                    status=status,
                    priority=task_data['priority'],
                    task_type=task_data['task_type'],
                    start_date=start_date,
                    due_date=due_date,
                    estimated_hours=task_data['estimated_hours'],
                    progress_percentage=progress,
                    is_recurring=task_data.get('is_recurring', False),
                    recurrence_pattern=task_data.get('recurrence_pattern', '')
                )
                
                # Si está completada, agregar fecha de completado
                if status == 'completed':
                    task.completed_date = due_date - timedelta(days=random.randint(0, 2))
                    task.actual_hours = task_data['estimated_hours'] + random.uniform(-1, 2)
                    task.save()
                
                created_tasks.append(task)
                
                # Crear entrada en historial
                TaskHistory.objects.create(
                    task=task,
                    action='created',
                    user=created_user,
                    description=f'Tarea creada y asignada a {assigned_user.get_full_name_display()}'
                )
                
                # Agregar algunos comentarios a tareas aleatorias
                if random.random() < 0.4:  # 40% de probabilidad
                    comments = [
                        'Iniciando trabajo en esta tarea.',
                        'Necesito más información del cliente.',
                        'Trabajo en progreso, sin problemas hasta ahora.',
                        'Cliente confirmó disponibilidad para la visita.',
                        'Equipo revisado, todo en orden.',
                        'Pendiente confirmación de repuestos.'
                    ]
                    
                    comment_text = random.choice(comments)
                    TaskComment.objects.create(
                        task=task,
                        author=assigned_user,
                        content=comment_text,
                        is_internal=random.choice([True, False])
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Creada tarea: {task.title[:50]}... ({task.get_status_display()})'
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creando tarea {i+1}: {e}')
                )

        # Estadísticas finales
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Creadas {len(created_tasks)} tareas de ejemplo exitosamente!'
            )
        )
        
        # Mostrar estadísticas
        from django.db.models import Count
        stats = Task.objects.values('status').annotate(count=Count('status'))
        
        self.stdout.write('\nEstadísticas de tareas creadas:')
        for stat in stats:
            status_display = dict(Task.STATUS_CHOICES).get(stat['status'], stat['status'])
            self.stdout.write(f'  - {status_display}: {stat["count"]} tareas')
        
        priority_stats = Task.objects.values('priority').annotate(count=Count('priority'))
        self.stdout.write('\nPor prioridad:')
        for stat in priority_stats:
            priority_display = dict(Task.PRIORITY_CHOICES).get(stat['priority'], stat['priority'])
            self.stdout.write(f'  - {priority_display}: {stat["count"]} tareas')
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                '¡El gestor de tareas está listo para usar!\n'
                'Puedes acceder al dashboard en: /tasks/'
            )
        )