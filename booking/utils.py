# utils.py
import base64
import hmac
import hashlib
import qrcode
from django.conf import settings
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Sum
from .models import Booking


def generate_secure_qr_data(booking):
    """
    Generate secure QR code for the booking.
    The QR code data includes booking id, user id, bus trip id, and a secure signature.
    """
    qr_payload = f"{booking.id}|{booking.user.id}|{booking.bus_trip.id}"  # Booking ID | User ID | Trip ID
    signature = hmac.new(settings.SECRET_KEY.encode(),
                         qr_payload.encode(), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode()

    # Combine data and signature
    qr_code_data = f"{qr_payload}|{encoded_signature}"

    # Generate the QR code from the data
    qr = qrcode.make(qr_code_data)

    # Save the QR code image to the booking object
    qr_code_image = BytesIO()
    qr.save(qr_code_image, format='PNG')
    qr_code_image.seek(0)

    # Store the QR code in the booking object
    booking.qr_code = InMemoryUploadedFile(
        qr_code_image, None, f"booking_{booking.id}_qr.png", 'image/png', qr_code_image.tell(), None
    )
    booking.save()  # Save the booking with the generated QR code
