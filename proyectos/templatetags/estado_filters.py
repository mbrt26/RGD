from django import template

register = template.Library()

@register.filter(name='get_estado_badge')
def get_estado_badge(estado):
    """
    Returns the appropriate Bootstrap badge class based on the estado.
    """
    estado_badges = {
        'no_iniciado': 'secondary',
        'en_proceso': 'primary',
        'finalizado': 'success',
        'pendiente': 'warning',
        'en_revision': 'info',
        'aprobado': 'success',
        'rechazado': 'danger',
        'entregado': 'success',
        'completado': 'success',
        'suspendido': 'warning',
        'cancelado': 'danger',
    }
    return estado_badges.get(estado, 'secondary')
