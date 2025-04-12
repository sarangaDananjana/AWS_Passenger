from django.db import models
from busstops.models import Buses
from django.utils.timezone import now


class LiveLocation(models.Model):
    bus = models.OneToOneField(
        Buses, on_delete=models.CASCADE, related_name='live_location'
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Live Location of {self.bus.bus_name} - ({self.latitude}, {self.longitude})"
