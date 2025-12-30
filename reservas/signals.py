from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Reservation
from .emails import send_reservation_confirmation, send_cancellation_notice


@receiver(post_save, sender=Reservation)
def handle_reservation_created(sender, instance, created, **kwargs):
    """Envía email de confirmación cuando se crea una nueva reserva"""
    if created and instance.status == 'confirmed':
        # Solo enviar si el usuario tiene email
        if instance.user.email:
            send_reservation_confirmation(instance)


@receiver(pre_save, sender=Reservation)
def handle_reservation_cancelled(sender, instance, **kwargs):
    """Envía email cuando se cancela una reserva"""
    if instance.pk:  # Si ya existe en la BD
        try:
            old_instance = Reservation.objects.get(pk=instance.pk)
            # Si cambió de otro estado a 'cancelled'
            if old_instance.status != 'cancelled' and instance.status == 'cancelled':
                if instance.user.email:
                    send_cancellation_notice(instance)
        except Reservation.DoesNotExist:
            pass