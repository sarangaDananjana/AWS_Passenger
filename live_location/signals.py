from django.db.models.signals import post_save
from django.dispatch import receiver
from busstops.models import Buses
from .models import LiveLocation


@receiver(post_save, sender=Buses)
def create_live_location(sender, instance, created, **kwargs):
    """
    Automatically create a LiveLocation entry when a new bus is added.
    """
    if created:
        LiveLocation.objects.create(
            bus=instance, latitude=0.0, longitude=0.0)  # Default values
