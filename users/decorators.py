from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

def module_permission_required(module, action):
    """
    Decorator que verifica si el usuario tiene permisos específicos para un módulo.
    
    Usage:
        @module_permission_required('crm', 'view')
        def my_view(request):
            # código de la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if request.user.has_module_permission(module, action):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, _('No tienes permisos para realizar esta acción.'))
                return redirect('crm:dashboard')  # Redirigir al dashboard principal
        
        return _wrapped_view
    return decorator

def superuser_required(view_func):
    """
    Decorator que requiere que el usuario sea superusuario.
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, _('Solo los superusuarios pueden acceder a esta sección.'))
            return redirect('crm:dashboard')
    
    return _wrapped_view

def role_required(role_name):
    """
    Decorator que verifica si el usuario tiene un rol específico.
    
    Usage:
        @role_required('Administrador')
        def my_view(request):
            # código de la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if request.user.role and request.user.role.name == role_name and request.user.role.is_active:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, _('No tienes el rol necesario para acceder a esta sección.'))
                return redirect('crm:dashboard')
        
        return _wrapped_view
    return decorator

def any_permission_required(*permissions):
    """
    Decorator que verifica si el usuario tiene al menos uno de los permisos especificados.
    
    Usage:
        @any_permission_required(('crm', 'view'), ('proyectos', 'view'))
        def my_view(request):
            # código de la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            for module, action in permissions:
                if request.user.has_module_permission(module, action):
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, _('No tienes permisos para acceder a esta sección.'))
            return redirect('crm:dashboard')
        
        return _wrapped_view
    return decorator

def all_permissions_required(*permissions):
    """
    Decorator que verifica si el usuario tiene todos los permisos especificados.
    
    Usage:
        @all_permissions_required(('crm', 'view'), ('crm', 'add'))
        def my_view(request):
            # código de la vista
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            for module, action in permissions:
                if not request.user.has_module_permission(module, action):
                    messages.error(request, _('No tienes todos los permisos necesarios para acceder a esta sección.'))
                    return redirect('crm:dashboard')
            
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator