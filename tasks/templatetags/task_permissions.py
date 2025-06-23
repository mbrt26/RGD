from django import template

register = template.Library()

@register.filter
def can_edit_task(task, user):
    """
    Template filter to check if a user can edit a task.
    Usage: {{ task|can_edit_task:user }}
    """
    if not user or not user.is_authenticated:
        return False
    
    if hasattr(task, 'can_be_edited_by'):
        return task.can_be_edited_by(user)
    
    return False

@register.filter
def can_view_task(task, user):
    """
    Template filter to check if a user can view a task.
    Usage: {{ task|can_view_task:user }}
    """
    if not user or not user.is_authenticated:
        return False
    
    if hasattr(task, 'can_be_viewed_by'):
        return task.can_be_viewed_by(user)
    
    return False