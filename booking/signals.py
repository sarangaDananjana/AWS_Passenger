# booking/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking
# Import your QR code generation function
from .utils import generate_secure_qr_data


@receiver(post_save, sender=Booking)
def generate_qr_code_for_booking(sender, instance, created, **kwargs):
    """
    Signal to generate the QR code for the newly created Booking instance.
    """
    if created:  # Only run for newly created bookings
        # Generate the QR code for the booking
        # This can be your function to generate the QR code
        generate_secure_qr_data(instance)
