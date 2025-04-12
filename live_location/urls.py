from django.urls import path
from .views import update_live_location, get_live_location

urlpatterns = [
    path('update/', update_live_location, name='update_live_location'),
    path('get/<int:bus_id>/', get_live_location, name='get_live_location'),
]
