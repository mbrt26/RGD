from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def dias_retraso_badge(proyecto):
    """Genera un badge visual para mostrar el estado de retraso del proyecto"""
    if not proyecto:
        return ""
    
    dias_retraso = proyecto.dias_retraso
    nivel = proyecto.nivel_retraso
    
    if dias_retraso == 0:
        return mark_safe('<span class="badge bg-success">Al día</span>')
    
    # Configuración de colores por nivel
    colores = {
        'leve': 'warning',
        'moderado': 'warning',
        'severo': 'danger',
        'critico': 'danger'
    }
    
    iconos = {
        'leve': 'clock',
        'moderado': 'exclamation-triangle',
        'severo': 'exclamation-triangle',
        'critico': 'ban'
    }
    
    color = colores.get(nivel, 'secondary')
    icono = iconos.get(nivel, 'clock')
    
    return mark_safe(
        f'<span class="badge bg-{color}">'
        f'<i class="fas fa-{icono} me-1"></i>'
        f'{dias_retraso} días de retraso'
        f'</span>'
    )


@register.filter
def estado_cronograma_badge(proyecto):
    """Genera un badge para mostrar el estado del cronograma"""
    if not proyecto:
        return ""
    
    estado = proyecto.estado_cronograma
    desviacion = proyecto.desviacion_cronograma
    
    configuracion = {
        'adelantado': {
            'color': 'success',
            'icono': 'check-circle',
            'texto': f'Adelantado ({desviacion:+.1f}%)'
        },
        'en_tiempo': {
            'color': 'primary',
            'icono': 'clock',
            'texto': 'En tiempo'
        },
        'ligeramente_atrasado': {
            'color': 'warning',
            'icono': 'exclamation-triangle',
            'texto': f'Ligeramente atrasado ({desviacion:+.1f}%)'
        },
        'muy_atrasado': {
            'color': 'danger',
            'icono': 'times-circle',
            'texto': f'Muy atrasado ({desviacion:+.1f}%)'
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
def fecha_con_retraso(fecha, proyecto):
    """Muestra una fecha con color rojo si el proyecto está atrasado"""
    if not fecha or not proyecto:
        return fecha
    
    fecha_formateada = fecha.strftime('%d/%m/%Y')
    
    if proyecto.esta_atrasado:
        return mark_safe(
            f'<span class="text-danger fw-bold" title="Proyecto atrasado {proyecto.dias_retraso} días">'
            f'<i class="fas fa-exclamation-triangle me-1"></i>'
            f'{fecha_formateada}'
            f'</span>'
        )
    else:
        return fecha_formateada


@register.filter
def progreso_tiempo_visual(proyecto):
    """Genera una barra de progreso visual del tiempo transcurrido"""
    if not proyecto:
        return ""
    
    porcentaje = proyecto.porcentaje_tiempo_transcurrido
    avance_real = float(proyecto.avance)
    
    # Determinar color basado en la comparación tiempo vs avance
    if avance_real >= porcentaje:
        color_tiempo = 'success'
        color_avance = 'success'
    elif avance_real >= porcentaje - 10:
        color_tiempo = 'warning'
        color_avance = 'warning'
    else:
        color_tiempo = 'danger'
        color_avance = 'danger'
    
    return mark_safe(f'''
        <div class="progress position-relative mb-1" style="height: 20px;">
            <div class="progress-bar bg-{color_tiempo}" role="progressbar" 
                 style="width: {min(porcentaje, 100)}%"
                 title="Tiempo transcurrido: {porcentaje:.1f}%">
            </div>
            <div class="progress-bar bg-{color_avance}" role="progressbar" 
                 style="width: {min(avance_real, 100)}%; margin-left: -{min(porcentaje, 100)}%; opacity: 0.7"
                 title="Avance real: {avance_real}%">
            </div>
            <small class="position-absolute w-100 text-center text-dark fw-bold" 
                   style="top: 2px;">
                {avance_real:.1f}% / {porcentaje:.1f}%
            </small>
        </div>
        <small class="text-muted">Avance / Tiempo</small>
    ''')


@register.filter
def alertas_retraso_list(proyecto):
    """Genera una lista HTML con las alertas de retraso del proyecto"""
    if not proyecto:
        return ""
    
    alertas = proyecto.get_alertas_retraso()
    
    if not alertas:
        return mark_safe('<small class="text-success"><i class="fas fa-check-circle me-1"></i>Sin alertas</small>')
    
    html_alertas = []
    
    colores_nivel = {
        'leve': 'warning',
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


@register.filter
def dias_restantes_badge(proyecto):
    """Genera un badge con los días restantes del proyecto"""
    if not proyecto:
        return ""
    
    dias = proyecto.dias_restantes
    
    if proyecto.estado == 'finalizado':
        return mark_safe('<span class="badge bg-secondary">Finalizado</span>')
    
    if dias <= 0:
        return mark_safe('<span class="badge bg-danger">Fecha límite excedida</span>')
    elif dias <= 3:
        color = 'danger'
        icono = 'exclamation-triangle'
    elif dias <= 7:
        color = 'warning'
        icono = 'clock'
    else:
        color = 'primary'
        icono = 'calendar'
    
    return mark_safe(
        f'<span class="badge bg-{color}">'
        f'<i class="fas fa-{icono} me-1"></i>'
        f'{dias} días restantes'
        f'</span>'
    )


@register.simple_tag
def resumen_tiempo_proyecto(proyecto):
    """Genera un resumen completo del estado temporal del proyecto"""
    if not proyecto:
        return ""
    
    context = {
        'dias_retraso': proyecto.dias_retraso,
        'nivel_retraso': proyecto.nivel_retraso,
        'dias_restantes': proyecto.dias_restantes,
        'porcentaje_tiempo': proyecto.porcentaje_tiempo_transcurrido,
        'avance_real': float(proyecto.avance),
        'desviacion': proyecto.desviacion_cronograma,
        'estado_cronograma': proyecto.estado_cronograma,
        'alertas': proyecto.get_alertas_retraso()
    }
    
    return context


@register.filter
def semaforo_proyecto(proyecto):
    """Genera un indicador visual tipo semáforo del estado del proyecto"""
    if not proyecto:
        return ""
    
    # Determinar color principal basado en múltiples factores
    alertas = proyecto.get_alertas_retraso()
    tiene_alertas_severas = any(a['nivel'] in ['severo', 'critico'] for a in alertas)
    tiene_alertas_moderadas = any(a['nivel'] == 'moderado' for a in alertas)
    
    if tiene_alertas_severas or proyecto.dias_retraso > 15:
        color = 'danger'
        estado = 'Crítico'
        icono = 'times-circle'
    elif tiene_alertas_moderadas or proyecto.dias_retraso > 0 or proyecto.desviacion_cronograma < -10:
        color = 'warning'
        estado = 'Atención'
        icono = 'exclamation-triangle'
    else:
        color = 'success'
        estado = 'Normal'
        icono = 'check-circle'
    
    return mark_safe(
        f'<span class="badge bg-{color} fs-6" title="{estado}">'
        f'<i class="fas fa-{icono}"></i>'
        f'</span>'
    )