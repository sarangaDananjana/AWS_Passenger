from django.db import models
from members.models import User, BusConductorProfile


CITY_TO_PROVINCE_MAP = {
    "Ampara District": "Eastern Province",
    "Anuradhapura District": "North Central Province",
    "Badulla District": "Uva Province",
    "Batticaloa District": "Eastern Province",
    "Colombo District": "Western Province",
    "Galle District": "Southern Province",
    "Gampaha District": "Western Province",
    "Hambantota District": "Southern Province",
    "Jaffna District": "Northern Province",
    "Kalutara District": "Western Province",
    "Kandy District": "Central Province",
    "Kegalle District": "Sabaragamuwa Province",
    "Kilinochchi District": "Northern Province",
    "Kurunegala District": "North Western Province",
    "Mannar District": "Northern Province",
    "Matale District": "Central Province",
    "Matara District": "Southern Province",
    "Monaragala District": "Uva Province",
    "Mullaitivu District": "Northern Province",
    "Nuwara Eliya District": "Central Province",
    "Polonnaruwa District": "North Central Province",
    "Puttalam District": "North Western Province",
    "Ratnapura District": "Sabaragamuwa Province",
    "Trincomalee District": "Eastern Province",
    "Vavuniya District": "Northern Province"
}


CENTRAL_PROVINCE = "Central Province"
EASTERN_PROVINCE = "Eastern Province"
NORTH_CENTRAL_PROVINCE = "North Central Province"
NORTHERN_PROVINCE = "Northern Province"
NORTH_WESTERN_PROVINCE = "North Western Province"
SABARAGAMUWA_PROVINCE = "Sabaragamuwa Province"
SOUTHERN_PROVINCE = "Southern Province"
UVA_PROVINCE = "Uva Province"
WESTERN_PROVINCE = "Western Province"

PROVINCES_IN_SRI_LANKA = [
    (CENTRAL_PROVINCE, "Central Province"),
    (EASTERN_PROVINCE, "Eastern Province"),
    (NORTH_CENTRAL_PROVINCE, "North Central Province"),
    (NORTHERN_PROVINCE, "Northern Province"),
    (NORTH_WESTERN_PROVINCE, "North Western Province"),
    (SABARAGAMUWA_PROVINCE, "Sabaragamuwa Province"),
    (SOUTHERN_PROVINCE, "Southern Province"),
    (UVA_PROVINCE, "Uva Province"),
    (WESTERN_PROVINCE, "Western Province")
]


AMPARA_DISTRICT = "Ampara District"
ANURADHAPURA_DISTRICT = "Anuradhapura District"
BADULLA_DISTRICT = "Badulla District"
BATTICALOA_DISTRICT = "Batticaloa District"
COLOMBO_DISTRICT = "Colombo District"
GALLE_DISTRICT = "Galle District"
GAMPAHA_DISTRICT = "Gampaha District"
HAMBANTOTA_DISTRICT = "Hambantota District"
JAFFNA_DISTRICT = "Jaffna District"
KALUTARA_DISTRICT = "Kalutara District"
KANDY_DISTRICT = "Kandy District"
KEGALLE_DISTRICT = "Kegalle District"
KILINOCHCHI_DISTRICT = "Kilinochchi District"
KURUNEGALA_DISTRICT = "Kurunegala District"
MANNAR_DISTRICT = "Mannar District"
MATALE_DISTRICT = "Matale District"
MATARA_DISTRICT = "Matara District"
MONARAGALA_DISTRICT = "Monaragala District"
MULLAITIVU_DISTRICT = "Mullaitivu District"
NUWARA_ELIYA_DISTRICT = "Nuwara Eliya District"
POLONNARUWA_DISTRICT = "Polonnaruwa District"
PUTTALAM_DISTRICT = "Puttalam District"
RATNAPURA_DISTRICT = "Ratnapura District"
TRINCOMALEE_DISTRICT = "Trincomalee District"
VAVUNIYA_DISTRICT = "Vavuniya District"


DISTRICTS_IN_SRI_LANKA = [
    (AMPARA_DISTRICT, "Ampara District"),
    (ANURADHAPURA_DISTRICT, "Anuradhapura District"),
    (BADULLA_DISTRICT, "Badulla District"),
    (BATTICALOA_DISTRICT, "Batticaloa District"),
    (COLOMBO_DISTRICT, "Colombo District"),
    (GALLE_DISTRICT, "Galle District"),
    (GAMPAHA_DISTRICT, "Gampaha District"),
    (HAMBANTOTA_DISTRICT, "Hambantota District"),
    (JAFFNA_DISTRICT, "Jaffna District"),
    (KALUTARA_DISTRICT, "Kalutara District"),
    (KANDY_DISTRICT, "Kandy District"),
    (KEGALLE_DISTRICT, "Kegalle District"),
    (KILINOCHCHI_DISTRICT, "Kilinochchi District"),
    (KURUNEGALA_DISTRICT, "Kurunegala District"),
    (MANNAR_DISTRICT, "Mannar District"),
    (MATALE_DISTRICT, "Matale District"),
    (MATARA_DISTRICT, "Matara District"),
    (MONARAGALA_DISTRICT, "Monaragala District"),
    (MULLAITIVU_DISTRICT, "Mullaitivu District"),
    (NUWARA_ELIYA_DISTRICT, "Nuwara Eliya District"),
    (POLONNARUWA_DISTRICT, "Polonnaruwa District"),
    (PUTTALAM_DISTRICT, "Puttalam District"),
    (RATNAPURA_DISTRICT, "Ratnapura District"),
    (TRINCOMALEE_DISTRICT, "Trincomalee District"),
    (VAVUNIYA_DISTRICT, "Vavuniya District")
]

NORMAL = 'Normal'
SEMI_LUXURY = 'Semi-Luxury'
LUXURY = 'Luxury'

FARE_TYPES = [
    (NORMAL, "Normal"),
    (SEMI_LUXURY, "Semi-Luxury"),
    (LUXURY, "Luxury")
]


class BoardingPoint(models.Model):
    name = models.CharField(max_length=1000)
    province = models.CharField(
        max_length=250, choices=PROVINCES_IN_SRI_LANKA, blank=True)
    city = models.CharField(
        max_length=250, choices=DISTRICTS_IN_SRI_LANKA, blank=True)
    latitude = models.FloatField(default=1)
    longitude = models.FloatField(default=1)
    # section = ManytoMany Relation with Section Class
    # bus_route = ManytoMany Relation with BusRoute Class

    def __str__(self):
        return f"{self.name} || {self.city} || {self.province}"


class BusRoute(models.Model):
    name = models.CharField(max_length=255)
    route_number = models.CharField(max_length=255, blank=True, null=True)
    route_boarding_points = models.ManyToManyField(
        BoardingPoint, related_name='bus_route')
    display_name = models.CharField(max_length=255, default='Colombo-Kandy')
    is_it_reversed = models.BooleanField(default=False)
    # sections = Foriegn Key with Section Class

    def __str__(self):
        return f"{self.name}"


class Section(models.Model):
    bus_route = models.ForeignKey(
        BusRoute, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=255)
    position = models.PositiveSmallIntegerField(default=1)
    section_boarding_points = models.ManyToManyField(
        BoardingPoint, related_name='section')
    distance = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True, help_text="in KM s")
    time = models.DurationField(null=True, blank=True,
                                help_text="Normal travel time")
    busy_time = models.DurationField(
        null=True, blank=True, help_text="Travel time during busy hours")

    class Meta:
        unique_together = ('bus_route', 'position')

    def __str__(self):
        return f"{self.name} (Route: {self.bus_route.name})"


class Buses(models.Model):
    SEAT_TYPES = [
	(0, '0-seater'),
        (32, '32-seater'),
        (40, '40-seater'),
        (52, '52-seater'),
        (64, '64-seater'),
    ]

    BUS_TYPES = [
        ('NORMAL', 'Normal'),
        ('SEMI_LUXURY', 'Semi-Luxury'),
        ('LUXURY', 'Luxury'),
    ]

    bus_name = models.CharField(max_length=255, blank=True)
    bus_number = models.CharField(max_length=25)
    seat_count = models.PositiveIntegerField(choices=SEAT_TYPES, default=0)
    bus_type = models.CharField(
        max_length=20, choices=BUS_TYPES, default='NORMAL')
    route_permit_number = models.CharField(
        max_length=100, null=True, blank=True)
    route_permit_image = models.ImageField(
        upload_to="route_permits/", null=True, blank=True)
    owner = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='bus', null=True, blank=True
    )
    is_approved = models.BooleanField(default=False)
    # seats = ForeignKey to Seat Model
    # trips = ForiegnKey to BusTrip

    def __str__(self):
        return f"{self.bus_number} || {self.bus_name} || {self.seat_count}"


class Seat(models.Model):
    bus = models.ForeignKey(
        Buses, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ('bus', 'seat_number')

    def __str__(self):
        return f"Seat {self.seat_number} (on {self.bus.bus_number})"


class BusFareSemiLuxury(models.Model):
    fare_number = models.PositiveSmallIntegerField()
    fare_price = models.FloatField()


class BusFareLuxury(models.Model):
    fare_number = models.PositiveSmallIntegerField()
    fare_price = models.FloatField()
