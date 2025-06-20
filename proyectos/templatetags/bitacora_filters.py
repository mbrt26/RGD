from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone

register = template.Library()


@register.filter
def estado_bitacora_badge(bitacora):
    """Genera un badge visual para mostrar el estado de la bitácora"""
    if not bitacora:
        return ""
    
    estado = bitacora.estado
    
    configuracion = {
        'planeada': {
            'color': 'secondary',
            'icono': 'calendar',
            'texto': 'Planeada'
        },
        'en_proceso': {
            'color': 'warning',
            'icono': 'clock',
            'texto': 'En Proceso'
        },
        'completada': {
            'color': 'success',
            'icono': 'check-circle',
            'texto': 'Completada'
        },
        'cancelada': {
            'color': 'danger',
            'icono': 'times-circle',
            'texto': 'Cancelada'
        }
    }
    
    config = configuracion.get(estado, {
        'color': 'secondary',
        'icono': 'question',
        'texto': estado.title()
    })
    
    return mark_safe(
        f'<span class="badge bg-{config["color"]}">'
        f'<i class="fas fa-{config["icono"]} me-1"></i>'
        f'{config["texto"]}'
        f'</span>'
    )


@register.filter
def retraso_bitacora_badge(bitacora):
    """Genera un badge para mostrar el retraso de la bitácora"""
    if not bitacora:
        return ""
    
    dias_retraso = bitacora.dias_retraso_ejecucion
    nivel = bitacora.nivel_urgencia
    
    if dias_retraso == 0:
        return mark_safe('<span class="badge bg-success">A tiempo</span>')
    
    colores = {
        'leve': 'warning',
        'moderado': 'warning', 
        'critico': 'danger'
    }
    
    iconos = {
        'leve': 'clock',
        'moderado': 'exclamation-triangle',
        'critico': 'exclamation-triangle'
    }
    
    color = colores.get(nivel, 'secondary')
    icono = iconos.get(nivel, 'clock')
    
    return mark_safe(
        f'<span class="badge bg-{color}">'
        f'<i class="fas fa-{icono} me-1"></i>'
        f'{dias_retraso} días retraso'
        f'</span>'
    )


@register.filter
def urgencia_registro_badge(bitacora):
    """Badge para mostrar la urgencia de registro de bitácoras planeadas"""
    if not bitacora or bitacora.estado != 'planeada':
        return ""
    
    if not bitacora.requiere_registro_urgente:
        return mark_safe('<span class="badge bg-primary">Programada</span>')
    
    nivel = bitacora.nivel_urgencia
    dias = bitacora.dias_retraso_ejecucion
    
    colores = {
        'leve': 'warning',
        'moderado': 'warning',
        'critico': 'danger'
    }
    
    color = colores.get(nivel, 'danger')
    
    return mark_safe(
        f'<span class="badge bg-{color} text-white">'
        f'<i class="fas fa-exclamation-triangle me-1"></i>'
        f'Registrar urgente ({dias} días)'
        f'</span>'
    )


@register.filter
def validacion_bitacora_badge(bitacora):
    """Badge para mostrar el estado de validación de la bitácora"""
    if not bitacora:
        return ""
    
    estado = bitacora.estado_validacion
    
    configuracion = {
        'pendiente': {
            'color': 'secondary',
            'icono': 'hourglass-half',
            'texto': 'Pendiente Validación'
        },
        'validada_director': {
            'color': 'info',
            'icono': 'user-check',
            'texto': 'Validada Director'
        },
        'validada_ingeniero': {
            'color': 'info',
            'icono': 'user-check', 
            'texto': 'Validada Ingeniero'
        },
        'validada_completa': {
            'color': 'success',
            'icono': 'check-double',
            'texto': 'Validación Completa'
        },
        'rechazada': {
            'color': 'danger',
            'icono': 'times-circle',
            'texto': 'Rechazada'
        }
    }
    
    config = configuracion.get(estado, configuracion['pendiente'])
    
    return mark_safe(
        f'<span class="badge bg-{config["color"]}">'
        f'<i class="fas fa-{config["icono"]} me-1"></i>'
        f'{config["texto"]}'
        f'</span>'
    )


@register.filter
def firmas_digitales_status(bitacora):
    """Muestra el estado de las firmas digitales"""
    if not bitacora:
        return ""
    
    html_parts = []
    
    # Estado firma director
    if bitacora.firma_director:
        html_parts.append(
            '<span class="badge bg-success me-1">'
            f'<i class="fas fa-signature me-1"></i>Director: '
            f'{bitacora.fecha_firma_director.strftime("%d/%m/%Y %H:%M") if bitacora.fecha_firma_director else "Firmado"}'
            '</span>'
        )
    else:
        html_parts.append(
            '<span class="badge bg-warning me-1">'
            '<i class="fas fa-pen me-1"></i>Director: Pendiente'
            '</span>'
        )
    
    # Estado firma ingeniero
    if bitacora.firma_ingeniero:
        html_parts.append(
            '<span class="badge bg-success me-1">'
            f'<i class="fas fa-signature me-1"></i>Ingeniero: '
            f'{bitacora.fecha_firma_ingeniero.strftime("%d/%m/%Y %H:%M") if bitacora.fecha_firma_ingeniero else "Firmado"}'
            '</span>'
        )
    else:
        html_parts.append(
            '<span class="badge bg-warning me-1">'
            '<i class="fas fa-pen me-1"></i>Ingeniero: Pendiente'
            '</span>'
        )
    
    return mark_safe('<div>' + ''.join(html_parts) + '</div>')


@register.filter
def fecha_planificada_vs_real(bitacora):
    """Compara fecha planificada vs real con colores"""
    if not bitacora:
        return ""
    
    fecha_planificada = bitacora.fecha_planificada.strftime('%d/%m/%Y')
    
    if bitacora.fecha_ejecucion_real:
        fecha_real = bitacora.fecha_ejecucion_real.strftime('%d/%m/%Y')
        
        if bitacora.dias_retraso_ejecucion > 0:
            return mark_safe(
                f'<div>'
                f'<small class="text-muted">Planificada: {fecha_planificada}</small><br>'
                f'<small class="text-danger fw-bold">Real: {fecha_real} ({bitacora.dias_retraso_ejecucion} días retraso)</small>'
                f'</div>'
            )
        else:
            return mark_safe(
                f'<div>'
                f'<small class="text-muted">Planificada: {fecha_planificada}</small><br>'
                f'<small class="text-success">Real: {fecha_real} (A tiempo)</small>'
                f'</div>'
            )
    else:
        # No se ha ejecutado aún
        hoy = timezone.now().date()
        if hoy > bitacora.fecha_planificada:
            dias_retraso = (hoy - bitacora.fecha_planificada).days
            return mark_safe(
                f'<div>'
                f'<small class="text-danger fw-bold">Planificada: {fecha_planificada}</small><br>'
                f'<small class="text-danger">⚠️ {dias_retraso} días de retraso</small>'
                f'</div>'
            )
        else:
            return mark_safe(
                f'<div>'
                f'<small class="text-primary">Planificada: {fecha_planificada}</small><br>'
                f'<small class="text-muted">Pendiente ejecución</small>'
                f'</div>'
            )


@register.filter
def equipo_trabajo_display(bitacora):
    """Muestra el equipo de trabajo de manera organizada"""
    if not bitacora:
        return ""
    
    html_parts = []
    
    # Líder de trabajo
    if bitacora.lider_trabajo:
        html_parts.append(
            f'<div><strong>Líder:</strong> '
            f'<span class="badge bg-primary">{bitacora.lider_trabajo.nombre}</span></div>'
        )
    
    # Responsable
    html_parts.append(
        f'<div><strong>Responsable:</strong> '
        f'<span class="badge bg-info">{bitacora.responsable.nombre}</span></div>'
    )
    
    # Equipo
    if bitacora.equipo.exists():
        equipo_nombres = [f'<span class="badge bg-secondary me-1">{colaborador.nombre}</span>' 
                         for colaborador in bitacora.equipo.all()]
        html_parts.append(
            f'<div><strong>Equipo:</strong><br>{"".join(equipo_nombres)}</div>'
        )
    
    return mark_safe('<div class="equipo-trabajo">' + '<br>'.join(html_parts) + '</div>')


@register.filter
def alertas_bitacora_list(bitacora):
    """Genera una lista HTML con las alertas de la bitácora"""
    if not bitacora:
        return ""
    
    alertas = bitacora.get_alertas_bitacora()
    
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


@register.filter
def semaforo_bitacora(bitacora):
    """Genera un indicador visual tipo semáforo del estado de la bitácora"""
    if not bitacora:
        return ""
    
    alertas = bitacora.get_alertas_bitacora()
    tiene_alertas_criticas = any(a['nivel'] == 'critico' for a in alertas)
    tiene_alertas_moderadas = any(a['nivel'] == 'moderado' for a in alertas)
    
    if bitacora.estado == 'cancelada':
        color = 'secondary'
        estado = 'Cancelada'
        icono = 'ban'
    elif tiene_alertas_criticas or (bitacora.requiere_registro_urgente and bitacora.nivel_urgencia == 'critico'):
        color = 'danger'
        estado = 'Crítico'
        icono = 'exclamation-triangle'
    elif tiene_alertas_moderadas or bitacora.requiere_registro_urgente:
        color = 'warning'
        estado = 'Atención'
        icono = 'exclamation-triangle'
    elif bitacora.estado == 'completada' and bitacora.estado_validacion_completo:
        color = 'success'
        estado = 'Completo'
        icono = 'check-circle'
    else:
        color = 'primary'
        estado = 'Normal'
        icono = 'info-circle'
    
    return mark_safe(
        f'<span class="badge bg-{color} fs-6" title="{estado}">'
        f'<i class="fas fa-{icono}"></i>'
        f'</span>'
    )