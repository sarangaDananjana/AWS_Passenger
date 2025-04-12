from django.contrib import admin
from .models import Booking, BusTrip


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'seat', 'start_point', 'end_point')


@admin.register(BusTrip)
class BusTripAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'bus', 'route', 'start_time')
