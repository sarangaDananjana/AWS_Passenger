from django.conf import settings
from django.db import models
from busstops.models import Seat, BoardingPoint, BusRoute, Buses
from members.models import User


SECRET_QR_KEY = settings.SECRET_KEY  # Use a secret key to sign QR codes

BOOOKING_STATUS = [
    ('PENDING', 'Pending'),
    ('BOOKED', 'Booked'),
    ('VERIFIED', 'Verified'),
    ('BOOKING_CANCELED', 'Booking_canceled'),
    ('BUS_TRIP_CANCELED', 'Bus_trip_canceled'),
    ('RESCHEDULED_1', 'Rescheduled_1'),
    ('RESCHEDULED_2', 'Rescheduled_2'),
    ('RESCHEDULED_3', 'Rescheduled_3'),
]


class BusTrip(models.Model):
    name = models.CharField(max_length=255, blank=True, editable=False)
    bus = models.ForeignKey(
        Buses, on_delete=models.CASCADE, related_name="trips")
    route = models.ForeignKey(
        BusRoute, on_delete=models.CASCADE, related_name="trips")
    start_time = models.DateTimeField()
    revenue = models.DecimalField(default=0.0, max_digits=10, decimal_places=2)
    company_3_percent_cut = models.DecimalField(
        default=0.0, max_digits=10, decimal_places=2)
    is_revenue_released = models.BooleanField(default=False)
    is_bustrip_canceled = models.BooleanField(default=False)
    cancellation_fee_resolved = models.BooleanField(default=False)
    # seat = ForeignKey on Booking Model

    def save(self, *args, **kwargs):

        self.name = f"{self.bus.bus_name} | on | {self.route.name}"

    # If the trip is canceled, update all related bookings
        if self.is_bustrip_canceled:
            self.revenue = 0.0
            Booking.objects.filter(bus_trip=self).update(
                booking_status='BUS_TRIP_CANCELED')

        super().save(*args, **kwargs)  # Call the parent save method

    def __str__(self):
        return f"Bus {self.bus.bus_name} on {self.route.name} at {self.start_time}"


class Booking(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='booking')
    bus_trip = models.ForeignKey(
        BusTrip, on_delete=models.CASCADE, null=True, blank=True, related_name='seat')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    start_point = models.ForeignKey(
        BoardingPoint, on_delete=models.CASCADE, related_name='start_bookings')
    end_point = models.ForeignKey(
        BoardingPoint, on_delete=models.CASCADE, related_name='end_bookings')
    booked_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    fare_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0)
    company_4_precent_cut = models.DecimalField(
        default=0.0, max_digits=10, decimal_places=2)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    booking_status = models.CharField(max_length=55,
                                      choices=BOOOKING_STATUS, default='BOOKED')

    class Meta:
        unique_together = ('bus_trip', 'seat')

    def __str__(self):
        return f"Booking {self.id} - {self.user} - {self.fare_price}"
