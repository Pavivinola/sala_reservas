from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_reservation_confirmation(reservation):
    """Envía email de confirmación cuando se crea una reserva"""
    user = reservation.user
    
    subject = f'Confirmación de Reserva - {reservation.room.name}'
    
    message = f"""
Hola {user.first_name or user.username},

Tu reserva ha sido confirmada exitosamente:

📅 Fecha: {reservation.date.strftime('%d/%m/%Y')}
🏢 Sala: {reservation.room.name}
📍 Ubicación: {reservation.room.location}
⏰ Horario: {reservation.time_block.start_time.strftime('%H:%M')} - {reservation.time_block.end_time.strftime('%H:%M')}
👥 Capacidad: {reservation.room.capacity} personas

"""
    
    # Agregar materiales si los hay
    if reservation.requested_materials.exists():
        materials_list = ", ".join([m.name for m in reservation.requested_materials.all()])
        message += f"🛠️ Materiales solicitados: {materials_list}\n\n"
    
    if reservation.notes:
        message += f"📝 Notas: {reservation.notes}\n\n"
    
    message += """
¡Nos vemos pronto!

---
Sistema de Reservas de Salas
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False


def send_reservation_reminder(reservation):
    """Envía recordatorio antes de que comience la reserva"""
    user = reservation.user
    
    subject = f'Recordatorio: Tu reserva comienza pronto - {reservation.room.name}'
    
    message = f"""
Hola {user.first_name or user.username},

Te recordamos que tu reserva comenzará pronto:

📅 Fecha: HOY {reservation.date.strftime('%d/%m/%Y')}
🏢 Sala: {reservation.room.name}
📍 Ubicación: {reservation.room.location}
⏰ Horario: {reservation.time_block.start_time.strftime('%H:%M')} - {reservation.time_block.end_time.strftime('%H:%M')}

¡No olvides llegar a tiempo!

---
Sistema de Reservas de Salas
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar recordatorio: {e}")
        return False


def send_cancellation_notice(reservation):
    """Envía notificación cuando se cancela una reserva"""
    user = reservation.user
    
    subject = f'Reserva Cancelada - {reservation.room.name}'
    
    message = f"""
Hola {user.first_name or user.username},

Tu reserva ha sido cancelada:

📅 Fecha: {reservation.date.strftime('%d/%m/%Y')}
🏢 Sala: {reservation.room.name}
⏰ Horario: {reservation.time_block.start_time.strftime('%H:%M')} - {reservation.time_block.end_time.strftime('%H:%M')}

Si tienes alguna duda, contacta con el administrador.

---
Sistema de Reservas de Salas
"""
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar notificación de cancelación: {e}")
        return False