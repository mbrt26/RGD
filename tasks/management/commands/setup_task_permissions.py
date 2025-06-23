from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from users.models import Role, Permission

class Command(BaseCommand):
    help = 'Configura permisos predeterminados para el módulo de tareas'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Configurando permisos para el módulo de tareas...')
        )

        # Definir configuraciones de permisos por rol
        role_permissions = {
            'Administrador': {
                'tasks': ['view', 'add', 'change', 'delete', 'export', 'import']
            },
            'Director de Proyectos': {
                'tasks': ['view', 'add', 'change', 'export']
            },
            'Vendedor': {
                'tasks': ['view', 'add', 'change']
            },
            'Técnico': {
                'tasks': ['view', 'add', 'change']
            },
            'Solo Lectura': {
                'tasks': ['view']
            },
        }

        # Aplicar permisos para cada rol
        for role_name, modules in role_permissions.items():
            try:
                role = Role.objects.get(name=role_name)
                self.stdout.write(f'Configurando permisos para rol: {role_name}')
                
                for module, actions in modules.items():
                    for action in actions:
                        permission, created = Permission.objects.get_or_create(
                            role=role,
                            module=module,
                            action=action,
                            defaults={'is_granted': True}
                        )
                        
                        if created:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Creado permiso: {module}.{action}'
                                )
                            )
                        else:
                            # Actualizar permiso existente
                            permission.is_granted = True
                            permission.save()
                            self.stdout.write(
                                f'  → Actualizado permiso: {module}.{action}'
                            )
                            
            except Role.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Rol "{role_name}" no existe. Omitiendo...')
                )
                continue

        # Crear categorías predeterminadas
        self.stdout.write('\nCreando categorías predeterminadas...')
        
        from tasks.models import TaskCategory
        
        default_categories = [
            {
                'name': 'Planificación',
                'module': 'proyectos',
                'description': 'Tareas relacionadas con planificación de proyectos',
                'color': '#007bff'
            },
            {
                'name': 'Ejecución',
                'module': 'proyectos',
                'description': 'Tareas de ejecución de actividades de proyecto',
                'color': '#28a745'
            },
            {
                'name': 'Seguimiento',
                'module': 'proyectos',
                'description': 'Tareas de seguimiento y control',
                'color': '#17a2b8'
            },
            {
                'name': 'Soporte Técnico',
                'module': 'servicios',
                'description': 'Tareas de soporte y asistencia técnica',
                'color': '#ffc107'
            },
            {
                'name': 'Instalación',
                'module': 'servicios',
                'description': 'Tareas de instalación de equipos',
                'color': '#fd7e14'
            },
            {
                'name': 'Preventivo',
                'module': 'mantenimiento',
                'description': 'Mantenimiento preventivo programado',
                'color': '#20c997'
            },
            {
                'name': 'Correctivo',
                'module': 'mantenimiento',
                'description': 'Mantenimiento correctivo urgente',
                'color': '#dc3545'
            },
            {
                'name': 'Inventario',
                'module': 'insumos',
                'description': 'Gestión de inventario y almacén',
                'color': '#6f42c1'
            },
            {
                'name': 'Administrativa',
                'module': 'general',
                'description': 'Tareas administrativas generales',
                'color': '#6c757d'
            },
            {
                'name': 'Urgente',
                'module': 'general',
                'description': 'Tareas que requieren atención inmediata',
                'color': '#e83e8c'
            }
        ]
        
        for cat_data in default_categories:
            category, created = TaskCategory.objects.get_or_create(
                name=cat_data['name'],
                module=cat_data['module'],
                defaults={
                    'description': cat_data['description'],
                    'color': cat_data['color'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Creada categoría: {cat_data["name"]} ({cat_data["module"]})'
                    )
                )
            else:
                self.stdout.write(
                    f'  → Categoría ya existe: {cat_data["name"]} ({cat_data["module"]})'
                )

        self.stdout.write(
            self.style.SUCCESS('\n¡Configuración completada exitosamente!')
        )
        self.stdout.write(
            'El módulo de tareas está listo para usar con permisos y categorías configuradas.'
        )