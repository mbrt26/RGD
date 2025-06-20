from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone

register = template.Library()


@register.filter
def porcentaje_ejecucion_badge(proyecto):
    """Genera un badge visual para mostrar el porcentaje de ejecución del presupuesto"""
    if not proyecto:
        return ""
    
    porcentaje = proyecto.porcentaje_ejecucion_presupuesto
    avance = float(proyecto.avance)
    
    # Determinar color basado en la comparación con el avance
    if porcentaje > avance + 20:
        color = 'danger'
        icono = 'exclamation-triangle'
        estado = 'Sobreejecución'
    elif porcentaje > avance + 10:
        color = 'warning'
        icono = 'exclamation-triangle'
        estado = 'Ejecución Alta'
    elif porcentaje < avance - 15:
        color = 'info'
        icono = 'info-circle'
        estado = 'Subejecución'
    else:
        color = 'success'
        icono = 'check-circle'
        estado = 'Normal'
    
    return mark_safe(
        f'<span class="badge bg-{color}" title="{estado}">'
        f'<i class="fas fa-{icono} me-1"></i>'
        f'{porcentaje:.1f}%'
        f'</span>'
    )


@register.filter
def estado_presupuesto_badge(proyecto):
    """Genera un badge para mostrar el estado del presupuesto"""
    if not proyecto:
        return ""
    
    estado = proyecto.estado_presupuesto
    
    configuracion = {
        'normal': {
            'color': 'success',
            'icono': 'check-circle',
            'texto': 'Normal'
        },
        'sobreejecucion_moderada': {
            'color': 'warning',
            'icono': 'exclamation-triangle',
            'texto': 'Sobreejecución Moderada'
        },
        'sobreejecucion_critica': {
            'color': 'danger',
            'icono': 'exclamation-triangle',
            'texto': 'Sobreejecución Crítica'
        },
        'subejecucion_leve': {
            'color': 'info',
            'icono': 'info-circle',
            'texto': 'Subejecución Leve'
        },
        'subejecucion_alta': {
            'color': 'secondary',
            'icono': 'minus-circle',
            'texto': 'Subejecución Alta'
        }
    }
    
    config = configuracion.get(estado, {
        'color': 'secondary',
        'icono': 'question',
        'texto': 'Sin datos'
    })
    
    return mark_safe(
        f'<span class="badge bg-{config["color"]}">'
        f'<i class="fas fa-{config["icono"]} me-1"></i>'
        f'{config["texto"]}'
        f'</span>'
    )


@register.filter
def progreso_presupuesto_visual(proyecto):
    """Genera una barra de progreso visual del presupuesto vs avance"""
    if not proyecto:
        return ""
    
    porcentaje_gasto = proyecto.porcentaje_ejecucion_presupuesto
    avance_real = float(proyecto.avance)
    
    # Determinar colores
    if porcentaje_gasto > avance_real + 15:
        color_gasto = 'danger'
        color_avance = 'success'
    elif porcentaje_gasto > avance_real + 5:
        color_gasto = 'warning'
        color_avance = 'success'
    else:
        color_gasto = 'primary'
        color_avance = 'success'
    
    return mark_safe(f'''
        <div class="progress position-relative mb-1" style="height: 25px;">
            <div class="progress-bar bg-{color_gasto}" role="progressbar" 
                 style="width: {min(porcentaje_gasto, 100)}%"
                 title="Ejecución presupuesto: {porcentaje_gasto:.1f}%">
            </div>
            <div class="progress-bar bg-{color_avance} progress-bar-striped" role="progressbar" 
                 style="width: {min(avance_real, 100)}%; margin-left: -{min(porcentaje_gasto, 100)}%; opacity: 0.8"
                 title="Avance físico: {avance_real}%">
            </div>
            <small class="position-absolute w-100 text-center text-dark fw-bold" 
                   style="top: 4px;">
                💰 {porcentaje_gasto:.1f}% / 🔧 {avance_real:.1f}%
            </small>
        </div>
        <small class="text-muted">Presupuesto / Avance</small>
    ''')


@register.filter
def riesgo_sobrecosto_badge(proyecto):
    """Genera un badge del riesgo de sobrecosto"""
    if not proyecto:
        return ""
    
    riesgo = proyecto.riesgo_sobrecosto
    
    configuracion = {
        'dentro_presupuesto': {
            'color': 'success',
            'icono': 'check-circle',
            'texto': 'Dentro Presupuesto'
        },
        'bajo': {
            'color': 'info',
            'icono': 'info-circle',
            'texto': 'Riesgo Bajo'
        },
        'moderado': {
            'color': 'warning',
            'icono': 'exclamation-triangle',
            'texto': 'Riesgo Moderado'
        },
        'alto': {
            'color': 'danger',
            'icono': 'exclamation-triangle',
            'texto': 'Riesgo Alto'
        },
        'sin_presupuesto': {
            'color': 'secondary',
            'icono': 'question',
            'texto': 'Sin Presupuesto'
        }
    }
    
    config = configuracion.get(riesgo, configuracion['sin_presupuesto'])
    
    return mark_safe(
        f'<span class="badge bg-{config["color"]}">'
        f'<i class="fas fa-{config["icono"]} me-1"></i>'
        f'{config["texto"]}'
        f'</span>'
    )


@register.filter
def presupuesto_disponible_badge(proyecto):
    """Genera un badge del presupuesto disponible"""
    if not proyecto:
        return ""
    
    disponible = proyecto.presupuesto_disponible
    porcentaje_disponible = (disponible / float(proyecto.presupuesto) * 100) if proyecto.presupuesto > 0 else 0
    
    if porcentaje_disponible <= 5:
        color = 'danger'
        icono = 'exclamation-triangle'
    elif porcentaje_disponible <= 15:
        color = 'warning'
        icono = 'exclamation-circle'
    else:
        color = 'success'
        icono = 'check-circle'
    
    return mark_safe(
        f'<span class="badge bg-{color}">'
        f'<i class="fas fa-{icono} me-1"></i>'
        f'${disponible:,.0f} ({porcentaje_disponible:.1f}%)'
        f'</span>'
    )


@register.filter
def eficiencia_presupuestaria_badge(proyecto):
    """Genera un badge de eficiencia presupuestaria"""
    if not proyecto:
        return ""
    
    eficiencia = proyecto.eficiencia_presupuestaria
    
    if eficiencia == float('inf'):
        return mark_safe('<span class="badge bg-info">Sin Gastos</span>')
    
    if eficiencia >= 1.2:
        color = 'success'
        icono = 'thumbs-up'
        texto = f'Eficiente ({eficiencia:.2f})'
    elif eficiencia >= 0.8:
        color = 'primary'
        icono = 'balance-scale'
        texto = f'Normal ({eficiencia:.2f})'
    elif eficiencia >= 0.6:
        color = 'warning'
        icono = 'exclamation-triangle'
        texto = f'Ineficiente ({eficiencia:.2f})'
    else:
        color = 'danger'
        icono = 'thumbs-down'
        texto = f'Muy Ineficiente ({eficiencia:.2f})'
    
    return mark_safe(
        f'<span class="badge bg-{color}">'
        f'<i class="fas fa-{icono} me-1"></i>'
        f'{texto}'
        f'</span>'
    )


@register.filter
def alertas_presupuesto_list(proyecto):
    """Genera una lista HTML con las alertas de presupuesto del proyecto"""
    if not proyecto:
        return ""
    
    alertas = proyecto.get_alertas_presupuesto()
    
    if not alertas:
        return mark_safe('<small class="text-success"><i class="fas fa-check-circle me-1"></i>Sin alertas</small>')
    
    html_alertas = []
    
    colores_nivel = {
        'leve': 'info',
        'moderado': 'warning',
        'severo': 'danger',
        'critico': 'danger'
    }
    
    for alerta in alertas:
        color = colores_nivel.get(alerta['nivel'], 'secondary')
        html_alertas.append(
            f'<li><small class="text-{color}"><i class="fas fa-exclamation-triangle me-1"></i>{alerta["mensaje"]}</small></li>'
        )
    
    return mark_safe(f'<ul class="list-unstyled mb-0">{"".join(html_alertas)}</ul>')


@register.simple_tag
def resumen_presupuesto_proyecto(proyecto):
    """Genera un resumen completo del estado presupuestario del proyecto"""
    if not proyecto:
        return ""
    
    context = {
        'presupuesto_total': proyecto.presupuesto,
        'gasto_real': proyecto.gasto_real,
        'presupuesto_disponible': proyecto.presupuesto_disponible,
        'porcentaje_ejecucion': proyecto.porcentaje_ejecucion_presupuesto,
        'estado_presupuesto': proyecto.estado_presupuesto,
        'riesgo_sobrecosto': proyecto.riesgo_sobrecosto,
        'proyeccion_final': proyecto.proyeccion_costo_final,
        'eficiencia': proyecto.eficiencia_presupuestaria,
        'alertas': proyecto.get_alertas_presupuesto()
    }
    
    return context


@register.filter
def proyeccion_costo_badge(proyecto):
    """Badge que muestra la proyección del costo final"""
    if not proyecto:
        return ""
    
    proyeccion = proyecto.proyeccion_costo_final
    sobrecosto_proyectado = ((proyeccion - float(proyecto.presupuesto)) / float(proyecto.presupuesto) * 100) if proyecto.presupuesto > 0 else 0
    
    if sobrecosto_proyectado > 20:
        color = 'danger'
        icono = 'arrow-up'
    elif sobrecosto_proyectado > 10:
        color = 'warning'
        icono = 'arrow-up'
    elif sobrecosto_proyectado > 0:
        color = 'info'
        icono = 'arrow-up'
    else:
        color = 'success'
        icono = 'check'
    
    return mark_safe(
        f'<span class="badge bg-{color}" title="Proyección costo final">'
        f'<i class="fas fa-{icono} me-1"></i>'
        f'${proyeccion:,.0f}'
        f'</span>'
    )