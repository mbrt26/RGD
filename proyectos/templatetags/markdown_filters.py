from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='markdown_to_html')
def markdown_to_html(value):
    """Convierte texto con formato markdown simple a HTML"""
    if not value:
        return ''
    
    # Escapar caracteres HTML
    from django.utils.html import escape
    value = escape(value)
    
    # Convertir negrita
    value = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', value)
    
    # Convertir saltos de línea dobles a párrafos
    paragraphs = value.split('\n\n')
    html_paragraphs = []
    
    for paragraph in paragraphs:
        if paragraph.strip():
            # Convertir saltos de línea simples a <br>
            paragraph = paragraph.replace('\n', '<br>')
            html_paragraphs.append(f'<p>{paragraph}</p>')
    
    return mark_safe(''.join(html_paragraphs))