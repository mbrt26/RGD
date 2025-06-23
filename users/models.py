from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class Role(models.Model):
    """Modelo para definir roles en el sistema."""
    name = models.CharField(_('nombre'), max_length=100, unique=True)
    description = models.TextField(_('descripción'), blank=True)
    is_active = models.BooleanField(_('activo'), default=True)
    created_at = models.DateTimeField(_('fecha creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha actualización'), auto_now=True)
    
    class Meta:
        verbose_name = _('Rol')
        verbose_name_plural = _('Roles')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Permission(models.Model):
    """Modelo para definir permisos específicos por módulo."""
    
    MODULE_CHOICES = [
        ('crm', _('CRM')),
        ('proyectos', _('Proyectos')),
        ('servicios', _('Servicios')),
        ('mantenimiento', _('Mantenimiento')),
        ('insumos', _('Insumos')),
        ('tasks', _('Tareas')),
        ('users', _('Usuarios')),
    ]
    
    ACTION_CHOICES = [
        ('view', _('Ver')),
        ('add', _('Crear')),
        ('change', _('Editar')),
        ('delete', _('Eliminar')),
        ('export', _('Exportar')),
        ('import', _('Importar')),
    ]
    
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions', verbose_name=_('rol'))
    module = models.CharField(_('módulo'), max_length=20, choices=MODULE_CHOICES)
    action = models.CharField(_('acción'), max_length=20, choices=ACTION_CHOICES)
    is_granted = models.BooleanField(_('permitido'), default=True)
    
    class Meta:
        verbose_name = _('Permiso')
        verbose_name_plural = _('Permisos')
        unique_together = ['role', 'module', 'action']
        ordering = ['role', 'module', 'action']
    
    def __str__(self):
        return f"{self.role.name} - {self.get_module_display()} - {self.get_action_display()}"

class User(AbstractUser):
    """Custom user model that extends the default User model."""
    email = models.EmailField(_('email address'), unique=True)
    telefono = models.CharField(_('teléfono'), max_length=20, blank=True)
    cargo = models.CharField(_('cargo'), max_length=100, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, 
                           verbose_name=_('rol'), related_name='users')
    created_at = models.DateTimeField(_('fecha creación'), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_('fecha actualización'), auto_now=True, null=True)
    
    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['username']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.username
    
    def has_module_permission(self, module, action):
        """Verifica si el usuario tiene permiso para realizar una acción en un módulo."""
        if self.is_superuser:
            return True
        
        if not self.role or not self.role.is_active:
            return False
            
        try:
            permission = Permission.objects.get(
                role=self.role,
                module=module,
                action=action
            )
            return permission.is_granted
        except Permission.DoesNotExist:
            return False
    
    def get_full_name_display(self):
        """Retorna el nombre completo o username si no hay nombre."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
