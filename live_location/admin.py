from django.contrib import admin
from .models import LiveLocation


@admin.register(LiveLocation)
class LiveLocationAdmin(admin.ModelAdmin):
    list_display = ('bus', 'latitude', 'longitude', 'last_updated')
