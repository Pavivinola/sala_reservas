from django.core.mail import send_mail
from django.conf import settings
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sala_reservas.settings')
django.setup()

# Enviar email de prueba
try:
    send_mail(
        subject='Prueba de Email - Sistema de Reservas',
        message='Este es un email de prueba desde Django. Si recibes esto, ¡la configuración funciona!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['jamq201027@gmail.com'],  # Pon tu email personal aquí
        fail_silently=False,
    )
    print("✅ Email enviado correctamente!")
except Exception as e:
    print(f"❌ Error al enviar email: {e}")