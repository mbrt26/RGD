from django import template
from django.contrib.auth import get_user_model

register = template.Library()

User = get_user_model()

@register.filter
def has_module_permission(user, permission_string):
    """
    Template filter para verificar permisos de módulo.
    Usage: {{ user|has_module_permission:"users:view" }}
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        module, action = permission_string.split(':')
        return user.has_module_permission(module, action)
    except (ValueError, AttributeError):
        return False

@register.simple_tag
def user_can(user, module, action):
    """
    Template tag para verificar permisos de módulo.
    Usage: {% user_can user 'users' 'view' as can_view %}
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    try:
        return user.has_module_permission(module, action)
    except AttributeError:
        return False

@register.inclusion_tag('users/permission_check.html')
def show_if_permitted(user, module, action):
    """
    Inclusion tag para mostrar contenido solo si el usuario tiene permisos.
    Usage: {% show_if_permitted user 'users' 'view' %}
    """
    has_permission = False
    
    if user and user.is_authenticated:
        if user.is_superuser:
            has_permission = True
        else:
            try:
                has_permission = user.has_module_permission(module, action)
            except AttributeError:
                has_permission = False
    
    return {'has_permission': has_permission}