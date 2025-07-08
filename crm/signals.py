"""
Signals para el módulo CRM
Automatización de procesos cuando cambian los estados de los tratos
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib import messages
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Trato
from proyectos.models import Proyecto, EntregableProyecto
from servicios.models import SolicitudServicio

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Trato)
def trato_pre_save_handler(sender, instance, **kwargs):
    """
    Signal que se ejecuta antes de guardar un Trato.
    Guarda el estado anterior para comparar en post_save y valida campos obligatorios.
    """
    logger.info(f"[SIGNAL-PRE] pre_save - Trato ID: {instance.id if instance.id else 'NEW'}, estado: {instance.estado}, centro_costos: {instance.centro_costos}")
    
    # Validar centro de costos si se está marcando como ganado
    if instance.estado == 'ganado' and not instance.centro_costos:
        raise ValidationError(
            "Para marcar el trato como 'Ganado' y convertirlo a proyecto, "
            "debe ingresar obligatoriamente el Centro de Costos."
        )
    
    if instance.pk:
        try:
            instance._estado_anterior = Trato.objects.get(pk=instance.pk).estado
        except Trato.DoesNotExist:
            instance._estado_anterior = None
    else:
        instance._estado_anterior = None

@receiver(post_save, sender=Trato)
def trato_post_save_handler(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de guardar un Trato.
    Crea automáticamente un proyecto cuando un trato cambia a estado 'ganado'.
    """
    logger.info(f"[SIGNAL] post_save - Trato ID: {instance.id}, created: {created}, estado: {instance.estado}, tipo_negociacion: {instance.tipo_negociacion}")
    
    # Solo procesar si el trato cambió a 'ganado' y no es una creación nueva
    if not created and instance.estado == 'ganado':
        estado_anterior = getattr(instance, '_estado_anterior', None)
        logger.info(f"[SIGNAL] Trato {instance.id} - Estado anterior: {estado_anterior}, Estado actual: {instance.estado}")
        
        # Solo procesar si cambió de otro estado a 'ganado'
        if estado_anterior and estado_anterior != 'ganado':
            logger.info(f"[SIGNAL] Procesando cambio a 'ganado' para Trato {instance.id} con tipo_negociacion: {instance.tipo_negociacion}")
            
            try:
                # Crear proyecto si el tipo de negociación es 'contrato' o 'diseno'
                if instance.tipo_negociacion in ['contrato', 'diseno']:
                    logger.info(f"[SIGNAL] Creando proyecto para Trato {instance.id}")
                    success, message, proyecto = crear_proyecto_desde_trato(instance)
                    logger.info(f"[SIGNAL] Resultado proyecto - Success: {success}, Message: {message}")
                
                # Crear solicitud de servicio si el tipo de negociación es 'control' o 'servicios'
                elif instance.tipo_negociacion in ['control', 'servicios']:
                    logger.info(f"[SIGNAL] Creando solicitud de servicio para Trato {instance.id}")
                    resultado = crear_solicitud_servicio_desde_trato(instance)
                    if resultado:
                        success, message, solicitud = resultado
                        logger.info(f"[SIGNAL] Resultado servicio - Success: {success}, Message: {message}")
                    else:
                        logger.error(f"[SIGNAL] crear_solicitud_servicio_desde_trato retornó None para Trato {instance.id}")
                else:
                    logger.warning(f"[SIGNAL] Tipo de negociación '{instance.tipo_negociacion}' no reconocido para Trato {instance.id}")
                    
            except Exception as e:
                logger.error(f"[SIGNAL] Error al crear proyecto/solicitud desde trato {instance.id}: {str(e)}", exc_info=True)

def crear_proyecto_desde_trato(trato):
    """
    Crea un proyecto automáticamente desde un trato ganado.
    
    Args:
        trato: Instancia del modelo Trato
    
    Returns:
        tuple: (success: bool, message: str, proyecto: Proyecto|None)
    """
    # 1. Verificar si ya existe un proyecto para este trato
    if Proyecto.objects.filter(trato=trato).exists():
        mensaje = f"⚠️ Ya existe un proyecto asociado al trato #{trato.numero_oferta}. No se creará un nuevo proyecto."
        logger.warning(mensaje)
        return False, mensaje, None
    
    # 2. Verificar datos obligatorios y generar avisos
    campos_faltantes = []
    datos_proyecto = {}
    
    # Cliente (obligatorio)
    if trato.cliente and trato.cliente.nombre:
        datos_proyecto['cliente'] = trato.cliente.nombre
    else:
        campos_faltantes.append('Cliente')
    
    # Centro de costos (obligatorio - ya validado en pre_save)
    if trato.centro_costos:
        datos_proyecto['centro_costos'] = trato.centro_costos
    else:
        # Esto no debería suceder debido a la validación en pre_save
        raise ValidationError("Centro de Costos es obligatorio para crear un proyecto.")
    
    # Nombre del proyecto
    if trato.nombre_proyecto:
        datos_proyecto['nombre_proyecto'] = trato.nombre_proyecto
    elif trato.descripcion:
        datos_proyecto['nombre_proyecto'] = trato.descripcion[:200]  # Truncar si es muy largo
    else:
        campos_faltantes.append('Nombre del Proyecto')
        datos_proyecto['nombre_proyecto'] = f"Proyecto Trato #{trato.numero_oferta}"
    
    # Orden o contrato (debe ser único)
    if trato.orden_contrato:
        datos_proyecto['orden_contrato'] = trato.orden_contrato
    else:
        campos_faltantes.append('Orden o Contrato')
        datos_proyecto['orden_contrato'] = f"ORD-{trato.numero_oferta}-{timezone.now().strftime('%Y%m%d')}"
    
    # Verificar unicidad de orden_contrato
    if Proyecto.objects.filter(orden_contrato=datos_proyecto['orden_contrato']).exists():
        datos_proyecto['orden_contrato'] = f"{datos_proyecto['orden_contrato']}-{timezone.now().strftime('%H%M%S')}"
    
    # Días prometidos
    if trato.dias_prometidos and trato.dias_prometidos > 0:
        datos_proyecto['dias_prometidos'] = trato.dias_prometidos
    else:
        campos_faltantes.append('Días Prometidos')
        datos_proyecto['dias_prometidos'] = 30  # Valor por defecto
    
    # 3. Calcular fechas
    fecha_inicio = timezone.now().date()
    fecha_fin = fecha_inicio + timezone.timedelta(days=datos_proyecto['dias_prometidos'])
    
    datos_proyecto.update({
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'presupuesto': trato.valor if trato.valor else 0,
        'estado': 'pendiente',
        'avance': 0,
        'gasto_real': 0,
        'creado_por': trato.responsable,
    })
    
    # 4. Generar mensaje sobre campos faltantes
    mensaje_campos = ""
    if campos_faltantes:
        mensaje_campos = f"\n⚠️ Algunos campos se completaron con valores por defecto: {', '.join(campos_faltantes)}"
    
    try:
        # 5. Crear el proyecto con la relación al trato
        datos_proyecto['trato'] = trato
        proyecto = Proyecto.objects.create(**datos_proyecto)
        
        # 6. Cargar entregables automáticamente
        try:
            EntregableProyecto.cargar_entregables_desde_json(proyecto)
            mensaje_entregables = "\n📋 Entregables cargados automáticamente desde plantilla."
        except Exception as e:
            logger.warning(f"No se pudieron cargar entregables para proyecto {proyecto.id}: {str(e)}")
            mensaje_entregables = "\n⚠️ No se pudieron cargar los entregables automáticamente."
        
        # 7. Mensaje de éxito
        mensaje_exito = (
            f"✅ Proyecto creado automáticamente: '{proyecto.nombre_proyecto}'\n"
            f"🆔 Orden/Contrato: {proyecto.orden_contrato}\n" 
            f"📅 Fecha inicio: {proyecto.fecha_inicio}\n"
            f"📅 Fecha fin: {proyecto.fecha_fin}\n"
            f"💰 Presupuesto: ${proyecto.presupuesto:,.2f}"
            f"{mensaje_campos}"
            f"{mensaje_entregables}"
        )
        
        logger.info(f"Proyecto {proyecto.id} creado automáticamente desde trato {trato.id}")
        return True, mensaje_exito, proyecto
        
    except ValidationError as e:
        mensaje_error = f"❌ Error de validación al crear proyecto: {str(e)}"
        logger.error(mensaje_error)
        return False, mensaje_error, None
    
    except Exception as e:
        mensaje_error = f"❌ Error inesperado al crear proyecto: {str(e)}"
        logger.error(mensaje_error)
        return False, mensaje_error, None

def obtener_resumen_proyecto_creado(proyecto):
    """
    Genera un resumen del proyecto creado para mostrar al usuario.
    
    Args:
        proyecto: Instancia del modelo Proyecto
    
    Returns:
        dict: Resumen del proyecto
    """
    return {
        'id': proyecto.id,
        'nombre': proyecto.nombre_proyecto,
        'cliente': proyecto.cliente,
        'centro_costos': proyecto.centro_costos,
        'orden_contrato': proyecto.orden_contrato,
        'fecha_inicio': proyecto.fecha_inicio,
        'fecha_fin': proyecto.fecha_fin,
        'dias_prometidos': proyecto.dias_prometidos,
        'presupuesto': proyecto.presupuesto,
        'estado': proyecto.get_estado_display(),
        'url_proyecto': f'/proyectos/proyectos/{proyecto.id}/',
    }


def crear_solicitud_servicio_desde_trato(trato):
    """
    Crea una solicitud de servicio automáticamente desde un trato ganado
    con tipo de negociación 'control' o 'servicios'.
    
    Args:
        trato: Instancia del modelo Trato
    
    Returns:
        tuple: (success: bool, message: str, solicitud: SolicitudServicio|None)
    """
    logger.info(f"[SERVICIO] Iniciando creación de solicitud para Trato {trato.id} - tipo: {trato.tipo_negociacion}")
    
    # 1. Verificar si ya existe una solicitud de servicio para este trato
    if SolicitudServicio.objects.filter(trato_origen=trato).exists():
        mensaje = f"⚠️ Ya existe una solicitud de servicio asociada al trato #{trato.numero_oferta}. No se creará una nueva solicitud."
        logger.warning(mensaje)
        return False, mensaje, None
    
    # 2. Verificar datos obligatorios y generar avisos
    campos_faltantes = []
    datos_solicitud = {}
    
    # Cliente (obligatorio)
    if trato.cliente:
        datos_solicitud['cliente_crm'] = trato.cliente
    else:
        campos_faltantes.append('Cliente')
    
    # Trato de origen (para anclaje correcto de contactos y cotizaciones)
    datos_solicitud['trato_origen'] = trato
    
    # Centro de costos (obligatorio - ya validado en pre_save)
    if trato.centro_costos:
        datos_solicitud['centro_costo'] = trato.centro_costos
    else:
        # Esto no debería suceder debido a la validación en pre_save
        raise ValidationError("Centro de Costos es obligatorio para crear una solicitud de servicio.")
    
    # Contacto (opcional)
    if trato.contacto:
        datos_solicitud['contacto_crm'] = trato.contacto
    
    # Cotización aprobada (si existe una versión de cotización activa/aprobada para este trato)
    try:
        # Buscar la cotización más reciente del trato
        cotizacion = trato.cotizaciones.order_by('-fecha_creacion').first()
        if cotizacion:
            # Obtener la versión más reciente de la cotización
            version_activa = cotizacion.versiones.order_by('-version').first()
            if version_activa:
                datos_solicitud['cotizacion_aprobada'] = version_activa
    except Exception as e:
        logger.warning(f"No se pudo asignar cotización al servicio para trato {trato.id}: {str(e)}")
    
    # Nombre del proyecto o descripción del servicio
    if trato.nombre_proyecto:
        datos_solicitud['nombre_proyecto'] = trato.nombre_proyecto
    elif trato.descripcion:
        datos_solicitud['nombre_proyecto'] = trato.descripcion[:200]  # Truncar si es muy largo
    else:
        datos_solicitud['nombre_proyecto'] = f"Servicio Trato #{trato.numero_oferta}"
    
    # Dirección del servicio (usar dirección del cliente si no hay específica)
    if trato.cliente and trato.cliente.direccion:
        datos_solicitud['direccion_servicio'] = trato.cliente.direccion
    else:
        datos_solicitud['direccion_servicio'] = "Por definir"
        campos_faltantes.append('Dirección del Servicio')
    
    # 3. Configurar datos específicos de la solicitud de servicio
    # Generar número de orden único (máximo 20 caracteres)
    # No asignar numero_orden para que se genere automáticamente en el modelo
    # datos_solicitud['numero_orden'] se generará automáticamente como FS{año}{numero}
    
    # Determinar tipo de servicio basado en el tipo de negociación
    if trato.tipo_negociacion == 'control':
        datos_solicitud['tipo_servicio'] = 'inspeccion'  # Control se mapea a Visita de Inspección
    elif trato.tipo_negociacion == 'servicios':
        datos_solicitud['tipo_servicio'] = 'correctivo'  # Servicios se mapea a Mantenimiento Correctivo
    else:
        datos_solicitud['tipo_servicio'] = 'correctivo'  # Por defecto
    
    # 4. Configurar fechas
    fecha_programada = timezone.now() + timezone.timedelta(days=7)  # Una semana adelante por defecto
    if trato.dias_prometidos and trato.dias_prometidos > 0:
        fecha_programada = timezone.now() + timezone.timedelta(days=min(trato.dias_prometidos, 30))
    
    datos_solicitud.update({
        'fecha_programada': fecha_programada,
        'duracion_estimada': 240,  # 4 horas por defecto
        'estado': 'pendiente',
        'creado_por': trato.responsable,
        'observaciones_internas': f"Solicitud creada automáticamente desde trato CRM #{trato.numero_oferta}"
    })
    
    # 5. Generar mensaje sobre campos faltantes
    mensaje_campos = ""
    if campos_faltantes:
        mensaje_campos = f"\n⚠️ Algunos campos se completaron con valores por defecto: {', '.join(campos_faltantes)}"
    
    try:
        # 6. Crear la solicitud de servicio
        solicitud = SolicitudServicio.objects.create(**datos_solicitud)
        
        # 7. Mensaje de éxito
        mensaje_exito = (
            f"✅ Solicitud de servicio creada automáticamente: '{solicitud.numero_orden}'\n"
            f"🏢 Cliente: {solicitud.cliente_crm.nombre}\n"
            f"📅 Fecha programada: {solicitud.fecha_programada.strftime('%d/%m/%Y %H:%M')}\n"
            f"🔧 Tipo de servicio: {solicitud.get_tipo_servicio_display()}\n"
            f"📍 Centro de costos: {solicitud.centro_costo}"
            f"{mensaje_campos}"
        )
        
        logger.info(f"Solicitud de servicio {solicitud.id} creada automáticamente desde trato {trato.id}")
        return True, mensaje_exito, solicitud
        
    except ValidationError as e:
        mensaje_error = f"❌ Error de validación al crear solicitud de servicio: {str(e)}"
        logger.error(mensaje_error)
        return False, mensaje_error, None
    
    except Exception as e:
        mensaje_error = f"❌ Error inesperado al crear solicitud de servicio: {str(e)}"
        logger.error(mensaje_error)
        return False, mensaje_error, None