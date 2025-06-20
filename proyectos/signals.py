from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Actividad, Proyecto


@receiver(post_save, sender=Actividad)
def actualizar_avance_proyecto_actividad_guardada(sender, instance, **kwargs):
    """
    Signal que actualiza el avance del proyecto cuando se guarda una actividad.
    Se dispara después de guardar una actividad para recalcular el avance del proyecto.
    """
    if instance.proyecto:
        instance.proyecto.actualizar_avance_real()


@receiver(post_delete, sender=Actividad)
def actualizar_avance_proyecto_actividad_eliminada(sender, instance, **kwargs):
    """
    Signal que actualiza el avance del proyecto cuando se elimina una actividad.
    Se dispara después de eliminar una actividad para recalcular el avance del proyecto.
    """
    if instance.proyecto:
        instance.proyecto.actualizar_avance_real()