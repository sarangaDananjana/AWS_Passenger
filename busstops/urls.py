from django.urls import path
from .views import booking_search

urlpatterns = [
    path('api/booking_search', booking_search, name='booking_search'),
]
