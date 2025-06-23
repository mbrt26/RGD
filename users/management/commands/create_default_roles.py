from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from users.models import Role, Permission

class Command(BaseCommand):
    help = 'Crea roles por defecto en el sistema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando roles por defecto...'))
        
        # Crear rol de Administrador con todos los permisos
        admin_role, created = Role.objects.get_or_create(
            name='Administrador',
            defaults={
                'description': 'Acceso completo a todos los módulos del sistema',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Rol "{admin_role.name}" creado')
            # Crear todos los permisos para el administrador
            modules = dict(Permission.MODULE_CHOICES)
            actions = dict(Permission.ACTION_CHOICES)
            
            for module_key in modules.keys():
                for action_key in actions.keys():
                    Permission.objects.get_or_create(
                        role=admin_role,
                        module=module_key,
                        action=action_key,
                        defaults={'is_granted': True}
                    )
        else:
            self.stdout.write(f'- Rol "{admin_role.name}" ya existe')
        
        # Crear rol de Director de Proyectos
        director_role, created = Role.objects.get_or_create(
            name='Director de Proyectos',
            defaults={
                'description': 'Gestión completa de proyectos y acceso limitado a otros módulos',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Rol "{director_role.name}" creado')
            # Permisos específicos para director de proyectos
            project_permissions = [
                ('proyectos', 'view'), ('proyectos', 'add'), ('proyectos', 'change'), ('proyectos', 'delete'), ('proyectos', 'export'),
                ('crm', 'view'), ('crm', 'change'),
                ('servicios', 'view'),
                ('mantenimiento', 'view'),
            ]
            
            for module, action in project_permissions:
                Permission.objects.get_or_create(
                    role=director_role,
                    module=module,
                    action=action,
                    defaults={'is_granted': True}
                )
        else:
            self.stdout.write(f'- Rol "{director_role.name}" ya existe')
        
        # Crear rol de Vendedor
        sales_role, created = Role.objects.get_or_create(
            name='Vendedor',
            defaults={
                'description': 'Gestión de CRM y cotizaciones',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Rol "{sales_role.name}" creado')
            # Permisos específicos para vendedor
            sales_permissions = [
                ('crm', 'view'), ('crm', 'add'), ('crm', 'change'), ('crm', 'export'),
                ('proyectos', 'view'),
            ]
            
            for module, action in sales_permissions:
                Permission.objects.get_or_create(
                    role=sales_role,
                    module=module,
                    action=action,
                    defaults={'is_granted': True}
                )
        else:
            self.stdout.write(f'- Rol "{sales_role.name}" ya existe')
        
        # Crear rol de Técnico
        tech_role, created = Role.objects.get_or_create(
            name='Técnico',
            defaults={
                'description': 'Acceso a servicios técnicos y mantenimiento',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Rol "{tech_role.name}" creado')
            # Permisos específicos para técnico
            tech_permissions = [
                ('servicios', 'view'), ('servicios', 'add'), ('servicios', 'change'),
                ('mantenimiento', 'view'), ('mantenimiento', 'add'), ('mantenimiento', 'change'),
                ('proyectos', 'view'),
            ]
            
            for module, action in tech_permissions:
                Permission.objects.get_or_create(
                    role=tech_role,
                    module=module,
                    action=action,
                    defaults={'is_granted': True}
                )
        else:
            self.stdout.write(f'- Rol "{tech_role.name}" ya existe')
        
        # Crear rol de Solo Lectura
        readonly_role, created = Role.objects.get_or_create(
            name='Solo Lectura',
            defaults={
                'description': 'Solo puede ver información, sin permisos de edición',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write(f'✓ Rol "{readonly_role.name}" creado')
            # Solo permisos de vista
            modules = dict(Permission.MODULE_CHOICES)
            
            for module_key in modules.keys():
                if module_key != 'users':  # No acceso a gestión de usuarios
                    Permission.objects.get_or_create(
                        role=readonly_role,
                        module=module_key,
                        action='view',
                        defaults={'is_granted': True}
                    )
        else:
            self.stdout.write(f'- Rol "{readonly_role.name}" ya existe')
        
        self.stdout.write(
            self.style.SUCCESS('¡Roles por defecto creados exitosamente!')
        )