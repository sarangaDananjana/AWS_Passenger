from django.core.exceptions import ValidationError
from django import forms
from django.contrib import admin
from .models import BusRoute, Section, BoardingPoint, Buses, Seat, BusFareSemiLuxury, BusFareLuxury
from .models import CITY_TO_PROVINCE_MAP
from django.db.models.signals import post_save
from django.dispatch import receiver


class BoardingPointAdminForm(forms.ModelForm):
    class Meta:
        model = BoardingPoint
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        city = cleaned_data.get('city')
        province = cleaned_data.get('province')

        if city in CITY_TO_PROVINCE_MAP:
            cleaned_data['province'] = CITY_TO_PROVINCE_MAP[city]

        # Check if a boarding point with the same name, city, and province exists
        similar_points = BoardingPoint.objects.filter(
            name__iexact=name,
            city__iexact=city,
            province__iexact=province
        ).exclude(id=self.instance.id if self.instance else None)

        if similar_points.exists():
            raise ValidationError(
                f"A boarding point with the name '{name}' already exists in the city '{city}' and province '{province}'."
            )

        return cleaned_data


@admin.register(BoardingPoint)
class BoardingPointAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'province',
                    'city', 'latitude', 'longitude')
    search_fields = ('name',)
    list_editable = ('latitude', 'longitude')
    form = BoardingPointAdminForm


@admin.register(Buses)
class BusesAdmin(admin.ModelAdmin):
    list_display = ('bus_name', 'bus_number')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ('id', 'bus', 'seat_number')


@receiver(post_save, sender=Buses)
def create_or_update_seats_for_bus(sender, instance, created, **kwargs):
    if created:
        # Newly created bus → generate seats
        Seat.objects.bulk_create([
            Seat(bus=instance, seat_number=i + 1)
            for i in range(instance.seat_count)
        ])
    else:
        # Check if seat count changed
        current_seat_count = instance.seats.count()
        if current_seat_count != instance.seat_count:
            # 🔁 Replace all seats with new range
            instance.seats.all().delete()
            Seat.objects.bulk_create([
                Seat(bus=instance, seat_number=i + 1)
                for i in range(instance.seat_count)
            ])



@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'bus_route',
                    'position', 'distance', 'time')


@admin.register(BusRoute)
class BusRouteAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'is_it_reversed')


@admin.register(BusFareSemiLuxury)
class BusFareSemiLuxuryAdmin(admin.ModelAdmin):
    list_display = ('fare_number', 'fare_price')


@admin.register(BusFareLuxury)
class BusFareLuxuryAdmin(admin.ModelAdmin):
    list_display = ('fare_number', 'fare_price')
