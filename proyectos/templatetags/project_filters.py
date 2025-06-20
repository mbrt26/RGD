from django import template
from django.utils.html import format_html

register = template.Library()

@register.filter
def get_estado_badge(estado):
    """Return the appropriate Bootstrap badge class for the project status."""
    badge_classes = {
        'pendiente': 'secondary',
        'en_ejecucion': 'primary',
        'finalizado': 'success',
        # Mantener estados antiguos para compatibilidad
        'en_progreso': 'primary',
        'en_revision': 'info',
        'completado': 'success',
        'suspendido': 'warning',
        'cancelado': 'danger',
    }
    return badge_classes.get(estado, 'secondary')


@register.filter
def get_avance_color(avance):
    """Return the appropriate Bootstrap progress bar color based on progress percentage."""
    if not avance:
        return 'secondary'
    
    avance = int(avance)
    if avance < 25:
        return 'danger'
    elif avance < 50:
        return 'warning'
    elif avance < 75:
        return 'info'
    else:
        return 'success'

@register.filter
def get_responsable_badge(responsable_ejecucion):
    """Return the appropriate Bootstrap badge class for responsable de ejecución."""
    badge_classes = {
        'rgd': 'success',
        'cliente': 'info',
        'externo': 'warning',
    }
    return badge_classes.get(responsable_ejecucion, 'secondary')

@register.filter
def add_class(field, css_class):
    """Add a CSS class to a form field."""
    return field.as_widget(attrs={'class': css_class})

@register.simple_tag
def progress_bar(value, color_class=''):
    """
    Render a Bootstrap progress bar with the given value and color class.
    
    Usage:
    {% progress_bar value 'bg-success' %}
    """
    html = """
    <div class="progress" style="height: 20px;">
        <div class="progress-bar {}" role="progressbar" 
             style="width: {}%;" 
             aria-valuenow="{}" 
             aria-valuemin="0" 
             aria-valuemax="100">
            {}%
        </div>
    </div>
    """
    return format_html(html, color_class, value, value, value)
