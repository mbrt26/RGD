from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


class ModulePermissionMixin(UserPassesTestMixin):
    """
    Mixin para verificar permisos de módulo en vistas basadas en clase.
    
    Uso:
        class MyView(LoginRequiredMixin, ModulePermissionMixin, ListView):
            module_name = 'crm'
            permission_action = 'view'  # 'view', 'add', 'change', 'delete'
    """
    module_name = None
    permission_action = 'view'
    
    def test_func(self):
        """Verifica si el usuario tiene el permiso requerido."""
        user = self.request.user
        
        # Superusuarios siempre tienen acceso
        if user.is_superuser:
            return True
        
        # Verificar que se hayan definido el módulo y la acción
        if not self.module_name or not self.permission_action:
            return False
        
        # Verificar el permiso usando el método del modelo User
        return user.has_module_permission(self.module_name, self.permission_action)
    
    def handle_no_permission(self):
        """Maneja el caso cuando el usuario no tiene permisos."""
        messages.error(
            self.request, 
            _('No tienes permisos para realizar esta acción en el módulo %(module)s.') % {
                'module': self.get_module_display()
            }
        )
        return redirect('crm:dashboard')
    
    def get_module_display(self):
        """Retorna el nombre del módulo para mostrar."""
        module_names = {
            'crm': 'CRM',
            'proyectos': 'Proyectos',
            'servicios': 'Servicios',
            'mantenimiento': 'Mantenimiento',
            'insumos': 'Insumos',
            'tasks': 'Tareas',
            'users': 'Usuarios',
        }
        return module_names.get(self.module_name, self.module_name)


class MultiplePermissionsMixin(UserPassesTestMixin):
    """
    Mixin para verificar múltiples permisos (OR lógico).
    El usuario necesita al menos uno de los permisos especificados.
    
    Uso:
        class MyView(LoginRequiredMixin, MultiplePermissionsMixin, ListView):
            permissions_required = [
                ('crm', 'view'),
                ('proyectos', 'view'),
            ]
    """
    permissions_required = []
    
    def test_func(self):
        """Verifica si el usuario tiene al menos uno de los permisos requeridos."""
        user = self.request.user
        
        # Superusuarios siempre tienen acceso
        if user.is_superuser:
            return True
        
        # Verificar que se hayan definido permisos
        if not self.permissions_required:
            return False
        
        # Verificar si tiene al menos uno de los permisos
        for module, action in self.permissions_required:
            if user.has_module_permission(module, action):
                return True
        
        return False
    
    def handle_no_permission(self):
        """Maneja el caso cuando el usuario no tiene permisos."""
        messages.error(
            self.request, 
            _('No tienes los permisos necesarios para acceder a esta sección.')
        )
        return redirect('crm:dashboard')